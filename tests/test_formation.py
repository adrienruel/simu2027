"""Canal commun « formation_superieure » (phase Q, moteur/qualifications.py) : diplômés en plus par cohorte,
absorption par le besoin de postes, excédent (déclassés, partis), coût, profils."""
import pytest

from moteur import canaux_declares, noyau, qualifications as q
from moteur import statu_quo as sq
from moteur.noyau import ANNEES
from moteur.parametres import Parametres

P = Parametres()
SQ = P.val("formation_superieure.diplomes_statu_quo")


def decl(objectif, debut=2028, plein=2032):
    return {"filiere": "ingenieurs", "objectif": objectif, "debut": debut, "plein": plein}


def gain(objectif, s="prudent", t=2060):
    return q.pib(P, s, decl(objectif))["productivite"][t]


def test_filiere_inconnue_refusee():
    with pytest.raises(ValueError, match="filière inconnue"):
        q.flux_vise(P, {"filiere": "medecins", "objectif": 1, "debut": 2028, "plein": 2030})


def test_objectif_sous_le_statu_quo_ne_fait_rien():
    d = decl(SQ - 1000)
    assert q.flux_vise(P, d) == 0
    assert all(v == 0 for v in q.cout(P, "prudent", d, ANNEES).values())
    assert all(v == 0 for x in q.pib(P, "prudent", d).values() for v in x.values())


def test_conservation_des_cohortes():
    for s in sq.SCENARIOS:
        for c in q.cohortes(P, s, decl(100_000)).values():
            assert c["absorbes"] + c["excedent"] == pytest.approx(c["diplomes"])
            assert c["absorbes"] >= 0 and c["excedent"] >= -1e-9


def test_sous_le_besoin_tout_est_absorbe_et_le_gain_est_proportionnel():
    """Petit flux en plus (sous le besoin annuel) : aucun excédent, gain proportionnel au flux."""
    petit = SQ + 0.25 * P.val("formation_superieure.besoin_annuel", "crise") / P.val("formation_superieure.part_objectif_atteinte", "prudent")
    d = decl(petit)
    assert all(c["excedent"] == pytest.approx(0, abs=1e-6) for c in q.cohortes(P, "prudent", d).values())
    double = decl(SQ + 2 * (petit - SQ))
    assert all(c["excedent"] == pytest.approx(0, abs=1e-6) for c in q.cohortes(P, "prudent", double).values())
    assert gain(SQ + 2 * (petit - SQ)) == pytest.approx(2 * gain(petit), rel=1e-9)


def test_offre_au_dela_du_besoin_gain_marginal_decroissant():
    """Au-delà du besoin, chaque diplômé en plus rapporte moins (déclassés, départs) : gain marginal décroissant."""
    for s in ("crise", "prudent", "median"):
        g1, g2, g3 = gain(70_000, s) - gain(SQ, s), gain(100_000, s) - gain(70_000, s), gain(130_000, s) - gain(100_000, s)
        assert g1 / (70_000 - SQ) > g2 / 30_000 > g3 / 30_000 > 0
        assert sum(c["excedent"] for c in q.cohortes(P, s, decl(130_000)).values()) > 0


def test_ordre_des_scenarios():
    d = decl(100_000)
    g = [q.pib(P, s, d)["productivite"][2050] for s in sq.SCENARIOS]
    c = [q.cout(P, s, d, [2040])[2040] for s in sq.SCENARIOS]
    r = [q.pib(P, s, d)["entree_retardee"][2040] for s in sq.SCENARIOS]
    assert g == sorted(g) and c == sorted(c, reverse=True) and r == sorted(r)


def test_premiers_diplomes_apres_les_etudes():
    d = decl(100_000)
    for s in sq.SCENARIOS:
        delai = P.val("formation_superieure.delai_diplome", s)
        assert q.diplomes(P, s, d, 2028 + delai - 1) == 0 < q.diplomes(P, s, d, 2028 + delai)
        assert q.places(P, s, d, 2028) > 0


def test_profil_statu_quo_cale_sur_l_iesf():
    st = q.stock_statu_quo(P, "prudent")
    assert sum(st[ANNEES[0]].values()) == pytest.approx(P.val("formation_superieure.stock_en_activite"))
    pr = q.profils(P, "prudent", decl(100_000))
    assert pr[2050]["part_emploi_programme"] > pr[2050]["part_emploi_statu_quo"]
    assert q.profils(P, "prudent", None)[2050]["part_emploi_programme"] == pr[2050]["part_emploi_statu_quo"]
    pa = q.par_age(P, "prudent", decl(100_000), [2050])[2050]
    d = q.detail(P, "prudent", decl(100_000))[2050]
    assert sum(x["absorbes"] for x in pa.values()) == pytest.approx(d["absorbes_en_emploi"])
    assert sum(x["declasses"] for x in pa.values()) == pytest.approx(d["declasses_en_emploi"])


def test_philippe_passe_par_le_canal_commun():
    prog = noyau.charger("philippe")
    assert "formation_superieure" in canaux_declares.declares(prog)
    assert not any(k.startswith("philippe_mesures.ingenieurs") for k in prog.pt._p)
    p = Parametres(programme="philippe")
    noms = [m.nom for m in prog.mesures(p)["prudent"]]
    assert any(n.startswith("PHI-NUM-03") for n in noms)
    assert any("formation supérieure, diplômés en plus" in n for n in noms)
