"""Programme Tondelier sur le noyau (5 novembre 2026)."""

import pytest
import yaml

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import RACINE, Parametres


@pytest.fixture(scope="module")
def prog():
    return noyau.charger("tondelier")


@pytest.fixture(scope="module")
def p():
    return Parametres()


def test_programme_disponible():
    assert "tondelier" in noyau.programmes_disponibles()


def test_chaque_mesure_renvoie_a_la_fiche(prog):
    """Chaque mesure chiffrée renvoie à un identifiant de la fiche des mesures (mesures.yaml, citations vérifiées)."""
    fiche = yaml.safe_load((RACINE / "programmes" / "tondelier" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    for nom, par in prog.pt._p.items():
        if nom.startswith("tondelier_mesures."):
            for i in par.valeur["id"].split("/"):
                i = i if "-" in i else par.valeur["id"].split("-")[0] + "-" + i
                assert i in ids, f"{nom} : {i} absent de la fiche"


def test_aucune_recette_annoncee_reprise(prog):
    """Règle des autres candidats : la recette annoncée sur les successions (15 Md€) n'est pas saisie."""
    m = prog.pt.val("tondelier_mesures.successions")["montant"]
    assert max(m.values()) < 15


def test_smic(prog, p):
    s = prog.smic(p)
    assert s["hausse_brut_smic"] == pytest.approx(2000 / 1.013 / 1823.03 - 1, abs=0.01)
    # allègements nominalisés : le coût au SMIC monte plus que le brut
    assert s["hausse_cout_smic"] > s["hausse_brut_smic"]
    assert 0 < s["prelevements"] < 20


def test_retour_a_62_ans_coute_et_se_stabilise(prog, p):
    c = prog.pensions_62(p, "prudent")
    # relecture neutre du 11/11/2026 (âge légal réel des générations) : ≈ 15 Md€ en 2029, chiffrages publics 10 à 20
    assert 10 < c[2029] < 25
    assert c[2050] > 0


def test_mesures_sur_des_postes_connus(prog, p):
    res = noyau.simuler(p, prog)
    assert set(res) == set(sq.SCENARIOS)
    # le programme creuse le déficit par rapport au statu quo dans le prudent
    base = sq.simuler(p)
    assert res["prudent"][2037]["solde_primaire"] < base["prudent"][2037]["solde_primaire"]
