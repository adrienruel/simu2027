"""Canal commun des naissances (moteur/naissances.py, 14/11/2026)."""
import pytest

from moteur import naissances, noyau
from moteur.parametres import Parametres


def _mesures(nom, p):
    return noyau.charger(nom).entrees(p, ("prudent",))["prudent"].mesures


def test_soutien_et_garde():
    p = Parametres()
    m = _mesures("philippe", p)
    assert naissances.soutien_par_enfant(p, "prudent", m) > 500
    assert naissances.points_couverture(p, "prudent", m) > 0
    assert naissances.effet(p, "prudent", m) > 0.05
    assert naissances.effet(p, "prudent", _mesures("zemmour", p)) < 0  # allocations familiales réservées
    assert naissances.effet(p, "prudent", _mesures("roussel", p)) == 0


def test_interrupteur_et_aidants():
    p = Parametres()
    m = _mesures("glucksmann", p)
    assert not any(naissances.est_soutien(x) for x in m if "aidants" in x.nom.lower())
    assert naissances.effet(p.avec({"demographie.naissances_communes": False}), "prudent", m) == 0


def test_conges_hors_soutien_monetaire():
    """Phase Q (20/11/2026) : un congé indemnisé remplace un salaire ; il ne compte pas comme soutien par enfant."""
    p = Parametres()
    for nom in ("melenchon", "tondelier", "retailleau"):
        m = _mesures(nom, p)
        conges = [x for x in m if x.enfants == "conge"]
        assert conges, nom
        sans = [x for x in m if x.enfants != "conge"]
        assert naissances.soutien_par_enfant(p, "prudent", m) == naissances.soutien_par_enfant(p, "prudent", sans)


@pytest.mark.lent
def test_garde_compte_les_places_au_cout_de_la_mesure():
    p = Parametres()
    for nom in noyau.programmes_disponibles():
        if nom == "statu_quo":
            continue
        for x in _mesures(nom, p):
            if x.enfants == "garde":
                assert x.cout_place > 0, x.nom
    m = _mesures("melenchon", p)
    assert not any(x.enfants == "garde" for x in m if "gratuites" in x.nom)  # qualité : pas de place en plus


def test_hausse_du_soutien_lit_le_scenario_miroir():
    """La semi-élasticité est définie pour une baisse : une hausse du soutien a l'effet le plus faible en crise."""
    p = Parametres()
    m = [x for x in _mesures("lisnard", p) if naissances.est_soutien(x)]
    assert naissances.soutien_par_enfant(p, "prudent", m) > 0
    sc = noyau.charger("lisnard").entrees(p, ("crise", "optimiste"))
    eff = {s: naissances.effet(p, s, sc[s].mesures) for s in sc}
    par_euro = {s: eff[s] / naissances.soutien_par_enfant(p, s, sc[s].mesures) for s in sc}
    assert par_euro["crise"] < par_euro["optimiste"]
