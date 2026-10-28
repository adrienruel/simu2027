"""Étape 1 : feuilles annexes de la trajectoire, contre la v235."""
import sys
from pathlib import Path

import pytest
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outils"))
from arbre import VAL  # noqa: E402

from moteur.parametres import Parametres

P = Parametres()
ANNEES = list(range(2029, 2074))


def serie(feuille, ligne):
    return [VAL[(feuille, f"{get_column_letter(i + 2)}{ligne}")] for i in range(45)]


def comparer(calcule: dict, feuille: str, ligne: int, tol=0.01):
    for t, cible in zip(ANNEES, serie(feuille, ligne)):
        assert calcule[t] == pytest.approx(cible, abs=tol), (feuille, ligne, t)


def test_calendrier():
    from moteur import calendrier
    a = calendrier.annees_2027_2028(P)
    assert a[2027]["dette"] == pytest.approx(VAL[("Calendrier budgétaire", "I18")], abs=0.01)
    assert a[2028]["dette"] == pytest.approx(VAL[("Calendrier budgétaire", "I19")], abs=0.01)


def test_successions():
    from moteur.recettes import successions, autres
    comparer(successions.supplement(P, autres.ligne_8_successions(P) / 1e9), "Successions", 15)


def test_ascenseur_social():
    from moteur.ascenseur_social import annuel
    from moteur.recettes import autres
    a = annuel(P, autres.ligne_8_successions(P) / 1e9, P.val("successions.exoneration_entreprises"))
    comparer({t: v["recettes"] for t, v in a.items()}, "Ascenseur social", 57)
    comparer({t: v["depenses"] for t, v in a.items()}, "Ascenseur social", 53)


def test_economies_registre():
    from moteur.mesures import economies
    comparer(economies(P), "Économies", 28)


@pytest.mark.parametrize("scenario, ligne", [("prudent", 49), ("median", 50), ("optimiste", 51)])
def test_sante(scenario, ligne):
    from moteur import sante
    comparer(sante.depenses(P, scenario), "Santé", ligne)


def test_tva_sante():
    from moteur import sante
    tv = sante.tva_sante(P)
    comparer(tv["prudent"], "Santé", 85)
    comparer(tv["median"], "Santé", 86)
