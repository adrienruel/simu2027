"""Valeur d'un emploi au barème du programme (21/11/2026, moteur/emploi_valeur.py)."""
import pytest

from moteur import emploi_valeur as ev
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres

P = Parametres()


def baisse(md, instrument="travail", incidence=""):
    return Mesure("Essai", "recettes", {t: -md for t in ANNEES}, instrument=instrument, incidence=incidence)


def test_statu_quo_facteur_un():
    assert all(v == 1.0 for v in ev.facteur(P, "prudent", [], 1.3).values())


def test_la_cellule_retrouve_la_valeur_d_un_emploi():
    from moteur.programme_simple import ProgrammeSimple
    c = ev.cellule(P, 1.3)
    v = ProgrammeSimple.valeur_emploi_cellule(P, 1.3) - P.val("emploi.allocation_chomeur_evitee")
    assert c["prelevements"] + c["tva"] == pytest.approx(v, rel=1e-9)


def test_baisse_d_impot_sur_le_travail_fait_rapporter_moins():
    for inc in ("", "proportionnel", "bas"):
        f = ev.facteur(P, "prudent", [baisse(10, incidence=inc)], 1.3)
        assert f[2037] < 1.0
    hausse = ev.facteur(P, "prudent", [baisse(-10)], 1.3)
    assert hausse[2037] > 1.0


def test_incidence_compte():
    """Un allègement près du SMIC pèse plus sur un emploi à 1,3 SMIC qu'un impôt des hauts revenus."""
    bas = 1 - ev.facteur(P, "prudent", [baisse(10, incidence="bas")], 1.3)[2037]
    haut = 1 - ev.facteur(P, "prudent", [baisse(10, incidence="haut")], 1.3)[2037]
    assert bas > haut >= 0
    assert ev.facteur(P, "prudent", [baisse(10, incidence="haut")], "moyen")[2037] <= 1.0


def test_consommation_et_mesures_hors_champ():
    assert ev.facteur(P, "prudent", [baisse(10, instrument="consommation")], 1.3)[2037] < 1.0
    autre = Mesure("Essai", "recettes", {t: -10 for t in ANNEES}, instrument="capital_entreprises")
    assert ev.facteur(P, "prudent", [autre], 1.3)[2037] == 1.0
    effet = Mesure("Essai", "recettes", {t: -10 for t in ANNEES}, instrument="travail", nature="effet_macro")
    assert ev.facteur(P, "prudent", [effet], 1.3)[2037] == 1.0


def test_impots_sur_la_marge_d_un_emploi():
    """Part non salariale de la valeur ajoutée : IS et impôts de production au taux implicite, au barème du
    programme ; rien sans marge."""
    va = P.val("seniors.valeur_ajoutee_emploi")
    e = ev.excedent(P, "prudent", [], "moyen", va)
    marge = va - ev.cellule(P, "moyen")["cout"]
    assert e[2037] == pytest.approx(marge * P.val("emploi.taux_impots_excedent"))
    assert all(v == 0 for v in ev.excedent(P, "prudent", [], "moyen", 1000.0).values())
    hausse_is = Mesure("Essai", "recettes", {t: 20.0 for t in ANNEES}, instrument="capital_entreprises")
    assert ev.excedent(P, "prudent", [hausse_is], "moyen", va)[2037] > e[2037]
