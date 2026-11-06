"""Canal d'offre commun (6 novembre 2026)."""

import pytest

from moteur import noyau, offre
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


def _baisse(instrument, md=-30.0, poste="recettes"):
    return Mesure("essai", poste, {t: md for t in (2027, 2028, *ANNEES)}, instrument=instrument)


def test_baisse_et_hausse_symetriques_au_miroir_pres(p):
    """Baisse d'impôt : élasticité du scénario ; hausse : celle du scénario miroir (prudent → médian)."""
    y = sq.pib(p, "prudent")
    bas = offre.effets(p, "prudent", [_baisse("travail", -30.0)])
    haut = offre.effets(p, "prudent", [_baisse("travail", +30.0)])
    pts = 30.0 / y[2073] * 100
    assert bas["detail"]["travail"]["effet_pib_pct"][2073] == pytest.approx(
        p.val("offre.elasticite_travail", "prudent") * pts, rel=0.02)
    assert haut["detail"]["travail"]["effet_pib_pct"][2073] == pytest.approx(
        -sq._v(p, "offre.elasticite_travail", "median") * pts, rel=0.02)


def test_montee_comme_mesange(p):
    """Ajustement partiel : ≈ 10 % de l'effet de long terme la première année, ≈ 40 % à cinq ans, ≈ 65 % à dix ans."""
    y = sq.pib(p, "prudent")
    m = Mesure("essai", "recettes", {t: -0.01 * y[max(t, 2029)] for t in (2027, 2028, *ANNEES)}, instrument="cout_travail")
    d = offre.effets(p, "prudent", [m])["detail"]["cout_travail"]  # 1 point de PIB chaque année
    lt = 1.0 * p.val("offre.elasticite_cout_travail", "prudent")
    e = d["effet_pib_pct"]
    assert e[2027] / lt == pytest.approx(0.1, abs=0.02)
    assert 0.35 < e[2031] / lt < 0.5
    assert 0.6 < e[2036] / lt < 0.72


def test_emplois_de_l_offre_de_travail_viennent_de_l_inactivite(p):
    d = offre.effets(p, "prudent", [_baisse("travail")])
    t = 2040
    emplois = sum(v[t] for v in d["emplois"].values())
    assert emplois > 0 and d["actifs"][t] == pytest.approx(emplois)
    c = offre.effets(p, "prudent", [_baisse("cout_travail")])
    assert sum(v[t] for v in c["emplois"].values()) > 0 and c["actifs"][t] == 0


def test_transfert_en_plus_joue_contre_l_offre(p):
    d = offre.effets(p, "prudent", [_baisse("transferts_actifs", +10.0, poste="pauvrete")])
    assert d["dpib"][2050] < 0


def test_instrument_inconnu(p):
    with pytest.raises(ValueError):
        offre.effets(p, "prudent", [_baisse("magie")])


def test_interrupteur(p):
    """Canal coupé : pas de mesure d'offre, PIB du programme sans effet d'offre."""
    z = noyau.charger("zemmour")
    avec = z.contexte(p)["prudent"]["pib"][2050]
    q = p.avec({"offre.actif": False})
    sans_mes = [m for m in noyau.charger("zemmour").mesures(q)["prudent"] if m.nom.startswith("Effet d'offre")]
    assert not sans_mes
    sans = noyau.charger("zemmour").contexte(q)["prudent"]["pib"][2050]
    assert avec > sans


def test_baisse_de_la_csg_rapporte_de_l_offre_et_hausses_de_tondelier_en_coutent(p):
    for nom, signe in (("zemmour", 1), ("tondelier", -1)):
        prog = noyau.charger(nom)
        m = [x for x in prog.mesures(p)["prudent"] if x.nom.startswith("Effet d'offre")]
        assert len(m) == 1 and signe * m[0].valeurs[2050] > 0


def test_ecologie_de_droite_hors_du_canal(p):
    """Son moteur a ses propres canaux d'offre : aucune de ses mesures ne porte d'instrument."""
    e = noyau.charger("ecologie_de_droite")
    assert all(not m.instrument for m in e.mesures(p)["prudent"])
