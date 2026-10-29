"""Convertit les fichiers de projections de population de l'Insee (juin 2026) en CSV lus par le moteur.

Fichiers Insee (Insee Résultats « Projections de population 2026 pour la France ») :
    00_central.xlsx, 12_fec_basse.xlsx, 11_fec_haute.xlsx
Feuille « population » : population au 1er janvier par âge (0 à 105 ans et plus) et année (1962-2070).
Feuille « deces » : décès par âge atteint et année (gardés pour vérifier la série de l'ancien système).

Écrit parametres/donnees/population_insee_2026_<scénario>.csv (annee, age, population) pour 2026-2070, et
deces_insee_2026_<scénario>.csv.

    python -m outils.population_insee <dossier des fichiers xlsx>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl

RACINE = Path(__file__).resolve().parent.parent
FICHIERS = {"central": "00_central", "fec_basse": "12_fec_basse", "fec_haute": "11_fec_haute"}


def lire(chemin: Path, feuille: str) -> dict[int, dict[int, float]]:
    ws = openpyxl.load_workbook(chemin, read_only=True, data_only=True)[feuille]
    lignes = ws.iter_rows(values_only=True)
    next(lignes)
    entete = next(lignes)
    annees = [int(x) if isinstance(x, (int, float)) else None for x in entete[1:]]
    out: dict[int, dict[int, float]] = {}
    for l in lignes:
        if l[0] is None:
            continue
        if str(l[0]).strip().lower().startswith("total"):
            break  # sous le total : tableaux par grand groupe d'âge
        try:
            age = int(str(l[0]).split()[0].rstrip("+"))
        except ValueError:
            continue
        for an, v in zip(annees, l[1:]):
            if an and 2026 <= an <= 2070 and isinstance(v, (int, float)):
                out.setdefault(an, {})[age] = float(v)
    return out


def convertir(dossier: Path) -> list[Path]:
    ecrits = []
    for nom, base in FICHIERS.items():
        chemin = next(dossier.glob(f"*{base}.xlsx"))
        for feuille, prefixe in (("population", "population"), ("deces", "deces")):
            d = lire(chemin, feuille)
            sortie = RACINE / "parametres" / "donnees" / f"{prefixe}_insee_2026_{nom}.csv"
            with sortie.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["annee", "age", "population" if prefixe == "population" else "deces"])
                for an in sorted(d):
                    for age in sorted(d[an]):
                        w.writerow([an, age, round(d[an][age])])
            ecrits.append(sortie)
    return ecrits


if __name__ == "__main__":
    for x in convertir(Path(sys.argv[1])):
        print(x)
