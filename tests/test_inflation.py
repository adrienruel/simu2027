"""Inflation et règle d'indexation (moteur/inflation.py)."""
import pytest

from moteur.inflation import indice_reel, serie
from moteur.parametres import Parametres

P = Parametres()


def test_base_banque_de_france_puis_long_terme():
    s = serie(P)
    assert s[2027] == pytest.approx(0.019) and s[2028] == pytest.approx(0.016)
    assert s[2040] == pytest.approx(0.018)
    assert serie(P, "crise")[2040] < s[2040] < serie(P, "optimiste")[2040]


def test_recession_de_2029_baisse_l_inflation():
    assert serie(P)[2029] < 0.016


def test_indexation_min_inflation_croissance():
    i = indice_reel(P)
    assert i[2029] == 1.0
    assert i[2030] < 1.0  # récession de 2029, sans rattrapage
    assert i[2073] == pytest.approx(i[2030])
    ancienne = indice_reel(P.avec({"revalorisation.regle": "croissance_sans_inflation"}))
    assert ancienne[2073] < 0.7


def test_v235_inchangee():
    v = Parametres(reference="v235")
    assert not v.val("inflation.active") and v.val("revalorisation.regle") == "croissance_sans_inflation"
    assert v.val("ancien_systeme.age_legal")["programme"] == 65
