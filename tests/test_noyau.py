"""Noyau commun (moteur/noyau.py) : programme vide = statu quo ; règle de trajectoire et dynamiques génériques."""

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


def test_regle_generique_du_noyau(p):
    """Règle et dynamique génériques : un levier de 5 Md€ de capacité, toujours entièrement utilisé avec une cible de
    0 % (le statu quo est en déficit) ; un levier sans limite ramène exactement à la cible de 3 %. Les comptes
    publient le déficit avec et sans règle."""
    from moteur.noyau import Levier, Regle

    class Rien:
        def debut(self, t, etat):
            return {"pib": 0.0}

        def fin(self, t, etat):
            pass
    base = noyau.trajectoire(p, "prudent")
    assert base[2029]["deficit"] > 3.5  # le cas testé suppose un statu quo au-dessus de la cible
    r1 = noyau.trajectoire(p, "prudent", regle=Regle(0.0, [Levier("petit", lambda t, e: 5.0)]), dynamiques=[Rien()])
    r2 = noyau.trajectoire(p, "prudent", regle=Regle(0.03, [Levier("grand", lambda t, e: 1e6)]), dynamiques=[Rien()])
    assert r1[2029]["deficit_avant_regle"] == pytest.approx(base[2029]["deficit"])
    assert r1[2029]["regle"]["leviers"]["petit"] == pytest.approx(5.0)
    assert r1[2029]["deficit"] == pytest.approx(base[2029]["deficit"] - 5.0 / base[2029]["pib"] * 100)
    assert r1[2029]["regle"]["reste_a_couvrir"] > 0
    assert all(r2[t]["deficit"] == pytest.approx(3.0, abs=1e-6) for t in ANNEES if r2[t]["deficit_avant_regle"] > 3.0)
    assert all(r2[t]["deficit"] <= r2[t]["deficit_avant_regle"] + 1e-9 for t in ANNEES)


def test_programmes_disponibles():
    """Le comparateur prend le statu quo et les programmes de programmes/publies.yaml."""
    noms = noyau.programmes_disponibles()
    assert noms[0] == "statu_quo" and len(noms) == 12
    # Bertrand : retiré le 28/11/2026 (plus en campagne), gardé comme programme de test
    assert set(noyau.programmes_disponibles(tous=True)) == set(noms) | {"bertrand"}


def test_variante_fonds_commune_aux_programmes(p):
    """Règle commune (15/11/2026) : l'argent public versé à un fonds de capitalisation est consolidé quand le fonds
    est compté dans les APU (Philippe : abondement de l'État ; Retailleau : part des employeurs publics)."""
    from moteur import fonds_apu
    for nom, bas, haut in (("philippe", 3.0, 11.0), ("retailleau", 0.05, 1.0)):
        prog = noyau.charger(nom)
        v = fonds_apu.variante(p, prog, ("prudent",))["prudent"]
        assert bas < -v["deplace"][2037] < haut
        assert v["apu"][2037]["pib"] == pytest.approx(v["publie"][2037]["pib"], rel=1e-3)
        assert v["apu"][2037]["deficit"] < v["publie"][2037]["deficit"]
    assert fonds_apu.a_un_fonds(noyau.charger("bertrand"), p)  # lecture commune de la capitalisation (16/11/2026)
    assert not fonds_apu.a_un_fonds(noyau.charger("attal"), p)
