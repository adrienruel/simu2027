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

import csv

from .distribution import DONNEES
from .parametres import Parametres

ANNEES = list(range(2029, 2074))
DERNIERE_GENERATION = 1979  # 50 ans en 2029 ; les générations du nouveau système ont 22 à 49 ans en 2029 (cohortes_2029.csv)


_V235: dict = {}


def _csv_v235() -> dict[int, dict]:
    if not _V235:
        with (DONNEES / "ancien_systeme_retraites.csv").open(encoding="utf-8") as f:
            _V235.update({int(l["annee"]): {k: float(v) for k, v in l.items()} for l in csv.DictReader(f)})
    return {a: dict(l) for a, l in _V235.items()}


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


def _report(p: Parametres, g: int) -> float:
    """Années de report de l'âge légal pour la génération g (mesure du programme : de 64 ans à ancien_systeme.age_legal["programme"])."""
    a = p.val("ancien_systeme.age_legal")
    annees = a["programme"] - a["actuel"]
    # deux trimestres de plus par génération : la génération qui a 64 ans en 2029 part à 64 ans et demi
    return min(annees, max(0.0, (g + a["actuel"] - a["premiere_annee"] + 1) * a["pas_par_generation"]))


def _part(r: dict[int, float], b: int, report: float, age_legal: int) -> float:
    """Part de la génération partie à l'âge b, profil décalé de « report » années à partir de l'âge légal."""
    if b < age_legal or report <= 0:
        return r[b]
    x = b - report
    lo = int(x // 1)
    return r[max(lo, age_legal - 1)] + (r[lo + 1] - r[lo]) * (x - lo) if lo >= age_legal - 1 else r[age_legal - 1]


def _brut(p: Parametres, avec_report: bool) -> dict[int, dict[str, float]]:
    from .demographie import _projection
    pop = _projection("central")
    from .inflation import facteur_prix
    nouveau = p.val("ancien_systeme.pension_nouveaux_relative")
    r = _part_age(p)
    geles = p.val("ancien_systeme.droits_geles_des_2029")
    age_legal = p.val("ancien_systeme.age_legal")["actuel"]
    brut = {}
    for t in ANNEES:
        dep = eff = 0.0
        for a in range(t - DERNIERE_GENERATION, 106):
            g = t - a
            n = pop[t][a]
            rep = _report(p, g) if avec_report else 0.0
            # parts de la génération parties chaque année d'âge, chacune gelée depuis son départ
            for b in range(50, a + 1):
                d = _part(r, b, rep, age_legal) - _part(r, b - 1, rep, age_legal)
                if d <= 0:
                    continue
                depart = g + b
                niveau = 1.0 if depart < 2029 else nouveau
                gel = 2029 if geles else max(2029, depart)
                dep += n * d * niveau / facteur_prix(p, gel, t)
                eff += n * d
        brut[t] = {"depenses": dep, "retraites": eff}
    return brut


def par_generation(p: Parametres, avec_report: bool = False) -> dict[int, dict[str, float]]:
    """Série calée sur 2029 ; avec_report : âge légal reporté (mesure du programme, ancien_systeme.age_legal)."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("ancien_brut", False) not in cache:
        cache[("ancien_brut", False)] = _brut(p, False)
    if avec_report and ("ancien_brut", True) not in cache:
        cache[("ancien_brut", True)] = _brut(p, True)
    base, brut = cache[("ancien_brut", False)], cache[("ancien_brut", avec_report)]
    v = _csv_v235()
    k = v[2029]["depenses_desindexees_md"] * v[2029]["part_ancien_systeme"] / base[2029]["depenses"]
    # effectif calé sur les retraités du COR en 2029 (résidents à l'étranger et pensions de réversion seules compris)
    kn = p.val("anciennes_pensions.retraites_ancien_2029_millions")[0] * 1e6 / base[2029]["retraites"]
    return {t: {"depenses_md": brut[t]["depenses"] * k, "retraites_millions": brut[t]["retraites"] * kn / 1e6} for t in ANNEES}


def economie_age_legal(p: Parametres) -> dict[int, float] | None:
    """Économie du report de l'âge légal sur les pensions (Md€), ou None hors module par génération."""
    if not (p.val("ancien_systeme.par_generation") and p.val("demographie.active")):
        return None
    sans, avec = par_generation(p), par_generation(p, avec_report=True)
    return {t: sans[t]["depenses_md"] - avec[t]["depenses_md"] for t in ANNEES}


def serie(p: Parametres) -> dict[int, dict[str, float]]:
    """Dépenses de l'ancien système (Md€ de 2026) et nombre de ses retraités (millions), par année."""
    cache = p.__dict__.setdefault("_cache", {})
    if "ancien_systeme" in cache:
        return cache["ancien_systeme"]
    if p.val("ancien_systeme.par_generation") and p.val("demographie.active"):
        out = par_generation(p)
    else:
        v = _csv_v235()
        cor = dict(zip(ANNEES, p.val("anciennes_pensions.retraites_ancien_2029_millions")))
        out = {t: {"depenses_md": v[t]["depenses_desindexees_md"] * v[t]["part_ancien_systeme"],
                   "retraites_millions": cor[t] * v[t]["part_ancien_systeme"]} for t in ANNEES}
    cache["ancien_systeme"] = out
    return out


def depenses(p: Parametres) -> dict[int, float]:
    return {t: x["depenses_md"] for t, x in serie(p).items()}


def retraites_reportes(p: Parametres) -> dict[int, float]:
    """Personnes dont le départ dans l'ancien système est reporté par le report de l'âge légal (millions)."""
    if not (p.val("ancien_systeme.par_generation") and p.val("demographie.active")):
        return {t: 0.0 for t in ANNEES}
    sans, avec = par_generation(p), par_generation(p, avec_report=True)
    return {t: max(0.0, sans[t]["retraites_millions"] - avec[t]["retraites_millions"]) for t in ANNEES}


def contribution_solidarite(p: Parametres) -> dict[int, float]:
    """Contribution progressive des retraités de l'ancien système (Md€, avant fuite), par année."""
    c = p.val("ancien_systeme.contribution_solidarite")
    if c["taux_haut"] <= 0 and c["taux_bas"] <= 0:
        return {t: 0.0 for t in ANNEES}
    deciles = p.val("anciennes_pensions.deciles_drees_2020")
    moy = sum(deciles) / len(deciles)
    def taux(x, k_=1.0):
        sb, sh = c["seuil_bas"] * k_, c["seuil_haut"] * k_
        if x <= sb:
            return 0.0
        if x >= sh:
            return c["taux_haut"]
        return c["taux_bas"] + (c["taux_haut"] - c["taux_bas"]) * (x - sb) / (sh - sb)
    from .inflation import indice_reel
    idx = indice_reel(p)
    out = {}
    for t, x in serie(p).items():
        k_ = idx.get(t, 1.0)  # seuils revalorisés comme le RUI (règle d'indexation)
        if t < c["debut"] or x["retraites_millions"] <= 0:
            out[t] = 0.0
            continue
        moyenne = x["depenses_md"] * 1e9 / (x["retraites_millions"] * 1e6) / 12
        pensions = [d * moyenne / moy for d in deciles]
        effectif = sum(taux(v, k_) * v for v in pensions) / sum(pensions)
        out[t] = effectif * x["depenses_md"]
    return out
