"""Revenus et effectifs des inactifs (parametres/donnees/inactifs.csv), lus par le statu quo."""
from __future__ import annotations



def lire_inactifs():
    import csv
    from ..distribution import DONNEES
    with (DONNEES / "inactifs.csv").open(encoding="utf-8") as f:
        l = list(csv.DictReader(f))
    return [float(x["autre_revenu_annuel"]) for x in l], [float(x["effectif"]) for x in l]


