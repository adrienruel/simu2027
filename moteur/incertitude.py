"""Incertitude : distribution du déficit quand les hypothèses de comportement varient ensemble.

Chaque paramètre ventilé par scénario dont les valeurs diffèrent est tiré au hasard, indépendamment des
autres, entre sa valeur de crise et sa valeur optimiste (loi uniforme) ; les emplois créés par les réformes
aussi (entre le jeu de crise et le jeu optimiste de la feuille Emploi). Le tirage remplace la colonne
prudente ; on calcule le prudent sans clause de trajectoire, qui sinon effacerait l'écart.

Ce n'est pas une loi de probabilité « vraie » : les bornes sont celles des scénarios, et l'indépendance
des tirages rend les cas extrêmes (tout favorable ou tout défavorable) rares. Le scénario de crise, où tout
est défavorable en même temps, reste à lire à part.

    python -m moteur.incertitude      # écrit sorties/incertitude.json (quelques minutes)
"""
from __future__ import annotations

import dataclasses
import json
import random
from pathlib import Path

from . import noyau
from .parametres import Parametres

ANNEES_CLES = (2029, 2032, 2037, 2050)
SORTIE = Path(__file__).resolve().parent.parent / "sorties" / "incertitude.json"


def parametres_incertains(p: Parametres) -> list[str]:
    out = []
    for x in p:
        if not x.par_scenario:
            continue
        v = x.valeur
        if not all(isinstance(v[s], (int, float)) and not isinstance(v[s], bool) for s in p.scenarios):
            continue
        if v["crise"] != v["optimiste"] and x.unite != "annee":
            out.append(x.cle)
    return out


def tirage(p: Parametres, rng: random.Random, cles: list[str]) -> tuple[Parametres, dict]:
    c = p.avec()
    tire = {}
    for cle in cles:
        v = dict(c._p[cle].valeur)
        u = rng.random()
        v["prudent"] = v["crise"] + u * (v["optimiste"] - v["crise"])
        tire[cle] = u
        c._p[cle] = dataclasses.replace(c._p[cle], valeur=v)
    c.emplois_tirage = rng.random()
    tire["emplois_reformes"] = c.emplois_tirage
    return c, tire


def _mesure(p: Parametres, scenario: str = "prudent") -> dict:
    """Déficit, dette et chômage d'un scénario du programme sur le noyau commun (12/11/2026)."""
    res = noyau.simuler(p, noyau.charger(p.programme), scenarios=(scenario,))[scenario]
    return {t: {"deficit": res[t]["deficit"], "dette_pib": res[t]["dette_pib"], "chomage": res[t]["chomage"]} for t in ANNEES_CLES}


def _quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * q
    i = int(k)
    return s[i] + (s[min(i + 1, len(s) - 1)] - s[i]) * (k - i)


def simuler(n: int = 300, graine: int = 2029, p: Parametres | None = None) -> dict:
    p = (p or Parametres()).avec({"clause.active": False})
    cles = parametres_incertains(p)
    rng = random.Random(graine)
    tirages = []
    for _ in range(n):
        c, tire = tirage(p, rng, cles)
        tirages.append({"tirage": tire, "resultat": _mesure(c)})
    prudent = _mesure(p)
    crise = _mesure(p, "crise")
    resume = {}
    for t in ANNEES_CLES:
        for g in ("deficit", "dette_pib", "chomage"):
            xs = [r["resultat"][t][g] for r in tirages]
            resume[f"{g}_{t}"] = {"p10": _quantile(xs, 0.1), "p50": _quantile(xs, 0.5), "p90": _quantile(xs, 0.9),
                                  "min": min(xs), "max": max(xs), "prudent": prudent[t][g], "crise": crise[t][g],
                                  "part_pire_que_prudent": sum(x > prudent[t][g] for x in xs) / len(xs)}
    # Corrélation de rang simple entre chaque tirage et le déficit 2037 : ce qui fait le plus bouger le résultat
    import statistics
    d37 = [r["resultat"][2037]["deficit"] for r in tirages]
    poids = {}
    for cle in cles + ["emplois_reformes"]:
        us = [r["tirage"][cle] for r in tirages]
        try:
            poids[cle] = statistics.correlation(us, d37)
        except statistics.StatisticsError:
            poids[cle] = 0.0
    return {"n": n, "graine": graine, "parametres": cles, "resume": resume,
            "influence_deficit_2037": dict(sorted(poids.items(), key=lambda kv: -abs(kv[1])))}


if __name__ == "__main__":
    SORTIE.parent.mkdir(exist_ok=True)
    r = simuler()
    SORTIE.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Écrit : {SORTIE}")
    for t in ANNEES_CLES:
        x = r["resume"][f"deficit_{t}"]
        print(t, "déficit sans clause : P10 %.2f  P50 %.2f  P90 %.2f  | prudent %.2f  crise %.2f  | part des tirages pires que le prudent %.0f %%"
              % (x["p10"], x["p50"], x["p90"], x["prudent"], x["crise"], 100 * x["part_pire_que_prudent"]))
    print("Influence sur le déficit 2037 (corrélation) :")
    for k, v in list(r["influence_deficit_2037"].items())[:12]:
        print(f"  {k:50} {v:+.2f}")
