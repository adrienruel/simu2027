"""IS progressif (moteur/is_bareme.py)."""
import pytest

from moteur.is_bareme import impot_etat, taux_grandes, taux_investissement, taux_marginal_etat, taux_moyen, taux_taille
from moteur.parametres import Parametres
from moteur.recettes.entreprises import is_beneficiaires

P = Parametres()
B = P.avec({"entreprises.is_progressif": {"active": True, "tranches": [[0, 0.15], [42500, 0.30], [250000, 0.45]]}})


def test_taux_unique_par_defaut():
    for f in (taux_grandes, taux_investissement, taux_moyen):
        assert f(P) == pytest.approx(0.40)
    assert impot_etat(P, 100000) == pytest.approx(40000)


def test_bareme():
    assert impot_etat(B, 42500) == pytest.approx(6375)
    assert impot_etat(B, 100000) == pytest.approx(6375 + 57500 * 0.30)
    assert taux_marginal_etat(B, 300000) == 0.45 and taux_marginal_etat(B, 10000) == 0.15
    assert taux_taille(B, "TPE") == 0.30 and taux_grandes(B) == 0.45
    assert 0.15 < taux_moyen(B) < 0.45


def test_calage_neutre():
    from outils.is_progressif import caler, parametres
    t = caler([(0, 0.15), (42500, 0.30)], 250000)
    assert is_beneficiaires(parametres([(0, 0.15), (42500, 0.30), (250000, t)])) == pytest.approx(is_beneficiaires(P), rel=1e-6)
    assert t > 0.40  # alléger les petites oblige à monter le haut du barème
