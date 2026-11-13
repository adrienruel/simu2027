"""Dépenses de santé année par année et volet santé de la TVA (feuille Santé, sections 3 à 8)."""
from __future__ import annotations

from .parametres import Parametres
from .depenses.statique import sante_statique, economies_sante_a_terme
from .tva import produits as produits_tva

ANNEES = list(range(2029, 2074))
SCENARIOS = ("prudent", "median", "optimiste")


def pente_assurance_maladie(p: Parametres, nom: str) -> float:
    """Croissance réelle annuelle : PIB + écart qui porte la part de la santé dans le PIB au repère 2030."""
    d = p.val("sante_trajectoire.depenses_2024")
    part = d["sante_md"] / d["pib_md"]
    ecart = ((part + p.val("sante_trajectoire.scenarios_assurance_maladie")[nom]) / part) ** (1 / 6) - 1
    return (1 + p.val("macro.tendance", "prudent")) * (1 + ecart) - 1


def pente_promede(p: Parametres, nom: str) -> float:
    x = p.val("sante_trajectoire.promede")[nom]
    return (1 + p.val("macro.tendance", "prudent")) * (1 + (x["part_2060"] / x["part_2011"]) ** (1 / 49) - 1) - 1


def pente_1(p, s):
    return pente_assurance_maladie(p, p.val("sante_trajectoire.pente_phase_1", s))


def pente_2(p, s):
    return pente_promede(p, p.val("sante_trajectoire.pente_phase_2", s))


def _croissance(p, s, t):
    d = p.val("sante_trajectoire.derniere_annee_phase_1")
    a, b = pente_1(p, s), pente_2(p, s)
    return (1 + a) ** (t - 2029) if t <= d else (1 + a) ** (d - 2029) * (1 + b) ** (t - d)


def derive_2029(p: Parametres) -> float:
    g = p.val("macro.tendance", "prudent")
    return ((1 + pente_assurance_maladie(p, p.val("sante_trajectoire.scenario_2027_2029"))) / (1 + g)) ** 3 if p.val("sante_trajectoire.derive_prise_en_compte") else 1.0


def economie_hopitaux_ia(p: Parametres, t: int) -> float:
    h = p.val("sante_trajectoire.hopitaux_administratifs")
    masse = h["postes"] * h["cout_aligne"] / 1e9
    baisse = min(p.val("ia.plafond_taches_automatisables"),
                 max(0, t - p.val("ia.premiere_annee") + 1) * p.val("ia.departs_retraite_annuels") * p.val("ia.part_departs_non_remplaces"))
    return baisse * masse * (1 - p.val("ia.cout_services_ia"))


def trajectoire_statu_quo(p: Parametres, s: str) -> dict:
    """Santé du statu quo (ONDAM + autonomie, prévisions communes : dérive 2027-2029, assurance maladie puis PROMEDE,
    sur les salaires) et invalidité du statu quo (bloc « AAH et invalidité »), avec le facteur de croissance de la
    santé (rapport à la base de 2026) et celui des salaires depuis 2029. Sert de base quand
    sante_trajectoire.base_statu_quo est vrai (décision d'Adrien du 13/11/2026)."""
    import copy
    from . import statu_quo as sq
    from .unites import facteur
    if s == "prudent" and p.colonne_prudent != "prudent":
        # copie en_crise / en_scenario : le statu quo se calcule sur le vrai scénario, comme sq.blocs(p, s) du noyau
        s = p.colonne_prudent
        p = copy.copy(p)
        p.__dict__.pop("_cache", None)
        p.colonne_prudent = "prudent"
    san, blo, w, y = sq.sante(p, s), sq.blocs(p, s), sq.salaires(p, s), sq.pib(p, s)
    auto = p.val("sante.aide_sociale_autonomie_2024") * facteur(p, 2024, "recettes")
    inv = p.val("sante.pensions_invalidite_2024") * facteur(p, 2024, "recettes")
    part = inv / (p.val("statu_quo.aah") + inv)
    base = p.val("sante.ondam_2026") + auto
    return {"sante": san, "invalidite": {t: blo[t]["aah_invalidite"] * part for t in ANNEES},
            "C": {t: san[t] / base for t in ANNEES}, "wt": {t: w[t] / w[2029] for t in ANNEES},
            "yt": {t: y[t] / y[2029] for t in ANNEES}, "autonomie": auto}


