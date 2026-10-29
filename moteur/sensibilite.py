"""Sensibilité : quels paramètres pèsent le plus sur le solde ? (pour décider quoi sourcer d'abord)

Chaque paramètre numérique est augmenté de 10 % (toutes ses valeurs à la fois) ; on mesure l'écart de
solde (Md€) et de déficit (points de PIB) dans le prudent, sans clause de trajectoire.
Les années, les booléens et les textes sont laissés de côté.
"""
from __future__ import annotations

import copy
import dataclasses

from .macro import calculer
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


def _variante(p: Parametres, cle: str, k: float) -> Parametres:
    c = p.avec()
    c._p[cle] = dataclasses.replace(c._p[cle], valeur=_multiplier(copy.deepcopy(c._p[cle].valeur), k))
    return c


def _mesure(p: Parametres) -> dict:
    sc = calculer(p)["prudent"]
    return {t: (sc.solde_public[t], -sc.maastricht[t] * 100) for t in ANNEES_CLES}


def sensibilites(p: Parametres | None = None, statuts=("HYPOTHESE",), k: float = 1.1) -> list[dict]:
    p = (p or Parametres()).avec({"clause.active": False})
    base = _mesure(p)
    out = []
    for x in p:
        if x.statut not in statuts or x.unite == "annee" or not _numerique(x.valeur) or x.cle.startswith("crise."):
            continue
        try:
            v = _mesure(_variante(p, x.cle, k))
        except Exception as e:  # une variante qui casse un calcul est signalée, pas ignorée
            out.append({"cle": x.cle, "erreur": str(e)[:120]})
            continue
        out.append({"cle": x.cle, "unite": x.unite, "note": x.note,
                    **{f"solde_{t}": v[t][0] - base[t][0] for t in ANNEES_CLES},
                    **{f"deficit_{t}": v[t][1] - base[t][1] for t in ANNEES_CLES}})
    return sorted(out, key=lambda r: -abs(r.get("deficit_2037", 0)))
