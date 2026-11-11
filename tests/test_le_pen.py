"""Programme Le Pen (Rassemblement national), partiel (11 novembre 2026, phase 3)."""

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
    return noyau.charger("le_pen")


def test_programme_disponible_et_chiffre(p, prog):
    assert "le_pen" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "le_pen" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert all(m["traitement"] for m in fiche["mesures"])
    for cle, par in prog.pt._p.items():
        if cle.startswith(("le_pen_mesures.", "le_pen_ecologie.")):
            assert par.valeur["id"].rstrip("b") in ids, cle


def test_sens_des_scenarios(prog):
    for cle, par in prog.pt._p.items():
        if not cle.startswith("le_pen_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        assert v == sorted(v) if par.valeur["poste"] == "recettes" else v == sorted(v, reverse=True), cle


def test_economies_annoncees_non_reprises(p, prog):
    """140 Md€ annoncés : jamais repris ; les économies nommées sont estimées, l'enveloppe est le reste plafonné."""
    b = noyau.bilan_mesures(prog, p, "prudent", (2032,))
    economies = sum(x[2032] for x in b if x[2032] > 0 and x["nature"] == "mesure")
    assert economies < 40


def test_retour_a_62_ans_comme_glucksmann(p, prog):
    g = noyau.charger("glucksmann")
    assert prog.retraites(p, "prudent")["pensions"][2035] == pytest.approx(g.retraites(p, "prudent")["pensions"][2035])


def test_emissions_en_hausse(p, prog):
    b = em.bilan(p, "prudent", prog.mesures(p)["prudent"], prog.contexte(p)["prudent"])
    assert b[2037]["effet_mesures"] > 3
