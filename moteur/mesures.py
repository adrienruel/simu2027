"""Registre des mesures datées : montée en charge linéaire, puis indexation (feuille Économies).

Chaque mesure : interrupteur, montant à plein effet (Md€ de 2026), première année, année de plein effet,
indexation après le plein effet (« pib » : croissance tendancielle ; « ancien_systeme » : dépenses de
l'ancien système de retraite, pour les mesures qui portent sur les pensions).
C'est le premier embryon du registre des lois de l'architecture année par année.

Règle de sourçage (décision d'Adrien, 05/11/2026), commune à tous les programmes : une économie saisie comme un
montant (nature « montant ») n'est retenue que si elle cite au moins economies.sources_minimum sources
indépendantes (colonne « sources », séparées par « ; »), dont aucune n'est le programme ou une déclaration d'un
candidat ou d'un parti. Sinon elle compte pour zéro et est publiée comme écartée. Une économie retenue est
multipliée par le taux de réalisation du scénario (economies.taux_realisation). Une mesure dont le montant est
calculé par le moteur à partir de règles (nature « calcul_moteur ») n'est pas un montant saisi : ses paramètres
suivent la règle générale des sources.
"""
from __future__ import annotations

import csv

from .parametres import PROGRAMME_DEFAUT, Parametres, dossier_programme

ANNEES = list(range(2029, 2074))


# Repérage des sources déclaratives (« programme de stabilité » ou « loi de programmation » restent des sources)
MOTS_DECLARATIFS = ("programme du candidat", "programme de la candidate", "programme électoral", "programme présidentiel",
                    "candidat", "candidate", "porte-parole", "profession de foi", "meeting", "tract",
                    "site de campagne", "chiffrage du parti", "chiffrage de la campagne")


def sources(m: dict) -> list[str]:
    return [x.strip() for x in (m.get("sources") or "").split(";") if x.strip()]


def motif_ecartee(m: dict, p: Parametres | None = None) -> str | None:
    """Raison pour laquelle une économie saisie n'est pas retenue (None si elle l'est).

    Natures : « montant » (montant unique recoupé par economies.sources_minimum sources, × taux de réalisation) ;
    « estimation » (pas de chiffrage recoupé : estimation propre par scénario, colonnes estimation_<scénario>, avec sa
    méthode et au moins une source pour ses bases ; le taux de réalisation est déjà dans l'estimation, décision
    d'Adrien du 05/11/2026) ; « calcul_moteur » (montant calculé par le moteur)."""
    nature = m.get("nature") or "montant"
    if nature == "calcul_moteur" or (p is not None and not p.val("economies.estimations")):
        return None  # v235 : montants saisis, sans règle de sources
    if nature == "estimation":
        src = sources(m)
        if any(any(k in x.lower() for k in MOTS_DECLARATIFS) for x in src):
            return "source déclarative (programme ou candidat)"
        if not src or not (m.get("methode") or "").strip():
            return "estimation sans méthode ou sans source pour ses bases"
        if any((m.get(f"estimation_{s}") or "").strip() == "" for s in ("crise", "prudent", "median", "optimiste")):
            return "estimation incomplète (une valeur par scénario)"
        return None
    minimum = p.val("economies.sources_minimum") if p is not None else 2
    src = sources(m)
    declaratives = [x for x in src if any(k in x.lower() for k in MOTS_DECLARATIFS)]
    if declaratives:
        return f"source déclarative (programme ou candidat) : {declaratives[0]}"
    if len(src) < minimum:
        return f"{len(src)} source(s) indépendante(s) sur {minimum} exigées"
    return None


