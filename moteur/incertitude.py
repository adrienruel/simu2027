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


# Paramètres que le moteur lit dans le scénario miroir quand le sens d'un effet s'inverse (MIROIR dans
# moteur/bouclage.py, capital.py, migrations.py, noyau.py, offre.py, programme_simple.py, reformes_structurelles.py).
# Phase 3.2 (16/11/2026) : leur colonne prudente, que le tirage médian lit en miroir, est tirée au point miroir
# z_m = −z − z90 (z = 0, médian → prudent ; z = −z90, prudent → médian ; z = +z90, optimiste → vers la crise), comme
# les scénarios publiés (MIROIR : prudent ↔ médian, crise ↔ optimiste). Avant, elle restait au prudent publié.
# Liste explicite : d'autres lectures de la colonne prudente ne sont pas des miroirs (macro.tendance avant 2029,
# inflation de 2027-2028), et ne doivent pas bouger.
MIROIR_CLES = (
    "macro.multiplicateur", "macro.annees_effet_ajustement", "bouclage.prime_demande", "emploi_public.eviction_privee",
    "seniors.devenir", "macro.elasticite_invest", "capital_public.parametres", "demographie.titres_vers_solde",
    "macro.reformes_structurelles", "offre.recherche", "offre.education", "offre.travail_participation",
    "offre.travail_heures", "offre.demande_travail", "offre.travail_couples", "offre.travail_part_pib",
    "offre.elasticite_capital_menages", "offre.elasticite_consommation", "offre.elasticite_cout_travail",
    "offre.elasticite_successions", "offre.elasticite_transferts_actifs",
    "demographie.natalite_semi_elasticite", "demographie.creches_effet", "macro.semi_elasticite_transfert",
)


def z_miroir(z: float) -> float:
    return -z - Z90


def _tirer_jeu(d: dict, z: float, miroir: bool = False) -> dict:
    orig, d = d, dict(d)
    if isinstance(d["median"], list):
        d["median"] = [_valeur(orig, z, i) for i in range(len(orig["median"]))]
        if miroir and "prudent" in orig:
            d["prudent"] = [_valeur(orig, z_miroir(z), i) for i in range(len(orig["median"]))]
    else:
        d["median"] = _valeur(orig, z)
        if miroir and "prudent" in orig:
            d["prudent"] = _valeur(orig, z_miroir(z))
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


def tirer(p: Parametres, graine: int, i: int, rho: float, liste=None, miroir: bool = True) -> Parametres:
    """Copie de p dont chaque jeu de scénarios incertain a sa colonne médiane tirée (tirage n° i), et, pour les
    paramètres lus en miroir (MIROIR_CLES), sa colonne prudente au point miroir (miroir=False : l'ancien tirage)."""
    return tirer_z(p, lambda nom: z_tirage(graine, i, rho, nom), liste, miroir)


LOIS_FICHIER = Path(__file__).resolve().parent.parent / "parametres" / "commun" / "lois.yaml"
_LOIS: dict | None = None


def lois() -> dict:
    """Roadmap 6.1 (22/11/2026) : lois sourcées (parametres/commun/lois.yaml), par nom de cible (« clé » ou
    « clé/sous-champ »). Chaque loi donne les valeurs aux centiles 10 et 90 du côté défavorable (« prudent ») et
    favorable (« optimiste ») tirées de la littérature, et sa source ; le centre reste la colonne médiane (sauf
    « median » écrit). Elle remplace, pour le tirage seulement, les colonnes de scénario du paramètre."""
    global _LOIS
    if _LOIS is None:
        import yaml
        _LOIS = {}
        if LOIS_FICHIER.exists():
            for nom, x in (yaml.safe_load(LOIS_FICHIER.read_text(encoding="utf-8")) or {}).items():
                if not x.get("source") or "prudent" not in x or "optimiste" not in x:
                    raise ValueError(f"loi {nom} : prudent, optimiste et source obligatoires")
                _LOIS[nom] = x
    return _LOIS


