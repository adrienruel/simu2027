"""Déduction intégrale de l'investissement et fin de la déduction des intérêts (feuille IS investissement)."""
from __future__ import annotations

from .parametres import Parametres

ANNEES = list(range(2029, 2074))


def part_deduite(p: Parametres, t: int, montee: int | None = None) -> float:
    montee = montee or p.val("is_investissement.montee_annees")
    return min(1, (t - 2029 + 1) / montee) * p.val("is_investissement.part_admise")


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
    return {t: p.val("is_investissement.active") * part_deduite(p, t, p.val("is_investissement.montee_annees")) / p.val("is_investissement.part_admise")
            * p.val("is_investissement.part_payeurs_is") * taux * i["part_va"] * va * (1 - i["part_sans_recette"]) * (1 - i["part_reactions"]) * (1 + g) ** (t - 2029)
            for t in ANNEES}


def cout_net_etat(p: Parametres, etale: bool = False) -> dict[int, float]:
    """Coût net pour l'État (Md€) : déduction en plus × IS, moins les intérêts non déduits (lignes 41 et 78)."""
    montee = p.val("is_investissement.montee_etalee_annees") if etale else p.val("is_investissement.montee_annees")
    ded = _deduction_en_plus(p, montee)
    t_is = p.val("entreprises.taux_is_etat")
    rec = interets_non_deduits(p, t_is)
    return {t: p.val("is_investissement.active") * p.val("is_investissement.part_payeurs_is") * t_is * ded[t] - rec[t] for t in ANNEES}


def baisse_cout_capital(p: Parametres) -> float:
    """Baisse du coût du capital pour les entreprises qui paient l'IS (part du coût actuel, ligne 21)."""
    z = p.val("is_investissement.valeur_actuelle_amortissements")
    te = p.val("entreprises.taux_is_etat")
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
