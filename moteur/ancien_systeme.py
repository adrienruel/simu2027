"""Pensions de l'ancien système, génération par génération (29 octobre 2026).

Qui reste dans l'ancien système : les générations nées en 1978 ou avant (51 ans ou plus en 2029). Les plus
jeunes (22 à 50 ans en 2029) reçoivent le remboursement de leurs cotisations et relèvent du nouveau système
(feuille Socle actuariel, cohortes_2029.csv).

Pour chaque génération et chaque année :
- survivants : population par âge des projections de l'Insee de juin 2026 (mortalité centrale ; les générations
  nées avant 1979 ne dépendent pas de la fécondité future) ;
- part déjà partie à la retraite à chaque âge (paramètre ancien_systeme.part_retraites_age, âge légal de 64 ans) ;
- pension : la même pour tous en 2029 (les nouveaux retraités touchent un peu moins que la moyenne, DREES), puis
  gelée en euros courants dès 2029 ou dès le départ s'il est plus tardif (désindexation) : elle perd l'inflation
  chaque année en euros constants.
Le niveau est calé sur les dépenses de l'ancien système en 2029 (428 Md€, série de la v235 issue du COR) et
l'effectif sur les retraités du COR en 2029 (19,15 millions : résidents à l'étranger et réversions seules
compris) ; le module ne change que leur évolution.

Sans le module (v235) : dépenses désindexées du COR × part des retraités de l'ancien système.
"""
from __future__ import annotations

import csv

from .distribution import DONNEES
from .parametres import Parametres

ANNEES = list(range(2029, 2074))
DERNIERE_GENERATION = 1978


def _csv_v235() -> dict[int, dict]:
    with (DONNEES / "ancien_systeme_retraites.csv").open(encoding="utf-8") as f:
        return {int(l["annee"]): {k: float(v) for k, v in l.items()} for l in csv.DictReader(f)}


def _part_age(p: Parametres) -> dict[int, float]:
    t = {int(a): v for a, v in p.val("ancien_systeme.part_retraites_age").items()}
    a_max = max(t)
    return {a: (t[a] if a in t else (1.0 if a > a_max else 0.0)) for a in range(0, 106)}


def par_generation(p: Parametres) -> dict[int, dict[str, float]]:
    from .demographie import _projection
    pop = _projection("central")
    infl = p.val("calendrier.inflation")
    nouveau = p.val("ancien_systeme.pension_nouveaux_relative")
    r = _part_age(p)
    geles = p.val("ancien_systeme.droits_geles_des_2029")
    brut = {}
    for t in ANNEES:
        dep = eff = 0.0
        for a in range(t - DERNIERE_GENERATION, 106):
            g = t - a
            n = pop[t][a]
            # parts de la génération parties chaque année d'âge, chacune gelée depuis son départ
            for b in range(50, a + 1):
                d = r[b] - r[b - 1]
                if d <= 0:
                    continue
                depart = g + b
                niveau = 1.0 if depart < 2029 else nouveau
                gel = 2029 if geles else max(2029, depart)
                dep += n * d * niveau * (1 + infl) ** -(t - gel)
                eff += n * d
        brut[t] = {"depenses": dep, "retraites": eff}
    v = _csv_v235()
    k = v[2029]["depenses_desindexees_md"] * v[2029]["part_ancien_systeme"] / brut[2029]["depenses"]
    # effectif calé sur les retraités du COR en 2029 (résidents à l'étranger et pensions de réversion seules compris)
    kn = p.val("anciennes_pensions.retraites_ancien_2029_millions")[0] * 1e6 / brut[2029]["retraites"]
    return {t: {"depenses_md": brut[t]["depenses"] * k, "retraites_millions": brut[t]["retraites"] * kn / 1e6} for t in ANNEES}


def serie(p: Parametres) -> dict[int, dict[str, float]]:
    """Dépenses de l'ancien système (Md€ de 2026) et nombre de ses retraités (millions), par année."""
    cache = p.__dict__.setdefault("_cache", {})
    if "ancien_systeme" in cache:
        return cache["ancien_systeme"]
    if p.val("ancien_systeme.par_generation") and p.val("demographie.active"):
        out = par_generation(p)
    else:
        v = _csv_v235()
        cor = dict(zip(ANNEES, p.val("anciennes_pensions.retraites_ancien_2029_millions")))
        out = {t: {"depenses_md": v[t]["depenses_desindexees_md"] * v[t]["part_ancien_systeme"],
                   "retraites_millions": cor[t] * v[t]["part_ancien_systeme"]} for t in ANNEES}
    cache["ancien_systeme"] = out
    return out


def depenses(p: Parametres) -> dict[int, float]:
    return {t: x["depenses_md"] for t, x in serie(p).items()}
