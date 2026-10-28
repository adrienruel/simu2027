"""Restitution : les résultats d'une simulation mis en forme pour le tableau de bord (JSON).

    from moteur.restitution import donnees
    d = donnees()          # dictionnaire sérialisable
"""
from __future__ import annotations

import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

from .parametres import Parametres
from .simulation import ORDRE, simuler

RACINE = Path(__file__).resolve().parent.parent

LIBELLES_CANAUX = {
    "emploi": "Emplois créés (RUI économisé, impôt, TVA)",
    "ajustement_budgetaire": "Ajustement budgétaire (multiplicateur)",
    "capital_du_fonds": "Capital du fonds souverain",
    "logement": "Logement",
    "erosion_is": "Érosion de l'assiette de l'IS",
    "fraude_tva": "Fraude à la TVA récupérée",
    "fin_aides_construction": "Fin des aides à la construction",
    "productivite": "Productivité",
    "reactions_impot": "Réactions à l'impôt",
    "ia": "Intelligence artificielle",
    "tendance_et_ecole": "Croissance tendancielle et école",
    "investissement_entreprises": "Investissement des entreprises",
    "sante": "Santé (écart au prudent, TVA santé)",
    "carbone": "Carbone",
    "eviction_epargne": "Éviction de l'épargne volontaire",
    "clause": "Clause de trajectoire",
}

POSTES = [("recettes", "Recettes"), ("sante", "Santé"), ("retraites", "Retraites"), ("rui_aah", "RUI et AAH"),
          ("investissement", "Investissement"), ("autres", "Autres dépenses"), ("charge_dette", "Charge de la dette (réelle)"),
          ("solde", "Solde public")]


def _version() -> str:
    try:
        return subprocess.run(["git", "describe", "--always", "--dirty"], cwd=RACINE, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "inconnue"


def _r(x: float, n: int = 4) -> float:
    return round(float(x), n)


def donnees(p: Parametres | None = None) -> dict:
    p = p or Parametres()
    res = simuler(p)
    annees = sorted(res["prudent"])
    scen = [s for s in ORDRE if s in res]
    series = {}
    for s in scen:
        b = res[s]
        series[s] = {
            "deficit": [_r(b[t]["deficit"]) for t in annees],
            "dette_pib": [_r(b[t]["dette_pib"], 3) for t in annees],
            "chomage": [_r(b[t]["chomage"]) for t in annees],
            "pib": [_r(b[t]["pib"], 2) for t in annees],
            "emplois": [round(b[t]["emplois_supplementaires"]) for t in annees],
            "postes": {k: [_r(b[t][k], 3) for t in annees] for k, _ in POSTES},
            "canaux": {k: [_r(b[t]["canaux"][k], 3) for t in annees] for k in LIBELLES_CANAUX},
        }
        if "deficit_avant_clause" in b[annees[0]]:
            series[s]["deficit_avant_clause"] = [_r(b[t]["deficit_avant_clause"]) for t in annees]
            series[s]["clause"] = {k: [_r(b[t]["clause_detail"][k], 3) for t in annees]
                                   for k in ("etalement", "contribution", "points", "rui", "rui_euros", "reste")}
    statuts = Counter(x.statut for x in p)
    hypotheses = sorted((x.cle for x in p if x.statut == "HYPOTHESE"))
    groupes = Counter(c.split(".")[0] for c in hypotheses)
    return {
        "meta": {"version": _version(), "date": date.today().isoformat(), "euros": "euros constants de 2026",
                 "scenario_publie": "prudent", "chomage_jusqu_a": 2040},
        "annees": annees,
        "scenarios": scen,
        "series": series,
        "libelles_canaux": LIBELLES_CANAUX,
        "postes": POSTES,
        "parametres": {"total": sum(statuts.values()), "statuts": dict(statuts),
                       "hypotheses_par_groupe": groupes.most_common()},
    }
