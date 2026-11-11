"""Programmes Bertrand, Zemmour et Arthaud, et la bibliothèque de mesures commune (6 novembre 2026)."""

import pytest
import yaml

from moteur import bibliotheque as bib
from moteur import noyau
from moteur import statu_quo as sq
from moteur.noyau import ANNEES
from moteur.parametres import RACINE, Parametres

PETITS = ("bertrand", "zemmour", "arthaud")


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.mark.parametrize("nom", PETITS)
def test_programme_disponible_et_chiffre(nom, p):
    assert nom in noyau.programmes_disponibles()
    prog = noyau.charger(nom)
    res = noyau.simuler(p, prog)
    assert set(res) == set(sq.SCENARIOS)
    for s in sq.SCENARIOS:
        assert all(abs(res[s][t]["deficit"]) < 200 for t in (2029, 2037))


@pytest.mark.parametrize("nom", PETITS)
def test_chaque_mesure_renvoie_a_la_fiche(nom):
    """Chaque ligne chiffrée renvoie à une mesure de la fiche (mesures.yaml)."""
    fiche = yaml.safe_load((RACINE / "programmes" / nom / "mesures.yaml").read_text(encoding="utf-8"))
    ids = {m["id"] for m in fiche["mesures"]}
    prog = noyau.charger(nom)
    for cle, par in prog.pt._p.items():
        if cle.startswith(f"{nom}_mesures."):
            prefixe = par.valeur["id"].rsplit("-", 1)[0]
            for i in par.valeur["id"].split("/"):
                i = i if i.count("-") >= 2 else f"{prefixe}-{i}"
                assert i in ids, f"{cle} : {i} absent de la fiche"


def test_aucune_economie_annoncee_reprise():
    """Règle des autres candidats : les montants annoncés par Reconquête ne sont pas saisis."""
    z = noyau.charger("zemmour")
    annonces = {"aide_developpement": 14, "energies_renouvelables": 8, "subventions": 1.3, "politique_ville": 8,
                "audiovisuel": 4, "anah": 6, "ademe": 3.4, "france_travail": 4, "ars": 1, "rsa_trois_ans": 4.8,
                "budget_ue": 14, "etudiants_etrangers": 4, "visas": 0.7, "hebergement_urgence": 0.7}
    for cle, annonce in annonces.items():
        m = z.pt.val(f"zemmour_mesures.{cle}")["montant"]
        # prudent sous l'annonce (l'optimiste peut l'approcher quand l'annonce est basse)
        assert abs(m["prudent"]) < annonce, cle
        assert max(abs(v) for v in m.values()) <= max(annonce, abs(m["optimiste"]))
    # non-remplacement : 800 000 postes annoncés, 200 000 réalisés en prudent (règle commune, relecture neutre)
    postes = -sum(z.pt.val(f"zemmour_mesures.non_remplacement_{v}")["montant"]["prudent"] for v in ("etat", "collectivites", "hopitaux"))
    assert postes * 1e9 / 55000 == pytest.approx(200000, rel=0.01)
    pref = sum(-z.pt.val(f"zemmour_mesures.preference_{b}")["montant"]["optimiste"] for b in ("famille", "logement", "pauvrete"))
    assert pref < 15


def test_economies_de_bertrand_bien_en_dessous_de_l_annonce(p):
    """Les lignes identifiées de Bertrand n'approchent pas les 100 Md€ annoncés."""
    b = noyau.charger("bertrand")
    economies = sum(x[2037] for x in noyau.bilan_mesures(b, p, "optimiste", annees=(2037,)) if x[2037] > 0)
    assert economies < 40


def test_smic_de_la_bibliotheque_retrouve_tondelier(p):
    """Mêmes paramètres, même résultat que le calcul propre au programme Tondelier."""
    t = noyau.charger("tondelier")
    ref = t.smic(p)
    infl = p.val("inflation.base")["2027"]
    x = bib.smic(p, 2000 / (1 + infl), 1.4, 0.5, 9000)["prive"]
    for k in ("prelevements", "aides", "tva", "is", "hausse_cout"):
        assert x[k] == pytest.approx(ref[k], rel=1e-9)
    assert x["emplois_ponderes"] == pytest.approx(ref["emplois_ponderes"], rel=1e-9)


