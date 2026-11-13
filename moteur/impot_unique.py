"""Impôt unique sur le revenu : barème par tranches sur le coût employeur annuel.

Personne seule. Le traitement des couples et des enfants (quotient plafonné) sera
codé avec OpenFisca à l'étape 3, une fois sa mécanique précisée.
"""
from __future__ import annotations

from .parametres import Parametres


def bareme(p: Parametres, scenario: str = "prudent") -> tuple[list[float], list[float]]:
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("bareme_impot_unique", scenario)
    if cle not in cache:
        cache[cle] = _bareme(p, scenario)
    return cache[cle]


def _bareme(p: Parametres, scenario: str) -> tuple[list[float], list[float]]:
    seuils = list(p.val("impot_unique.seuils", scenario))
    taux = list(p.val("impot_unique.taux", scenario))
    if len(taux) != len(seuils) + 1:
        raise ValueError("Il faut un taux de plus que de seuils")
    if seuils != sorted(seuils):
        raise ValueError("Seuils non croissants")
    plafond = p.val("impot_unique.plafond_taux_marginal", scenario)
    if max(taux) > plafond + 1e-12:
        raise ValueError(f"Taux marginal {max(taux)} au-dessus du plafond {plafond}")
    return seuils, taux


def impot(cout_employeur_annuel: float, p: Parametres, scenario: str = "prudent") -> float:
    """Impôt annuel dû sur un coût employeur annuel (euros de 2026)."""
    seuils, taux = bareme(p, scenario)
    bornes = [0.0, *seuils, float("inf")]
    du = 0.0
    for bas, haut, t in zip(bornes[:-1], bornes[1:], taux):
        if cout_employeur_annuel > bas:
            du += (min(cout_employeur_annuel, haut) - bas) * t
    return du


def taux_marginal(cout_employeur_annuel: float, p: Parametres, scenario: str = "prudent") -> float:
    seuils, taux = bareme(p, scenario)
    for s, t in zip(seuils, taux):
        if cout_employeur_annuel <= s:
            return t
    return taux[-1]
