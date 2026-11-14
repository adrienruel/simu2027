"""Canal commun des naissances (moteur/naissances.py, 14/11/2026)."""
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