def depenses(p: Parametres, s: str) -> dict[int, float]:
    if p.val("sante_trajectoire.base_statu_quo"):
        return _depenses_sur_statu_quo(p, s)
    base = sante_statique(p) + economies_sante_a_terme(p, "prudent")  # Santé!B5
    k = derive_2029(p)
    mesures = p.val("sante.mesures_a_terme", s)
    montee = p.val("sante_trajectoire.montee_mesures")
    options = p.val("sante_trajectoire.options")
    fg = p.val("sante_trajectoire.forfait_generalistes")
    g = p.val("macro.tendance", "prudent")
    out = {}
    for t in ANNEES:
        n = max(0, t - 2029)
        eco = sum(v * min(1, n / montee[m]) for m, v in mesures.items())
        eco += sum(o["montant"] * o["comptee"] * min(1, n) for o in options.values())
        cr = _croissance(p, s, t)
        forfait = fg["revalorise_croissance"] * fg["depense_am_2024"] * k * (cr - (1 + g) ** (t - 2029)) * (1 - fg["part_perdue"][s])
        out[t] = (base * k - eco) * cr - economie_hopitaux_ia(p, t) - forfait
    return out


def _depenses_sur_statu_quo(p: Parametres, s: str) -> dict[int, float]:
    """Santé du programme = santé + invalidité du statu quo (mêmes prévisions), moins les mesures du programme. Le
    périmètre propre au programme (gestion de l'assurance maladie, autonomie nette du revenu universel, coût des
    agents hospitaliers) suit la croissance de la santé du statu quo."""
    T = trajectoire_statu_quo(p, s)
    C, wt = T["C"], T["wt"]
    k = derive_2029(p)
    propre = _perimetre_propre(p, T)
    mesures = p.val("sante.mesures_a_terme", s)
    montee = p.val("sante_trajectoire.montee_mesures")
    options = p.val("sante_trajectoire.options")
    fg = p.val("sante_trajectoire.forfait_generalistes")
    out = {}
    for t in ANNEES:
        n = max(0, t - 2029)
        eco = sum(v * min(1, n / montee[m]) for m, v in mesures.items())
        eco += sum(o["montant"] * o["comptee"] * min(1, n) for o in options.values())
        forfait = fg["revalorise_croissance"] * fg["depense_am_2024"] * (C[t] - k * wt[t]) * (1 - fg["part_perdue"][s])
        out[t] = (T["sante"][t] + T["invalidite"][t] + propre * C[t] - eco * C[t] / k
                  - economie_hopitaux_ia(p, t) - forfait)
    return out


PRODUITS_NOCIFS = {"tabac": "Tabac", "alcool": "Alcool", "sucres": "Produits sucrés et ultra-transformés"}


def surplus_pib(p: Parametres, s: str) -> dict[int, float]:
    """Surplus de dépenses de santé au-delà d'une part constante du PIB (Md€) : dérive de la pente sur la base de
    2029, avant les mesures (même base que le garde-fou)."""
    if p.val("sante_trajectoire.base_statu_quo"):  # 14/11/2026 : santé du statu quo contre le PIB du statu quo
        T = trajectoire_statu_quo(p, s)
        tot = {t: T["sante"][t] + T["invalidite"][t] + _perimetre_propre(p, T) * T["C"][t] for t in ANNEES}
        return {t: max(0.0, tot[t] - tot[2029] * T["yt"][t]) for t in ANNEES}
    base = (sante_statique(p) + economies_sante_a_terme(p, "prudent")) * derive_2029(p)
    g = p.val("macro.tendance", "prudent")
    return {t: max(0.0, base * (_croissance(p, s, t) - (1 + g) ** (t - 2029))) for t in ANNEES}


def _perimetre_propre(p: Parametres, T: dict) -> float:
    """Périmètre santé propre au programme, hors statu quo (Md€ de 2026) : gestion de l'assurance maladie, autonomie
    nette du revenu universel, moins le coût des agents hospitaliers aligné sur le privé."""
    from .depenses.statique import autonomie, economie_hopitaux, securite_sociale
    return securite_sociale(p)[1] + autonomie(p) - economie_hopitaux(p) - T["autonomie"]


