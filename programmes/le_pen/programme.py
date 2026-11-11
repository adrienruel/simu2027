"""Programme de Marine Le Pen (Rassemblement national), chiffré mesure par mesure sur le noyau (11 novembre 2026).

Sources : contre-budget et « trajectoire financière du quinquennat » présentés le 6 octobre 2026 (Public Sénat,
Acteurs publics, AFP), mesures recensées par votons-2027.fr (site rassemblementnational.fr), FranceBudget, chiffrages
de l'Institut Montaigne (2022 et 2024) ; fiche : mesures.yaml. Programme partiel : le document du contre-budget n'est
pas publié en ligne. Les économies annoncées (140 Md€ nets en 2032, dont 29 Md€ sur l'immigration, 20,7 sur l'État,
9 sur l'Union européenne) ne sont pas reprises : chaque mesure nommée est estimée, le reste passe par l'enveloppe
d'économies déduite du programme domaine par domaine (règle commune).

- **mesures simples** (groupe le_pen_mesures, moteur/programme_simple.py) ;
- **mesures calculées** :
  - retraite : réforme de 2023 abrogée, 62 ans et 42 annuités, 60 ans pour les carrières commencées avant 20 ans,
    soit les règles d'avant 2023 (moteur/bibliotheque.baisse_age_legal_detail, même profil que Glucksmann) ;
    emploi des seniors (scénario miroir).

    python -m moteur.noyau le_pen
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import Mesure
from moteur.programme_simple import ProgrammeSimple


class LePen(ProgrammeSimple):
    nom = "le_pen"
    libelle = "Le Pen (Rassemblement national) — partiel"

    def retraites(self, p, s) -> dict:
        return bib.baisse_age_legal_detail(p, s, {self.v("retraites.annee"): self.v("retraites.profil_62_ans")})

    def mesures_calculees(self, p, s, idx):
        out, canaux = [], {}
        # RN-RET-01 : réforme de 2023 abrogée, 62 ans pour les départs de 2028
        det = self.retraites(p, s)
        pens = det["pensions"]
        serie = {2027: 0.0, 2028: 0.5 * pens[2029], **pens}
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out += [
            Mesure("RN-RET-01 — réforme de 2023 abrogée, 62 ans et 42 annuités, 60 ans pour les carrières longues",
                   "retraites", serie),
            Mesure("RN-RET-01 — prélèvements sur les pensions en plus", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": {t: -v for t, v in det["retraites_en_plus"].items()},
                                          "baisse": True}
        return out, canaux


def programme() -> LePen:
    return LePen()
