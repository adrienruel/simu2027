"""Extrait les valeurs cibles de la v235 (feuilles Total et Trajectoire) en CSV.

Ces valeurs sont ce que le moteur doit reproduire à l'étape 1.
Usage : python outils/extraire_cibles.py
"""
import csv
from pathlib import Path

REF = Path("reference/v235")
OUT = Path("reference/cibles")


def nombre(x: str):
    try:
        return float(x)
    except ValueError:
        return None


def trajectoire():
    lignes = (REF / "trajectoire_2029_2073.tsv").read_text(encoding="utf-8").splitlines()
    annees, rangs = None, []
    for l in lignes:
        c = l.split("\t")
        if c[0] == "Année":
            annees = [int(float(a)) for a in c[1:46]]
            continue
        if annees and len(c) >= 46 and all(nombre(v) is not None for v in c[1:46]):
            rangs.append([c[0]] + c[1:46])
    with open(OUT / "trajectoire.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["poste", *annees])
        w.writerows(rangs)
    return len(rangs)


def total():
    lignes = (REF / "total.tsv").read_text(encoding="utf-8").splitlines()
    rangs = []
    for l in lignes:
        c = l.split("\t")
        if len(c) >= 2 and c[0] and nombre(c[1]) is not None:
            ancien = nombre(c[2]) if len(c) > 2 else None
            rangs.append([c[0][:160], c[1], "" if ancien is None else c[2]])
    with open(OUT / "total.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["poste", "nouveau", "ancien"])
        w.writerows(rangs)
    return len(rangs)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("trajectoire :", trajectoire(), "postes ; total :", total(), "lignes")
