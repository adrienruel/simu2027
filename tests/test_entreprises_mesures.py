"""Impôts des entreprises sur la population synthétique : niveaux nationaux, taux réduit, retour d'IS."""
import pytest

from outils import entreprises_mesures as em
from outils import population_entreprises as pe


@pytest.fixture(scope="module")
def base():
    return em.Base(pe.generer(n_par_cellule={"MIC": 600, "PME": 400, "GE_ETI": 200}))


def test_niveaux_nationaux(base):
    t = base.totaux(em.ACTUELLE)
    assert t["is"] == pytest.approx(70.47, rel=1e-3)
    assert t["c3s"] == pytest.approx(4.8, rel=1e-6)
    assert t["cvae"] == 0.0


def test_taux_reduit_cale(base):
    # 5 points de moins sur environ 27 Md€ de base (Insee, 2022) : de l'ordre de 1,4 Md€
    r = base.reforme({"is_reduit": 0.10})
    assert -2.0 < r["total"] < -1.0


def test_retour_is_impots_production(base):
    r = base.reforme({"c3s_taux": 0.0, "cfe": 0.0, "cfe_industrie": 0.0})
    brut = r["c3s"] + r["cfe"]
    assert brut < 0 and 0.2 < -r["is"] / brut < 0.3
