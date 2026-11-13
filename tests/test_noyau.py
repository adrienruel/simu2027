"""Noyau commun (moteur/noyau.py) : programme vide = statu quo ; « Écologie de droite » tourne sur le même noyau que
les autres programmes (plus de moteur propre depuis le 12/11/2026) ; règle de trajectoire et dynamiques génériques."""

import pytest

from moteur import noyau, statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


def test_programme_vide_egale_statu_quo(p):
    vide = noyau.simuler(p, noyau.charger("vide"))
    ref = sq.simuler(p)
    for s in sq.SCENARIOS:
        for t in ANNEES:
            assert vide[s][t]["deficit"] == ref[s][t]["deficit"]
            assert vide[s][t]["dette"] == ref[s][t]["dette"]


def test_une_recette_ponctuelle(p):
    base = noyau.trajectoire(p, "prudent")
    avec = noyau.trajectoire(p, "prudent", [Mesure("essai", "recettes", {2030: 10.0})])
    assert avec[2029]["deficit"] == pytest.approx(base[2029]["deficit"])
    assert base[2030]["deficit"] - avec[2030]["deficit"] == pytest.approx(10 / base[2030]["pib"] * 100)
    assert avec[2031]["dette"] < base[2031]["dette"] - 10  # 10 Md€ de dette en moins, plus les intérêts évités


def test_poste_et_contexte_inconnus(p):
    with pytest.raises(ValueError, match="poste inconnu"):
        noyau.trajectoire(p, "prudent", [Mesure("essai", "ministere_imaginaire", {2030: 1.0})])
    with pytest.raises(ValueError, match="Contexte inconnu"):
        noyau.trajectoire(p, "prudent", contexte={"croissance": {}})
    noyau.trajectoire(p, "prudent", [Mesure("essai", "nouveau:revenu", {2030: 1.0})])  # bloc nouveau admis


def test_regle_generique_du_noyau(p):
    """Règle et dynamique génériques : un levier de 5 Md€ de capacité, toujours entièrement utilisé avec une cible de
    0 % (le statu quo est en déficit) ; un levier sans limite ramène exactement à la cible de 3 %. Les comptes
    publient le déficit avec et sans règle."""
    from moteur.noyau import Levier, Regle

    class Rien:
        def debut(self, t, etat):
            return {"pib": 0.0}

        def fin(self, t, etat):
            pass
    base = noyau.trajectoire(p, "prudent")
    assert base[2029]["deficit"] > 3.5  # le cas testé suppose un statu quo au-dessus de la cible
    r1 = noyau.trajectoire(p, "prudent", regle=Regle(0.0, [Levier("petit", lambda t, e: 5.0)]), dynamiques=[Rien()])
    r2 = noyau.trajectoire(p, "prudent", regle=Regle(0.03, [Levier("grand", lambda t, e: 1e6)]), dynamiques=[Rien()])
    assert r1[2029]["deficit_avant_regle"] == pytest.approx(base[2029]["deficit"])
    assert r1[2029]["regle"]["leviers"]["petit"] == pytest.approx(5.0)
    assert r1[2029]["deficit"] == pytest.approx(base[2029]["deficit"] - 5.0 / base[2029]["pib"] * 100)
    assert r1[2029]["regle"]["reste_a_couvrir"] > 0
    assert all(r2[t]["deficit"] == pytest.approx(3.0, abs=1e-6) for t in ANNEES if r2[t]["deficit_avant_regle"] > 3.0)
    assert all(r2[t]["deficit"] <= r2[t]["deficit_avant_regle"] + 1e-9 for t in ANNEES)


def test_ecologie_de_droite_sur_le_noyau_sans_moteur_propre(p):
    """Le programme n'appelle plus aucun moteur : le noyau l'exécute avec ses mesures, un fonds (dynamique) et la
    règle de trajectoire. Chaque scénario publie les deux déficits ; la règle ramène à 3 % ou s'épuise."""
    import importlib
    for mod in ("moteur.macro", "moteur.simulation", "moteur.trajectoire_annuelle"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)
    r = noyau.resultats(p)
    for s in sq.SCENARIOS:
        assert "fonds" in r[s][2037]["dynamiques"]
        # 2037 : avant la dernière année de la règle ; soit la cible est atteinte, soit les leviers sont au maximum
        regle = r[s][2037]["regle"]
        if regle["reste_a_couvrir"] > 1e-6:
            assert all(regle["leviers"][k] == pytest.approx(regle["capacites"][k]) for k in regle["leviers"])
        else:
            # la contribution est un emprunt aux ménages (12/11/2026) : la règle la compte, le déficit publié aussi
            contribution = regle["leviers"]["Contribution d'épargne retraite"] / r[s][2037]["pib"] * 100
            assert (r[s][2037]["deficit"] == pytest.approx(3.0 + contribution, abs=0.01)
                    or r[s][2037]["deficit_avant_regle"] <= 3.0)


def test_scenario_sans_regle_est_un_vrai_contrefactuel(p):
    """Le « sans règle » publié est le scénario complet sans la règle : identique à un passage avec la clause
    désactivée (même dette et même PIB, années suivantes comprises) ; les créances de la règle sont publiées."""
    avec = noyau.resultats(p, ("prudent",))["prudent"]
    coupee = noyau.resultats(p.avec({"clause.active": False}), ("prudent",))["prudent"]
    for t in (2029, 2037, 2050, 2073):
        assert avec[t]["deficit_sans_regle"] == pytest.approx(coupee[t]["deficit"], abs=1e-6)
        assert avec[t]["sans_regle"]["dette_pib"] == pytest.approx(coupee[t]["dette_pib"], abs=1e-6)
    assert avec[2050]["quasi_dette"] > 0 and coupee[2050]["quasi_dette"] == 0
    # contribution en emprunt (12/11/2026) : les créances sont déjà dans la dette publiée, sans double compte
    assert avec[2050]["dette_et_quasi_dette_pib"] == pytest.approx(avec[2050]["dette_pib"])
    ancienne = noyau.resultats(p.avec({"clause.contribution_en_emprunt": False}), ("prudent",))["prudent"]
    assert ancienne[2050]["dette_et_quasi_dette_pib"] > ancienne[2050]["dette_pib"]


