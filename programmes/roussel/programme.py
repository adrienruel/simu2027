"""Programme de Fabien Roussel (Parti communiste français), chiffré mesure par mesure sur le noyau (11 novembre 2026).

Pas de programme présidentiel 2027 arrêté : candidature validée le 6 septembre 2026 ; sources : discours de
l'université d'été (22 août 2026) et de la Fête de l'Humanité (2025 et 12 septembre 2026), « Pacte pour l'avenir de
la France » (2025), pages thématiques de pcf.fr, recensées par programme-candidat.fr, quivoter2027.com,
swipetonvote.fr et votons-2027.fr (ce dernier encore sur le programme de 2022). Fiche : mesures.yaml. Aucune recette
annoncée n'est reprise (60 Md€ de contribution des banques et assurances, 211 Md€ d'aides « réorientées »).

- **mesures simples** (groupe roussel_mesures, moteur/programme_simple.py) ; les montants communs avec Mélenchon
  (ISF, taxe Zucman, « 100 % Sécu », logement public) reprennent ses estimations ;
- **mesures calculées** :
  - SMIC à 1 700 € net (moteur/bibliotheque.smic, même calcul que Mélenchon) ; point d'indice +5 % ;
  - retraite à 60 ans à taux plein : 62 ans pour les départs de 2028, puis 60 ans en 2032 (même calendrier que
    Mélenchon), emploi des seniors ; pensions indexées sur le salaire moyen au lieu des prix ;
  - assurance chômage d'avant 2019 (programme du Nouveau Front populaire, 2024) ;
  - « sécurité d'emploi ou de formation » : emplois garantis au SMIC (même mécanique que la garantie d'emploi de
    Mélenchon) ;
  - 32 heures sans perte de salaire, dans le privé et dans la fonction publique : coût horaire, embauches de partage
    du travail, heures perdues (PIB) et embauches publiques.

    python -m moteur.noyau roussel
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ANNEES_AVANT, ProgrammeSimple

POSTE_VERSANT = {"etat_civils": "etat_missions", "etat_militaires": "defense_ue", "territoriale": "collectivites",
                 "hospitaliere": "sante"}


class Roussel(ProgrammeSimple):
    nom = "roussel"
    libelle = "Roussel (Parti communiste français)"

    def smic(self, p) -> dict:
        infl27 = p.val("inflation.base")["2027"]
        cible = bib.brut_de_net_mensuel(self.v("smic.smic_net_programme") / (1 + infl27))
        return bib.smic(p, cible, self.v("smic.diffusion_jusqu_a"), self.v("smic.part_marge_absorbee"),
                        self.v("smic.valeur_emploi_chomeur"),
                        allegements_suivent_smic=self.v("smic.allegements_suivent_smic"))

    def retraites(self, p, s) -> dict:
        cal = self.v("retraites.calendrier")
        return bib.baisse_age_legal_detail(p, s, {cal["abrogation"]: self.v("retraites.profil_62_ans"),
                                                  cal["soixante_ans"]: self.v("retraites.profil_60_ans")})

    def mesures_calculees(self, p, s, idx):
        out, canaux = [], {}
        ip = idx["pib"]
        e = sq.effectifs(p, s)
        y = sq.pib(p, s)
        rec = sq.recettes(p, s)
        un = {2027: 0.0, 2028: 1.0}  # tout à partir de la loi de finances 2028

        def ser(v, montee=un):
            return {**{t: v * montee[t] for t in ANNEES_AVANT}, **{t: v * ip[t] for t in ANNEES}}

        # PCF-SAL-01 : SMIC à 1 700 € net
        sm = self._cache.setdefault(("smic", id(p)), self.smic(p))
        pr, pu = sm["prive"], sm["public"]
        nom = "PCF-SAL-01 — SMIC à 1 700 € net"
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

        def m3(t):  # montée en trois ans à partir de 2028
            return min(1.0, max(0.0, (t - 2027) / 3))
        out.append(Mesure(f"{nom} : emplois perdus ({emplois / 1e3:.0f} 000)", "recettes",
                          {2027: 0.0, 2028: -perte * m3(2028), **{t: -perte * m3(t) * ip[t] for t in ANNEES}},
                          nature="effet_macro"))
        canaux["*SMIC à 1 700 € net : emplois perdus"] = {t: -emplois * m3(t) for t in ANNEES}

        # PCF-SAL-02 : point d'indice +5 %
        cout_public = sq.prelevements_activite(p)["public"]["cout"]
        hausse = cout_public * self.v("fp.part_indiciaire") * self.v("fp.hausse_point")
        part_fp = self.part_prelevements_fp(p)
        for v, part in versants.items():
            out.append(Mesure(f"PCF-SAL-02 — point d'indice +5 % ({POSTE_VERSANT[v]})", POSTE_VERSANT[v],
                              ser(hausse * part / tot)))
        out.append(Mesure("PCF-SAL-02 — prélèvements sur la hausse du point d'indice", "recettes",
                          ser(part_fp * hausse)))

        # PCF-RET-01 : retraite à 62 puis 60 ans
        det = self.retraites(p, s)
        pens = det["pensions"]
        serie = {2027: 0.0, 2028: 0.5 * pens[2029], **pens}
        ret = sq.retraites(p, s)
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / ret[2029]["depenses"]
        out += [
            Mesure("PCF-RET-01 — retraite à 62 ans en 2028, puis à 60 ans à taux plein en 2032", "retraites", serie),
            Mesure("PCF-RET-01 — prélèvements sur les pensions en plus", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": {t: -v for t, v in det["retraites_en_plus"].items()},
                                          "baisse": True}

        # PCF-RET-02 : pensions indexées sur le salaire moyen au lieu des prix (à partir de 2028)
        w = sq.salaires(p, s)
        # chaque pension gagne, depuis sa liquidation (ou 2029), la croissance réelle des salaires ; ancienneté moyenne
        # des pensions en cours ≈ 12 ans (âge moyen des retraités ≈ 75 ans, départ ≈ 63 ans) : écart w(t) / w(t − 12)
        anc = int(self.v("retraites.anciennete_moyenne"))
        idx_sal = {t: (ret[t]["depenses"] + pens.get(t, 0.0)) * (w[t] / w[max(2029, t - anc)] - 1) for t in ANNEES}
        out += [
            Mesure("PCF-RET-02 — pensions revalorisées comme le salaire moyen (au lieu des prix)", "retraites",
                   {2027: 0.0, 2028: 0.0, **idx_sal}),
            Mesure("PCF-RET-02 — prélèvements sur les pensions revalorisées", "recettes",
                   {2027: 0.0, 2028: 0.0, **{t: taux_prel * v for t, v in idx_sal.items()}}),
        ]

        # PCF-EMP-03 : assurance chômage d'avant 2019
        h = self.v("chomage.hausse_taux", s)
        canaux["Assurance chômage plus généreuse : chômeurs en plus"] = {
            t: -h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}

        # PCF-EMP-02 : sécurité d'emploi ou de formation (emplois garantis, éviction propre)
        g = self.v("emplois_aides.securite_emploi")
        ev = g["eviction"][s]

        def mont(t):
            return min(1.0, max(0.0, (t - g["debut"] + 1) / (g["plein"] - g["debut"] + 1)))
        canaux["*Sécurité d'emploi ou de formation : emplois créés"] = {t: g["emplois"] * mont(t) for t in ANNEES}
        canaux["Sécurité d'emploi ou de formation : emplois privés évincés"] = {
            t: -ev * g["emplois"] * mont(t) for t in ANNEES}

        # PCF-EMP-01 : 32 heures sans perte de salaire (privé : méthode commune ProgrammeSimple.trente_deux_heures)
        c = dict(self.v("temps_travail.trente_deux_heures"))
        c["emplois_concernes"] = c["emplois_prive"]
        out += self.trente_deux_heures(p, s, idx, c, self.v("temps_travail.elasticite_emploi", s),
                                       "PCF-EMP-01 — 32 heures", canaux)

        def m32(t):
            return min(1.0, max(0.0, (t - c["debut"] + 1) / (c["plein"] - c["debut"] + 1)))
        # fonction publique : 32 heures, embauches pour garder le service
        hausse_fp = cout_public * (c["heures_actuelles"] / c["heures_cible"] - 1) * c["part_compensee_fp"][s]
        for v, part in versants.items():
            out.append(Mesure(f"PCF-EMP-01 — 32 heures dans la fonction publique : embauches ({POSTE_VERSANT[v]})",
                              POSTE_VERSANT[v], {2027: 0.0, 2028: hausse_fp * part / tot * m32(2028),
                                                 **{t: hausse_fp * part / tot * m32(t) * ip[t] for t in ANNEES}}))
        out.append(Mesure("PCF-EMP-01 — 32 heures dans la fonction publique : prélèvements sur ces embauches", "recettes",
                          {2027: 0.0, 2028: part_fp * hausse_fp * m32(2028),
                           **{t: part_fp * hausse_fp * m32(t) * ip[t] for t in ANNEES}}))
        n_fp = hausse_fp * 1e9 / self.v("emploi.cout_poste_public")
        canaux["*Postes publics : 32 heures dans la fonction publique"] = {t: n_fp * m32(t) for t in ANNEES}
        # même éviction que les autres postes publics créés (règle commune, emploi_public.eviction_privee)
        ev_fp = sq._v(p, "emploi_public.eviction_privee", s)
        canaux["32 heures : emplois privés évincés par les embauches publiques"] = {
            t: -ev_fp * n_fp * m32(t) for t in ANNEES}
        return out, canaux


def programme() -> Roussel:
    return Roussel()
