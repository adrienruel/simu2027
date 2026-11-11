"""Programme Roussel (Parti communiste français) (11 novembre 2026, phase 3)."""

import pytest
import yaml

from moteur import noyau
from moteur import statu_quo as sq
from moteur.ecologie import emissions as em
from moteur.parametres import RACINE, Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def prog():
    return noyau.charger("roussel")


def test_programme_disponible_et_chiffre(p, prog):
    assert "roussel" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "roussel" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert all(m["traitement"] for m in fiche["mesures"])
    for cle, par in prog.pt._p.items():
        if cle.startswith(("roussel_mesures.", "roussel_ecologie.")):
            assert par.valeur["id"] in ids, cle


def test_sens_des_scenarios(prog):
    for cle, par in prog.pt._p.items():
        if not cle.startswith("roussel_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        assert v == sorted(v) if par.valeur["poste"] in ("recettes", "participations") else v == sorted(v, reverse=True), cle


def test_retraite_comme_melenchon(p, prog):
    m = noyau.charger("melenchon")
    assert prog.retraites(p, "prudent")["pensions"][2035] == pytest.approx(m.retraites(p, "prudent")["pensions"][2035])


def test_trente_deux_heures(p, prog):
    """32 heures : moins de production (heures non compensées), embauches de partage et embauches publiques."""
    ctx = prog.contexte(p)["prudent"]
    c = ctx["emplois_canaux"][2035]
    assert c["PCF-EMP-01 — 32 heures : embauches de partage du travail"] > 0 > c["PCF-EMP-01 — 32 heures : emplois perdus par le coût horaire"]
    assert prog.pib_en_plus[(id(p), "prudent")][2035] < 0


def test_emissions(p, prog):
    b = em.bilan(p, "prudent", prog.mesures(p)["prudent"], prog.contexte(p)["prudent"])
    assert b[2040]["effet_mesures"] < 0
