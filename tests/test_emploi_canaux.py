"""Bloc emploi unifié."""
import pytest

from moteur.emploi import effets_reformes
from moteur.emploi_canaux import CANAUX, emplois_par_mesure, gain_au_cout, gains_par_canal
from moteur.parametres import Parametres

P = Parametres()


def test_somme_des_mesures_egale_total():
    e, m = effets_reformes(P), emplois_par_mesure(P)
    for j in ("crise", "median", "optimiste"):
        assert sum(m[j].values()) == pytest.approx(e[j]["emplois"], rel=1e-12)


def test_chaque_mesure_a_un_canal():
    m = emplois_par_mesure(P)
    assert set(m["crise"]) == set(CANAUX)
    assert set(CANAUX.values()) <= set(P.val("emploi.cout_par_canal"))


def test_gain_croissant_avec_le_salaire():
    g = [gain_au_cout(c, P, "prudent") for c in (23000, 35000, 50000, 80000)]
    assert all(b > a for a, b in zip(g, g[1:]))
    gc = gains_par_canal(P, "prudent")
    assert gc["localisation"] > gc["cout_travail"]


def test_taux_effectif_moyen():
    from moteur.taux_effectifs import eatr, eatr_actuel, eatr_nouveau
    # déduction immédiate : seule la rente est taxée, EATR = τ (p − r) / p
    assert eatr(0.45, 1.0, 0.20, 0.03, 0.10) == pytest.approx(0.45 * 0.17 / 0.20)
    # sans déduction meilleure qu'aujourd'hui, le taux effectif dépasse le taux légal (amortissements lents)
    assert eatr(0.45, 0.742, 0.20, 0.03, 0.10) > 0.45
    assert eatr_actuel(P) < eatr_nouveau(P, "prudent") < 0.45
    assert eatr_nouveau(P, "optimiste") < eatr_nouveau(P, "crise")
