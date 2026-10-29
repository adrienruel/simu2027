"""Emploi : les quatorze réformes, baisse du chômage, gain budgétaire par emploi (feuille Emploi).

Les réformes sont chiffrées sous trois jeux d'hypothèses (crise, médian, optimiste). Chaque réforme ferme
une part de l'écart entre le chômage actuel et le chômage incompressible (rendements décroissants).
"""
from __future__ import annotations

import math

from .epargne import taux_epargne
from .impot_unique import impot
from .parametres import Parametres
from .recettes.impot_salaires import effectifs_prive_2026
from .recettes import entreprises
from .systeme_actuel import net_actuel

JEUX = ("crise", "median", "optimiste")


def population_active(p: Parametres) -> float:
    return p.val("inactifs.chomeurs_bit") / p.val("chomage.taux_2026")


def cout_smic_annuel(p: Parametres) -> float:
    return p.val("epargne.cout_smic_mensuel") * 12


def _taux_local(p: Parametres) -> float:
    from .collectivites import taux_impot_local
    return taux_impot_local(p)


def baisse_cout_travail(p: Parametres) -> float:
    """Coût de la baisse ciblée du coût employeur, plafonnée à l'impôt dû (Md€, Emploi!E86)."""
    b = p.val("emploi.baisse_cout_travail")
    smic = cout_smic_annuel(p)
    d = effectifs_prive_2026(p)
    total = 0.0
    for c, n in zip(d.milieux, d.effectifs):
        x = c / smic
        taux = b["taux"] if x <= b["plein_jusqu_a"] else (b["taux"] * (b["nulle_a"] - x) / (b["nulle_a"] - b["plein_jusqu_a"]) if x < b["nulle_a"] else 0.0)
        total += min(taux * c, impot(c, p)) * n
    return total / 1e9


def marge_intensive(p: Parametres) -> dict[str, float]:
    """Variation des heures des bas salaires (EQTP), selon la part gardée par euro de coût en plus."""
    d = effectifs_prive_2026(p)
    nets = [net_actuel(x, p, False) / 12 for x in [l for l in _net_avant_aides()]]
    c = d.milieux
    gard_auj_1 = (nets[1] - nets[0]) * 12 / (c[1] - c[0])
    gard_prog_1 = 1 - p.val("rui.montant") / p.val("epargne.cout_smic_mensuel")
    gard_auj_2 = (nets[5] - nets[2]) * 12 / (c[5] - c[2])
    gard_prog_2 = 1 - p.val("impot_unique.taux")[1] - p.val("rui.montant") / p.val("epargne.cout_smic_mensuel") - _taux_local(p)
    mi = p.val("emploi.marge_intensive")
    v1 = (d.effectifs[0] + d.effectifs[1]) * mi["facteur_eqtp"]
    v2 = (sum(d.effectifs[2:6]) + d.effectifs[6] * (cout_smic_annuel(p) - 22500) / 2500) * mi["facteur_eqtp"]
    base = v1 * math.log(gard_prog_1 / gard_auj_1) + v2 * math.log(gard_prog_2 / gard_auj_2)
    return {j: mi[j] * base for j in JEUX}


def _net_avant_aides():
    from .recettes.entreprises import _net_avant_aides as n
    return n("salaries_prive.csv")


def emplois_reforme_entreprises(p: Parametres) -> dict[str, float]:
    """Fin des impôts de production assis sur les salaires (coût du travail) et IS à 45 % (localisation)."""
    d = effectifs_prive_2026(p)
    smic = cout_smic_annuel(p)
    masse = sum(c * n for c, n in zip(d.milieux, d.effectifs))
    parts = [sum(c * n for c, n in zip(d.milieux, d.effectifs) if lo <= c < hi) / masse
             for lo, hi in ((0, 1.6 * smic), (1.6 * smic, 2.5 * smic), (2.5 * smic, 1e15))]
    ent = entreprises._lire("entreprises.csv")
    ia = p.val("entreprises.is_actuel")
    is_actuel = sum((e["benefice_median"] * ia["taux_reduit"] if e["benefice_median"] <= ia["seuil_reduit"]
                     else ia["seuil_reduit"] * ia["taux_reduit"] + (e["benefice_median"] - ia["seuil_reduit"]) * ia["taux_normal"])
                    * e["entreprises_beneficiaires"] for e in ent) / 1e9
    assiette = sum(e["benefice_median"] * e["entreprises_beneficiaires"] for e in ent) / 1e9
    prod = p.val("entreprises.impots_production_2023") - p.val("entreprises.impots_production_hors_marchand")
    part_sal = p.val("emploi.impots_production_salaires") / p.val("entreprises.impots_production_2023")
    taux_actuel = (is_actuel + prod * (1 - part_sal)) / (assiette + prod * (1 - part_sal))
    taux_nouveau = p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    ecart = (taux_nouveau - taux_actuel) * 100
    salaries = sum(d.effectifs)
    out = {}
    for j in JEUX:
        epm = p.val("emploi.emplois_par_milliard_tranches", j)
        cout_travail = p.val("emploi.impots_production_salaires") * sum(a * b for a, b in zip(parts, epm))
        l = p.val("emploi.localisation", j)
        loc = -ecart * (l["hausse"] if ecart > 0 else l["baisse"]) * l["part"] * l["mobilite"] * salaries
        out[j] = cout_travail + loc
    return out


