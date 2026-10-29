"""Module de population, places de crèche et pensions de l'ancien système par génération."""
import pytest

from moteur import demographie
from moteur.ancien_systeme import serie
from moteur.parametres import Parametres

P = Parametres()


def test_population_insee_totaux():
    """Totaux publiés par l'Insee (Insee Première n° 2108) : 69,08 millions en 2026, 65,89 en 2070 (central)."""
    pop = demographie._projection("central")
    assert sum(pop[2026]) / 1e6 == pytest.approx(69.082, abs=0.01)
    assert sum(pop[2070]) / 1e6 == pytest.approx(65.887, abs=0.01)
    assert sum(demographie._projection("fec_basse")[2070]) < sum(pop[2070]) < sum(demographie._projection("fec_haute")[2070])


def test_indices_valent_un_en_2029_et_sans_module():
    assert all(v == pytest.approx(1.0) for v in demographie.indices(P)[2029].values())
    sans = P.avec({"demographie.active": False})
    assert all(v == 1.0 for t in (2040, 2073) for v in demographie.indices(sans)[t].values())


def test_effet_natalite_suit_le_soutien():
    """Plus de soutien par enfant, plus de naissances ; des crèches en plus, plus de naissances."""
    base = demographie.effet_naissances(P)
    assert demographie.effet_naissances(P.avec({"rui_complements.part_enfant": 0.30})) > base
    assert demographie.effet_naissances(P.avec({"famille.creches_nouvelles/points_couverture": 0.0})) < base


def test_ancien_systeme_cale_en_2029_et_s_eteint():
    s = serie(P)
    assert s[2029]["depenses_md"] == pytest.approx(428.007695, rel=1e-9)
    assert s[2029]["retraites_millions"] == pytest.approx(19.15, rel=1e-9)
    annees = list(range(2044, 2074))
    assert all(s[a]["depenses_md"] > s[a + 1]["depenses_md"] for a in annees[:-1])
    assert s[2073]["depenses_md"] < 0.05 * s[2029]["depenses_md"]  # nés en 1978 ou avant : 95 ans ou plus en 2073


def test_droits_geles_coutent_moins():
    geles = serie(P.avec({"ancien_systeme.droits_geles_des_2029": True}))
    s = serie(P)
    assert all(geles[t]["depenses_md"] <= s[t]["depenses_md"] + 1e-9 for t in range(2029, 2074))


def test_v235_garde_la_serie_du_cor():
    v = Parametres(reference="v235")
    assert not v.val("demographie.active")
    assert serie(v)[2050]["depenses_md"] == pytest.approx(348.974448 * 0.776825, rel=1e-6)
