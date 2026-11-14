"""Incertitude chiffrée (phase D de la roadmap, 13/11/2026) : Monte Carlo commun à tous les programmes.

Loi de chaque hypothèse (D1). Un paramètre dont les valeurs diffèrent entre scénarios (ventilé par scénario, ou
sous-champ structuré dont les clés sont des scénarios : montants des mesures, jeux d'emploi…) reçoit une loi
dont le prudent est le 10e centile, le médian la médiane et l'optimiste le 90e centile, avec une queue de chaque côté :
    v(z) = médian + z / 1,2816 × (optimiste − médian)   si z ≥ 0
    v(z) = médian + |z| / 1,2816 × (prudent − médian)   si z < 0
z suit une loi normale ; au-delà des centiles 10 et 90 la pente continue, bornée par la valeur de crise (ou, sans crise
plus défavorable, un pas de plus que le prudent) et par un pas de plus que l'optimiste. Sans prudent écrit (jeux
d'emploi), le prudent est le milieu de la crise et du médian, comme dans le moteur. Les années sont exclues.

Corrélation : z = √ρ × Z + √(1 − ρ) × ε, Z commun au tirage (le « climat » : productivité, comportements et
multiplicateurs ont tendance à être bons ou mauvais ensemble), ε propre au paramètre. ρ = 1 redonne les scénarios
(chaque centile de la loi est le même point pour tous les paramètres) ; ρ = 0 suppose l'indépendance, qui rend les cas
où tout va bien ou tout va mal très rares. Faute de source, on publie la fourchette entre les deux bornes
(incertitude.correlation, décision du 14/11/2026).

Tirages communs (D2) : le z d'un paramètre ne dépend que de la graine, du numéro du tirage et du nom du paramètre :
deux programmes qui partagent une hypothèse la voient tirée au même point, et les écarts entre programmes se lisent
tirage par tirage. Chaque tirage remplace la colonne médiane et se calcule dans le scénario médian (la colonne
prudente reste celle du scénario prudent : c'est elle que le moteur lit pour les effets en sens inverse, comme dans le
scénario médian publié).

    python -m moteur.incertitude [n] [rho]     # écrit sorties/incertitude_rho0.json et incertitude_rho1.json
"""
from __future__ import annotations

import copy
import dataclasses
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

from . import noyau
from .parametres import Parametres

Z90 = 1.2815515655446004
ANNEES_CLES = (2029, 2032, 2037, 2050)
GRANDEURS = ("deficit", "dette_pib", "chomage", "pib")
SORTIE = Path(__file__).resolve().parent.parent / "sorties" / "incertitude.json"
SCEN = ("crise", "prudent", "median", "optimiste")


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _est_jeu(d) -> bool:
    """Dictionnaire de valeurs par scénario (au moins médian et optimiste, rien d'autre que des scénarios)."""
    return isinstance(d, dict) and {"median", "optimiste"} <= set(d) and set(d) <= set(SCEN) and all(
        _num(x) or (isinstance(x, list) and x and all(_num(y) for y in x)) for x in d.values())


def _valeur(d: dict, z: float, i: int | None = None):
    """Valeur tirée d'un jeu de scénarios (élément i d'une liste)."""
    g = (lambda k: d[k][i]) if i is not None else (lambda k: d[k])
    med, opt = g("median"), g("optimiste")
    cri = g("crise") if "crise" in d else None
    pru = g("prudent") if "prudent" in d else ((cri + med) / 2 if cri is not None else med)
    if z >= 0:
        v = med + z / Z90 * (opt - med)
        borne = opt + (opt - med)
        v = min(v, borne) if opt >= med else max(v, borne)
    else:
        v = med - z / Z90 * (pru - med)
        au_dela = cri is not None and (cri - pru) * (pru - med) > 0
        borne = cri if au_dela else pru + (pru - med)
        v = max(v, borne) if pru <= med else min(v, borne)
    ancres = [x for x in (cri, pru, med, opt) if x is not None]
    if min(ancres) >= 0:
        v = max(v, 0.0)
    if all(isinstance(x, int) for x in ancres):
        v = int(round(v))
    return v


def _tirer_jeu(d: dict, z: float) -> dict:
    d = dict(d)
    if isinstance(d["median"], list):
        d["median"] = [_valeur(d, z, i) for i in range(len(d["median"]))]
    else:
        d["median"] = _valeur(d, z)
    return d


def _differe(d: dict) -> bool:
    return len({json.dumps(v) for v in d.values()}) > 1


def cibles(p: Parametres) -> list[tuple[str, tuple]]:
    """(clé, chemin) des jeux de scénarios incertains : le paramètre lui-même, ou un sous-champ structuré."""
    out = []
    for x in p:
        if x.unite == "annee":
            continue
        if x.par_scenario:
            if _est_jeu(x.valeur) and _differe(x.valeur):
                out.append((x.cle, ()))
            continue

        def descendre(v, chemin):
            if not isinstance(v, dict) or len(chemin) > 3:
                return
            if _est_jeu(v):
                if _differe(v):
                    out.append((x.cle, chemin))
                return
            for k, w in v.items():
                descendre(w, chemin + (k,))
        descendre(x.valeur, ())
    return out


