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
    from moteur.mesures import ecartees
    from moteur.mesures import registre, plein_effet
    ecartees_ = {"eco:" + x["mesure"][:50] for x in ecartees(P)}  # économies sans sources : comptées pour zéro (05/11/2026)
    ecartees_ |= {"eco:" + m["mesure"][:50] for m in registre(P.programme)  # estimées à zéro dans le prudent (AME…)
                  if (m.get("nature") or "montant") != "calcul_moteur" and plein_effet(m, P) == 0}
    for m in R["mesures"]:
        effet = max(abs(m["annees"][t]["solde_avant_clause"]) for t in m["annees"])
        if m["id"] in NULLES_DANS_LE_PRUDENT or m["id"] in ecartees_:
            assert effet < 1e-9, m["id"]
        else:
            assert effet > 0.01, m["id"]


def test_decomposition():
    for m in R["mesures"]:
        for t, d in m["annees"].items():
            assert d["statique"] + d["economie"] + d["dette_interets"] == pytest.approx(d["solde_avant_clause"], abs=1e-9)


def test_interactions_limitees():
    """Les effets des mesures s'additionnent à peu près. Depuis la prime de taux liée à la dette (29/10/2026),
    les intérêts dépendent de la dette accumulée : les interactions croissent avec le temps (tolérance : 5 Md€
    ou 10 % de l'effet d'ensemble)."""
    for t in (2029, 2037, 2050):
        somme = sum(m["annees"][t]["solde_avant_clause"] for m in R["mesures"])
        ens = R["ensemble"][t]["solde_avant_clause"]
        assert abs(ens - somme) < max(5, 0.12 * abs(ens)), t  # 12 % : interactions avec les règles par ministère (04/11/2026)


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
