"""Canal d'offre commun (6 novembre 2026)."""

import pytest

from moteur import noyau, offre
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres


@pytest.fixture(scope="module")
def p():
    return Parametres()


def _baisse(instrument, md=-30.0, poste="recettes"):
    return Mesure("essai", poste, {t: md for t in (2027, 2028, *ANNEES)}, instrument=instrument)


def test_baisse_et_hausse_symetriques_au_miroir_pres(p):
    """Baisse d'impôt : élasticité du scénario ; hausse : celle du scénario miroir (prudent → médian)."""
    y = sq.pib(p, "prudent")
    bas = offre.effets(p, "prudent", [_baisse("travail", -30.0)])
    haut = offre.effets(p, "prudent", [_baisse("travail", +30.0)])
    pts = 30.0 / y[2073] * 100
    assert bas["detail"]["travail:proportionnel"]["effet_pib_pct"][2073] == pytest.approx(
        offre.travail_par_point(p, "prudent")["pib_pct"] * pts, rel=0.02)
    assert haut["detail"]["travail:proportionnel"]["effet_pib_pct"][2073] == pytest.approx(
        -offre.travail_par_point(p, "median")["pib_pct"] * pts, rel=0.02)


def test_travail_par_cellule(p):
    """Par cellule de salaire (OpenFisca) : 1 point de PIB de prélèvements en moins ≈ +0,2 à +1 % de PIB à long terme ;
    réparti sur les bas salaires (incidence « bas »), il fait plus d'emplois que sur les hauts revenus (« haut »)."""
    x = offre.travail_par_point(p, "prudent")
    assert 0.2 < x["pib_pct"] < 1.0
    assert offre.travail_par_point(p, "prudent", "bas")["emplois"] > offre.travail_par_point(p, "prudent", "haut")["emplois"]
    assert offre.travail_par_point(p, "optimiste")["pib_pct"] > x["pib_pct"]


def test_entreprises_calees_sur_les_cohortes(p):
    """Même élasticité de l'investissement que les cohortes d'entreprises : l'effet suit macro.elasticite_invest."""
    a = offre.capital_entreprises_par_point(p, "prudent")
    q = p.avec({"macro.elasticite_invest": 2 * p.val("macro.elasticite_invest", "prudent")})
    assert 0.1 < a < 1.0
    assert offre.capital_entreprises_par_point(q, "prudent") == pytest.approx(2 * a, rel=0.01)


def test_demande_par_instrument(p):
    """Une baisse de CSG relance moins qu'une dépense publique du même montant (Kilponen et al., 2015)."""
    dep = Mesure("d", "etat_missions", {2029: 10.0})
    csg = Mesure("c", "recettes", {2029: -10.0}, instrument="travail")
    ent = Mesure("e", "recettes", {2029: -10.0}, instrument="capital_entreprises")
    i = {m.nom: offre.impulsion(p, [m], (2029,))[2029] for m in (dep, csg, ent)}
    assert i["d"] == pytest.approx(10.0) and 0 < i["e"] < i["c"] < i["d"]


def test_seniors(p):
    """Âge reculé : une part en emploi, une au chômage, le reste inactif ; âge abaissé : scénario miroir."""
    nr = {t: 100000.0 for t in ANNEES}
    k = p.val("seniors.part_concernee")
    r = offre.seniors(p, "prudent", nr)
    pe, pc = p.val("seniors.devenir", "prudent")
    assert r["emplois"][2040] == pytest.approx(k * pe * 1e5) and r["actifs"][2040] == pytest.approx(k * (pe + pc) * 1e5)
    b = offre.seniors(p, "prudent", {t: -v for t, v in nr.items()}, baisse_age=True)
    pe_m, _ = sq._v(p, "seniors.devenir", "median")
    assert b["emplois"][2040] == pytest.approx(-k * pe_m * 1e5)


def test_seniors_cales_sur_l_etude_d_impact_de_2023(p):
    """Deux ans d'âge (retour à 62 ans) : 200 000 à 400 000 emplois, autour des 300 000 de l'étude d'impact de 2023."""
    t = noyau.charger("tondelier")
    for s in ("prudent", "optimiste"):
        c = t.contexte(p)[s]["emplois_canaux"][2040]
        assert 200000 < -c["Seniors : emploi (âge de la retraite)"] < 400000, s


