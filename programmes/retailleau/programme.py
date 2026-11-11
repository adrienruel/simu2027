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
from moteur import offre
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
        h = self.v("chomage.baisse_taux", s)
        canaux["Assurance chômage resserrée : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        out_c, emplois_c = self.capitalisation(p, s)
        out += out_c
        canaux["Capitalisation obligatoire : emplois (coût du travail et salaire net)"] = emplois_c
        return out, canaux

    def capitalisation(self, p, s):
        """RET-RET-02 : 1 % du brut des entrants sur le marché du travail depuis 2028, moitié salarié, moitié
        employeur, versé à un fonds hors des administrations publiques. Budget : seulement la part des employeurs
        publics. Emplois : canal d'offre commun appliqué à la part employeur du privé (coût du travail) et à la part
        salariale (prélèvement sur le travail), comme s'il s'agissait d'une cotisation de plus."""
        c = self.v("capitalisation.cotisation")
        w = sq.salaires(p, s)
        e = sq.effectifs(p, s)
        par_tete = 12 * min(c["taux"] * c["brut_moyen_mensuel"], c["plafond_mensuel"]) / 1e9  # Md€ de 2026 par an
        couverts = {t: min(e[t]["emploi"], c["entrants_par_an"] * c["taux_emploi"] * max(0, t - c["debut"] + 1))
                    for t in ANNEES}
        total = {t: couverts[t] * par_tete * w[t] / w[2029] for t in ANNEES}
        pe, pp = c["part_employeur"], c["part_public"]
        employeur_prive = Mesure("capitalisation (part employeur, privé)", "recettes",
                                 {t: pe * (1 - pp) * total[t] for t in ANNEES}, instrument="cout_travail")
        salariale = Mesure("capitalisation (part salariale)", "recettes",
                           {t: (1 - pe) * total[t] for t in ANNEES}, instrument="travail")
        of = offre.effets(p, s, [employeur_prive, salariale], annees_avant=())
        emplois = {t: sum(serie.get(t, 0.0) for serie in of["emplois"].values()) for t in ANNEES}
        out = [Mesure("RET-RET-02 — part de capitalisation : cotisation des employeurs publics (1 % du brut, moitié)",
                      "etat_missions", {2027: 0.0, 2028: 0.0, **{t: pe * pp * total[t] for t in ANNEES}})]
        return out, emplois


def programme() -> Retailleau:
    return Retailleau()
