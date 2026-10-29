"""Réformes du supérieur et carrières (moteur/carrieres.py)."""
from moteur.carrieres import emplois_entree_plus_tot, prime_salaire
from moteur.cohortes import agregats, indices as indices_cohortes
from moteur.demographie import effectifs, indices
from moteur.parametres import Parametres


def test_entree_plus_tot_niveau():
    p = Parametres()
    e = emplois_entree_plus_tot(p, "prudent", 2040)
    assert set(e) == set(range(19, 24))
    # 3 % de 1,6 million d'années d'études × 50 % en emploi
    assert abs(sum(e.values()) - 24000) < 1
    assert sum(emplois_entree_plus_tot(p, "crise", 2040).values()) < sum(e.values())
    assert emplois_entree_plus_tot(p, "prudent", 2028) == {}


def test_montee():
    p = Parametres()
    assert abs(sum(emplois_entree_plus_tot(p, "prudent", 2029).values()) - 8000) < 1


def test_prime_nulle_en_prudent_et_crise():
    p = Parametres()
    for j in ("prudent", "crise"):
        assert prime_salaire(p, j, 2060, 30) == 0.0
    assert prime_salaire(p, "median", 2060, 30) > 0
    assert prime_salaire(p, "median", 2060, 60) == 0.0  # né en 2000, avant la réforme
    assert prime_salaire(p, "median", 2060, 21) == 0.0  # avant le diplôme


def test_desactive_neutre():
    p = Parametres().avec({"carrieres.active": False})
    assert emplois_entree_plus_tot(p, "prudent", 2040) == {}
    assert prime_salaire(p, "optimiste", 2060, 30) == 0.0


def test_effet_present_des_2029_dans_les_indices():
    p = Parametres()
    assert indices(p)[2029]["emploi"] > 1.0
    assert indices_cohortes(p)[2029]["impot"] > 1.0
    q = Parametres().avec({"carrieres.active": False})
    assert abs(indices(q)[2029]["emploi"] - 1.0) < 1e-12
    assert abs(indices_cohortes(q)[2029]["impot"] - 1.0) < 1e-12


def test_salaries_en_plus():
    p = Parametres()
    a, b = agregats(p)[2040], agregats(p, carrieres=False)[2040]
    assert 20000 < a["salaries"] - b["salaries"] < 24000  # × part des salariés dans l'emploi
    # un jeune pèse moins qu'un emploi moyen dans l'indice d'emploi
    d = effectifs(p)[2040]["emploi"] - effectifs(p, carrieres=False)[2040]["emploi"]
    assert 0.5 * 24000 < d < 0.7 * 24000
