"""Assemblage des lignes de recettes de la feuille Total (nouveau système, statique, €)."""
from __future__ import annotations

from ..parametres import Parametres
from . import entreprises, impot_salaires, independants, retraites_croisiere, tva_menages


def ligne_2_is(p: Parametres, scenario: str = "prudent") -> float:
    """IS de l'État (bénéficiaires + déficitaires passant en bénéfice), en euros de 2024."""
    return entreprises.is_beneficiaires(p, scenario) + entreprises.is_deficitaires(p, scenario)


def ligne_3_tva(p: Parametres, scenario: str = "prudent") -> float:
    """TVA et accises sur la consommation, y compris la TVA non déductible des entreprises (€ de 2024)."""
    return (tva_menages.tva_prive(p, scenario) + tva_menages.tva_public(p, scenario)
            + tva_menages.tva_retraites(p, scenario) + tva_menages.tva_etudiants(p)
            + tva_menages.tva_inactifs(p) + tva_menages.tva_chomeurs(p)
            + entreprises.tva_non_deductible(p, scenario) + independants.tva_independants(p, scenario))


def lignes_calculees(p: Parametres, scenario: str = "prudent") -> dict[int, float]:
    return {
        2: ligne_2_is(p, scenario),
        3: ligne_3_tva(p, scenario),
        4: impot_salaires.impot_prive(p, scenario),
        5: retraites_croisiere.impot_retraites(p, scenario),
        6: impot_salaires.impot_public(p, scenario),
        16: independants.ligne_16(p, scenario),
    }


def recettes_nouveau_systeme(p: Parametres, scenario: str = "prudent") -> dict:
    """Recettes statiques du nouveau système (Total!B17), en euros de 2026.

    Les lignes calées sur des montants de 2024 passent par le facteur de recettes (une seule fois) ;
    les lignes calculées sur les distributions de 2026 et la contribution d'épargne n'y passent pas.
    """
    from ..unites import facteur
    from . import autres
    l = lignes_calculees(p, scenario)
    tva_ent = entreprises.tva_non_deductible(p, scenario)
    l[7] = autres.ligne_7_dividendes(p)
    l[8] = autres.ligne_8_successions(p)
    l[9] = autres.ligne_9_contribution(p)
    l[15] = autres.ligne_15_accises_entreprises(p, l[3], scenario)
    l[19] = autres.ligne_19_revenus_capital(p)
    l[20] = autres.ligne_20_bailleurs(p, scenario)
    en_2024 = l[2] + l[7] + l[8] + l[15] + l[19] + l[20] + tva_ent
    en_2026 = (l[3] - tva_ent) + l[4] + l[5] + l[6] + l[9] + l[16]
    return {"lignes": l, "total": en_2024 * facteur(p, 2024, "recettes") + en_2026}
