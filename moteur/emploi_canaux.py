"""Bloc emploi unifié : chaque mesure, son canal, ses emplois et ce qu'ils rapportent au budget.

Canaux :
- offre : incitation à travailler, recherche d'emploi, qualification (le chômeur reprend un emploi) ;
- appariement : rencontre de l'offre et de la demande (conseil, accompagnement, logement, mobilité) ;
- cout_travail : baisse du coût du travail ou de ses rigidités (l'employeur embauche) ;
- localisation : activités qui partent ou viennent selon l'imposition des bénéfices ;
- population_active : emplois qui s'ajoutent sans venir du chômage (seniors, cumul emploi-socle) ;
- perdus : emplois subventionnés qui disparaissent.

Règles contre le double compte (docs/bloc_emploi.md) :
1. Un emploi n'est compté qu'une fois : toutes les réformes qui réduisent le chômage passent par une seule
   courbe de rendements décroissants (la baisse totale ne peut pas dépasser l'écart au chômage
   incompressible) ; chaque mesure reçoit la part de la baisse proportionnelle à son effet propre.
2. Les emplois de la population active (seniors, cumul) ne viennent pas du chômage : ils sont hors de
   cette courbe, mais ne réduisent pas non plus le taux de chômage.
3. Une mesure qui joue sur deux canaux (réforme des entreprises : coût du travail et localisation) est
   comptée dans chacun, avec des assiettes distinctes (les salaires pour l'un, les bénéfices pour l'autre).
4. Chaque emploi rapporte au budget selon son salaire : un emploi au SMIC rapporte moins qu'un emploi
   moyen. Faute de source sur le salaire des emplois créés, on prend le bas (prudent) pour les emplois
   gagnés, et le salaire moyen pour les emplois perdus par localisation (activités mobiles et rentables).
5. Le gain par emploi est calculé dans le nouveau système (impôt unique, impôt local, RUI économisé, TVA
   aux taux du nouveau système), et non avec le taux de TVA de l'ancien système.
"""
from __future__ import annotations

import math

from .emploi import (JEUX, _taux_local, baisse_cout_travail, cout_smic_annuel, emplois_perdus_fin_prime,
                     emplois_perdus_subventions, marge_intensive, population_active)
from .epargne import taux_epargne
from .impot_unique import impot
from .parametres import Parametres
from .recettes.impot_salaires import effectifs_prive_2026
from .tva import taux_pour_revenu

CANAUX = {
    "allocation_chomage_rui": "offre", "france_travail_conseil": "appariement",
    "selection_universite_apprentissage": "offre", "droit_a_construire": "appariement",
    "accompagnement_ia": "appariement", "alternance": "offre", "contrat_assoupli": "cout_travail",
    "bas_salaires": "offre", "entreprises_cout_travail": "cout_travail", "entreprises_localisation": "localisation",
    "baisse_cout_travail": "cout_travail", "commerces": "cout_travail", "smic_croissance": "cout_travail",
    "prime_jeunes": "cout_travail", "accords_branche": "cout_travail",
}


def _parts_entreprises(p: Parametres) -> dict[str, dict[str, float]]:
    """Réforme des entreprises séparée en coût du travail et localisation (emplois, par jeu)."""
    from .recettes import entreprises
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
    taux_nouveau = (p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes")
                    + p.val("impot_local_entreprises.taux_regions"))
    ecart = (taux_nouveau - taux_actuel) * 100
    salaries = sum(d.effectifs)
    out = {}
    for j in JEUX:
        epm = p.val("emploi.emplois_par_milliard_tranches", j)
        l = p.val("emploi.localisation", j)
        out[j] = {"cout_travail": p.val("emploi.impots_production_salaires") * sum(a * b for a, b in zip(parts, epm)),
                  "localisation": -ecart * (l["hausse"] if ecart > 0 else l["baisse"]) * l["part"] * l["mobilite"] * salaries}
    return out


