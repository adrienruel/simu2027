"""Règle de trajectoire dans tous les scénarios : même point de départ (DÉCISION d'Adrien du 29/10/2026)."""
import pytest

from moteur.parametres import Parametres
from moteur.simulation import simuler

R = simuler(Parametres())


@pytest.mark.parametrize("s", ["crise", "prudent", "median", "optimiste"])
def test_meme_point_de_depart(s):
    assert R[s][2029]["deficit"] == pytest.approx(3.0, abs=0.01)
    assert R[s][2029]["deficit_avant_clause"] > 3.0


@pytest.mark.parametrize("s", ["median", "optimiste"])
def test_sortie_plus_tot_que_le_prudent(s):
    # contribution et baisse du RUI arrêtées dès que le déficit sans règle passe sous 3 %
    fin = max(t for t in R[s] if R[s][t]["clause_detail"]["contribution"] + R[s][t]["clause_detail"]["rui"] > 0.01)
    fin_p = max(t for t in R["prudent"] if R["prudent"][t]["clause_detail"]["contribution"] + R["prudent"][t]["clause_detail"]["rui"] > 0.01)
    assert fin < fin_p
    assert all(R[s][t]["clause_detail"]["contribution"] < 0.01 for t in R[s] if R[s][t]["deficit_avant_clause"] <= 3.0)


def test_point_de_depart_commun_sans_regle():
    """2029 : toutes les hypothèses à leur valeur prudente (DÉCISION d'Adrien du 30/10/2026)."""
    for x in ("crise", "median", "optimiste"):
        assert R[x][2029]["deficit_avant_clause"] == pytest.approx(R["prudent"][2029]["deficit_avant_clause"], abs=0.02)
        assert R[x][2029]["chomage"] == pytest.approx(R["prudent"][2029]["chomage"], abs=0.01)
        assert R[x][2029]["pib"] == pytest.approx(R["prudent"][2029]["pib"], rel=0.001)


def test_ordre_des_scenarios_sans_regle():
    for t in (2031, 2037, 2050):
        assert (R["crise"][t]["deficit_avant_clause"] > R["prudent"][t]["deficit_avant_clause"]
                > R["median"][t]["deficit_avant_clause"] > R["optimiste"][t]["deficit_avant_clause"])


def test_v235_prudent_seul():
    v = Parametres(reference="v235")
    assert v.val("clause.scenarios") == ["prudent"]
