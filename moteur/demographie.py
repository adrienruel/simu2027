"""Population année par année (projections de l'Insee de juin 2026) et effet du programme sur la natalité.

Ce que le module fournit, pour chaque jeu de paramètres (crise, prudent, médian, optimiste) :
- la population par âge (0 à 105 ans et plus), de 2026 à 2073 (l'Insee s'arrête en 2070 : 2071-2073 prolongés
  par la variation moyenne de 2066-2070) ;
- des indices rapportés à 2029, qui font évoluer les postes du budget :
  * emploi : population par âge × taux d'emploi par âge de 2025 (taux figés : la démographie seule) ;
  * adultes : 18-64 ans (RUI des actifs, des chômeurs, des inactifs, des étudiants) ;
  * enfants : 0-17 ans (compléments de RUI par enfant) ;
  * total : toute la population (autres dépenses publiques) ;
  * seniors : 65 ans ou plus (pour la restitution).

Effet du programme sur la natalité : le soutien par enfant change (outils/valeur_enfant.py : OpenFisca pour le
système actuel, moteur pour le nouveau). Variation relative des naissances = semi-élasticité × écart moyen de
soutien (pour 100 € par an) + effet des crèches. Elle s'applique aux générations nées à partir de 2030, avec une
montée en charge, en interpolant entre les scénarios central et fécondité haute de l'Insee (qui ne diffèrent que
par la fécondité) : population(âge, t) += (haute − centrale)(âge, t) × Δ indicateur / (1,70 − 1,45).
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


def ecart_soutien_enfant(p: Parametres) -> float:
    """Écart moyen de soutien par enfant, nouveau système − système actuel (€ par an), pondéré par rang et ménage."""
    with (DONNEES / "valeur_enfant_2026.csv").open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    menages = sorted({l["menage"] for l in lignes})
    reste = 1 - sum(POIDS_MENAGES.values())
    autres = [m for m in menages if m not in POIDS_MENAGES]
    poids = {m: POIDS_MENAGES.get(m, reste / len(autres)) for m in menages}
    return sum(poids[l["menage"]] * PARTS_RANG[int(l["rang"])] * (float(l["nouveau"]) - float(l["actuel"])) for l in lignes)


def effet_naissances(p: Parametres, jeu: str = "prudent") -> float:
    """Variation relative des naissances due au programme (à plein effet)."""
    return (p.val("demographie.natalite_semi_elasticite", jeu) * ecart_soutien_enfant(p) / 100
            + p.val("demographie.creches_effet"))


def population(p: Parametres, jeu: str = "prudent") -> dict[int, tuple[float, ...]]:
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("population", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    base = _projection(p.val("demographie.scenario_fecondite", jeu))
    out = dict(base)
    effet = effet_naissances(p, jeu)
    if effet:
        fv = p.val("demographie.fecondite_variantes")
        d_ind = effet * fv["central"] / (fv["fec_haute"] - fv["central"])  # en fraction de l'écart haute − centrale
        haute, centrale = _projection("fec_haute"), _projection("central")
        montee = p.val("demographie.natalite_montee")
        out = {}
        for t, v in base.items():
            w = list(v)
            for a in range(0, max(0, t - 2030) + 1):
                naissance = t - a
                k = min(1.0, (naissance - 2030 + 1) / montee)
                w[a] += (haute[t][a] - centrale[t][a]) * d_ind * k
            out[t] = tuple(w)
    cache[cle] = out
    return out


def _tranche(nom: str) -> range:
    if nom.endswith("+"):
        return range(int(nom[:-1]), AGE_MAX + 1)
    a, b = nom.split("-")
    return range(int(a), int(b) + 1)


def effectifs(p: Parametres, jeu: str = "prudent") -> dict[int, dict[str, float]]:
    """Effectifs par grand groupe et emploi (personnes), par année."""
    taux = {a: v for k, v in p.val("demographie.taux_emploi_age").items() for a in _tranche(k)}
    out = {}
    for t, v in population(p, jeu).items():
        out[t] = {"emploi": sum(v[a] * taux.get(a, 0.0) for a in range(AGE_MAX + 1)),
                  "adultes": sum(v[18:65]), "enfants": sum(v[0:18]), "total": sum(v),
                  "seniors": sum(v[65:]), "moins_de_3_ans": sum(v[0:3])}
    return out


def indices(p: Parametres, jeu: str = "prudent") -> dict[int, dict[str, float]]:
    """Effectifs rapportés à 2029 (1 partout si le module est désactivé)."""
    groupes = ("emploi", "adultes", "enfants", "total", "seniors", "moins_de_3_ans")
    if not p.val("demographie.active"):
        return {t: {g: 1.0 for g in groupes} for t in ANNEES}
    e = effectifs(p, jeu)
    return {t: {g: e[t][g] / e[2029][g] for g in groupes} for t in ANNEES}
