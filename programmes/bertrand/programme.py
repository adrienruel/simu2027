"""Programme de Xavier Bertrand (Nous France), chiffré sur le noyau (6 novembre 2026).

Pas de programme publié : mesures tirées des entretiens et tribunes de 2025-2026 (fiche : mesures.yaml). Mesures
simples dans parametres.yaml (groupe bertrand_mesures), plus une mesure de la bibliothèque commune : le report de
l'âge légal (moteur/bibliotheque.py), dont une part de l'économie est rendue par les départs anticipés avec décote.

Les 20 Md€ d'économies par an annoncés (100 Md€ en cinq ans) ne sont pas saisis (règle) : seules les lignes
identifiées (retraites, assurance chômage, fonctionnaires) sont chiffrées, les deux dernières en trois scénarios.

    python -m moteur.noyau bertrand
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ProgrammeSimple


class Bertrand(ProgrammeSimple):
    nom = "bertrand"
    libelle = "Bertrand (Nous France)"

    def mesures_calculees(self, p, s, idx):
        det = bib.report_age_legal_detail(p, s, self.v("retraites.age_cible"), self.v("retraites.premiere_generation"),
                                   self.v("retraites.pas_par_generation"))
        eco = det["pensions"]
        k = self.v("retraites.part_economie_gardee", s)
        # les départs anticipés avec décote rendent aussi une partie des personnes au travail
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": {t: k * v for t, v in det["non_retraites"].items()}, "baisse": False}
        serie = {2027: 0.0, 2028: 0.0, **{t: -k * eco[t] for t in ANNEES}}
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out = [
            Mesure(f"BER-RET-01 — âge légal porté à {self.v('retraites.age_cible')} ans, départs anticipés avec décote",
                   "retraites", serie),
            Mesure("BER-RET-01 — prélèvements sur les pensions en moins", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        cap, emplois_cap = bib.capitalisation_obligatoire(p, s, p.val("lectures_communes.capitalisation"), "BER-RET-02")
        return out + cap, {"Capitalisation obligatoire : emplois (coût du travail et salaire net)": emplois_cap}


def programme() -> Bertrand:
    return Bertrand()
