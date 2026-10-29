"""Ménages types et système actuel calculé par OpenFisca."""
import pytest

from moteur.epargne import epargne_annuelle, net_apres_impot, part_rui_salarie
from moteur.menages_types import comparer, definitions, impot_menage, nouveau
from moteur.impot_unique import impot
from moteur.parametres import Parametres
from moteur.systeme_actuel import nets_prive, nets_public, _table_openfisca

P = Parametres()


def test_personne_seule_coherente_avec_le_moteur():
    m = {"adultes": ["median"], "enfants": []}
    n = nouveau(m, P)
    c = P.val("profils.cout_median_annuel")
    attendu = net_apres_impot(c, P) - n["impot_local"] - epargne_annuelle(c, P, "prudent", part_rui_salarie(c, P), contribution=False)
    assert n["revenu_disponible"] == pytest.approx(attendu)


def test_quotient_conjugal_et_familial():
    assert impot_menage([50000, 0], 0, P) == pytest.approx(2 * impot(25000, P))
    sans = impot_menage([60000], 0, P)
    avec = impot_menage([60000], 2, P)
    assert sans - avec <= 2 * P.val("quotient.plafond_demi_part") + 1e-9
    assert avec <= sans


def test_tables_openfisca_croissantes():
    for v in (None, "etat_civils", "territoriale", "hospitaliere"):
        T = _table_openfisca(versant=v)
        assert all(b >= a for a, b in zip(T["cout_du_travail"], T["cout_du_travail"][1:]))
    a, b = nets_prive(P)["avant_aides"], nets_public(P)["avant_aides"]
    assert all(y >= x for x, y in zip(a, a[1:])) and all(y >= x for x, y in zip(b, b[1:]))


def test_tous_les_menages_comparés():
    r = comparer(P)
    assert len(r) == len(definitions())
    assert all(x["actuel"]["revenu_disponible"] > 0 and x["nouveau"]["revenu_disponible"] > 0 for x in r)
