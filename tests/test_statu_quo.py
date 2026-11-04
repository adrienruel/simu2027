"""Scénario sans réforme (moteur/statu_quo.py) : indépendance vis-à-vis des programmes, identités comptables,
calage de départ et validation contre le COR (rapport annuel de juin 2026)."""

import pytest

from moteur import parametres as mp
from moteur import statu_quo as sq
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def res(p):
    return sq.simuler(p)


def test_independant_du_programme(tmp_path, monkeypatch, res):
    """Le statu quo ne lit aucun paramètre d'un programme : avec un programme vide, il est identique."""
    (tmp_path / "programmes" / "vide").mkdir(parents=True)
    (tmp_path / "programmes" / "vide" / "parametres.yaml").write_text("# programme vide\n", encoding="utf-8")
    monkeypatch.setattr(mp, "RACINE", tmp_path)
    vide = sq.simuler(Parametres(programme="vide"))
    for s in sq.SCENARIOS:
        for t in (2029, 2050, 2073):
            assert vide[s][t]["deficit"] == pytest.approx(res[s][t]["deficit"], abs=1e-12)


def test_identites_comptables(p, res):
    infl = sq.inflation(p, "prudent")
    v = res["prudent"]
    dette_prec = sq.dette_fin_2028(p)
    for t in sq.ANNEES:
        x = v[t]
        assert x["depenses_primaires"] == pytest.approx(sum(x["blocs"].values()))
        assert x["dette"] == pytest.approx(dette_prec - x["solde"])
        assert x["deficit"] == pytest.approx(-(x["solde"] - infl[t] * dette_prec) / x["pib"] * 100)
        dette_prec = x["dette"]


def test_depart_cale_sur_le_plf_2027(p, res):
    x = res["prudent"][2029]
    # recettes du PLF 2027 (51,9 %) moins la CVAE qui baisse de 0,28 % à 0,09 % de 2027 à 2029 (loi en vigueur)
    baisse_cvae = 3.0 * (1 - 0.0009 / 0.0028) / sq.pib_2026(p) * 100
    assert x["recettes_pib"] == pytest.approx(51.9 - baisse_cvae, abs=0.01)
    assert x["retraites_pib"] == pytest.approx(14.1, abs=0.01)
    # dépense primaire de 2027 (54,0 %) + deux années de dérive de la santé (régulation de 2027-2029)
    assert 54.0 < x["depenses_primaires_pib"] < 54.3
    assert sq.depart(p)["blocs"]["autres"] > 0
    # 2029 : déficit de 2027 + intérêts recalculés sur la dette de fin 2028
    assert 5.0 < x["deficit"] < 6.0


def test_chomage_de_depart(p):
    assert sq.effectifs(p, "prudent")[2026]["taux_chomage"] == pytest.approx(p.val("chomage.taux_2026"))


def _part_retraites(p, t, productivite=None):
    q = p if productivite is None else p.avec({"macro.tendance": productivite, "macro.ia_productivite": 0.0})
    return sq.retraites(q, "prudent")[t]["depenses"] / sq.pib(q, "prudent")[t] * 100


def test_retraites_calees_sur_le_cor(p):
    """Seul paramètre calé : l'érosion relative, sur 15,3 % du PIB en 2070 (productivité 0,7 %)."""
    assert _part_retraites(p, 2070) == pytest.approx(15.3, abs=0.1)


def test_retraites_controles_hors_calage(p):
    """Contrôles non calés : 2030 (COR 14,1 %), 2045 (COR 14,2 %) et les variantes de productivité du COR
    (0,4 % : 16,1 % ; 1,0 % : 14,5 % en 2070)."""
    assert _part_retraites(p, 2030) == pytest.approx(14.1, abs=0.15)
    assert _part_retraites(p, 2045) == pytest.approx(14.2, abs=0.15)
    assert _part_retraites(p, 2070, 0.004) == pytest.approx(16.1, abs=0.3)
    assert _part_retraites(p, 2070, 0.010) == pytest.approx(14.5, abs=0.3)
    assert _part_retraites(p, 2070, 0.004) > _part_retraites(p, 2070, 0.007) > _part_retraites(p, 2070, 0.010)


