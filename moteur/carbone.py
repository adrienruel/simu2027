"""Carbone dynamique : prix, érosion de l'assiette, ETS2, importations, DOM (feuille Carbone, lignes 56 à 75)."""
from __future__ import annotations

from .is_bareme import taux_moyen
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
    fin = p.val("carbone.fin_hausse")
    return base if opt == 1 else base * (1 + p.val("carbone.hausse_valeur_action_climat")) ** (min(t, fin) - 2030)


def recette_statique(p: Parametres) -> float:
    """Recette carbone statique de 2029 (Md€ de 2026) : la part des recettes statiques qui dépend du prix du carbone.

    Accises carbone de la ligne 3 (écart entre le prix du carbone et un prix nul) et accises carbone brutes des
    entreprises, nettes d'IS. L'accise sur le contenu importé est comptée à part (effet_solde) ; l'accise de
    transition qui cale la ligne 15 est un montant fixe."""
    v = p.val("carbone.recette_2029_nette_is")
    if v != "calcul":
        return v
    cache = p.__dict__.setdefault("_cache", {})
    if "recette_carbone" not in cache:
        from .recettes import autres, entreprises
        from .recettes.total import ligne_3_tva
        from .unites import facteur
        z = p.avec({"tva.prix_carbone_2024": 0.0})
        z.colonne_prudent, z._surcharges, z.taux_local_copie = p.colonne_prudent, p._surcharges, p.taux_local_copie
        menages = (ligne_3_tva(p) - entreprises.tva_non_deductible(p)) - (ligne_3_tva(z) - entreprises.tva_non_deductible(z))
        brutes = (autres.accises_entreprises_brutes(p) * (1 - taux_moyen(p))
                  * facteur(p, 2024, "recettes"))
        cache["recette_carbone"] = (menages + brutes) / 1e9
    return cache["recette_carbone"]


def prix_finaux(p: Parametres) -> dict[str, dict[int, float]]:
    """Prix final TTC de chaque énergie dans le programme, rapporté au statu quo, année par année (correction du
    05/11/2026, remarque d'Adrien : l'essence et l'électricité baissent, le gaz monte).

    Le programme remplace les taxes actuelles sur l'énergie (accises, dont la composante carbone, et TVA) par la TVA
    et l'accise écologique du barème (parametres/donnees/tva_produits.csv) : carburants à 20 % de TVA plus le prix du
    carbone (contre 110 % du prix hors taxe aujourd'hui), gaz et fioul à 5,5 % plus le prix du carbone (40 %),
    électricité à 5,5 % sans accise (37 %). Le statu quo ajoute l'ETS2 à partir de 2028 ; le prix du carbone du
    programme est supposé le comprendre. Prix hors taxe constants en euros de 2026."""
    import csv as _csv
    from .distribution import DONNEES
    from .ecologie import emissions as em
    rows = {l["categorie"]: l for l in _csv.DictReader((DONNEES / "tva_produits.csv").open(encoding="utf-8"))}
    c, g = p.val("tva.carburants"), p.val("tva.gaz_fioul")
    k_carb = (c["co2_essence"] * (1 - c["part_gazole"]) + c["co2_gazole"] * c["part_gazole"]) / c["prix_ht"]
    k_gaz = g["co2_gaz_kwh"] / g["prix_gaz_kwh"] * g["part_gaz"] + c["co2_gazole"] / g["prix_fioul_litre"] * (1 - g["part_gaz"])
    tv = {k: float(rows[k]["tva"]) for k in ("Carburants", "Gaz et fioul", "Électricité")}
    an = {k: float(rows[k]["ancien_taux"]) for k in ("Carburants", "Gaz et fioul", "Électricité")}
    ets = p.val("ecologie.prix_carbone_statu_quo")
    out = {"transports": {}, "batiments": {}, "electricite": {}}
    for t in em.ANNEES:
        pc = prix(p, t) / 1000 if t >= 2029 else 0.0
        e2 = ets["ets2"] / 1000 if t >= ets["debut_ets2"] else 0.0
        if t < 2029:
            out["transports"][t] = out["batiments"][t] = out["electricite"][t] = 1.0
            continue
        out["transports"][t] = (1 + tv["Carburants"] + pc * k_carb) / (1 + an["Carburants"] + e2 * k_carb * 1.2)
        out["batiments"][t] = (1 + tv["Gaz et fioul"] + pc * k_gaz) / (1 + an["Gaz et fioul"] + e2 * k_gaz * 1.2)
        out["electricite"][t] = (1 + tv["Électricité"]) / (1 + an["Électricité"])
    return out


