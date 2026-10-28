"""Coût de la transition des retraites, 2029-2073 (feuilles Socle actuariel, Coût transition, Pénibilité).

Coût de transition(t) = dépenses de l'ancien système × part restante + socle des retraités du nouveau
système + remboursement de 35 % au sens de Maastricht − retraites inscrites au budget (220 Md€)
− économie sur les hautes pensions + surcoût de la pénibilité.
"""
from __future__ import annotations

import csv
import math

from .distribution import DONNEES
from .epargne import capital_par_euro_de_rente, revenu_par_euro_de_capital
from .impot_unique import impot
from .parametres import Parametres

ANNEES = list(range(2029, 2074))


def _csv(nom):
    with (DONNEES / nom).open(encoding="utf-8") as f:
        return [{k: float(v) for k, v in l.items()} for l in csv.DictReader(f)]


def survie(p: Parametres, age_depart: float, age: float) -> float:
    a, b = p.val("epargne.gompertz_a"), p.val("epargne.gompertz_b")
    return math.exp(-a / b * (math.exp(b * age) - math.exp(b * age_depart)))


def taux_epargne_net(net_mensuel: float, p: Parametres) -> float:
    """Taux d'épargne par profil, sur le net mensuel (seuils = nets du SMIC et de 2 SMIC dans le nouveau système)."""
    smic = p.val("epargne.cout_smic_mensuel")
    k = p.val("epargne.multiple_smic_taux_plein")
    bas = smic - impot(smic * 12, p) / 12
    haut = k * smic - impot(k * smic * 12, p) / 12
    taux = p.val("epargne.taux_plein") * (1 - p.val("epargne.contribution_transition"))
    return taux * min(1.0, max(0.0, (net_mensuel / 12 - bas) / (haut - bas)))


def socle_par_generation(p: Parametres) -> list[dict]:
    """Socle annuel moyen (5 quintiles) de chaque génération (Socle actuariel, colonnes E à L)."""
    r = p.val("epargne.rendement_fonds")
    rev = revenu_par_euro_de_capital(p)
    emploi = p.val("epargne.taux_emploi_carriere")
    socle, seuil = p.val("retraites.socle_plein") * 12, p.val("retraites.rente_annulant_socle") * 12
    ratio = p.val("transition.taux_remboursement") / p.val("transition.taux_implicite_fichier_source")
    out = []
    for c in _csv("cohortes_2029.csv"):
        annees = p.val("epargne.age_acces_socle") - max(c["age_2029"], p.val("transition.age_debut_carriere"))
        f = ((1 + r) ** annees - 1) / r
        socles = []
        for s in p.val("transition.salaires_quintiles"):
            capital = taux_epargne_net(s, p) * s * emploi * f + c["remboursement_par_actif"] * ratio * emploi
            socles.append(socle * max(0.0, 1 - capital * rev / seuil))
        out.append({**c, "socle_moyen": sum(socles) / len(socles), "socles": socles})
    return out


def cout_socle(p: Parametres) -> dict[int, float]:
    """Socle versé aux retraités du nouveau système vivants (Md€), par année."""
    gens = socle_par_generation(p)
    acces = p.val("epargne.age_acces_socle")
    out = {}
    for an in ANNEES:
        total = 0.0
        for g in gens:
            age = g["age_2029"] + (an - 2029)
            if age >= acces:
                total += g["population_2026"] * survie(p, g["age_2029"], age) * g["socle_moyen"]
        out[an] = total / 1e9
    return out


def retraites_nouveau_systeme(p: Parametres) -> dict[int, float]:
    acces = p.val("epargne.age_acces_socle")
    return {an: sum(g["population_2026"] * survie(p, g["age_2029"], g["age_2029"] + an - 2029)
                    for g in _csv("cohortes_2029.csv") if g["age_2029"] + an - 2029 >= acces) for an in ANNEES}


def remboursements(p: Parametres) -> dict[int, dict]:
    """Remboursement de 35 % crédité au départ en retraite, payé d'abord en participations de l'État."""
    ratio = p.val("transition.taux_remboursement") / p.val("transition.taux_implicite_fichier_source")
    emploi = p.val("epargne.taux_emploi_carriere")
    gens = {g["age_2029"]: g for g in _csv("cohortes_2029.csv")}
    plafond = p.val("transition.participations_etat") * (1 - p.val("transition.decote_participations"))
    cumul, out = 0.0, {}
    for an in ANNEES:
        age = p.val("epargne.age_acces_socle") - (an - 2029)
        g = gens.get(age)
        du = g["population_2026"] * g["remboursement_par_actif"] * ratio * emploi / 1e9 if g else 0.0
        participations = min(du, plafond - cumul)
        cumul += participations
        maastricht = p.val("transition.rendement_dividendes_perdu") * cumul + du
        out[an] = {"du": du, "participations": participations, "cumul": cumul, "maastricht": maastricht}
    return out


def economie_hautes_pensions_2026(p: Parametres) -> float:
    h = p.val("transition.hautes_pensions")
    return (h["retraites_millions"] * 1e6 * (h["part_3000"] * h["seuil_1"] / (h["pareto"] - 1) * h["taux_1"]
            + h["part_5000"] * h["seuil_2"] / (h["pareto"] - 1) * h["taux_2"]) * 12 / 1e9)


def penibilite(p: Parametres) -> dict[int, float]:
    gens = socle_par_generation(p)
    acces, avance = p.val("epargne.age_acces_socle"), p.val("penibilite.avance_annees")
    part = p.val("penibilite.part_concernes")
    socle_modeste = sum(gens[0]["socles"][:2]) / 2 / 12
    nouveaux = retraites_nouveau_systeme(p)
    out = {}
    for an in ANNEES:
        dans_avance = sum(g["population_2026"] * survie(p, g["age_2029"], g["age_2029"] + an - 2029)
                          for g in gens if acces - avance <= g["age_2029"] + an - 2029 < acces)
        out[an] = (dans_avance * part * socle_modeste * 12 + nouveaux[an] * part * p.val("penibilite.hausse_socle_mensuelle") * 12) / 1e9
    return out


def cout_transition(p: Parametres) -> dict[int, dict]:
    anc = {int(l["annee"]): l for l in _csv("ancien_systeme_retraites.csv")}
    socle = cout_socle(p)
    remb = remboursements(p)
    pen = penibilite(p)
    hp = economie_hautes_pensions_2026(p)
    budget = p.val("budget_statique.retraites_socle")
    base85 = anc[2029]["depenses_desindexees_md"]
    out = {}
    for an in ANNEES:
        ancien = anc[an]["depenses_desindexees_md"] * anc[an]["part_ancien_systeme"]
        actuariel = ancien + socle[an] + remb[an]["maastricht"] - budget
        hautes = hp * anc[an]["part_ancien_systeme"] * anc[an]["depenses_desindexees_md"] / base85
        out[an] = {"actuariel": actuariel, "hautes_pensions": hautes, "penibilite": pen[an],
                   "net": actuariel - hautes + pen[an], "participations": remb[an]["participations"]}
    return out


def cout_transition_moyen(p: Parametres) -> float:
    c = cout_transition(p)
    return sum(v["net"] for v in c.values()) / len(c)
