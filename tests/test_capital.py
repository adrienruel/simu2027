"""Phase E5 (14/11/2026) : stock de capital commun (moteur/capital.py)."""
import pytest

from moteur import capital, offre, statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres
from moteur.programme_simple import TOUTES

P = Parametres()


def test_stock_de_long_terme():
    """À long terme : capital en plus = élasticité × baisse du coût × investissement / usure ; PIB = capital × (rendement
    net + usure), la valeur d'un euro de capital des cohortes d'Écologie de droite."""
    s = "prudent"
    r = capital.accumuler(P, s, {t: -0.01 for t in TOUTES}, TOUTES)
    el, us = sq._v(P, "macro.elasticite_invest", s), sq._v(P, "macro.usure_capital", s)
    y = sq.pib(P, s)
    inv = P.val("is_investissement.investissement_snf_2025") * y[2073] / y[2029]
    g = y[2073] / y[2072] - 1  # l'investissement suit le PIB : capital = flux / (usure + croissance)
    assert r["capital"][2073] == pytest.approx(el * 0.01 * inv / (us + g), rel=0.02)
    assert r["pib"][2073] == pytest.approx(r["capital"][2073] * (sq._v(P, "macro.pib_par_euro_capital", s) + us))


def test_miroir_pour_une_hausse():
    """Une hausse du coût du capital prend l'élasticité du scénario miroir (phase A4)."""
    s = "prudent"
    baisse = capital.accumuler(P, s, {t: -0.01 for t in TOUTES}, TOUTES)["flux"][2040]
    hausse = capital.accumuler(P, s, {t: 0.01 for t in TOUTES}, TOUTES)["flux"][2040]
    el_s, el_m = sq._v(P, "macro.elasticite_invest", s), sq._v(P, "macro.elasticite_invest", "median")
    assert hausse == pytest.approx(-baisse * el_m / el_s)


def test_baisse_is_33_a_25():
    """Contrôle : la baisse de l'IS de 33,3 à 25 % (coût du capital −3,8 %) donne de l'ordre de 0,25 % de PIB à long
    terme, ce que donne la valeur ajoutée des SNF × taux de marge (32,2 %) × capital en plus."""
    z = P.val("is_investissement.valeur_actuelle_amortissements")
    d = ((1 - 0.25 * z) / 0.75) / ((1 - 0.3333 * z) / 0.6667) - 1
    r = capital.accumuler(P, "median", {t: d for t in TOUTES}, TOUTES)
    pct = r["pib"][2073] / sq.pib(P, "median")[2073] * 100
    assert 0.15 < pct < 0.35


def test_canal_offre_utilise_le_stock_commun():
    y = sq.pib(P, "prudent")
    m = [Mesure("IS", "recettes", {t: -0.01 * y[max(t, 2029)] for t in TOUTES}, instrument="capital_entreprises")]
    neuf = offre.effets(P, "prudent", m)["dpib"][2073]
    ancien = offre.effets(P.avec({"macro.capital_commun": False}), "prudent", m)["dpib"][2073]
    assert neuf == pytest.approx(capital.effet_fiscal(P, "prudent", {t: 1.0 for t in TOUTES}, TOUTES)["pib"][2073])
    assert 1.8 < ancien / neuf < 2.8  # l'ancien calcul comptait environ deux fois plus
