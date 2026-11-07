"""Programme d'Édouard Philippe (Horizons), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : site de campagne (quatre pages de priorités), interviews, discours et publications d'Horizons de 2025-2026,
recensés par programmes-2027.fr (87 mesures) ; fiche : mesures.yaml. Les économies annoncées ne sont pas reprises :
seules les mesures nommées sont estimées, en trois scénarios quand elles n'ont pas de source.

- **mesures simples** (groupe philippe_mesures) : impôts de production −50 Md€ et aides aux entreprises supprimées,
  impôt sur le revenu après une naissance, non-remplacement d'un départ sur trois, enseignants, défense… ;
- **mesures calculées** : retraite à 65 ans (moteur/bibliotheque.report_age_legal_detail, même rythme que Bertrand et
  Zemmour), emploi des seniors ; chômage plus bas avec l'indemnisation ramenée à 12 mois.

    python -m moteur.noyau philippe
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ProgrammeSimple


class Philippe(ProgrammeSimple):
    nom = "philippe"
    libelle = "Philippe (Horizons)"

    def mesures_calculees(self, p, s, idx):
        canaux = {}
        det = bib.report_age_legal_detail(p, s, self.v("retraites.age_cible"), self.v("retraites.premiere_generation"),
                                          self.v("retraites.pas_par_generation"))
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": det["non_retraites"], "baisse": False}
        serie = {2027: 0.0, 2028: 0.0, **{t: -det["pensions"][t] for t in ANNEES}}
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out = [
            Mesure(f"PHI-RET-01 — âge de départ porté à {self.v('retraites.age_cible')} ans", "retraites", serie),
            Mesure("PHI-RET-01 — prélèvements sur les pensions en moins", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        e = sq.effectifs(p, s)
        h = self.v("chomage.baisse_taux", s)
        canaux["Indemnisation chômage ramenée à 12 mois : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        return out, canaux


def programme() -> Philippe:
    return Philippe()