def effets_reformes(p: Parametres) -> dict[str, dict]:
    """Baisse du chômage par jeu d'hypothèses (points), emplois correspondants, chômage à terme."""
    pa = population_active(p)
    d = effectifs_prive_2026(p)
    e86 = baisse_cout_travail(p)
    ent = emplois_reforme_entreprises(p)
    mi = marge_intensive(p)
    r = p.val("emploi.retenues_calculees")
    epm = {j: p.val("emploi.emplois_par_milliard", j) for j in JEUX}
    b = p.val("emploi.bas_salaires_rui_prorata")
    # SMIC revalorisé de la croissance seule
    g, infl = p.val("macro.tendance", "prudent"), p.val("calendrier.inflation")
    baisse_smic = 1 - ((1 + g) / (1 + infl)) ** (p.val("emploi.annee_objectif") - 2029)
    masse = sum(c * n for c, n in zip(d.milieux, d.effectifs)) / 1e9
    baisse_cout_smic = baisse_smic * p.val("emploi.smic_effet_salaire_moyen") * masse
    pj = p.val("emploi.prime_jeunes")
    ab = p.val("emploi.accords_branche")
    co = p.val("emploi.commerces")
    out = {}
    for j in JEUX:
        total = sum(x["retenue"] * x[j] for x in p.val("emploi.reformes_directes").values())
        total += b["retenue"] * (b[j] + mi[j] / pa)
        total += r["entreprises"] * ent[j] / pa
        total += r["baisse_cout_travail"] * e86 * epm[j] / pa
        total += r["commerces"] * co["salaries"] * co[j] / pa
        total += r["smic_croissance"] * baisse_cout_smic * epm[j] / pa
        total += r["prime_jeunes"] * pj["primes_par_an"] * pj[j]["embauche"] * pj[j]["annees"] / pa
        total += r["accords_branche"] * sum(d.effectifs) * ab["baisse_emploi_portugal"] * ab[j] / pa
        ecart = p.val("chomage.taux_2026") - p.val("emploi.chomage_incompressible")
        baisse = ecart * (1 - math.exp(-total / ecart))
        out[j] = {"somme": total, "baisse": baisse, "emplois": baisse * pa, "chomage": p.val("chomage.taux_2026") - baisse}
    return out


def cout_reformes(p: Parametres) -> float:
    """Coût annuel des réformes retenues (Md€, Emploi!G24), ajouté aux dépenses de la trajectoire."""
    r = p.val("emploi.retenues_calculees")
    total = sum(x["retenue"] * x["cout"] for x in p.val("emploi.reformes_directes").values())
    total += p.val("emploi.bas_salaires_rui_prorata")["retenue"] * p.val("emploi.bas_salaires_rui_prorata")["cout"]
    total += r["baisse_cout_travail"] * baisse_cout_travail(p)
    total += r["prime_jeunes"] * cout_prime_jeunes(p)
    rui = p.val("rui.montant")
    ap = p.val("emploi.aide_personne")
    total += ap["retenue"] * sum(ap["etp"].values()) * rui * 12 / 1e9
    am = p.val("emploi.assistantes_maternelles")
    part_base = (rui / p.val("sante.heures_mensuelles_temps_plein")) / (cout_smic_annuel(p) / (p.val("sante.heures_mensuelles_temps_plein") * 12))
    total += am["retenue"] * am["heures"] * am["part_heures_modestes"] * (am["part_etat_bas_revenu"] - part_base) * am["cout_heure"] * am["part_complement"] / 1e9
    cr = p.val("emploi.creches")
    part_creche = part_base + (am["part_etat_bas_revenu"] - part_base) * am["part_heures_modestes"] * am["part_complement"]
    total += cr["retenue"] * (cr["places_psu"] * cr["cout_psu"] + cr["places_micro"] * cr["cout_micro"]) / 1e9 * part_creche
    return total