def test_prestations_indexees_sur_les_prix_perdent_du_poids(res):
    """À législation constante, les prestations revalorisées sur les prix baissent en part du PIB quand la
    productivité monte ; les dépenses qui suivent le PIB gardent leur part."""
    a, b = res["prudent"][2029], res["prudent"][2073]
    assert b["blocs"]["famille"] / b["pib"] < a["blocs"]["famille"] / a["pib"]
    assert b["blocs"]["investissement"] / b["pib"] == pytest.approx(a["blocs"]["investissement"] / a["pib"])


def test_sans_prime_de_dette_la_dette_monte_moins(p, res):
    q = sq.simuler(p.avec({"macro.prime_dette": 0.0}))
    assert q["prudent"][2050]["dette_pib"] < res["prudent"][2050]["dette_pib"]
    assert q["prudent"][2029]["deficit"] == pytest.approx(res["prudent"][2029]["deficit"])


def test_ordre_des_scenarios(res):
    """Plus de productivité et de fécondité : un statu quo moins dégradé."""
    t = 2050
    assert res["optimiste"][t]["dette_pib"] < res["median"][t]["dette_pib"] < res["prudent"][t]["dette_pib"]


def test_ecart_avec_un_programme(p, res):
    from moteur.simulation import simuler
    e = sq.ecart(simuler(p), res)
    assert set(e) == set(sq.SCENARIOS)
    assert set(e["prudent"][2037]) == {"deficit", "solde_primaire", "dette_pib", "chomage", "pib"}


def test_prelevements_sur_les_salaires_controles_par_openfisca(p):
    """Deux calculs indépendants : OpenFisca sur les distributions de salaires de 2026, et la répartition des
    recettes (reconstitution de la v235, calée sur le PLF 2027). Écart sous 3 %."""
    a = sq.prelevements_activite(p)
    r = sq.recettes_par_impot(p, "prudent")[2029]
    assert a["prive"]["prelevements"] == pytest.approx(r["salaires_prive"], rel=0.03)
    assert a["public"]["prelevements"] == pytest.approx(r["salaires_public"], rel=0.03)


def test_prelevements_sur_les_pensions_par_openfisca(p):
    """CSG, CRDS, CASA et impôt sur le revenu des retraités : OpenFisca sur la distribution de la DREES retrouve la
    répartition des recettes (reconstitution de la v235) à 2 % près ; à barèmes sur les prix, taux moyen stable ;
    à barèmes sur les salaires, il baisse quand les pensions baissent par rapport aux salaires."""
    pr = sq.prelevements_retraites(p, "prudent")
    r = sq.recettes_par_impot(p, "prudent")
    assert pr[2029]["total"] == pytest.approx(r[2029]["retraites"], rel=0.02)
    ret = sq.retraites(p, "prudent")
    q = p.avec({"statu_quo.baremes_retraites": "salaires"})
    pq = sq.prelevements_retraites(q, "prudent")
    taux = {t: pq[t]["total"] / ret[t]["depenses"] for t in (2029, 2073)}
    assert taux[2073] < taux[2029]  # barèmes sur les salaires : le taux baisse avec la pension relative
    assert pr[2073]["total"] / ret[2073]["depenses"] == pytest.approx(pr[2029]["total"] / ret[2029]["depenses"], abs=0.01)


def test_tva_par_source_de_revenu(p):
    """TVA du statu quo calée sur la répartition des recettes ; le calcul par source de revenu (fonction de
    consommation, revenus OpenFisca) en explique au moins 85 % ; la TVA des retraités recoupe le calcul de la v235
    (recettes.autres.tva_retraites_actuelle, Md€ de 2024)."""
    from moteur.recettes.autres import tva_retraites_actuelle
    from moteur.unites import facteur
    tv = sq.tva(p, "prudent")
    assert tv[2029]["total"] == pytest.approx(sq.recettes_par_impot(p, "prudent")[2029]["tva"])
    assert 1.0 <= tv["calage"] < 1.15
    ref = tva_retraites_actuelle(p) / 1e9 * facteur(p, 2024, "recettes")
    assert tv[2029]["retraites"] / tv["calage"] == pytest.approx(ref, rel=0.10)


