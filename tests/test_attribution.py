"""Registre des lois et attribution par mesure."""
import pytest

from moteur.attribution import attribuer, mesures, variante
from moteur.macro import calculer
from moteur.parametres import ErreurParametre, Parametres

P = Parametres()
R = attribuer(P)
NULLES_DANS_LE_PRUDENT = {"ecole", "credibilite"}  # paramètres à 0 dans le prudent


def test_avec_ne_touche_pas_l_original():
    v = P.avec({"emploi.reformes_directes/alternance/retenue": 0, "macro.fraude_tva": 0})
    assert P.val("emploi.reformes_directes")["alternance"]["retenue"] == 1
    assert v.val("emploi.reformes_directes")["alternance"]["retenue"] == 0
    assert P.val("macro.fraude_tva", "median") == 3 and v.val("macro.fraude_tva", "median") == 0
    with pytest.raises(ErreurParametre):
        P.avec({"macro.inexistant": 0})
    with pytest.raises(ErreurParametre):
        P.avec({"emploi.creches/inexistant": 0})


def test_chaque_neutralisation_a_un_effet():
    for m in R["mesures"]:
        effet = max(abs(m["annees"][t]["solde_avant_clause"]) for t in m["annees"])
        if m["id"] in NULLES_DANS_LE_PRUDENT:
            assert effet < 1e-9, m["id"]
        else:
            assert effet > 0.01, m["id"]


def test_decomposition():
    for m in R["mesures"]:
        for t, d in m["annees"].items():
            assert d["statique"] + d["economie"] + d["dette_interets"] == pytest.approx(d["solde_avant_clause"], abs=1e-9)


def test_interactions_limitees():
    for t in (2029, 2037, 2050):
        somme = sum(m["annees"][t]["solde_avant_clause"] for m in R["mesures"])
        assert abs(R["ensemble"][t]["solde_avant_clause"] - somme) < 5, t


def test_sans_clause_egale_avant_clause_la_premiere_annee():
    avec = calculer(P)["prudent"]
    sans = calculer(P.avec({"clause.active": False}))["prudent"]
    assert -sans.maastricht[2029] == pytest.approx(avec.detail["clause"][2029]["avant"], abs=1e-12)
    assert all(sans.clause[t] == 0 for t in sans.clause)


def test_registre_identifiants_uniques():
    ids = [m["id"] for m in mesures()]
    assert len(ids) == len(set(ids))
    for m in mesures():
        variante(P, m)  # chaque neutralisation est applicable
