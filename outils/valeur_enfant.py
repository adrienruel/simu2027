"""Ce que rapporte (ou coûte) un enfant de plus au ménage, système actuel contre nouveau système.

Pour chaque couple type et chaque rang d'enfant (1er, 2e, 3e), écart de revenu disponible entre le ménage
avec n enfants et le ménage avec n − 1 enfants, dans le système actuel (OpenFisca-France, législation 2026 :
allocations familiales, complément familial, allocation de rentrée, quotient familial, aides au logement…)
et dans le nouveau système (complément de RUI par enfant, quotient plafonné).

Sert à chiffrer l'incitation financière du programme à avoir des enfants (moteur/demographie.py).
Écrit parametres/donnees/valeur_enfant_2026.csv.

    python -m outils.valeur_enfant
"""
from __future__ import annotations

import csv
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
from moteur.demographie import COUPLES, menages_valeur_enfant as menages  # noqa: F401  (une seule définition)


def calculer() -> list[dict]:
    from moteur.menages_types import nouveau
    from moteur.parametres import Parametres
    from outils.openfisca_menages import calculer as of
    p = Parametres()
    ms = menages()
    act = {l["id"]: l for l in of(2026, ms)}
    nouv = {m["id"]: nouveau(m, p)["revenu_disponible"] for m in ms}
    out = []
    for c in COUPLES:
        for n in (1, 2, 3):
            a, b = f"{c}_{n}", f"{c}_{n - 1}"
            out.append({"menage": c, "rang": n,
                        "actuel": round(act[a]["revenu_disponible"] - act[b]["revenu_disponible"], 2),
                        "nouveau": round(nouv[a] - nouv[b], 2)})
    return out


def ecrire() -> Path:
    lignes = calculer()
    sortie = RACINE / "parametres" / "donnees" / "valeur_enfant_2026.csv"
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    return sortie


if __name__ == "__main__":
    for l in calculer():
        print(f"{l['menage']:18} rang {l['rang']}  actuel {l['actuel']:8.0f}  nouveau {l['nouveau']:8.0f}  écart {l['nouveau'] - l['actuel']:+8.0f}")
    print(ecrire())
