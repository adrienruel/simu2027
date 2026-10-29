"""Registre des mesures datées : montée en charge linéaire, puis indexation (feuille Économies).

Chaque mesure : interrupteur, montant à plein effet (Md€ de 2026), première année, année de plein effet,
indexation après le plein effet (« pib » : croissance tendancielle ; « ancien_systeme » : dépenses de
l'ancien système de retraite, pour les mesures qui portent sur les pensions).
C'est le premier embryon du registre des lois de l'architecture année par année.
"""
from __future__ import annotations

import csv

from .distribution import DONNEES
from .parametres import Parametres
from .retraites_transition import _csv as _csv_retraites

ANNEES = list(range(2029, 2074))


def registre() -> list[dict]:
    with (DONNEES / "mesures_economies.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def effet(m: dict, t: int, p: Parametres, ancien: dict[int, float]) -> float:
    debut, plein = int(m["premiere_annee"]), int(m["annee_plein_effet"])
    montee = min(1.0, max(0.0, (t - debut + 1) / (plein - debut + 1)))
    if m["indexation"] == "pib":
        index = (1 + p.val("macro.tendance", "prudent")) ** (t - plein)
    else:
        index = ancien[t] / ancien[max(2029, plein)]
    return float(m["retenue"]) * float(m["plein_effet_md"]) * montee * index


def economies(p: Parametres) -> dict[int, float]:
    anc = {int(x["annee"]): x["depenses_desindexees_md"] * x["part_ancien_systeme"] for x in _csv_retraites("ancien_systeme_retraites.csv")}
    reg = registre()
    return {t: sum(effet(m, t, p, anc) for m in reg) for t in ANNEES}


def economies_par_mesure(p: Parametres) -> dict[str, dict[int, float]]:
    """Économie de chaque mesure du registre, année par année (Md€, positif = économie)."""
    anc = {int(x["annee"]): x["depenses_desindexees_md"] * x["part_ancien_systeme"] for x in _csv_retraites("ancien_systeme_retraites.csv")}
    out: dict[str, dict[int, float]] = {}
    for m in registre():
        d = out.setdefault(m["mesure"], {t: 0.0 for t in ANNEES})
        for t in ANNEES:
            d[t] += effet(m, t, p, anc)
    return out
