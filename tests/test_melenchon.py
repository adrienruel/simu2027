"""Programme Mélenchon (L'Avenir en commun, 5e édition) et baisse de l'âge légal de la bibliothèque (6 novembre 2026)."""

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
    return noyau.charger("melenchon")


def test_programme_disponible_et_chiffre(p, prog):
    assert "melenchon" in noyau.programmes_disponibles()
    res = noyau.simuler(p, prog)
    assert set(res) == set(sq.SCENARIOS)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


def test_chaque_mesure_renvoie_a_la_fiche(prog):
    fiche = yaml.safe_load((RACINE / "programmes" / "melenchon" / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    for cle, par in prog.pt._p.items():
        if cle.startswith("melenchon_mesures."):
            assert par.valeur["id"] in ids, f"{cle} : {par.valeur['id']} absent de la fiche"


def test_sens_des_scenarios(prog):
    """Dépense : crise ≥ prudent ≥ médian ≥ optimiste ; recette : l'inverse (règle de prudence)."""
    for cle, par in prog.pt._p.items():
        if not cle.startswith("melenchon_mesures.") or not isinstance(par.valeur["montant"], dict):
            continue
        # superprofits : recette qui ne joue qu'en crise ; dépenses des communes : contrepartie exacte de la taxe
        # d'habitation (même montant que la recette, effet net nul)
        if cle.split(".")[1] in ("superprofits", "depenses_communes_th"):
            continue
        m = par.valeur["montant"]
        v = [m[s] for s in ("crise", "prudent", "median", "optimiste")]
        if par.valeur["poste"] in ("recettes", "participations"):
            assert v == sorted(v), cle
        else:
            assert v == sorted(v, reverse=True), cle


def test_baisse_age_retrouve_le_retour_a_62_ans_de_tondelier(p):
    t = noyau.charger("tondelier")
    pt = Parametres(programme="tondelier")
    ref = t.pensions_62(pt, "prudent")
    d = bib.baisse_age_legal_detail(pt, "prudent", {2028: t.v("retraites.profil_62_ans")})
    for a in (2029, 2040, 2060):
        assert d["pensions"][a] == pytest.approx(ref[a], rel=1e-9)
        assert d["retraites_en_plus"][a] == pytest.approx(-t._non_retraites[(id(pt), "prudent")][a], rel=1e-9)


def test_soixante_ans_coute_plus_que_62_ans(p, prog):
    d60 = prog.retraites(p, "prudent")["pensions"]
    d62 = bib.baisse_age_legal_detail(p, "prudent", {2028: prog.v("retraites.profil_62_ans")})["pensions"]
    # 2029 : passage de 62 à 60 ans déjà entamé (mélange des profils de 2028 à 2032)
    assert d62[2029] < d60[2029] < 1.6 * d62[2029]
    assert d60[2037] > 1.5 * d62[2037]


def test_aucune_recette_annoncee():
    """Le livre ne chiffre rien : aucune ligne ne porte le statut SOURCE pour un montant de recette ou d'économie."""
    prog = noyau.charger("melenchon")
    for cle, par in prog.pt._p.items():
        if cle.startswith("melenchon_mesures.") and par.valeur["poste"] == "recettes":
            assert par.statut != "SOURCE", cle


def test_mesures_de_2027_2028_dans_la_dette_de_depart(p, prog):
    ctx = prog.contexte(p)["prudent"]
    avant = prog._calcul(p)["details"]["prudent"]["avant_2029"]
    assert avant > 0
    assert ctx["dette_depart"] == pytest.approx(sq.dette_fin_2028(p) + avant)
    assert all(t in ctx["chomage"] for t in ANNEES)


def test_multiplicateur_en_miroir_pour_une_relance(p):
    """Décision du 07/11/2026 : une relance prend le multiplicateur du scénario miroir, un resserrement le sien."""
    from moteur.programme_simple import multiplicateur
    an = list(range(2028, 2040))
    relance = {t: 10.0 for t in an}
    resserrement = {t: -10.0 for t in an}
    m = {sc: sq._v(p, "macro.multiplicateur", sc) for sc in sq.SCENARIOS}
    assert multiplicateur(p, "optimiste", relance, an)[2028] == pytest.approx(10 * m["crise"])
    assert multiplicateur(p, "crise", relance, an)[2028] == pytest.approx(10 * m["optimiste"])
    assert multiplicateur(p, "crise", resserrement, an)[2028] == pytest.approx(-10 * m["crise"])
    # relance de même taille : l'optimiste donne au moins autant de PIB que le prudent, la crise au plus autant
    d = {sc: multiplicateur(p, sc, relance, an)[2030] for sc in sq.SCENARIOS}
    assert d["optimiste"] >= d["prudent"] >= d["crise"]


def test_trente_deux_heures_penibles(p, prog):
    """LFI-EMP-10 : 32 heures dans les métiers pénibles ou de nuit du privé (11/11/2026)."""
    ctx = prog.contexte(p)
    cle = "LFI-EMP-10 — 32 heures (métiers pénibles ou de nuit) : emplois perdus par le coût horaire"
    pr, op = ctx["prudent"]["emplois_canaux"][2035][cle], ctx["optimiste"]["emplois_canaux"][2035][cle]
    assert pr < op < 0
