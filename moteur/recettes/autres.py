"""Lignes 7, 8, 9, 15, 19 et 20 de la feuille Total, et l'ancienne TVA (colonne C, ligne 3)."""
from __future__ import annotations

from ..parametres import Parametres
from ..systeme_actuel import consommation_actuelle_ht, net_actuel
from ..tva import accises_calculees, taux_effectifs
from .impot_salaires import effectifs_prive_2026, effectifs_public_2026
from . import tva_menages
from ..unites import facteur

MD = 1e9


def ligne_7_dividendes(p: Parametres) -> float:
    ft, pfu = p.val("capital.flat_tax_dividendes"), p.val("dividendes.pfu_actuel")
    base = (p.val("dividendes.revenus_capitaux_mobiliers_2023") - p.val("revenus_capital.interets")) * MD
    return ft * base * min(1.0, ((1 - ft) / (1 - pfu)) ** p.val("dividendes.elasticite_taux_net"))


def ligne_8_successions(p: Parametres) -> float:
    return (p.val("successions.base_nouveau_systeme") - p.val("successions.exoneration_entreprises")) * MD


def ligne_9_contribution(p: Parametres) -> float:
    """Recettes non fiscales restant au budget + contribution d'épargne levée en contrepartie (+ contribution de transition, nulle en statique)."""
    r = p.val("fonds.recettes_non_fiscales")
    verse = r * p.val("fonds.part_versee_au_fonds")
    return ((r - verse) + verse) * MD  # + flux d'épargne × contribution de transition (0 en statique)


def reaction_revenus_capital(p: Parametres) -> float:
    return 1 - ((1 - p.val("revenus_capital.plafond")) / (1 - p.val("revenus_capital.taux_actuel"))) ** p.val("revenus_capital.elasticite")


def ligne_19_revenus_capital(p: Parametres) -> float:
    base = (p.val("revenus_capital.interets") + p.val("revenus_capital.plus_values_immobilieres") * (1 - p.val("logement.part_plus_values_bailleurs"))
            + p.val("revenus_capital.plus_values_actions"))
    return base * p.val("revenus_capital.taux_moyen_bareme") * (1 - reaction_revenus_capital(p)) * MD


def ligne_20_bailleurs(p: Parametres, scenario: str = "prudent") -> float:
    t = p.val("entreprises.taux_is_etat", scenario)
    loyers = p.val("revenus_capital.loyers") * (1 - p.val("logement.amortissement_loyers")) * t
    pv = p.val("revenus_capital.plus_values_immobilieres") * p.val("logement.part_plus_values_bailleurs") * t
    sociaux = p.val("logement.is_bailleurs_sociaux") * t
    return (loyers + pv + sociaux) * MD


def ancienne_tva_ligne_3(p: Parametres) -> float:
    """Colonne « Ancien », ligne 3 (base brute, avant le passage en euros de 2024 de la ligne 17)."""
    t = p.val("systeme_actuel.taux_tva_moyen")
    total = 0.0
    from .entreprises import _net_avant_aides
    d = effectifs_prive_2026(p)
    for n, an in zip(d.effectifs, _net_avant_aides("salaries_prive.csv")):
        total += n * t * consommation_actuelle_ht(net_actuel(an, p, False), p)
    d = effectifs_public_2026(p)
    for n, an in zip(d.effectifs, _net_avant_aides("fonctionnaires.csv")):
        total += n * t * consommation_actuelle_ht(net_actuel(an, p, True), p)
    total += p.val("accises_entreprises.tva_retraites_actuelle") * MD
    total += tva_menages.tva_etudiants(p) + tva_menages.tva_inactifs(p)  # v235 : même valeur que le nouveau système
    total += p.val("accises_entreprises.ancienne_tva_entreprises") * MD
    return total


def accises_entreprises_brutes(p: Parametres) -> float:
    a = p.val("accises_entreprises.achats_ht")
    ca = accises_calculees(p)
    return (a["carburants"] * ca["carburants"] + a["gaz_fioul"] * ca["gaz_fioul"]
            + a["electricite"] * 0.0 + a["aerien"] * ca["aerien"]) * MD


def carbone_importe_2029(p: Parametres, tva_ligne_3: float) -> float:
    """Accise sur le contenu carbone importé (Carbone!B69, année 2029, prix de 2029)."""
    from ..tva import prix_carbone
    from ..distribution import DONNEES
    import csv
    parts = {l["categorie"]: float(l["part_median"]) for l in csv.DictReader((DONNEES / "tva_produits.csv").open(encoding="utf-8"))}
    sante, tva = taux_effectifs(p)["median"]
    conso = tva_ligne_3 / MD / (sante + tva) * (parts["Biens manufacturés"] + parts["Véhicules"])
    taux = prix_carbone(p) / 1000 * p.val("carbone_importe.intensite_kg_par_euro") * p.val("carbone_importe.part_importee") * p.val("carbone_importe.part_hors_ue")
    x = taux * (1 - p.val("carbone_importe.abattement_preuve"))
    return conso * x * (1 + x / p.val("carbone_importe.passage_prix_vente")) ** (-p.val("carbone_importe.elasticite_prix")) * MD


def ligne_15_accises_entreprises(p: Parametres, tva_ligne_3: float, scenario: str = "prudent") -> float:
    """Accises carbone des entreprises + accise de transition (calage « recettes TVA égales »), nettes de l'IS."""
    t = p.val("entreprises.taux_is_etat", scenario)
    brutes = accises_entreprises_brutes(p)
    ancien = ancienne_tva_ligne_3(p) + p.val("accises_entreprises.autres_impots_produits_actuels") * MD
    importe = carbone_importe_2029(p, tva_ligne_3) / facteur(p, 2024, "recettes")
    transition = max(0.0, ancien - tva_ligne_3 - brutes - importe)
    return (brutes + transition) * (1 - t)
