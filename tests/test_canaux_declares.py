"""Canaux déclarés, ouverts à tous les programmes (moteur/canaux_declares.py, décision d'Adrien du 12/11/2026)."""
import pytest

from moteur import canaux_declares, noyau
from moteur.noyau import ANNEES
from moteur.parametres import Parametres
from programmes.le_pen.programme import LePen

P = Parametres()
PAR = {"crise": 0.0, "prudent": 0.001, "median": 0.002, "optimiste": 0.003}


def _programme(canaux: dict) -> LePen:
    """Un programme existant auquel on déclare des canaux (sans toucher à son fichier de paramètres)."""
    prog = LePen()
    for nom, valeur in canaux.items():
        cle = f"le_pen_canaux.{nom}"
        prog.pt._p[cle] = prog.pt._valider(cle, {"valeur": valeur, "unite": "sans_unite", "statut": "HYPOTHESE"})
    return prog


BASE = noyau.simuler(P, LePen(), scenarios=("prudent",))["prudent"]


def test_sans_canal_declare_rien_ne_change():
    assert canaux_declares.declares(LePen()) == {}
    r = noyau.simuler(P, _programme({}), scenarios=("prudent",))["prudent"]
    assert all(r[t]["deficit"] == BASE[t]["deficit"] and r[t]["deficit_sans_regle"] == r[t]["deficit"] for t in ANNEES)


def test_canal_inconnu_refuse():
    with pytest.raises(ValueError, match="Canal déclaré inconnu"):
        canaux_declares.declares(_programme({"miracle": {"montant": PAR}}))


def test_fraude_tva_et_productivite():
    prog = _programme({"fraude_tva": {"montant": {"crise": 0, "prudent": 2.0, "median": 3, "optimiste": 5}, "debut": 2029, "montee": 4},
                       "productivite": {"taux": PAR, "debut": 2030, "annees": 10}})
    r = noyau.simuler(P, prog, scenarios=("prudent",))["prudent"]
    noms = {m.nom for m in prog.mesures(P)["prudent"]}
    assert {"Canal déclaré : fraude à la TVA", "Canal déclaré : productivité"} <= noms
    # 2029 : un quart de la fraude, pas encore de productivité
    assert BASE[2029]["solde_primaire"] + 0.5 == pytest.approx(r[2029]["solde_primaire"], abs=1e-6)
    assert r[2029]["pib"] == pytest.approx(BASE[2029]["pib"])
    from moteur import statu_quo as sq  # dix ans de gain sur le PIB du statu quo, puis palier
    assert r[2045]["pib"] - BASE[2045]["pib"] == pytest.approx(sq.pib(P, "prudent")[2045] * (1.001 ** 10 - 1), rel=1e-9)
    assert r[2050]["deficit"] < BASE[2050]["deficit"]


def test_ecole_ia_et_ecart_de_taux():
    prog = _programme({"ecole": {"niveau_eleves": {s: 0.2 for s in PAR}, "debut": 2035, "annees": 20},
                       "adoption_ia": {"part": {s: 0.1 for s in PAR}},
                       "baisse_ecart_taux": {"baisse": {"crise": 0, "prudent": 0.002, "median": 0.002, "optimiste": 0.004}, "annees": 8}})
    r = noyau.simuler(P, prog, scenarios=("prudent",))["prudent"]
    assert r[2034]["pib"] > BASE[2034]["pib"] and r[2060]["pib"] > r[2034]["pib"] / BASE[2034]["pib"] * BASE[2060]["pib"]
    assert r[2029]["taux_apparent"] == pytest.approx(BASE[2029]["taux_apparent"])
    assert r[2040]["taux_apparent"] < BASE[2040]["taux_apparent"]


def test_regle_de_trajectoire_declaree():
    """Un programme qui déclare une règle : déficit ramené à la cible tant que les leviers suffisent ; publication
    avec et sans règle ; le scénario sans règle est celui du programme sans ce canal."""
    regle = {"cible": 0.03, "derniere_annee": 2073,
             "leviers": [{"nom": "Hausse d'impôt", "poste": "recettes", "capacite_pib": 0.01},
                         {"nom": "Baisse des autres dépenses", "poste": "autres", "capacite_pib": 0.01}]}
    r = noyau.simuler(P, _programme({"regle_trajectoire": regle}), scenarios=("prudent",))["prudent"]
    assert BASE[2029]["deficit"] > 5.0  # sans règle : au-dessus de la cible de plus de deux points
    assert r[2029]["deficit"] == pytest.approx(BASE[2029]["deficit"] - 2.0, abs=1e-6)  # deux leviers d'un point au maximum
    assert r[2029]["regle"]["reste_a_couvrir"] > 0
    assert r[2029]["blocs"]["autres"] == pytest.approx(BASE[2029]["blocs"]["autres"] - 0.01 * BASE[2029]["pib"])
    for t in (2029, 2050, 2073):
        assert r[t]["deficit_sans_regle"] == pytest.approx(BASE[t]["deficit"], abs=1e-9)
        assert r[t]["sans_regle"]["dette_pib"] == pytest.approx(BASE[t]["dette_pib"], abs=1e-9)
    assert r[2073]["dette_pib"] < BASE[2073]["dette_pib"]
