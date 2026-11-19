"""Micro vieillie : retraités et emploi des seniors du programme (phase O, 19/11/2026).

Avant la phase O, les retraités de la population vieillie suivaient la série du COR du statu quo pour tous les
programmes : un programme qui change l'âge de départ n'avait ni plus ni moins de retraités dans la micro, alors que
le moteur en compte (bibliotheque.*_age_legal_detail, offre.seniors)."""
from __future__ import annotations

import pytest

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import Parametres
from outils import openfisca_population as op
from outils import vieillissement as v


@pytest.fixture(scope="module")
def base():
    p = Parametres()
    return p, op.lire(), sq.simuler(p)["prudent"][2029]["emploi"]


def _tot(lg, f):
    return sum(l["poids"] for l in lg if f(l))


def _occupe(l):
    return l["statut"] in ("salarie_prive", "agent_public", "independant")


@pytest.mark.parametrize("nom", ["le_pen", "philippe"])
def test_retraites_et_emploi_seniors_suivent_le_moteur(base, nom):
    p, lignes, emploi_ref = base
    prog = noyau.charger(nom)
    traj = noyau.simuler(p, prog, scenarios=("prudent",))["prudent"]
    ec = v.ecart_seniors(prog, p)
    assert ec is not None
    an = 2037
    sans = v.recaler(lignes, prog, p, an, traj, emploi_ref)
    avec = v.recaler(lignes, prog, p, an, traj, emploi_ref, seniors=ec[an])
    d_ret = _tot(avec, lambda l: l["statut"] == "retraite") - _tot(sans, lambda l: l["statut"] == "retraite")
    assert d_ret == pytest.approx(ec[an]["retraites"], rel=0.1)
    # l'écart de retraités est entre 60 et 69 ans
    d_ret_age = (_tot(avec, lambda l: l["statut"] == "retraite" and 60 <= l["age"] <= 69)
                 - _tot(sans, lambda l: l["statut"] == "retraite" and 60 <= l["age"] <= 69))
    assert d_ret_age == pytest.approx(d_ret, rel=0.1)
    # même signe pour l'emploi des 60-69 ans que les emplois du moteur ; emploi total inchangé (à 0,1 % près)
    d_emp = (_tot(avec, lambda l: _occupe(l) and 60 <= l["age"] <= 69)
             - _tot(sans, lambda l: _occupe(l) and 60 <= l["age"] <= 69))
    assert d_emp * ec[an]["emploi"] > 0
    assert _tot(avec, _occupe) == pytest.approx(_tot(sans, _occupe), rel=1e-3)


def test_sans_changement_d_age_pas_d_ecart(base):
    p, _, _ = base
    prog = noyau.charger("attal")  # pas de mesure d'âge de départ
    noyau.simuler(p, prog, scenarios=("prudent",))
    assert v.ecart_seniors(prog, p) is None