def test_cvae_eteinte_en_2030(p):
    """Législation en vigueur : la CVAE (0,28 % en 2027) baisse à 0,09 % en 2029 et disparaît en 2030."""
    r, y = sq.recettes_par_impot(p, "prudent"), sq.pib(p, "prudent")
    d = sq.recettes_par_impot_depart(p)["impots_de_production"]
    part = {t: r[t]["impots_de_production"] / y[t] for t in (2029, 2030, 2050)}
    y0 = sq.pib_2026(p)
    assert part[2029] == pytest.approx((d - 3.0 * (1 - 0.0009 / 0.0028)) / y0)
    assert part[2030] == pytest.approx((d - 3.0) / y0)
    assert part[2050] == pytest.approx(part[2030])


def test_prime_activite_a_bareme_constant(p):
    """Législation constante : barème de la prime d'activité fixe en euros constants, salaires qui montent ; moins de
    salariés y ont droit (rien ne change sans croissance des salaires)."""
    pa = sq.prime_activite_relative(p, "prudent")
    assert pa[2029] == pytest.approx(1.0)
    assert pa[2073] < pa[2050] < pa[2037] < 1.0
    q = p.avec({"macro.tendance": 0.0, "macro.ia_productivite": 0.0})
    assert sq.prime_activite_relative(q, "prudent")[2073] == pytest.approx(1.0)


def test_depenses_identifiees_et_reste(p):
    """État mission par mission, défense et UE, collectivités : le reste (Sécurité sociale hors blocs, opérateurs)
    est positif et de l'ordre de 100 Md€ (gestion des caisses, action sociale, opérateurs financés par des taxes
    affectées ≈ 22 Md€) ; un reste négatif signalerait un double compte."""
    b = sq.depart(p)["blocs"]
    assert 50 < b["autres"] < 150
    assert 180 < b["etat_missions"] < 260
    assert 200 < b["collectivites"] < 260
    m = {x["mission"]: x for x in sq.missions_etat(p)}
    assert not any(k.startswith(sq.EXCLUES) for k in m)
    assert m["Engagements financiers hors charge de la dette"]["regle"] == "prix"


def test_validation_hcfp_et_cour_des_comptes(p, res):
    """Point de départ contre les projections publiques (HCFP, avis n° 2026-5 ; Cour des comptes, juin 2026) :
    dette d'environ 122 % fin 2027, +2,5 points par an ; intérêts 91 Md€ en 2027, +12 Md€ par an ; un déficit
    primaire d'environ 2 % fait monter la dette (la Cour : il faudrait un excédent primaire pour la réduire)."""
    assert 122 < sq.dette_fin_2028(p) / sq.pib_2026(p) * 100 < 128
    assert 91 < res["prudent"][2029]["charge_dette"] < 115
    x = res["prudent"]
    assert x[2029]["solde_primaire"] < 0 and x[2035]["dette_pib"] > x[2029]["dette_pib"]


def test_retraites_entre_commission_europeenne_et_cor(res):
    """Commission européenne (rapport sur le vieillissement 2024, démographie plus ancienne : fécondité plus haute) :
    13,6 % du PIB en 2070 ; COR 2026 (même démographie que le modèle) : 15,3 %. Le statu quo suit le COR."""
    r = res["prudent"]
    assert 13.6 < r[2070]["retraites_pib"] <= 15.4


def test_indexation_des_prestations(p):
    """Prestations sur les salaires (décision d'Adrien) : plus de dépense que sur les prix, sans effet en 2029."""
    sal = sq.blocs(p.avec({"statu_quo.indexation_prestations": "salaires"}), "prudent")
    prix = sq.blocs(p.avec({"statu_quo.indexation_prestations": "prix"}), "prudent")
    for b in ("famille", "logement", "pauvrete", "aah_invalidite"):
        assert sal[2029][b] == pytest.approx(prix[2029][b])
        assert sal[2060][b] > prix[2060][b]
