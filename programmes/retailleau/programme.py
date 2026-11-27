"""Programme de Bruno Retailleau (Les Républicains), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : livrets « Nos propositions pour la France » (LR, janvier à septembre 2026), entretiens et communiqués,
recensés par programmes-2027.fr (93 mesures) ; fiche : mesures.yaml. Les économies annoncées (197 Md€) ne sont pas
reprises : seules les mesures nommées sont estimées.

- **mesures simples** (groupe retailleau_mesures) ;
- **mesures calculées** :
  - retraite : âge minimal de 63 ans avec décote et taux plein automatique ramené à 65 ans : solde net estimé
    (relecture neutre du 11/11/2026 : ce n'est pas un report de l'âge à 65 ans) ;
  - restitution aux salariés (13 Md€ de cotisations salariales en moins, plus le « zéro cotisation » des mesures
    simples) : moteur/bibliotheque.baisse_prelevements_salaries ;
  - chômage plus bas avec l'assurance chômage resserrée ;
  - part de capitalisation obligatoire (1 % du brut des nouveaux entrants, phase 2 du 11/11/2026) : hors budget,
    sauf la part des employeurs publics ; emplois perdus par le coût du travail et le salaire net (canal d'offre).

    python -m moteur.noyau retailleau
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ProgrammeSimple


class Retailleau(ProgrammeSimple):
    nom = "retailleau"
    libelle = "Retailleau (Les Républicains)"

    def mesures_calculees(self, p, s, idx):
        canaux = {}
        # RET-RET-01 : âge minimal de 63 ans avec décote, taux plein à 65 ans (au lieu de 67) : solde net estimé
        sol = self.v("retraites.solde_reforme", s)
        d0, d1 = self.v("retraites.debut"), self.v("retraites.plein")

        def mont(t):
            return min(1.0, max(0.0, (t - d0 + 1) / (d1 - d0 + 1)))
        out = [Mesure("RET-RET-01 — âge minimal de 63 ans avec décote, taux plein automatique à 65 ans (solde net)",
                      "retraites", {2027: 0.0, 2028: 0.0, **{t: -sol * mont(t) * idx["pib"][t] for t in ANNEES}})]
        out += bib.baisse_prelevements_salaries(
            p, idx, self.v("restitution.baisse_salaries"), self.v("restitution.part_ir_retrouvee", s),
            self.v("restitution.premiere_annee"), "RET-ECO-06 — restitution aux salariés : cotisations salariales en moins")
        e = sq.effectifs(p, s)
        h = -self.effet_ac(s)
        canaux["Assurance chômage resserrée : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        out_c, emplois_c = self.capitalisation(p, s)
        out += out_c
        canaux["Capitalisation obligatoire : emplois (coût du travail et salaire net)"] = emplois_c
        return out, canaux

    def capitalisation(self, p, s):
        """RET-RET-02 : 1 % du brut des entrants depuis 2028, moitié salarié, moitié employeur (règle commune :
        bibliotheque.capitalisation_obligatoire)."""
        return bib.capitalisation_obligatoire(p, s, self.v("capitalisation.cotisation"), "RET-RET-02")


def programme() -> Retailleau:
    return Retailleau()
