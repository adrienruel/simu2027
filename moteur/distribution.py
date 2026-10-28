"""Distributions de salaires par classe et passage en euros de 2026.

Reproduit la feuille « Passage en euros de 2026 » de la v235 : chaque classe d'origine
est relevée par le facteur de salaire, puis son effectif est réparti entre les deux
classes de 2026 qui l'encadrent, par interpolation sur le logarithme du salaire.
Les effectifs sont conservés ; sous la première classe ou au-delà de la dernière,
tout reste dans la classe extrême.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

DONNEES = Path(__file__).resolve().parent.parent / "parametres" / "donnees"


@dataclass(frozen=True)
class Distribution:
    classes: list[str]
    milieux: list[float]      # coût employeur annuel du milieu de classe (euros de 2026)
    effectifs: list[float]


def lire(nom: str) -> Distribution:
    with (DONNEES / nom).open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    return Distribution(
        [l["classe"] for l in lignes],
        [float(l["cout_employeur_milieu"]) for l in lignes],
        [float(l["effectif_origine"]) for l in lignes],
    )


def repartir(salaire: float, milieux: list[float]) -> list[float]:
    """Parts d'un salarié de salaire donné dans chaque classe (somme = 1)."""
    n = len(milieux)
    parts = [0.0] * n
    if salaire <= milieux[0]:
        parts[0] = 1.0
        return parts
    if salaire >= milieux[-1]:
        parts[-1] = 1.0
        return parts
    for j in range(n - 1):
        bas, haut = milieux[j], milieux[j + 1]
        if bas < salaire <= haut:
            w = (math.log(salaire) - math.log(bas)) / (math.log(haut) - math.log(bas))
            parts[j], parts[j + 1] = 1 - w, w
            return parts
    raise AssertionError("salaire hors des bornes")


def passer_en_2026(d: Distribution, facteur: float) -> Distribution:
    """Effectifs de 2026 par classe, les milieux de classe étant pris en euros de 2026."""
    eff = [0.0] * len(d.milieux)
    for milieu, n in zip(d.milieux, d.effectifs):
        for j, part in enumerate(repartir(milieu * facteur, d.milieux)):
            eff[j] += n * part
    return Distribution(d.classes, d.milieux, eff)
