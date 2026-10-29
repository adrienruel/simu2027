"""Collectivités : besoin de recettes locales et taux de l'impôt local unique (feuille Collectivités).

Le taux dépend de l'IS local, qui dépend du bénéfice des entreprises, qui dépend de la consommation des
ménages, qui dépend du taux : la v235 atteint ce point fixe en recopiant le taux à la main (B91).
Ici il est calculé par itération (taux_impot_local).
"""
from __future__ import annotations

from .parametres import Parametres

_CACHE: dict[int, float] = {}


def environnement(p: Parametres) -> dict[str, float]:
    b = p.val("environnement.bombardiers")
    flotte = b["appareils"] * b["prix_unitaire_m"] / 1000
    loyer = flotte * b["rendement_fonds"] / (1 - (1 + b["rendement_fonds"]) ** -b["duree_location"])
    transfere = sum(p.val("environnement.ecosystemes_transferes_regions_m").values()) / 1000
    c = p.val("environnement.chaleur")
    perte_is = c["logements_millions"] * c["part_sans_protection"] * c["cout_logement"] * c["part_recours"] / 1000 / c["duree_amortissement"] * p.val("entreprises.taux_is_etat")
    return {"economie_etat": transfere - loyer - perte_is, "recettes_regions": transfere}


def is_local(p: Parametres) -> dict[str, float]:
    """IS local au taux de base, sur la même assiette que l'IS de l'État (Md€, lignes 33)."""
    from .recettes import entreprises, independants
    from .recettes.autres import accises_entreprises_brutes
    from .unites import facteur
    t_is = p.val("entreprises.taux_is_etat")
    s17 = t_is + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    erosion = (s17 - p.val("macro.taux_reference_is", "prudent")) * (p.val("macro.semi_elasticite_transfert", "prudent")
               * p.val("macro.part_grandes_entreprises", "prudent") + p.val("macro.reaction_reelle", "prudent"))
    j20 = entreprises.is_beneficiaires(p) / 1e9
    ind_b30 = independants.is_local_independants(p) / (p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")) / 1e9
    bailleurs = (p.val("revenus_capital.loyers") * (1 - p.val("logement.amortissement_loyers"))
                 + p.val("revenus_capital.plus_values_immobilieres") * p.val("logement.part_plus_values_bailleurs")) * t_is
    base = (j20 * (1 - erosion) + ind_b30 / facteur(p, 2024, "recettes") * t_is + entreprises.is_deficitaires(p) / 1e9
            + bailleurs - accises_entreprises_brutes(p) / 1e9 * t_is) / t_is
    return {"communes": base * p.val("impot_local_entreprises.taux_communes"), "regions": base * p.val("impot_local_entreprises.taux_regions")}


def besoin(p: Parametres) -> dict[str, float]:
    """Besoin de recettes locales nouvelles (Md€, ligne 27)."""
    from .unites import facteur
    conc = p.val("collectivites_detail.concours_etat_aujourdhui")
    part_om = p.val("budget_statique.concours_outre_mer")["part"]
    perdu = {k: conc[k] * (1 - part_om) for k in ("communes", "regions")}
    for x in p.val("collectivites_detail.ressources_perdues_fixes").values():
        for k in perdu:
            perdu[k] += x[k]
    charges = {k: 0.0 for k in perdu}
    for x in p.val("collectivites_detail.charges_fixes").values():
        for k in charges:
            charges[k] += x[k]
    sante_brut = p.val("sante.aide_sociale_autonomie_2024") * facteur(p, 2024, "recettes") * (1 if p.val("sante.reprise_autonomie_par_etat") else 0)
    charges["regions"] += -p.val("collectivites_detail.aide_sociale_enfance") - sante_brut
    ms = p.val("collectivites_detail.masse_salariale_agents")
    t = p.val("alignement.charges_patronales_prive")
    v = p.val("alignement.versants")["territoriale"]
    baisse_terr = (1 + t) / (1 + v["charges_actuelles"]) - 1
    ia = p.val("ia.plafond_taches_automatisables") * (1 - p.val("ia.cout_services_ia"))
    for k in charges:
        charges[k] += ms[k] * baisse_terr - ms[k] * p.val("collectivites_detail.part_agents_gestion") * ia
    bf = dict(zip(("communes", "regions"), p.val("collectivites.besoin_financement_2024")))
    couvert = p.val("collectivites.part_financee")  # Collectivités!B26 : 0 = laissé en déficit public
    md = p.val("collectivites_detail.meme_doctrine")
    gains_c = sum(x["gain"] * x["part_communes"] for x in md.values())
    gains_r = sum(x["gain"] * (1 - x["part_communes"]) for x in md.values())
    isl = is_local(p)
    cp = p.val("collectivites_detail.carence_poids")
    carence_terr = cp["economie_etat_hopitaux"] * cp["territoriale"] / (cp["etat"] + cp["territoriale"] + cp["hospitaliere"])
    hu = p.val("collectivites_detail.hebergement_urgence")
    communes = (perdu["communes"] + charges["communes"] + bf["communes"] * couvert
                - p.val("collectivites_detail.ressources_perdues_fixes")["versement_mobilite"]["communes"] * p.val("collectivites_detail.versement_mobilite_compense")
                - gains_c - isl["communes"] + hu["montant"] * (1 - hu["part_etat"])
                - carence_terr * ms["communes"] / (ms["communes"] + ms["regions"]) + p.val("collectivites_detail.taxe_fonciere_menages"))
    regions = (perdu["regions"] + charges["regions"] + bf["regions"] * couvert - gains_r + environnement(p)["recettes_regions"]
               - isl["regions"] - carence_terr * ms["regions"] / (ms["communes"] + ms["regions"]))
    return {"communes": communes, "regions": regions, "total": communes + regions}


def assiette_impot_local(p: Parametres) -> float:
    """Assiette de l'impôt local sur les revenus d'activité (Md€) : coût employeur des salariés et des agents
    (alignés), salaire des indépendants, au-delà de l'abattement. Les retraités n'en paient pas."""
    v = p.val("collectivites_detail.assiette_revenus")
    if v != "calcul":
        return v
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public
    from .recettes import independants
    ab = p.val("impot_local.abattement")
    a = facteur_alignement_public(p)
    dp, dg = effectifs_prive_2026(p), effectifs_public_2026(p)
    total = sum(n * max(0.0, c - ab) for c, n in zip(dp.milieux, dp.effectifs))
    total += sum(n * max(0.0, c * a - ab) for c, n in zip(dg.milieux, dg.effectifs))
    if p.val("impot_local.independants_sur_salaire"):
        total += sum(x["effectif"] * x["part_percue"] * max(0.0, x["salaire"] - ab) for x in independants.classes(p))
    return total / 1e9


def taux_calcule(p: Parametres) -> float:
    return besoin(p)["total"] / assiette_impot_local(p)


def taux_impot_local(p: Parametres, salaries: bool = False, tolerance: float = 1e-13, iterations_max: int = 50) -> float:
    """Taux moyen de l'impôt local unique au point fixe (le taux finance le besoin qu'il influence).

    Valeur de départ : impot_local.taux_point_fixe. Le résultat est gardé sur l'objet de paramètres.
    Si p.taux_local_copie est donné (reproduction de la v235), les feuilles de salariés (salaries=True)
    lisent cette copie (Collectivités!B91) et les autres le taux calculé en un pas à partir d'elle (B32).
    """
    force = getattr(p, "_taux_local_force", None)
    if force is not None:
        return force
    cache = p.__dict__.setdefault("_cache", {})
    copie = getattr(p, "taux_local_copie", None)
    if copie is not None:
        if salaries:
            return copie
        if "taux_local_un_pas" not in cache:
            p._taux_local_force = copie
            try:
                cache["taux_local_un_pas"] = taux_calcule(p)
            finally:
                p._taux_local_force = None
        return cache["taux_local_un_pas"]
    if "taux_local" in cache:
        return cache["taux_local"]
    x = p.val("impot_local.taux_point_fixe")
    for _ in range(iterations_max):
        p._taux_local_force = x
        try:
            y = taux_calcule(p)
        finally:
            p._taux_local_force = None
        if abs(y - x) < tolerance:
            x = y
            break
        x = y
    else:
        raise RuntimeError("Le taux de l'impôt local ne converge pas")
    cache["taux_local"] = x
    return x
