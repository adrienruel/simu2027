"""Programme Philippe (Horizons) (7 novembre 2026)."""

import pytest
import yaml

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import RACINE, Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def prog():
    return noyau.charger("philippe")


def test_programme_disponible_et_chiffre(p, prog):
    assert "philippe" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "philippe" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert len(ids) == 91 and all(m["traitement"] for m in fiche["mesures"])
    for cle, par in prog.pt._p.items():
        if cle.startswith("philippe_mesures."):
            assert par.valeur["id"] in ids, cle


def test_sens_des_scenarios(prog):
    for cle, par in prog.pt._p.items():
        if not cle.startswith("philippe_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        assert v == sorted(v) if par.valeur["poste"] == "recettes" else v == sorted(v, reverse=True), cle


def test_aides_aux_entreprises_sous_l_annonce(prog):
    """50 Md€ d'aides supprimées annoncés : 70 % en prudent ; la baisse d'impôts de production est la mesure, entière."""
    a = sum(prog.v(f"mesures.aides_entreprises_{k}")["montant"]["prudent"] for k in ("travail", "capital"))
    b = sum(prog.v(f"mesures.impots_production_{k}")["montant"]["prudent"] for k in ("travail", "capital"))
    assert a == pytest.approx(35) and b == pytest.approx(-50)


def test_retraite_a_65_ans_fait_des_seniors_en_emploi(p, prog):
    c = prog.contexte(p)["prudent"]["emplois_canaux"][2040]
    assert c["Seniors : emploi (âge de la retraite)"] > 30000
