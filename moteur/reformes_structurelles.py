"""Gains de productivité des réformes de structure : barème commun à tous les programmes (12/11/2026).

Demande d'Adrien : évaluer les gains de productivité de la façon la plus juste possible, pour tous les programmes, au
lieu d'un gain propre à « Écologie de droite ». Méthode : le cadre de quantification de l'OCDE (Égert et Gal, 2017),
qui donne l'effet sur le PIB par habitant d'une « réforme typique observée » par domaine, à 5 ans, 10 ans et long terme.
Les domaines retenus sont ceux que le reste du modèle ne compte pas déjà : réglementation des marchés de produits (pmr)
et protection de l'emploi (epl). Les autres domaines du cadre (coin fiscal, assurance chômage, IS, retraite, SMIC,
recherche, garde d'enfants) passent déjà par le canal d'offre commun, les mesures d'emploi ou les instruments.

Chaque programme déclare un nombre de réformes typiques par domaine (positif : libéralise ; négatif : réglemente ou
nationalise), avec la mesure qui le justifie, dans `<nom>_canaux.reformes_structurelles` (barème et grille :
parametres/commun/economie.yaml, macro.reformes_structurelles).
"""
from __future__ import annotations

from .parametres import Parametres

MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}
DOMAINES = ("pmr", "epl")


def _chemin(b: dict, k: int, part_lt: float, annee_lt: int) -> float:
    """Effet d'une réforme typique k années après son début (k = 1 la première année)."""
    if k <= 0:
        return 0.0
    if k <= 5:
        return b["cinq_ans"] * k / 5
    if k <= 10:
        return b["cinq_ans"] + (b["dix_ans"] - b["cinq_ans"]) * (k - 5) / 5
    return b["dix_ans"] + part_lt * (b["long_terme"] - b["dix_ans"]) * min(1.0, (k - 10) / (annee_lt - 10))


def gain(p: Parametres, decl: dict, s: str, t: int) -> float:
    """Gain relatif de PIB (0,01 = +1 %) l'année t, scénario s, pour les réformes déclarées `decl`
    ({"pmr": n, "epl": n, "debut": année})."""
    bar = p.val("macro.reformes_structurelles")
    if s == "prudent" and getattr(p, "colonne_prudent", "prudent") == "crise":
        s = "crise"  # copie de crise d'« Écologie de droite » (Parametres.en_crise) : la colonne prudente lit la crise
    k = t - int(decl.get("debut", 2028)) + 1
    total = 0.0
    for dom in DOMAINES:
        n = max(-bar["plafond"], min(bar["plafond"], float(decl.get(dom, 0.0))))
        if not n:
            continue
        jeu = s if n > 0 else MIROIR[s]
        effet = bar["poids"][jeu] * _chemin(bar[dom], k, bar["part_long_terme"][jeu], bar["annee_long_terme"])
        if dom == "epl":
            effet *= bar["part_hors_emploi_epl"]
        total += n * effet
    return total