def _croissance_conso(p: Parametres, s: str) -> dict[int, float]:
    """Croissance des assiettes de consommation depuis 2029 : PIB du statu quo (base_statu_quo) ou tendance du prudent."""
    if p.val("sante_trajectoire.base_statu_quo"):
        return trajectoire_statu_quo(p, s)["yt"]
    g = p.val("macro.tendance", "prudent")
    return {t: (1 + g) ** (t - 2029) for t in ANNEES}


def bases_produits_nocifs(p: Parametres) -> dict[str, float]:
    """Dépense des ménages par produit nocif (Md€ de 2026) : part du panier médian (tva_produits.csv) × dépense de
    consommation des ménages (Insee 2025), portée en 2026 par la croissance en valeur."""
    import csv
    from .distribution import DONNEES
    parts = {l["categorie"]: float(l["part_median"]) for l in csv.DictReader((DONNEES / "tva_produits.csv").open(encoding="utf-8"))}
    conso = p.val("sante_produits_nocifs.consommation_menages_2025") * (1 + p.val("unites.pib_volume_2026")) * (1 + p.val("unites.deflateur_2026"))
    return {k: parts[cat] * conso for k, cat in PRODUITS_NOCIFS.items()}


def accise_produits_nocifs(p: Parametres, s: str) -> dict[int, dict]:
    """Surplus de dépenses de santé (au-delà d'une part constante du PIB) financé par une accise supplémentaire sur le
    tabac, l'alcool et les produits sucrés et ultra-transformés (décision d'Adrien, 05/11/2026).

    Chaque année, l'accise est relevée (hausse de prix commune, plafonnée par produit) pour couvrir le surplus de
    l'année précédente, net des soins déjà évités. La hausse de prix réduit le volume taxé (élasticité qui compte
    aussi les achats transfrontaliers et la contrebande) et la consommation (élasticité de consommation) ; la baisse
    de consommation réduit les soins avec un délai (moyenne des baisses des « annees_plein_effet » dernières années,
    les maladies évitées n'apparaissant que progressivement). Ce qui dépasse les plafonds reste en dépense
    (non_couvert). Montants en Md€ de 2026 ; recette et soins évités améliorent le solde."""
    q = p.val
    eps_taxe, eps_conso = q("sante_produits_nocifs.elasticite_volume_taxe", s), q("sante_produits_nocifs.elasticite_consommation", s)
    plafond = q("sante_produits_nocifs.hausse_prix_maximale")
    pp = q("tva_sante_long_terme.produits")
    couts = {"tabac": pp["tabac"]["cout_soins"], "alcool": q("tva.alcool")["cout_soins_md"], "sucres": pp["sucres"]["cout_soins"]}
    delai = q("tva_sante_long_terme.annees_plein_effet", s)
    g = q("macro.tendance", "prudent")
    base0 = bases_produits_nocifs(p)
    surplus = surplus_pib(p, s)
    cr_conso = _croissance_conso(p, s)

    def effets(x: float, crois: float) -> tuple[dict, float]:
        """Hausse de prix x (commune, plafonnée) : hausse par produit et recette supplémentaire."""
        h = {k: min(x, plafond[k]) for k in base0}
        rec = sum(h[k] * base0[k] * crois * (1 + h[k]) ** eps_taxe[k] for k in base0)
        return h, rec

    out, baisses = {}, []
    evites_prec = 0.0
    for t in ANNEES:
        crois = cr_conso[t]
        besoin = max(0.0, (surplus[t - 1] if t > 2029 else 0.0) - evites_prec)
        h_max, rec_max = effets(max(plafond.values()), crois)
        if besoin <= 0:
            h, rec = {k: 0.0 for k in base0}, 0.0
        elif rec_max <= besoin:
            h, rec = h_max, rec_max
        else:  # recette croissante en x jusqu'aux plafonds (élasticités > −1) : dichotomie
            lo, hi = 0.0, max(plafond.values())
            for _ in range(60):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if effets(mid, crois)[1] < besoin else (lo, mid)
            h, rec = effets(hi, crois)
        baisses.append({k: 1 - (1 + h[k]) ** eps_conso[k] for k in base0})
        fen = baisses[-delai:]
        evites = sum(couts[k] * crois * sum(b[k] for b in fen) / delai for k in base0)
        out[t] = {"surplus": surplus[t], "recette": rec, "soins_evites": evites,
                  "non_couvert": max(0.0, surplus[t] - rec - evites), "hausse_prix": h}
        evites_prec = evites
    return out


