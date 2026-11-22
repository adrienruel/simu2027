"""Phase F1 : population synthétique et calcul par OpenFisca (outils/population_synthetique.py, openfisca_population.py)."""
import pytest

from moteur.parametres import Parametres
from outils import population_synthetique as ps


@pytest.fixture(scope="module")
def lignes():
    return ps.generer()


def test_marges_calees(lignes):
    e = [abs(x) for x in ps.ECARTS_CALAGE]
    assert max(e) < 0.35  # couples sans enfant au RSA : 37 000 familles, la marge la plus difficile
    assert sum(x < 0.02 for x in e) >= len(e) - 1


def test_effectifs_et_masses(lignes):
    p = Parametres()
    poids = lambda f: sum(l["poids"] for l in lignes if f(l))  # noqa: E731
    menages = sum({l["menage"]: l["poids"] for l in lignes if not l["rattache"]}.values())
    assert menages == pytest.approx(p.val("microsimulation.menages_2026") * 1e6, rel=0.03)
    assert poids(lambda l: l["statut"] == "retraite") == pytest.approx(16.9e6, rel=0.03)
    assert poids(lambda l: l["statut"] == "chomeur") == pytest.approx(2.7e6, rel=0.05)
    masse = lambda c: sum(l[c] * l["poids"] for l in lignes) / 1e9  # noqa: E731
    assert 950 < masse("salaire_brut") < 1150  # Insee : salaires bruts ≈ 1 050 Md€
    assert 370 < masse("pension_brute") < 420
    assert masse("dividendes") == pytest.approx(53, rel=0.01)


def test_deterministe():
    a = ps.generer(n_menages=300)
    b = ps.generer(n_menages=300)
    assert [l["salaire_brut"] for l in a] == [l["salaire_brut"] for l in b]


def test_etudiants_rattaches(lignes):
    et = [l for l in lignes if l["rattache"]]
    assert et and all(l["statut"] == "etudiant" and l["type"] == "seul" and l["role"] == "ref" for l in et)


def test_impot_revenu_openfisca(lignes):
    """Critère de sortie de la phase F pour l'IR : à 5 % du PLF 2026, plus les dépenses fiscales que la population n'a
    pas (microsimulation.niches_ir_non_modelisees : emploi à domicile, heures supplémentaires, dons, travaux, garde)."""
    pytest.importorskip("openfisca_france")
    from outils import openfisca_population as op
    res = op.totaux(lignes)
    p = Parametres()
    cible = p.val("microsimulation.cibles_2026")["impot_revenu"] + sum(p.val("microsimulation.niches_ir_non_modelisees").values())
    assert res["impot_revenu"] == pytest.approx(cible, rel=0.05)
