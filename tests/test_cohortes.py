"""Cellules de salariés (âge × tranche de salaire) et comptes d'épargne par génération."""
import pytest

from moteur.cohortes import agregats, indices, socle_par_cellule
from moteur.macro import flux_epargne_obligatoire
from moteur.parametres import Parametres
from moteur.recettes import tva_menages
from moteur.recettes.impot_salaires import impot_prive, impot_public

P = Parametres()


def test_calage_2026_sur_le_budget_statique():
    """En 2026, les cellules retrouvent le budget statique (même distribution de salaires, à 1 % près)."""
    a = agregats(P)[2026]
    assert a["impot"] == pytest.approx(impot_prive(P) + impot_public(P), rel=0.01)
    assert a["tva"] == pytest.approx(tva_menages.tva_prive(P) + tva_menages.tva_public(P), rel=0.01)
    assert a["epargne"] == pytest.approx(flux_epargne_obligatoire(P), rel=0.02)


def test_indices_valent_un_en_2029():
    assert all(v == pytest.approx(1.0) for v in indices(P)[2029].values())


def test_socle_par_cellule_borne():
    plein = P.val("retraites.socle_plein") * 12
    for g in socle_par_cellule(P):
        assert 0 < g["socle_carriere"] <= g["socle_moyen"] <= plein


def test_sans_cellules_les_indices_valent_un():
    sans = P.avec({"cohortes.active": False})
    assert all(v == 1.0 for v in indices(sans)[2073].values())
