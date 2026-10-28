"""Étape 1 : recettes de la feuille Total, contre les valeurs de la v235."""
import pytest

from moteur.parametres import Parametres
from moteur.recettes import impot_salaires as sal

P = Parametres()
MD = 1e9
TOL = 0.01 * MD  # 0,01 Md€


def test_effectifs_conserves():
    d = sal.effectifs_prive_2026(P)
    assert sum(d.effectifs) == pytest.approx(sum(sal.lire("salaries_prive.csv").effectifs))


def test_effectif_classe_27_5_30k():
    # Passage en euros de 2026!M50
    assert sal.effectifs_prive_2026(P).effectifs[8] == pytest.approx(1_216_660, rel=1e-5)


def test_impot_prive_total_ligne_4():
    assert sal.impot_prive(P) == pytest.approx(452_838_702_211.722, abs=TOL)


def test_alignement_public():
    assert sal.facteur_alignement_public(P) - 1 == pytest.approx(-0.135152, abs=1e-6)  # Fonctionnaires!AY1


def test_impot_public_total_ligne_6():
    assert sal.impot_public(P) == pytest.approx(140_079_910_374.771, abs=TOL)


from moteur import epargne as ep
from moteur.recettes import retraites_croisiere as rc


def test_capital_par_euro_de_rente():
    assert ep.capital_par_euro_de_rente(P) == pytest.approx(15.9366, abs=1e-4)  # Socle actuariel!B16


def test_revenu_par_euro_de_capital():
    assert ep.revenu_par_euro_de_capital(P) == pytest.approx(0.0430243, abs=1e-7)


def test_rente_classe_27_5_30k():
    assert ep.rente_mensuelle(ep.epargne_annuelle(28_750, P), P) == pytest.approx(114.965, abs=1e-3)  # BB10


def test_impot_retraites_ligne_5():
    assert rc.impot_retraites(P) == pytest.approx(24_097_348_601.3389, abs=TOL)


from moteur import tva
from moteur.recettes import tva_menages as tm


def test_taux_effectifs_profils():
    t = tva.taux_effectifs(P)
    assert t["median"] == pytest.approx((0.0287723815411384, 0.152708082066367), abs=1e-12)
    assert t["tres_aise"][1] == pytest.approx(0.171267089578342, abs=1e-12)


# Valeurs v235 (€) : Salariés du privé!Z37, Fonctionnaires!Y37, Retraités!R36,
# Inactifs & Étudiants!I3 et I43, RUI!B27
CIBLES_TVA = {
    "tva_prive": 80_566_423_065.2441,
    "tva_public": 22_757_029_279.7504,
    "tva_retraites": 42_122_112_518.2071,
    "tva_etudiants": 4_275_196_804.27712,
    "tva_inactifs": 8_197_115_109.23356,
    "tva_chomeurs": 3_065_064_092.28578,
}


@pytest.mark.parametrize("fonction", list(CIBLES_TVA))
def test_tva_par_population(fonction):
    assert getattr(tm, fonction)(P) == pytest.approx(CIBLES_TVA[fonction], abs=TOL)


from moteur.recettes import entreprises as en, independants as ind, total as tot

CIBLES_ENTREPRISES = {
    "benefice_capte": -3.1122212034735e9,     # Entreprises & Dividendes!S13
    "is_beneficiaires": 148.980111518611e9,  # J20
    "is_deficitaires": 0.279880493779545e9,  # F122
    "tva_non_deductible": 76.00990116e9,     # X20
}


@pytest.mark.parametrize("fonction", list(CIBLES_ENTREPRISES))
def test_entreprises(fonction):
    assert getattr(en, fonction)(P) == pytest.approx(CIBLES_ENTREPRISES[fonction], abs=TOL)


def test_independants():
    assert ind.impot_independants(P) == pytest.approx(33.6415265661194e9, abs=TOL)
    assert ind.tva_independants(P) == pytest.approx(11.1574248590074e9, abs=TOL)
    assert ind.is_local_independants(P) == pytest.approx(1.80406606946615e9, abs=TOL)