def test_smic_allegements_suivent_le_smic(p):
    """Loi actuelle (allègements en multiples du SMIC) : le coût au SMIC monte comme le brut, et les salaires non
    relevés gagnent des allègements (coût en moins) ; le coût total monte moins que dans la lecture nominale."""
    cible = bib.brut_de_net_mensuel(2200 / 1.019)
    loi = bib.smic(p, cible, 1.4, 0.5, 9000, allegements_suivent_smic=True)["prive"]
    nom = bib.smic(p, cible, 1.4, 0.5, 9000)["prive"]
    assert loi["hausse_cout"] < nom["hausse_cout"]
    assert any(r < 1 for _, r in loi["chocs"])  # salaires au-dessus de la diffusion : coût en baisse


def test_emplois_a_elasticite_constante_bornes(p):
    a = noyau.charger("arthaud")
    pr = a.smic(p)["prive"]
    for el in (-0.4, -0.8, -1.0):
        perdus = sum(n * (1 - r ** el) for n, r in pr["chocs"])
        touches = sum(n for n, r in pr["chocs"] if r > 1)
        assert 0 < perdus < touches
        # plus faible que la formule linéaire pour une forte hausse
        assert perdus < -el * pr["emplois_ponderes"]


def test_report_de_l_age_legal(p):
    eco = bib.report_age_legal(p, "prudent", 65, 1966, 0.25)
    # la génération 1966 (63 ans 3 mois au statu quo, suspension de la LFSS 2026) part à 63 ans et demi : effet faible
    # dès 2029
    assert 0 <= eco[2029] < 1 and eco[2030] > eco[2029]
    # un an de plus : entre 0,2 et 0,45 point de PIB d'économie de pensions à terme (Cour des comptes, 2025 :
    # 65 ans ≈ 9,2 Md€ de 2026 ; relecture neutre du 11/11/2026)
    y = sq.pib(p, "prudent")
    assert 0.2 < eco[2040] / y[2040] * 100 < 0.45
    # plus de report, plus d'économie
    assert bib.report_age_legal(p, "prudent", 66, 1966, 0.25)[2045] > eco[2045]


def test_csg_activite(p):
    c = bib.csg_activite(p)
    assert 90 < c["csg_prive"] + c["csg_public"] < 115  # CSG sur les revenus d'activité salariés ≈ 100 Md€
    assert 0 < c["ir_prive"] < c["csg_prive"] * 0.3


def test_defense_sans_lpm(p):
    d = bib.defense_sans_lpm(p, "prudent")
    assert 5 < d[2029] < 20
    assert all(v > 0 for v in d.values())


def test_suppression_de_postes_eviction_miroir(p):
    """Supprimer des postes publics : la reprise par le privé est prise au scénario miroir (prudent → médian)."""
    b = noyau.charger("bertrand")
    ctx = b.contexte(p)["prudent"]
    t = 2035
    c = ctx["emplois_canaux"][t]
    postes = c["Postes publics créés ou supprimés"]
    assert postes < 0
    ev = sq._v(p, "emploi_public.eviction_privee", "median")
    assert c["Éviction d'emplois privés par les postes publics"] == pytest.approx(-ev * postes)


@pytest.mark.parametrize("nom", PETITS)
def test_mesures_de_2027_2028_dans_la_dette_de_depart(nom, p):
    prog = noyau.charger(nom)
    ctx = prog.contexte(p)["prudent"]
    avant = prog._calcul(p)["details"]["prudent"]["avant_2029"]
    assert ctx["dette_depart"] == pytest.approx(sq.dette_fin_2028(p) + avant)
    assert all(t in ctx["chomage"] for t in ANNEES)
