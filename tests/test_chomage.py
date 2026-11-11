"""Chômage modélisé jusqu'en 2073 (moteur/demographie.chomage_tendanciel, noyau commun)."""
import pytest

from moteur.demographie import chomage_tendanciel
from moteur import noyau
from moteur.noyau import ANNEES
from moteur.parametres import Parametres

P = Parametres()
R = noyau.resultats(P)


def test_tendanciel_cale_sur_2026():
    assert chomage_tendanciel(P)[2026]["taux"] == pytest.approx(P.val("chomage.taux_2026"), abs=1e-12)


def test_tendanciel_suit_la_composition_par_age():
    c = chomage_tendanciel(P)
    # moins de jeunes dans la population active : taux tendanciel un peu plus bas, jamais loin de 2026
    assert 0.075 < c[2073]["taux"] < c[2026]["taux"]


def test_chomage_calcule_chaque_annee():
    for s in ("prudent", "median", "optimiste"):
        c = {t: R[s][t]["chomage"] / 100 for t in ANNEES}
        assert all(P.val("emploi.chomage_incompressible") < c[t] < 0.12 for t in ANNEES)


def test_ordre_des_scenarios():
    for t in (2037, 2050, 2073):
        assert R["prudent"][t]["chomage"] > R["median"][t]["chomage"] > R["optimiste"][t]["chomage"]


def test_chomeurs_seniors_ajoutes():
    """Chômeurs seniors en plus avec l'âge à 67 ans : présents dès la montée en charge, au plus haut pendant la
    transition (personnes dont le départ est reporté, canal commun offre.seniors : plus personne après 2050), puis
    stables à leur niveau de long terme. 12/11/2026 : l'ancien moteur donnait un niveau de 2073 égal à celui de 2037
    à 1 % près, avec ses propres parts d'emploi des reportés ; le canal commun donne un pic de transition plus haut."""
    c = noyau.charger("ecologie_de_droite")._statique(P, ("prudent",))["prudent"]["chomeurs_seniors"]
    assert c[2037] > c[2032] > 0
    assert c[2037] > c[2073] > 0.5 * c[2037]
    assert c[2073] == pytest.approx(c[2060], rel=0.10)


def test_v235_inchangee():
    v = Parametres(reference="v235")
    assert v.val("chomage.dynamique") is False


def test_attente_couvre_les_generations_apres_2007():
    """Entre l'âge légal et 67 ans, le RUI est versé aussi aux générations nées après 2007 (2072-2073)."""
    from moteur.retraites_transition import attente_rui_et_socle
    a = attente_rui_et_socle(P)
    assert a[2073] == pytest.approx(a[2070], rel=0.05)
