"""Programme de Raphaël Glucksmann (Place publique), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : « Notre vision pour la France. Acte I » (Place publique, 23 juin 2025), débats de LCP (23 septembre et
5 octobre 2026), Public Sénat (24 août 2026), L'Info Durable (12 octobre 2026), recensés par programmes-2027.fr
(112 mesures) ; fiche : mesures.yaml. Rien n'est chiffré par le candidat sauf le plan contre les violences sexistes et
sexuelles (1 Md€) : chaque montant est estimé par le modèle (parametres.yaml), aucune recette annoncée n'est reprise.

- **mesures simples** (groupe glucksmann_mesures, moteur/programme_simple.py) ;
- **mesures calculées** :
  - SMIC à 1 600 € net en deux ans (moteur/bibliotheque.smic, privé et agents publics, emplois perdus) ;
  - CSG sur les salaires abaissée de 15 Md€ (fraction de la suppression calculée par OpenFisca pour Zemmour, impôt
    sur le revenu en plus, prestations en moins) ;
  - retraite : 62 ans pour les départs de 2028 (moteur/bibliotheque.baisse_age_legal_detail), emploi des seniors ;
  - chômage plus élevé quand la réforme de l'assurance chômage est abrogée (Banque de France) ;
  - Territoires zéro chômeur généralisés (emplois aidés, éviction propre) ;
  - service civique obligatoire de dix mois : jeunes retirés de l'emploi, sans devenir chômeurs.

    python -m moteur.noyau glucksmann
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import offre
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ANNEES_AVANT, ProgrammeSimple

POSTE_VERSANT = {"etat_civils": "etat_missions", "etat_militaires": "defense_ue", "territoriale": "collectivites",
                 "hospitaliere": "sante"}
INC_CSG = "openfisca:csg_activite_supprimee"


class Glucksmann(ProgrammeSimple):
    nom = "glucksmann"
    libelle = "Glucksmann (Place publique)"

    def smic(self, p) -> dict:
        infl27 = p.val("inflation.base")["2027"]
        cible = bib.brut_de_net_mensuel(self.v("smic.smic_net_programme") / (1 + infl27))
        return bib.smic(p, cible, self.v("smic.diffusion_jusqu_a"), self.v("smic.part_marge_absorbee"),
                        self.v("smic.valeur_emploi_chomeur"),
                        allegements_suivent_smic=self.v("smic.allegements_suivent_smic"))

    def retraites(self, p, s) -> dict:
        return bib.baisse_age_legal_detail(p, s, {self.v("retraites.annee"): self.v("retraites.profil_62_ans")})

    def mesures_calculees(self, p, s, idx):
        out, canaux = [], {}
        ip = idx["pib"]
        e = sq.effectifs(p, s)

        # GLU-ECO-01 : SMIC à 1 600 € net en deux ans (moitié en 2028, entier en 2029)
        montee = {2027: 0.0, 2028: 0.5}

        def ser(v):
            return {**{t: v * montee[t] for t in ANNEES_AVANT}, **{t: v * ip[t] for t in ANNEES}}

        sm = self._cache.setdefault(("smic", id(p)), self.smic(p))
        pr, pu = sm["prive"], sm["public"]
        nom = "GLU-ECO-01 — SMIC à 1 600 € net en deux ans"
        out += [
            Mesure(f"{nom} : prélèvements sur les hausses de salaire (privé)", "recettes", ser(pr["prelevements"])),
            Mesure(f"{nom} : TVA sur les revenus en plus (privé)", "recettes", ser(pr["tva"])),
            Mesure(f"{nom} : prime d'activité et aides en moins (privé)", "pauvrete", ser(pr["aides"])),
            Mesure(f"{nom} : IS sur les marges réduites", "recettes", ser(pr["is"])),
        ]
        versants = p.val("statu_quo.versants_fonction_publique")
        tot = sum(versants.values())
        for v, part in versants.items():
            out.append(Mesure(f"{nom} : rémunérations publiques ({POSTE_VERSANT[v]})", POSTE_VERSANT[v],
                              ser(pu["hausse_cout"] * part / tot)))
        out += [
            Mesure(f"{nom} : prélèvements et TVA sur les rémunérations publiques", "recettes",
                   ser(pu["prelevements"] + pu["tva"])),
            Mesure(f"{nom} : aides en moins (agents publics)", "pauvrete", ser(pu["aides"])),
        ]
        el = self.v("smic.elasticite_emploi", s)
        emplois = sum(n * (1 - r ** el) for n, r in pr["chocs"])
        perte = emplois * pr["perte_par_emploi"] / 1e9

        def m3(t):  # emplois : montée en trois ans à partir de 2028
            return min(1.0, max(0.0, (t - 2027) / 3))
        out.append(Mesure(f"{nom} : emplois perdus ({emplois / 1e3:.0f} 000)", "recettes",
                          {**{t: -perte * m3(t) for t in ANNEES_AVANT},
                           **{t: -perte * m3(t) * ip[t] for t in ANNEES}}, nature="effet_macro"))
        canaux["*SMIC à 1 600 € net : emplois perdus"] = {t: -emplois * m3(t) for t in ANNEES}

        # GLU-FIS-01b : CSG sur les salaires abaissée de 15 Md€ (fraction de la suppression totale)
        c = bib.csg_activite(p)
        f = self.v("csg.baisse") / (c["csg_prive"] + c["csg_public"])
        k = self.v("csg.part_ir_retrouvee", s)
        debut = self.v("csg.premiere_annee")

        def ser_csg(v, indice):
            return {**{t: (v if t >= debut else 0.0) for t in ANNEES_AVANT}, **{t: v * idx[indice][t] for t in ANNEES}}
        nom = "GLU-FIS-01b — CSG sur les salaires abaissée"
        st = offre.statique_openfisca(p, "csg_activite_supprimee")
        out += [
            Mesure(f"{nom} (privé)", "recettes", ser_csg(-f * c["csg_prive"], "recette:salaires_prive"),
                   instrument="travail", incidence=INC_CSG),
            Mesure(f"{nom} (agents publics)", "recettes", ser_csg(-f * c["csg_public"], "recette:salaires_public"),
                   instrument="travail", incidence=INC_CSG),
            Mesure(f"{nom} : impôt sur le revenu en plus (CSG déductible plus faible)", "recettes",
                   ser_csg(f * k * (c["ir_prive"] + c["ir_public"]), "recette:salaires_prive"),
                   instrument="travail", incidence=INC_CSG),
            Mesure(f"{nom} : prime d'activité, RSA et aides au logement en moins", "pauvrete",
                   ser_csg(f * st["prestations_en_plus"], "recette:salaires_prive")),
        ]

        # GLU-RET-01 : retraite à 62 ans pour les départs de 2028
        det = self.retraites(p, s)
        pens = det["pensions"]
        serie = {2027: 0.0, 2028: 0.5 * pens[2029], **pens}
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out += [
            Mesure("GLU-RET-01 — réforme de 2023 abrogée, retraite à 62 ans", "retraites", serie),
            Mesure("GLU-RET-01 — prélèvements sur les pensions en plus", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": {t: -v for t, v in det["retraites_en_plus"].items()},
                                          "baisse": True}

        # GLU-EMP-02 : chômage plus élevé quand la réforme de l'assurance chômage est abrogée
        h = self.v("chomage.hausse_taux", s)
        canaux["Assurance chômage plus généreuse : chômeurs en plus"] = {
            t: -h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}

        # GLU-EMP-01 : Territoires zéro chômeur généralisés
        g = self.v("emplois_aides.territoires_zero_chomeur")
        ev = g["eviction"][s]

        def mont(t):
            return min(1.0, max(0.0, (t - g["debut"] + 1) / (g["plein"] - g["debut"] + 1)))
        canaux["*Territoires zéro chômeur : emplois créés"] = {t: g["emplois"] * mont(t) for t in ANNEES}
        canaux["Territoires zéro chômeur : emplois privés évincés"] = {t: -ev * g["emplois"] * mont(t) for t in ANNEES}

        # GLU-SOC-02 : service civique obligatoire de dix mois (2029, toute la génération en 2032)
        n = self.v("service_civique.jeunes") * 10 / 12 * self.v("service_civique.part_en_emploi", s)

        def msc(t):
            return min(1.0, max(0.0, (t - 2028) / 4))
        sc = {t: -n * msc(t) * e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}
        canaux["Service civique obligatoire : jeunes retirés de l'emploi"] = sc
        self.actifs_en_plus = getattr(self, "actifs_en_plus", {})
        self.actifs_en_plus[(id(p), s)] = dict(sc)
        return out, canaux


def programme() -> Glucksmann:
    return Glucksmann()
