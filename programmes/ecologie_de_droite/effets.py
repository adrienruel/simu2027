"""Effets économiques du programme « Écologie de droite », recodés en mesures sur le noyau commun (12 novembre 2026).

Avant cette date, ces effets sortaient de moteur/macro.py, un moteur propre au programme (vingt canaux additifs).
Ils sont maintenant calculés ici, à partir des mêmes paramètres, sous forme de mesures contre le statu quo ; tout
ce qui est mécanique commune vient du noyau et de la chaîne des programmes simples :

- multiplicateur de l'impulsion budgétaire, dissipation, scénario miroir, capacité (programme_simple.multiplicateur) ;
- chômage de conjoncture (loi d'Okun), emplois et chômeurs des seniors (offre.seniors) ;
- intérêts, prime de dette, effet de Fisher, dette et déficit (noyau.trajectoire) ;
- règle de trajectoire (noyau.Regle) : la cible, l'ordre des leviers et l'arithmétique sont au noyau ; ici, la
  description de ce que chaque levier (contribution d'épargne, revenu universel) rapporte et déclenche.

Ce qui reste propre au programme, parce que c'est une réforme du programme et non une mécanique :
- les emplois des réformes (14 chômeurs repris par canal, emploi_canaux), l'activité des inactifs, les seniors à
  long terme et le cumul emploi-retraite ;
- le logement, l'érosion de l'IS (localisation), la fraude à la TVA, la productivité, l'IA, l'école, les réactions
  des hauts revenus, l'investissement des entreprises (IS), le permis rapide, les dirigeants de petites sociétés ;
- le fonds d'épargne retraite (`Fonds`, une dynamique du noyau) : son capital grossit avec l'épargne, rapporte au
  PIB et à l'État, et dépend de la dette (part à l'étranger) et de la règle (contribution) ; il faut donc l'avancer
  année par année avec les comptes.

Ce qui n'existe plus : le canal « ajustement budgétaire » (effort de 2029 saisi), remplacé par l'impulsion des
mesures elles-mêmes ; les canaux « démographie » et « tendance » ne sont plus des effets sur le PIB (le statu quo de
chaque scénario porte déjà sa population, sa tendance et l'IA) ; ils restent des mesures de recettes d'écart de
méthode tant que le registre budgétaire (budget.py) est calculé sur la tendance et la population du prudent.
"""
from __future__ import annotations

from moteur.reformes_structurelles import gain as gain_reformes

import math

from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Levier, Mesure, Regle
from moteur.parametres import Parametres

from . import budget


def montee(t: int, annees: float) -> float:
    return min(1.0, (t - 2029 + 1) / annees)


def dividende_croissance(q: Parametres, pib0: dict) -> dict[int, float] | None:
    """Part d'un euro de PIB en plus (productivité) qui passe au solde primaire du programme, année par année.

    Calculée sur le programme lui-même (05/11/2026) : les postes sont recalculés avec une tendance de productivité
    relevée de macro.ecart_dividende, et le dividende est l'écart de solde primaire rapporté à l'écart de PIB. Chaque
    poste suit alors sa propre règle. None : ancienne convention (v235)."""
    if not q.val("macro.dividende_calcule") or getattr(q, "_calcul_dividende", False):
        return None
    d = q.val("macro.ecart_dividende")
    g = q.val("macro.tendance", "prudent")
    # sans l'accise sur les produits nocifs : règle de financement du surplus de santé, plafonnée (non linéaire) ;
    # la garder rendait le dividende instable d'une variante à l'autre (relecture des tests, 05/11/2026)
    base = {"sante_produits_nocifs.active": False} if q.val("sante_produits_nocifs.active") else {}
    q0 = q.avec(base) if base else q
    qd = q.avec({**base, "macro.tendance": g + d})
    for x in (q0, qd):
        x.colonne_prudent, x._surcharges = q.colonne_prudent, q._surcharges
        x._calcul_dividende = True
    traj = budget.postes(q0, "prudent")
    traj_d = budget.postes(qd, "prudent")
    out = {}
    for t in ANNEES:
        dp = pib0[t] * (((1 + g + d) / (1 + g)) ** (t - 2029) - 1)
        out[t] = (traj_d[t]["solde_primaire_hors_macro"] - traj[t]["solde_primaire_hors_macro"]) / dp if dp else 0.0
    out[2029] = out[2030]
    return out


