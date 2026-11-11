"""Programme de Nathalie Arthaud (Lutte ouvrière), chiffrage PARTIEL sur le noyau (6 novembre 2026).

Lutte ouvrière ne présente pas de programme électoral chiffré (fiche : mesures.yaml). Le cœur du programme
(expropriation sans indemnité des grands groupes, interdiction des licenciements, répartition du travail sans perte
de salaire, planification) change l'économie entière : il n'est pas chiffré. Sont chiffrées les mesures qui ont une
ligne budgétaire :

- SMIC à 2 200 € net (moteur/bibliotheque.smic, même mécanique que le programme Tondelier, privé et agents publics) ;
- défense au niveau du PLF 2027 (moteur/bibliotheque.defense_sans_lpm) ;
- mesures simples (parametres.yaml, groupe arthaud_mesures) : embauches dans les services publics, annulation de
  mesures du budget 2027, confiscation des bénéfices du pétrole et de l'armement, carburant à prix coûtant ;
- ajout du 11/11/2026 : répartition du travail sans perte de salaire (ProgrammeSimple.trente_deux_heures, durée
  ramenée jusqu'à absorber le chômage), interdiction des licenciements (emplois maintenus par réquisition, embauches
  en moins), égalité salariale femmes-hommes dans le privé.

    python -m moteur.noyau arthaud
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ANNEES_AVANT, ProgrammeSimple

POSTE_VERSANT = {"etat_civils": "etat_missions", "etat_militaires": "defense_ue", "territoriale": "collectivites",
                 "hospitaliere": "sante"}


class Arthaud(ProgrammeSimple):
    nom = "arthaud"
    libelle = "Arthaud (Lutte ouvrière) — partiel"

    def smic(self, p) -> dict:
        infl27 = p.val("inflation.base")["2027"]
        cible = bib.brut_de_net_mensuel(self.v("smic.smic_net_programme") / (1 + infl27))
        return bib.smic(p, cible, self.v("smic.diffusion_jusqu_a"), self.v("smic.part_marge_absorbee"),
                        self.v("smic.valeur_emploi_chomeur"),
                        allegements_suivent_smic=self.v("smic.allegements_suivent_smic"))

    def mesures_calculees(self, p, s, idx):
        out = []
        ip = idx["pib"]
        sm = self._cache.setdefault(("smic", id(p)), self.smic(p))
        pr, pu = sm["prive"], sm["public"]
        montee = {2027: 0.5, 2028: 1.0}

        def ser(v):
            return {**{t: v * montee[t] for t in ANNEES_AVANT}, **{t: v * ip[t] for t in ANNEES}}
        out += [
            Mesure("ART-ECO-01 — SMIC à 2 200 € net : prélèvements sur les hausses de salaire (privé)", "recettes", ser(pr["prelevements"])),
            Mesure("ART-ECO-01 — SMIC à 2 200 € net : TVA sur les revenus en plus (privé)", "recettes", ser(pr["tva"])),
            Mesure("ART-ECO-01 — SMIC à 2 200 € net : prime d'activité et aides en moins (privé)", "pauvrete", ser(pr["aides"])),
            Mesure("ART-ECO-01 — SMIC à 2 200 € net : IS sur les marges réduites", "recettes", ser(pr["is"])),
        ]
        # agents publics : hausse de coût par versant, prélèvements, TVA et aides
        versants = p.val("statu_quo.versants_fonction_publique")
        tot = sum(versants.values())
        for v, part in versants.items():
            out.append(Mesure(f"ART-ECO-01 — SMIC à 2 200 € net : rémunérations publiques ({POSTE_VERSANT[v]})",
                              POSTE_VERSANT[v], ser(pu["hausse_cout"] * part / tot)))
        out += [
            Mesure("ART-ECO-01 — SMIC à 2 200 € net : prélèvements et TVA sur les rémunérations publiques", "recettes",
                   ser(pu["prelevements"] + pu["tva"])),
            Mesure("ART-ECO-01 — SMIC à 2 200 € net : aides en moins (agents publics)", "pauvrete", ser(pu["aides"])),
        ]
        # emplois perdus (privé), montée en trois ans (2027-2029)
        el = self.v("smic.elasticite_emploi", s)
        emplois = sum(n * (1 - r ** el) for n, r in pr["chocs"])  # élasticité constante
        perte = emplois * pr["perte_par_emploi"] / 1e9
        m3 = {2027: 1 / 3, 2028: 2 / 3}
        out.append(Mesure(f"ART-ECO-01 — SMIC à 2 200 € net : emplois perdus ({emplois / 1e3:.0f} 000)", "recettes",
                          {**{t: -perte * m3[t] for t in ANNEES_AVANT},
                           **{t: -perte * min(1.0, (t - 2026) / 3) * ip[t] for t in ANNEES}}, nature="effet_macro"))
        perdus = {t: -emplois * min(1.0, (t - 2026) / 3) for t in ANNEES}
        # défense
        if self.v("defense.niveau_2026"):
            d = bib.defense_sans_lpm(p, s)
            out.append(Mesure("ART-INT-01 — défense au niveau du PLF 2027 (loi de programmation militaire abandonnée)",
                              "defense_ue", {2027: 0.0, 2028: -0.5 * d[2029], **{t: -d[t] for t in ANNEES}}))
        canaux = {"*SMIC à 2 200 € net : emplois perdus": perdus}
        e = sq.effectifs(p, s)
        e_ref = sq.effectifs(p, "prudent")[2029]
        y = sq.pib(p, s)
        r_emp = {t: e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}

        # ART-EMP-02 : répartition du travail sans perte de salaire, jusqu'à absorber le chômage du statu quo
        c = dict(self.v("temps_travail.repartition"))
        c["heures_cible"] = c["heures_actuelles"] * (1 - e_ref["chomeurs"] / e_ref["emploi"])
        c["emplois_concernes"] = c["emplois_prive"]
        prefixe = f"ART-EMP-02 — répartition du travail ({c['heures_cible']:.1f} heures)"
        out += self.trente_deux_heures(p, s, idx, c, self.v("temps_travail.elasticite_emploi", s), prefixe, canaux)
        out += self.heures_fonction_publique(p, s, idx, c, prefixe, canaux)

        # ART-EMP-01 : interdiction des licenciements (réquisition des entreprises défaillantes)
        li = self.v("licenciements.interdiction")
        stock, maintenus = 0.0, {}
        for t in range(li["debut"], max(ANNEES) + 1):
            stock = stock * (1 - li["sortie_an"]) + li["emplois_menaces_an"] * li["part_maintenue"][s]
            maintenus[t] = stock
        maint = {t: maintenus.get(t, 0.0) * r_emp[t] for t in ANNEES}
        canaux["*Interdiction des licenciements : emplois maintenus par réquisition"] = maint
        cout = li["cout_net_emploi"][s]
        out.append(Mesure("ART-EMP-01 — interdiction des licenciements : emplois maintenus par réquisition (coût net)",
                          "autres", {2027: 0.0, 2028: maintenus[2028] * cout / 1e9,
                                  **{t: maint[t] * cout * ip[t] / 1e9 for t in ANNEES}}))
        # ces emplois produisent moins qu'un emploi moyen : la valeur ajoutée comptée par le canal est corrigée
        self.ajouter_pib(p, s, {t: -maint[t] * y[t] / e[t]["emploi"] * (1 - li["productivite_relative"]) for t in ANNEES})
        n_prive = self.v("temps_travail.repartition")["emplois_prive"]
        canaux["Interdiction des licenciements : embauches en moins"] = {
            t: -li["embauches_en_moins"][s] * n_prive * min(1.0, (t - 2027) / 4) * r_emp[t] for t in ANNEES}

        # ART-FAM-02 : égalité salariale femmes-hommes (privé, écart à poste comparable)
        eg = self.v("egalite.salariale")
        pa = sq.prelevements_activite(p)["prive"]
        taux_prel = (pa["prelevements"] + pa["impot_revenu"]) / pa["cout"]
        hausse = pa["cout"] * eg["part_femmes_cout"] * eg["ecart"]
        taux_tva = p.val("systeme_actuel.taux_tva_moyen")
        taux_is = 0.25

        def me(t):
            return min(1.0, max(0.0, (t - eg["debut"] + 1) / (eg["plein"] - eg["debut"] + 1)))

        def serie(v):
            return {2027: 0.0, 2028: v * me(2028), **{t: v * me(t) * ip[t] for t in ANNEES}}
        out += [
            Mesure("ART-FAM-02 — égalité salariale : prélèvements sur les hausses de salaire", "recettes",
                   serie(hausse * taux_prel)),
            Mesure("ART-FAM-02 — égalité salariale : TVA sur les revenus en plus", "recettes",
                   serie(hausse * (1 - taux_prel) * taux_tva)),
            Mesure("ART-FAM-02 — égalité salariale : IS sur les marges réduites", "recettes",
                   serie(-hausse * eg["part_is"] * taux_is)),
        ]
        el_t = self.v("temps_travail.elasticite_emploi", s)
        perdus_f = eg["emplois_femmes"] * (1 - (1 + eg["ecart"]) ** el_t)
        canaux["Égalité salariale : emplois perdus par le coût du travail"] = {t: -perdus_f * me(t) * r_emp[t] for t in ANNEES}
        return out, canaux


def programme() -> Arthaud:
    return Arthaud()
