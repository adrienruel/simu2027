"""Population synthétique d'entreprises : totaux d'Ésane exacts par cellule, IS par taille proche de la DGFiP."""
import numpy as np
import pytest

from outils import population_entreprises as pe


@pytest.fixture(scope="module")
def pop():
    return pe.generer(n_par_cellule={"MIC": 600, "PME": 400, "GE_ETI": 200})


def test_totaux_esane(pop):
    for c in pe._lire("entreprises_secteurs_tailles.csv"):
        sel = [e for e in pop if e["secteur"] == c["secteur"] and e["taille"] == c["taille"]]
        w = np.array([e["poids"] for e in sel])
        assert w.sum() == pytest.approx(c["entreprises"], rel=1e-9)
        assert w @ np.array([e["etp"] for e in sel]) == pytest.approx(c["etp"], rel=1e-9)
        assert w @ np.array([e["va"] for e in sel]) == pytest.approx(c["va_m"] * 1e6, rel=1e-9)
        assert w @ np.array([e["ebe"] for e in sel]) == pytest.approx(c["ebe_m"] * 1e6, rel=1e-9)


def test_bornes_classes():
    assert pe._bornes("500 k€–1 M€") == (5e5, 1e6)
    assert pe._bornes("20–42,5 k€") == (2e4, 42500.0)


def test_is_par_taille(pop):
    r = pe.controler(pop)
    tot = sum(v["is_brut_md"] for v in r.values())
    tot_dg = sum(v["is_brut_md_dgfip"] for v in r.values())
    assert abs(tot / tot_dg - 1) < 0.10
    assert r["PME"]["benefices_md"] == pytest.approx(r["PME"]["benefices_md_dgfip"], rel=0.05)
