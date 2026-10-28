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


def test_logement_reprise_amortissements():
    from moteur.logement import reprise_amortissements
    comparer(reprise_amortissements(P), "Logement", 104)


@pytest.mark.parametrize("scenario, col", [("prudent", "B"), ("median", "C"), ("optimiste", "D")])
def test_hauts_revenus(scenario, col):
    from moteur import hauts_revenus as hr
    assert hr.reactions(P)[scenario]["montant"] == pytest.approx(VAL[("Hauts revenus", f"{col}9")], abs=0.01)
    assert hr.baisse_revenus_declares(P)[scenario] == pytest.approx(VAL[("Effets macro", f"{col}226")], abs=0.01)


def test_emploi():
    from moteur import emploi as em
    e = em.effets_reformes(P)
    for j, col in (("crise", "D"), ("median", "E"), ("optimiste", "F")):
        assert e[j]["emplois"] == pytest.approx(VAL[("Emploi", f"{col}22")], abs=1)
    assert em.cout_reformes(P) == pytest.approx(VAL[("Emploi", "G24")], abs=0.01)
    assert em.gain_par_emploi(P, "prudent") == pytest.approx(VAL[("Emploi", "B245")], abs=0.01)
