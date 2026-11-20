"""Pensions de l'ancien système, génération par génération (29 octobre 2026).

Qui reste dans l'ancien système : les générations nées en 1979 ou avant (50 ans ou plus en 2029). Les plus
jeunes (22 à 49 ans en 2029) reçoivent le remboursement de leurs cotisations et relèvent du nouveau système
(feuille Socle actuariel, cohortes_2029.csv).

Pour chaque génération et chaque année :
- survivants : population par âge des projections de l'Insee de juin 2026 (mortalité centrale ; les générations
  nées avant 1979 ne dépendent pas de la fécondité future) ;
- part déjà partie à la retraite à chaque âge (paramètre ancien_systeme.part_retraites_age, âge légal de 64 ans,
  la loi actuelle) ; le report de l'âge légal du programme (ancien_systeme.age_legal, 67 ans) est une mesure, calculée en décalant ce profil d'un an
  (deux trimestres par génération) : economie_age_legal ;
- pension : la même pour tous en 2029 (les nouveaux retraités touchent un peu moins que la moyenne, DREES), puis
  gelée en euros courants dès 2029 ou dès le départ s'il est plus tardif (désindexation) : elle perd l'inflation
  chaque année en euros constants.
Le niveau est calé sur les dépenses de l'ancien système en 2029 (428 Md€, série de la v235 issue du COR) et
l'effectif sur les retraités du COR en 2029 (19,15 millions : résidents à l'étranger et réversions seules
compris) ; le module ne change que leur évolution.

Sans le module (v235) : dépenses désindexées du COR × part des retraités de l'ancien système.
"""
from __future__ import annotations


from .parametres import Parametres

ANNEES = list(range(2029, 2074))
DERNIERE_GENERATION = 1979  # 50 ans en 2029 ; les générations du nouveau système ont 22 à 49 ans en 2029 (cohortes_2029.csv)


_V235: dict = {}


def _part_age(p: Parametres) -> dict[int, float]:
    t = {int(a): v for a, v in p.val("ancien_systeme.part_retraites_age").items()}
    a_max = max(t)
    return {a: (t[a] if a in t else (1.0 if a > a_max else 0.0)) for a in range(0, 106)}


def _complet(t: dict) -> dict[int, float]:
    t = {int(a): v for a, v in t.items()}
    return {a: (t[a] if a in t else (1.0 if a > max(t) else 0.0)) for a in range(0, 106)}


def profil_generation(p: Parametres):
    """Part de la génération g partie à la retraite à l'âge b, au statu quo (loi de 2023 et suspension de la LFSS 2026) :
    profil à 62 ans (part_retraites_62) jusqu'à la génération 1960, profil à 64 ans (part_retraites_age) à partir de
    1969, mélange des deux selon l'âge légal de la génération entre les deux (age_legal_generation). Renvoie
    (part(g, b), age_legal(g))."""
    r64 = _part_age(p)
    r62 = _complet(p.val("ancien_systeme.part_retraites_62"))
    cal = {int(g): v for g, v in p.val("ancien_systeme.age_legal_generation").items()}
    g0, g1 = min(cal), max(cal)
    cache = {}

    def age_legal(g: int) -> float:
        return cal[min(max(g, g0), g1)]

    def profil(g: int) -> dict[int, float]:
        lam = (age_legal(g) - 62.0) / 2.0
        if lam not in cache:
            cache[lam] = {b: (1 - lam) * r62[b] + lam * r64[b] for b in r64}
        return cache[lam]

    def part(g: int, b: int) -> float:
        return profil(g)[b]
    part.profil = profil
    return part, age_legal


def _part(r: dict[int, float], b: int, report: float, age_legal: int) -> float:
    """Part de la génération partie à l'âge b, profil décalé de « report » années à partir de l'âge légal."""
    if b < age_legal or report <= 0:
        return r[b]
    x = b - report
    lo = int(x // 1)
    return r[max(lo, age_legal - 1)] + (r[lo + 1] - r[lo]) * (x - lo) if lo >= age_legal - 1 else r[age_legal - 1]


