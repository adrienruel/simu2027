"""Étape 1 : lignes 17 à 22 et 43 de la feuille Trajectoire, contre la v235."""
import sys
from pathlib import Path

import pytest
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outils"))
from arbre import VAL  # noqa: E402

from moteur import trajectoire_annuelle as ta
from moteur.parametres import Parametres

R = ta.postes(Parametres(reference="v235"))


@pytest.mark.parametrize("poste, ligne", [("recettes_hors_macro", 43), ("sante", 18), ("retraites", 19), ("rui_aah", 20),
                                          ("investissement", 21), ("autres", 22)])
def test_postes(poste, ligne):
    for i, t in enumerate(ta.ANNEES):
        cible = VAL[("Trajectoire 2029-2073", f"{get_column_letter(i + 2)}{ligne}")]
        assert R[t][poste] == pytest.approx(cible, abs=0.01), (poste, t)


def test_recettes_avec_effets_macro_ligne_17():
    from moteur.simulation import simuler
    res = simuler(Parametres(reference="v235"), crise=False)
    for i, t in enumerate(ta.ANNEES):
        cible = VAL[("Trajectoire 2029-2073", f"{get_column_letter(i + 2)}17")]
        assert res["prudent"][t]["recettes"] == pytest.approx(cible, abs=0.01), t
