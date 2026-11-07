"""Programme Attal (Renaissance, site de campagne et lettre du 15/10/2026) (7 novembre 2026)."""

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
    return noyau.charger("attal")


def test_programme_disponible_et_chiffre(p, prog):
    assert "attal" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "attal" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert len(ids) == 106 and all(m["traitement"] for m in fiche["mesures"])
    for cle, par in prog.pt._p.items():
        if cle.startswith("attal_mesures."):
            assert par.valeur["id"] in ids, cle
    # les propositions du seul parti ne sont pas chiffrées
    parti = [m["id"] for m in fiche["mesures"] if m["source"].startswith(("Convention", "Pétition"))]
    chiffrees = {par.valeur["id"] for cle, par in prog.pt._p.items() if cle.startswith("attal_mesures.")}
    assert parti and not set(parti) & chiffrees


def test_sens_des_scenarios(prog):
    for cle, par in prog.pt._p.items():
        if not cle.startswith("attal_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        assert v == sorted(v) if par.valeur["poste"] == "recettes" else v == sorted(v, reverse=True), cle


def test_economies_annoncees_non_reprises(prog):
    """150 Md€ annoncés : les économies nommées et chiffrées restent bien en dessous."""
    eco = -sum(min(0.0, par.valeur["montant"]["prudent"]) for cle, par in prog.pt._p.items()
               if cle.startswith("attal_mesures.") and par.valeur["poste"] != "recettes")
    assert eco < 30
    assert prog.v("mesures.assurance_chomage")["montant"]["prudent"] > -5


def test_droit_au_brut_et_annee_blanche(p, prog):
    m = {x.nom: x for x in prog.mesures(p)["prudent"]}
    cot = sum(x.valeurs[2030] for n, x in m.items() if n.startswith("ATT-ECO-01") and ("(privé)" in n or "(agents" in n))
    assert -55 < cot < -40
    pens = next(x for n, x in m.items() if "pensions non revalorisées" in n)
    assert pens.valeurs[2029] < 0 and abs(pens.valeurs[2060]) < 0.25 * abs(pens.valeurs[2029])
