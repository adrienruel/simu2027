"""Étape 1 : feuille Effets macro, trois scénarios, 2029-2073, contre la v235."""
import sys
from pathlib import Path

import pytest
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outils"))
from arbre import VAL  # noqa: E402

from moteur import macro
from moteur.parametres import Parametres

R = macro.calculer(Parametres())
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