def test_seniors_dans_les_programmes(p):
    """65 ans (Bertrand, Zemmour) : emplois de seniors en plus ; 62 ans (Tondelier) : en moins."""
    for nom, signe in (("bertrand", 1), ("zemmour", 1), ("tondelier", -1)):
        c = noyau.charger(nom).contexte(p)["prudent"]["emplois_canaux"][2040]
        assert signe * c["Seniors : emploi (âge de la retraite)"] > 30000, nom


def test_montee_comme_mesange(p):
    """Ajustement partiel : ≈ 10 % de l'effet de long terme la première année, ≈ 40 % à cinq ans, ≈ 65 % à dix ans."""
    y = sq.pib(p, "prudent")
    m = Mesure("essai", "recettes", {t: -0.01 * y[max(t, 2029)] for t in (2027, 2028, *ANNEES)}, instrument="cout_travail")
    d = offre.effets(p, "prudent", [m])["detail"]["cout_travail"]  # 1 point de PIB chaque année
    lt = 1.0 * p.val("offre.elasticite_cout_travail", "prudent")
    e = d["effet_pib_pct"]
    assert e[2027] / lt == pytest.approx(0.1, abs=0.02)
    assert 0.35 < e[2031] / lt < 0.5
    assert 0.6 < e[2036] / lt < 0.72


def test_emplois_de_l_offre_de_travail_viennent_de_l_inactivite(p):
    d = offre.effets(p, "prudent", [_baisse("travail")])
    t = 2040
    emplois = sum(v[t] for v in d["emplois"].values())
    assert emplois > 0 and d["actifs"][t] == pytest.approx(emplois)
    c = offre.effets(p, "prudent", [_baisse("cout_travail")])
    assert sum(v[t] for v in c["emplois"].values()) > 0 and c["actifs"][t] == 0


def test_transfert_en_plus_joue_contre_l_offre(p):
    d = offre.effets(p, "prudent", [_baisse("transferts_actifs", +10.0, poste="pauvrete")])
    assert d["dpib"][2050] < 0


def test_instrument_inconnu(p):
    with pytest.raises(ValueError):
        offre.effets(p, "prudent", [_baisse("magie")])


def test_interrupteur(p):
    """Canal coupé : pas de mesure d'offre, PIB du programme sans effet d'offre."""
    z = noyau.charger("zemmour")
    avec = z.contexte(p)["prudent"]["pib"][2050]
    q = p.avec({"offre.actif": False})
    sans_mes = [m for m in noyau.charger("zemmour").mesures(q)["prudent"] if m.nom.startswith("Effet d'offre")]
    assert not sans_mes
    sans = noyau.charger("zemmour").contexte(q)["prudent"]["pib"][2050]
    assert avec > sans


def test_baisse_de_la_csg_rapporte_de_l_offre_et_hausses_de_tondelier_en_coutent(p):
    for nom, signe in (("zemmour", 1), ("tondelier", -1)):
        prog = noyau.charger(nom)
        m = [x for x in prog.mesures(p)["prudent"] if x.nom.startswith("Effet d'offre")]
        assert len(m) == 1 and signe * m[0].valeurs[2050] > 0


def test_ecologie_de_droite_hors_du_canal(p):
    """Son moteur a ses propres canaux d'offre : aucune de ses mesures ne porte d'instrument."""
    e = noyau.charger("ecologie_de_droite")
    assert all(not m.instrument for m in e.mesures(p)["prudent"])


def test_tables_openfisca_recoupent_la_bibliotheque(p):
    """Deux calculs indépendants d'OpenFisca (personne seule) : la CSG supprimée moins l'impôt sur le revenu en plus de
    la bibliothèque (tables du système actuel) et les impôts en moins de la table de réforme (outils/openfisca_offre.py)."""
    from moteur import bibliotheque as bib
    c = bib.csg_activite(p)
    net = c["csg_prive"] + c["csg_public"] - c["ir_prive"] - c["ir_public"]
    assert offre.statique_openfisca(p, "csg_activite_supprimee")["impots_en_moins"] == pytest.approx(net, rel=0.05)


def test_reformes_openfisca_dans_la_fourchette_macro(p):
    """Suppression de la CSG sur le travail, pour 1 point de PIB : effet de long terme dans la fourchette de la
    littérature (≈ 0,3 à 1 % de PIB)."""
    e = {s: offre.travail_par_point(p, s, "openfisca:csg_activite_supprimee")["pib_pct"] for s in sq.SCENARIOS}
    assert 0.2 < e["crise"] < e["prudent"] < e["median"] < e["optimiste"] < 1.3


