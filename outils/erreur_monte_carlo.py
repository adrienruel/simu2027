"""Erreur de Monte Carlo des quantiles publiés (roadmap du moteur 25/11/2026, R4.2).

Rééchantillonne (bootstrap) les tirages déjà faits par `python -m moteur.incertitude` et donne, pour l'écart de déficit
au statu quo d'une année : la demi-largeur de l'intervalle à 90 % de p10, p50 et p90, et la stabilité du classement
des programmes sur la médiane (part des rééchantillonnages où chaque programme garde son rang le plus fréquent). Un
rang stable à moins de 95 % veut dire que les tirages ne suffisent pas à départager ce programme de ses voisins.
Rien n'est écrit dans sorties/ : sortie à l'écran.

    python -m outils.erreur_monte_carlo                    # ρ = 0 et ρ = 1, 2037, 500 rééchantillonnages
    python -m outils.erreur_monte_carlo --annee 2050 --b 1000
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter

from moteur import incertitude as inc
from moteur.incertitude import _quantile

QUANTILES = (("p10", 0.1), ("p50", 0.5), ("p90", 0.9))


def ecarts(tirages: list[dict], annee: int) -> dict[str, list[float]]:
    """Écart de déficit au statu quo par programme, sur les tirages où le programme et le statu quo existent tous
    les deux (mêmes tirages pour tous les programmes : ceux où aucun n'a échoué)."""
    noms = [k for k in tirages[0] if k not in ("statu_quo", "i", "erreurs") and inc.SUFFIXE_FONDS not in k]
    communs = [d for d in tirages if d.get("statu_quo") and all(d.get(n) for n in noms)]
    a = str(annee)
    return {n: [d[n][a]["deficit"] - d["statu_quo"][a]["deficit"] for d in communs] for n in noms}


def bootstrap(ec: dict[str, list[float]], b: int = 500, graine: int = 2029) -> dict[str, dict]:
    rng = random.Random(graine)
    noms = list(ec)
    n = len(next(iter(ec.values())))
    q = {nm: {k: [] for k, _ in QUANTILES} for nm in noms}
    rangs = {nm: [] for nm in noms}
    for _ in range(b):
        idx = [rng.randrange(n) for _ in range(n)]
        med = {}
        for nm in noms:
            xs = [ec[nm][i] for i in idx]
            for k, x in QUANTILES:
                q[nm][k].append(_quantile(xs, x))
            med[nm] = q[nm]["p50"][-1]
        for r, nm in enumerate(sorted(noms, key=lambda k: med[k]), 1):
            rangs[nm].append(r)
    out = {}
    for nm in noms:
        rang, nb = Counter(rangs[nm]).most_common(1)[0]
        out[nm] = {"p50": _quantile(ec[nm], 0.5), "tirages": n, "rang": rang, "stabilite_rang": nb / b,
                   **{f"demi_ic90_{k}": (_quantile(v, 0.95) - _quantile(v, 0.05)) / 2 for k, v in q[nm].items()}}
    return out


def groupes_ex_aequo(tirages: list[dict], annee: int, grandeur: str = "deficit", b: int = 500,
                     seuil: float = 0.95, graine: int = 2029) -> dict[str, list[str]]:
    """Programmes que les tirages ne départagent pas, pour l'affichage « ex æquo » du comparateur (26/11/2026).

    Programmes rangés par médiane de la grandeur (statu quo à part). Deux voisins sont ex æquo quand leur ordre
    s'inverse dans plus de 1 − seuil des rééchantillonnages ; les chaînes de voisins ex æquo forment un groupe.
    Rend {programme: [autres programmes du groupe]} (liste vide : départagé de ses voisins)."""
    noms = [k for k in tirages[0] if k not in ("statu_quo", "i", "erreurs") and inc.SUFFIXE_FONDS not in k]
    communs = [d for d in tirages if d.get("statu_quo") and all(d.get(n) for n in noms)]
    a = str(annee)
    if grandeur.startswith("ecart_"):  # écart au statu quo, tirage par tirage (ex. ecart_deficit)
        g = grandeur.removeprefix("ecart_")
        val = {n: [d[n][a][g] - d["statu_quo"][a][g] for d in communs] for n in noms}
    else:
        val = {n: [d[n][a][grandeur] for d in communs] for n in noms}
    ordre = sorted(noms, key=lambda n: _quantile(val[n], 0.5))
    paires = list(zip(ordre, ordre[1:]))
    tenu = Counter()
    rng = random.Random(graine)
    m = len(communs)
    for _ in range(b):
        idx = [rng.randrange(m) for _ in range(m)]
        med = {n: _quantile([val[n][i] for i in idx], 0.5) for n in noms}
        for x, y in paires:
            if med[x] <= med[y]:
                tenu[(x, y)] += 1
    groupes, courant = [], [ordre[0]] if ordre else []
    for x, y in paires:
        if tenu[(x, y)] / b < seuil:
            courant.append(y)
        else:
            groupes.append(courant)
            courant = [y]
    if courant:
        groupes.append(courant)
    return {n: [k for k in g if k != n] for g in groupes for n in g}


def main(argv=None) -> dict:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--annee", type=int, default=2037)
    a.add_argument("--b", type=int, default=500, help="rééchantillonnages")
    a.add_argument("--graine", type=int, default=2029, help="graine des tirages publiés")
    args = a.parse_args(argv)
    res = {}
    for rho in (0.0, 1.0):
        f = inc.fichier_tirages(rho, args.graine)
        if not f.exists():
            print(f"{f.name} absent : python -m moteur.incertitude d'abord")
            continue
        tirages = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        r = res[rho] = bootstrap(ecarts(tirages, args.annee), args.b)
        print(f"ρ = {rho:g}, {args.annee}, écart de déficit au statu quo (points de PIB), "
              f"{next(iter(r.values()))['tirages']} tirages, {args.b} rééchantillonnages")
        for nm, x in sorted(r.items(), key=lambda kv: kv[1]["p50"]):
            alerte = "" if x["stabilite_rang"] >= 0.95 else "  ← rang non départagé"
            print(f"  {nm:12s} p50 {x['p50']:+7.2f} ±{x['demi_ic90_p50']:.3f}  p10 ±{x['demi_ic90_p10']:.3f}"
                  f"  p90 ±{x['demi_ic90_p90']:.3f}  rang {x['rang']:2d} ({x['stabilite_rang']:.0%}){alerte}")
    return res


if __name__ == "__main__":
    main()
