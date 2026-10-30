"""Lignes 7, 8, 9, 15, 19 et 20 de la feuille Total, et l'ancienne TVA (colonne C, ligne 3)."""
from __future__ import annotations

from ..parametres import Parametres
from ..systeme_actuel import consommation_actuelle_ht
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
    from ..is_bareme import taux_moyen
    t = taux_moyen(p, scenario)  # taux unique, ou moyen effectif d'un IS progressif
    loyers = p.val("revenus_capital.loyers") * (1 - p.val("logement.amortissement_loyers")) * t
    pv = p.val("revenus_capital.plus_values_immobilieres") * p.val("logement.part_plus_values_bailleurs") * t
    sociaux = p.val("logement.is_bailleurs_sociaux") * t
    return (loyers + pv + sociaux) * MD


def tva_retraites_actuelle(p: Parametres) -> float:
    """TVA payée aujourd'hui par les retraités (€ de 2024) : distribution DREES des pensions, recalée sur la pension
    nette moyenne de fin 2023 revalorisée en 2024, impôt sur le revenu moyen retiré, fonction de consommation actuelle."""
    v = p.val("accises_entreprises.tva_retraites_actuelle")
    if v != "calcul":
        return v * MD
    r = p.val("retraites_actuels.donnees")
    dec = p.val("anciennes_pensions.deciles_drees_2020")
    echelle = r["pension_nette_moyenne_2023"] * (1 + r["revalorisation_2024"]) / (sum(dec) / len(dec))
    t = p.val("systeme_actuel.taux_tva_moyen")
    conso = sum(t * consommation_actuelle_ht(12 * d * echelle * (1 - r["taux_ir_moyen"]), p) for d in dec) / len(dec)
    return conso * r["residents_france_2023"]


def ancienne_tva_ligne_3(p: Parametres) -> float:
    """Colonne « Ancien », ligne 3 (base brute, avant le passage en euros de 2024 de la ligne 17)."""
    t = p.val("systeme_actuel.taux_tva_moyen")
    total = 0.0
    d = effectifs_prive_2026(p)
    from ..systeme_actuel import nets_prive
    for n, na in zip(d.effectifs, nets_prive(p)["actuel"]):
        total += n * t * consommation_actuelle_ht(na, p)
    d = effectifs_public_2026(p)
    from ..systeme_actuel import nets_public
    for n, na in zip(d.effectifs, nets_public(p)["actuel"]):
        total += n * t * consommation_actuelle_ht(na, p)
    total += tva_retraites_actuelle(p)
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
    from ..is_bareme import taux_moyen
    t = taux_moyen(p, scenario)
    brutes = accises_entreprises_brutes(p)
    ancien = ancienne_tva_ligne_3(p) + p.val("accises_entreprises.autres_impots_produits_actuels") * MD
    importe = carbone_importe_2029(p, tva_ligne_3) / facteur(p, 2024, "recettes")
    transition = max(0.0, ancien - tva_ligne_3 - brutes - importe)
    return (brutes + transition) * (1 - t)
