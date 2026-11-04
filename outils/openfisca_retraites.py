"""Prélèvements sur les pensions du système actuel, calculés par OpenFisca-France (statu quo, 4 novembre 2026).

Sur une grille de pensions brutes mensuelles (retraités de 70 ans, propriétaires, sans enfant à charge) :
- personne seule ;
- couple marié de deux retraités, le conjoint touchant statu_quo.retraites_ratio_conjoint × la pension (calcul du
  foyer, rapporté à la pension de la personne de la grille au prorata des pensions).
Variables : CSG (déductible et imposable), CRDS, CASA, impôt sur le revenu, pension nette. Les revenus des deux
années précédentes sont identiques (le taux de CSG dépend du revenu fiscal de référence de l'avant-dernière année).

    python -m outils.openfisca_retraites          # écrit parametres/donnees/openfisca_retraites_2026.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RATIO_CONJOINT = 0.62  # copie de statu_quo.retraites_ratio_conjoint (pension du conjoint / pension de la grille)


def grille_mensuelle() -> list[float]:
    return [float(x) for x in list(range(0, 3000, 50)) + list(range(3000, 6000, 100)) + list(range(6000, 15001, 500))]


def _calculer(annee: int, couple: bool) -> list[dict]:
    from openfisca_core.simulation_builder import SimulationBuilder
    from openfisca_france import FranceTaxBenefitSystem
    tbs = FranceTaxBenefitSystem()
    g = grille_mensuelle()
    an = str(annee)
    mois = [f"{y}-{m:02d}" for y in (annee - 2, annee - 1, annee) for m in range(1, 13)]
    naissance = f"{annee - 70}-01-01"
    ind, foy, men, fam = {}, {}, {}, {}
    for k, pm in enumerate(g):
        ind[f"a{k}"] = {"retraite_brute": {m: pm for m in mois}, "date_naissance": {"ETERNITY": naissance}}
        membres = [f"a{k}"]
        if couple:
            ind[f"b{k}"] = {"retraite_brute": {m: pm * RATIO_CONJOINT for m in mois}, "date_naissance": {"ETERNITY": naissance}}
            membres.append(f"b{k}")
            for i in membres:
                ind[i]["statut_marital"] = {m: "marie" for m in mois}
        foy[f"f{k}"] = {"declarants": membres}
        men[f"m{k}"] = {"personne_de_reference": [f"a{k}"], **({"conjoint": [f"b{k}"]} if couple else {}),
                        "statut_occupation_logement": {an: "proprietaire"}}
        fam[f"fa{k}"] = {"parents": membres}
    sim = SimulationBuilder().build_from_entities(tbs, {"individus": ind, "foyers_fiscaux": foy, "menages": men, "familles": fam})
    def indiv(v):
        return sim.calculate_add(v, an)
    csg = -(indiv("csg_deductible_retraite") + indiv("csg_imposable_retraite"))
    crds, casa = -indiv("crds_retraite"), -indiv("casa")
    ir = -sim.calculate("impot_revenu_restant_a_payer", an)  # par foyer, positif = impôt payé
    pas = 2 if couple else 1
    lignes = []
    for k, pm in enumerate(g):
        idx = [pas * k + j for j in range(pas)]
        brut = 12 * pm * (1 + (RATIO_CONJOINT if couple else 0))
        prelev_sociaux = sum(csg[i] + crds[i] + casa[i] for i in idx)
        part = 1 / (1 + (RATIO_CONJOINT if couple else 0))  # part de la personne de la grille dans le foyer
        lignes.append({"pension_brute_mensuelle": pm,
                       "prelevements_sociaux": prelev_sociaux * part,
                       "impot_revenu": max(0.0, float(ir[k])) * part,
                       "taux_total": (prelev_sociaux + max(0.0, float(ir[k]))) / brut if brut else 0.0})
    return lignes


def ecrire(annee: int = 2026) -> Path:
    sortie = RACINE / "parametres" / "donnees" / f"openfisca_retraites_{annee}.csv"
    seul, couple = _calculer(annee, False), _calculer(annee, True)
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pension_brute_mensuelle", "seul_prelevements_sociaux", "seul_impot_revenu",
                    "couple_prelevements_sociaux", "couple_impot_revenu"])
        for a, b in zip(seul, couple):
            w.writerow([a["pension_brute_mensuelle"], round(a["prelevements_sociaux"], 2), round(a["impot_revenu"], 2),
                        round(b["prelevements_sociaux"], 2), round(b["impot_revenu"], 2)])
    return sortie


if __name__ == "__main__":
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    print(f"Écrit : {ecrire(a)}")