@pytest.mark.parametrize("ligne, cible", [
    (2, 149_259_992_012.39), (3, 248_150_266_888.005), (4, 452_838_702_211.722),
    (5, 24_097_348_601.3389), (6, 140_079_910_374.771), (16, 31_837_460_496.6533),
])
def test_lignes_total(ligne, cible):
    assert tot.lignes_calculees(P)[ligne] == pytest.approx(cible, abs=TOL)


from moteur.recettes import autres as au


@pytest.mark.parametrize("ligne, cible", [
    (7, 11_961_865_379.2212), (8, 15_100_000_000), (9, 29_000_000_000), (15, 34_305_400_355.2415),
    (19, 12_682_130_400.4462), (20, 6_392_000_000),
])
def test_autres_lignes_total(ligne, cible):
    assert tot.recettes_nouveau_systeme(P)["lignes"][ligne] == pytest.approx(cible, abs=TOL)


def test_ancienne_tva():
    assert au.ancienne_tva_ligne_3(P) == pytest.approx(213_574_450_264.849, abs=TOL)


def test_recettes_totales_total_b17():
    """Critère de sortie de l'étape 1 pour les recettes statiques."""
    assert tot.recettes_nouveau_systeme(P)["total"] == pytest.approx(1_167_767_351_278, abs=TOL)


# --- Dépenses statiques -----------------------------------------------------------
from moteur.depenses import budget_etat as be, statique as st


@pytest.mark.parametrize("ligne, cible", [
    ("Intérieur", 26.7002139995783), ("Justice", 24.0029420198187), ("Armées", 73.6178056612685),
    ("Finances", 15.6771992499163), ("Affaires étrangères", 6.94169649538487), ("Éducation", 75.8632350832806),
    ("Recherche", 28.9876067427487), ("Agriculture", 4.07109373714303), ("Culture", 8.28918334954837),
    ("Écologie", 7.26545394984185), ("Sports", 1.23813948800979), ("Administration", 3.96854268070846),
    ("Autres", 11.3757254190831), ("Contribution UE", 30.3536345776031),
])
def test_missions_etat(ligne, cible):
    assert be.lignes_modele(P)[ligne] == pytest.approx(cible, abs=0.01)


@pytest.mark.parametrize("ligne, cible", [
    ("sante", 305.932977141111), ("rui_aah", 127.70289191419), ("securite_sociale_hors_sante", 17.1589964751672),
    ("autres_missions", 14.1107254190831), ("subventions_restees", 15.213), ("collectivites", 15.9119989539),
])
def test_lignes_depenses(ligne, cible):
    assert st.depenses(P)["lignes"][ligne] == pytest.approx(cible, abs=0.01)


def test_depenses_totales_total_b44():
    """Avec quatre termes encore provisoires (coût de transition, IA, économies des missions, quotient familial)."""
    assert st.depenses(P)["total"] == pytest.approx(1217.58240587589, abs=0.01)


# --- Transition des retraites et IA ---------------------------------------------
from moteur import retraites_transition as rt
from moteur.depenses import ia_administration as iam
import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "outils"))


def _serie(feuille, colonne, ligne0):
    from arbre import VAL
    return [VAL[(feuille, f"{colonne}{ligne0 + i}")] for i in range(45)]


def test_cout_transition_par_annee():
    """Coût transition!F5:F49 (coût net lissé), 2029-2073."""
    c = rt.cout_transition(P)
    for an, cible in zip(rt.ANNEES, _serie("Coût transition", "F", 5)):
        assert c[an]["net"] == pytest.approx(cible, abs=0.01), an


def test_participations_remises_au_fonds_v235():
    c = rt.cout_transition(P)
    for an, cible in zip(rt.ANNEES, _serie("Coût transition", "V", 5)):
        assert c[an]["participations"] == pytest.approx(cible, abs=0.01), an


def test_cout_transition_moyen():
    assert rt.cout_transition_moyen(P) == pytest.approx(132.911922023133, abs=0.01)


def test_ia_administration():
    e = iam.economie_nette(P)
    for an, cible in zip(iam.ANNEES, _serie("IA administration", "E", 13)):
        assert e[an] == pytest.approx(cible, abs=0.01), an
