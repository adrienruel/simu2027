"""Phase E de la roadmap (14/11/2026) : macro bouclée (moteur/bouclage.py)."""
from __future__ import annotations

import pytest

from moteur import bouclage, noyau, statu_quo as sq
from moteur.parametres import Parametres
from moteur.programme_simple import TOUTES, multiplicateur
from outils.banc_mesange import ANS, MESANGE, banc


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def resultats_banc():
    return banc()


def test_reponse_unitaire_normalisee(p):
    u = bouclage.reponses_unitaires(p)
    assert max(u["pib"]) == pytest.approx(1.0)
    assert u["pic"] == 1  # effet maximal la deuxième année, comme Mésange
    assert 0.1 < u["pib"][-1] < 0.3  # part gardée à long terme (Mésange : 0,16)
    assert u["prix"][10] > 0  # la demande fait monter les prix


def test_critere_sortie_depense(resultats_banc):
    """Critère de sortie de la phase E : dépense publique d'un point de PIB, Mésange à 30 % près (ici 10 %)."""
    for a, c in zip(ANS, MESANGE["depense"]):
        assert abs(resultats_banc["depense"][a]["pib"] - c) <= 0.10 * c


def test_critere_sortie_cotisations(resultats_banc):
    """Baisse des cotisations employeurs d'un point de PIB (demande bouclée + canal d'offre) : 30 % près ; prix en
    baisse, comme Mésange."""
    for a, c in zip(ANS, MESANGE["cotisations_employeurs"]):
        assert abs(resultats_banc["cotisations_employeurs"][a]["pib"] - c) <= 0.10 * c
        assert resultats_banc["cotisations_employeurs"][a]["prix"] < 0


def test_critere_sortie_investissement_public(resultats_banc):
    """Investissement public : 10 % près sur tous les horizons (effet d'impact de l'accélérateur,
    bouclage.investissement_impact ; capital public en plus de la demande, capital.capital_public)."""
    for a, c in zip(ANS, MESANGE["investissement_public"]):
        assert abs(resultats_banc["investissement_public"][a]["pib"] - c) <= 0.10 * c


@pytest.mark.parametrize("nom", ["tva", "csg", "impot_revenu", "cotisations_employeurs"])
def test_profils_mesange(resultats_banc, nom):
    """Impôts à profil de Mésange (demande + canal d'offre) : 10 % près ; prix du même signe que Mésange."""
    from outils.banc_mesange import PRIX_MESANGE
    for a, c, pr in zip(ANS, MESANGE[nom], PRIX_MESANGE[nom]):
        assert abs(resultats_banc[nom][a]["pib"] - c) <= 0.10 * abs(c)
        assert resultats_banc[nom][a]["prix"] * pr > 0


def test_balance_courante(p):
    """E4 : la balance courante retire de la balance commerciale les intérêts en plus versés aux non-résidents."""
    r = noyau.simuler(p, noyau.charger("melenchon"), scenarios=["prudent"], contrefactuel=False)["prudent"]
    base = noyau.simuler(p, None, scenarios=["prudent"])["prudent"]
    t = 2037
    d = (r[t]["charge_dette"] - base[t]["charge_dette"]) / r[t]["pib"] * 100
    assert r[t]["balance_courante"] == pytest.approx(r[t]["balance_commerciale"] - 0.56 * d)


def test_sans_bouclage_ancien_calcul():
    """macro.bouclage faux : forme linéaire d'avant, à l'identique, et aucun contexte bouclé."""
    q = Parametres().avec({"macro.bouclage": False})
    cout = {t: (10.0 if t >= 2029 else 0.0) for t in TOUTES}
    d = multiplicateur(q, "prudent", cout, TOUTES)
    m, n = sq._v(q, "macro.multiplicateur", "median"), sq._v(q, "macro.annees_effet_ajustement", "median")
    assert d[2029] == pytest.approx(m * 10)
    assert d[2031] == pytest.approx(m * 10 * (1 - 2 / n))
    assert bouclage.contexte(q, "prudent", {"inflation": {}, "inflation_taux": {}, "taux_marche": {}}) == {}


def test_miroir_relance_resserrement(p):
    """Le sens compte : une relance prend le multiplicateur du scénario miroir, un resserrement celui du scénario."""
    cout = {t: (10.0 if t >= 2029 else 0.0) for t in TOUTES}
    relance = bouclage.reponse(p, "optimiste", cout, TOUTES)["dpib_avant_capacite"]
    resserr = bouclage.reponse(p, "optimiste", {t: -v for t, v in cout.items()}, TOUTES)["dpib_avant_capacite"]
    m_crise, m_opt = sq._v(p, "macro.multiplicateur", "crise"), sq._v(p, "macro.multiplicateur", "optimiste")
    assert relance[2030] == pytest.approx(-resserr[2030] * m_crise / m_opt)


def test_statu_quo_inchange(p):
    """Le programme vide reste le statu quo : le bouclage ne joue que sur les écarts des programmes."""
    a = noyau.simuler(p, None, scenarios=["prudent"])["prudent"]
    b = noyau.simuler(p.avec({"macro.bouclage": False}), None, scenarios=["prudent"])["prudent"]
    for t in (2029, 2037, 2050, 2073):
        assert a[t]["deficit"] == pytest.approx(b[t]["deficit"], abs=1e-12)


def test_inflation_allege_dette_nominale(p):
    """Une hausse des prix due au programme allège la dette réelle : à solde égal, la dette baisse."""
    base = noyau.trajectoire(p, "prudent")
    infl = sq.inflation(p, "prudent")
    choc = {t: infl[t] + (0.01 if t == 2030 else 0.0) for t in noyau.ANNEES}
    r = noyau.trajectoire(p, "prudent", contexte={"inflation": choc, "inflation_taux": infl})
    assert r[2031]["dette"] < base[2031]["dette"]


