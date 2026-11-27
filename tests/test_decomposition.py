"""Décomposition du déficit et variantes communes de la dette (phase 3.1, 16/11/2026)."""
import pytest

from moteur import decomposition as dc
from moteur import noyau
from moteur.parametres import Parametres
from outils import variantes_dette as vd


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def sq(p):
    return noyau.simuler(p)


@pytest.mark.parametrize("nom", ["lisnard", "melenchon", "philippe"])
def test_decomposition_exacte(p, sq, nom):
    """Les composantes redonnent l'écart de déficit, entre deux années comme entre programme et statu quo."""
    res = noyau.simuler(p, noyau.charger(nom))
    for s in res:
        for t in (2030, 2037, 2050, 2073):
            for a, b in ((res[s][2029], res[s][t]), (sq[s][t], res[s][t]), (sq[s][2029], sq[s][t])):
                e = dc.ecart(a, b)
                assert abs(e["residu"]) < 1e-9
            n = dc.niveau(res[s][t])
            assert abs(n["residu"]) < 1e-9


def test_composantes_du_taux(sq):
    """Le taux apparent est la somme de ses composantes publiées."""
    for traj in sq.values():
        for x in traj.values():
            assert x["taux_apparent"] == pytest.approx(x["taux_base"] + x["taux_fisher"] + x["taux_bce"] + x["taux_prime"] + x["taux_scenario"], abs=1e-15)


def test_convention_2027_2028_par_defaut(p):
    """Décision D3 d'Adrien (27/11/2026) : 2027 et 2028 projetées avec la croissance de la Banque de France."""
    assert noyau.facteur_2027_2028(p) == pytest.approx(1.009 * 1.012)


def test_variantes(p, sq):
    """Calcul principal sans prime de dette (27/11/2026) ; la variante « avec la réaction des marchés » la remet et
    creuse le déficit du statu quo ; taux long plus bas : moins d'intérêts ; croissance en 2027-2028 : dette de départ
    plus basse, flux inchangés."""
    assert all(abs(x["taux_prime"]) < 1e-12 or x["taux_prime"] == p.val("macro.prime_dette_bornes")[0] for x in sq["prudent"].values())
    avec = noyau.simuler(vd._variante(p, vd.VARIANTES["avec_reaction_marches"]), scenarios=["prudent"])["prudent"]
    assert avec[2050]["taux_prime"] > 0.01 and avec[2050]["deficit"] > sq["prudent"][2050]["deficit"]
    bas = noyau.simuler(vd._variante(p, vd.VARIANTES["taux_long_3_3"]), scenarios=["prudent"])["prudent"]
    assert bas[2040]["deficit"] < sq["prudent"][2040]["deficit"]
    # 27/11/2026 (D3) : le calcul publié projette 2027-2028 (Banque de France) ; la variante remet l'économie de 2026
    # en 2029 : dette de départ plus haute, flux inchangés
    assert noyau.facteur_2027_2028(p) == pytest.approx(1.009 * 1.012)
    q = vd._variante(p, vd.VARIANTES["economie_2026_en_2029"])
    assert noyau.facteur_2027_2028(q) == pytest.approx(1.0)
    cr = noyau.simuler(q, scenarios=["prudent"])["prudent"]
    assert cr[2029]["dette_debut"] == pytest.approx(sq["prudent"][2029]["dette_debut"] * (1.009 * 1.012))
    assert cr[2029]["solde_primaire"] == pytest.approx(sq["prudent"][2029]["solde_primaire"])


def test_aux_taux_statu_quo():
    """26/11/2026 : dette et déficit aux taux du statu quo. Pour le statu quo, ses propres comptes ; pour un programme
    inflationniste, plus de dette que dans le calcul principal (27/11 : son inflation n'efface plus sa dette) ; les
    intérêts de la dette en plus restent comptés (plus de déficit que le seul primaire)."""
    from moteur import decomposition as dc
    from moteur import noyau
    from moteur.parametres import Parametres
    p = Parametres()
    base = noyau.simuler(p, None, scenarios=("prudent",))["prudent"]
    a = dc.aux_taux_statu_quo(base, base)
    assert all(abs(a[t]["dette_pib"] - base[t]["dette_pib"]) < 1e-9 for t in base)
    assert all(abs(a[t]["deficit"] - base[t]["deficit"]) < 1e-9 for t in base)
    r = noyau.simuler(p, noyau.charger("melenchon"), scenarios=("prudent",))["prudent"]
    b = dc.aux_taux_statu_quo(r, base)
    assert b[2037]["dette_pib"] > r[2037]["dette_pib"]
    assert b[2037]["deficit"] > -r[2037]["solde_primaire"] / r[2037]["pib"] * 100