def cout_prime_jeunes(p: Parametres) -> float:
    pj = p.val("emploi.prime_jeunes")
    return pj["primes_par_an"] * pj["part_rui"] * p.val("rui.montant") * pj["duree_mois"] / 1e9


def emplois_perdus_subventions(p: Parametres) -> dict[str, float]:
    s = p.val("emploi.subventions_supprimees")
    n = s["insertion"] + s["territoires_zero_chomeur"] + s["contrats_aides"]
    return {j: s["retenu"] * n * s[j] for j in JEUX}


def emplois_perdus_fin_prime(p: Parametres) -> dict[str, float]:
    pj = p.val("emploi.prime_jeunes")
    return {j: p.val("emploi.retenues_calculees")["prime_jeunes"] * pj["primes_par_an"] * pj[j]["embauche"] * pj[j]["annees"] for j in JEUX}


def gain_par_emploi(p: Parametres, scenario: str) -> float:
    """RUI économisé + impôt unique + TVA sur la consommation en plus (€/an), pour un emploi à 1,3 SMIC."""
    part_rui = p.val("emploi.gain_par_emploi", scenario)
    rui = p.val("rui.montant") * 12
    cout = p.val("emploi.cout_emploi_cree_smic") * cout_smic_annuel(p)
    imp = impot(cout, p)
    local = max(0.0, cout - p.val("impot_local.abattement")) * _taux_local(p)
    conso = (cout - imp - local) * (1 - taux_epargne(cout, p)) - rui * part_rui
    return part_rui * rui + imp + p.val("systeme_actuel.taux_tva_moyen") * conso


def valeur_ajoutee_par_emploi(p: Parametres) -> float:
    return p.val("emploi.cout_emploi_cree_smic") * cout_smic_annuel(p) / (1 - p.val("emploi.taux_marge_snf") - p.val("emploi.impots_production_va"))


def entrees_macro(p: Parametres) -> dict:
    """Ce que la feuille Effets macro lit dans la feuille Emploi, par scénario du modèle."""
    e = effets_reformes(p)
    perdus, fin_prime = emplois_perdus_subventions(p), emplois_perdus_fin_prime(p)
    u = getattr(p, "emplois_tirage", None)  # incertitude : tirage entre le jeu de crise et le jeu optimiste
    if u is not None:
        mix = lambda d: d["crise"] + u * (d["optimiste"] - d["crise"])
        sortie = entrees_macro_sans_tirage(p, e, perdus, fin_prime)
        sortie["emplois_terme"]["prudent"] = mix({k: e[k]["emplois"] for k in JEUX})
        sortie["emplois_perdus_subventions"]["prudent"] = mix(perdus)
        sortie["emplois_perdus_tardifs"]["prudent"] = mix(fin_prime)
        return sortie
    return entrees_macro_sans_tirage(p, e, perdus, fin_prime)


def entrees_macro_sans_tirage(p: Parametres, e: dict, perdus: dict, fin_prime: dict) -> dict:
    return {
        # prudent : milieu des jeux crise et médian ; calcul de crise : jeu de crise seul (Effets macro!B8)
        "emplois_terme": {"prudent": e["crise"]["emplois"] if p.colonne_prudent == "crise" else (e["crise"]["emplois"] + e["median"]["emplois"]) / 2,
                          "median": e["median"]["emplois"], "optimiste": e["optimiste"]["emplois"]},
        # v235 : le prudent prend la valeur de crise pour les emplois perdus
        "emplois_perdus_subventions": {"prudent": perdus["crise"], "median": perdus["median"], "optimiste": perdus["optimiste"]},
        "emplois_perdus_tardifs": {"prudent": fin_prime["crise"], "median": fin_prime["median"], "optimiste": fin_prime["optimiste"],
                                   "annee": p.val("emploi.prime_jeunes")["derniere_annee"]},
        "gain_par_emploi": {s: gain_par_emploi(p, s) for s in ("prudent", "median", "optimiste")},
        "valeur_ajoutee_par_emploi": {"valeur": valeur_ajoutee_par_emploi(p)},
    }