def points_par_mesure(p: Parametres) -> dict[str, dict[str, float]]:
    """Baisse du chômage (points) due à chaque mesure, avant rendements décroissants, par jeu."""
    pa = population_active(p)
    d = effectifs_prive_2026(p)
    e86 = baisse_cout_travail(p)
    ent = _parts_entreprises(p)
    mi = marge_intensive(p)
    r = p.val("emploi.retenues_calculees")
    b = p.val("emploi.bas_salaires_rui_prorata")
    g, infl = p.val("macro.tendance", "prudent"), p.val("calendrier.inflation")
    baisse_smic = 1 - ((1 + g) / (1 + infl)) ** (p.val("emploi.annee_objectif") - 2029)
    masse = sum(c * n for c, n in zip(d.milieux, d.effectifs)) / 1e9
    baisse_cout_smic = baisse_smic * p.val("emploi.smic_effet_salaire_moyen") * masse
    pj, ab, co = p.val("emploi.prime_jeunes"), p.val("emploi.accords_branche"), p.val("emploi.commerces")
    out = {}
    for j in JEUX:
        epm = p.val("emploi.emplois_par_milliard", j)
        x = {k: v["retenue"] * v[j] for k, v in p.val("emploi.reformes_directes").items()}
        x["bas_salaires"] = b["retenue"] * (b[j] + mi[j] / pa)
        x["entreprises_cout_travail"] = r["entreprises"] * ent[j]["cout_travail"] / pa
        x["entreprises_localisation"] = r["entreprises"] * ent[j]["localisation"] / pa
        x["baisse_cout_travail"] = r["baisse_cout_travail"] * e86 * epm / pa
        x["commerces"] = r["commerces"] * co["salaries"] * co[j] / pa
        x["smic_croissance"] = r["smic_croissance"] * baisse_cout_smic * epm / pa
        x["prime_jeunes"] = r["prime_jeunes"] * pj["primes_par_an"] * pj[j]["embauche"] * pj[j]["annees"] / pa
        x["accords_branche"] = r["accords_branche"] * sum(d.effectifs) * ab["baisse_emploi_portugal"] * ab[j] / pa
        out[j] = x
    return out


def emplois_par_mesure(p: Parametres) -> dict[str, dict[str, float]]:
    """Emplois à terme de chaque mesure, rendements décroissants répartis au prorata (règle 1)."""
    pa = population_active(p)
    ecart = p.val("chomage.taux_2026") - p.val("emploi.chomage_incompressible")
    out = {}
    for j, x in points_par_mesure(p).items():
        total = sum(x.values())
        baisse = ecart * (1 - math.exp(-total / ecart))
        k = baisse / total if total else 1.0
        out[j] = {m: v * k * pa for m, v in x.items()}
    return out


def cout_moyen_prive(p: Parametres) -> float:
    d = effectifs_prive_2026(p)
    return sum(c * n for c, n in zip(d.milieux, d.effectifs)) / sum(d.effectifs)


def cout_canal(canal: str, p: Parametres) -> float:
    """Coût employeur annuel d'un emploi du canal (règle 4)."""
    k = p.val("emploi.cout_par_canal")[canal]
    if k == "moyen":
        return cout_moyen_prive(p)
    if k == "median":
        return p.val("profils.cout_median_annuel")
    return k * cout_smic_annuel(p)


def gain_au_cout(cout: float, p: Parametres, scenario: str) -> float:
    """Ce qu'un emploi rapporte au budget (€/an) : RUI économisé, impôt unique, TVA du nouveau système sur la
    consommation en plus (règle 5). Même structure que le gain de la v235, au coût et aux taux du canal."""
    part_rui = p.val("emploi.gain_par_emploi", scenario)
    rui = p.val("rui.montant") * 12
    imp = impot(cout, p)
    local = max(0.0, cout - p.val("impot_local.abattement")) * _taux_local(p)
    net = cout - imp - local
    sante, tva = taux_pour_revenu(net, p)
    t = sante + tva
    conso = (net * (1 - taux_epargne(cout, p)) - rui * part_rui) / (1 + t)
    return part_rui * rui + imp + t * conso


def gains_par_canal(p: Parametres, scenario: str) -> dict[str, float]:
    return {c: gain_au_cout(cout_canal(c, p), p, scenario) for c in p.val("emploi.cout_par_canal")}


def solde_reformes(p: Parametres, scenario_modele: str, jeux_poids: dict[str, float]) -> float:
    """Effet à terme sur le solde (€/an) des emplois des réformes, pour un mélange de jeux (poids)."""
    e = emplois_par_mesure(p)
    g = gains_par_canal(p, scenario_modele)
    return sum(w * sum(v * g[CANAUX[m]] for m, v in e[j].items()) for j, w in jeux_poids.items())


def tableau(p: Parametres | None = None) -> list[dict]:
    """Pour la restitution : emplois et effet sur le solde à terme de chaque mesure, dans le prudent."""
    p = p or Parametres()
    e = emplois_par_mesure(p)
    g = gains_par_canal(p, "prudent")
    out = []
    for m in e["crise"]:
        emplois = (e["crise"][m] + e["median"][m]) / 2
        out.append({"mesure": m, "canal": CANAUX[m], "emplois_crise": e["crise"][m], "emplois_prudent": emplois,
                    "emplois_median": e["median"][m], "emplois_optimiste": e["optimiste"][m],
                    "gain_par_emploi": g[CANAUX[m]], "solde_md": emplois * g[CANAUX[m]] / 1e9})
    return out


__all__ = ["CANAUX", "emplois_par_mesure", "gain_au_cout", "gains_par_canal", "solde_reformes", "tableau",
           "emplois_perdus_fin_prime", "emplois_perdus_subventions"]