class Effets:
    """Effets du programme dans un scénario. p : paramètres du statu quo ; q : ceux du programme (copie de crise pour
    le scénario de crise) ; s : scénario du noyau ; jeu : jeu de paramètres (crise → prudent de la copie de crise)."""

    def __init__(self, p: Parametres, q: Parametres, s: str, jeu: str) -> None:
        self.p, self.q, self.s, self.jeu = p, q, s, jeu
        self.m = lambda cle, sc=None: q.val(f"macro.{cle}", jeu)
        self._preparer()

    # ------------------------------------------------------------------------------------------ préparation
    def _preparer(self) -> None:
        p, q, s, jeu, m = self.p, self.q, self.s, self.jeu, self.m
        from moteur.emploi import entrees_macro, participation_inactifs, population_active, cout_smic_annuel
        from moteur.hauts_revenus import baisse_revenus_declares, reactions
        from moteur.demographie import chomage_tendanciel, indices as indices_demo
        from moteur import is_investissement as isi
        from moteur import sante as module_sante
        from moteur.carbone import effet_solde
        from moteur.recettes.total import ligne_3_tva, recettes_nouveau_systeme
        from moteur.unites import facteur
        from moteur.logement import reprise_amortissements
        from moteur.mesures import ecart_scenario
        self.tend0 = tend0 = q.val("macro.tendance", "prudent")
        self.corr = corr = q.val("macro.corrections_relecture")
        pv = entrees_macro(q)
        self.pv = {k: v[jeu] for k, v in pv.items() if isinstance(v, dict) and jeu in v}
        self.pv_brut = pv
        self.ri = reactions(q)[jeu]
        self.baisse_declares = baisse_revenus_declares(q)[jeu]
        pi = participation_inactifs(q)
        self.inactifs_terme = pi["crise"] if (jeu == "prudent" and q.colonne_prudent == "crise") else pi[jeu]
        pib_2026 = 2920 * facteur(q, 2024, "recettes")
        demo = {x: indices_demo(q, x) for x in ("prudent", "median", "optimiste")}
        self.demo = demo
        self.dp, self.ds = demo["prudent"], demo[jeu]
        # PIB de référence du programme (économie de 2026 placée en 2029, démographie du prudent) : sert d'échelle aux
        # canaux propres au programme et au dividende de croissance ; le PIB publié part du statu quo du scénario
        self.pib0 = {t: pib_2026 * (1 + tend0) ** (t - 2029) * self.dp[t]["emploi"] for t in ANNEES}
        self.y_sq = sq.pib(p, s)
        self.n = {t: t - 2029 for t in ANNEES}
        self.croiss = {t: (1 + tend0) ** (t - 2029) for t in ANNEES}
        rec = recettes_nouveau_systeme(q)["total"] / 1e9
        self.part_budget = part_budget = rec / pib_2026
        par_revenu = q.val("macro.impots_par_revenu") and q.val("cohortes.active") and q.val("demographie.active")
        if par_revenu:
            from moteur.cohortes import agregats
            from moteur.is_bareme import taux_local, taux_moyen
            a = agregats(q)
            taux_salaires = {t: (a[t]["impot"] + a[t]["local"] + a[t]["tva"]) / a[t]["masse"] for t in ANNEES}
            self.taux_benefices = taux_moyen(q) + taux_local(q)
            part_sal_va = 1 - q.val("emploi.taux_marge_snf") - q.val("emploi.impots_production_va")
            self.taux_va = {t: part_sal_va * taux_salaires[t] + (1 - part_sal_va) * self.taux_benefices for t in ANNEES}
        else:
            self.taux_benefices = part_budget
            self.taux_va = {t: part_budget for t in ANNEES}
        self.par_revenu = par_revenu
        self.traj = budget.postes(q, "prudent")
        # phase A7 (13/11/2026) : l'IA du statu quo, absente du registre, est comptée par le registre lui-même, recalculé
        # avec la tendance relevée du rythme de l'IA (grand pas, stable), puis ramené chaque année au niveau de l'IA
        # atteint (k_t) ; remplace le dividende à petit pas (q_div), instable d'une année à l'autre
        self.ia_registre = None
        if q.val("macro.registre_par_scenario") and not getattr(q, "_calcul_dividende", False):
            # (pas dans les copies de calcul : la déduction de l'investissement y relance une simulation complète)
            ia = q.val("macro.ia_productivite", jeu)
            if ia:
                qi = q.avec({"macro.tendance": tend0 + ia})
                qi.colonne_prudent, qi._surcharges, qi._calcul_dividende = q.colonne_prudent, q._surcharges, True
                ti, t0 = budget.postes(qi, "prudent"), self.traj
                d0, d1 = q.val("macro.premiere_annee_ia"), q.val("macro.annees_ia")
                self.ia_registre = {}
                r = 0.0
                for t in ANNEES:
                    r = (1 + r) * (1 + ia * (d0 <= t < d0 + d1)) - 1
                    bump = ((1 + tend0 + ia) / (1 + tend0)) ** (t - 2029) - 1  # niveau du registre relevé (0 en 2029)
                    if bump:
                        self.ia_registre[t] = r / bump * (ti[t]["solde_primaire_hors_macro"] - t0[t]["solde_primaire_hors_macro"])
                # 2029 : registre relevé égal au registre de base ; même rapport que 2030, au niveau de l'IA de 2029
                r30 = (1 + ia) ** 2 - 1
                self.ia_registre[2029] = self.ia_registre[2030] * ia / r30
        self.dividende = dividende_croissance(q, self.pib0)
        self.q_div = self.dividende if self.dividende is not None else {t: q.val("macro.part_pib_tendanciel_au_solde") for t in ANNEES}
        self.div_sq = sq.dividende_productivite(p, s)
        from moteur.canaux_declares import facteur_ia
        self.k_ia = facteur_ia(p, s, q.val("macro.adoption_ia_budget"))
        from moteur import fraude as fr
        self.fraude = fr.effets(p, s, q.val("macro.fraude_controle"))
        self.bases_demo = budget.lignes(q, "prudent").bases_demographie
        self.cle_indice = {"recettes": "emploi", "recettes_population": "total", "salaries_impot": "c_impot",
                           "salaries_tva": "c_tva", "salaries_rui": "c_rui", "adultes": "adultes", "enfants": "enfants",
                           "total": "total"}
        # entreprises
        from moteur.recettes import entreprises
        from moteur.is_bareme import taux_grandes
        self.j20 = entreprises.is_beneficiaires(q) / 1e9
        self.s17 = (q.val("entreprises.taux_is_etat") + q.val("impot_local_entreprises.taux_communes")
                    + q.val("impot_local_entreprises.taux_regions"))
        self.s17_ge = (taux_grandes(q) + q.val("impot_local_entreprises.taux_communes")
                       + q.val("impot_local_entreprises.taux_regions"))
        self.isv = isv = isi.entrees_macro(q)
        self.l25 = dict(zip(ANNEES, isv["ligne25"]))
        self.b20 = isv["b20"][jeu]
        # santé, carbone
        dep_s = {x: module_sante.depenses(q, x) for x in ("prudent", "median", "optimiste")}
        tv = module_sante.tva_sante(q)
        gf_s = module_sante.garde_fou(q, "prudent")
        gf_sc = ({x: module_sante.garde_fou(q, x) for x in ("median", "optimiste")} if q.val("sante_produits_nocifs.active")
                 else {x: {t: 0.0 for t in ANNEES} for x in ("median", "optimiste")})
        self.sante = ({t: 0.0 for t in ANNEES} if (jeu == "prudent" or q.colonne_prudent == jeu)
                      else {t: dep_s["prudent"][t] - gf_s[t] - dep_s[jeu][t] + gf_sc[jeu][t] for t in ANNEES})
        self.tva_sante = tv[jeu]
        self.carbone = effet_solde(q, ligne_3_tva(q) / 1e9)[jeu]
        self.eco_ecart = ecart_scenario(q, jeu) if jeu != "prudent" else {t: 0.0 for t in ANNEES}
        self.logement104 = reprise_amortissements(q)
        # emploi
        self.pa = population_active(q)
        self.dyn_ch = q.val("chomage.dynamique") and q.val("demographie.active")
        self.ct = chomage_tendanciel(q, jeu)
        self.k_pa = self.pa / self.ct[2026]["actifs"]
        self.u_inc = q.val("emploi.chomage_incompressible")
        self.ecart_26 = q.val("chomage.taux_2026") - self.u_inc
        self.cout_smic = cout_smic_annuel(q)
        self.va_emploi = self.pv_brut["valeur_ajoutee_par_emploi"]["valeur"]
        from moteur.ancien_systeme import retraites_reportes
        self.lien_reportes = q.val("macro.seniors_lies_aux_reportes") and q.val("ancien_systeme.par_generation") and q.val("demographie.active")
        self.reportes = {t: v * 1e6 for t, v in retraites_reportes(q).items()} if self.lien_reportes else None
        # entreprises par taille
        from moteur import entreprises_cellules as ec
        self.ec = ec
        self.ent_cellules = ec.actif(q)
        self.k_productif = sum(ec.capital_productif(q).values())
        self.intensite = ec.intensite_emploi(q)
        self._serie_entreprises()
        self._serie_pib_et_solde()

    def _serie_entreprises(self) -> None:
        """Investissement des entreprises (IS) et capital du permis rapide : ne dépendent pas des comptes."""
        q, jeu, m = self.q, self.jeu, self.m
        self.k_inv, self.k_inv_tailles, self.k_permis = {}, {}, {}
        k_inv, k_perm, tailles = 0.0, 0.0, {}
        cout_capital = (((1 - self.s17 * self.isv["b18"]) / (1 - self.s17)) / ((1 - self.isv["b19"] * self.isv["b18"]) / (1 - self.isv["b19"]))
                        - 1 - m("reduction_cout_capital_autres"))
        sep = q.val("macro.permis_rapide_separe")
        for t in ANNEES:
            self.k_permis[t] = k_perm  # début d'année
            if self.ent_cellules:
                fl = self.ec.flux_investissement(q, jeu, lambda cle, _s: m(cle), self.isv["b4"] * self.b20 * self.isv["b21"] * self.l25[t],
                                                  par_taille=True)
                for k_, v_ in fl.items():
                    tailles[k_] = tailles.get(k_, 0.0) * (1 - m("usure_capital")) + v_ * montee(t, m("montee_invest"))
                k_inv = sum(tailles.values())
            else:
                k_inv = k_inv * (1 - m("usure_capital")) - m("elasticite_invest") * (
                    cout_capital - self.isv["b4"] * self.b20 * self.isv["b21"] * self.l25[t]) * self.isv["investissement"] * montee(t, m("montee_invest"))
            self.k_inv[t] = k_inv
            self.k_inv_tailles[t] = dict(tailles)
            if sep:
                k_perm = k_perm * (1 - m("usure_capital")) + m("permis_rapide")

    def _serie_pib_et_solde(self) -> None:
        """Séries de PIB (Md€ ajoutés au PIB du statu quo) et de solde (Md€), canal par canal, hors fonds et hors
        règle, avec les emplois."""
        p, q, jeu, m, tend0, corr = self.p, self.q, self.jeu, self.m, self.tend0, self.corr
        from moteur.taux_effectifs import ecart_localisation
        pv, pvb = self.pv, self.pv_brut
        pib, solde, emplois = {}, {}, {}
        for c in ("emploi_reformes", "seniors_long", "inactifs", "logement", "productivite", "hauts_revenus",
                  "ia_adoption", "ecole", "investissement", "permis"):
            pib[c] = {}
        for c in ("emploi", "logement", "aides_construction", "erosion_is", "fraude_tva", "productivite", "reactions",
                  "investissement", "permis", "dirigeants", "ia", "ia_adoption", "ecole", "sante", "tva_sante", "carbone", "eviction",
                  "demographie", "tendance", "economies_registre"):
            solde[c] = {}
        for c in ("reformes", "seniors_long", "cumul", "inactifs"):
            emplois[c] = {}
        tva_point = budget.tva_par_point_eviction(q)
        jeu_eff = "crise" if (jeu == "prudent" and q.colonne_prudent == "crise") else jeu
        r_ecole = r_ia = r_adopt = 0.0
        arb = q.val("entreprises_cellules.arbitrage_tpe") if self.ent_cellules else None
        from moteur.entreprises_cellules import arbitrage_tpe
        for t in ANNEES:
            n = self.n[t]
            # emploi des réformes
            k_ch = max(0.0, self.ct[t]["taux"] - self.u_inc) / self.ecart_26 if self.dyn_ch else 1.0
            fa = self.ds[t]["adultes"] if corr else 1.0
            perdus = fa * (pv["emplois_perdus_subventions"] + pv["emplois_perdus_tardifs"] * (t > pvb["emplois_perdus_tardifs"]["annee"]))
            emp_ref = fa * pv["emplois_terme"] * k_ch * montee(t, m("annees_montee_emploi")) - perdus
            sen_long = fa * m("seniors_long") * max(0, min(1, (t - m("annee_seniors_long") + 1) / m("montee_seniors_long")))
            cumul = fa * m("cumul_emploi_socle") * max(0, min(1, (t - m("annee_cumul") + 1) / m("montee_cumul")))
            inactifs = self.inactifs_terme * montee(t, m("annees_montee_emploi")) * self.ds[t]["adultes"]
            emplois["reformes"][t], emplois["seniors_long"][t], emplois["cumul"][t], emplois["inactifs"][t] = emp_ref, sen_long, cumul, inactifs
            if "solde_reformes_terme" in pv:  # bloc emploi unifié : chaque emploi au gain de son canal
                gc = pv["gains_canaux"]
                solde["emploi"][t] = (fa * pv["solde_reformes_terme"] * k_ch * montee(t, m("annees_montee_emploi"))
                                      - perdus * gc["perdus"] + sen_long * gc["population_active"] + cumul * gc["perdus"]
                                      + inactifs * gc["inactifs"]) / 1e9
            else:
                solde["emploi"][t] = (emp_ref + sen_long + cumul + inactifs) * pv["gain_par_emploi"] / 1e9
            pib["emploi_reformes"][t] = emp_ref * self.va_emploi / 1e9
            pib["seniors_long"][t] = (sen_long + cumul) * self.va_emploi / 1e9
            pib["inactifs"][t] = inactifs * self.va_emploi / 1e9
            # logement
            if n < m("duree_initiale"):
                logements = m("logements_initial") * (1 - m("extinction_aides_construction") * max(0, 1 - (n + 1) / 3))
            else:
                logements = m("logements_croisiere")
            pib["logement"][t] = logements * q.val("logement_dynamique.prix_moyen_ht_neuf") * m("part_additionnelle_logement") / 1e9
            solde["logement"][t] = pib["logement"][t] * self.part_budget + self.logement104[t]
            solde["aides_construction"][t] = -m("extinction_aides_construction") * m("aides_construction") * max(0, 1 - (n + 1) / 3)
            # érosion de l'IS (localisation) et fraude à la TVA
            ecart_eff = ecart_localisation(q, jeu_eff, t)
            if ecart_eff is None:
                taux = (self.s17 - m("taux_reference_is")) * (m("semi_elasticite_transfert") * m("part_grandes_entreprises") + m("reaction_reelle"))
            else:
                taux = ((self.s17_ge - m("taux_reference_is")) * m("semi_elasticite_transfert") * m("part_grandes_entreprises")
                        + ecart_eff / 100 * m("reaction_reelle"))
            solde["erosion_is"][t] = -self.j20 * self.croiss[t] * taux * montee(t, m("montee_erosion_is"))
            # barème commun de la fraude (phase B5, moteur/fraude.py) : recettes moins coût des agents
            solde["fraude_tva"][t] = self.fraude["recettes"][t] - self.fraude["cout"][t]
            # productivité (réforme du programme), sur le PIB du statu quo du scénario
            y = self.y_sq[t]
            # barème commun des réformes de structure (12/11/2026, moteur/reformes_structurelles.py)
            pib["productivite"][t] = y * gain_reformes(q, q.val("macro.reformes_programme"), jeu, t)
            # gains de productivité : dividende de productivité du statu quo, la même règle que pour tous les programmes
            # (relecture neutre n° 2, point 1, décision d'Adrien du 12/11/2026) ; q_div (dividende du budget du
            # programme) ne sert plus qu'aux écarts de méthode (tendance, IA du statu quo)
            solde["productivite"][t] = pib["productivite"][t] * self.div_sq[t]
            # tendance et IA : le statu quo du scénario les porte déjà dans son PIB ; le budget du programme (calculé sur
            # la tendance du prudent, sans IA) en est écarté, d'où une mesure de recettes d'écart de méthode
            pib_tend = self.pib0[t] * (((1 + m("tendance")) / (1 + tend0)) ** n - 1) if jeu != "prudent" else 0.0
            base = self.pib0[t] + pib_tend
            g_ia = m("ia_productivite") * (q.val("macro.premiere_annee_ia") <= t < q.val("macro.premiere_annee_ia") + q.val("macro.annees_ia"))
            r_ia = (1 + r_ia) * (1 + g_ia) - 1
            pib_ia = base * r_ia
            r_adopt = (1 + r_adopt) * (1 + g_ia * m("adoption_ia") * self.k_ia) - 1  # proportionnel au budget (B6)
            pib["ia_adoption"][t] = (y) * r_adopt  # l'IA du statu quo est déjà dans y
            solde["ia"][t] = (self.ia_registre[t] if self.ia_registre is not None
                              else pib_ia * self.q_div[t])  # écart de méthode : l'IA du statu quo, absente du budget
            solde["ia_adoption"][t] = (base + pib_ia) * r_adopt * self.div_sq[t]  # canal du programme
            g_ecole = m("niveau_eleves") * m("croissance_par_ecart_type") * min(1, max(0, (t - q.val("macro.premiere_annee_ecole") + 1) / q.val("macro.annees_ecole")))
            r_ecole = (1 + r_ecole) * (1 + g_ecole) - 1
            pib["ecole"][t] = y * r_ecole
            solde["ecole"][t] = pib["ecole"][t] * self.div_sq[t]
            solde["tendance"][t] = pib_tend * self.q_div[t]
            solde["economies_registre"][t] = self.eco_ecart[t]
            # réactions à l'impôt, hauts revenus
            ri = self.ri
            solde["reactions"][t] = -ri["montant"] * min(1, (n + 1) / ri["montee"]) * self.croiss[t]
            pib["hauts_revenus"][t] = -self.baisse_declares * m("part_reelle_hauts_revenus") * min(1, (n + 1) / ri["montee"]) * self.croiss[t]
            # investissement des entreprises
            k_inv = self.k_inv[t]
            pib["investissement"][t] = k_inv * (m("pib_par_euro_capital") + m("usure_capital"))
            solde["investissement"][t] = (k_inv * m("pib_par_euro_capital") * self.taux_benefices if (corr and self.par_revenu)
                                          else (k_inv * m("pib_par_euro_capital") if corr else pib["investissement"][t]) * self.part_budget)
            # permis rapide : capital privé à part
            sep = q.val("macro.permis_rapide_separe")
            kp = self.k_permis[t]
            pib["permis"][t] = kp * (m("pib_par_euro_capital") + m("usure_capital")) if sep else 0.0
            solde["permis"][t] = ((kp * m("pib_par_euro_capital") * self.taux_benefices - q.val("macro.permis_rapide_cout") * self.croiss[t])
                                  if sep else 0.0)
            solde["dirigeants"][t] = (-arbitrage_tpe(q, jeu)["perte"] * min(1.0, (n + 1) / arb["montee"]) * self.croiss[t]) if arb else 0.0
            # santé, TVA santé, carbone, éviction de l'épargne volontaire : écarts de scénario du registre
            solde["sante"][t] = self.sante[t]
            solde["tva_sante"][t] = self.tva_sante[t]
            solde["carbone"][t] = self.carbone[t]
            solde["eviction"][t] = (m("eviction") - q.val("macro.eviction", "prudent")) * tva_point * self.croiss[t]
            # démographie : budget calculé sur la population du prudent
            dp, ds = self.dp[t], self.ds[t]
            solde["demographie"][t] = sum(b * (ds[self.cle_indice[k]] - dp[self.cle_indice[k]]) for k, b in self.bases_demo[t].items())
        # phase A1 (12/11/2026) : dividende recalculé par le noyau sur le profil de gain du programme (réformes, IA,
        # école réunies), comme pour les autres programmes (statu_quo.dividende_programme)
        dpib_prod = {t: pib["productivite"][t] + pib["ia_adoption"][t] + pib["ecole"][t] for t in ANNEES}
        div_prog = sq.dividende_programme(self.p, self.s, dpib_prod)
        for c in ("productivite", "ia_adoption", "ecole"):
            for t in ANNEES:
                if self.div_sq[t]:
                    solde[c][t] *= div_prog[t] / self.div_sq[t]
        self.div_programme = div_prog
        self.pib, self.solde, self.emplois = pib, solde, emplois

    # ------------------------------------------------------------------------------------------ mesures
    LIBELLES = {
        "emploi": "Emploi : réformes, seniors à long terme, cumul emploi-retraite, inactifs",
        "logement": "Logement : constructions en plus (TVA, impôts) et reprise des amortissements",
        "aides_construction": "Logement : fin des aides à la construction",
        "erosion_is": "Entreprises : érosion de l'IS (localisation des bénéfices)",
        "fraude_tva": "Lutte contre la fraude (barème commun, net du coût des agents)",
        "productivite": "Productivité (réformes de structure, barème commun)",
        "reactions": "Réactions des hauts revenus à l'impôt",
        "investissement": "Investissement des entreprises (déduction immédiate, IS)",
        "permis": "Permis de construire rapide",
        "dirigeants": "Dirigeants de petites sociétés qui se versent un salaire",
        "ecole": "École (niveau des élèves)",
        "ia_adoption": "Adoption de l'IA (en plus du statu quo)",
        "tva_sante": "Santé : TVA sur les dépenses de santé du scénario",
        "carbone": "Carbone : recette du scénario",
        "eviction": "Épargne obligatoire qui évince l'épargne volontaire (TVA), écart au prudent",
    }
    METHODE = {
        "ia": "Écart de méthode : IA du statu quo (le budget du programme est calculé sans l'IA du statu quo)",
        "tendance": "Écart de méthode : tendance du scénario (le budget du programme est calculé sur la tendance du prudent)",
        "demographie": "Écart de méthode : démographie du scénario (le budget du programme est calculé sur la population du prudent)",
        "economies_registre": "Écart de méthode : économies datées du registre, estimées par scénario",
        "sante": "Écart de méthode : santé du scénario (budget du programme calculé au prudent)",
    }

    def prelevements_pour_impulsion(self) -> list[Mesure]:
        """Prélèvements portés par un effet, à compter dans l'impulsion budgétaire avec leur poids de demande : la
        recette carbone du scénario pèse sur la consommation (relecture du 11/11/2026). Copies réservées au calcul de
        l'impulsion : les mesures publiées ne portent pas d'instrument (le canal d'offre commun ne s'y applique pas)."""
        return [Mesure("Carbone : recette du scénario", "recettes", dict(self.solde["carbone"]), "effet_macro",
                       instrument="consommation")]

    def mesures(self) -> list[Mesure]:
        out = []
        for c, lib in self.LIBELLES.items():
            out.append(Mesure(f"Effet macro : {lib}", "recettes", dict(self.solde[c]), "effet_macro"))
        for c, lib in self.METHODE.items():
            if self.ia_registre is not None and c in ("tendance", "demographie", "economies_registre", "sante"):
                continue  # phase A7 : le registre du scénario les compte (lignes nulles)
            if self.ia_registre is not None and c == "ia":
                out.append(Mesure("Effet macro : IA du statu quo dans le budget du programme (registre recalculé avec l'IA du "
                                  "scénario)", "recettes", dict(self.solde[c]), "effet_macro"))
                continue
            out.append(Mesure(lib, "recettes", dict(self.solde[c]), "methode"))
        return out

    def pib_direct(self) -> dict[int, float]:
        """PIB en plus du statu quo hors multiplicateur, seniors et fonds (Md€)."""
        return {t: sum(v[t] for v in self.pib.values()) for t in ANNEES}

    def emplois_canaux(self, noms: dict) -> dict[int, dict]:
        return {t: {noms[c]: self.emplois[c][t] for c in self.emplois} for t in ANNEES}

    def jeunes(self) -> dict[int, float]:
        from moteur.carrieres import emplois_entree_plus_tot
        return {t: sum(emplois_entree_plus_tot(self.q, self.jeu, t).values()) for t in ANNEES}

    # ------------------------------------------------------------------------------------------ fonds et règle
    def fonds(self, chomeurs_denominateur: dict, part_rec: dict, multiplicateur_clause) -> "Fonds":
        return Fonds(self, chomeurs_denominateur, part_rec, multiplicateur_clause)


