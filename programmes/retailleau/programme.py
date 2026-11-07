"""Programme de Bruno Retailleau (Les Républicains), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : livrets « Nos propositions pour la France » (LR, janvier à septembre 2026), entretiens et communiqués,
recensés par programmes-2027.fr (93 mesures) ; fiche : mesures.yaml. Les économies annoncées (197 Md€) ne sont pas
reprises : seules les mesures nommées sont estimées.

- **mesures simples** (groupe retailleau_mesures) ;
- **mesures calculées** :
  - retraite : taux plein à 65 ans, départs dès 63 ans avec décote (moteur/bibliotheque.report_age_legal_detail, même
    lecture que Bertrand), emploi des seniors ;
  - restitution aux salariés (13 Md€ de cotisations salariales en moins, plus le « zéro cotisation » des mesures
    simples) : moteur/bibliotheque.baisse_prelevements_salaries ;
  - chômage plus bas avec l'assurance chômage resserrée.

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
        det = bib.report_age_legal_detail(p, s, self.v("retraites.age_cible"), self.v("retraites.premiere_generation"),
                                          self.v("retraites.pas_par_generation"))
        k = self.v("retraites.part_economie_gardee", s)
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": {t: k * v for t, v in det["non_retraites"].items()}, "baisse": False}
        serie = {2027: 0.0, 2028: 0.0, **{t: -k * det["pensions"][t] for t in ANNEES}}
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out = [
            Mesure("RET-RET-01 — taux plein à 65 ans, départs dès 63 ans avec décote", "retraites", serie),
            Mesure("RET-RET-01 — prélèvements sur les pensions en moins", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        out += bib.baisse_prelevements_salaries(
            p, idx, self.v("restitution.baisse_salaries"), self.v("restitution.part_ir_retrouvee", s),
            self.v("restitution.premiere_annee"), "RET-ECO-06 — restitution aux salariés : cotisations salariales en moins")
        e = sq.effectifs(p, s)
        h = self.v("chomage.baisse_taux", s)
        canaux["Assurance chômage resserrée : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        return out, canaux


def programme() -> Retailleau:
    return Retailleau()
