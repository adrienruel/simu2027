"""« Programme IA » : programme de test écrit par Claude pour s'amuser (18 novembre 2026).

Pas un candidat : 20 mesures proposées par une IA, passées au banc du comparateur avec les mêmes règles que les
autres. Non publié (absent de programmes/publies.yaml) : hors des sorties et des tests par défaut, sans effet sur
les programmes publiés. Fiche : mesures.yaml ; montants : parametres.yaml (groupe programme_ia_mesures).

Le programme annonce +41,5 Md€ net en 2032, dont 30 Md€ par une règle de dépense. Comme pour les candidats, ce
chiffre n'est pas repris : la règle passe par l'enveloppe commune (économies déduites domaine par domaine, l'annonce
n'est qu'un plafond) et chaque autre mesure est estimée en crise / prudent / médian / optimiste.

Version 2 (18/11/2026, soir) : optimisée sur le comparateur, mêmes barèmes que les candidats. Ajouts : assurance
chômage (forme d'Attal), âge légal à 65 ans (bibliothèque, forme de Bertrand), successions, jours de carence, canaux
communs de l'offre de logements et des réformes de structure (rail, électricité) ; logement neuf ramené au foncier
public ; plan IA testé puis retiré (rendement trop faible dans le prudent).

Version 3 (18/11/2026, soir) : « le président choisit ». Règle fixée d'avance : meilleur déficit prudent du
simulateur, avec les émissions en baisse et sans toucher aux petites pensions ni aux minima sociaux. Retirées :
enseignants, crèches, accès aux soins, justice, seniors, leasing, foncier public ; pensions sous-indexées 5 ans.

    python -m moteur.noyau programme_ia
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ProgrammeSimple


class ProgrammeIA(ProgrammeSimple):
    nom = "programme_ia"
    libelle = "Programme IA (test)"

    def mesures_calculees(self, p, s, idx):
        out, canaux = [], {}
        e = sq.effectifs(p, s)

        # IA-RET-24 (version 2, si programme_ia_retraites est déclaré) : âge légal, comme Bertrand (bibliothèque)
        if self.a("retraites.age_cible"):
            det = bib.report_age_legal_detail(p, s, self.v("retraites.age_cible"), self.v("retraites.premiere_generation"),
                                              self.v("retraites.pas_par_generation"))
            k = self.v("retraites.part_economie_gardee", s)
            self.non_retraites = getattr(self, "non_retraites", {})
            self.non_retraites[(id(p), s)] = {"serie": {t: k * v for t, v in det["non_retraites"].items()}, "baisse": False}
            serie = {2027: 0.0, 2028: 0.0, **{t: -k * det["pensions"][t] for t in ANNEES}}
            taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
            out += [
                Mesure(f"IA-RET-24 — âge légal porté à {self.v('retraites.age_cible')} ans, carrières longues et usure gardées",
                       "retraites", serie),
                Mesure("IA-RET-24 — prélèvements sur les pensions en moins", "recettes",
                       {t: taux_prel * v for t, v in serie.items()}),
            ]

        # IA-EMP-21 : assurance chômage, chômage structurel plus bas (même forme que Attal)
        h = self.v("chomage.baisse_taux", s)
        canaux["Assurance chômage modulée : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        return out, canaux


def programme() -> ProgrammeIA:
    return ProgrammeIA()