@pytest.fixture(scope="module")
def ed(p):
    prog = noyau.charger("ecologie_de_droite")
    return prog, noyau.simuler(p, prog), None


def test_bilan_des_mesures(ed, p):
    prog, r, _ = ed
    b = noyau.bilan_mesures(prog, p)
    natures = {x["nature"] for x in b}
    assert {"budget", "effet_macro"} <= natures
    # le budget du programme, ses effets, le fonds et la règle expliquent tout l'écart de solde primaire avec le statu quo
    base = sq.simuler(p)["prudent"]
    for t in (2029, 2050):
        effet = sum(x[t] for x in b) + r["prudent"][t]["dynamiques"]["fonds"]["solde"]
        effet += r["prudent"][t]["regle"]["gain_comptes"]  # ce que la règle a inscrit au solde
        assert effet == pytest.approx(r["prudent"][t]["solde_primaire"] - base[t]["solde_primaire"], abs=1e-6)


def test_perimetre_aligne_sans_effet_sur_le_solde(ed, p):
    """Les collectivités remises au budget du programme : autant de ressources que de dépenses."""
    prog, _, _ = ed
    per = [m for m in prog.mesures(p)["prudent"] if m.nature == "perimetre"]
    assert len(per) >= 2
    for t in (2029, 2073):
        assert sum(m.valeurs[t] for m in per if m.poste == "recettes") == pytest.approx(
            sum(m.valeurs[t] for m in per if m.poste != "recettes"))
    from programmes.ecologie_de_droite.programme import collectivites_hors_budget, ecart_de_depart
    c = collectivites_hors_budget(p)
    assert 200 < c["depenses"] < 260 and c["ressources"] == pytest.approx(c["depenses"] - c["besoin_financement"])
    e = ecart_de_depart(p)
    assert abs(e["Recettes"]) < 250


def test_programmes_disponibles():
    """Le comparateur prend le statu quo et chaque dossier programmes/<nom>/ qui a un programme.py."""
    noms = noyau.programmes_disponibles()
    assert noms[0] == "statu_quo" and "ecologie_de_droite" in noms
    assert noyau.charger("ecologie_de_droite").libelle == "Écologie de droite"


def test_impulsion_budgetaire_d_ecologie_de_droite(p):
    """Ce qui entre dans le multiplicateur (relecture indépendante du 11/11/2026) : natures connues ; reclassements
    et détails sans effet net ; revenu universel pondéré comme un transfert ; l'impulsion calculée de 2029 retrouve
    l'effort que le programme déclare (macro.effort_2029 − assouplissement + prélèvement sur les anciennes pensions)."""
    from moteur import offre
    m = noyau.charger("ecologie_de_droite").mesures(p)["prudent"]
    assert {x.nature for x in m} <= {"budget", "classement", "detail", "effet_macro", "mesure", "methode", "perimetre", "physique"}
    for nature in ("detail", "perimetre"):
        for t in (2029, 2050):
            net = sum((-1 if x.poste == "recettes" else 1) * x.valeurs.get(t, 0.0) for x in m if x.nature == nature)
            assert net == pytest.approx(0.0, abs=1e-6), (nature, t)
    w = p.val("demande.poids")
    rui = next(x for x in m if x.poste == "nouveau:rui_aah")
    assert offre.poids_demande(p, rui) == w["transferts_cibles"]
    assert all(not x.instrument for x in m)  # le canal d'offre commun ne s'applique pas à ce programme
    prog = noyau.charger("ecologie_de_droite")
    st = prog._statique(p, ("prudent",))["prudent"]
    assert offre.poids_demande(p, st["effets"].prelevements_pour_impulsion()[0]) == w["consommation"]
    imp = st["impulsion"]
    anc = next(x for x in m if x.nom.startswith("Anciennes pensions : prélèvement net")).valeurs[2029]
    declare = (p.val("macro.effort_2029") - p.val("macro.assouplissement_2029")) * sq.pib(p, "prudent")[2029] + anc
    # depuis le 14/11/2026, les recettes sont nettes des réactions des contribuables, comme chez les autres programmes
    declare += sum(x.valeurs[2029] for x in st["effets"].mesures_nettes())
    assert -imp[2029] == pytest.approx(declare, rel=0.15)


def test_variante_fonds_dans_les_administrations_publiques(p):
    """Variante de classement (relecture I5) : les investissements financés par le fonds comptés en dépense publique.
    Même économie (PIB inchangé la première année), déficit avant règle plus haut du montant de ces investissements."""
    prog = noyau.charger("ecologie_de_droite")
    base = noyau.simuler(p, prog, scenarios=("prudent",), contrefactuel=False)["prudent"]
    var = prog.variante_fonds_apu(p, ("prudent",))["prudent"]
    inv = var[2029]["investissements_du_fonds"]
    assert 50 < inv < 100
    assert var[2029]["pib"] == pytest.approx(base[2029]["pib"])
    assert var[2029]["deficit_avant_regle"] - base[2029]["deficit_avant_regle"] == pytest.approx(inv / base[2029]["pib"] * 100, abs=1e-6)
    assert all(var[t]["dette_pib"] > base[t]["dette_pib"] for t in (2029, 2037, 2050, 2073))
