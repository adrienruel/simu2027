"""Effets macroéconomiques, 2029-2073, scénarios prudent, médian et optimiste (feuille Effets macro).

Chaque scénario part du PIB de référence (économie de 2026 placée en 2029, tendance de 0,7 %) et du
solde primaire hors effets macro, puis ajoute des effets sur le PIB et sur le solde ; la charge de la
dette et la dette se calculent année par année.

FIDELITE_V235 regroupera les écarts de la v235 reproduits volontairement (aucun à ce jour dans cette feuille).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .parametres import Parametres
from .recettes.total import recettes_nouveau_systeme
from .recettes import entreprises
from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public
from .recettes.tva_menages import part_rui_agent
from .epargne import epargne_annuelle, part_rui_salarie
from .retraites_transition import cout_transition
from .unites import facteur

ANNEES = list(range(2029, 2074))
SCENARIOS = ("prudent", "median", "optimiste")

FIDELITE_V235: dict[str, bool] = {}


@dataclass
class Scenario:
    nom: str
    pib_effet: dict = field(default_factory=dict)
    solde_effet: dict = field(default_factory=dict)
    emplois: dict = field(default_factory=dict)
    charge_dette: dict = field(default_factory=dict)
    solde_public: dict = field(default_factory=dict)
    dette: dict = field(default_factory=dict)
    maastricht: dict = field(default_factory=dict)
    dette_pib: dict = field(default_factory=dict)
    clause: dict = field(default_factory=dict)
    detail: dict = field(default_factory=dict)


def flux_epargne_obligatoire(p: Parametres, scenario: str = "prudent") -> float:
    """Total!B63 : épargne obligatoire annuelle des salariés et des agents (€)."""
    d = effectifs_prive_2026(p)
    total = sum(n * epargne_annuelle(c, p, scenario, part_rui_salarie(c, p), contribution=False) for c, n in zip(d.milieux, d.effectifs))
    d, a = effectifs_public_2026(p), facteur_alignement_public(p)
    total += sum(n * epargne_annuelle(c * a, p, scenario, part_rui_agent(c), contribution=False) for c, n in zip(d.milieux, d.effectifs))
    return total


def tva_par_point_eviction(p: Parametres, scenario: str = "prudent") -> float:
    """Total!B70 : TVA en plus si toute l'épargne obligatoire évinçait l'épargne volontaire (Md€)."""
    from .recettes.tva_menages import budget_actif
    total = 0.0
    d = effectifs_prive_2026(p)
    for c, n in zip(d.milieux, d.effectifs):
        b = budget_actif(c, p, scenario, part_rui_salarie(c, p))
        total += n * (b["oblig"] * b["taux"] / (1 + b["taux"]) if b["volontaire"] > 0 else 0.0)
    d, a = effectifs_public_2026(p), facteur_alignement_public(p)
    for c, n in zip(d.milieux, d.effectifs):
        b = budget_actif(c * a, p, scenario, part_rui_agent(c))
        total += n * (b["oblig"] * b["taux"] / (1 + b["taux"]) if b["volontaire"] > 0 else 0.0)
    return total / 1e9


def _montee(t, annees):
    return min(1.0, (t - 2029 + 1) / annees)


def calculer(p: Parametres, scenario_retenu: str = "prudent") -> dict[str, Scenario]:
    pv: dict = {}
    from .emploi import entrees_macro, population_active
    pv.update(entrees_macro(p))
    from .hauts_revenus import reactions, baisse_revenus_declares
    pv["reactions_impot"] = reactions(p)
    pv["baisse_revenus_declares"] = baisse_revenus_declares(p)
    pa = population_active(p)
    m = lambda cle, s: p.val(f"macro.{cle}", s)
    tend0 = m("tendance", "prudent")
    pib_2026 = 2920 * facteur(p, 2024, "recettes")  # Total!F18, Md€
    from .demographie import indices as indices_demo
    demo = {s_: indices_demo(p, s_) for s_ in SCENARIOS}  # « prudent » lit la colonne de crise dans le calcul de crise
    pib0 = {t: pib_2026 * (1 + tend0) ** (t - 2029) * demo["prudent"][t]["emploi"] for t in ANNEES}
    rec = recettes_nouveau_systeme(p)["total"] / 1e9
    part_budget = rec / pib_2026  # Total!F19
    from .trajectoire_annuelle import postes
    traj = postes(p, scenario_retenu)
    from .trajectoire_annuelle import lignes as lignes_traj
    bases_demo = lignes_traj(p, scenario_retenu).bases_demographie
    cle_indice = {"recettes": "emploi", "adultes": "adultes", "enfants": "enfants", "total": "total"}
    sp_hors = {t: traj[t]["solde_primaire_hors_macro"] for t in ANNEES}
    from .calendrier import dette_fin_2028, transferts_collectivites
    transferts = {t: transferts_collectivites(p) for t in ANNEES}
    dette0 = dette_fin_2028(p)
    infl = p.val("calendrier.inflation")
    participations = {t: v["participations"] for t, v in cout_transition(p).items()}
    j20 = entreprises.is_beneficiaires(p) / 1e9
    s17 = p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    from .depenses.statique import subventions_restees
    from .depenses import budget_etat
    cr = {x["mission"]: float(x["credits"]) for x in budget_etat._missions() if x["credits"] != "calcul"}
    repris = (cr["Infrastructures et services de transport"] + cr["Service public de l’énergie, énergie et climat"]
              + cr["Investir pour la France de 2030"] + p.val("fonds_reprises.investissements_locaux_rentables"))
    # Part des investissements publics reprise par le fonds : 100 % (Total!B71)
    b24 = flux_epargne_obligatoire(p) / 1e9 * (1 - p.val("epargne.contribution_transition")) - (repris - subventions_restees(p)) * 1.0
    rendement = p.val("epargne.rendement_fonds")
    etr = p.val("macro.etranger")
    from . import is_investissement as module_isi
    isv = module_isi.entrees_macro(p)
    l25 = dict(zip(ANNEES, isv["ligne25"]))
    from . import sante as module_sante
    dep_s = {s_: module_sante.depenses(p, s_) for s_ in SCENARIOS}
    gf_s = module_sante.garde_fou(p, scenario_retenu)
    tv = module_sante.tva_sante(p)
    sante = {"median": {t: dep_s["prudent"][t] - gf_s[t] - dep_s["median"][t] for t in ANNEES},
             "optimiste": {t: dep_s["prudent"][t] - gf_s[t] - dep_s["optimiste"][t] for t in ANNEES},
             "tva_prudent": tv["prudent"], "tva_median": tv["median"], "tva_optimiste": tv["optimiste"]}
    from .carbone import effet_solde
    from .recettes.total import ligne_3_tva
    carbone = effet_solde(p, ligne_3_tva(p) / 1e9)
    from .logement import reprise_amortissements
    logement104 = reprise_amortissements(p)
    personnes_en_emploi = p.val("inactifs.chomeurs_bit") / p.val("chomage.taux_2026") - p.val("inactifs.chomeurs_bit")
    rui_ch = personnes_en_emploi * p.val("rui.montant") * 12 / 1e9
    va = pv["valeur_ajoutee_par_emploi"]["valeur"]

    # Taux d'intérêt (lignes 204 à 222)
    def taux_reel(t, s):
        nominal = min(p.val("macro.taux_long_terme"),
                      p.val("macro.taux_apparent_2029") + (p.val("macro.taux_long_terme") - p.val("macro.taux_apparent_2029")) * (t - 2029) / p.val("macro.annees_taux_long_terme"))
        return nominal - infl - m("baisse_spread", s) * min(1.0, max(0, t - 2029) / p.val("macro.annees_baisse_spread"))

    from .depenses.statique import rui_aah
    flux_epargne = flux_epargne_obligatoire(p) / 1e9
    rui_total = rui_aah(p) - p.val("rui_complements.aah") - p.val("rui_complements.aide_poste_entreprises_adaptees")
    c8, c16 = module_isi.cout_net_etat(p), module_isi.cout_net_etat(p, etale=True)
    gain_etalement = {t: c8[t] - c16[t] for t in ANNEES}
    etalement_declenche = None

    from .anciennes_pensions import recette_nette
    traj_anc_2029 = recette_nette(p)[2029]
    tva_point = tva_par_point_eviction(p)
    out = {}
    for s in ("median", "optimiste", "prudent"):  # la clause du prudent se cale sur le médian
        sc = Scenario(s)
        eff = m("effort_2029", s) + traj_anc_2029 / pib0[2029] - p.val("macro.assouplissement_2029")
        if s == "prudent" and p.colonne_prudent == "crise":
            eff = p.val("crise.effort_2029_saisi")  # Effets macro!B19 saisi dans le scénario de crise
        from .taux_effectifs import ecart_localisation
        ecart_eff = ecart_localisation(p, "crise" if (s == "prudent" and p.colonne_prudent == "crise") else s)
        if ecart_eff is None:
            erosion_taux = (s17 - m("taux_reference_is", s)) * (m("semi_elasticite_transfert", s) * m("part_grandes_entreprises", s) + m("reaction_reelle", s))
        else:  # transfert de bénéfices : taux légal ; réaction réelle : taux effectif moyen (déduction comprise)
            erosion_taux = ((s17 - m("taux_reference_is", s)) * m("semi_elasticite_transfert", s) * m("part_grandes_entreprises", s)
                            + ecart_eff / 100 * m("reaction_reelle", s))
        cout_capital = (((1 - s17 * isv["b18"]) / (1 - s17)) / ((1 - isv["b19"] * isv["b18"]) / (1 - isv["b19"])) - 1
                        - m("reduction_cout_capital_autres", s))
        accumulation = rendement * m("part_reinvestie", s) * m("part_capital_nouveau", s)
        capital, k_inv, part_etr = 0.0, 0.0, etr["depart"]
        dette_prec = dette0
        r_ecole = r_ia = r_adopt = 0.0
        for t in ANNEES:
            n = t - 2029
            # Emploi
            emp_ref = (pv["emplois_terme"][s] * _montee(t, m("annees_montee_emploi", s)) - pv["emplois_perdus_subventions"][s]
                       - pv["emplois_perdus_tardifs"][s] * (t > pv["emplois_perdus_tardifs"]["annee"]))
            emp_sen = (m("seniors_court", s) * _montee(t, m("montee_seniors_court", s))
                       + m("seniors_long", s) * max(0, min(1, (t - m("annee_seniors_long", s) + 1) / m("montee_seniors_long", s)))
                       + m("cumul_emploi_socle", s) * max(0, min(1, (t - m("annee_cumul", s) + 1) / m("montee_cumul", s))))
            if "solde_reformes_terme" in pv:  # bloc emploi unifié : chaque emploi au gain de son canal
                gc = pv["gains_canaux"][s]
                seniors = (m("seniors_court", s) * _montee(t, m("montee_seniors_court", s))
                           + m("seniors_long", s) * max(0, min(1, (t - m("annee_seniors_long", s) + 1) / m("montee_seniors_long", s))))
                cumul = emp_sen - seniors
                perdus = (pv["emplois_perdus_subventions"][s]
                          + pv["emplois_perdus_tardifs"][s] * (t > pv["emplois_perdus_tardifs"]["annee"]))
                s_emploi = (pv["solde_reformes_terme"][s] * _montee(t, m("annees_montee_emploi", s))
                            - perdus * gc["perdus"] + seniors * gc["population_active"] + cumul * gc["perdus"]) / 1e9
            else:
                s_emploi = (emp_ref + emp_sen) * pv["gain_par_emploi"][s] / 1e9
            # Ajustement budgétaire
            pib_aj = -eff * m("multiplicateur", s) * max(0, 1 - n / m("annees_effet_ajustement", s)) * pib0[t]
            s_aj = pib_aj * part_budget + pib_aj / pib0[t] * 100 * m("emplois_par_point_pib", s) / 100 * rui_ch
            # Capital du fonds (début d'année)
            pib_cap = capital * m("pib_par_euro_capital", s)
            s_cap = pib_cap * part_budget
            # Logement
            if n < m("duree_initiale", s):
                logements = m("logements_initial", s) * (1 - m("extinction_aides_construction", s) * max(0, 1 - (n + 1) / 3))
            else:
                logements = m("logements_croisiere", s)
            pib_log = logements * p.val("logement_dynamique.prix_moyen_ht_neuf") * m("part_additionnelle_logement", s) / 1e9
            s_log = pib_log * part_budget + logement104[t]
            s_erosion = -j20 * (1 + tend0) ** n * erosion_taux * _montee(t, m("montee_erosion_is", s))
            s_fraude = m("fraude_tva", s) * _montee(t, m("montee_fraude", s))
            s_aides = -m("extinction_aides_construction", s) * m("aides_construction", s) * max(0, 1 - (n + 1) / 3)
            # Productivité, tendance, école, IA
            pib_prod = pib0[t] * ((1 + m("productivite", s)) ** max(0, min(m("annees_productivite", s), t - p.val("macro.premiere_annee_productivite") + 1)) - 1)
            pib_tend = pib0[t] * (((1 + m("tendance", s)) / (1 + tend0)) ** (t - 2028) - 1) if s != "prudent" else 0.0
            base = pib0[t] + pib_tend
            g_ecole = m("niveau_eleves", s) * m("croissance_par_ecart_type", s) * min(1, max(0, (t - p.val("macro.premiere_annee_ecole") + 1) / p.val("macro.annees_ecole")))
            r_ecole = (1 + r_ecole) * (1 + g_ecole) - 1
            pib_ecole = base * r_ecole if s != "prudent" else 0.0
            g_ia = m("ia_productivite", s) * (p.val("macro.premiere_annee_ia") <= t < p.val("macro.premiere_annee_ia") + p.val("macro.annees_ia"))
            r_ia = (1 + r_ia) * (1 + g_ia) - 1
            pib_ia = base * r_ia
            r_adopt = (1 + r_adopt) * (1 + g_ia * m("adoption_ia", s)) - 1
            pib_adopt = (base + pib_ia) * r_adopt
            # Réactions à l'impôt et hauts revenus
            ri = pv["reactions_impot"][s]
            s_react = -ri["montant"] * min(1, (n + 1) / ri["montee"]) * (1 + tend0) ** n
            pib_hr = -pv["baisse_revenus_declares"][s] * m("part_reelle_hauts_revenus", s) * min(1, (n + 1) / pv["reactions_impot"][s]["montee"]) * (1 + tend0) ** n
            # Investissement des entreprises
            k_inv = k_inv * (1 - m("usure_capital", s)) - m("elasticite_invest", s) * (
                cout_capital - isv["b4"] * isv["b20"][s] * isv["b21"] * l25[t]) * isv["investissement"] * _montee(t, m("montee_invest", s))
            pib_inv = k_inv * (m("pib_par_euro_capital", s) + m("usure_capital", s))
            # Démographie : écart au prudent (fécondité et effet sur la natalité du scénario)
            dp, ds = demo["prudent"][t], demo[s][t]
            pib_demo = pib0[t] * (ds["emploi"] / dp["emploi"] - 1)
            s_demo = sum(b * (ds[cle_indice[k]] - dp[cle_indice[k]]) for k, b in bases_demo[t].items())
            # Totaux
            pib = (pib_demo + (emp_ref + emp_sen) * va / 1e9 + pib_aj + pib_cap + pib_log + pib_prod + pib_hr + pib_ia + pib_adopt + pib_inv
                   + pib_tend + pib_ecole)
            q = p.val("macro.part_pib_tendanciel_au_solde")
            solde = (s_demo + s_emploi + s_aj + s_cap + s_log + s_erosion + s_fraude + s_aides + pib_prod * q + s_react
                     + (pib_ia + pib_adopt) * q)
            if s == "prudent":
                solde += (sante["tva_prudent"][t] + pib_inv * part_budget + carbone["prudent"][t]
                          + (m("eviction", s) - m("eviction", scenario_retenu)) * tva_point * (1 + tend0) ** n)
                # Clause de trajectoire : ramène le prudent sur le déficit du médian
                interets_t = taux_reel(t, s) * dette_prec
                pib_t = pib0[t] + pib
                avant = -(sp_hors[t] + solde - transferts[t] - interets_t - infl * dette_prec) / pib_t
                ecart = max(0.0, avant - (-out["median"].maastricht[t])) if p.val("clause.active") else 0.0
                montant = ecart * pib_t
                if etalement_declenche is None:
                    etalement_declenche = 1.0 if ecart > 0 else 0.0
                c_etal = etalement_declenche * gain_etalement[t]
                actif = t <= p.val("clause.derniere_annee")
                cap_point = flux_epargne / 10 * (1 + tend0) ** n
                c_contrib = max(0.0, min(montant - c_etal, cap_point * p.val("clause.points_contribution_max"))) if actif else 0.0
                cap_rui = rui_total / p.val("rui.montant") * 10 * (1 + tend0) ** n
                c_rui = max(0.0, min(montant - c_etal - c_contrib, cap_rui * (p.val("rui.montant") - p.val("clause.plancher_rui")) / 10)) if actif else 0.0
                mesures = c_etal + c_contrib + c_rui
                sc.detail.setdefault("clause", {})[t] = {"avant": avant, "etalement": c_etal, "contribution": c_contrib,
                                                         "points": c_contrib / cap_point if cap_point else 0.0,
                                                         "rui": c_rui, "rui_euros": c_rui / cap_rui * 10 if cap_rui else 0.0,
                                                         "reste": montant - mesures}
            else:
                solde += (sante[s][t] + sante[f"tva_{s}"][t] + (pib_tend + pib_ecole) * q + pib_inv * part_budget + carbone[s][t]
                          + (m("eviction", s) - m("eviction", scenario_retenu)) * tva_point * (1 + tend0) ** n)
                mesures = 0.0
            solde_total = solde + mesures
            # Décomposition par canal (Md€, effet sur le solde), pour la restitution
            if s == "prudent":
                c_sante, c_tva_sante, c_tend = 0.0, sante["tva_prudent"][t], 0.0
                c_carbone = carbone["prudent"][t]
            else:
                c_sante, c_tva_sante, c_tend = sante[s][t], sante[f"tva_{s}"][t], (pib_tend + pib_ecole) * q
                c_carbone = carbone[s][t]
            sc.detail.setdefault("canaux", {})[t] = {
                "emploi": s_emploi, "ajustement_budgetaire": s_aj, "capital_du_fonds": s_cap, "logement": s_log,
                "erosion_is": s_erosion, "fraude_tva": s_fraude, "fin_aides_construction": s_aides,
                "productivite": pib_prod * q, "reactions_impot": s_react, "ia": (pib_ia + pib_adopt) * q,
                "tendance_et_ecole": c_tend, "investissement_entreprises": pib_inv * part_budget,
                "sante": c_sante + c_tva_sante, "carbone": c_carbone,
                "eviction_epargne": (m("eviction", s) - m("eviction", scenario_retenu)) * tva_point * (1 + tend0) ** n,
                "clause": mesures, "demographie": s_demo,
            }
            interets = taux_reel(t, s) * dette_prec
            solde_public = sp_hors[t] + solde_total - transferts[t] - interets
            dette = dette_prec - solde_public - participations[t]
            pib_total = pib0[t] + pib
            maastricht = (solde_public - infl * dette_prec) / pib_total
            sc.pib_effet[t], sc.solde_effet[t], sc.emplois[t] = pib, solde_total, emp_ref + emp_sen
            sc.detail.setdefault("pib_reference", {})[t] = pib0[t]
            sc.charge_dette[t], sc.solde_public[t], sc.dette[t] = interets, solde_public, dette
            sc.maastricht[t], sc.dette_pib[t], sc.clause[t] = maastricht, dette / pib_total, mesures
            # Taux de chômage (Emploi lignes 28 à 30) : hors seniors, effet récessif de la bascule compris
            sc.detail.setdefault("chomage", {})[t] = (p.val("inactifs.chomeurs_bit") - emp_ref
                                                        - pib_aj / pib0[t] * m("emplois_par_point_pib", s) * personnes_en_emploi) / pa
            # Année suivante : capital du fonds, part à l'étranger
            capital = capital + b24 * ds["emploi"] * m("part_capital_nouveau", s) * (1 - m("eviction", s)) * (1 - part_etr) + m("permis_rapide", s) + capital * accumulation
            if maastricht >= etr["solde_minimum"]:
                part_etr = max(part_etr, min(etr["plafond"], etr["depart"] + (etr["plafond"] - etr["depart"]) * max(0, (etr["dette_debut"] - dette / pib_total) / (etr["dette_debut"] - etr["dette_plafond"]))))
            dette_prec = dette
        out[s] = sc
    return {k: out[k] for k in SCENARIOS}
