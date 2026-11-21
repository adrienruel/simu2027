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


def test_minimum_de_pension_des_carrieres_completes(pop):
    """Pensions entre le plancher de carrière complète et 1 870 € brut portées à 1 870 € : ≈ 4 millions de retraités,
    ≈ 20 Md€ bruts (moteur, LFI-RET-03 : 22 Md€ au prudent) ; sous le plancher, inchangées."""
    from outils.openfisca_mesures import Base
    lg = Base.population(type("B", (), {"lignes": pop})(), [{"population": {"pension_minimum": {"mensuel_brut": 1870}}}])
    gain = sum(l2["poids"] * (l2["pension_brute"] - l1["pension_brute"]) for l1, l2 in zip(pop, lg)) / 1e9
    n = sum(l1["poids"] for l1, l2 in zip(pop, lg) if l2["pension_brute"] > l1["pension_brute"])
    assert 3e6 < n < 5.5e6
    assert 14 < gain < 26
    assert all(l2["pension_brute"] == l1["pension_brute"] for l1, l2 in zip(pop, lg) if l1["pension_brute"] < 12 * 1000)


def test_assurance_chomage_au_montant_du_moteur(pop):
    """Roadmap 3.4 : les allocations des chômeurs concernés baissent (ou montent) du montant donné, au prorata."""
    from outils.openfisca_mesures import Base
    b = type("B", (), {"lignes": pop})()
    m0 = sum(l["poids"] * l["chomage_brut"] for l in pop) / 1e9
    lg = Base.population(b, [{"population": {"assurance_chomage": {"montant_md": 3.0, "age_max": 50}}}])
    assert sum(l["poids"] * l["chomage_brut"] for l in lg) / 1e9 == pytest.approx(m0 - 3.0, abs=0.01)
    assert all(l2["chomage_brut"] == l1["chomage_brut"] for l1, l2 in zip(pop, lg) if l1["age"] >= 50)
    lg = Base.population(b, [{"population": {"assurance_chomage": {"montant_md": -6.0}}}])
    assert sum(l["poids"] * l["chomage_brut"] for l in lg) / 1e9 == pytest.approx(m0 + 6.0, abs=0.01)
