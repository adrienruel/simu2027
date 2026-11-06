"""Programme d'Éric Zemmour (Reconquête), chiffré sur le noyau (6 novembre 2026).

Programme partiel (tract de priorités d'octobre 2026, tracts thématiques, pétitions, entretiens ; fiche :
mesures.yaml). Mesures simples dans parametres.yaml (groupe zemmour_mesures) ; mesures calculées :

- suppression de la CSG sur les revenus du travail : CSG des salariés et des agents publics par OpenFisca (2026) sur
  les distributions de 2026 (moteur/bibliotheque.csg_activite), CSG des indépendants, impôt sur le revenu en plus
  (la CSG déductible entre dans le revenu imposable) ;
- suppression des droits de succession : toute la recette du statu quo ;
- report de l'âge légal (même arbitrage que Bertrand : 65 ans, un trimestre par génération).

Aucune économie annoncée n'est reprise (80, 100 ou 140 Md€ selon les documents) : seules les lignes identifiées sont
chiffrées, chacune en quatre scénarios. Non chiffré : arrêt de l'immigration légale et « remigration » (population
active : variante démographique à construire), protectionnisme européen, six puis quatorze EPR (EDF, hors
administrations), capitalisation (financement non décrit).

    python -m moteur.noyau zemmour
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ANNEES_AVANT, ProgrammeSimple


class Zemmour(ProgrammeSimple):
    nom = "zemmour"
    libelle = "Zemmour (Reconquête)"

    def mesures_calculees(self, p, s, idx):
        out = []
        debut = self.v("csg.premiere_annee")

        def serie(montant_2029, indice):
            return {**{t: (montant_2029 if t >= debut else 0.0) for t in ANNEES_AVANT},
                    **{t: montant_2029 * idx[indice][t] for t in ANNEES}}
        # CSG sur les revenus du travail
        c = bib.csg_activite(p)
        k = self.v("csg.part_ir_retrouvee", s)
        ind = self.v("csg.independants", s)
        out += [
            Mesure("ZEM-FIS-01 — CSG supprimée sur les salaires du privé", "recettes",
                   serie(-c["csg_prive"], "recette:salaires_prive"), instrument="travail"),
            Mesure("ZEM-FIS-01 — CSG supprimée sur les rémunérations des agents publics", "recettes",
                   serie(-c["csg_public"], "recette:salaires_public"), instrument="travail"),
            Mesure("ZEM-FIS-01 — CSG supprimée sur les revenus des indépendants", "recettes",
                   serie(-ind, "recette:independants"), instrument="travail"),
            Mesure("ZEM-FIS-01 — impôt sur le revenu en plus (CSG déductible qui disparaît)", "recettes",
                   serie(k * c["ir_prive"], "recette:salaires_prive"), instrument="travail"),
            Mesure("ZEM-FIS-01 — impôt sur le revenu en plus (agents publics, indépendants)", "recettes",
                   serie(k * c["ir_public"] + 0.1 * ind, "recette:salaires_public"), instrument="travail"),
        ]
        # droits de succession
        rec = sq.recettes_par_impot(p, s)
        part = self.v("successions.part_supprimee")
        out.append(Mesure("ZEM-FIS-02 — droits de succession supprimés", "recettes",
                          {**{t: (-part * rec[2029]["successions"] if t >= debut else 0.0) for t in ANNEES_AVANT},
                           **{t: -part * rec[t]["successions"] for t in ANNEES}}, instrument="successions"))
        # retraites
        eco = bib.report_age_legal(p, s, self.v("retraites.age_cible"), self.v("retraites.premiere_generation"),
                                   self.v("retraites.pas_par_generation"))
        ser = {2027: 0.0, 2028: 0.0, **{t: -eco[t] for t in ANNEES}}
        taux_prel = rec[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out += [Mesure(f"ZEM-RET-01 — âge légal porté à {self.v('retraites.age_cible')} ans", "retraites", ser),
                Mesure("ZEM-RET-01 — prélèvements sur les pensions en moins", "recettes",
                       {t: taux_prel * v for t, v in ser.items()})]
        return out, {}


def programme() -> Zemmour:
    return Zemmour()
