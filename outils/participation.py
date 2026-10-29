"""Gain à travailler d'une personne seule sans emploi, système actuel (OpenFisca-France, législation 2026).

Revenu disponible à 0, au mi-temps et au temps plein au SMIC (locataire, zone 2, 550 € de loyer : RSA, prime
d'activité, aides au logement compris). Le nouveau système est recalculé par le moteur (moteur/emploi.py,
participation_inactifs). Écrit parametres/donnees/participation_2026.csv.

    python -m outils.participation
"""
from __future__ import annotations

import csv
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
QUOTITES = (0.0, 0.5, 1.0)


def ecrire() -> Path:
    from moteur.parametres import Parametres
    from outils.openfisca_menages import calculer
    p = Parametres()
    smic = p.val("epargne.cout_smic_mensuel") * 12
    ms = [{"id": f"q{q}", "libelle": "seul", "adultes": [q * smic], "enfants": []} for q in QUOTITES]
    sortie = RACINE / "parametres" / "donnees" / "participation_2026.csv"
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["quotite_smic", "revenu_disponible_actuel"])
        for q, l in zip(QUOTITES, calculer(2026, ms)):
            w.writerow([q, round(l["revenu_disponible"], 2)])
    return sortie


if __name__ == "__main__":
    print(ecrire())
