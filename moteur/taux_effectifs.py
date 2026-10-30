"""Taux effectif moyen d'imposition des bénéfices (EATR, méthode Devereux et Griffith).

Pourquoi : un IS à 45 % avec déduction immédiate de l'investissement n'a pas le même effet qu'un IS à 45 %
avec les amortissements actuels. La littérature distingue :
- le transfert de bénéfices (montages comptables), qui suit le taux légal (Heckemeyer et Overesch, 2017) :
  la déduction de l'investissement n'y change rien ;
- le choix de localisation d'une activité rentable, qui suit le taux effectif moyen (Devereux et Griffith,
  1998 et 2003) : la déduction immédiate exonère le rendement normal du capital, seule la rente reste taxée ;
- l'investissement à la marge, qui suit le taux marginal effectif (coût du capital) : déjà traité par le
  module macro (canal de l'investissement).

Projet type de l'OCDE (Corporate Tax Statistics, méthodologie de Hanappi, 2018) : rentabilité avant impôt de
20 %, taux d'intérêt réel de 3 % ; dépréciation économique moyenne de 10 % par an.
"""
from __future__ import annotations

from .is_investissement import part_admise
from .parametres import Parametres


def eatr(taux: float, z: float, p: float, r: float, delta: float) -> float:
    """Taux effectif moyen d'un investissement d'une unité financé sur fonds propres.

    z : valeur actuelle des amortissements fiscaux par euro investi (1 = déduction immédiate)."""
    a = taux * z
    avant = (p - r) / (1 + r)
    apres = -(1 - a) + ((p + delta) * (1 - taux) + (1 - delta) * (1 - a)) / (1 + r)
    return (avant - apres) / (p / (1 + r))


def part_impots_production(p: Parametres) -> float:
    """Impôts de production assis sur le capital, en part du résultat avant ces impôts (système actuel)."""
    from .recettes import entreprises
    ent = entreprises._lire("entreprises.csv")
    assiette = sum(e["benefice_median"] * e["entreprises_beneficiaires"] for e in ent) / 1e9
    prod = p.val("entreprises.impots_production_2023") - p.val("entreprises.impots_production_hors_marchand")
    part_sal = p.val("emploi.impots_production_salaires") / p.val("entreprises.impots_production_2023")
    hors_salaires = prod * (1 - part_sal)
    return hors_salaires / (assiette + hors_salaires)


def eatr_actuel(p: Parametres) -> float:
    """IS à 25 % avec les amortissements actuels, après les impôts de production sur le capital (déductibles)."""
    c = p.val("entreprises.taux_effectifs")
    prod = part_impots_production(p)
    return prod + (1 - prod) * eatr(p.val("is_investissement.taux_is_actuel"),
                                    p.val("is_investissement.valeur_actuelle_amortissements"), c["rentabilite"],
                                    c["taux_reel"], c["depreciation"])


def eatr_nouveau(p: Parametres, jeu: str = "prudent", annee: int | None = None) -> float:
    """IS du nouveau système (État et local), déduction immédiate pour la part de l'investissement concernée,
    sans impôts de production."""
    c = p.val("entreprises.taux_effectifs")
    from .is_bareme import taux_grandes
    taux = (taux_grandes(p) + p.val("impot_local_entreprises.taux_communes")
            + p.val("impot_local_entreprises.taux_regions"))  # activités mobiles : taux des grandes entreprises
    z0 = p.val("is_investissement.valeur_actuelle_amortissements")
    part = (p.val("is_investissement.part_investissement_concernee", jeu) * p.val("is_investissement.active")
            * part_admise(p, annee))
    z = part * 1.0 + (1 - part) * z0
    return eatr(taux, z, c["rentabilite"], c["taux_reel"], c["depreciation"])


def ecart_localisation(p: Parametres, jeu: str = "prudent", annee: int | None = None) -> float | None:
    """Hausse du taux effectif moyen (points) qui pilote la localisation des activités ; None si le moteur
    garde la méthode de la v235 (taux légal du nouveau système contre taux effectif actuel).

    annee : part déduite en vigueur cette année-là (érosion de l'IS, année par année) ; None : part de départ
    (emplois de la localisation, qui se décident pendant la montée en charge : prudent)."""
    if not p.val("entreprises.localisation_taux_effectif"):
        return None
    return (eatr_nouveau(p, jeu, annee) - eatr_actuel(p)) * 100
