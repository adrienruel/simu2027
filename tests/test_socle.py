"""Premiers tests : paramètres, unités, barème.

Valeurs de référence : État du programme (v232), profils types « Détail SMIC » et
« Détail médian » (impôt unique mensuel).
"""
import pytest

from moteur.parametres import ErreurParametre, Parametres
from moteur.unites import DoubleConversion, Montant, en_euros_2026, facteur
from moteur import impot_unique as iu

P = Parametres()


# --- Paramètres --------------------------------------------------------------
def test_tous_les_parametres_sont_valides():
    assert len(list(P)) > 0
    for prm in P:
        if prm.statut == "SOURCE":
            assert prm.source


def test_source_obligatoire(tmp_path):
    f = tmp_path / "p.yaml"
    f.write_text("scenarios: [prudent]\ng:\n  x: {valeur: 1, unite: taux, statut: SOURCE}\n")
    with pytest.raises(ErreurParametre):
        Parametres(f)


def test_montant_sans_annee_refuse(tmp_path):
    f = tmp_path / "p.yaml"
    f.write_text("scenarios: [prudent]\ng:\n  x: {valeur: 1, unite: md_eur, statut: DECISION}\n")
    with pytest.raises(ErreurParametre):
        Parametres(f)


# --- Unités ------------------------------------------------------------------
def test_facteur_salaire_prive_2024():
    assert facteur(P, 2024, "salaire_prive") == pytest.approx(1.020 * 1.022)


def test_facteur_recettes_2024():
    assert facteur(P, 2024, "recettes") == pytest.approx(1.039456425, abs=1e-9)  # Total!B124


def test_aucun_montant_converti_deux_fois():
    m = en_euros_2026(Montant(100.0, 2024), P, "recettes")
    with pytest.raises(DoubleConversion):
        en_euros_2026(m, P, "recettes")


# --- Barème ------------------------------------------------------------------
@pytest.mark.parametrize("cout, impot_mensuel", [
    (23_750, 168),   # SMIC
    (42_500, 1_129), # salarié médian
])
def test_profils_types_v232(cout, impot_mensuel):
    assert iu.impot(cout, P) / 12 == pytest.approx(impot_mensuel, abs=0.5)


def test_rien_sous_le_premier_seuil():
    assert iu.impot(12_500, P) == 0


def test_borne_taux_marginal():
    for cout in range(0, 300_001, 1_000):
        assert iu.taux_marginal(cout, P) <= P.val("impot_unique.plafond_taux_marginal")


def test_impot_croissant():
    precedent = -1.0
    for cout in range(0, 200_001, 500):
        i = iu.impot(cout, P)
        assert i >= precedent
        precedent = i


def test_facteur_public_2023():
    assert facteur(P, 2023, "salaire_public") == pytest.approx(1.03924956063269, abs=1e-12)


def test_cle_en_double_refusee(tmp_path):
    f = tmp_path / "p.yaml"
    f.write_text("scenarios: [prudent]\ng:\n  x: {valeur: 1, unite: taux, statut: DECISION}\n  x: {valeur: 2, unite: taux, statut: DECISION}\n")
    with pytest.raises(ErreurParametre):
        Parametres(f)
