"""Capital des entreprises : stock commun, usure et coût du capital (phase E5 de la roadmap, 14/11/2026).

Un impôt sur les entreprises change leur coût du capital ; l'investissement réagit (élasticité au coût du capital,
macro.elasticite_invest), le capital s'accumule et s'use, et chaque euro de capital en plus produit chaque année son
rendement net plus son usure. C'est la mécanique des cohortes d'entreprises d'Écologie de droite
(programmes/ecologie_de_droite/effets.py, moteur/entreprises_cellules.flux_investissement), désormais commune :

    flux_t = − élasticité × Δcoût_t × investissement des SNF_t       (Md€ d'investissement en plus)
    ΔK_t   = (1 − usure) × ΔK_(t−1) + flux_t                         (capital en plus, Md€)
    ΔPIB_t = ΔK_t × (rendement net + usure)                          (macro.pib_par_euro_capital + macro.usure_capital)

Δcoût_t : variation relative du coût du capital, chaque variation montant en macro.montee_invest ans. À long terme,
ΔK = élasticité × |Δcoût| × investissement / usure, soit le capital des SNF (≈ 3 650 Md€ = 365 / 0,10) × élasticité ×
|Δcoût|.

Avant (canal d'offre commun, `offre.capital_entreprises_par_point`) : PIB × part du capital (0,35) × variation du
capital, soit environ deux fois plus par euro de capital (0,35 × PIB / capital des SNF ≈ 0,29, contre un rendement
brut de 0,13 à 0,15 : taux de marge des SNF 32 % × valeur ajoutée 1 545 Md€ / capital ≈ 0,14 ; coût d'usage ≈ 0,14).
La part du capital s'applique à la valeur ajoutée des entreprises, pas à tout le PIB.

Les taux d'intérêt ne passent pas ici : leur effet, capital compris, est dans la variante de taux de Mésange
(moteur/bouclage.py, rétroaction du noyau).
"""
from __future__ import annotations

from . import statu_quo as sq

MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}


def valeur_euro(p, s: str) -> float:
    """PIB produit chaque année par un euro de capital des entreprises en plus : rendement net + usure."""
    return sq._v(p, "macro.pib_par_euro_capital", s) + sq._v(p, "macro.usure_capital", s)


def baisse_cout_par_point(p, s: str) -> float:
    """Baisse relative du coût du capital pour 1 point de PIB d'impôt sur les entreprises en moins : coût
    (1 − τz)/(1 − τ) au taux d'IS de 25 %, la baisse du taux qui fait 1 point de PIB d'IS du statu quo."""
    rec = sq.recettes_par_impot(p, s)[2029]
    y29 = sq.pib(p, s)[2029]
    tau, z = 0.25, p.val("is_investissement.valeur_actuelle_amortissements")
    dtau = tau / (rec["impot_sur_les_societes"] / y29 * 100)
    cc = (1 - tau * z) / (1 - tau)
    cc2 = (1 - (tau - dtau) * z) / (1 - (tau - dtau))
    return 1 - cc2 / cc


def accumuler(p, s: str, dcout: dict, annees) -> dict:
    """Capital et PIB en plus pour une variation relative du coût du capital (dcout : {année: fraction}, négative =
    coût plus bas). Une baisse prend l'élasticité du scénario, une hausse celle du scénario miroir (phase A4). Rend
    {"flux", "capital", "pib"} en Md€."""
    annees = list(annees)
    usure = sq._v(p, "macro.usure_capital", s)
    montee = sq._v(p, "macro.montee_invest", s)
    el = {sc: sq._v(p, "macro.elasticite_invest", sc) for sc in (s, MIROIR[s])}
    y = sq.pib(p, s)
    inv0 = p.val("is_investissement.investissement_snf_2025")
    v = valeur_euro(p, s)
    flux, capital, pib = {}, {}, {}
    k, prec, chocs = 0.0, 0.0, []
    for i_t, t in enumerate(annees):
        d = dcout.get(t, 0.0) - prec
        prec = dcout.get(t, 0.0)
        if d:
            chocs.append((i_t, d))
        effectif = sum(x * min(1.0, (i_t - j + 1) / montee) for j, x in chocs)  # chaque variation monte en `montee` ans
        e = el[s] if effectif <= 0 else el[MIROIR[s]]
        inv = inv0 * y[max(t, 2029)] / y[2029]
        flux[t] = -e * effectif * inv
        k = (1 - usure) * k + flux[t]
        capital[t] = k
        pib[t] = k * v
    return {"flux": flux, "capital": capital, "pib": pib}


def effet_fiscal(p, s: str, pts: dict, annees) -> dict:
    """Points de PIB d'impôt sur les entreprises en moins (pts, + = baisse) → capital et PIB en plus (Md€), et effet sur
    le PIB en % du statu quo (effet_pib_pct), pour le canal d'offre commun."""
    k = baisse_cout_par_point(p, s)
    r = accumuler(p, s, {t: -k * pts.get(t, 0.0) for t in annees}, annees)
    y = sq.pib(p, s)
    r["effet_pib_pct"] = {t: r["pib"][t] / y[max(t, 2029)] * 100 for t in annees}
    return r


def capital_public(p, s: str, pts: dict, annees) -> dict:
    """Capital public en plus (points de PIB) et effet productif sur le PIB (%), pour l'investissement public en plus
    (pts : points de PIB investis chaque année, + = plus d'investissement) ; phase E5.

    K_t = (1 − usure) × K_(t−1) + pts_t ; effet_t = θ × K_t, θ = effet_long_terme × usure, pour qu'un point de PIB
    investi chaque année donne effet_long_terme à long terme. effet_long_terme ne compte que l'effet productif EN PLUS
    de la demande : la demande bouclée (moteur/bouclage.py) garde déjà ≈ 0,19 à long terme pour toute dépense. Une
    baisse prend la valeur du scénario miroir. Le capital reste après la fin de l'investissement et s'use."""
    c = p.val("capital_public.parametres")
    us = c["usure"]
    lt = {sc: c["effet_long_terme"][sc] for sc in (s, MIROIR[s])}
    k, out_k, out_e = 0.0, {}, {}
    for t in annees:
        k = (1 - us) * k + pts.get(t, 0.0)
        out_k[t] = k
        out_e[t] = (lt[s] if k >= 0 else lt[MIROIR[s]]) * us * k
    return {"capital_pts": out_k, "effet_pib_pct": out_e}
