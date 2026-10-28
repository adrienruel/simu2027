"""Épargne obligatoire, capital accumulé et revenu du capital à la retraite.

Reproduit les colonnes AX–BB (privé) et AZ–BD (public) des feuilles de la v235,
et la feuille Socle actuariel (B8, B16).
"""
from __future__ import annotations

import math

from .impot_unique import impot
from .parametres import Parametres


def taux_epargne(cout_employeur: float, p: Parametres) -> float:
    """0 % au SMIC, taux plein à k × SMIC, linéaire entre les deux (en coût employeur mensuel)."""
    smic = p.val("epargne.cout_smic_mensuel")
    k = p.val("epargne.multiple_smic_taux_plein")
    x = (cout_employeur / 12 - smic) / ((k - 1) * smic)
    return p.val("epargne.taux_plein") * min(1.0, max(0.0, x))


def capital_par_euro_de_rente(p: Parametres) -> float:
    """Prix d'une rente viagère de 1 €/an à l'âge d'accès (mortalité de Gompertz, 55 ans)."""
    a, b = p.val("epargne.gompertz_a"), p.val("epargne.gompertz_b")
    x0, r = p.val("epargne.age_acces_socle"), p.val("epargne.rendement_fonds")
    total = 0.0
    for k in range(1, 56):
        t = k - 0.5
        survie = math.exp(-a / b * (math.exp(b * (x0 + t)) - math.exp(b * x0)))
        total += survie / (1 + r) ** t
    return total


def revenu_par_euro_de_capital(p: Parametres) -> float:
    """Moitié en rente viagère, moitié conservée et placée au rendement du fonds."""
    part = p.val("epargne.part_rente_viagere")
    return (1 - part) * p.val("epargne.rendement_fonds") + part / capital_par_euro_de_rente(p)


def valeur_future(taux_mensuel: float, n_mois: int, versement: float) -> float:
    """Équivalent de FV(taux, n, -versement, 0) d'Excel (versements en fin de période)."""
    if taux_mensuel == 0:
        return versement * n_mois
    return versement * ((1 + taux_mensuel) ** n_mois - 1) / taux_mensuel


def rente_mensuelle(epargne_annuelle: float, p: Parametres) -> float:
    """Revenu mensuel du capital à la retraite, pour une épargne annuelle constante."""
    r = p.val("epargne.rendement_fonds")
    n = p.val("epargne.annees_carriere")
    cap = valeur_future(r / 12, n * 12, epargne_annuelle / 12)
    return cap * p.val("epargne.taux_emploi_carriere") * revenu_par_euro_de_capital(p) / 12


def part_rui_salarie(cout_employeur: float, p: Parametres) -> float:
    """Part du RUI conservée par un salarié : 1 − coût / coût d'un SMIC à temps plein."""
    return max(0.0, 1 - cout_employeur / (p.val("epargne.cout_smic_mensuel") * 12))


def net_apres_impot(cout_employeur: float, p: Parametres, scenario: str = "prudent",
                    part_rui: float | None = None) -> float:
    if part_rui is None:
        part_rui = part_rui_salarie(cout_employeur, p)
    return cout_employeur - impot(cout_employeur, p, scenario) + part_rui * p.val("rui.montant") * 12


def epargne_annuelle(cout_employeur: float, p: Parametres, scenario: str = "prudent",
                     part_rui: float | None = None, contribution: bool = True) -> float:
    """Épargne obligatoire versée au compte (après contribution de transition éventuelle)."""
    e = taux_epargne(cout_employeur, p) * net_apres_impot(cout_employeur, p, scenario, part_rui)
    if contribution:
        e *= 1 - p.val("epargne.contribution_transition")
    return e
