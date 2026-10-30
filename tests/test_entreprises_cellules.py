"""Entreprises par taille (moteur/entreprises_cellules.py)."""
import pytest

from moteur.entreprises_cellules import bilan, facteur_production, tailles
from moteur.parametres import Parametres
from moteur.recettes.entreprises import is_beneficiaires

P = Parametres()


def test_parts_somment_a_un():
    t = tailles(P)
    for k in ("part_production", "part_investissement", "part_benefices"):
        assert sum(x[k] for x in t) == pytest.approx(1.0)
    # élasticité moyenne pondérée par l'investissement inchangée
    assert sum(x["part_investissement"] * x["elasticite_normee"] for x in t) == pytest.approx(1.0)


def test_is_actuel_cale_sur_la_dgfip():
    from moteur.unites import facteur
    assert sum(x["is_actuel"] for x in bilan(P)) == pytest.approx(69.0 * facteur(P, 2024, "recettes"), rel=0.01)


def test_deplacement_vers_les_petites():
    b = {x["taille"]: x for x in bilan(P)}
    assert b["TPE"]["ecart_pct"] > b["PME"]["ecart_pct"] > b["ETI"]["ecart_pct"] > b["GE"]["ecart_pct"]
    assert b["GE"]["ecart"] < 0 < b["TPE"]["ecart"]


def test_impots_production_des_deficitaires_hors_base():
    sans = Parametres().avec({"entreprises_cellules.active": False})
    assert facteur_production(sans) == 1.0
    assert 0.75 < facteur_production(P) < 1.0
    assert is_beneficiaires(P) < is_beneficiaires(sans)


def test_v235_inchangee():
    assert not Parametres(reference="v235").val("entreprises_cellules.active")


def test_dirigeants_payes_en_salaire():
    from moteur.entreprises_cellules import arbitrage_tpe
    a = {j: arbitrage_tpe(P, j) for j in ("crise", "prudent", "median", "optimiste")}
    assert a["crise"]["perte"] > a["prudent"]["perte"] > a["median"]["perte"] > a["optimiste"]["perte"] > 0
    # on ne perd jamais plus que l'IS et la flat tax du bénéfice passé en salaire
    assert a["prudent"]["perte"] < 0.64 * a["prudent"]["salaire"]
    sans = Parametres().avec({"entreprises_cellules.arbitrage_tpe/active": False})
    assert arbitrage_tpe(sans)["perte"] == 0.0


def test_bilan_avec_deduction_et_interets():
    from moteur.entreprises_cellules import bilan_annees
    b = {x["taille"]: x for x in bilan(P)}
    for t, lignes in bilan_annees(P, (2037, 2073)).items():
        for x in lignes:
            assert x["deduction"] > 0 and x["interets"] > 0
            assert x["ecart"] == pytest.approx(b[x["taille"]]["ecart"] - x["deduction"] + x["interets"])


def test_deduction_sur_l_is_local_aussi():
    from moteur.is_investissement import cout_net_etat
    sans = Parametres().avec({"is_investissement.assiette_locale": False})
    assert cout_net_etat(P)[2037] == pytest.approx(cout_net_etat(sans)[2037] * 0.45 / 0.40, rel=1e-6)
