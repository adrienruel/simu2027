"""IS de l'État et TVA non déductible des entreprises (feuille Entreprises & Dividendes, Total lignes 2 et 3).

Le nouveau bénéfice imposable de chaque classe = bénéfice actuel + impôts de production
supprimés + bénéfice capté sur la consommation en plus des ménages + TVA non déductible
supprimée (nulle depuis la v231). Effets d'érosion de l'assiette : feuille Effets macro (à venir).
"""
from __future__ import annotations

import csv

from ..distribution import DONNEES
from ..parametres import Parametres
from ..systeme_actuel import consommation_actuelle_ht
from .impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public
from .tva_menages import budget_actif, part_rui_agent
from ..epargne import part_rui_salarie


def _lire(nom):
    with (DONNEES / nom).open(encoding="utf-8") as f:
        return [{k: (v if k == "classe" else float(v)) for k, v in l.items()} for l in csv.DictReader(f)]


def _capte(net_act: float, conso_nouvelle: float, p: Parametres) -> float:
    """Bénéfice capté par les entreprises françaises sur la variation de consommation d'une personne."""
    q = p.val("entreprises.profil_import_marge")
    x = min(net_act / q["plafond_revenu"], 1)
    importe = q["import_bas"] + q["import_hausse"] * x
    marge = q["marge_bas"] + q["marge_hausse"] * x
    return (conso_nouvelle - consommation_actuelle_ht(net_act, p)) * (1 - importe) * marge


def benefice_capte(p: Parametres, scenario: str = "prudent") -> float:
    """Bénéfice supplémentaire total capté (€) — Entreprises & Dividendes!S13."""
    total = 0.0
    d = effectifs_prive_2026(p)
    from ..systeme_actuel import nets_prive
    for c, n, na in zip(d.milieux, d.effectifs, nets_prive(p)["actuel"]):
        total += n * _capte(na, budget_actif(c, p, scenario, part_rui_salarie(c, p))["conso_ht"], p)
    d, a = effectifs_public_2026(p), facteur_alignement_public(p)
    from ..systeme_actuel import nets_public
    for c, n, na in zip(d.milieux, d.effectifs, nets_public(p)["actuel"]):
        total += n * _capte(na, budget_actif(c * a, p, scenario, part_rui_agent(c))["conso_ht"], p)
    return total


def _net_avant_aides(nom):
    return [l["net_avant_aides_actuel"] for l in _lire(nom)]


def classes_entreprises(p: Parametres, scenario: str = "prudent") -> list[dict]:
    ent = _lire("entreprises.csv")
    assiette = sum(e["benefice_median"] * e["entreprises_beneficiaires"] for e in ent)
    recalage = ((p.val("entreprises.impots_production_2023") - p.val("entreprises.impots_production_hors_marchand")) * 1e9
                / sum(e["impots_production_origine"] * e["entreprises_beneficiaires"] for e in ent))
    capte = benefice_capte(p, scenario)
    r_tva = p.val("entreprises.ratio_tva_non_deductible")
    taux = p.val("entreprises.taux_is_etat", scenario)
    from ..entreprises_cellules import facteur_production
    fp = facteur_production(p, scenario)
    out = []
    for e in ent:
        prod = e["impots_production_origine"] * recalage
        capte_e = capte * e["benefice_median"] / assiette
        tva_nouvelle = e["tva_non_deductible"] * r_tva
        # impôts de production supprimés : la part payée par les entreprises déficitaires n'entre pas dans le bénéfice
        # imposable de l'année (moteur/entreprises_cellules.py ; v235 : tout entre)
        base = e["benefice_median"] + prod * fp + capte_e + e["tva_non_deductible"] - tva_nouvelle
        out.append({**e, "impots_production": prod, "capte": capte_e, "tva_nouvelle": tva_nouvelle,
                    "base_is": base, "is": taux * base})
    return out


def is_beneficiaires(p: Parametres, scenario: str = "prudent") -> float:
    return sum(c["is"] * c["entreprises_beneficiaires"] for c in classes_entreprises(p, scenario))


def is_deficitaires(p: Parametres, scenario: str = "prudent") -> float:
    """Entreprises déficitaires qui passent en bénéfice (bloc 5).

    v235 : l'allègement retenu est la TVA non déductible de la plus petite classe plus son
    bénéfice capté, alors que cette TVA n'est plus supprimée depuis la v231. Reproduit tel quel.
    """
    c0 = classes_entreprises(p, scenario)[0]
    allegement = c0["tva_non_deductible"] + c0["capte"]
    taux = p.val("entreprises.taux_is_etat", scenario)
    return sum(max(0.0, allegement - d["perte_mediane"]) * taux * d["effectif"] for d in _lire("entreprises_deficitaires.csv"))


def tva_non_deductible(p: Parametres, scenario: str = "prudent") -> float:
    return sum(c["tva_nouvelle"] * c["entreprises_beneficiaires"] for c in classes_entreprises(p, scenario))
