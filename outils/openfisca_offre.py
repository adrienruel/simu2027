"""Tables d'OpenFisca-France pour l'offre de travail (6 novembre 2026) : revenu disponible selon le salaire, pour une
personne seule et pour un second apporteur dans un couple, dans le système actuel et pour chaque réforme du travail
des programmes.

Le moteur lit ces tables (moteur/offre.py) : pour chaque cellule de salaire, il compare le gain à travailler
(revenu disponible au salaire de la cellule moins revenu disponible sans salaire) et le taux marginal, avant et après
la réforme. Le moteur n'a pas besoin d'OpenFisca pour tourner : ce script régénère les tables.

Cas types (législation 2026, revenus identiques les deux années précédentes) :
- seul : personne seule sans enfant, locataire du parc privé en zone 2, loyer de 550 € par mois (comme
  outils/openfisca_actuel.py) ;
- couples : couple marié, locataire en zone 2, loyer de 750 € par mois ; le salaire de la grille est celui du second
  apporteur ; neuf cas : conjoint à 18 000, 30 000 ou 55 000 € brut par an (≈ 2e décile, médiane, 8e décile des
  salaires à temps complet, Insee) × zéro, un ou deux enfants (8 et 11 ans). Le moteur les pondère (offre.couples_cas).

Réformes (paramètres d'OpenFisca modifiés, rien d'autre) :
- csg_activite_supprimee : CSG sur les revenus d'activité à 0 (déductible et imposable) — Zemmour ;
- csg_activite_plus1 : CSG déductible sur les revenus d'activité +1 point — Tondelier (COT-04) ;
- ir_tranche_11_a_9 : tranche à 11 % de l'impôt sur le revenu ramenée à 9 % — Bertrand, Tondelier (REC-11) ;
- ir_tranche_60 : tranche à 60 % au-delà de 250 000 € par part — Tondelier (REC-10) ;
- allegements_1_6_smic : réduction générale des cotisations patronales arrêtée à 1,6 SMIC au lieu de 3 — Tondelier
  (REC-37) ;
- cotisation_au_dessus_pss : cotisation vieillesse salariale +1 point au-delà du plafond de la Sécurité sociale —
  Tondelier (COT-01) ;
- cotisations_vieillesse_plus1 : cotisations vieillesse déplafonnées +0,5 point salarié et +0,5 point employeur —
  Tondelier (COT-02, +0,2 point par an pendant cinq ans).

    python -m outils.openfisca_offre
"""
from __future__ import annotations

import csv
from pathlib import Path

from outils.openfisca_actuel import grille_bruts

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "parametres" / "donnees"
CONJOINTS = (18000.0, 30000.0, 55000.0)
ENFANTS = (0, 1, 2)
CAS_COUPLES = [(c, e) for c in CONJOINTS for e in ENFANTS]
REFORMES = ("actuel", "csg_activite_supprimee", "csg_activite_plus1", "ir_tranche_11_a_9", "ir_tranche_60",
            "allegements_1_6_smic", "cotisation_au_dessus_pss", "cotisations_vieillesse_plus1")


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
        elif nom == "allegements_1_6_smic":
            params.prelevements_sociaux.reductions_cotisations_sociales.allegement_general.ensemble_des_entreprises \
                .plafond.update(start=debut, value=1.6)
        elif nom == "cotisation_au_dessus_pss":
            c = params.prelevements_sociaux.cotisations_securite_sociale_regime_general.cnav.salarie.vieillesse_plafonnee
            c.brackets[1].rate.update(start=debut, value=0.01)
        elif nom == "cotisations_vieillesse_plus1":
            c = params.prelevements_sociaux.cotisations_securite_sociale_regime_general.cnav
            c.salarie.vieillesse_deplafonnee.brackets[0].rate.update(start=debut, value=0.004 + 0.005)
            c.employeur.vieillesse_deplafonnee.brackets[0].rate.update(start=debut, value=0.0211 + 0.005)
        else:
            raise ValueError(nom)
        return params

    class R(Reform):
        def apply(self):
            self.modify_parameters(modifier_function=modifier)
    return R(tbs)


