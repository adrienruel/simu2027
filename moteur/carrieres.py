"""Réformes de l'enseignement supérieur : ce qu'elles changent aux carrières des générations (29 octobre 2026).

Réformes : sélection à l'université, apprentissage et alternance, RUI étudiant sous condition, prépas et écoles
facturées. Leurs coûts et économies budgétaires sont déjà comptés ailleurs (moteur/depenses/economies_missions.py :
années d'études en plus et sélection ; moteur/objectifs.py : RUI étudiant ; moteur/ascenseur_social.py : prépas et
écoles). Ce module ajoute leurs effets sur les carrières, dans les cellules de salariés (moteur/cohortes.py) et
dans l'emploi du module de population (moteur/demographie.py), donc dans le PIB et les recettes.

Quatre effets demandés, et ce qui en est retenu :
1. Entrée plus tôt dans l'emploi : les années d'études en plus supprimées (education.universite :
   3 % de 1,6 million d'étudiants, soit 48 000 années par an, économie déjà comptée au budget) sont passées
   hors des études. Une part de ces jeunes est en emploi (carrieres.entree_plus_tot) ; ils s'ajoutent aux
   personnes en emploi de 19 à 23 ans, sans venir du chômage (canal de la population active, comme les
   seniors : pas de double compte avec la courbe du chômage du bloc emploi).
2. Meilleur emploi des jeunes : déjà compté dans le bloc emploi (réformes « sélection à l'université et
   apprentissage » et « alternance », en points de chômage). Rien n'est ajouté ici.
3. et 4. Moins de décrochage et salaires plus élevés : une part d'une génération qui serait sortie du
   supérieur sans diplôme obtient une licence (carrieres.decrochage, en points de génération) ; elle gagne
   l'écart de salaire licence − bac général du Céreq, dont on ne garde qu'une part (le reste est un effet de
   sélection, pas de diplôme). Ce gain s'applique aux salaires des générations entrées dans le supérieur sous
   le nouveau système (nées à partir de carrieres.decrochage.premiere_generation), à partir de 22 ans. L'effet
   sur l'emploi de ce diplôme n'est pas ajouté : c'est le mécanisme du canal « sélection » du bloc emploi.
   Prudent et crise : 0 (pas d'estimation causale ; la hausse du passage en L2 après la loi ORE n'est pas
   attribuable à la loi, SIES 2023).

Les indices (moteur/demographie.indices, moteur/cohortes.indices) sont rapportés à 2029 sans ces effets, pour que
l'effet présent dès 2029 ne soit pas effacé par la normalisation.
"""
from __future__ import annotations

from .parametres import Parametres


def actif(p: Parametres) -> bool:
    return bool(p.val("carrieres.active")) and bool(p.val("demographie.active"))


def _ages(nom: str) -> range:
    a, b = nom.split("-")
    return range(int(a), int(b) + 1)


def emplois_entree_plus_tot(p: Parametres, jeu: str, t: int) -> dict[int, float]:
    """Personnes en emploi en plus, par âge, l'année t (entrée plus tôt dans l'emploi)."""
    if not actif(p):
        return {}
    e = p.val("carrieres.entree_plus_tot")
    u = p.val("education.universite")
    annees = u["part_annees_supplementaires"] * u["etudiants"]
    k = min(1.0, max(0.0, (t - e["debut"] + 1) / e["montee"]))
    if k <= 0:
        return {}
    ages = _ages(e["ages"])
    part = p.val("carrieres.entree_plus_tot_part_en_emploi", jeu)
    return {a: annees * part * k / len(ages) for a in ages}


def prime_salaire(p: Parametres, jeu: str, t: int, a: int) -> float:
    """Gain relatif de salaire moyen de la génération née en t − a, à l'âge a (moins de décrochage)."""
    if not actif(p):
        return 0.0
    d = p.val("carrieres.decrochage")
    points = p.val("carrieres.decrochage_points", jeu)
    if not points or a < d["age_diplome"] or t - a < d["premiere_generation"]:
        return 0.0
    # montée : les premières générations n'ont fait qu'une partie de leurs études sous le nouveau système
    k = min(1.0, (t - a - d["premiere_generation"] + 1) / d["montee_generations"])
    return points * d["ecart_salaire"] * d["part_causale"] * k


def resume(p: Parametres, jeu: str = "prudent", annees=(2029, 2032, 2037, 2050, 2073)) -> dict:
    """Pour la restitution : emplois en plus (milliers) et gain moyen de salaire des salariés (%), par année."""
    from .cohortes import AGES_ACTIFS, _taux_emploi
    from .demographie import population
    pops, te = population(p, jeu), _taux_emploi(p)
    out = {}
    for t in annees:
        emp = sum(emplois_entree_plus_tot(p, jeu, t).values())
        n = sum(pops[t][a] * te.get(a, 0.0) for a in AGES_ACTIFS)
        prime = sum(pops[t][a] * te.get(a, 0.0) * prime_salaire(p, jeu, t, a) for a in AGES_ACTIFS) / n
        out[t] = {"emplois_milliers": round(emp / 1e3, 1), "prime_salaire_pct": round(100 * prime, 3)}
    return out
