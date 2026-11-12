"""Variante migratoire commune (phase B2 de la roadmap, DÉCISION d'Adrien du 12/11/2026, soir).

Un programme qui change le solde migratoire déclare, dans `<nom>_canaux.solde_migratoire`, la variation du solde
annuel (personnes par an, par scénario ; négatif = moins d'entrées nettes), son début et sa montée. Le moteur :

1. construit l'écart de population par âge, année par année : chaque année, la variation du solde est répartie par
   âge selon le profil des immigrés de l'Insee (demographie.migrations.profil), puis vieillit avec la survie de la
   projection centrale (âges de 60 ans et plus ; avant 60 ans, survie quasi complète) ;
2. recalcule le statu quo avec cette population (statu_quo.population) : emploi aux taux par âge de 2025, corrigé du
   taux d'emploi relatif des immigrés (demographie.migrations.emploi_relatif), PIB, recettes par cellules de
   salariés, dépenses qui suivent la population (prestations, santé, collectivités, école, pensions par génération) ;
3. rend les écarts au statu quo : recettes, dépenses par bloc, PIB, emploi et population active, pour le programme.

Limites écrites : les enfants nés en France des personnes en plus ou en moins ne sont pas comptés (fécondité de la
projection inchangée) ; les salaires des personnes concernées sont ceux de la moyenne de leur âge (seul l'emploi est
corrigé) ; les dépenses propres à l'immigration (asile, AME, rétention) restent dans les mesures des programmes.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES
from .parametres import Parametres

AGE_MAX = 105


def _profil(p: Parametres) -> list[float]:
    """Part de chaque âge dans le solde migratoire (somme 1), à partir des tranches de l'Insee."""
    from .demographie import _tranche
    tr = p.val("demographie.migrations")["profil"]
    w = [0.0] * (AGE_MAX + 1)
    for nom, part in tr.items():
        ages = list(_tranche(nom)) if not nom.endswith("+") else list(range(int(nom[:-1]), 80))
        for a in ages:
            w[a] += part / len(ages)
    tot = sum(w)
    return [x / tot for x in w]


MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}


def variation(p: Parametres, s: str, decl: dict) -> float:
    """Variation du solde migratoire annuel (personnes) : donnée directement (« variation »), ou tirée des titres de
    séjour en moins (« titres_en_moins ») × part au solde × réalisation (demographie.titres_vers_solde). Une hausse
    des entrées (titres négatifs) prend le scénario miroir."""
    if "variation" in decl:
        v = decl["variation"]
        return v[s] if isinstance(v, dict) else v
    n = decl["titres_en_moins"]
    n = n[s] if isinstance(n, dict) else n
    c = p.val("demographie.titres_vers_solde")
    sc = s if n >= 0 else MIROIR[s]
    return -n * c["part_au_solde"][sc] * c["realisation"][sc]


def ecart_population(p: Parametres, s: str, decl: dict) -> dict[int, list[float]]:
    """Écart de population par âge (personnes) dû à la variation du solde migratoire déclarée."""
    from .demographie import _projection
    c = _projection("central")
    prof = _profil(p)
    v = variation(p, s, decl)
    debut, montee = int(decl.get("debut", 2028)), max(1, int(decl.get("montee", 1)))
    d = [0.0] * (AGE_MAX + 1)
    out = {}
    for t in range(2026, ANNEES[-1] + 1):
        if t > 2026:
            nd = [0.0] * (AGE_MAX + 1)
            for a in range(AGE_MAX):
                surv = (min(1.0, c[t][a + 1] / c[t - 1][a]) if a >= 60 and c[t - 1][a] > 0 else 0.999)
                nd[a + 1] += d[a] * surv
            nd[AGE_MAX] += d[AGE_MAX] * 0.6
            d = nd
        k = min(1.0, max(0.0, (t - debut + 1) / montee))
        for a in range(AGE_MAX + 1):
            d[a] += v * k * prof[a]
        out[t] = list(d)
    return out


def effets(p: Parametres, s: str, decl: dict) -> dict:
    """Écarts au statu quo (Md€ de 2026, personnes) : recettes, blocs, PIB, emploi, actifs."""
    cache = p.__dict__.setdefault("_cache", {})
    v = variation(p, s, decl)
    cle = ("migrations", s, v, decl.get("debut", 2028), decl.get("montee", 1))
    if cle in cache:
        return cache[cle]
    q = p.avec({})
    q._choc_population = ecart_population(p, s, decl)
    e0, e1 = sq.effectifs(p, s), sq.effectifs(q, s)
    y0, y1 = sq.pib(p, s), sq.pib(q, s)
    r0, r1 = sq.recettes(p, s), sq.recettes(q, s)
    b0, b1 = sq.blocs(p, s), sq.blocs(q, s)
    # santé : le statu quo ne la fait pas dépendre de la population ; ici, rapport des populations pondérées par la
    # dépense relative par âge (demographie.sante_relative_age)
    from .demographie import _tranche
    poids = [0.0] * (AGE_MAX + 1)
    for nom, w in p.val("demographie.sante_relative_age").items():
        for a in _tranche(nom):
            poids[a] = w
    pop0, san = sq.population(p, s), sq.sante(p, s)
    blocs = {t: {b: b1[t][b] - b0[t].get(b, 0.0) for b in b1[t]} for t in ANNEES}
    for t in ANNEES:
        ref = sum(pop0[t][a] * poids[a] for a in range(AGE_MAX + 1))
        blocs[t]["sante"] = blocs[t].get("sante", 0.0) + san[t] * sum(q._choc_population[t][a] * poids[a]
                                                                    for a in range(AGE_MAX + 1)) / ref
    out = {
        "recettes": {t: r1[t] - r0[t] for t in ANNEES},
        "blocs": blocs,
        "pib": {t: y1[t] - y0[t] for t in ANNEES},
        "emploi": {t: e1[t]["emploi"] - e0[t]["emploi"] for t in ANNEES},
        "actifs": {t: (e1[t]["emploi"] + e1[t]["chomeurs"]) - (e0[t]["emploi"] + e0[t]["chomeurs"]) for t in ANNEES},
        "population": {t: e1[t]["total"] - e0[t]["total"] for t in ANNEES},
        "variation_solde": v,
    }
    cache[cle] = out
    return out
