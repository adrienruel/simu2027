"""Étape 1 : feuille Effets macro, trois scénarios, 2029-2073, contre la v235."""
import sys
from pathlib import Path

import pytest
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outils"))
from arbre import VAL  # noqa: E402

from moteur import macro
from moteur.parametres import Parametres

R = macro.calculer(Parametres(reference="v235"))
LIGNES = {
    "prudent": {"pib_effet": 107, "solde_effet": 109, "charge_dette": 111, "solde_public": 112, "dette": 113, "maastricht": 114, "dette_pib": 115},
    "median": {"pib_effet": 136, "solde_effet": 138, "charge_dette": 140, "solde_public": 141, "dette": 142, "maastricht": 143, "dette_pib": 144},
    "optimiste": {"pib_effet": 165, "solde_effet": 167, "charge_dette": 169, "solde_public": 170, "dette": 171, "maastricht": 172, "dette_pib": 173},
}
CAS = [(s, k, l) for s, d in LIGNES.items() for k, l in d.items()]


@pytest.mark.parametrize("scenario, grandeur, ligne", CAS)
def test_effets_macro(scenario, grandeur, ligne):
    serie = getattr(R[scenario], grandeur)
    tol = 1e-6 if grandeur in ("maastricht", "dette_pib") else 0.01
    for i, t in enumerate(macro.ANNEES):
        cible = VAL[("Effets macro", f"{get_column_letter(i + 2)}{ligne}")]
        assert serie[t] == pytest.approx(cible, abs=tol), (scenario, grandeur, t)


def test_deficits_publies_prudent():
    d = R["prudent"].maastricht
    assert [round(-d[t] * 100, 2) for t in (2029, 2032, 2037)] == [4.67, 3.81, 2.31]


@pytest.mark.parametrize("cle, ligne", [("avant", 8), ("etalement", 12), ("contribution", 14), ("points", 15), ("rui", 17), ("rui_euros", 18), ("reste", 19)])
def test_clause_de_trajectoire(cle, ligne):
    c = R["prudent"].detail["clause"]
    for i, t in enumerate(macro.ANNEES):
        cible = VAL[("Clause de trajectoire", f"{get_column_letter(i + 2)}{ligne}")]
        assert c[t][cle] == pytest.approx(cible, abs=1e-6 if cle == "avant" else 0.01), (cle, t)


def test_prudent_avant_clause_publie():
    c = R["prudent"].detail["clause"]
    assert [round(c[t]["avant"] * 100, 2) for t in (2029, 2032, 2037)] == [5.23, 5.18, 4.07]


@pytest.mark.parametrize("scenario, ligne", [("prudent", 28), ("median", 29), ("optimiste", 30)])
def test_chomage(scenario, ligne):
    c = R[scenario].detail["chomage"]
    for i, t in enumerate(macro.ANNEES):
        cible = VAL.get(("Emploi", f"{get_column_letter(i + 2)}{ligne}"))
        if cible is None:  # la v235 s'arrête en 2040
            break
        assert c[t] == pytest.approx(cible, abs=1e-9), (scenario, t)


def test_chomage_2037_publie():
    assert round(R["prudent"].detail["chomage"][2037] * 100, 2) == 7.26
    assert round(R["median"].detail["chomage"][2037] * 100, 2) == 6.13
