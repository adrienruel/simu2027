"""Programme de Jean-Luc Mélenchon (La France insoumise), chiffré mesure par mesure sur le noyau (6 novembre 2026).

Source : « L'Avenir en commun. Le programme de la Nouvelle France », 5e édition (La Dispute, novembre 2026), lu en
entier ; fiche des mesures et citations : mesures.yaml. Le livre ne chiffre rien : chaque montant est estimé par le
modèle (parametres.yaml), aucune recette ni économie annoncée n'est reprise.

- **mesures simples** (groupe melenchon_mesures, moteur/programme_simple.py) : recettes, prestations, santé, éducation,
  logement, investissement, collectivités, participations ;
- **mesures calculées** :
  - SMIC à 1 700 € net dès juillet 2027 (moteur/bibliotheque.smic, privé et agents publics, emplois perdus) ;
  - point d'indice +10 % dès juillet 2027, réparti entre les versants de la fonction publique ;
  - retraite : 62 ans pour les départs de 2028, puis 60 ans en 2032 (moteur/bibliotheque.baisse_age_legal_detail,
    même calcul et même calage que le statu quo), prélèvements sur les pensions, emploi des seniors (offre.seniors) ;
  - chômage plus élevé quand les réformes de l'assurance chômage sont annulées (Banque de France) ;
  - sixième semaine de congés payés et 4 février férié : coût horaire du travail du privé +2,7 %, emplois perdus.

    python -m moteur.noyau melenchon
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ANNEES_AVANT, ProgrammeSimple

POSTE_VERSANT = {"etat_civils": "etat_missions", "etat_militaires": "defense_ue", "territoriale": "collectivites",
                 "hospitaliere": "sante"}


class Melenchon(ProgrammeSimple):
    nom = "melenchon"
    libelle = "Mélenchon (La France insoumise)"

    # ------------------------------------------------------------------ SMIC
    def smic(self, p) -> dict:
        infl27 = p.val("inflation.base")["2027"]
        cible = bib.brut_de_net_mensuel(self.v("smic.smic_net_programme") / (1 + infl27))
        return bib.smic(p, cible, self.v("smic.diffusion_jusqu_a"), self.v("smic.part_marge_absorbee"),
                        self.v("smic.valeur_emploi_chomeur"),
                        allegements_suivent_smic=self.v("smic.allegements_suivent_smic"))

    # ------------------------------------------------------------------ retraites
    def retraites(self, p, s) -> dict:
        cal = self.v("retraites.calendrier")
        return bib.baisse_age_legal_detail(p, s, {cal["abrogation"]: self.v("retraites.profil_62_ans"),
                                                  cal["soixante_ans"]: self.v("retraites.profil_60_ans")})

    def mesures_calculees(self, p, s, idx):
        out, canaux = [], {}
        ip = idx["pib"]
        demi = {2027: 0.5, 2028: 1.0}  # mesures dès juillet 2027

        def ser(v, montee=demi):
            return {**{t: v * montee[t] for t in ANNEES_AVANT}, **{t: v * ip[t] for t in ANNEES}}

        # LFI-SAL-01 : SMIC à 1 700 € net
        sm = self._cache.setdefault(("smic", id(p)), self.smic(p))
        pr, pu = sm["prive"], sm["public"]
        nom = "LFI-SAL-01 — SMIC à 1 700 € net"
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
        m3 = {2027: 1 / 6, 2028: 1 / 2}  # montée en trois ans à partir de juillet 2027
        out.append(Mesure(f"{nom} : emplois perdus ({emplois / 1e3:.0f} 000)", "recettes",
                          {**{t: -perte * m3[t] for t in ANNEES_AVANT},
                           **{t: -perte * min(1.0, (t - 2026.5) / 3) * ip[t] for t in ANNEES}}, nature="effet_macro"))
        canaux["*SMIC à 1 700 € net : emplois perdus"] = {t: -emplois * min(1.0, (t - 2026.5) / 3) for t in ANNEES}

        # LFI-FP-01 : point d'indice +10 %
        cout_public = sq.prelevements_activite(p)["public"]["cout"]
        hausse = cout_public * self.v("fp.part_indiciaire") * self.v("fp.hausse_point")
        part_fp = self.part_prelevements_fp(p)
        for v, part in versants.items():
            out.append(Mesure(f"LFI-FP-01 — point d'indice +10 % ({POSTE_VERSANT[v]})", POSTE_VERSANT[v],
                              ser(hausse * part / tot)))
        out.append(Mesure("LFI-FP-01 — prélèvements sur la hausse du point d'indice", "recettes",
                          ser(part_fp * hausse)))

        # LFI-RET-01 : retraite à 62 puis 60 ans
        det = self.retraites(p, s)
        pens = det["pensions"]
        serie = {2027: 0.0, 2028: 0.5 * pens[2029], **pens}
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
        out += [
            Mesure("LFI-RET-01 — retraite à 62 ans en 2028, puis à 60 ans en 2032", "retraites", serie),
            Mesure("LFI-RET-01 — prélèvements sur les pensions en plus", "recettes",
                   {t: taux_prel * v for t, v in serie.items()}),
        ]
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": {t: -v for t, v in det["retraites_en_plus"].items()},
                                          "baisse": True}

        # LFI-PRE-05 : chômage plus élevé avec l'assurance chômage d'avant 2019
        e = sq.effectifs(p, s)
        h = self.v("chomage.hausse_taux", s)
        canaux["Assurance chômage plus généreuse : chômeurs en plus"] = {
            t: -h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}

        # LFI-EMP-01 et LFI-EMP-02 : emplois aidés (éviction propre, pas celle des postes publics)
        for cle, libelle in (("garantie_emploi", "Garantie d'emploi"), ("emploi_jeune", "Emploi spécifique jeune")):
            g = self.v(f"emplois_aides.{cle}")
            ev = g["eviction"][s]
            def mont(t, g=g):
                return min(1.0, max(0.0, (t - g["debut"] + 1) / (g["plein"] - g["debut"] + 1)))
            canaux[f"*{libelle} : emplois créés"] = {t: g["emplois"] * mont(t) for t in ANNEES}
            canaux[f"{libelle} : emplois privés évincés"] = {t: -ev * g["emplois"] * mont(t) for t in ANNEES}

        # LFI-EMP-07 : sixième semaine de congés et 4 février férié (coût horaire du privé)
        k = 1 + self.v("temps_travail.hausse_cout_horaire")
        el_t = self.v("temps_travail.elasticite_emploi", s)
        n_prive = self.v("temps_travail.emplois_prive")
        perdus = n_prive * (1 - k ** el_t)
        canaux["Sixième semaine de congés et 4 février férié : emplois perdus"] = {
            t: -perdus * min(1.0, (t - 2027) / 2) * (e[t]["emploi"] / e[2029]["emploi"]) for t in ANNEES}
        # LFI-EMP-10 : 32 heures dans les métiers pénibles ou de nuit, privé compris (méthode commune, 11/11/2026)
        c = dict(self.v("temps_travail.trente_deux_heures"))
        c["emplois_concernes"] = c["emplois_concernes"][s]
        c["emplois_prive"] = n_prive
        out += self.trente_deux_heures(p, s, idx, c, el_t, "LFI-EMP-10 — 32 heures (métiers pénibles ou de nuit)",
                                       canaux)
        # effets en tonnes (groupe melenchon_ecologie) : ProgrammeSimple.mesures_ecologie, commun depuis le 11/11/2026
        return out, canaux


def programme() -> Melenchon:
    return Melenchon()
