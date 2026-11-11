"""Tests de cohérence du levier IS : taux légal et déduction de l'investissement."""

from moteur.is_investissement import cout_net_etat
from moteur import noyau
from moteur.parametres import Parametres
from moteur.recettes.total import recettes_nouveau_systeme
from moteur.taux_effectifs import eatr_nouveau
from moteur.emploi_canaux import tableau

P = Parametres()


def _v(te, d):
    return P.avec({"entreprises.taux_is_etat": te, "is_investissement.part_admise": d, "is_investissement.hausse_part_admise/cible": d, "clause.active": False})


def _canal(p, canal, t=2037):
    return noyau.charger(p.programme).canaux_courts(p, "prudent")[canal][t]


def _loc(p):
    return next(x for x in tableau(p) if x["mesure"] == "entreprises_localisation")["emplois_prudent"]


def test_recettes_statiques_croissent_avec_le_taux():
    r = [recettes_nouveau_systeme(_v(te, 1.0))["total"] for te in (0.20, 0.30, 0.40)]
    assert r[0] < r[1] < r[2]


def test_deduction_baisse_le_taux_effectif_et_coute():
    assert eatr_nouveau(_v(0.40, 1.0)) < eatr_nouveau(_v(0.40, 0.5)) < eatr_nouveau(_v(0.40, 0.0))
    assert cout_net_etat(_v(0.40, 1.0))[2037] > cout_net_etat(_v(0.40, 0.5))[2037] > cout_net_etat(_v(0.40, 0.0))[2037]


def test_localisation_moins_de_pertes_avec_un_taux_plus_bas_ou_plus_de_deduction():
    assert _loc(_v(0.30, 1.0)) > _loc(_v(0.40, 1.0))
    assert _loc(_v(0.40, 1.0)) > _loc(_v(0.40, 0.0))


def test_erosion_croissante_avec_le_taux():
    e = [_canal(_v(te, 1.0), "erosion_is") for te in (0.20, 0.30, 0.40)]
    assert e[0] > e[1] > e[2]


def test_investissement_croit_avec_la_deduction():
    i = [_canal(_v(0.40, d), "investissement") for d in (0.0, 0.5, 1.0)]
    assert i[0] < i[1] < i[2]


def test_sans_deduction_les_interets_restent_non_deduits_sans_division_par_zero():
    c = cout_net_etat(_v(0.40, 0.0))
    assert c[2037] < 0