class Fonds:
    """Fonds d'épargne retraite et règle de trajectoire du programme : dynamique du noyau (état d'un scénario).

    Début d'année : capital → PIB, impôts sur son rendement, emplois ; rentes et créances de la règle ; effet
    récessif des baisses du revenu universel décidées les années précédentes (même multiplicateur et même dissipation
    que l'impulsion budgétaire, à partir de l'année suivante). Fin d'année : capital de l'année suivante (épargne
    nouvelle, rendements, contribution prise par la règle, créances rendues), part à l'étranger selon la dette."""

    def __init__(self, E: Effets, denominateur: dict, part_rec: dict, mult_clause) -> None:
        self.E, self.denominateur, self.part_rec, self.mult_clause = E, denominateur, part_rec, mult_clause
        q, jeu, m = E.q, E.jeu, E.m
        self.etr = q.val("macro.etranger")
        self.part_etr = self.etr["depart"]
        self.capital = 0.0
        self.hist_rui: dict[int, float] = {}
        self.part_prelevee: dict[int, float] = {}
        self.creances: dict[int, float] = {}
        self.c_contrib: dict[int, float] = {}
        self.paiement = 0.0
        self.paiements: dict[int, float] = {}
        self.historique: dict[int, dict] = {}
        self.restit = q.val("clause.restitution")
        # contribution de la règle comptée en emprunt aux ménages (décision d'Adrien du 12/11/2026) : hors recettes,
        # dans la dette ; le remboursement à 67 ans est hors solde ; les créances sont déjà dans la dette publiée
        self.emprunt = bool(q.val("clause.contribution_en_emprunt"))
        self.quasi_dette_dans_dette = self.emprunt
        self.acces_socle = int(q.val("epargne.age_acces_socle"))
        from moteur.tva import taux_effectifs as taux_eff
        self.fuite_rui = (1 + sum(taux_eff(q)["modeste"])) if E.corr else 1.0
        self.comptes_actifs = q.val("cohortes.active") and q.val("demographie.active") and E.corr
        from moteur.depenses.statique import subventions_restees, rui_aah
        from moteur.depenses import budget_etat
        cr = {x["mission"]: float(x["credits"]) for x in budget_etat._missions() if x["credits"] != "calcul"}
        repris = (cr["Infrastructures et services de transport"] + cr["Service public de l’énergie, énergie et climat"]
                  + cr["Investir pour la France de 2030"] + q.val("fonds_reprises.investissements_locaux_rentables"))
        self.flux_epargne = budget.flux_epargne_obligatoire(q) / 1e9
        self.flux_brut = self.flux_epargne * (1 - q.val("epargne.contribution_transition"))
        self.repris_net = repris - subventions_restees(q)
        self.b24 = self.flux_brut - self.repris_net * 1.0
        self.rui_total = rui_aah(q) - q.val("rui_complements.aah") - q.val("rui_complements.aide_poste_entreprises_adaptees")
        if self.comptes_actifs:
            from moteur.cohortes import comptes
            self.cpt = comptes(q, jeu)
            self.cal = self.flux_brut / (self.cpt[2029]["versements"] / 1e9)
        from moteur.inflation import indice_reel
        self.idx_reel = indice_reel(q, "prudent")
        if self.restit["active"]:
            from moteur.demographie import population as pop_demo, _tranche
            self.pop_age = pop_demo(q, "prudent")
            self.taux_age = {a: v for k, v in q.val("demographie.taux_emploi_age").items() for a in _tranche(k)}
        from moteur import is_investissement as isi
        c8, c16 = isi.cout_net_etat(q), isi.cout_net_etat(q, etale=True)
        self.gain_etalement = {t: c8[t] - c16[t] for t in ANNEES}
        self.pa_ent = E.ent_cellules and E.dyn_ch

    # --------------------------------------------------------------------------------- dynamique du noyau
    def debut(self, t: int, etat: dict) -> dict:
        E, q, m, n = self.E, self.E.q, self.E.m, self.E.n[t]
        cap = self.capital
        pib_cap = cap * (m("pib_par_euro_capital") + m("usure_capital_fonds") + m("externalites_capital_fonds"))
        pib_epargne = cap * (m("pib_par_euro_capital") + m("usure_capital_fonds"))
        emp_fonds = 0.0
        if self.pa_ent:
            k_eff = E.ec.capital_efficace(q, cap / (1 + E.tend0) ** n) if cap > 0 else 0.0
            k_eff += sum(v * E.intensite[k] for k, v in E.k_inv_tailles[t].items())
            y_add = (pib_cap + E.k_inv[t] * (m("pib_par_euro_capital") + m("usure_capital")) * (1 + E.tend0) ** n) / E.pib0[t]
            x_k = math.log(max(1e-9, 1 + k_eff / E.k_productif)) - math.log(max(1e-9, 1 + y_add))
            du = q.val("entreprises_cellules.capital_chomage_elasticite", E.jeu) * E.ct[t]["taux"] * x_k
            du = min(du, max(0.0, E.ct[t]["taux"] - E.u_inc))
            emp_fonds = du * E.ct[t]["actifs"] * E.k_pa
        pib_emp = emp_fonds * E.cout_smic / 1e9 * (1 + E.tend0) ** n
        s_emp = emp_fonds * E.pv["gains_canaux"]["offre"] / 1e9 * (1 + E.tend0) ** n if "gains_canaux" in E.pv else 0.0
        s_cap = ((cap * (m("pib_par_euro_capital") * E.taux_benefices + m("externalites_capital_fonds") * E.taux_va[t])
                  if E.par_revenu else cap * (m("pib_par_euro_capital") + m("externalites_capital_fonds")) * E.part_budget)
                 if E.corr else pib_cap * E.part_budget)
        # règle : créances rendues avec le rendement du fonds, payées au départ à 67 ans ; ou socle en plus
        sortie = 0.0
        self.paiement = 0.0
        if self.restit["active"]:
            self.quasi_dette_debut = sum(self.creances.values())  # stock dû en début d'année (intérêts, noyau)
            for g in list(self.creances):
                self.creances[g] *= 1 + q.val("epargne.rendement_fonds")
            if t >= self.restit["debut"]:
                self.paiement = sum(v for g, v in self.creances.items() if g + self.acces_socle <= t)
                for g in [g for g in self.creances if g + self.acces_socle <= t]:
                    del self.creances[g]
            if not self.emprunt:  # emprunt : rembourser la dette n'est pas une dépense
                sortie += self.paiement
        elif E.corr:
            from moteur.retraites_transition import socle_supplementaire
            reval = (self.idx_reel[t] - 1) if q.val("revalorisation.rui_aah_socle_croissance") else 0.0
            sortie += socle_supplementaire(q, self.part_prelevee, t) * (1 + reval)
        self.paiements[t] = self.paiement
        # effet récessif des baisses du revenu universel décidées avant t (à partir de l'année suivante)
        dpib_rui = 0.0
        avant_k = 0.0
        for k in sorted(self.hist_rui):
            dpib_rui -= self.mult_clause(k, t, self.hist_rui[k] - avant_k)
            avant_k = self.hist_rui[k]
        e = sq.effectifs(E.p, E.s)
        k_emp = sq._v(E.p, "macro.emplois_par_point_pib", E.s)
        conj = dpib_rui / E.y_sq[t] * k_emp * e[t]["emploi"]
        cpt_t = ({"encours_comptes": self.cpt[t]["encours"] / 1e9 * self.cal, "rentes": self.cpt[t]["paiements"] / 1e9 * self.cal}
                 if self.comptes_actifs else {})
        self.historique[t] = {**cpt_t, "capital": cap, "pib_epargne_fonds": pib_epargne, "emplois_fonds": emp_fonds, "dpib_rui": dpib_rui,
                              "conjoncture_rui": conj, "paiement": self.paiement, "part_etr": self.part_etr,
                              "creances": sum(self.creances.values()),
                              "solde": s_cap + s_emp - sortie + dpib_rui * self.part_rec[t]}
        return {"pib": pib_cap + pib_emp + dpib_rui,
                "recettes": s_cap + s_emp - sortie + dpib_rui * self.part_rec[t],
                "emploi": emp_fonds + conj,
                "chomage": -(emp_fonds + conj) / self.denominateur[t] * 100,
                "detail": {"fonds": self.historique[t], "pib_hors_consommation": pib_epargne}}

    def fin(self, t: int, etat: dict) -> None:
        E, m, q = self.E, self.E.m, self.E.q
        k = m("part_capital_nouveau") * (1 - m("eviction")) * (1 - self.part_etr)
        sep = q.val("macro.permis_rapide_separe")
        c = self.c_contrib.get(t, 0.0)
        if self.comptes_actifs:
            cpt = self.cpt[t]
            rend_net = (cpt["rendements"] - cpt["paiements"]) / 1e9 * self.cal
            apport = (self.flux_brut * E.ds[t]["c_epargne"] - self.repris_net) * k
            part_k = min(1.0, self.capital / (cpt["encours"] / 1e9 * self.cal)) if cpt["encours"] > 0 else 0.0
            self.capital = (self.capital + apport + rend_net * part_k + (0.0 if sep else m("permis_rapide")) - c * k + self.paiement * k)
        else:
            accumulation = q.val("epargne.rendement_fonds") * m("part_reinvestie") * m("part_capital_nouveau")
            self.capital = (self.capital + self.b24 * E.ds[t]["c_epargne"] * k + (0.0 if sep else m("permis_rapide"))
                            + self.capital * accumulation - c * k + self.paiement * k)
        self.historique[t]["capital_fin"] = self.capital  # fin d'année, après l'épargne et les rendements de l'année
        etr = self.etr
        if etat["maastricht"] >= etr["solde_minimum"]:
            ratio = etat["dette"] / etat["pib_t"]
            self.part_etr = max(self.part_etr, min(etr["plafond"], etr["depart"] + (etr["plafond"] - etr["depart"])
                                                   * max(0, (etr["dette_debut"] - ratio) / (etr["dette_debut"] - etr["dette_plafond"]))))

    def taux_quasi_dette(self) -> float:
        """Rendement réel servi sur les créances des ménages (epargne.rendement_fonds) : le noyau compte en intérêts
        l'écart avec le taux réel de la dette de marché sur le stock de début d'année (phase A6 du 12/11/2026)."""
        return self.E.q.val("epargne.rendement_fonds")

    def quasi_dette(self) -> float:
        """Créances des contributions prises par la règle, dues aux ménages à 67 ans avec le rendement du fonds (Md€,
        fin d'année) : un emprunt aux ménages. Avec clause.contribution_en_emprunt (12/11/2026), il est déjà dans la
        dette publiée (quasi_dette_dans_dette) ; sinon il est hors dette et publié à part (relecture du 11/11/2026)."""
        return sum(self.creances.values())

    # --------------------------------------------------------------------------------- règle de trajectoire
    def regle(self) -> Regle | None:
        E, q = self.E, self.E.q
        if E.jeu not in q.val("clause.scenarios") or not q.val("clause.active"):
            return None
        m = E.m
        fuite = self.fuite_rui

        def cap_point(t):
            return self.flux_epargne / 10 * E.croiss[t] * (E.ds[t]["c_epargne"] if E.corr else 1.0)

        def cap_contribution(t, etat):
            return cap_point(t) * q.val("clause.points_contribution_max")

        def appliquer_contribution(t, x, etat):
            self.c_contrib[t] = x
            self.part_prelevee[t] = (x / cap_point(t) / 10) if cap_point(t) else 0.0
            if self.restit["active"] and x > 0:
                w = {t - a: self.pop_age[t][a] * self.taux_age.get(a, 0.0) for a in range(18, self.acces_socle)}
                tot = sum(w.values())
                for g, v in w.items():
                    self.creances[g] = self.creances.get(g, 0.0) + x * v / tot

        def reval(t):
            return self.idx_reel[t] if q.val("revalorisation.rui_aah_socle_croissance") else 1.0

        def cap_rui(t, etat):
            if E.corr:  # marge jusqu'au plancher, sur le RUI réel de l'année (revalorisation.regle)
                rui_t = q.val("rui.montant") * reval(t)
                base = self.rui_total * reval(t) * E.ds[t]["adultes"]
                return base * max(0.0, 1 - q.val("clause.plancher_rui") / rui_t)
            return self.rui_total / q.val("rui.montant") * 10 * E.croiss[t] * (q.val("rui.montant") - q.val("clause.plancher_rui")) / 10

        def appliquer_rui(t, x, etat):
            self.hist_rui[t] = x

        def ecritures_rui(t, x):
            # une baisse du RUI de x fait perdre la TVA et les accises sur la consommation qu'il finançait : le solde
            # gagne x / (1 + taux des ménages modestes) (relecture du 29/10/2026)
            return [("nouveau:rui_aah", -x), ("recettes", -x * (1 - 1 / fuite))]

        def detail_contribution(t, x, etat):
            return {"points": x / cap_point(t) if cap_point(t) else 0.0}

        def detail_rui(t, x, etat):
            base = self.rui_total * reval(t) * E.ds[t]["adultes"]
            return {"euros": x * q.val("rui.montant") * reval(t) / base if base else 0.0}  # € par mois

        # emprunt : la règle compte la contribution comme si elle couvrait le déficit (règle inchangée), mais rien
        # n'est écrit en recettes ; le déficit publié et la dette la comptent
        ecritures_contribution = (lambda t, x: []) if self.emprunt else None
        leviers = {
            "contribution": Levier("Contribution d'épargne retraite", cap_contribution, 1.0, ecritures_contribution, appliquer_contribution, detail_contribution),
            "rui": Levier("Baisse du revenu universel", cap_rui, 1 / fuite, ecritures_rui, appliquer_rui, detail_rui),
        }
        ordre = [leviers[i] for i in q.val("clause.ordre")]
        etal = lambda t, etat, declenchee: declenchee * self.gain_etalement[t]
        return Regle(q.val("clause.cible"), ordre, int(q.val("clause.derniere_annee")), [etal])