def _avec_loi(d: dict, nom: str) -> dict:
    """Jeu de scénarios d'une cible, ses ancres remplacées par sa loi sourcée s'il y en a une."""
    x = lois().get(nom)
    if x is None:
        return d
    d = dict(d)
    for k in ("prudent", "optimiste", "median", "crise"):
        if k in x:
            d[k] = x[k]
    if "crise" in d and "crise" not in x:
        del d["crise"]  # la borne de crise du scénario ne vaut plus pour une loi d'une autre source
    return d


def tirer_z(p: Parametres, z_de, liste=None, miroir: bool = True) -> Parametres:
    """Comme tirer, avec z_de(nom) → z donné (tests : tous les paramètres au même point)."""
    c = p.avec()
    for cle, chemin in (liste if liste is not None else cibles(p)):
        nom = "/".join((cle,) + tuple(str(k) for k in chemin))
        z = z_de(nom)
        par = c[cle]
        mir = miroir and cle in MIROIR_CLES
        if not chemin:
            tire = _tirer_jeu(_avec_loi(par.valeur, nom), z, mir)
            c.remplacer(cle, dataclasses.replace(par, valeur={**par.valeur, "median": tire["median"],
                                                         **({"prudent": tire["prudent"]} if mir and "prudent" in par.valeur else {})}))
            continue
        v = copy.deepcopy(par.valeur)
        cible = v
        for k in chemin[:-1]:
            cible = cible[k]
        tire = _tirer_jeu(_avec_loi(cible[chemin[-1]], nom), z, mir)
        orig = cible[chemin[-1]]
        cible[chemin[-1]] = {**orig, "median": tire["median"], **({"prudent": tire["prudent"]} if mir and "prudent" in orig else {})}
        c.remplacer(cle, dataclasses.replace(par, valeur=v))
    return c


def _lire(res: dict) -> dict:
    return {t: {g: res[t][g] for g in GRANDEURS} for t in ANNEES_CLES}


def programmes() -> list[str]:
    """Programmes publiés (programmes/publies.yaml), sans le statu quo."""
    return noyau.programmes_disponibles()[1:]


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
        # fonds de capitalisation compté dans les administrations publiques (variante commune, moteur/fonds_apu.py),
        # tiré lui aussi (phase 3.2, 16/11/2026) : la fourchette du classement du fonds se lit à côté de la publiée
        if nom in FONDS and out[nom] is not None:
            from . import fonds_apu
            try:
                out[nom + SUFFIXE_FONDS] = _lire(fonds_apu.variante(p, prog, scenarios=("median",))["median"]["apu"])
            except Exception as e:  # noqa: BLE001
                out[nom + SUFFIXE_FONDS] = None
                out.setdefault("erreurs", {})[nom + SUFFIXE_FONDS] = f"{type(e).__name__}: {e}"[:200]
    return out


# programmes publiés qui proposent un fonds de capitalisation (outils/variante_fonds_apu.PROGRAMMES)
FONDS = ("philippe", "retailleau", "bertrand", "zemmour", "le_pen")
SUFFIXE_FONDS = "@fonds_apu"


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
    variantes = [n + SUFFIXE_FONDS for n in noms if n in FONDS and any(n + SUFFIXE_FONDS in d for d in tirages)]
    for nom in ["statu_quo"] + noms + variantes:
        r = {}
        tous = tirages
        tirages = [d for d in tous if d.get(nom) is not None and d.get("statu_quo") is not None]
        r["tirages_retenus"] = len(tirages)
        r["tirages_ecartes"] = len(tous) - len(tirages)
        if not tirages:
            out["programmes"][nom] = r
            tirages = tous
            continue
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
        cles = listes["base"] + (listes.get(nom.split("@")[0]) or [])
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
            # plus de recyclage des processus (maxtasksperchild=10 jusqu'au 25/11/2026) : les copies de paramètres
            # ne sont plus gardées en vie (parametres.jeton, R1.4), la mémoire d'un processus reste stable (≈ 60 Mo
            # après 12 tirages, contre 1,1 Go avant)
            with mp.get_context("fork").Pool(processus) as pool:
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
        from outils import trace
        trace.enregistrer([f, fichier_tirages(rho, 2029)], script="moteur.incertitude")
        print(f"Écrit : {f}")
