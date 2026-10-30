"""Déduction intégrale de l'investissement et fin de la déduction des intérêts (feuille IS investissement)."""
from __future__ import annotations

from .parametres import Parametres

ANNEES = list(range(2029, 2074))


def part_admise(p: Parametres, t: int | None = None) -> float:
    """Part de l'investissement déduite immédiatement, à plein régime, l'année t (None : part de départ)."""
    depart = p.val("is_investissement.part_admise")
    if t is None:
        return depart
    h = dict(p.val("is_investissement.hausse_part_admise"))
    if h["debut"] == "conditionnel":
        pas = annees_sous_seuil(p, t)
        return depart + (max(depart, h["cible"]) - depart) * min(1.0, pas / h["duree"])
    if h["fin"] <= h["debut"]:
        return depart if t < h["debut"] else max(depart, h["cible"])
    k = min(1.0, max(0.0, (t - h["debut"] + 1) / (h["fin"] - h["debut"] + 1)))
    return depart + (max(depart, h["cible"]) - depart) * k


def annees_sous_seuil(p: Parametres, t: int) -> int:
    """Nombre d'années avant t où le déficit du prudent, avant clause, calculé sans la hausse, est sous le seuil :
    la part déduite monte d'un pas chacune de ces années (pause quand le déficit repasse au-dessus)."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("deficit_sans_hausse_deduction", p.colonne_prudent)
    if cle not in cache:
        from .macro import calculer
        sans = p.avec({"is_investissement.hausse_part_admise/debut": 9999, "is_investissement.hausse_part_admise/fin": 9999})
        sans.colonne_prudent, sans._surcharges, sans.taux_local_copie = p.colonne_prudent, p._surcharges, p.taux_local_copie
        cache[cle] = {u: c["avant"] for u, c in calculer(sans)["prudent"].detail["clause"].items()}
    seuil = p.val("is_investissement.hausse_part_admise")["seuil_deficit"]
    return sum(1 for u, d in cache[cle].items() if u < t and d < seuil)


def part_deduite(p: Parametres, t: int, montee: int | None = None) -> float:
    montee = montee or p.val("is_investissement.montee_annees")
    return min(1, (t - 2029 + 1) / montee) * part_admise(p, t)


def _deduction_en_plus(p: Parametres, montee: int) -> dict[int, float]:
    g, infl = p.val("macro.tendance", "prudent"), p.val("calendrier.inflation")
    inv = p.val("is_investissement.investissement_snf_2025")
    out = {t: 0.0 for t in ANNEES}
    for cat in p.val("is_investissement.categories").values():
        immediat = {t: part_deduite(p, t, montee) * inv * cat["part"] * (1 + g) ** (t - 2029) for t in ANNEES}
        stock = 0.0
        for t in ANNEES:
            n = t - 2029
            sortant = immediat[t - cat["duree"]] / (1 + infl) ** cat["duree"] if n >= cat["duree"] else 0.0
            stock = immediat[t] + stock / (1 + infl) - sortant
            out[t] += immediat[t] - stock / cat["duree"]
    return out


def interets_non_deduits(p: Parametres, taux: float) -> dict[int, float]:
    i = p.val("is_investissement.interets")
    va = i["ebe_2025"] / i["taux_marge_2025"]
    g = p.val("macro.tendance", "prudent")
    montee = p.val("is_investissement.montee_annees")
    return {t: p.val("is_investissement.active") * min(1, (t - 2029 + 1) / montee)
            * p.val("is_investissement.part_payeurs_is") * taux * i["part_va"] * va * (1 - i["part_sans_recette"]) * (1 - i["part_reactions"]) * (1 + g) ** (t - 2029)
            for t in ANNEES}


def cout_net_etat(p: Parametres, etale: bool = False) -> dict[int, float]:
    """Coût net (Md€) : déduction en plus × IS, moins les intérêts non déduits (lignes 41 et 78) ; IS de l'État et,
    depuis le 30/10/2026, IS local (même assiette)."""
    montee = p.val("is_investissement.montee_etalee_annees") if etale else p.val("is_investissement.montee_annees")
    ded = _deduction_en_plus(p, montee)
    from .is_bareme import taux_investissement
    t_is = taux_investissement(p)  # taux unique, ou marginal pondéré par l'investissement (IS progressif)
    if p.val("is_investissement.assiette_locale"):
        # l'IS local (communes, régions) a la même assiette que l'IS de l'État (moteur/collectivites.py) : la
        # déduction de l'investissement et la fin de la déduction des intérêts jouent aussi sur lui (30/10/2026)
        t_is += p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    rec = interets_non_deduits(p, t_is)
    return {t: p.val("is_investissement.active") * p.val("is_investissement.part_payeurs_is") * t_is * ded[t] - rec[t] for t in ANNEES}


def baisse_cout_capital(p: Parametres) -> float:
    """Baisse du coût du capital pour les entreprises qui paient l'IS (part du coût actuel, ligne 21)."""
    z = p.val("is_investissement.valeur_actuelle_amortissements")
    from .is_bareme import taux_investissement
    te = taux_investissement(p)
    tl = p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    ta = p.val("is_investissement.taux_is_actuel")
    return ((1 - te * z - tl * z) / (1 - te - tl) - 1) / ((1 - ta * z) / (1 - ta))


def entrees_macro(p: Parametres) -> dict:
    return {"investissement": p.val("is_investissement.investissement_snf_2025"),
            "b18": p.val("is_investissement.valeur_actuelle_amortissements"),
            "b19": p.val("is_investissement.taux_is_actuel"),
            "b4": p.val("is_investissement.active"),
            "b20": {s: p.val("is_investissement.part_investissement_concernee", s) for s in ("prudent", "median", "optimiste")},
            "b21": baisse_cout_capital(p),
            "ligne25": [part_deduite(p, t) for t in ANNEES]}