def garde_fou(p: Parametres, s: str = "prudent") -> dict[int, float]:
    """Effet sur le solde (Md€, + = mieux) du financement du surplus de santé.

    sante_produits_nocifs.active (décision du 05/11/2026) : accise sur les produits nocifs (accise_produits_nocifs),
    recette et soins évités. Sinon (v235) : dépassement de la pente d'engagement, repris l'année suivante par
    l'accise santé, sans effet sur la consommation."""
    if p.val("sante_produits_nocifs.active"):
        a = accise_produits_nocifs(p, s)
        return {t: a[t]["recette"] + a[t]["soins_evites"] for t in ANNEES}
    base = sante_statique(p) + economies_sante_a_terme(p, "prudent")
    k = derive_2029(p)
    d = p.val("sante_trajectoire.derniere_annee_phase_1")
    engagement = pente_1(p, "median")
    pente = pente_1(p, s)
    b = pente_2(p, s)
    depas = {t: max(0.0, base * k * ((1 + pente) ** (min(t, d) - 2029) - (1 + engagement) ** (min(t, d) - 2029)) * (1 + b) ** max(0, t - d)) for t in ANNEES}
    return {t: (0.0 if t == 2029 else depas[t - 1]) for t in ANNEES}


def tva_sante(p: Parametres) -> dict[str, dict[int, float]]:
    """Effet sur le solde du volet santé de la TVA : perte de recette (baisse des ventes) et soins évités."""
    pr = {x.categorie: x for x in produits_tva(p)}
    al = p.val("tva.alcool")
    recette_alcool = al["cout_soins_md"] * (1 - al["part_vin"] * al["abattement_vin"])
    ht = p.val("tva_sante_long_terme.hausse_prix_tabac")
    hausse = {"tabac": ht["prix_apres"] / ht["prix_avant"] - 1}
    import csv
    from .distribution import DONNEES
    ancien = {l["categorie"]: float(l["ancien_taux"]) for l in csv.DictReader((DONNEES / "tva_produits.csv").open(encoding="utf-8"))}
    hausse["alcool"] = (1 + pr["Alcool"].taux_total) / (1 + ancien["Alcool"]) - 1
    hausse["sucres"] = (1 + pr["Produits sucrés et ultra-transformés"].taux_total) / (1 + ancien["Produits sucrés et ultra-transformés"]) - 1
    pp = p.val("tva_sante_long_terme.produits")
    recettes = {"tabac": pp["tabac"]["recette"], "alcool": recette_alcool, "sucres": pp["sucres"]["recette"]}
    couts = {"tabac": pp["tabac"]["cout_soins"], "alcool": al["cout_soins_md"], "sucres": pp["sucres"]["cout_soins"]}
    eps = p.val("tva_sante_long_terme.elasticite_prix")
    baisse = {k: (1 + h) ** eps - 1 for k, h in hausse.items()}
    perte = sum(recettes[k] * baisse[k] for k in recettes)
    g = p.val("macro.tendance", "prudent")
    out = {"perte": {}, **{s: {} for s in SCENARIOS}}
    sur_sq = p.val("sante_trajectoire.base_statu_quo")
    for s in SCENARIOS:
        vb = p.val("tva_sante_long_terme.vraie_baisse_consommation", s)
        a_terme = -sum(couts[k] * baisse[k] * vb[k] for k in couts)
        annees = p.val("tva_sante_long_terme.annees_plein_effet", s)
        cr = _croissance_conso(p, s) if sur_sq else {t: (1 + g) ** (t - 2029) for t in ANNEES}
        for t in ANNEES:
            pt = perte * cr[t]
            evites = a_terme * min(1, max(0, t - 2028) / annees) * cr[t]
            if s == "prudent":
                out["perte"][t] = pt
            # sur le statu quo (14/11/2026), les soins évités comptent dans tous les scénarios : la pente commune ne
            # compte pas la prévention du programme ; avant, médian et optimiste : perte seule (leur pente la comptait)
            out[s][t] = pt + evites if (s == "prudent" or sur_sq) else pt
    return out
