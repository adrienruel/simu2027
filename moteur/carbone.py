"""Carbone dynamique : prix, érosion de l'assiette, ETS2, importations, DOM (feuille Carbone, lignes 56 à 75)."""
from __future__ import annotations

from .parametres import Parametres
from .tva import prix_carbone

ANNEES = list(range(2029, 2074))
SCENARIOS = ("prudent", "median", "optimiste")


def prix(p: Parametres, t: int) -> float:
    p0 = prix_carbone(p)
    opt = p.val("carbone.option_prix")
    if opt == 0 or t < 2030:
        return p0
    f = 1.0
    for g in p.val("tva.croissance_prix_carbone"):
        f *= 1 + g
    base = p.val("carbone.prix_option_2030") * f
    return base if opt == 1 else base * (1 + p.val("carbone.hausse_valeur_action_climat")) ** (t - 2030)


def effet_solde(p: Parametres, tva_ligne_3_md: float) -> dict[str, dict[int, float]]:
    """Effet sur le solde par scénario (Md€), lignes 72 à 74."""
    r5 = p.val("carbone.recette_2029_nette_is")
    g = p.val("macro.tendance", "prudent")
    p0 = prix_carbone(p)
    e2, dom = p.val("carbone.ets2"), p.val("carbone.dom")
    # Accise sur le contenu importé : même formule que la ligne 69, prix de l'année
    out = {s: {} for s in SCENARIOS}
    for t in ANNEES:
        n = t - 2029
        fp = prix(p, t) / p0
        fd = (1 + p.val("carbone.part_accise_prix_final") * (fp - 1)) ** (-p.val("carbone_importe.elasticite_prix"))
        statique = r5 * (1 + g) ** n
        ets2 = -e2["emissions_mt"] * (1 + p.val("carbone.baisse_tendancielle_emissions", "prudent")) ** n * e2["prix"] * e2["part_fonds_social"] / 1000 + e2["dotation_france"]
        importe = _importe(p, tva_ligne_3_md, t, fp)
        accise_pkm = dom["accise_aller_retour_ref"] / (2 * dom["distance_ref_km"])
        vols = -dom["exonerer_vols"] * dom["passagers_millions"] * dom["part_metropole"] * dom["distance_km"] * accise_pkm / 1000 * fp * fd
        dom_tva = -dom["preserver_fiscalite"] * dom["cout_regime_tva"] * (1 + g) ** n
        ets1 = 0.0  # complément ETS1 désactivé (Carbone!B27 = 0)
        for s in SCENARIOS:
            reelle = r5 * fp * fd * (1 + p.val("carbone.baisse_tendancielle_emissions", s)) ** n
            out[s][t] = reelle - statique + ets2 + importe + ets1 + vols + dom_tva
    return out


def _importe(p: Parametres, tva_md: float, t: int, fp: float) -> float:
    from .tva import taux_effectifs
    import csv
    from .distribution import DONNEES
    parts = {l["categorie"]: float(l["part_median"]) for l in csv.DictReader((DONNEES / "tva_produits.csv").open(encoding="utf-8"))}
    sante, tva = taux_effectifs(p)["median"]
    conso = tva_md / (sante + tva) * (parts["Biens manufacturés"] + parts["Véhicules"])
    taux = prix_carbone(p) / 1000 * p.val("carbone_importe.intensite_kg_par_euro") * p.val("carbone_importe.part_importee") * p.val("carbone_importe.part_hors_ue")
    x = taux * fp * (1 - p.val("carbone_importe.abattement_preuve"))
    g = p.val("macro.tendance", "prudent")
    return conso * (1 + g) ** (t - 2029) * x * (1 + x / p.val("carbone_importe.passage_prix_vente")) ** (-p.val("carbone_importe.elasticite_prix"))
