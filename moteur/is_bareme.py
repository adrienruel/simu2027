"""IS progressif (test demandé par Adrien le 30/10/2026) : barème par tranches de bénéfice, pour l'IS de l'État.

Sans barème (entreprises.is_progressif.active : non), toutes les fonctions rendent le taux unique
entreprises.taux_is_etat. Avec un barème, chaque usage prend le taux qui lui correspond :
- recettes : barème appliqué au bénéfice de chaque classe (moteur/recettes/entreprises.py) ;
- investissement et déduction : taux marginal de chaque taille d'entreprise, au bénéfice moyen de la taille ;
- transfert de bénéfices et localisation des activités : taux des grandes entreprises (activités mobiles) ;
- usages agrégés sans répartition par entreprise (bailleurs, accises nettes d'IS) : taux moyen effectif.
L'IS local (communes, régions) reste proportionnel.
"""
from __future__ import annotations

from .parametres import Parametres


def actif(p: Parametres) -> bool:
    b = p.val("entreprises.is_progressif")
    return bool(b and b.get("active"))


def tranches(p: Parametres) -> list[tuple[float, float]]:
    """(seuil bas, taux) de chaque tranche, seuils croissants ; taux unique sans barème."""
    if not actif(p):
        return [(0.0, p.val("entreprises.taux_is_etat"))]
    return [(float(s), float(t)) for s, t in p.val("entreprises.is_progressif")["tranches"]]


def impot_etat(p: Parametres, benefice: float) -> float:
    tr = tranches(p)
    total = 0.0
    for i, (s, t) in enumerate(tr):
        haut = tr[i + 1][0] if i + 1 < len(tr) else float("inf")
        if benefice > s:
            total += (min(benefice, haut) - s) * t
    return total


def taux_marginal_etat(p: Parametres, benefice: float) -> float:
    taux = tranches(p)[0][1]
    for s, t in tranches(p):
        if benefice > s:
            taux = t
    return taux


def taux_local(p: Parametres) -> float:
    return p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")


def benefice_representatif(x: dict) -> float:
    """Bénéfice moyen d'une entreprise bénéficiaire de la taille (DGFiP 2024 ; part des bénéficiaires : 62 %,
    1,7 million sur 2,72, appliquée à toutes les tailles)."""
    return x["benefices_md"] * 1e9 / (x["entreprises_is"] * 0.62)


def taux_taille(p: Parametres, taille: str) -> float:
    """Taux marginal de l'IS de l'État au bénéfice moyen de la taille (TPE, PME, ETI, GE)."""
    if not actif(p):
        return p.val("entreprises.taux_is_etat")
    from .entreprises_cellules import tailles
    x = next(y for y in tailles(p) if y["taille"] == taille)
    return taux_marginal_etat(p, benefice_representatif(x))


def taux_grandes(p: Parametres) -> float:
    """Taux des grandes entreprises (transfert de bénéfices, localisation des activités mobiles)."""
    return taux_taille(p, "GE")


def taux_investissement(p: Parametres) -> float:
    """Taux marginal moyen pondéré par l'investissement de chaque taille (valeur de la déduction)."""
    if not actif(p):
        return p.val("entreprises.taux_is_etat")
    from .entreprises_cellules import tailles
    return sum(x["part_investissement"] * taux_taille(p, x["taille"]) for x in tailles(p))


def taux_moyen(p: Parametres, scenario: str = "prudent") -> float:
    """Taux moyen effectif de l'IS de l'État sur les entreprises bénéficiaires (usages agrégés)."""
    if not actif(p):
        return p.val("entreprises.taux_is_etat", scenario)
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("is_taux_moyen", scenario)
    if cle not in cache:
        from .recettes.entreprises import classes_entreprises
        c = classes_entreprises(p, scenario)
        cache[cle] = (sum(x["is"] * x["entreprises_beneficiaires"] for x in c)
                      / sum(x["base_is"] * x["entreprises_beneficiaires"] for x in c))
    return cache[cle]