def test_couples_ponderes_et_impot_des_menages(p):
    """Neuf cas de couples pondérés à 1 ; l'impôt sur le revenu des salariés est plus faible avec les couples qu'en
    personnes seules (quotient conjugal et familial)."""
    cas = offre._cas_couples(p)
    assert len(cas) == 9 and sum(w for _, w in cas) == pytest.approx(1.0)
    ir = offre.ir_salaries_menages(p)
    assert ir["menages"] < ir["seuls"]


def test_allegements_par_le_cout_du_travail(p):
    """Allègements arrêtés à 1,6 SMIC (Tondelier) : effet par le coût du travail (emplois pris sur le chômage),
    pas par le revenu des salariés."""
    x = offre.travail_par_point(p, "prudent", "openfisca:allegements_1_6_smic")
    assert x["emplois"] == pytest.approx(0.0, abs=1) and x["emplois_demande"] > 0
    st = offre.statique_openfisca(p, "allegements_1_6_smic")
    assert 15 < -st["prelevements_en_moins"] < 40  # hausse de cotisations patronales (Md€)


def test_investissement_public(p):
    m = Mesure("i", "investissement", {t: 10.0 for t in (2027, 2028, *ANNEES)})
    d = offre.effets(p, "prudent", [m])
    assert d["dpib"][2050] > 0
    m2 = Mesure("i", "investissement", {t: -10.0 for t in (2027, 2028, *ANNEES)})
    assert offre.effets(p, "prudent", [m2])["dpib"][2050] < -d["dpib"][2050]  # baisse : scénario miroir


def test_part_travail_d_une_mesure(p):
    """« réforme@part » : seule cette part du montant joue sur l'offre de travail."""
    a = Mesure("a", "recettes", {t: 10.0 for t in (2027, 2028, *ANNEES)}, instrument="travail",
               incidence="openfisca:csg_activite_plus1")
    b = Mesure("b", "recettes", {t: 10.0 for t in (2027, 2028, *ANNEES)}, instrument="travail",
               incidence="openfisca:csg_activite_plus1@0.5")
    assert offre.effets(p, "prudent", [b])["dpib"][2050] == pytest.approx(0.5 * offre.effets(p, "prudent", [a])["dpib"][2050])


def test_contrainte_de_capacite(p):
    """Relance au-delà du seuil : seule une part passe dans le PIB ; un resserrement n'est pas touché."""
    from moteur.programme_simple import contrainte_capacite
    y = sq.pib(p, "prudent")
    seuil, k = sq._v(p, "capacite.seuil_pib", "prudent"), sq._v(p, "capacite.effet_au_dela", "prudent")
    brut = {2029: 0.06 * y[2029], 2030: -0.06 * y[2030], 2031: 0.01 * y[2031]}
    c = contrainte_capacite(p, "prudent", brut)
    lim = seuil / 100 * y[2029]
    assert c[2029] == pytest.approx(lim + k * (brut[2029] - lim))
    assert c[2030] == brut[2030] and c[2031] == brut[2031]


def test_economies_non_detaillees_deduites_du_programme(p):
    """Décision du 11/11/2026 : économies annoncées non détaillées déduites du programme, domaine par domaine
    (capacité des précédents × intensité que le programme donne au domaine, moins les économies déjà nommées dans ce
    domaine), jamais par le chiffre du candidat ; plus d'économies dans les scénarios favorables ; un domaine protégé
    par le candidat (santé chez Bertrand) n'en reçoit pas."""
    for nom in ("attal", "philippe", "retailleau", "lisnard", "bertrand"):
        g = noyau.charger(nom)
        g.mesures(p)
        d = {s: g.enveloppe_detail[(id(p), s)] for s in sq.SCENARIOS}
        assert d["crise"]["retenu"] <= d["prudent"]["retenu"] <= d["median"]["retenu"] <= d["optimiste"]["retenu"], nom
        assert d["optimiste"]["retenu"] <= g.v("enveloppe.annonce"), nom
        for s, x in d.items():
            for dom, v in x["domaines"].items():
                assert v["retenu"] == pytest.approx(max(0.0, v["capacite"] - v["deja_nommees"])), (nom, s, dom)
    b = noyau.charger("bertrand")
    assert not [m for m in b.mesures(p)["prudent"] if m.note == "enveloppe" and m.poste == "sante"]
    # sans enveloppe : rien (Zemmour : plan Knafo détaillé ligne à ligne)
    z = noyau.charger("zemmour")
    assert not [m for m in z.mesures(p)["prudent"] if m.note == "enveloppe"]
