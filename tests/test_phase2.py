"""Phase 2 de la roadmap (11/11/2026) : émissions des cinq derniers programmes, capitalisation de Retailleau,
taxe plastique de Tondelier, effets d'offre de l'éducation et de la recherche."""
import pytest

from moteur import noyau, offre
from moteur.ecologie import emissions as em
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.mark.parametrize("nom,signe", [("glucksmann", -1), ("philippe", -1), ("attal", -1),
                                       ("retailleau", 1), ("lisnard", 1)])
def test_emissions_des_cinq_programmes(p, nom, signe):
    """Chaque programme a des effets en tonnes ; Retailleau et Lisnard (fin du soutien aux renouvelables, de
    MaPrimeRénov' ou des ZFE) émettent plus que le statu quo, les trois autres moins."""
    prog = noyau.charger(nom)
    b = em.bilan(p, "prudent", prog.mesures(p)["prudent"], prog.contexte(p)["prudent"])
    assert signe * b[2037]["effet_mesures"] > 0.05


def test_emissions_ordre_des_scenarios(p):
    """Prudent : l'effet favorable au climat est le plus faible (Glucksmann), l'effet défavorable le plus fort
    (Retailleau)."""
    for nom in ("glucksmann", "retailleau"):
        prog = noyau.charger(nom)
        m, c = prog.mesures(p), prog.contexte(p)
        pr = em.bilan(p, "prudent", m["prudent"], c["prudent"])[2040]["effet_mesures"]
        me = em.bilan(p, "median", m["median"], c["median"])[2040]["effet_mesures"]
        assert pr > me  # plus d'émissions (ou moins de baisse) dans le prudent


def test_capitalisation_retailleau(p):
    """1 % du brut des entrants : hors budget sauf les employeurs publics ; emplois perdus par le coût du travail."""
    r = noyau.charger("retailleau")
    out, emplois = r.capitalisation(p, "prudent")
    assert 0.1 < out[0].valeurs[2037] < 0.5
    assert emplois[2050] < emplois[2037] < 0


def test_taxe_plastique_tondelier(p):
    t = noyau.charger("tondelier")
    noms = [m.nom for m in t.mesures(p)["prudent"]]
    assert any(n.startswith("REC-46") for n in noms)


def test_education_et_recherche(p):
    """Effets de long terme : nuls au début, croissants ensuite ; une baisse prend le scénario miroir."""
    plus = [Mesure("e", "etat_missions", {t: 5.0 for t in ANNEES}, instrument="education"),
            Mesure("r", "etat_missions", {t: 5.0 for t in ANNEES}, instrument="recherche")]
    d = offre.effets(p, "prudent", plus, annees_avant=())["detail"]
    e, r = d["education"]["effet_pib_pct"], d["recherche"]["effet_pib_pct"]
    assert abs(e[2030]) < 0.01 and e[2073] > e[2050] > e[2040] > 0
    assert r[2031] == 0 and r[2050] > r[2035] > 0
    moins = [Mesure("e", "etat_missions", {t: -5.0 for t in ANNEES}, instrument="education")]
    m = offre.effets(p, "prudent", moins, annees_avant=())["detail"]["education"]["effet_pib_pct"]
    assert -m[2073] > e[2073]  # baisse : scénario miroir (médian), perte plus forte que le gain du prudent