_Z: dict = {}


def _z_propre(graine: int, i: int, nom: str) -> float:
    k = (graine, i, nom)
    if k not in _Z:
        _Z[k] = random.Random(f"{graine}|{i}|{nom}").gauss(0.0, 1.0)
    return _Z[k]


def z_tirage(graine: int, i: int, rho: float, nom: str) -> float:
    commun = random.Random(f"{graine}|{i}|commun").gauss(0.0, 1.0)
    propre = random.Random(f"{graine}|{i}|{nom}").gauss(0.0, 1.0)
    return math.sqrt(rho) * commun + math.sqrt(1 - rho) * propre


def tirer(p: Parametres, graine: int, i: int, rho: float, liste=None) -> Parametres:
    """Copie de p dont chaque jeu de scénarios incertain a sa colonne médiane tirée (tirage n° i)."""
    c = p.avec()
    for cle, chemin in (liste if liste is not None else cibles(p)):
        nom = "/".join((cle,) + tuple(str(k) for k in chemin))
        z = z_tirage(graine, i, rho, nom)
        par = c._p[cle]
        if not chemin:
            c._p[cle] = dataclasses.replace(par, valeur=_tirer_jeu(par.valeur, z))
            continue
        v = copy.deepcopy(par.valeur)
        cible = v
        for k in chemin[:-1]:
            cible = cible[k]
        cible[chemin[-1]] = _tirer_jeu(cible[chemin[-1]], z)
        c._p[cle] = dataclasses.replace(par, valeur=v)
    return c


def _lire(res: dict) -> dict:
    return {t: {g: res[t][g] for g in GRANDEURS} for t in ANNEES_CLES}


def programmes() -> list[str]:
    from .noyau import charger  # noqa: F401
    racine = Path(__file__).resolve().parent.parent / "programmes"
    return sorted(d.name for d in racine.iterdir() if (d / "programme.py").exists())


def un_tirage(i: int, graine: int, rho: float, noms: list[str], base: Parametres, propres: dict, listes: dict) -> dict:
    """Statu quo et programmes du tirage i, dans le scénario médian, avec leur règle de trajectoire."""
    p = tirer(base, graine, i, rho, listes["base"])
    out = {"statu_quo": _lire(noyau.simuler(p, None, scenarios=("median",), contrefactuel=False)["median"])}
    for nom in noms:
        prog = noyau.charger(nom)
        if nom in propres:
            prog.pt = tirer(propres[nom], graine, i, rho, listes[nom])
        try:
            out[nom] = _lire(noyau.simuler(p, prog, scenarios=("median",), contrefactuel=False)["median"])
        except Exception as e:  # noqa: BLE001 — tirage écarté pour ce programme, compté dans le résumé
            out[nom] = None
            out.setdefault("erreurs", {})[nom] = f"{type(e).__name__}: {e}"[:200]
    return out


def _quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * q
    j = int(k)
    return s[j] + (s[min(j + 1, len(s) - 1)] - s[j]) * (k - j)


def _rangs(xs: list[float]) -> list[float]:
    ordre = sorted(range(len(xs)), key=lambda k: xs[k])
    r = [0.0] * len(xs)
    for pos, k in enumerate(ordre):
        r[k] = pos
    return r


def resumer(tirages: list[dict], noms: list[str], graine: int, rho: float, listes: dict, n_sensibilite: int = 10) -> dict:
    """Intervalles (D4), probabilité de faire mieux que le statu quo, et sensibilité (D3)."""
    out = {"n": len(tirages), "graine": graine, "rho": rho, "programmes": {}}
    for nom in ["statu_quo"] + noms:
        r = {}
        tous = tirages
        tirages = [d for d in tous if d.get(nom) is not None and d.get("statu_quo") is not None]
        r["tirages_retenus"] = len(tirages)
        for t in ANNEES_CLES:
            for g in GRANDEURS:
                xs = [d[nom][t][g] for d in tirages]
                r[f"{g}_{t}"] = {"p10": _quantile(xs, 0.1), "p50": _quantile(xs, 0.5), "p90": _quantile(xs, 0.9),
                                 "moyenne": statistics.fmean(xs)}
            if nom != "statu_quo":
                ec = [d[nom][t]["deficit"] - d["statu_quo"][t]["deficit"] for d in tirages]
                r[f"ecart_deficit_{t}"] = {"p10": _quantile(ec, 0.1), "p50": _quantile(ec, 0.5), "p90": _quantile(ec, 0.9)}
                r[f"proba_mieux_que_statu_quo_{t}"] = sum(x < 0 for x in ec) / len(ec)
        # sensibilité : corrélation de rang entre le z de chaque hypothèse et le déficit de 2037 du programme
        cles = listes["base"] + (listes.get(nom) or [])
        y = _rangs([d[nom][2037]["deficit"] for d in tirages])
        infl = []
        for cle, chemin in cles:
            n_ = "/".join((cle,) + tuple(str(k) for k in chemin))
            # z propre seulement (le commun est le même pour toutes les hypothèses : poids_climat_commun)
            propre = [_z_propre(graine, d["i"], n_) for d in tirages]
            try:
                c = statistics.correlation(_rangs(propre), y)
            except statistics.StatisticsError:
                c = 0.0
            infl.append((n_, c))
        infl.sort(key=lambda kv: -abs(kv[1]))
        r["sensibilite_deficit_2037"] = infl[:n_sensibilite]
        if rho > 0:
            zc = [z_tirage(graine, d["i"], 1.0, "x") for d in tirages]  # le commun ne dépend pas du nom
            try:
                r["poids_climat_commun"] = statistics.correlation(_rangs(zc), y)
            except statistics.StatisticsError:
                r["poids_climat_commun"] = 0.0
        out["programmes"][nom] = r
        tirages = tous
    return out


