"""Corrections du 30/10/2026 avant l'audit : seniors, permis rapide, rendement du fonds."""
import pytest

from moteur.ancien_systeme import retraites_reportes
from moteur.macro import calculer
from moteur.parametres import Parametres

P = Parametres()
R = calculer(P)


def test_rendement_fonds_sous_le_rendement_net_d_impot():
    s17 = P.val("entreprises.taux_is_etat") + P.val("impot_local_entreprises.taux_communes") + P.val("impot_local_entreprises.taux_regions")
    assert P.val("epargne.rendement_fonds") == pytest.approx(P.val("macro.pib_par_euro_capital") * (1 - s17), abs=1e-4)


def test_seniors_suivent_les_reports():
    """Les emplois de seniors de l'ancien système s'éteignent quand plus personne n'est reporté."""
    rep = retraites_reportes(P)
    assert rep[2060] == 0
    sans = calculer(P.avec({"macro.seniors_lies_aux_reportes": False}))["prudent"]
    # en 2060, seul le forfait de la v235 garde des emplois de seniors de l'ancien système
    assert R["prudent"].emplois[2060] < sans.emplois[2060]


def test_permis_rapide_capital_a_part_avec_usure_et_cout():
    c = R["prudent"].detail["canaux"]
    assert c[2029]["permis_rapide"] < 0  # coût des services, pas encore de capital
    flux, usure = P.val("macro.permis_rapide"), P.val("macro.usure_capital")
    plafond = flux / usure * P.val("macro.pib_par_euro_capital")  # Md€ de rendement net au plus, avant impôt
    assert c[2073]["permis_rapide"] < plafond


def test_v235_inchangee():
    v = Parametres(reference="v235")
    assert v.val("epargne.rendement_fonds") == 0.0233
    assert not v.val("macro.seniors_lies_aux_reportes") and not v.val("macro.permis_rapide_separe")
