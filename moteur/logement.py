"""Logement : reprise des amortissements à la revente (feuille Logement, section 9)."""
from __future__ import annotations

import math

from .parametres import Parametres

ANNEES = list(range(2029, 2074))


def reprise_amortissements(p: Parametres, scenario: str = "prudent") -> dict[int, float]:
    """Recette d'IS sur les amortissements repris à la revente (Md€) : 2,5 % du stock accumulé depuis 2029."""
    amort = p.val("revenus_capital.loyers") * p.val("logement.amortissement_loyers")
    from .is_bareme import taux_moyen
    t_is = taux_moyen(p, scenario)
    return {t: p.val("logement_dynamique.part_amortissements_repris") * amort
            * (1 - math.exp(-p.val("logement_dynamique.part_parc_vendue_par_an") * (t - 2029))) * t_is for t in ANNEES}
