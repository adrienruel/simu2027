"""Programme de Nathalie Arthaud (Lutte ouvrière), chiffrage PARTIEL sur le noyau (6 novembre 2026).

Lutte ouvrière ne présente pas de programme électoral chiffré (fiche : mesures.yaml). Le cœur du programme
(expropriation sans indemnité des grands groupes, interdiction des licenciements, répartition du travail sans perte
de salaire, planification) change l'économie entière : il n'est pas chiffré. Sont chiffrées les mesures qui ont une
ligne budgétaire :

- SMIC à 2 200 € net (moteur/bibliotheque.smic, même mécanique que le programme Tondelier, privé et agents publics) ;
- défense au niveau du PLF 2027 (moteur/bibliotheque.defense_sans_lpm) ;
- mesures simples (parametres.yaml, groupe arthaud_mesures) : embauches dans les services publics, annulation de
  mesures du budget 2027, confiscation des bénéfices du pétrole et de l'armement.

    python -m moteur.noyau arthaud
"""
from __future__ import annotations

from moteur import bibliotheque as bib
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
        return out, {"*SMIC à 2 200 € net : emplois perdus": perdus}


def programme() -> Arthaud:
    return Arthaud()
