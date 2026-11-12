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
    r = noyau.simuler(P, prog, scenarios=("prudent",))["prudent"]
    noms = {m.nom for m in prog.mesures(P)["prudent"]}
    assert {"Canal déclaré : fraude à la TVA", "Canal déclaré : productivité"} <= noms
    # 2029 : un quart de la fraude, pas encore de productivité
    assert BASE[2029]["solde_primaire"] + 0.5 == pytest.approx(r[2029]["solde_primaire"], abs=1e-6)
    assert r[2029]["pib"] == pytest.approx(BASE[2029]["pib"])
    from moteur import statu_quo as sq  # dix ans de gain sur le PIB du statu quo, puis palier
    assert r[2045]["pib"] - BASE[2045]["pib"] == pytest.approx(sq.pib(P, "prudent")[2045] * (1.001 ** 10 - 1), rel=1e-9)
    assert r[2050]["deficit"] < BASE[2050]["deficit"]


def test_ecole_et_ia():
    prog = _programme({"ecole": {"niveau_eleves": {s: 0.2 for s in PAR}, "debut": 2035, "annees": 20},
                       "adoption_ia": {"part": {s: 0.1 for s in PAR}}})
    r = noyau.simuler(P, prog, scenarios=("prudent",))["prudent"]
    assert r[2034]["pib"] > BASE[2034]["pib"] and r[2060]["pib"] > r[2034]["pib"] / BASE[2034]["pib"] * BASE[2060]["pib"]


def test_baisse_de_l_ecart_de_taux_gagnee_par_le_resultat():
    """Règle commune (critère absolu, phase A5 du 12/11/2026) : la baisse suit les années où le ratio de dette baisse,
    une année où il remonte en fait perdre une ; nulle en crise et au prudent (barème), nulle pour le statu quo ;
    Écologie de droite la gagne dès 2031 au médian (dette en baisse dès 2030). Être sous le déficit du statu quo ne suffit plus."""
    from moteur import statu_quo as sq
    ref = {t: {"deficit": 9.0, "dette_pib": 100.0 + 5 * (t - 2029)} for t in ANNEES}
    mieux = {t: {"deficit": 4.0, "dette_pib": 120.0 - (t - 2032) if t >= 2032 else 120.0} for t in ANNEES}
    b = noyau.baisse_ecart_taux(P, "median", mieux, ref)
    bareme, duree = P.val("macro.baisse_spread", "median"), P.val("macro.annees_baisse_spread")
    assert b[2033] == 0 and b[2034] == pytest.approx(-bareme / duree) and b[2073] == pytest.approx(-bareme)
    # sous le déficit du statu quo, mais dette qui monte : aucune baisse
    diverge = {t: {"deficit": 8.0, "dette_pib": 100.0 + 4 * (t - 2029)} for t in ANNEES}
    assert noyau.baisse_ecart_taux(P, "median", diverge, ref) is None
    # dette en baisse puis en hausse : les années acquises se perdent
    aller_retour = {t: {"deficit": 3.0, "dette_pib": 100.0 - min(t - 2029, 10) + 2 * max(0, t - 2039)} for t in ANNEES}
    c = noyau.baisse_ecart_taux(P, "median", aller_retour, ref)
    assert c[2040] == pytest.approx(-bareme * min(1.0, 10 / duree)) and c[2073] == 0
    assert noyau.baisse_ecart_taux(P, "prudent", mieux, ref) is None
    vide = noyau.simuler(P, scenarios=("median",))["median"]
    assert all("baisse_ecart_taux" not in vide[t] for t in ANNEES)
    assert all(vide[t]["deficit"] == sq.simuler(P)["median"][t]["deficit"] for t in ANNEES)
    edd = noyau.resultats(P, ("median",))["median"]
    # dette en baisse dès 2030 (premier écart mesurable avec 2029) : baisse effective en 2031
    assert edd[2030]["baisse_ecart_taux"] == 0 and edd[2031]["baisse_ecart_taux"] == pytest.approx(bareme / duree)
    assert edd[2040]["baisse_ecart_taux"] == pytest.approx(bareme)


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
    même objet, aux valeurs d'Écologie de droite ; rien dans le scénario de crise ; l'école seulement à l'optimiste."""
    q = Parametres()
    ia = q.val("macro.adoption_ia", "optimiste")
    avec_ia, avec_ecole = set(), set()
    for nom in noyau.programmes_disponibles():
        if nom in ("statu_quo", "ecologie_de_droite"):
            continue
        prog = noyau.charger(nom)
        d = canaux_declares.declares(prog)
        if "adoption_ia" in d:
            avec_ia.add(nom)
            assert d["adoption_ia"]["part"] == {s: q.val("macro.adoption_ia", s) for s in ("crise", "prudent", "median", "optimiste")}
        if "ecole" in d:
            avec_ecole.add(nom)
            assert d["ecole"]["niveau_eleves"] == {s: q.val("macro.niveau_eleves", s) for s in ("crise", "prudent", "median", "optimiste")}
        m = prog.mesures(P)
        assert all(abs(v) < 1e-9 for x in m["crise"] if x.nom.startswith("Canal déclaré")
                   and "réformes de structure" not in x.nom for v in x.valeurs.values())  # miroir : réglementer coûte en crise
    assert ia > 0 and avec_ia == {"attal", "glucksmann", "philippe", "zemmour", "retailleau", "lisnard"}
    assert avec_ecole == {"arthaud", "attal", "glucksmann", "le_pen", "lisnard", "melenchon", "philippe", "retailleau", "roussel",
                          "tondelier", "zemmour"}
    assert avec_ia <= avec_ecole  # qui parle de l'IA parle aussi de l'école (vérifié le 12/11/2026)


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
