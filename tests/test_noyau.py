"""Noyau commun (moteur/noyau.py) : programme vide = statu quo ; « Écologie de droite » rebranché sur le noyau
retrouve exactement les résultats de son propre moteur."""

import pytest

from moteur import noyau, statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


def test_programme_vide_egale_statu_quo(p):
    vide = noyau.simuler(p, noyau.charger("vide"))
    ref = sq.simuler(p)
    for s in sq.SCENARIOS:
        for t in ANNEES:
            assert vide[s][t]["deficit"] == ref[s][t]["deficit"]
            assert vide[s][t]["dette"] == ref[s][t]["dette"]


def test_une_recette_ponctuelle(p):
    base = noyau.trajectoire(p, "prudent")
    avec = noyau.trajectoire(p, "prudent", [Mesure("essai", "recettes", {2030: 10.0})])
    assert avec[2029]["deficit"] == pytest.approx(base[2029]["deficit"])
    assert base[2030]["deficit"] - avec[2030]["deficit"] == pytest.approx(10 / base[2030]["pib"] * 100)
    assert avec[2031]["dette"] < base[2031]["dette"] - 10  # 10 Md€ de dette en moins, plus les intérêts évités


def test_poste_et_contexte_inconnus(p):
    with pytest.raises(ValueError, match="poste inconnu"):
        noyau.trajectoire(p, "prudent", [Mesure("essai", "ministere_imaginaire", {2030: 1.0})])
    with pytest.raises(ValueError, match="Contexte inconnu"):
        noyau.trajectoire(p, "prudent", contexte={"croissance": {}})
    noyau.trajectoire(p, "prudent", [Mesure("essai", "nouveau:revenu", {2030: 1.0})])  # bloc nouveau admis


@pytest.fixture(scope="module")
def ed(p):
    prog = noyau.charger("ecologie_de_droite")
    return prog, noyau.simuler(p, prog), prog.resultats_moteur(p)


def test_ecologie_de_droite_reproduite_par_le_noyau(ed):
    _, r, ref = ed
    for s in sq.SCENARIOS:
        for t in ANNEES:
            assert r[s][t]["deficit"] == pytest.approx(ref[s][t]["deficit"], abs=1e-9)
            assert r[s][t]["dette_pib"] == pytest.approx(ref[s][t]["dette_pib"], abs=1e-9)
            assert r[s][t]["interets_reels"] == pytest.approx(ref[s][t]["charge_dette"], abs=1e-6)


def test_bilan_des_mesures(ed, p):
    prog, r, _ = ed
    b = noyau.bilan_mesures(prog, p)
    natures = {x["nature"] for x in b}
    assert {"budget", "effet_macro"} <= natures
    # le budget du programme et ses effets macro expliquent tout l'écart de solde primaire avec le statu quo
    base = sq.simuler(p)["prudent"]
    for t in (2029, 2050):
        effet = sum(x[t] for x in b)
        assert effet == pytest.approx(r["prudent"][t]["solde_primaire"] - base[t]["solde_primaire"], abs=1e-6)
