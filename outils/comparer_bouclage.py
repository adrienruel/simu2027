"""Effet de la phase E (macro bouclée) sur chaque programme : déficit, dette, PIB et inflation, avec et sans
macro.bouclage. Usage : python -m outils.comparer_bouclage [programme ...] [--scenario prudent]"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

from moteur import noyau
from moteur.parametres import Parametres

ANNEES = (2029, 2032, 2037, 2050)


VARIANTE = {}  # options de la comparaison « avant » (par défaut : sans macro bouclée)


def calcul(args):
    nom, boucle, scen, var = args
    p = Parametres().avec({"macro.bouclage": True, **var} if not boucle and var else {"macro.bouclage": boucle})
    res = noyau.simuler(p, noyau.charger(nom), scenarios=scen, contrefactuel=False)
    return nom, boucle, {s: {t: {k: res[s][t][k] for k in ("deficit", "dette_pib", "pib", "inflation", "taux_apparent", "chomage")}
                             for t in ANNEES} for s in res}


def main():
    argv = sys.argv[1:]
    if "--e5" in argv:  # avant = phase E sans le stock de capital commun
        VARIANTE["macro.capital_commun"] = False
        argv.remove("--e5")
    if "--scenario" in argv:
        i = argv.index("--scenario"); del argv[i:i + 2]
    arg = [a for a in argv if not a.startswith("--")]
    scen = [sys.argv[sys.argv.index("--scenario") + 1]] if "--scenario" in sys.argv else None
    noms = arg or noyau.programmes_disponibles()
    taches = [(n, b, scen, dict(VARIANTE)) for n in noms for b in (False, True)]
    with ProcessPoolExecutor(2) as ex:
        out = list(ex.map(calcul, taches))
    r = {}
    for nom, b, v in out:
        r.setdefault(nom, {})["apres" if b else "avant"] = v
    json.dump(r, open("sorties/comparaison_bouclage.json", "w"), indent=1, default=str)
    for s in (scen or ["prudent", "median"]):
        print(f"\nDéficit (% du PIB), {s} : avant → après")
        for nom in noms:
            a, b = r[nom]["avant"][s], r[nom]["apres"][s]
            print(f"  {nom:<20}" + "  ".join(f"{t} {a[t]['deficit']:6.2f} → {b[t]['deficit']:6.2f}" for t in ANNEES))


if __name__ == "__main__":
    main()