def reponse_energie(p: Parametres, s: str = "prudent") -> dict[str, dict[int, float]]:
    """Facteur sur les émissions (et l'assiette taxée) des transports et des bâtiments : prix finaux du programme
    contre le statu quo, plus l'effet croisé de l'électricité moins chère. Une seule équation pour la recette, les
    émissions et l'inflation."""
    from .ecologie import emissions as em
    pf = prix_finaux(p)
    return {i: em.reponse_ratio(p, pf[i], s, pf["electricite"]) for i in ("transports", "batiments")}


def reponse_moyenne(p: Parametres, s: str = "prudent") -> dict[int, float]:
    """Facteur moyen sur l'assiette carbone des ménages et des entreprises, pondéré par les émissions du statu quo
    de 2029 (transports et bâtiments)."""
    from .ecologie import emissions as em
    r = reponse_energie(p, s)
    e = em.territoriales(p, s)[2029]
    w = {i: e[i] for i in r}
    return {t: sum(w[i] * r[i][t] for i in r) / sum(w.values()) for t in em.ANNEES}


def effet_solde(p: Parametres, tva_ligne_3_md: float) -> dict[str, dict[int, float]]:
    """Effet sur le solde par scénario (Md€), lignes 72 à 74."""
    r5 = recette_statique(p)
    g = p.val("macro.tendance", "prudent")
    p0 = prix_carbone(p)
    e2, dom = p.val("carbone.ets2"), p.val("carbone.dom")
    activite = p.val("ecologie_options.emissions_activite")
    if activite:
        # même équation que les émissions (moteur/ecologie/emissions.py) : l'assiette suit les émissions du statu quo
        # (activité, progrès technique) et répond au prix du programme rapporté au prix du statu quo, saut de 2029
        # compris, avec ajustement progressif
        from .ecologie import emissions as em
        reponse = {s: reponse_moyenne(p, s) for s in SCENARIOS}
        ind = {s: em.indice(p, s) for s in SCENARIOS}
        ind_ets2 = em.indice(p, "prudent", ("transports", "batiments"))
    # Accise sur le contenu importé : même formule que la ligne 69, prix de l'année
    out = {s: {} for s in SCENARIOS}
    for t in ANNEES:
        n = t - 2029
        fp = prix(p, t) / p0
        fd = (1 + p.val("carbone.part_accise_prix_final") * (fp - 1)) ** (-p.val("carbone_importe.elasticite_prix"))
        statique = r5 * (1 + g) ** n
        baisse_ets2 = ind_ets2[t] if activite else (1 + p.val("carbone.baisse_tendancielle_emissions", "prudent")) ** n
        ets2 = -e2["emissions_mt"] * baisse_ets2 * e2["prix"] * e2["part_fonds_social"] / 1000 + e2["dotation_france"]
        importe = _importe(p, tva_ligne_3_md, t, fp)
        accise_pkm = dom["accise_aller_retour_ref"] / (2 * dom["distance_ref_km"])
        vols = -dom["exonerer_vols"] * dom["passagers_millions"] * dom["part_metropole"] * dom["distance_km"] * accise_pkm / 1000 * fp * fd
        dom_tva = -dom["preserver_fiscalite"] * dom["cout_regime_tva"] * (1 + g) ** n
        ets1 = 0.0  # complément ETS1 désactivé (Carbone!B27 = 0)
        for s in SCENARIOS:
            if activite:
                reelle = r5 * fp * reponse[s][t] * ind[s][t]
            else:
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
