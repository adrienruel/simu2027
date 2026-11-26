"""Décomposition du déficit et variantes communes de la dette (phase 3.1, 16/11/2026)."""
import pytest

from moteur import decomposition as dc
from moteur import noyau
from moteur.parametres import Parametres
from outils import variantes_dette as vd


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def sq(p):
    return noyau.simuler(p)


@pytest.mark.parametrize("nom", ["lisnard", "melenchon", "philippe"])
def test_decomposition_exacte(p, sq, nom):
    """Les composantes redonnent l'écart de déficit, entre deux années comme entre programme et statu quo."""
    res = noyau.simuler(p, noyau.charger(nom))
    for s in res:
        for t in (2030, 2037, 2050, 2073):
            for a, b in ((res[s][2029], res[s][t]), (sq[s][t], res[s][t]), (sq[s][2029], sq[s][t])):
                e = dc.ecart(a, b)
                assert abs(e["residu"]) < 1e-9
            n = dc.niveau(res[s][t])
            assert abs(n["residu"]) < 1e-9


def test_composantes_du_taux(sq):
    """Le taux apparent est la somme de ses composantes publiées."""
    for traj in sq.values():
        for x in traj.values():
            assert x["taux_apparent"] == pytest.approx(x["taux_base"] + x["taux_fisher"] + x["taux_bce"] + x["taux_prime"] + x["taux_scenario"], abs=1e-15)


def test_convention_2027_2028_par_defaut(p):
    """Sans décision D3, la convention reste celle d'avant (économie de 2026 placée en 2029)."""
    assert noyau.facteur_2027_2028(p) == 1.0


def test_variantes(p, sq):
    """Sans prime de dette, la prime disparaît ; taux long plus bas : moins d'intérêts ; croissance en 2027-2028 :
    dette de départ plus basse, flux inchangés."""
    sans = noyau.simuler(vd._variante(p, vd.VARIANTES["sans_prime_dette"]), scenarios=["prudent"])["prudent"]
    assert all(abs(x["taux_prime"]) < 1e-12 or x["taux_prime"] == p.val("macro.prime_dette_bornes")[0] for x in sans.values())
    bas = noyau.simuler(vd._variante(p, vd.VARIANTES["taux_long_3_3"]), scenarios=["prudent"])["prudent"]
    assert bas[2040]["deficit"] < sq["prudent"][2040]["deficit"]
    q = vd._variante(p, vd.VARIANTES["croissance_2027_2028"])
    assert noyau.facteur_2027_2028(q) == pytest.approx(1.009 * 1.012)
    cr = noyau.simuler(q, scenarios=["prudent"])["prudent"]
    assert cr[2029]["dette_debut"] == pytest.approx(sq["prudent"][2029]["dette_debut"] / (1.009 * 1.012))
    assert cr[2029]["solde_primaire"] == pytest.approx(sq["prudent"][2029]["solde_primaire"])
