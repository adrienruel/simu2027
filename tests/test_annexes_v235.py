"""Étape 1 : feuilles annexes de la trajectoire, contre la v235."""
import sys
from pathlib import Path

import pytest
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outils"))
from arbre import VAL  # noqa: E402

from moteur.parametres import Parametres

P = Parametres(reference="v235")
ANNEES = list(range(2029, 2074))


def serie(feuille, ligne):
    return [VAL[(feuille, f"{get_column_letter(i + 2)}{ligne}")] for i in range(45)]


def comparer(calcule: dict, feuille: str, ligne: int, tol=0.01):
    for t, cible in zip(ANNEES, serie(feuille, ligne)):
        assert calcule[t] == pytest.approx(cible, abs=tol), (feuille, ligne, t)


def test_calendrier():
    from moteur import calendrier
    a = calendrier.annees_2027_2028(P)
    assert a[2027]["dette"] == pytest.approx(VAL[("Calendrier budgétaire", "I18")], abs=0.01)
    assert a[2028]["dette"] == pytest.approx(VAL[("Calendrier budgétaire", "I19")], abs=0.01)


def test_successions():
    from moteur.recettes import successions, autres
    comparer(successions.supplement(P, autres.ligne_8_successions(P) / 1e9), "Successions", 15)


def test_ascenseur_social():
    from moteur.ascenseur_social import annuel
    from moteur.recettes import autres
    a = annuel(P, autres.ligne_8_successions(P) / 1e9, P.val("successions.exoneration_entreprises"))
    comparer({t: v["recettes"] for t, v in a.items()}, "Ascenseur social", 57)
    comparer({t: v["depenses"] for t, v in a.items()}, "Ascenseur social", 53)


def test_economies_registre():
    from moteur.mesures import economies
    comparer(economies(P), "Économies", 28)


@pytest.mark.parametrize("scenario, ligne", [("prudent", 49), ("median", 50), ("optimiste", 51)])
def test_sante(scenario, ligne):
    from moteur import sante
    comparer(sante.depenses(P, scenario), "Santé", ligne)


def test_tva_sante():
    from moteur import sante
    tv = sante.tva_sante(P)
    comparer(tv["prudent"], "Santé", 85)
    comparer(tv["median"], "Santé", 86)


def test_logement_reprise_amortissements():
    from moteur.logement import reprise_amortissements
    comparer(reprise_amortissements(P), "Logement", 104)


@pytest.mark.parametrize("scenario, col", [("prudent", "B"), ("median", "C"), ("optimiste", "D")])
def test_hauts_revenus(scenario, col):
    from moteur import hauts_revenus as hr
    assert hr.reactions(P)[scenario]["montant"] == pytest.approx(VAL[("Hauts revenus", f"{col}9")], abs=0.01)
    assert hr.baisse_revenus_declares(P)[scenario] == pytest.approx(VAL[("Effets macro", f"{col}226")], abs=0.01)


def test_emploi():
    from moteur import emploi as em
    e = em.effets_reformes(P)
    for j, col in (("crise", "D"), ("median", "E"), ("optimiste", "F")):
        assert e[j]["emplois"] == pytest.approx(VAL[("Emploi", f"{col}22")], abs=1)
    assert em.cout_reformes(P) == pytest.approx(VAL[("Emploi", "G24")], abs=0.01)
    assert em.gain_par_emploi(P, "prudent") == pytest.approx(VAL[("Emploi", "B245")], abs=0.01)


@pytest.mark.parametrize("scenario, ligne", [("prudent", 72), ("median", 73), ("optimiste", 74)])
def test_carbone(scenario, ligne):
    from moteur import carbone
    from moteur.recettes.total import ligne_3_tva
    comparer(carbone.effet_solde(P, ligne_3_tva(P) / 1e9)[scenario], "Carbone", ligne)


@pytest.mark.parametrize("etale, ligne", [(False, 41), (True, 78)])
def test_is_investissement(etale, ligne):
    from moteur.is_investissement import cout_net_etat
    comparer(cout_net_etat(P, etale), "IS investissement", ligne)


def test_collectivites_point_fixe():
    from moteur import collectivites as co
    t = co.taux_impot_local(P)
    assert t == pytest.approx(VAL[("Collectivités", "B32")], abs=1e-8)
    assert abs(co.taux_calcule(P) - t) < 1e-12  # le taux finance bien le besoin qu'il induit
    b = co.besoin(P)
    assert b["communes"] == pytest.approx(VAL[("Collectivités", "B27")], abs=0.01)
    assert b["regions"] == pytest.approx(VAL[("Collectivités", "C27")], abs=0.01)


def test_quotient():
    from moteur.depenses import quotient as q
    assert q.cout(P)["total"] == pytest.approx(VAL[("Total", "B122")], abs=0.01)


def test_economies_missions():
    from moteur.depenses import economies_missions as em
    e = em.economies(P)
    assert e["missions"] == pytest.approx(VAL[("Budget État 2026", "D105")], abs=0.01)
    assert e["autres"] == pytest.approx(VAL[("Budget État 2026", "D111")], abs=0.01)


def test_anciennes_pensions():
    from moteur.anciennes_pensions import recette_nette
    comparer(recette_nette(P), "Anciennes pensions", 85)


def test_plus_aucune_entree_provisoire():
    """Étape 1 : le moteur ne lit plus aucune valeur calculée de la v235 (seuls les tests le font)."""
    racine = Path(__file__).resolve().parents[1] / "moteur"
    for f in racine.rglob("*.py"):
        texte = f.read_text(encoding="utf-8")
        assert "arbre" not in texte and "entrees_provisoires" not in texte, f
