"""Lutte contre la fraude : barème commun (phase B5 de la roadmap, 12/11/2026, nuit).

Un programme qui renforce le contrôle fiscal ou douanier déclare les agents de contrôle en plus (équivalents temps
plein), son début et son plein effet (`<nom>_canaux.fraude`, ou `macro.fraude_controle` pour Écologie de droite).
Recettes en plus = agents × montant moyen recouvré par agent de contrôle (fraude.recouvre_par_agent) × rendement
marginal du scénario (fraude.rendement_marginal), plafonnées (fraude.plafond_part × montants recouvrés de 2024), en
montée de debut à plein, suivant le PIB. Coût des agents ajouté sauf s'il est déjà dans une mesure du programme
(cout_deja_compte). Un renforcement sans chiffre vaut fraude.agents_renforcement_non_chiffre agents.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES
from .parametres import Parametres


def agents(p: Parametres, decl: dict) -> float:
    n = decl.get("agents", "non_chiffre")
    return float(p.val("fraude.agents_renforcement_non_chiffre") if n == "non_chiffre" else n)


def _montee(t: int, debut: int, plein: int) -> float:
    return min(1.0, max(0.0, (t - debut + 1) / (plein - debut + 1)))


def effets(p: Parametres, s: str, decl: dict, annees=ANNEES) -> dict[str, dict[int, float]]:
    """{"recettes": {année: Md€}, "cout": {année: Md€}} (Md€ de 2026 ; coût nul si déjà compté)."""
    c = p.val("fraude.bareme")
    n = agents(p, decl)
    debut, plein = int(decl.get("debut", 2028)), int(decl.get("plein", 2032))
    y = sq.pib(p, s)
    plein_md = min(n * c["recouvre_par_agent"] * c["rendement_marginal"][s] / 1e9,
                   c["plafond_part"] * c["recouvre_2024_md"])
    cout_md = 0.0 if decl.get("cout_deja_compte") else n * c["cout_agent"] / 1e9
    rec, cout = {}, {}
    for t in annees:
        g = y[max(t, 2029)] / y[2029]
        k = _montee(t, debut, plein)
        rec[t] = plein_md * k * g
        cout[t] = cout_md * k * g
    return {"recettes": rec, "cout": cout}
