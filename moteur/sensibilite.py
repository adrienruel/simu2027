"""Sensibilité : quels paramètres pèsent le plus sur le solde ? (pour décider quoi sourcer d'abord)

Chaque hypothèse numérique est augmentée de 10 % ; on mesure l'écart de solde (Md€) et de déficit
(points de PIB) dans le prudent, sans clause de trajectoire. Une valeur par scénario est augmentée dans
tous les scénarios ; une valeur structurée (dictionnaire) l'est champ par champ (« cle/champ »), sauf
une liste, augmentée d'un bloc. Les années, les booléens et les textes sont laissés de côté.

    python -m moteur.sensibilite      # écrit sorties/sensibilite.json (quelques minutes)
"""
from __future__ import annotations

import copy
import dataclasses

from .parametres import Parametres

ANNEES_CLES = (2029, 2032, 2037, 2050)


def _multiplier(v, k):
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        return v * k
    if isinstance(v, list):
        return [_multiplier(x, k) for x in v]
    if isinstance(v, dict):
        return {a: _multiplier(b, k) for a, b in v.items()}
    return v


def _numerique(v) -> bool:
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return False
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (list, dict)):
        return any(_numerique(x) for x in (v.values() if isinstance(v, dict) else v))
    return False


def _variante(p: Parametres, cle: str, k: float, chemin: tuple = ()) -> Parametres:
    c = p.avec()
    valeur = copy.deepcopy(c._p[cle].valeur)
    if not chemin:
        valeur = _multiplier(valeur, k)
    else:
        cible = valeur
        for x in chemin[:-1]:
            cible = cible[x]
        cible[chemin[-1]] = _multiplier(cible[chemin[-1]], k)
    c._p[cle] = dataclasses.replace(c._p[cle], valeur=valeur)
    return c


def _cibles(x) -> list[tuple]:
    """Les sous-champs à perturber séparément (vide = le paramètre d'un bloc)."""
    if x.par_scenario or not isinstance(x.valeur, dict):
        return [()]
    out = []
    def descendre(v, chemin):
        if isinstance(v, dict) and len(chemin) < 2:
            for a, b in v.items():
                descendre(b, chemin + (a,))
        elif _numerique(v):
            out.append(chemin)
    descendre(x.valeur, ())
    return out or [()]
