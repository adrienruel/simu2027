"""Population année par année (projections de l'Insee de juin 2026), commune à tous les programmes.

- population par âge (0 à 105 ans et plus), de 2026 à 2073 (l'Insee s'arrête en 2070 : 2071-2073 prolongés par la
  variation moyenne de 2066-2070) ;
- taux d'emploi par âge (2025, puis la projection de l'Insee des taux d'activité) ;
- écart de population dû à une variation des naissances (`ecart_naissances`), utilisé par le canal commun des
  naissances (moteur/naissances.py) : interpolation entre les scénarios central et fécondité haute de l'Insee.
"""
from __future__ import annotations

import csv
from functools import lru_cache

from .distribution import DONNEES
from .parametres import Parametres

ANNEES = list(range(2026, 2074))
AGE_MAX = 105
PARTS_RANG = {1: 0.44, 2: 0.35, 3: 0.21}  # rang 1 : Insee (2012) ; rangs 2 et 3+ : HYPOTHÈSE
POIDS_MENAGES = {"parent_isole_smic": 0.2}  # le reste réparti également entre les couples types (HYPOTHÈSE)


@lru_cache(maxsize=None)
def _projection(nom: str) -> dict[int, tuple[float, ...]]:
    """Population par âge (deux sexes) d'un scénario de l'Insee, prolongée jusqu'en 2073."""
    pop: dict[int, list[float]] = {}
    with (DONNEES / f"population_insee_2026_{nom}.csv").open(encoding="utf-8") as f:
        for l in csv.DictReader(f):
            t, a = int(l["annee"]), min(AGE_MAX, int(l["age"]))
            pop.setdefault(t, [0.0] * (AGE_MAX + 1))[a] += float(l["population"])
    derniere = max(pop)
    for t in range(derniere + 1, ANNEES[-1] + 1):
        pop[t] = [pop[t - 1][a] * ((pop[derniere][a] / pop[derniere - 5][a]) ** 0.2 if pop[derniere - 5][a] > 0 else 1.0)
                  for a in range(AGE_MAX + 1)]
    return {t: tuple(v) for t, v in pop.items() if t in ANNEES}


COUPLES = {"deux_smic": ["smic", "smic"], "smic_median": ["smic", "median"], "deux_medians": ["median", "median"],
           "cadre_median": [100000, "median"], "median_inactif": ["median", 0], "parent_isole_smic": ["smic"]}
AGES = [10, 6, 3]  # âges des enfants de rang 1, 2, 3


def population(p: Parametres, jeu: str = "prudent") -> dict[int, tuple[float, ...]]:
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("population", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    base = _projection(p.val("demographie.scenario_fecondite", jeu))
    out = dict(base)
    cache[cle] = out
    return out


def ecart_naissances(p: Parametres, effet: float) -> dict[int, list[float]]:
    """Écart de population par âge et par année dû à une variation relative des naissances (effet, à plein effet),
    en montée sur demographie.natalite_montee années à partir de 2030 : fraction de l'écart entre les projections de
    fécondité haute et centrale de l'Insee (mêmes naissances supplémentaires, puis même survie)."""
    fv = p.val("demographie.fecondite_variantes")
    d_ind = effet * fv["central"] / (fv["fec_haute"] - fv["central"])  # en fraction de l'écart haute − centrale
    haute, centrale = _projection("fec_haute"), _projection("central")
    montee = p.val("demographie.natalite_montee")
    out = {}
    for t, v in centrale.items():
        w = [0.0] * len(v)
        for a in range(0, max(0, t - 2030) + 1):
            k = min(1.0, (t - a - 2030 + 1) / montee)
            w[a] = (haute[t][a] - centrale[t][a]) * d_ind * k
        out[t] = w
    return out


def _tranche(nom: str) -> range:
    if nom.endswith("+"):
        return range(int(nom[:-1]), AGE_MAX + 1)
    a, b = nom.split("-")
    return range(int(a), int(b) + 1)


ANNEE_TAUX_EMPLOI = 2025  # année des taux d'emploi par âge observés (demographie.taux_emploi_age)


def taux_emploi_par_age(p: Parametres, t: int) -> dict[int, float]:
    """Taux d'emploi par âge l'année t (phase P, 19/11/2026) : taux de 2025 (demographie.taux_emploi_age), et pour les
    tranches de la projection de l'Insee (demographie.taux_activite_seniors_projection) le rapport du taux d'activité
    projeté de l'année à celui de 2025 ; interpolation linéaire entre les années de la projection, constant au-delà
    de ses bornes et avant 2025. Taux de 2025 figés si demographie.taux_emploi_tendance est faux (ou absent)."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("taux_emploi_par_age", t)
    if cle in cache:
        return cache[cle]
    base = {a: v for k, v in p.val("demographie.taux_emploi_age").items() for a in _tranche(k)}
    actif = "demographie.taux_emploi_tendance" in p._p and p.val("demographie.taux_emploi_tendance")
    if actif:
        proj = p.val("demographie.taux_activite_seniors_projection")

        def niveau(serie: dict, an: float) -> float:
            ans = sorted(int(x) for x in serie)
            v = {int(x): y for x, y in serie.items()}
            an = min(max(an, ans[0]), ans[-1])
            for a, b in zip(ans, ans[1:]):
                if a <= an <= b:
                    return v[a] + (v[b] - v[a]) * (an - a) / (b - a)
            return v[ans[-1]]
        for tranche, serie in proj.items():
            k = niveau(serie, max(t, ANNEE_TAUX_EMPLOI)) / niveau(serie, ANNEE_TAUX_EMPLOI)
            for a in _tranche(tranche):
                base[a] = base.get(a, 0.0) * k
    cache[cle] = base
    return base


