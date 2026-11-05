"""Module écologie : émissions, empreinte, réponse au prix (moteur/ecologie/emissions.py)."""
import pytest

from moteur.ecologie import emissions as em
from moteur.noyau import Mesure
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


def test_depart_source(p):
    """2025 : le total du Citepa ; empreinte proche du SDES (563 Mt en 2024, en baisse)."""
    b = em.bilan(p, "prudent")
    assert b[2025]["territoriales"] == pytest.approx(359.0)
    assert 540 < b[2025]["empreinte"] < 563


def test_programme_vide_egal_statu_quo(p):
    for s in ("crise", "prudent", "median", "optimiste"):
        b = em.bilan(p, s, [], {})
        for t in em.ANNEES:
            assert b[t]["effet_activite"] == 0 and b[t]["effet_mesures"] == 0
            assert b[t]["territoriales"] == pytest.approx(b[t]["statu_quo"])


def test_activite_separee(p):
    """Un PIB plus bas baisse les émissions : effet de l'activité, pas effet des mesures."""
    from moteur import statu_quo as sq
    y = {t: v * 0.95 for t, v in sq.pib(p, "prudent").items()}
    b = em.bilan(p, "prudent", [], {"pib": y})
    assert b[2040]["effet_activite"] < 0
    assert b[2040]["effet_mesures"] == pytest.approx(0.0, abs=1e-9)


def test_relocalisation(p):
    """Relocaliser baisse les émissions importées et monte moins les territoriales (intensité plus faible)."""
    m = Mesure("test", "recettes", {}, "physique", physique={"relocalisation_mt": {t: 10.0 for t in em.ANNEES}})
    b0, b1 = em.bilan(p, "prudent"), em.bilan(p, "prudent", [m], {})
    assert b1[2040]["importees"] == pytest.approx(b0[2040]["importees"] - 10)
    assert 0 < b1[2040]["territoriales"] - b0[2040]["territoriales"] < 10
    assert b1[2040]["empreinte"] < b0[2040]["empreinte"]


def test_effet_physique_inconnu(p):
    m = Mesure("test", "recettes", {}, "physique", physique={"emissions_mt:aviation": {2030: -1.0}})
    with pytest.raises(ValueError):
        em.bilan(p, "prudent", [m], {})


def test_reponse_prix_deux_sens(p):
    """Prix au-dessus du statu quo : émissions en baisse, progressivement ; en dessous : en hausse."""
    haut = em.reponse_prix(p, {t: 300.0 for t in em.ANNEES})
    bas = em.reponse_prix(p, {t: 10.0 for t in em.ANNEES})
    assert haut[2028] == 1.0 and haut[2029] < 1 and haut[2040] < haut[2030] < haut[2029]
    assert bas[2040] > 1
    assert em.reponse_prix(p, {t: em.prix_statu_quo(p, t) for t in em.ANNEES})[2050] == pytest.approx(1.0)


def test_une_seule_equation():
    """La réponse des émissions au prix utilise la même élasticité que la recette carbone d'Écologie de droite, et la
    hausse du prix de l'essence reste dans le bon ordre de grandeur (correction du 05/11/2026)."""
    q = Parametres(programme="ecologie_de_droite")
    r = q.val("ecologie.reponse_prix")
    assert r["elasticite"] == q.val("carbone_importe.elasticite_prix")
    hausse = (315 - em.prix_statu_quo(q, 2030)) * r["contenu_carbone_kg_par_euro"] / 1000
    assert 0.2 < hausse < 0.4  # essence : (315 − 91) €/t × 2,3 kg / 1,85 € ≈ +28 %


def test_snbc(p):
    b = em.snbc(p)
    assert (b[2024], b[2028], b[2029], b[2034], b[2038]) == (342, 342, 262, 194, 194)
    assert b[2050] == b[2073] == p.val("ecologie.objectif_2050")
    assert b[2044] < b[2039] < 194


def test_profil(p):
    """Montée, extinction et réduction au rythme de la décarbonation du statu quo."""
    spec = {"effet_mt": {"crise": -1.0, "prudent": -1.0, "median": -1.0, "optimiste": -1.0},
            "debut": 2028, "plein": 2031, "fin_debut": 2035, "fin": 2045}
    x = em.profil(p, "prudent", spec)
    assert x[2027] == 0 and x[2028] == pytest.approx(-0.25) and -1 < x[2031] < -0.9
    assert x[2045] == 0 and x[2040] > x[2034]
    y = em.profil(p, "prudent", {**spec, "suit_intensite": False, "fin": None})
    assert y[2060] == pytest.approx(-1.0)


def test_tondelier_chiffre_en_tonnes():
    """Les mesures écologiques de Tondelier ont un effet physique, nul dans le prudent quand rien ne le source."""
    pt = Parametres(programme="tondelier")
    mesures = {k: v.valeur for k, v in pt._p.items() if k.startswith("tondelier_ecologie.")}
    assert len(mesures) >= 8
    for k, v in mesures.items():
        if pt[k].source is None:
            assert v["effet_mt"]["prudent"] == 0, k
