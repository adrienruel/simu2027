"""Ascenseur social : dépenses et recettes année par année (feuille Ascenseur social, lignes 50 à 106)."""
from __future__ import annotations

from .parametres import Parametres

ANNEES = list(range(2029, 2074))


def _rampe(t, debut, annees):
    return min(1.0, max(0.0, (t - debut + 1) / annees))


def annuel(p: Parametres, droits_succession_md: float, exoneration_entreprises_md: float) -> dict[int, dict]:
    g = p.val("macro.tendance", "prudent")
    c12, bac, pr = p.val("ascenseur.classes_12"), p.val("ascenseur.bac_tout_age"), p.val("ascenseur.prepas")
    sc, av, ing = p.val("ascenseur.succession_cumul"), p.val("ascenseur.assurance_vie"), p.val("ascenseur.ecoles_ingenieurs")
    cout_12 = c12["niveaux"] * c12["part_supplementaire"] * c12["eleves_par_niveau"] * (1 / c12["eleves_dedoublee"] - 1 / c12["eleves_ordinaire"]) * c12["cout_enseignant"] / 1e9
    cout_bac = bac["candidats"] * bac["cout_2010"] * bac["inflation_2010_2026"] / 1e9
    recette_prepa = pr["etudiants"] * (pr["etudiants_public"] / pr["etudiants"]) * pr["cout_annuel"] * pr["part_facturee"] * pr["part_remboursee"] / 1e9
    nouveaux = ing["inscrits"] * (1 - ing["part_apprentissage"]) / ing["duree"] - ing["eleves_fonctionnaires"]
    ing_autres = nouveaux * (1 - ing["part_prepa"]) * ing["depense_par_eleve"] * ing["duree"] * ing["rembourse_autres"] / 1e9
    ing_prepa = nouveaux * ing["part_prepa"] * ing["depense_par_eleve"] * ing["duree"] * ing["rembourse_prepa"] / 1e9
    out = {}
    for t in ANNEES:
        n = t - 2029
        cr = (1 + g) ** n
        dep = cout_12 * min(1, (n + 1) / c12["montee"]) * cr + cout_bac * cr
        rec = (recette_prepa * _rampe(t, pr["premiere_annee"], pr["montee"]) * cr
               + droits_succession_md * sc["gain"] * (sc["part_immediate"] + (1 - sc["part_immediate"]) * min(1, n / sc["annees_plein_effet"])) * cr
               + exoneration_entreprises_md * p.val("ascenseur.plafond_exoneration_entreprises")["part_recuperee"] * cr
               + av["recette"] * (1 - av["part_perdue"]) * min(1, av["part_premiere_annee"] + (1 - av["part_premiere_annee"]) * n / av["annees_plein_effet"]) * cr
               + (ing_autres * _rampe(t, ing["debut_autres"], ing["montee_autres"]) + ing_prepa * _rampe(t, ing["debut_prepa"], ing["montee_prepa"])) * cr)
        out[t] = {"depenses": dep, "recettes": rec}
    return out
