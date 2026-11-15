"""Liens du moteur avec la microsimulation (phase F4, outils/vieillissement.py).

Mesures de recettes codées dans OpenFisca : leur montant (calé sur la population de 2026) suit, année après année,
l'indice que donne la population vieillie du programme (effet statique de la mesure l'année t / en 2026), en unités
de salaire de 2026 : composition par âge, emploi, retraités et pensions du programme. Années clés de la micro
interpolées ; avant la première, son indice ; après la dernière, le dernier.
"""
from __future__ import annotations

import csv

from .parametres import RACINE, Parametres

_TABLE: dict | None = None


def table() -> dict:
    global _TABLE
    if _TABLE is None:
        _TABLE = {}
        f = RACINE / "parametres" / "donnees" / "micro_recettes_annees.csv"
        if f.exists():
            with f.open(encoding="utf-8") as g:
                for l in csv.DictReader(g):
                    _TABLE.setdefault((l["programme"], l["mesure"]), {})[int(l["annee"])] = float(l["indice"])
    return _TABLE


def indice(p: Parametres, programme: str, ident: str, t: int) -> float:
    """Indice de la mesure en t (1 si la micro ne la couvre pas ou si l'option est désactivée)."""
    if not p.val("microsimulation.recettes_vieillies"):
        return 1.0
    x = table().get((programme, ident))
    if not x:
        return 1.0
    ans = sorted(x)
    if t <= ans[0]:
        return x[ans[0]]
    if t >= ans[-1]:
        return x[ans[-1]]
    for a, b in zip(ans, ans[1:]):
        if a <= t <= b:
            return x[a] + (x[b] - x[a]) * (t - a) / (b - a)
    return 1.0
