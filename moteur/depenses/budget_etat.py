"""Budget de l'État 2026 mission par mission (feuille Budget État 2026, lignes 11 à 67).

Le coût d'une mission conservée = part conservée × (crédits hors salaires + salaires alignés),
les salaires alignés étant le brut × (1 + charges patronales du privé), sans CAS Pensions.
"""
from __future__ import annotations

import csv

from ..distribution import DONNEES
from ..parametres import Parametres


def _missions():
    with (DONNEES / "missions_etat_2026.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _travail():
    with (DONNEES / "mission_travail_2026.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def couts_par_mission(p: Parametres) -> list[dict]:
    t = p.val("alignement.charges_patronales_prive")
    ms = _missions()
    defense = p.val("budget_etat.lpm_2030_courants") / (1 + p.val("budget_etat.inflation_2026_2030"))
    for m in ms:
        m["credits"] = defense if m["credits"] == "calcul" else float(m["credits"])
        m["titre2"] = float(m["titre2"])
    cas_sources = sum(float(m["cas_pensions"]) for m in ms if m["cas_source"] == "s")
    t2_reparti = sum(m["titre2"] for m in ms if m["cas_source"] == "r")
    reste_cas = p.val("budget_etat.cas_pensions_2026") - cas_sources
    for m in ms:
        m["cas"] = reste_cas * m["titre2"] / t2_reparti if m["cas_pensions"] == "calcul" else float(m["cas_pensions"])
        m["hors_cas"] = m["titre2"] - m["cas"]
    brut_par_euro = p.val("alignement.remunerations_activite_etat_2026") / sum(m["hors_cas"] for m in ms)
    out = []
    for m in ms:
        hors_salaires = m["credits"] - (m["hors_cas"] if m["mission"] == "Défense" else m["titre2"])
        aligne = m["hors_cas"] * brut_par_euro * (1 + t)
        if m["part_conservee"] == "calcul":  # Travail : part conservée = postes gardés ligne par ligne
            tr = _travail()
            gardes = 0.0
            for x in tr:
                credits = 2.0594 - m["titre2"] if x["credits"] == "calcul" else float(x["credits"])
                gardes += credits * float(x["part_conservee"])
            part = (gardes + aligne) / (hors_salaires + aligne)
        else:
            part = float(m["part_conservee"])
        out.append({"mission": m["mission"], "ligne": m["ligne_modele"], "cout": part * (hors_salaires + aligne)})
    return out


def baisse_cout_agents_etat(p: Parametres) -> float:
    return (p.val("alignement.remunerations_activite_etat_2026") * (1 + p.val("alignement.charges_patronales_prive"))
            / p.val("alignement.masse_salariale_etat_2026") - 1)


def lignes_modele(p: Parametres) -> dict[str, float]:
    """Totaux par ligne du modèle, en Md€ (Budget État 2026!B53:B66)."""
    out: dict[str, float] = {}
    for m in couts_par_mission(p):
        out[m["ligne"]] = out.get(m["ligne"], 0.0) + m["cout"]
    recherche = next(float(m["credits"]) for m in _missions() if m["ligne_modele"] == "Recherche")
    out["Éducation"] += p.val("budget_etat.apprentissage") + (p.val("budget_etat.eleves_prive") * p.val("budget_etat.part_eleves_retour_public")
                                                             * p.val("budget_etat.cout_eleve_public") / 1e9)
    out["Recherche"] += recherche * p.val("budget_etat.part_salariale_recherche") * baisse_cout_agents_etat(p)
    out["Contribution UE"] = p.val("budget_etat.contribution_ue_courants") / p.val("budget_etat.deflateur_contribution_ue")
    return out