def test_prime_de_dette_pese_sur_le_pib(p):
    """E1 : un programme dont le taux de marché dépasse celui du statu quo perd du PIB ; le statu quo n'en perd pas."""
    base = noyau.simuler(p, None, scenarios=["prudent"])["prudent"]
    assert all(base[t]["pib_taux"] == 0.0 for t in noyau.ANNEES)
    r = noyau.simuler(p, noyau.charger("melenchon"), scenarios=["prudent"], contrefactuel=False)["prudent"]
    assert r[2035]["ecart_marche"] > base[2035]["ecart_marche"]
    assert r[2035]["pib_taux"] < 0
    q = p.avec({"macro.bouclage_prime_demande": False})
    r0 = noyau.simuler(q, noyau.charger("melenchon"), scenarios=["prudent"], contrefactuel=False)["prudent"]
    assert r0[2035]["pib_taux"] == 0.0 and r0[2037]["deficit"] < r[2037]["deficit"]


def test_pensions_en_retard_sur_les_prix(p):
    """E2 : l'inflation due au programme fait perdre aux pensions ce pouvoir d'achat l'année même."""
    infl = sq.inflation(p, "prudent")
    choc = {t: (0.01 if t == 2031 else 0.0) for t in noyau.ANNEES}
    r = noyau.trajectoire(p, "prudent", contexte={"inflation": {t: infl[t] + choc[t] for t in noyau.ANNEES},
                                                  "inflation_taux": infl, "inflation_bouclage": choc})
    bl = sq.blocs(p, "prudent")
    assert r[2031]["erosion_pensions"] == pytest.approx(0.01 * bl[2031]["retraites"])
    assert r[2032]["erosion_pensions"] == 0.0


def test_balance_commerciale_mesange():
    """E4 : la relation publiée retrouve la balance commerciale des variantes de Mésange à 0,08 point près."""
    e = Parametres().val("bouclage.exterieur")
    cas = {  # (PIB %, prix %, balance Mésange) à 1, 5 et 10 ans
        "depense": [(0.78, 0.20, -0.30), (0.86, 1.42, -0.62), (0.53, 1.88, -0.71)],
        "investissement": [(1.31, 0.31, -0.52), (0.93, 1.86, -0.78), (0.57, 2.25, -0.86)],
        "cotisations": [(0.20, -0.36, -0.04), (0.97, -1.09, 0.00), (1.29, -1.32, 0.03)],
    }
    for lignes in cas.values():
        for y, pr, b in lignes:
            assert abs(-e["alpha"] * y - e["beta"] * pr - b) <= 0.085
    base = noyau.simuler(Parametres(), None, scenarios=["prudent"])["prudent"]
    assert base[2037]["balance_commerciale"] == 0.0


def test_critere_sortie_petrole(resultats_banc):
    """Hausse de 10 $ du baril (facture +0,2 point de PIB) : 30 % près à partir de la deuxième année (première année :
    effet d'impact trop fort, +36 %, la forme de demande commune montant plus vite que celle du pétrole dans Mésange)."""
    for a, c in zip(ANS[1:], MESANGE["petrole"][1:]):
        assert abs(resultats_banc["petrole"][a]["pib"] - c) <= 0.30 * abs(c)


def test_facture_energie_suit_les_tonnes(p):
    """E4 : une tonne de CO2 fossile évitée par une mesure allège la facture d'importation ; agriculture hors champ."""
    from moteur.noyau import Mesure
    k = p.val("bouclage.energie_importee")["md_par_mt"]
    m = [Mesure("rail", "recettes", {}, "physique", physique={"emissions_mt:transports": {2035: -10.0}}),
         Mesure("élevage", "recettes", {}, "physique", physique={"emissions_mt:agriculture": {2035: -10.0}})]
    fe = bouclage.facture_energie(p, m, noyau.ANNEES)
    assert fe[2035] == pytest.approx(-10 * k) and fe[2034] == 0.0


def test_emploi_de_conjoncture_revient_a_l_equilibre(p):
    """E6 : une dépense permanente crée des emplois qui disparaissent en une dizaine d'années (Mésange : 107 000 à
    3 ans, −8 000 à 10 ans), alors que le PIB reste plus haut ; les baisses d'impôt sur le travail gardent leurs
    emplois (salaires)."""
    from outils.banc_mesange import variante
    q = p.avec({"bouclage.bce/active": False})
    q.__dict__.pop("_cache", None)
    y = sq.pib(q, "median")
    un = {t: 0.01 * y[max(t, 2029)] for t in TOUTES}
    from moteur.noyau import Mesure
    from moteur import offre
    dep = bouclage.reponse(q, "median", offre.impulsion(q, [Mesure("d", "etat_missions", un)], TOUTES), TOUTES)
    assert 90_000 < dep["emplois"][2029] < 120_000 and abs(dep["emplois"][2036]) < 15_000
    assert dep["dpib"][2036] > 0.4 / 100 * y[2036]
    m = [Mesure("CSG", "recettes", {t: -v for t, v in un.items()}, instrument="travail")]
    csg = bouclage.reponse(q, "median", offre.impulsion(q, m, TOUTES), TOUTES, m)
    of = offre.effets(q, "median", m)
    total = csg["emplois"][2036] + sum(s.get(2036, 0.0) for s in of["emplois"].values())
    assert total == pytest.approx(151_000 * sq.effectifs(q, "median")[2036]["emploi"] / sq.effectifs(q, "median")[2029]["emploi"], rel=0.10)
