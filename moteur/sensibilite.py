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

from . import noyau
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


def _mesure(p: Parametres) -> dict:
    """Solde (Md€) et déficit (points de PIB) du prudent du programme sur le noyau commun (12/11/2026)."""
    res = noyau.simuler(p, noyau.charger(p.programme), scenarios=("prudent",))["prudent"]
    return {t: (res[t]["solde"], res[t]["deficit"]) for t in ANNEES_CLES}


def sensibilites(p: Parametres | None = None, statuts=("HYPOTHESE",), k: float = 1.1) -> list[dict]:
    p = (p or Parametres()).avec({"clause.active": False})
    base = _mesure(p)
    out = []
    for x in p:
        if x.statut not in statuts or x.unite == "annee" or not _numerique(x.valeur) or x.cle.startswith("crise."):
            continue
        for chemin in _cibles(x):
            nom = "/".join((x.cle,) + tuple(str(c) for c in chemin))
            try:
                v = _mesure(_variante(p, x.cle, k, chemin))
            except Exception as e:  # une variante qui casse un calcul est signalée, pas ignorée
                out.append({"cle": nom, "parametre": x.cle, "erreur": str(e)[:120]})
                continue
            out.append({"cle": nom, "parametre": x.cle, "unite": x.unite, "note": x.note,
                        **{f"solde_{t}": v[t][0] - base[t][0] for t in ANNEES_CLES},
                        **{f"deficit_{t}": v[t][1] - base[t][1] for t in ANNEES_CLES}})
    return sorted(out, key=lambda r: -abs(r.get("deficit_2037", 0)))


if __name__ == "__main__":
    import json
    from pathlib import Path
    sortie = Path(__file__).resolve().parent.parent / "sorties" / "sensibilite.json"
    sortie.parent.mkdir(exist_ok=True)
    res = sensibilites()
    sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Écrit : {sortie} ({len(res)} variantes)")
