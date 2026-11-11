"""Cellules de salariés (âge × tranche de salaire) et comptes d'épargne par génération."""
import pytest

from moteur.cohortes import agregats, indices, socle_par_cellule
from programmes.ecologie_de_droite.budget import flux_epargne_obligatoire
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
    """Sans les effets des réformes du supérieur (moteur/carrieres.py), présents dès 2029."""
    q = Parametres().avec({"carrieres.active": False})
    assert all(v == pytest.approx(1.0) for v in indices(q)[2029].values())


def test_socle_par_cellule_borne():
    plein = P.val("retraites.socle_plein") * 12
    for g in socle_par_cellule(P):
        assert 0 < g["socle_carriere"] <= g["socle_moyen"] <= plein


def test_sans_cellules_les_indices_valent_un():
    sans = P.avec({"cohortes.active": False})
    assert all(v == 1.0 for v in indices(sans)[2073].values())


def test_comptes_et_decumulation():
    """Les comptes grossissent, puis les rentes versées aux retraités montent après 2046."""
    from moteur.cohortes import comptes
    c = comptes(P)
    assert c[2029]["encours"] == 0 and c[2050]["encours"] > c[2040]["encours"] > 0
    assert c[2045]["paiements"] < c[2060]["paiements"] < c[2073]["paiements"]


def test_fiscalite_des_nouveaux_retraites_proche_de_la_croisiere():
    """Impôt et TVA des nouveaux retraités par profil : même ordre de grandeur que la croisière au prorata."""
    from moteur.cohortes import fiscalite_retraites_nouveaux
    from moteur.recettes.retraites_croisiere import impot_retraites
    from moteur.retraites_transition import retraites_nouveau_systeme
    f, n = fiscalite_retraites_nouveaux(P), retraites_nouveau_systeme(P)
    prorata = impot_retraites(P) * n[2073] / P.val("retraites.nombre_retraites")
    assert f[2073]["impot"] == pytest.approx(prorata, rel=0.15)


def test_menages_cales_en_2026():
    from moteur.cohortes import menages
    m = menages(P)[2026]
    assert m["couples"] == pytest.approx(P.val("quotient.conjugal")["couples"])
    assert m["part_un_revenu"] == pytest.approx(P.val("quotient.conjugal")["part_un_revenu"])