def registre(programme: str | None = PROGRAMME_DEFAUT) -> list[dict]:
    """Mesures datées du programme (programmes/<programme>/mesures_economies.csv) ; aucune sans programme."""
    if programme is None:
        return []
    with (dossier_programme(programme) / "mesures_economies.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ecartees(p: Parametres) -> list[dict]:
    """Économies saisies non retenues, avec leur motif (pour la restitution)."""
    return [{"mesure": m["mesure"], "plein_effet_md": float(m["plein_effet_md"] or 0), "motif": motif_ecartee(m, p)}
            for m in registre(p.programme) if float(m["retenue"] or 0) and motif_ecartee(m, p)]


def plein_effet(m: dict, p: Parametres, scenario: str = "prudent") -> float:
    """Montant à plein effet retenu (Md€ de 2026) : estimation du scénario, ou montant × taux de réalisation."""
    nature = m.get("nature") or "montant"
    if not p.val("economies.estimations"):  # v235 : montant saisi, réalisé en entier
        return float(m["plein_effet_md"])
    if nature == "estimation":
        # calcul de crise : colonne prudente = crise ; « depart » : colonne prudente même dans le calcul de crise
        s = "prudent" if scenario == "depart" else (p.colonne_prudent if scenario == "prudent" else scenario)
        return float(m[f"estimation_{s}"])
    realisation = 1.0 if nature == "calcul_moteur" else p.val("economies.taux_realisation", scenario)  # « depart » : prudent
    return float(m["plein_effet_md"]) * realisation


def effet(m: dict, t: int, p: Parametres, ancien: dict[int, float], scenario: str = "prudent") -> float:
    if m["mesure"] in p.mesures_desactivees:
        return 0.0
    if m["mesure"].startswith("Ancien système : âge de départ porté"):
        from .ancien_systeme import economie_age_legal
        e = economie_age_legal(p)
        if e is not None:  # calculée génération par génération (module de population)
            return float(m["retenue"]) * e[t]
    debut, plein = int(m["premiere_annee"]), int(m["annee_plein_effet"])
    montee = min(1.0, max(0.0, (t - debut + 1) / (plein - debut + 1)))
    if m["indexation"] == "pib":
        index = (1 + p.val("macro.tendance", "prudent")) ** (t - plein)
    else:
        index = ancien[t] / ancien[max(2029, plein)]
    if motif_ecartee(m, p):
        return 0.0
    if not p.val("economies.estimations") and not (m.get("decision") or "v").startswith("v"):
        return 0.0  # v235 : mesure ajoutée après la v235 (décision datée, pas une version du classeur)
    if t <= 2029 and p.val("macro.depart_commun"):
        scenario = "depart"  # option du point de départ commun : 2029 aux hypothèses prudentes
    return float(m["retenue"]) * plein_effet(m, p, scenario) * montee * index


def ecart_scenario(p: Parametres, s: str) -> dict[int, float]:
    """Économies du registre dans le scénario s moins celles du prudent (Md€, + = plus d'économies) : le moteur du
    programme calcule ses lignes au prudent, cet écart passe au solde du médian et de l'optimiste (moteur/macro.py)."""
    from .ancien_systeme import depenses as depenses_ancien
    anc = depenses_ancien(p)
    reg = registre(p.programme)
    return {t: sum(effet(m, t, p, anc, s) - effet(m, t, p, anc) for m in reg) for t in ANNEES}


def economies(p: Parametres) -> dict[int, float]:
    from .ancien_systeme import depenses as depenses_ancien
    anc = depenses_ancien(p)
    reg = registre(p.programme)
    return {t: sum(effet(m, t, p, anc) for m in reg) for t in ANNEES}


def economies_par_mesure(p: Parametres) -> dict[str, dict[int, float]]:
    """Économie de chaque mesure du registre, année par année (Md€, positif = économie)."""
    from .ancien_systeme import depenses as depenses_ancien
    anc = depenses_ancien(p)
    out: dict[str, dict[int, float]] = {}
    for m in registre(p.programme):
        d = out.setdefault(m["mesure"], {t: 0.0 for t in ANNEES})
        for t in ANNEES:
            d[t] += effet(m, t, p, anc)
    return out
