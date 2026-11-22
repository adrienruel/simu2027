"""Roadmap 4.4 (22/11/2026) : revenus du capital, dirigeants et entrepreneurs individuels, règles communes.

Trois canaux, séparés pour ne pas compter deux fois :

1. **Impôt sur les dividendes et les intérêts** (mesures marquées `pfu: {points, points_csg}`) : le moteur calcule le
   montant lui-même, au lieu du montant écrit par chaque programme. Recette = taux après × base après − taux avant ×
   base avant. Les dividendes répondent au taux net (élasticité `dividendes.elasticite_taux_net_scenarios`, réformes
   de 2013 et de 2018) ; les intérêts et les autres revenus du patrimoine soumis à la CSG ne répondent pas.
2. **Salaire ou dividendes** (dirigeants de sociétés) : une part `dividendes.part_redenomination` des dividendes perdus
   (ou gagnés) devient du salaire (ou en vient), taxé à `dividendes.ecart_prelevement_salaire_dividende`. France Stratégie
   (2023) ne trouve pas de redénomination en moyenne après le PFU : 0 au médian.
3. **Entrepreneurs individuels et IS** (mesures marquées `taux_is`) : quand l'écart entre l'impôt des personnes et l'IS
   se creuse, des entrepreneurs individuels passent à l'IS (semi-élasticité de la part des sociétés, de Mooij et
   Nicodème, 2008) ; leurs bénéfices passent de l'impôt sur le revenu et des cotisations des indépendants à l'IS et au
   PFU, moins lourds (`entreprises.ecart_prelevement_ei_is`).

Les scénarios sont ordonnés pour une hausse d'impôt (la crise perd le plus de base) ; une baisse prend le scénario
miroir, comme les bénéfices déplacés des groupes (roadmap 4.3).
"""
from __future__ import annotations

from .parametres import Parametres

MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}


def recette_pfu(p: Parametres, s: str, points: float = 0.0, points_csg: float = 0.0) -> dict[str, float]:
    """Recette en plus (Md€ de 2026, à plein effet) d'une hausse de `points` du PFU (part impôt sur le revenu) et de
    `points_csg` de la CSG sur les revenus du patrimoine. Détail : dividendes (statique, réponse de la base,
    redénomination), intérêts, autres revenus du patrimoine."""
    d = p.val("dividendes.bases_2026")
    tau = p.val("dividendes.pfu_actuel")
    delta = (points + points_csg) / 100
    sc = s if delta >= 0 else MIROIR[s]
    el = p.val("dividendes.elasticite_taux_net_scenarios", sc)
    base_apres = d["dividendes"] * ((1 - tau - delta) / (1 - tau)) ** el
    statique_div = delta * d["dividendes"]
    div = (tau + delta) * base_apres - tau * d["dividendes"]
    # dividendes perdus (ou gagnés) devenus salaire (ou venus du salaire) des dirigeants
    red = (p.val("dividendes.part_redenomination", sc) * (d["dividendes"] - base_apres)
           * p.val("dividendes.ecart_prelevement_salaire_dividende"))
    inte = delta * d["interets"]
    autres = points_csg / 100 * d["autres_csg"]
    return {"statique_dividendes": statique_div, "dividendes": div, "redenomination": red, "interets": inte,
            "autres_patrimoine": autres, "total": div + red + inte + autres}


def facteur_ei_vers_is(p: Parametres, s: str, montant: float) -> float:
    """Recette en plus par Md€ de montant statique d'une mesure sur le taux de l'IS, due aux entrepreneurs individuels
    qui changent de forme. Baisse de l'IS (montant < 0) : des EI passent à l'IS, le prélèvement baisse : facteur > 0,
    ligne négative. Δ taux (points) = montant / IS par point ; bénéfices qui changent de forme = semi-élasticité ×
    Δ points × bénéfices des PME à l'IS ; recette = − écart de prélèvement × bénéfices déplacés."""
    sc = MIROIR[s] if montant < 0 else s
    e = p.val("entreprises.ei_vers_is")
    semi = p.val("entreprises.semi_elasticite_incorporation", sc)
    par_point = e["is_md"] / (100 * e["taux_is"])
    return p.val("entreprises.ecart_prelevement_ei_is", sc) * semi / 100 * e["benefices_pme_is_md"] / par_point
