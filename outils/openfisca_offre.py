"""Tables d'OpenFisca-France pour l'offre de travail (6 novembre 2026) : revenu disponible selon le salaire, pour une
personne seule et pour un second apporteur dans un couple, dans le système actuel et pour chaque réforme du travail
des programmes.

Le moteur lit ces tables (moteur/offre.py) : pour chaque cellule de salaire, il compare le gain à travailler
(revenu disponible au salaire de la cellule moins revenu disponible sans salaire) et le taux marginal, avant et après
la réforme. Le moteur n'a pas besoin d'OpenFisca pour tourner : ce script régénère les tables.

Cas types (législation 2026, revenus identiques les deux années précédentes) :
- seul : personne seule sans enfant, locataire du parc privé en zone 2, loyer de 550 € par mois (comme
  outils/openfisca_actuel.py) ;
- couple : couple marié avec un enfant de 8 ans, locataire en zone 2, loyer de 750 € par mois ; le conjoint gagne
  30 000 € brut par an (≈ salaire médian, Insee) ; le salaire de la grille est celui du second apporteur.

Réformes (paramètres d'OpenFisca modifiés, rien d'autre) :
- csg_activite_supprimee : CSG sur les revenus d'activité à 0 (déductible et imposable) — Zemmour ;
- csg_activite_plus1 : CSG déductible sur les revenus d'activité +1 point — Tondelier (COT-04) ;
- ir_tranche_11_a_9 : tranche à 11 % de l'impôt sur le revenu ramenée à 9 % — Bertrand, Tondelier (REC-11) ;
- ir_tranche_60 : tranche à 60 % au-delà de 250 000 € par part — Tondelier (REC-10).

    python -m outils.openfisca_offre
"""
from __future__ import annotations

import csv
from pathlib import Path

from outils.openfisca_actuel import grille_bruts

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "parametres" / "donnees"
SALAIRE_CONJOINT = 30000.0
REFORMES = ("actuel", "csg_activite_supprimee", "csg_activite_plus1", "ir_tranche_11_a_9", "ir_tranche_60")


def systeme(nom: str):
    from openfisca_core.model_api import Reform
    from openfisca_france import FranceTaxBenefitSystem
    tbs = FranceTaxBenefitSystem()
    if nom == "actuel":
        return tbs
    debut = "2020-01-01"

    def modifier(params):
        a = params.prelevements_sociaux.contributions_sociales.csg.activite
        bareme = params.impot_revenu.bareme_ir_depuis_1945.bareme
        if nom == "csg_activite_supprimee":
            a.deductible.update(start=debut, value=0.0)
            a.imposable.update(start=debut, value=0.0)
            a.taux_global.update(start=debut, value=0.0)
        elif nom == "csg_activite_plus1":
            a.deductible.update(start=debut, value=0.068 + 0.01)
            a.taux_global.update(start=debut, value=0.092 + 0.01)
        elif nom == "ir_tranche_11_a_9":
            bareme.brackets[1].rate.update(start=debut, value=0.09)
        elif nom == "ir_tranche_60":
            from openfisca_core.parameters import ParameterScaleBracket
            b = ParameterScaleBracket("bareme_ir_60", data={"threshold": {debut: {"value": 250000.0}},
                                                             "rate": {debut: {"value": 0.60}}})
            bareme.brackets.append(b)
        else:
            raise ValueError(nom)
        return params

    class R(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=modifier)
    return R(tbs)


def _cas(bruts: list[float], couple: bool, annee: int) -> dict:
    an = str(annee)
    annees = [str(annee - 2), str(annee - 1), an]
    ind, foy, men, fam = {}, {}, {}, {}
    for k, b in enumerate(bruts):
        ind[f"i{k}"] = {"salaire_de_base": {y: b for y in annees}}
        if not couple:
            foy[f"f{k}"] = {"declarants": [f"i{k}"]}
            men[f"m{k}"] = {"personne_de_reference": [f"i{k}"], "statut_occupation_logement": {y: "locataire_vide" for y in annees},
                            "loyer": {y: 12 * 550.0 for y in annees}, "zone_apl": {y: "zone_2" for y in annees}}
            fam[f"fa{k}"] = {"parents": [f"i{k}"]}
        else:
            ind[f"c{k}"] = {"salaire_de_base": {y: SALAIRE_CONJOINT for y in annees},
                            "statut_marital": {y: "marie" for y in annees}}
            ind[f"i{k}"]["statut_marital"] = {y: "marie" for y in annees}
            ind[f"e{k}"] = {"date_naissance": {an: f"{annee - 8}-01-01"}}
            foy[f"f{k}"] = {"declarants": [f"c{k}", f"i{k}"], "personnes_a_charge": [f"e{k}"]}
            men[f"m{k}"] = {"personne_de_reference": [f"c{k}"], "conjoint": [f"i{k}"], "enfants": [f"e{k}"],
                            "statut_occupation_logement": {y: "locataire_vide" for y in annees},
                            "loyer": {y: 12 * 750.0 for y in annees}, "zone_apl": {y: "zone_2" for y in annees}}
            fam[f"fa{k}"] = {"parents": [f"c{k}", f"i{k}"], "enfants": [f"e{k}"]}
    return {"individus": ind, "foyers_fiscaux": foy, "menages": men, "familles": fam}


def calculer(nom: str, annee: int = 2026) -> list[dict]:
    from openfisca_core.simulation_builder import SimulationBuilder
    tbs = systeme(nom)
    bruts = grille_bruts()
    an = str(annee)
    out = {b: {"brut": b} for b in bruts}
    for couple in (False, True):
        sim = SimulationBuilder().build_from_entities(tbs, _cas(bruts, couple, annee))
        disp = sim.calculate_add("revenu_disponible", an)
        cout = sim.calculate_add("cout_du_travail", an)
        if not couple:
            net = sim.calculate_add("salaire_net", an)
            ir = sim.calculate_add("impot_revenu_restant_a_payer", an)
        cle = "couple" if couple else "seul"
        for k, b in enumerate(bruts):
            out[b][f"disponible_{cle}"] = float(disp[k])
            if not couple:
                out[b]["cout_du_travail"] = float(cout[k])
                out[b]["net_apres_ir_seul"] = float(net[k]) + float(ir[k])
    return list(out.values())


def ecrire(nom: str, annee: int = 2026) -> Path:
    lignes = calculer(nom, annee)
    sortie = DONNEES / f"openfisca_offre_{nom}_{annee}.csv"
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["brut", "cout_du_travail", "net_apres_ir_seul", "disponible_seul", "disponible_couple"])
        w.writeheader()
        for l in lignes:
            w.writerow({k: round(v, 2) for k, v in l.items()})
    return sortie


if __name__ == "__main__":
    for r in REFORMES:
        print(f"Écrit : {ecrire(r)}")
