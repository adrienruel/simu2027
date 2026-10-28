"""Non-remplacement des départs dans les fonctions de gestion de l'État (feuilles IA ministères et IA administration)."""
from __future__ import annotations

from ..parametres import Parametres
from .budget_etat import baisse_cout_agents_etat

ANNEES = list(range(2029, 2074))


def masse_gestion(p: Parametres) -> float:
    """Masse salariale alignée des fonctions de gestion (Md€)."""
    eff, part = p.val("ia.effectifs_etat"), p.val("ia.part_gestion")
    masse = p.val("alignement.masse_salariale_etat_2026") * (1 + baisse_cout_agents_etat(p))
    cout_agent = masse * 1e9 / sum(eff.values())
    return sum(eff[k] * part[k] for k in eff) * cout_agent / 1e9


def economie_nette(p: Parametres) -> dict[int, float]:
    """Économie nette annuelle (Md€, niveau de 2026, avant croissance)."""
    m = masse_gestion(p)
    out = {}
    for an in ANNEES:
        baisse = min(p.val("ia.plafond_taches_automatisables"),
                     max(0, an - p.val("ia.premiere_annee") + 1) * p.val("ia.departs_retraite_annuels") * p.val("ia.part_departs_non_remplaces"))
        out[an] = m * baisse * (1 - p.val("ia.cout_services_ia"))
    return out


def economie_moyenne(p: Parametres) -> float:
    e = economie_nette(p)
    return sum(e.values()) / len(e)
