"""Effets macroéconomiques, 2029-2073, scénarios prudent, médian et optimiste (feuille Effets macro).

Chaque scénario part du PIB de référence (économie de 2026 placée en 2029, tendance de 0,7 %) et du
solde primaire hors effets macro, puis ajoute des effets sur le PIB et sur le solde ; la charge de la
dette et la dette se calculent année par année.

Les termes venant de feuilles pas encore portées sont lus dans reference/entrees_provisoires_macro.json.

FIDELITE_V235 regroupera les écarts de la v235 reproduits volontairement (aucun à ce jour dans cette feuille).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

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
PROVISOIRES = Path(__file__).resolve().parents[1] / "reference" / "entrees_provisoires_macro.json"

FIDELITE_V235: dict[str, bool] = {}


def _prov():
    return json.loads(PROVISOIRES.read_text(encoding="utf-8"))


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


def _montee(t, annees):
    return min(1.0, (t - 2029 + 1) / annees)


def calculer(p: Parametres, scenario_retenu: str = "prudent") -> dict[str, Scenario]:
    pv = _prov()
    m = lambda cle, s: p.val(f"macro.{cle}", s)
    tend0 = m("tendance", "prudent")
    pib_2026 = 2920 * facteur(p, 2024, "recettes")  # Total!F18, Md€
    pib0 = {t: pib_2026 * (1 + tend0) ** (t - 2029) for t in ANNEES}
    rec = recettes_nouveau_systeme(p)["total"] / 1e9
    part_budget = rec / pib_2026  # Total!F19
    sp_hors = dict(zip(ANNEES, pv["solde_primaire_hors_macro"]["serie"]))
    transferts = dict(zip(ANNEES, pv["transferts_collectivites"]["serie"]))
    dette0 = pv["dette_depart"]["valeur"]
    infl = pv["inflation"]["valeur"]
    participations = {t: v["participations"] for t, v in cout_transition(p).items()}
    j20 = entreprises.is_beneficiaires(p) / 1e9
    s17 = p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    fr = pv["fonds_repris"]
    b24 = flux_epargne_obligatoire(p) / 1e9 * (1 - p.val("epargne.contribution_transition")) - (fr["b83"] - fr["d83"]) * fr["total_b71"]
    rendement = p.val("epargne.rendement_fonds")
    etr = p.val("macro.etranger")
    isv = pv["is_investissement"]
    l25 = dict(zip(ANNEES, isv["ligne25"]))
    sante = {k: dict(zip(ANNEES, v)) for k, v in pv["sante_solde"].items() if not k.startswith("_")}
    carbone = {k: dict(zip(ANNEES, v)) for k, v in pv["carbone_solde"].items() if not k.startswith("_")}
    logement104 = dict(zip(ANNEES, pv["logement_solde"]["serie"]))
    clause = dict(zip(ANNEES, pv["clause_mesures"]["serie"]))
    rui_ch = pv["rui_chomeurs_effectif"]["valeur"] * p.val("rui.montant") * 12 / 1e9
    va = pv["valeur_ajoutee_par_emploi"]["valeur"]

    # Taux d'intérêt (lignes 204 à 222)
    def taux_reel(t, s):
        nominal = min(p.val("macro.taux_long_terme"),
                      p.val("macro.taux_apparent_2029") + (p.val("macro.taux_long_terme") - p.val("macro.taux_apparent_2029")) * (t - 2029) / p.val("macro.annees_taux_long_terme"))
        return nominal - infl - m("baisse_spread", s) * min(1.0, max(0, t - 2029) / p.val("macro.annees_baisse_spread"))

    out = {}
    for s in SCENARIOS:
        sc = Scenario(s)
        eff = m("effort_2029", s) + pv["anciennes_pensions_2029"]["valeur"] / pib0[2029] - p.val("macro.assouplissement_2029")
        erosion_taux = (s17 - m("taux_reference_is", s)) * (m("semi_elasticite_transfert", s) * m("part_grandes_entreprises", s) + m("reaction_reelle", s))
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
            pib_log = logements * pv["prix_logement"]["valeur"] * m("part_additionnelle_logement", s) / 1e9
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
            pib_hr = -pv["baisse_revenus_declares"][s] * m("part_reelle_hauts_revenus", s) * min(1, (n + 1) / pv["reactions_impot"]["prudent" if s == "prudent" else s]["montee"]) * (1 + tend0) ** n
            # Investissement des entreprises
            k_inv = k_inv * (1 - m("usure_capital", s)) - m("elasticite_invest", s) * (
                cout_capital - isv["b4"] * isv["b20"][s] * isv["b21"] * l25[t]) * isv["investissement"] * _montee(t, m("montee_invest", s))
            pib_inv = k_inv * (m("pib_par_euro_capital", s) + m("usure_capital", s))
            # Totaux
            pib = ((emp_ref + emp_sen) * va / 1e9 + pib_aj + pib_cap + pib_log + pib_prod + pib_hr + pib_ia + pib_adopt + pib_inv
                   + pib_tend + pib_ecole)
            q = p.val("macro.part_pib_tendanciel_au_solde")
            solde = (s_emploi + s_aj + s_cap + s_log + s_erosion + s_fraude + s_aides + pib_prod * q + s_react
                     + (pib_ia + pib_adopt) * q)
            if s == "prudent":
                solde += (sante["tva_prudent"][t] + pib_inv * part_budget + carbone["prudent"][t]
                          + (m("eviction", s) - m("eviction", scenario_retenu)) * pv["tva_par_point_eviction"]["valeur"] * (1 + tend0) ** n)
                mesures = clause[t]
            else:
                solde += (sante[s][t] + sante[f"tva_{s}"][t] + (pib_tend + pib_ecole) * q + pib_inv * part_budget + carbone[s][t]
                          + (m("eviction", s) - m("eviction", scenario_retenu)) * pv["tva_par_point_eviction"]["valeur"] * (1 + tend0) ** n)
                mesures = 0.0
            solde_total = solde + mesures
            interets = taux_reel(t, s) * dette_prec
            solde_public = sp_hors[t] + solde_total - transferts[t] - interets
            dette = dette_prec - solde_public - participations[t]
            pib_total = pib0[t] + pib
            maastricht = (solde_public - infl * dette_prec) / pib_total
            sc.pib_effet[t], sc.solde_effet[t], sc.emplois[t] = pib, solde_total, emp_ref + emp_sen
            sc.charge_dette[t], sc.solde_public[t], sc.dette[t] = interets, solde_public, dette
            sc.maastricht[t], sc.dette_pib[t], sc.clause[t] = maastricht, dette / pib_total, mesures
            sc.detail[t] = {"pib_inv": pib_inv, "carbone": carbone.get(s, {}).get(t)}
            # Année suivante : capital du fonds, part à l'étranger
            capital = capital + b24 * m("part_capital_nouveau", s) * (1 - m("eviction", s)) * (1 - part_etr) + m("permis_rapide", s) + capital * accumulation
            if maastricht >= etr["solde_minimum"]:
                part_etr = max(part_etr, min(etr["plafond"], etr["depart"] + (etr["plafond"] - etr["depart"]) * max(0, (etr["dette_debut"] - dette / pib_total) / (etr["dette_debut"] - etr["dette_plafond"]))))
            dette_prec = dette
        out[s] = sc
    return out
