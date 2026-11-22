"""Roadmap 5.1 : variantes de FR-BDF (Banque de France, WP 1045, 2026) rejouées hors calage (docs/backtests.md)."""
import pytest

from outils import variantes_frbdf as v


@pytest.fixture(scope="module")
def res():
    return v.calcul(scenarios=("median",))


def test_signes_et_ordre_de_grandeur(res):
    """Mêmes signes que FR-BDF pour le PIB et le solde à 1, 2, 3, 5 et 10 ans ; PIB dans un facteur 4,5 (impôts
    directs la première année : 3,9 fois FR-BDF, calage sur Mésange, docs/backtests.md), solde dans un facteur 3."""
    for c, par in res.items():
        for h, (y, _e, b) in par["median"].items():
            fy, _fe, fb = v.FRBDF[c][h]
            assert y * fy > 0 and b * fb > 0, (c, h)
            assert 1 / 4.5 < y / fy < 4.5 or abs(y - fy) < 0.15, (c, h, y, fy)  # FR-BDF ≈ 0 : écart absolu
            assert 1 / 3 < b / fb < 3, (c, h, b, fb)


def test_depense_publique_proche(res):
    """Consommation publique : PIB à 25 % près de FR-BDF jusqu'à 5 ans."""
    for h in ("A1", "A2", "A3", "A5"):
        assert res["consommation_publique"]["median"][h][0] == pytest.approx(v.FRBDF["consommation_publique"][h][0], rel=0.25)
