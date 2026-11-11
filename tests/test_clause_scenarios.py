"""Règle de trajectoire dans tous les scénarios : même point de départ (DÉCISION d'Adrien du 29/10/2026).

Depuis le 12/11/2026, la règle est celle du noyau (moteur/noyau.Regle) : cible, leviers ordonnés, capacités."""
import pytest

from moteur import noyau
from moteur.parametres import Parametres

R = noyau.resultats(Parametres())
CONTRIBUTION, RUI = "Contribution d'épargne retraite", "Baisse du revenu universel"


@pytest.mark.parametrize("s", ["crise", "prudent", "median", "optimiste"])
def test_meme_point_de_depart(s):
    """3 % en 2029, sauf si les instruments de la règle sont au maximum (5 points d'épargne, RUI au plancher)."""
    r = R[s][2029]["regle"]
    if r["reste_a_couvrir"] > 1e-6:
        assert r["details"][CONTRIBUTION]["points"] == pytest.approx(5.0) and R[s][2029]["deficit"] < 4.0  # règle au maximum
    else:
        assert R[s][2029]["deficit"] == pytest.approx(3.0, abs=0.01)
    assert R[s][2029]["deficit_sans_regle"] > 3.0


@pytest.mark.parametrize("s", ["median", "optimiste"])
def test_sortie_plus_tot_que_le_prudent(s):
    # contribution et baisse du RUI arrêtées dès que le déficit sans règle passe sous 3 %
    def utilise(c):
        return c["regle"]["leviers"][CONTRIBUTION] + c["regle"]["leviers"][RUI]
    fin = max(t for t in R[s] if utilise(R[s][t]) > 0.01)
    fin_p = max(t for t in R["prudent"] if utilise(R["prudent"][t]) > 0.01)
    assert fin < fin_p
    assert all(R[s][t]["regle"]["leviers"][CONTRIBUTION] < 0.01 for t in R[s] if R[s][t]["deficit_avant_regle"] <= 3.0)


def test_option_point_de_depart_commun():
    """Option macro.depart_commun : supprimée avec l'ancien moteur (12/11/2026) ; le paramètre reste désactivé.
    Tous les scénarios partent du statu quo de leur propre scénario, avec le même mécanisme."""
    assert Parametres().val("macro.depart_commun") is False


def test_ordre_des_scenarios_sans_regle():
    # 2029 exclu : l'inflation plus basse de la crise baisse un peu ses intérêts nominaux (effet de Fisher)
    for t in (2032, 2037, 2050):
        assert (R["crise"][t]["deficit_sans_regle"] > R["prudent"][t]["deficit_sans_regle"]
                > R["median"][t]["deficit_sans_regle"] > R["optimiste"][t]["deficit_sans_regle"])


def test_les_comptes_se_publient_avec_et_sans_la_regle():
    """Le noyau publie le déficit de l'année avant et après les leviers de la règle. La règle ne le fait monter que si son gain net est négatif :
    restitution des contributions du fonds et effet récessif décalé des baisses du RUI passées l'emportent sur les
    leviers de l'année (même comportement que l'ancien moteur : médian 2040-2045, prudent 2044)."""
    for s in R:
        for t in R[s]:
            if R[s][t]["deficit"] > R[s][t]["deficit_avant_regle"] + 1e-9:
                assert R[s][t]["regle"]["gain"] < 0


def test_v235_prudent_seul():
    v = Parametres(reference="v235")
    assert v.val("clause.scenarios") == ["prudent"]
