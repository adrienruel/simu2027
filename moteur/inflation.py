"""Inflation année par année et règle d'indexation (30 octobre 2026, demandes d'Adrien).

Inflation de base : projections de la Banque de France (septembre 2026 : IPCH 1,9 % en 2027, 1,6 % en 2028), puis
convergence vers une inflation de long terme par scénario (cible de la BCE : 2 %). Inflation due au programme,
ajoutée à la base :
- prix du carbone : sa hausse réelle (valeur de l'action pour le climat, +3,2 % par an jusqu'en 2060, plus le
  saut à 300 € en 2030) renchérit l'énergie, au poids des taxes carbone dans la consommation, qui baisse avec les
  émissions ; transmission à l'inflation globale par scénario (les taxes carbone européennes et canadiennes n'ont
  pas augmenté significativement l'inflation globale : Konradt et Weder di Mauro, 2023) ;
- écart de production : l'effort budgétaire de 2029 fait baisser l'activité, donc l'inflation (pente de la
  courbe de Phillips) ;
- bascule de la TVA et des impôts sur les produits : neutre par construction (l'accise de transition cale les
  nouvelles taxes sur la consommation sur les anciennes) ; fin des impôts de production : gardée en bénéfice par
  les entreprises dans le budget statique (taxée à l'IS), donc pas de baisse des prix comptée (cohérence).

Règle d'indexation (DÉCISION d'Adrien du 30/10/2026) : RUI, AAH, socle et seuils de la contribution des retraités
revalorisés du minimum de l'inflation et de la croissance nominale. En euros constants : leur valeur réelle reste
la même, sauf les années où la croissance réelle est négative (elle baisse alors d'autant, sans rattrapage).
Ancienne règle : revalorisés de la croissance réelle sans l'inflation (perte de pouvoir d'achat d'environ 1,1 %
par an).
"""
from __future__ import annotations

from .parametres import Parametres

ANNEES = list(range(2027, 2074))


def ecart_production(p: Parametres, jeu: str, t: int) -> float:
    """Écart de production dû à l'effort budgétaire de 2029 (part du PIB, négatif), connu avant le calcul macro."""
    if t < 2029:
        return 0.0
    from .anciennes_pensions import recette_nette
    from .unites import facteur
    pib = 2920 * facteur(p, 2024, "recettes")
    # même effort que l'ancien module macro (supprimé le 12/11/2026 ; à remplacer par l'impulsion calculée) : effort de 2029 + prélèvement net sur les anciennes pensions − assouplissement
    # prélèvement net de 2029 sur les anciennes pensions : il ne dépend pas de l'inflation (pensions calées en 2029) ;
    # calculé sans le module d'inflation pour éviter la boucle (l'érosion des pensions gelées dépend de l'inflation)
    cache = p.__dict__.setdefault("_cache", {})
    if "recette_anc_2029" not in cache:
        q = p.avec({"inflation.active": False})
        q.colonne_prudent, q._surcharges = p.colonne_prudent, p._surcharges
        cache["recette_anc_2029"] = recette_nette(q)[2029]
    eff = max(0.0, p.val("macro.effort_2029", jeu) + cache["recette_anc_2029"] / pib - p.val("macro.assouplissement_2029"))
    n = t - 2029
    return -eff * p.val("macro.multiplicateur", jeu) * max(0.0, 1 - n / p.val("macro.annees_effet_ajustement", jeu))


def serie(p: Parametres, jeu: str = "prudent") -> dict[int, float]:
    """Inflation de chaque année (2027-2073)."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("inflation", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    if not p.val("inflation.active"):
        out = {t: p.val("calendrier.inflation") for t in ANNEES}
        cache[cle] = out
        return out
    b = p.val("inflation.base")
    lt = p.val("inflation.long_terme", jeu)
    conv = b["convergence_annees"]
    from .carbone import prix
    kappa = p.val("inflation.pente_phillips", jeu)
    trans = p.val("inflation.transmission_carbone", jeu)
    poids0 = p.val("inflation.poids_taxes_carbone_consommation")
    baisse = p.val("carbone.baisse_tendancielle_emissions", jeu)
    if p.val("ecologie_options.emissions_activite"):
        # poids des taxes carbone dans la consommation : assiette (émissions du statu quo × réponse au prix, comme la
        # recette carbone) rapportée au PIB
        from . import statu_quo as sq
        from .ecologie import emissions as em
        from .carbone import reponse_moyenne
        rep = reponse_moyenne(p, jeu)
        ind, y = em.indice(p, jeu), sq.pib(p, em.scenario(p, jeu))
        evol = {t: ind[t] * rep[t] / rep[2029] / (y[t] / y[2029]) for t in range(2029, 2074)}
    else:
        evol = {t: (1 + baisse) ** (t - 2029) for t in range(2029, 2074)}
    out = {}
    for t in ANNEES:
        if t == 2027:
            base = b["2027"]
        elif t == 2028:
            base = b["2028"]
        else:
            k = min(1.0, (t - 2028) / conv)
            base = b["2028"] + (lt - b["2028"]) * k
        carbone = 0.0
        if t >= 2030:
            poids = poids0 * evol[t]
            carbone = trans * poids * (prix(p, t) / prix(p, t - 1) - 1)
        phillips = kappa * (ecart_production(p, jeu, t) - (ecart_production(p, jeu, t - 1) if t > 2029 else 0.0)) if t >= 2029 else 0.0
        out[t] = base + carbone + phillips
    cache[cle] = out
    return out


def facteur_prix(p: Parametres, depuis: int, jusqu_a: int, jeu: str = "prudent") -> float:
    """Hausse cumulée des prix de la fin de l'année « depuis » à la fin de « jusqu_a » (gardée dans le cache de p :
    plusieurs centaines de milliers d'appels par passage)."""
    cache = p.__dict__.setdefault("_cache", {}).setdefault(("facteur_prix", jeu, p.colonne_prudent), {})
    cle = (depuis, jusqu_a)
    if cle not in cache:
        s = serie(p, jeu)
        f = 1.0
        for t in range(depuis + 1, jusqu_a + 1):
            f *= 1 + s.get(t, p.val("calendrier.inflation"))
        cache[cle] = f
    return cache[cle]


def indice_reel(p: Parametres, jeu: str = "prudent") -> dict[int, float]:
    """Valeur réelle des montants indexés (RUI, AAH, socle, seuils de la contribution), 1 en 2029."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("indice_reel", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    regle = p.val("revalorisation.regle")
    g = p.val("macro.tendance", jeu)
    out = {}
    if regle == "min_inflation_croissance_nominale":
        idx = 1.0
        for t in range(2029, 2074):
            if t > 2029:
                # revalorisation de janvier sur l'année écoulée : croissance réelle de t − 1 (tendance + variation de
                # l'écart de production ; 2029 : récession de l'effort budgétaire)
                u = t - 1
                gr = g + ecart_production(p, jeu, u) - (ecart_production(p, jeu, u - 1) if u > 2029 else 0.0)
                idx *= min(1.0, 1 + gr)
            out[t] = idx
    elif regle == "croissance_sans_inflation":
        infl = serie(p, jeu)
        prod = {t: (1 + p.val("macro.productivite", jeu)) ** max(0, min(p.val("macro.annees_productivite", jeu),
                                                                        t - p.val("macro.premiere_annee_productivite") + 1))
                for t in range(2029, 2074)}
        f = 1.0
        for t in range(2029, 2074):
            if t > 2029:
                f *= (1 + g) / (1 + infl[t])
            out[t] = f * prod[t]
    else:
        out = {t: 1.0 for t in range(2029, 2074)}
    cache[cle] = out
    return out
