"""Corrections du 30/10/2026 avant l'audit : seniors, permis rapide, rendement du fonds."""
import pytest

from moteur.ancien_systeme import retraites_reportes
from moteur import noyau
from moteur.parametres import Parametres

P = Parametres()
R = noyau.resultats(P, ("prudent",))["prudent"]
PROG = noyau.charger(P.programme)


def test_rendement_fonds_sous_le_rendement_net_d_impot():
    s17 = P.val("entreprises.taux_is_etat") + P.val("impot_local_entreprises.taux_communes") + P.val("impot_local_entreprises.taux_regions")
    assert P.val("epargne.rendement_fonds") == pytest.approx(P.val("macro.pib_par_euro_capital") * (1 - s17), abs=1e-4)


def test_seniors_suivent_les_reports():
    """Les emplois de seniors de l'ancien système s'éteignent quand plus personne n'est reporté."""
    rep = retraites_reportes(P)
    assert rep[2060] == 0
    sans = noyau.resultats(P.avec({"macro.seniors_lies_aux_reportes": False}), ("prudent",))["prudent"]
    # en 2060, seul le forfait de la v235 garde des emplois de seniors de l'ancien système
    cle = "Seniors : emploi (report de l'âge légal)"
    assert R[2060]["emplois_canaux"].get(cle, 0.0) == 0.0 and cle not in sans[2060]["emplois_canaux"]
    assert R[2037]["emplois_canaux"][cle] > 0


def test_permis_rapide_capital_a_part_avec_usure_et_cout():
    c = {t: {"permis_rapide": v} for t, v in PROG.canaux_courts(P, "prudent")["permis"].items()}
    assert c[2029]["permis_rapide"] < 0  # coût des services, pas encore de capital
    flux, usure = P.val("macro.permis_rapide"), P.val("macro.usure_capital")
    plafond = flux / usure * P.val("macro.pib_par_euro_capital")  # Md€ de rendement net au plus, avant impôt
    assert c[2073]["permis_rapide"] < plafond


def test_v235_inchangee():
    v = Parametres(reference="v235")
    assert v.val("epargne.rendement_fonds") == 0.0233
    assert not v.val("macro.seniors_lies_aux_reportes") and not v.val("macro.permis_rapide_separe")
