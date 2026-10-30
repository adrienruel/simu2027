"""Années 2027 et 2028 avant la bascule (feuille Calendrier budgétaire) : dette au 31 décembre 2028.

La dette est en euros constants de 2026 : chaque année, l'inflation en érode la valeur réelle.
Le PIB de 2027 et 2028 est celui de 2026 (pas de croissance comptée, sens prudent pour le ratio).
"""
from __future__ import annotations

from .parametres import Parametres
from .unites import facteur


def pib_2026(p: Parametres) -> float:
    return 2920 * facteur(p, 2024, "recettes")


def annees_2027_2028(p: Parametres) -> dict[int, dict]:
    pib = pib_2026(p)
    from .inflation import serie as serie_inflation
    deficit = p.val("calendrier.deficit_tendanciel_2027_2028")
    dette = p.val("calendrier.dette_fin_2026_pib") * pib
    mesures_2028 = sum(p.val("calendrier.mesures_2028").values())
    out = {}
    for an, mesures in ((2027, 0.0), (2028, mesures_2028)):
        solde = -deficit * pib + mesures
        dette = dette - solde - serie_inflation(p)[an] * dette
        out[an] = {"pib": pib, "solde": solde, "deficit": -solde / pib * 100, "dette": dette, "dette_pib": dette / pib}
    return out


def dette_fin_2028(p: Parametres) -> float:
    return annees_2027_2028(p)[2028]["dette"]


def transferts_collectivites(p: Parametres) -> float:
    return p.val("calendrier.dotations_collectivites") * p.val("calendrier.part_dotations_versee")
