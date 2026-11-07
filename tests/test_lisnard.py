"""Programme Lisnard (Nouvelle Énergie) (7 novembre 2026)."""

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
    return noyau.charger("lisnard")


def test_programme_disponible_et_chiffre(p, prog):
    assert "lisnard" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "lisnard" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert len(ids) == 94 and all(m["traitement"] for m in fiche["mesures"])
    for cle, par in prog.pt._p.items():
        if cle.startswith("lisnard_mesures."):
            assert par.valeur["id"] in ids, cle


def test_sens_des_scenarios(prog):
    for cle, par in prog.pt._p.items():
        if not cle.startswith("lisnard_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        assert v == sorted(v) if par.valeur["poste"] == "recettes" else v == sorted(v, reverse=True), cle


def test_annonces_non_reprises(prog):
    """200 Md€ annoncés : les économies nommées restent bien en dessous ; 400 000 postes réalisés à 70 % en prudent."""
    eco = -sum(min(0.0, par.valeur["montant"]["prudent"]) for cle, par in prog.pt._p.items()
               if cle.startswith("lisnard_mesures.") and par.valeur["poste"] != "recettes")
    assert eco < 60
    postes = -sum(prog.v(f"mesures.postes_{k}")["montant"]["prudent"] for k in ("etat", "collectivites", "hopitaux"))
    assert postes * 1e9 / 55000 == pytest.approx(280000, rel=0.01)



def test_120_md_rendus_aux_actifs(p, prog):
    """CSG de 9,2 à 6,6 % et cotisations salariales : 120 Md€ bruts à pleine montée (2031)."""
    m = [x for x in prog.mesures(p)["prudent"] if x.nom.startswith(("LIS-ECO-02", "LIS-ECO-07"))
         and ("(privé)" in x.nom or "(agents publics)" in x.nom)]
    assert sum(x.valeurs[2031] for x in m) / prog.indices(p, "prudent")["pib"][2031] == pytest.approx(-120, rel=0.12)
    assert sum(x.valeurs[2029] for x in m) == pytest.approx(0.5 * sum(x.valeurs[2031] for x in m), rel=0.1)