_ETAT: dict = {}


def _preparer(noms: list[str]) -> tuple:
    base = Parametres()
    propres = {}
    for nom in noms:
        prog = noyau.charger(nom)
        if hasattr(prog, "pt"):
            propres[nom] = prog.pt
    listes = {"base": cibles(base)}
    for nom, q in propres.items():
        # paramètres propres au programme seulement (les communs sont tirés dans base, au même point)
        listes[nom] = [(c, ch) for c, ch in cibles(q) if f"programmes/{nom}/" in str(q.origine[c])]
    return base, propres, listes


def _travail(args) -> dict:
    i, graine, rho, noms = args
    if "prep" not in _ETAT:
        _ETAT["prep"] = _preparer(noms)
    base, propres, listes = _ETAT["prep"]
    d = un_tirage(i, graine, rho, noms, base, propres, listes)
    d["i"] = i
    return d


def simuler(n: int = 200, graine: int = 2029, rho: float | None = None, noms: list[str] | None = None,
            journal=None, processus: int = 1) -> dict:
    noms = noms if noms is not None else programmes()
    base, propres, listes = _preparer(noms)
    if rho is None:
        raise ValueError("rho : une des bornes de incertitude.correlation (0 ou 1), ou une valeur d'essai")
    # tirages écrits au fil de l'eau (reprise possible après une interruption) : une ligne JSON par tirage
    fichier = fichier_tirages(rho, graine)
    faits = {}
    if fichier.exists():
        for ligne in fichier.read_text(encoding="utf-8").splitlines():
            if ligne.strip():
                d = json.loads(ligne)
                faits[d["i"]] = d
    a_faire = [i for i in range(n) if i not in faits]
    t0 = time.time()
    with fichier.open("a", encoding="utf-8") as fh:
        def garder(d):
            faits[d["i"]] = d
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            fh.flush()
            if journal and len(faits) % 10 == 0:
                journal(f"{len(faits)}/{n} tirages, {time.time() - t0:.0f} s")
        if processus > 1 and a_faire:
            import multiprocessing as mp
            # un processus neuf tous les 10 tirages : chaque tirage crée des copies de paramètres gardées en vie
            # jusqu'à la fin du processus (parametres._VIVANTES) ; sans recyclage la mémoire sature
            with mp.get_context("fork").Pool(processus, maxtasksperchild=10) as pool:
                for d in pool.imap_unordered(_travail, [(i, graine, rho, noms) for i in a_faire]):
                    garder(d)
        else:
            for i in a_faire:
                d = un_tirage(i, graine, rho, noms, base, propres, listes)
                d["i"] = i
                garder(d)
    tirages = [_cles_int(faits[i]) for i in range(n)]
    r = resumer(tirages, noms, graine, rho, listes)
    r["parametres_tires"] = len(listes["base"]) + sum(len(v) for k, v in listes.items() if k != "base")
    return r


def fichier_tirages(rho: float, graine: int) -> Path:
    return SORTIE.with_name(f"incertitude_tirages_rho{rho:g}_graine{graine}.jsonl")


def _cles_int(d: dict) -> dict:
    """Années relues en JSON : clés texte → entiers."""
    return {k: ({int(t): x for t, x in v.items()} if isinstance(v, dict) and k not in ("erreurs",) else v)
            for k, v in d.items()}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    bornes = [float(sys.argv[2])] if len(sys.argv) > 2 else Parametres().val("incertitude.correlation")
    for rho in bornes:
        r = simuler(n, rho=rho, journal=lambda m: print(m, flush=True), processus=2)
        f = SORTIE.with_name(f"incertitude_rho{rho:g}.json")
        f.parent.mkdir(exist_ok=True)
        f.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
        print(f"Écrit : {f}")
