"""Phase L (roadmap du comparateur, 4.1, 18/11/2026) : dépenses sensibles au chômage sur les chômeurs du programme.

Les blocs chômage et pauvreté suivent les chômeurs du programme ; l'allocation évitée n'est plus dans la valeur d'un
emploi des canaux. Ce qui est vérifié : la formule, le partage entre les deux blocs, les canaux exclus et le retour à
l'ancien calcul quand l'option est coupée."""
import pytest

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import Parametres
from moteur.programme_simple import ProgrammeSimple


@pytest.fixture(scope="module")
def p():
    return Parametres()


def test_statu_quo_sans_depense_en_plus(p):
    r = noyau.trajectoire(p, "prudent")
    assert all(r[t]["depenses_chomage_programme"] == 0.0 for t in (2029, 2037, 2050))


@pytest.mark.parametrize("nom", ["lisnard", "roussel", "tondelier"])
def test_formule_et_partage_des_blocs(p, nom):
    prog = noyau.charger(nom)
    s, t = "prudent", 2037
    ctx = prog.contexte(p)[s]
    r = noyau.simuler(p, prog, scenarios=[s])[s][t]
    e, w = sq.effectifs(p, s), sq.salaires(p, s)
    d_ch = ctx["chomeurs_depenses"][t] - r["pib_taux"] / r["pib"] * sq._v(p, "macro.emplois_par_point_pib", s) * e[t]["emploi"]
    attendu = d_ch * p.val("emploi.allocation_chomeur_evitee") * w[t] / w[2029] / 1e9
    assert r["depenses_chomage_programme"] == pytest.approx(attendu, rel=1e-9)
    # partage : la part de l'assurance chômage va au bloc chômage, le reste au bloc pauvreté
    p0 = p.avec({"emploi.depenses_chomage_programme": False})
    r0 = noyau.simuler(p0, noyau.charger(nom), scenarios=[s])[s][t]
    assert r0["depenses_chomage_programme"] == 0.0
    assert "chomeurs_depenses" not in noyau.charger(nom).contexte(p0)[s]


def test_canaux_exclus():
    canaux = {2037: {"SMIC : emplois perdus": -100.0, "Postes publics : 32 heures": 50.0, "Seniors : emploi": 30.0,
                     "Démographie : solde migratoire": 20.0, "Conjoncture (impulsion budgétaire)": 10.0,
                     "Offre : gain à travailler": 8.0}}
    budget = {"SMIC : emplois perdus", "Postes publics : 32 heures"}
    from moteur.noyau import ANNEES
    canaux = {t: canaux[2037] for t in ANNEES}
    actifs = {t: 3.0 for t in ANNEES}
    d = ProgrammeSimple.chomeurs_depenses(canaux, actifs, budget)
    # SMIC (budget compté), seniors et démographie exclus ; postes publics, conjoncture et offre comptés, moins les
    # actifs en plus de l'offre
    assert d[2037] == pytest.approx(-(50.0 + 10.0 + 8.0 - 3.0))


def test_allocation_retiree_de_la_valeur_d_un_emploi(p):
    """Un canal sans « * » vaut emploi.valeur_emploi moins l'allocation : l'allocation est dans les blocs."""
    prog = noyau.charger("glucksmann")
    m = [x for x in prog.mesures(p)["prudent"] if x.nom == "Emploi : Assurance chômage plus généreuse : chômeurs en plus"]
    p0 = p.avec({"emploi.depenses_chomage_programme": False})
    m0 = [x for x in noyau.charger("glucksmann").mesures(p0)["prudent"]
          if x.nom == "Emploi : Assurance chômage plus généreuse : chômeurs en plus"]
    v, a = prog.v("emploi.valeur_emploi"), p.val("emploi.allocation_chomeur_evitee")
    assert m[0].valeurs[2037] / m0[0].valeurs[2037] == pytest.approx((v - a) / v, rel=1e-6)
