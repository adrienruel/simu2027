"""Canaux déclarés, ouverts à tous les programmes (moteur/canaux_declares.py, décision d'Adrien du 12/11/2026)."""
import pytest

from moteur import canaux_declares, noyau
from moteur.noyau import ANNEES
from moteur.parametres import Parametres
from programmes.bertrand.programme import Bertrand as LePen  # un programme sans canal déclaré

P = Parametres()
PAR = {"crise": 0.0, "prudent": 0.001, "median": 0.002, "optimiste": 0.003}


def _programme(canaux: dict) -> LePen:
    """Un programme existant auquel on déclare des canaux (sans toucher à son fichier de paramètres)."""
    prog = LePen()
    for cle in [c for c in prog.pt._p if c.startswith(f"{prog.nom}_canaux.")]:
        del prog.pt._p[cle]  # aucun canal propre (Bertrand déclare un solde migratoire depuis la phase B2)
    for nom, valeur in canaux.items():
        cle = f"{prog.nom}_canaux.{nom}"
        prog.pt._p[cle] = prog.pt._valider(cle, {"valeur": valeur, "unite": "sans_unite", "statut": "HYPOTHESE"})
    return prog


BASE = noyau.simuler(P, _programme({}), scenarios=("prudent",))["prudent"]


def test_sans_canal_declare_rien_ne_change():
    assert canaux_declares.declares(_programme({})) == {}
    r = noyau.simuler(P, _programme({}), scenarios=("prudent",))["prudent"]
    assert all(r[t]["deficit"] == BASE[t]["deficit"] and r[t]["deficit_sans_regle"] == r[t]["deficit"] for t in ANNEES)


def test_canal_inconnu_refuse():
    with pytest.raises(ValueError, match="Canal déclaré inconnu"):
        canaux_declares.declares(_programme({"miracle": {"montant": PAR}}))


def test_fraude_tva_et_productivite():
    prog = _programme({"fraude_tva": {"montant": {"crise": 0, "prudent": 2.0, "median": 3, "optimiste": 5}, "debut": 2029, "montee": 4},
                       "productivite": {"taux": PAR, "debut": 2030, "annees": 10}})
    # mécanique du canal seule : sans la rétroaction des taux sur le PIB (phase E, tests/test_bouclage.py)
    q = P.avec({"macro.bouclage_prime_demande": False})
    r = noyau.simuler(q, prog, scenarios=("prudent",))["prudent"]
    noms = {m.nom for m in prog.mesures(P)["prudent"]}
    assert {"Canal déclaré : fraude à la TVA", "Canal déclaré : productivité"} <= noms
    # 2029 : un quart de la fraude, pas encore de productivité
    # à 0,05 Md€ près : effets bouclés de second ordre (prix, pensions en retard sur les prix) des mesures du programme
    assert BASE[2029]["solde_primaire"] + 0.5 == pytest.approx(r[2029]["solde_primaire"], abs=0.05)  # Bertrand : IR à 9,3 Md€ depuis F4
    assert r[2029]["pib"] == pytest.approx(BASE[2029]["pib"], abs=0.1)  # effets bouclés de la baisse d'IR de Bertrand (F4)
    from moteur import statu_quo as sq  # dix ans de gain sur le PIB du statu quo, puis palier
    # repère : le même programme sans canal (les effets bouclés de ses propres mesures durent jusqu'en 2045)
    r0 = noyau.simuler(q, _programme({}), scenarios=("prudent",))["prudent"]
    assert r[2045]["pib"] - r0[2045]["pib"] == pytest.approx(sq.pib(P, "prudent")[2045] * (1.001 ** 10 - 1), rel=1e-2)
    assert r[2050]["deficit"] < BASE[2050]["deficit"]


def test_ecole_et_ia():
    prog = _programme({"ecole": {"niveau_eleves": {s: 0.2 for s in PAR}, "debut": 2035, "annees": 20},
                       "adoption_ia": {"part": {s: 0.1 for s in PAR}}})
    r = noyau.simuler(P, prog, scenarios=("prudent",))["prudent"]
    assert r[2034]["pib"] > BASE[2034]["pib"] and r[2060]["pib"] > r[2034]["pib"] / BASE[2034]["pib"] * BASE[2060]["pib"]


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


def test_canaux_declares_par_les_programmes():
    """Barème commun du 12/11/2026 : adoption de l'IA et école déclarées par les programmes qui ont une mesure sur le
    même objet, aux mêmes valeurs pour tous (programme_commun, rangé le 16/11/2026 : aucun programme ne le recopie ni ne
    le redéfinit) ; rien dans le scénario de crise ; l'école seulement à l'optimiste."""
    q = Parametres()
    ia = q.val("programme_commun.canaux_adoption_ia_part", "optimiste")
    assert q.val("programme_commun.canaux_ecole_niveau_eleves", "prudent") == 0
    avec_ia, avec_ecole = set(), set()
    for nom in noyau.programmes_disponibles():
        if nom == "statu_quo":
            continue
        prog = noyau.charger(nom)
        d = canaux_declares.declares(prog)
        if "adoption_ia" in d:
            avec_ia.add(nom)
            assert "part" not in d["adoption_ia"]
        if "ecole" in d:
            avec_ecole.add(nom)
            assert "niveau_eleves" not in d["ecole"]
        m = prog.mesures(P)
        # IA et école : rien en crise (la fraude, le logement et le solde migratoire jouent dans tous les scénarios)
        assert all(abs(v) < 1e-9 for x in m["crise"]
                   if x.nom.startswith(("Canal déclaré : adoption de l'IA", "Canal déclaré : école")) for v in x.valeurs.values())
    assert ia > 0 and avec_ia == {"attal", "glucksmann", "philippe", "zemmour", "retailleau", "lisnard"}
    # phase B6 : l'école déclarée seulement pour des réformes d'organisation sans budget (les mesures budgétaires passent
    # par le canal d'offre de l'éducation)
    assert avec_ecole == {"zemmour"}


def test_reformes_structurelles_bareme():
    """Barème commun des réformes de structure (12/11/2026) : sens des scénarios, miroir, plafond."""
    from moteur.parametres import Parametres
    from moteur.reformes_structurelles import gain
    p = Parametres()
    lib, reg = {"pmr": 1, "debut": 2028}, {"pmr": -1, "debut": 2028}
    g = {s: gain(p, lib, s, 2045) for s in ("crise", "prudent", "median", "optimiste")}
    assert g["crise"] == 0 < g["prudent"] < g["median"] < g["optimiste"]
    r = {s: gain(p, reg, s, 2045) for s in ("crise", "prudent", "median", "optimiste")}
    assert r["crise"] < r["prudent"] < r["median"] < r["optimiste"] == 0
    assert abs(r["prudent"] + g["median"]) < 1e-12  # miroir
    assert gain(p, {"pmr": 5}, "median", 2045) == gain(p, {"pmr": 2}, "median", 2045)  # plafond
    # effet à 10 ans de l'OCDE au médian
    assert abs(gain(p, lib, "median", 2037) - 0.0102) < 1e-12
