"""Droits de succession : effet du nombre de décès (feuille Successions).

Les droits suivent le nombre de décès, à barème et patrimoine moyen constants ; le nombre de décès
est interpolé linéairement entre les repères, puis gardé constant après le dernier.
"""
from __future__ import annotations

from ..parametres import Parametres

ANNEES = list(range(2029, 2074))


def deces(p: Parametres, annee: int) -> float:
    r = sorted((int(k), v) for k, v in p.val("deces.reperes").items())
    if annee >= r[-1][0]:
        return r[-1][1]
    i = max(j for j, (a, _) in enumerate(r) if a <= annee)
    (a0, d0), (a1, d1) = r[i], r[i + 1]
    return d0 + (d1 - d0) * (annee - a0) / (a1 - a0)


def supplement(p: Parametres, base_md: float) -> dict[int, float]:
    """Recettes supplémentaires par rapport à l'année de référence (Md€)."""
    ref = deces(p, p.val("deces.annee_reference"))
    g = p.val("macro.tendance", "prudent")
    return {t: base_md * (1 + g) ** (t - 2029) * (deces(p, t) / ref - 1) for t in ANNEES}
