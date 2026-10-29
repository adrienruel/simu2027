"""Système actuel calculé par OpenFisca-France, pour une personne seule salariée du privé.

Calcule, sur une grille de salaires bruts, le coût employeur, le net, l'impôt sur le revenu, le RSA, la prime
d'activité, l'aide au logement et le revenu disponible, puis écrit une table que le moteur lit
(parametres/donnees/openfisca_prive_<année>.csv). Le moteur n'a pas besoin d'OpenFisca pour tourner :
seule cette table en vient, et ce script la régénère.

Hypothèses du cas type (à documenter dans le journal) : personne seule, sans enfant, locataire du parc
privé en zone 2, loyer de 550 € par mois ; mêmes revenus les deux années précédentes (les prestations se
calculent sur les revenus passés). Agents publics : fonctionnaires titulaires de chaque versant, primes à
24,6 % du brut (DGAFP, rapport annuel 2025, données 2023), le reste en traitement indiciaire.

    python -m outils.openfisca_actuel            # année 2026
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parent.parent
VARIABLES = ("cout_du_travail", "salaire_net", "impot_revenu_restant_a_payer", "csg", "rsa", "ppa", "aide_logement",
             "revenu_disponible")


def grille_bruts() -> list[float]:
    g = list(np.arange(0, 60000, 500)) + list(np.arange(60000, 200000, 2500)) + list(np.arange(200000, 1_000_000, 25000)) + list(np.arange(1_000_000, 4_000_001, 250000))
    return [float(x) for x in g]


PART_PRIMES_FONCTIONNAIRES = 0.246  # DGAFP, rapport annuel 2025 : primes = 24,6 % du brut des fonctionnaires (2023)
VERSANTS = {"etat_civils": "public_titulaire_etat", "etat_militaires": "public_titulaire_militaire",
            "territoriale": "public_titulaire_territoriale", "hospitaliere": "public_titulaire_hospitaliere"}


def _revenus(categorie: str | None, b: float, annees: list[str]) -> dict:
    """Entrées d'un individu pour un brut annuel b (primes comprises pour un fonctionnaire)."""
    if categorie is None:
        return {"salaire_de_base": {y: b for y in annees}}
    tib = b * (1 - PART_PRIMES_FONCTIONNAIRES)
    return {"traitement_indiciaire_brut": {y: tib for y in annees},
            "primes_fonction_publique": {y: b - tib for y in annees},
            "categorie_salarie": {y: categorie for y in annees}}


def calculer(annee: int = 2026, loyer_mensuel: float = 550.0, zone: str = "zone_2", categorie: str | None = None) -> list[dict]:
    from openfisca_core.simulation_builder import SimulationBuilder
    from openfisca_france import FranceTaxBenefitSystem
    tbs = FranceTaxBenefitSystem()
    bruts = grille_bruts()
    an = str(annee)
    annees = [str(annee - 2), str(annee - 1), an]
    n = len(bruts)
    cas = {
        "individus": {f"i{k}": _revenus(categorie, b, annees) for k, b in enumerate(bruts)},
        "foyers_fiscaux": {f"f{k}": {"declarants": [f"i{k}"]} for k in range(n)},
        "menages": {f"m{k}": {"personne_de_reference": [f"i{k}"],
                              "statut_occupation_logement": {y: "locataire_vide" for y in annees},
                              "loyer": {y: 12 * loyer_mensuel for y in annees},
                              "zone_apl": {y: zone for y in annees}} for k in range(n)},
        "familles": {f"fa{k}": {"parents": [f"i{k}"]} for k in range(n)},
    }
    sim = SimulationBuilder().build_from_entities(tbs, cas)
    res = {v: sim.calculate_add(v, an) for v in VARIABLES}
    lignes = []
    for k, b in enumerate(bruts):
        lignes.append({"brut": b, **{v: float(res[v][k]) for v in VARIABLES}})
    return lignes


def ecrire(annee: int = 2026, versant: str | None = None) -> Path:
    lignes = calculer(annee, categorie=VERSANTS[versant] if versant else None)
    nom = f"openfisca_prive_{annee}.csv" if versant is None else f"openfisca_public_{versant}_{annee}.csv"
    sortie = RACINE / "parametres" / "donnees" / nom
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["brut", *VARIABLES])
        w.writeheader()
        for l in lignes:
            w.writerow({k: round(v, 2) for k, v in l.items()})
    return sortie


if __name__ == "__main__":
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    import openfisca_france
    print(f"OpenFisca-France {openfisca_france.__version__ if hasattr(openfisca_france, '__version__') else ''}")
    print(f"Écrit : {ecrire(a)}")
    for v in VERSANTS:
        print(f"Écrit : {ecrire(a, v)}")
