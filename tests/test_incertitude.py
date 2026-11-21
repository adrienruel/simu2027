"""Incertitude chiffrée (phase D, moteur/incertitude.py)."""
import pytest

from moteur import incertitude as inc
from moteur.parametres import Parametres


def test_loi_centiles():
    d = {"crise": 0.0, "prudent": 1.0, "median": 2.0, "optimiste": 4.0}
    assert inc._valeur(d, 0.0) == pytest.approx(2.0)
    assert inc._valeur(d, -inc.Z90) == pytest.approx(1.0)  # prudent = 10e centile
    assert inc._valeur(d, inc.Z90) == pytest.approx(4.0)   # optimiste = 90e centile
    assert inc._valeur(d, -10) == pytest.approx(0.0)       # borné par la crise
    assert inc._valeur(d, 10) == pytest.approx(6.0)        # un pas de plus que l'optimiste


def test_loi_sans_prudent_ecrit_et_sens_inverse():
    jeu = {"crise": 0.1, "median": 0.3, "optimiste": 0.4}  # jeux d'emploi : prudent = milieu crise / médian
    assert inc._valeur(jeu, -inc.Z90) == pytest.approx(0.2)
    inverse = {"crise": 9.0, "prudent": 8.0, "median": 7.0, "optimiste": 6.0}
    assert inc._valeur(inverse, -inc.Z90) == pytest.approx(8.0)
    assert inc._valeur(inverse, -10) == pytest.approx(9.0)


def test_tirages_communs_et_reproductibles():
    a = inc.z_tirage(2029, 3, 0.5, "macro.multiplicateur")
    assert a == inc.z_tirage(2029, 3, 0.5, "macro.multiplicateur")
    assert a != inc.z_tirage(2029, 4, 0.5, "macro.multiplicateur")
    # rho = 1 : même z pour toutes les hypothèses d'un tirage
    assert inc.z_tirage(2029, 3, 1.0, "a") == pytest.approx(inc.z_tirage(2029, 3, 1.0, "b"))


def test_tirage_ne_touche_que_la_colonne_mediane(monkeypatch):
    """Paramètre qui n'est pas lu en miroir : seule la colonne médiane est tirée."""
    p = Parametres()
    monkeypatch.setattr(inc, "z_tirage", lambda g, i, rho, nom: -inc.Z90)
    c = inc.tirer(p, 1, 0, 1.0)
    assert "macro.tendance" not in inc.MIROIR_CLES
    v, w = p["macro.tendance"].valeur, c["macro.tendance"].valeur
    assert w["median"] == pytest.approx(v["prudent"])
    assert {k: w[k] for k in ("crise", "prudent", "optimiste")} == {k: v[k] for k in ("crise", "prudent", "optimiste")}
    assert p["macro.tendance"].valeur["median"] == v["median"]  # l'original n'est pas modifié


def test_tirage_miroir(monkeypatch):
    """Paramètre lu en miroir (phase 3.2) : sa colonne prudente est tirée au point miroir. Au 10e centile, le
    médian tiré vaut le prudent et le miroir vaut le médian, comme dans le scénario prudent publié."""
    p = Parametres()
    monkeypatch.setattr(inc, "z_tirage", lambda g, i, rho, nom: -inc.Z90)
    c = inc.tirer(p, 1, 0, 1.0)
    v, w = p["macro.multiplicateur"].valeur, c["macro.multiplicateur"].valeur
    assert w["median"] == pytest.approx(v["prudent"])
    assert w["prudent"] == pytest.approx(v["median"])
    assert p["macro.multiplicateur"].valeur["prudent"] == v["prudent"]
    ancien = inc.tirer(p, 1, 0, 1.0, miroir=False)["macro.multiplicateur"].valeur
    assert ancien["prudent"] == v["prudent"]


def test_reference_du_multiplicateur_fixe():
    """Un multiplicateur médian tiré à zéro ne divise plus par zéro (2 et 5 tirages sur 600 écartés avant le
    16/11/2026) : les profils d'emploi sont rapportés au multiplicateur de référence, fixe."""
    from moteur import noyau
    p = Parametres().avec({"macro.multiplicateur/median": 0.0})
    r = noyau.simuler(p, noyau.charger("lisnard"), scenarios=("median",), contrefactuel=False)
    assert r["median"][2037]["deficit"] == r["median"][2037]["deficit"]  # nombre (pas NaN)
    assert Parametres().val("bouclage.multiplicateur_reference") == Parametres().val("macro.multiplicateur", "median")


def test_rho1_dixieme_centile_retrouve_le_prudent():
    """Contrôle remis en test (phase 3.2, 16/11/2026) : ρ = 1 et tous les z au 10e centile redonnent le scénario
    prudent publié, à l'écart près des règles propres au prudent (moyennes de jeux, lectures hors miroir). Mesuré le
    16/11/2026, écart au statu quo en 2037 (tirage − publié, points de PIB) : statu quo −0,04 ; de −0,04 (Bertrand) à
    −0,73 (Arthaud) ; avant le tirage des miroirs, jusqu'à −1,36. Mesuré le 21/11/2026, après le taux apparent au
    rythme du refinancement : de −0,04 (Bertrand) à −0,87 (Mélenchon, dont le déficit de 30 % du PIB rend les intérêts
    plus sensibles à la dette nouvelle) ; seuil relevé de 0,8 à 0,9 point."""
    from moteur import noyau
    noms = inc.programmes()
    base, propres, listes = inc._preparer(noms)
    z = lambda nom: -inc.Z90
    p = inc.tirer_z(base, z, listes["base"])
    pub_sq = noyau.simuler(base, None, scenarios=("prudent",), contrefactuel=False)["prudent"][2037]["deficit"]
    t_sq = noyau.simuler(p, None, scenarios=("median",), contrefactuel=False)["median"][2037]["deficit"]
    assert abs(t_sq - pub_sq) < 0.1
    for nom in noms:
        pub = noyau.simuler(base, noyau.charger(nom), scenarios=("prudent",), contrefactuel=False)["prudent"][2037]["deficit"]
        prog = noyau.charger(nom)
        if nom in propres:
            prog.pt = inc.tirer_z(propres[nom], z, listes[nom])
        t = noyau.simuler(p, prog, scenarios=("median",), contrefactuel=False)["median"][2037]["deficit"]
        assert abs((t - t_sq) - (pub - pub_sq)) < 0.9, nom
