"""Mesures annuelles de la feuille Objectifs : TVA de 2028, fin du gel, RUI des étudiants."""
from __future__ import annotations

from .parametres import Parametres
from .retraites_transition import _csv as _csv_retraites

ANNEES = list(range(2029, 2074))


def surcroit_tva_2028(p: Parametres, t: int) -> tuple[float, float]:
    """(recette maintenue, montant rendu par le barème) pour l'année t (Objectifs lignes 15 et 63)."""
    g = p.val("macro.tendance", "prudent")
    b5, b6, b7 = p.val("objectifs.surcroit_tva_2028"), p.val("objectifs.tva_derniere_annee_pleine"), p.val("objectifs.tva_annees_extinction")
    rendu_active = p.val("objectifs.tva_rendue_par_bareme")
    base = b5 * (1 + g) ** (t - 2029)
    maintenu = base * (1 if t <= b6 else (1 if rendu_active else max(0, 1 - (t - b6) / b7)))
    rendu = base * (0 if t <= b6 else 1 - max(0, 1 - (t - b6) / b7)) if rendu_active else 0.0
    return maintenu, rendu


def fin_gel(p: Parametres, t: int) -> float:
    anc = {int(x["annee"]): x["depenses_desindexees_md"] * x["part_ancien_systeme"] for x in _csv_retraites("ancien_systeme_retraites.csv")}
    part_sous = p.val("revalorisation.part_pensions_sous_seuil") if p.val("revalorisation.pensions_sous_minimum_vieillesse") else 0
    g = p.val("macro.tendance", "prudent")
    return (1 - part_sous) * anc[t] * ((1 + g) ** max(0, t - p.val("objectifs.fin_gel_anciennes_pensions")) - 1)


def demi_rui_chez_parents(p: Parametres) -> float:
    """Économie du demi-RUI des étudiants logés chez leurs parents, nette de la TVA perdue (Budget État!D110)."""
    from .recettes.tva_menages import tva_etudiants
    rui_etu = p.val("inactifs.etudiants") * p.val("rui.montant") * 12 / 1e9
    tva_par_euro = tva_etudiants(p) / (p.val("rui.montant") * 12 * p.val("inactifs.etudiants"))
    return rui_etu * p.val("etudiants_rui.part_chez_parents") * 0.5 * (1 - tva_par_euro)


def rui_etudiants(p: Parametres) -> dict[int, float]:
    """Économie (négatif) du RUI étudiant sous condition de ressources, mis en place génération par génération."""
    rui = p.val("rui.montant") * 12
    regime = (p.val("etudiants_rui.boursiers_rui_plein") + 0.5 * p.val("etudiants_rui.juste_au_dessus_demi_rui")) * rui / 1e9
    sans_condition = p.val("inactifs.etudiants") * rui / 1e9 - demi_rui_chez_parents(p)
    out = {}
    for t in ANNEES:
        part = min(1, max(0, t - 2028) / p.val("etudiants_rui.duree_etudes"))
        out[t] = part * regime + (1 - part) * p.val("etudiants_rui.bourses_actuelles") - sans_condition
    return out
