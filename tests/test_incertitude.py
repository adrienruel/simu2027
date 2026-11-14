"""Incertitude chiffrée (phase D, moteur/incertitude.py)."""
import pytest

from moteur import incertitude as inc
from moteur.parametres import Parametres


def test_loi_centiles():
    d = {"crise": 0.0, "prudent": 1.0, "median": 2.0, "optimiste": 4.0}
    assert inc._valeur(d, 0.0) == pytest.approx(2.0)
    assert inc._valeur(d, -inc.Z90) == pytest.approx(1.0)  # prudent = 10e centile
    assert inc._valeur(d, inc.Z90) == pytest.approx(4.0)   # optimiste = 90e centile
    assert inc._valeur(d, -10) == pytest.approx(0.0)       # borné par la crise
    assert inc._valeur(d, 10) == pytest.approx(6.0)        # un pas de plus que l'optimiste


def test_loi_sans_prudent_ecrit_et_sens_inverse():
    jeu = {"crise": 0.1, "median": 0.3, "optimiste": 0.4}  # jeux d'emploi : prudent = milieu crise / médian
    assert inc._valeur(jeu, -inc.Z90) == pytest.approx(0.2)
    inverse = {"crise": 9.0, "prudent": 8.0, "median": 7.0, "optimiste": 6.0}
    assert inc._valeur(inverse, -inc.Z90) == pytest.approx(8.0)
    assert inc._valeur(inverse, -10) == pytest.approx(9.0)


def test_tirages_communs_et_reproductibles():
    a = inc.z_tirage(2029, 3, 0.5, "macro.multiplicateur")
    assert a == inc.z_tirage(2029, 3, 0.5, "macro.multiplicateur")
    assert a != inc.z_tirage(2029, 4, 0.5, "macro.multiplicateur")
    # rho = 1 : même z pour toutes les hypothèses d'un tirage
    assert inc.z_tirage(2029, 3, 1.0, "a") == pytest.approx(inc.z_tirage(2029, 3, 1.0, "b"))


def test_tirage_ne_touche_que_la_colonne_mediane(monkeypatch):
    p = Parametres()
    monkeypatch.setattr(inc, "z_tirage", lambda g, i, rho, nom: -inc.Z90)
    c = inc.tirer(p, 1, 0, 1.0)
    v, w = p["macro.multiplicateur"].valeur, c["macro.multiplicateur"].valeur
    assert w["median"] == pytest.approx(v["prudent"])
    assert {k: w[k] for k in ("crise", "prudent", "optimiste")} == {k: v[k] for k in ("crise", "prudent", "optimiste")}
    assert p["macro.multiplicateur"].valeur["median"] == v["median"]  # l'original n'est pas modifié
