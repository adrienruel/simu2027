"""Dépenses des ministères année par année (moteur/depenses/ministeres.py)."""
import pytest

from moteur.depenses.ministeres import publics, trajectoire
from moteur.depenses.statique import depenses
from moteur.parametres import Parametres

P = Parametres()


def test_point_de_depart_inchange():
    d = depenses(P)["lignes"]
    attendu = (d["missions"] + d["autres_missions"] + d["collectivites"] + d["securite_sociale_hors_sante"]
               + d["economies_missions"] + d["economies_supplementaires"])
    tr = trajectoire(P)
    assert tr["base"] == pytest.approx(attendu)
    assert sum(g["valeurs"][2029] for g in tr["groupes"].values()) == pytest.approx(attendu)


def test_les_ministeres_augmentent():
    g = trajectoire(P)["groupes"]
    total = {t: sum(x["valeurs"][t] for x in g.values()) for t in (2029, 2050, 2073)}
    assert total[2029] < total[2050] < total[2073]
    assert g["Armées"]["valeurs"][2073] > g["Armées"]["depart"]  # suit le PIB


def test_eleves_seulement_apres_2035():
    ix = publics(P)
    assert ix["eleves"][2030] == 1.0 and ix["eleves"][2035] == 1.0
    assert ix["eleves"][2060] < 1.0


def test_v235_inchangee():
    assert not Parametres(reference="v235").val("ministeres.par_public")
