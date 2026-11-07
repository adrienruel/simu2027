"""Programme Glucksmann (Place publique, « Acte I » et débats de 2026) (7 novembre 2026)."""

import pytest
import yaml

from moteur import bibliotheque as bib
from moteur import noyau
from moteur import statu_quo as sq
from moteur.noyau import ANNEES
from moteur.parametres import RACINE, Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def prog():
    return noyau.charger("glucksmann")


def test_programme_disponible_et_chiffre(p, prog):
    assert "glucksmann" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    assert set(res) == set(sq.SCENARIOS)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_fiche_complete_et_mesures_renvoyees():
    """112 mesures recensées (plus les lignes « b ») ; chaque ligne chiffrée renvoie à la fiche."""
    fiche = yaml.safe_load((RACINE / "programmes" / "glucksmann" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    assert len({i for i in ids if not i.endswith("b")}) == 112
    assert all(m["traitement"] for m in fiche["mesures"])
    prog = noyau.charger("glucksmann")
    for cle, par in prog.pt._p.items():
        if cle.startswith("glucksmann_mesures."):
            assert par.valeur["id"] in ids, cle


def test_sens_des_scenarios(prog):
    """Dépense : crise ≥ prudent ≥ médian ≥ optimiste ; recette : l'inverse."""
    for cle, par in prog.pt._p.items():
        if not cle.startswith("glucksmann_mesures."):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        if par.valeur["poste"] == "recettes":
            assert v == sorted(v), cle
        else:
            assert v == sorted(v, reverse=True), cle


def test_recette_des_successions_sous_l_annonce(prog):
    """Le candidat attend ≈ 15 Md€ des très gros héritages : rien de tel n'est saisi."""
    m = prog.v("mesures.grosses_successions")["montant"]
    assert m["prudent"] < 15 / 3 and m["optimiste"] < 15
    for cle, par in prog.pt._p.items():
        if cle.startswith("glucksmann_mesures.") and par.valeur["poste"] == "recettes":
            assert par.statut != "SOURCE", cle


def test_baisse_de_csg_fraction_de_la_suppression(p, prog):
    """15 Md€ de CSG en moins sur les revenus d'activité, impôt sur le revenu et prestations en sens inverse."""
    m = {x.nom: x.valeurs[2029] for x in prog.mesures(p)["prudent"] if x.nom.startswith("GLU-FIS-01b")}
    csg = sum(v for n, v in m.items() if "(privé)" in n or "(agents publics)" in n)
    assert -17 < csg < -14
    assert 0 < sum(v for n, v in m.items() if "impôt" in n) < 4


def test_retraite_a_62_ans_comme_tondelier(p, prog):
    d = prog.retraites(p, "prudent")
    ref = bib.baisse_age_legal_detail(p, "prudent", {2028: prog.v("retraites.profil_62_ans")})
    assert d["pensions"][2040] == pytest.approx(ref["pensions"][2040])
    c = prog.contexte(p)["prudent"]["emplois_canaux"][2040]
    assert -400000 < c["Seniors : emploi (âge de la retraite)"] < -200000


def test_service_civique_ne_fait_pas_de_chomeurs(p, prog):
    """Les jeunes en service civique quittent l'emploi sans devenir chômeurs."""
    q = p
    g = noyau.charger("glucksmann")
    ctx = g.contexte(q)["prudent"]
    sc = ctx["emplois_canaux"][2035]["Service civique obligatoire : jeunes retirés de l'emploi"]
    assert -200000 < sc < -50000
    assert g.actifs_en_plus[(id(q), "prudent")][2035] == pytest.approx(sc)
