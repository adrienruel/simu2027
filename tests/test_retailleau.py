"""Programme Retailleau (Les Républicains) (7 novembre 2026)."""

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
    return noyau.charger("retailleau")


def test_programme_disponible_et_chiffre(p, prog):
    assert "retailleau" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "retailleau" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert len(ids) == 98 and all(m["traitement"] for m in fiche["mesures"])
    for cle, par in prog.pt._p.items():
        if cle.startswith("retailleau_mesures."):
            assert par.valeur["id"] in ids, cle


def test_sens_des_scenarios(prog):
    for cle, par in prog.pt._p.items():
        if not cle.startswith("retailleau_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        assert v == sorted(v) if par.valeur["poste"] == "recettes" else v == sorted(v, reverse=True), cle


def test_annonces_non_reprises(prog):
    """197 Md€ annoncés : les économies nommées restent bien en dessous ; 400 000 postes réalisés à 70 % en prudent."""
    eco = -sum(min(0.0, par.valeur["montant"]["prudent"]) for cle, par in prog.pt._p.items()
               if cle.startswith("retailleau_mesures.") and par.valeur["poste"] != "recettes")
    assert eco < 60
    postes = -sum(prog.v(f"mesures.postes_{k}")["montant"]["prudent"] for k in ("etat", "collectivites", "hopitaux"))
    assert postes * 1e9 / 55000 == pytest.approx(280000, rel=0.01)
    assert prog.v("mesures.assurance_chomage")["montant"]["prudent"] > -8


def test_retraite_fait_des_seniors_en_emploi(p, prog):
    c = prog.contexte(p)["prudent"]["emplois_canaux"][2040]
    assert c["Seniors : emploi (âge de la retraite)"] > 20000