def _cas(bruts: list[float], couple: tuple | None, annee: int) -> dict:
    an = str(annee)
    annees = [str(annee - 2), str(annee - 1), an]
    ind, foy, men, fam = {}, {}, {}, {}
    for k, b in enumerate(bruts):
        ind[f"i{k}"] = {"salaire_de_base": {y: b for y in annees}}
        if couple is None:
            foy[f"f{k}"] = {"declarants": [f"i{k}"]}
            men[f"m{k}"] = {"personne_de_reference": [f"i{k}"], "statut_occupation_logement": {y: "locataire_vide" for y in annees},
                            "loyer": {y: 12 * 550.0 for y in annees}, "zone_apl": {y: "zone_2" for y in annees}}
            fam[f"fa{k}"] = {"parents": [f"i{k}"]}
        else:
            conj, nb = couple
            ind[f"c{k}"] = {"salaire_de_base": {y: conj for y in annees}, "statut_marital": {y: "marie" for y in annees}}
            ind[f"i{k}"]["statut_marital"] = {y: "marie" for y in annees}
            enfants = [f"e{k}_{j}" for j in range(nb)]
            for j, e in enumerate(enfants):
                ind[e] = {"date_naissance": {an: f"{annee - 8 - 3 * j}-01-01"}}
            foy[f"f{k}"] = {"declarants": [f"c{k}", f"i{k}"], "personnes_a_charge": enfants}
            men[f"m{k}"] = {"personne_de_reference": [f"c{k}"], "conjoint": [f"i{k}"], "enfants": enfants,
                            "statut_occupation_logement": {y: "locataire_vide" for y in annees},
                            "loyer": {y: 12 * 750.0 for y in annees}, "zone_apl": {y: "zone_2" for y in annees}}
            fam[f"fa{k}"] = {"parents": [f"c{k}", f"i{k}"], "enfants": enfants}
    return {"individus": ind, "foyers_fiscaux": foy, "menages": men, "familles": fam}


def colonne_couple(conj: float, enfants: int) -> str:
    return f"couple_{int(conj / 1000)}k_{enfants}e"


def calculer(nom: str, annee: int = 2026) -> list[dict]:
    from openfisca_core.simulation_builder import SimulationBuilder
    tbs = systeme(nom)
    bruts = grille_bruts()
    an = str(annee)
    out = {b: {"brut": b} for b in bruts}
    for cas in (None, *CAS_COUPLES):
        sim = SimulationBuilder().build_from_entities(tbs, _cas(bruts, cas, annee))
        disp = sim.calculate_add("revenu_disponible", an)
        ir = sim.calculate_add("impot_revenu_restant_a_payer", an)
        if cas is None:
            cout = sim.calculate_add("cout_du_travail", an)
            net = sim.calculate_add("salaire_net", an)
            for k, b in enumerate(bruts):
                out[b].update({"cout_du_travail": float(cout[k]), "net_apres_ir_seul": float(net[k]) + float(ir[k]),
                               "disponible_seul": float(disp[k]), "ir_seul": -float(ir[k])})
        else:
            col = colonne_couple(*cas)
            for k, b in enumerate(bruts):
                out[b][f"disponible_{col}"] = float(disp[k])
                out[b][f"ir_{col}"] = -float(ir[k])
    return list(out.values())


def ecrire(nom: str, annee: int = 2026) -> Path:
    lignes = calculer(nom, annee)
    sortie = DONNEES / f"openfisca_offre_{nom}_{annee}.csv"
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        for l in lignes:
            w.writerow({k: round(v, 2) for k, v in l.items()})
    return sortie


if __name__ == "__main__":
    for r in REFORMES:
        print(f"Écrit : {ecrire(r)}")
