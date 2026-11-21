"""Roadmap 3.3 (21/11/2026) : âge de départ dans la population de la microsimulation (sans OpenFisca)."""
import pytest

from outils import openfisca_population as op
from outils.openfisca_mesures import age_depart


@pytest.fixture(scope="module")
def pop():
    return op.lire()


def _bilan(lg):
    ret = sum(l["poids"] for l in lg if l["statut"] == "retraite")
    pen = sum(l["poids"] * l["pension_brute"] for l in lg) / 1e9
    return ret, pen


def test_age_abaisse_ou_releve(pop):
    """62 ans : ≈ +0,7 million de retraités et ≈ +18 Md€ de pensions brutes (moteur : 23,5 Md€ de pensions en 2032,
    même ordre) ; 60 ans : environ le double ; 65 ans : retraités et pensions en moins ; mêmes ménages, mêmes poids."""
    r0, p0 = _bilan(pop)
    out = {}
    for c in (60, 62, 65):
        lg = [dict(l) for l in pop]
        age_depart(lg, {"age_actuel": 64, "age_cible": c})
        assert [l["poids"] for l in lg] == [l["poids"] for l in pop]
        out[c] = _bilan(lg)
    assert 0.4e6 < out[62][0] - r0 < 1.0e6
    assert 12 < out[62][1] - p0 < 30
    assert out[60][1] - p0 > 1.8 * (out[62][1] - p0)
    assert out[65][0] < r0 and out[65][1] < p0
    lg = [dict(l) for l in pop]
    age_depart(lg, {"age_actuel": 64, "age_cible": 64})
    assert lg == pop
