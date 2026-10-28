"""Scénario de crise : quatrième scénario calculé, comparé à la v235.

Deux cibles :
- reference/cibles/crise.csv : la procédure de la feuille « Scénario de crise » refaite dans LibreOffice
  en pleine précision (outils/cibles_crise.py) ;
- la feuille « Scénario de crise » elle-même (lignes 5 à 9), arrondie à six décimales.
Pour reproduire la v235, le calcul garde le taux d'impôt local recopié à la main dans les feuilles de
salariés (comme_v235=True). Le calcul publié recalcule le point fixe avec les paramètres de crise.
"""
import csv
from pathlib import Path

import pytest

from moteur.macro import calculer
from moteur.parametres import Parametres
from moteur.unites import facteur

RACINE = Path(__file__).resolve().parent.parent
P = Parametres()
C = P.en_crise(comme_v235=True)
RES = calculer(C)["prudent"]
PIB0 = 2920 * facteur(C, 2024, "recettes")
TEND = C.val("macro.tendance", "prudent")


def _moteur(t):
    return {"deficit": -RES.maastricht[t], "dette_pib": RES.dette_pib[t],
            "pib": PIB0 * (1 + TEND) ** (t - 2029) + RES.pib_effet[t], "chomage": RES.detail["chomage"][t]}


def _cibles():
    for r in csv.DictReader((RACINE / "reference" / "cibles" / "crise.csv").open(encoding="utf-8")):
        yield int(r["annee"]), {k: float(v) for k, v in r.items() if k != "annee" and v}


@pytest.mark.parametrize("grandeur, tol", [("deficit", 1e-9), ("dette_pib", 1e-9), ("pib", 1e-6), ("chomage", 1e-9)])
def test_pleine_precision(grandeur, tol):
    for t, c in _cibles():
        if grandeur in c:
            assert _moteur(t)[grandeur] == pytest.approx(c[grandeur], abs=tol), t


def test_feuille_figee():
    lignes = list(csv.reader((RACINE / "reference" / "v235" / "scenario_de_crise.tsv").open(encoding="utf-8"), delimiter="\t"))
    lire = lambda i: [float(x) if x else None for x in lignes[i][1:]]
    deficit, dette, pib, chomage = lire(4), lire(5), lire(6), lire(8)
    for i, t in enumerate(range(2029, 2074)):
        m = _moteur(t)
        assert m["deficit"] == pytest.approx(deficit[i], abs=6e-7), t
        assert m["dette_pib"] == pytest.approx(dette[i], abs=6e-7), t
        assert m["pib"] == pytest.approx(pib[i], abs=6e-6), t
        if i < len(chomage) and chomage[i] is not None:
            assert m["chomage"] == pytest.approx(chomage[i], abs=6e-7), t


def test_publie_recalcule_le_point_fixe():
    """Sans la copie figée, le taux local monte un peu en crise ; l'écart de déficit reste minime."""
    from moteur.collectivites import taux_impot_local
    juste = P.en_crise()
    assert taux_impot_local(juste) > taux_impot_local(P)
    r = calculer(juste)["prudent"]
    assert max(abs(r.maastricht[t] - RES.maastricht[t]) for t in range(2029, 2074)) < 1e-3


def test_parametres_de_base_intacts():
    assert P.colonne_prudent == "prudent" and P.val("transition.decote_participations") == 0.1
    assert C.val("transition.decote_participations") == 0.2 and C.val("macro.multiplicateur") == 1
