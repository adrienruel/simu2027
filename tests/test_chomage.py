"""Chômage modélisé jusqu'en 2073 (moteur/demographie.chomage_tendanciel, moteur/macro.py)."""
import pytest

from moteur.demographie import chomage_tendanciel
from moteur.macro import ANNEES, calculer
from moteur.parametres import Parametres

P = Parametres()
R = calculer(P)


def test_tendanciel_cale_sur_2026():
    assert chomage_tendanciel(P)[2026]["taux"] == pytest.approx(P.val("chomage.taux_2026"), abs=1e-12)


def test_tendanciel_suit_la_composition_par_age():
    c = chomage_tendanciel(P)
    # moins de jeunes dans la population active : taux tendanciel un peu plus bas, jamais loin de 2026
    assert 0.075 < c[2073]["taux"] < c[2026]["taux"]


def test_chomage_calcule_chaque_annee():
    for s in ("prudent", "median", "optimiste"):
        c = R[s].detail["chomage"]
        assert set(ANNEES) <= set(c)
        assert all(P.val("emploi.chomage_incompressible") < c[t] < 0.12 for t in ANNEES)


def test_ordre_des_scenarios():
    for t in (2037, 2050, 2073):
        assert R["prudent"].detail["chomage"][t] > R["median"].detail["chomage"][t] > R["optimiste"].detail["chomage"][t]


def test_chomeurs_seniors_ajoutes():
    d = R["prudent"].detail["chomage_detail"]
    assert d[2073]["seniors"] > d[2037]["seniors"] > 0


def test_v235_inchangee():
    v = Parametres(reference="v235")
    assert v.val("chomage.dynamique") is False
    assert "chomage_detail" not in calculer(v)["prudent"].detail
