"""Étape 1 : recettes de la feuille Total, contre les valeurs de la v235."""
import pytest

from moteur.parametres import Parametres
from moteur.recettes import impot_salaires as sal

P = Parametres()
MD = 1e9
TOL = 0.01 * MD  # 0,01 Md€


def test_effectifs_conserves():
    d = sal.effectifs_prive_2026(P)
    assert sum(d.effectifs) == pytest.approx(sum(sal.lire("salaries_prive.csv").effectifs))


def test_effectif_classe_27_5_30k():
    # Passage en euros de 2026!M50
    assert sal.effectifs_prive_2026(P).effectifs[8] == pytest.approx(1_216_660, rel=1e-5)


def test_impot_prive_total_ligne_4():
    assert sal.impot_prive(P) == pytest.approx(452_838_702_211.722, abs=TOL)


def test_alignement_public():
    assert sal.facteur_alignement_public(P) - 1 == pytest.approx(-0.135152, abs=1e-6)  # Fonctionnaires!AY1


def test_impot_public_total_ligne_6():
    assert sal.impot_public(P) == pytest.approx(140_079_910_374.771, abs=TOL)


from moteur import epargne as ep
from moteur.recettes import retraites_croisiere as rc


def test_capital_par_euro_de_rente():
    assert ep.capital_par_euro_de_rente(P) == pytest.approx(15.9366, abs=1e-4)  # Socle actuariel!B16


def test_revenu_par_euro_de_capital():
    assert ep.revenu_par_euro_de_capital(P) == pytest.approx(0.0430243, abs=1e-7)


def test_rente_classe_27_5_30k():
    assert ep.rente_mensuelle(ep.epargne_annuelle(28_750, P), P) == pytest.approx(114.965, abs=1e-3)  # BB10


def test_impot_retraites_ligne_5():
    assert rc.impot_retraites(P) == pytest.approx(24_097_348_601.3389, abs=TOL)
