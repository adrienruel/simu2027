"""Phase A de la roadmap (cohérence comptable, 12/11/2026) : un euro de PIB, un emploi ou un point de taux produit le
même effet sur le solde, quel que soit le chemin. Tests rapides (pas de simulation complète des programmes)."""
import pytest

from moteur import noyau
from moteur import statu_quo as sq
from moteur.noyau import ANNEES
from moteur.parametres import Parametres
from moteur.programme_simple import ProgrammeSimple, production_non_marchande

P = Parametres()


def test_a1_dividende_du_programme_retrouve_le_statu_quo_recalcule():
    """Le dividende sur le profil du programme est exactement (Δ recettes − Δ dépenses) / Δ PIB du statu quo relevé
    de ce profil ; sur le profil type, il retrouve le dividende commun."""
    y = sq.pib(P, "prudent")
    profil = {t: y[t] * 0.01 * min(1.0, max(0.0, (t - 2028) / 10)) for t in ANNEES}
    d = sq.dividende_programme(P, "prudent", profil)
    commun = sq.dividende_productivite(P, "prudent")
    for t in (2033, 2037, 2050):
        assert d[t] == pytest.approx(commun[t], abs=1e-9)
    # le profil compte : un gain d'un coup en 2045 n'a pas le dividende du profil type
    tardif = {t: y[t] * 0.01 * (t >= 2045) for t in ANNEES}
    assert abs(sq.dividende_programme(P, "prudent", tardif)[2050] - d[2050]) > 0.005


def test_a2_un_emploi_vaut_la_meme_chose_partout():
    """Cellule OpenFisca au voisinage du SMIC (1,3 SMIC) ≈ valeur d'un emploi des autres canaux (20 000 €), à 5 %."""
    v = ProgrammeSimple.valeur_emploi_cellule(P, P.val("emploi.cout_emploi_cree_smic"))
    assert v == pytest.approx(20000, rel=0.05)
    assert ProgrammeSimple.valeur_emploi_cellule(P, 1.0) < v < ProgrammeSimple.valeur_emploi_cellule(P, "moyen")


def test_a2_trente_deux_heures_sans_double_compte():
    """32 heures : les embauches ne rapportent que l'allocation évitée et n'ajoutent pas de valeur ajoutée au PIB ;
    les emplois perdus coûtent la valeur de la cellule. Programme d'essai : 1 million de salariés concernés."""
    class Essai(ProgrammeSimple):
        nom = "roussel"  # seulement pour charger des paramètres ; le calcul n'en lit aucun
    prog = Essai()
    c = {"heures_actuelles": 35, "heures_cible": 32, "debut": 2029, "plein": 2029, "emplois_prive": 20_000_000,
         "part_marchande": 0.75, "emplois_concernes": 1_000_000,
         "gain_productivite": {s: 0.3 for s in sq.SCENARIOS}, "part_embauches": {s: 0.3 for s in sq.SCENARIOS}}
    idx = prog.indices(P, "prudent")
    canaux = {}
    mes = prog.trente_deux_heures(P, "prudent", idx, c, -0.8, "32 h", canaux)
    emb = canaux["**32 h : embauches de partage du travail"]
    perdus = canaux["*32 h : emplois perdus par le coût horaire"]
    alloc = P.val("emploi.allocation_chomeur_evitee")
    v = ProgrammeSimple.valeur_emploi_cellule(P, P.val("emploi.cout_emploi_cree_smic"))
    lignes = {m.nom.split(" : ", 1)[1]: m for m in mes}
    t = 2037
    ligne_emb = next(m for k, m in lignes.items() if k.startswith("allocations"))
    ligne_perdus = next(m for k, m in lignes.items() if k.startswith("emplois perdus"))
    assert ligne_emb.valeurs[t] == pytest.approx(emb[t] * alloc * idx["salaire"][t] / 1e9)
    assert ligne_perdus.valeurs[t] == pytest.approx(perdus[t] * v * idx["salaire"][t] / 1e9)
    assert not any("prélèvements des embauches" in m.nom for m in mes)


def test_a3_postes_publics_au_cout_des_facteurs():
    """Une dépense de postes constante entre au PIB à son coût une fois le multiplicateur éteint, ni plus ni moins
    (forme linéaire d'avant la phase E : macro.bouclage faux)."""
    q = P.avec({"macro.bouclage": False})
    d = sq._v(q, "macro.annees_effet_ajustement", "median")  # hausse : scénario miroir du prudent
    cout = {t: (10.0 if t >= 2030 else 0.0) for t in ANNEES}
    npm = production_non_marchande(q, "prudent", cout, ANNEES)
    assert npm[2029] == 0 and npm[2030] == 0
    assert npm[2030 + int(d)] == pytest.approx(10.0) and npm[2073] == pytest.approx(10.0)
    baisse = production_non_marchande(q, "prudent", {t: -v for t, v in cout.items()}, ANNEES)
    assert baisse[2073] == pytest.approx(-10.0)


def test_a3_postes_publics_forme_bouclee():
    """Phase E : au multiplicateur de 1 (prudent, miroir médian), effet de demande restant + production non marchande
    = coût des postes à long terme ; rien n'entre avant l'effet maximal."""
    from moteur import bouclage
    from moteur.programme_simple import multiplicateur
    cout = {t: (10.0 if t >= 2030 else 0.0) for t in ANNEES}
    npm = production_non_marchande(P, "prudent", cout, ANNEES)
    assert npm[2030] == 0 and npm[2031] == 0
    dem = bouclage.reponse(P, "prudent", cout, ANNEES)["dpib_avant_capacite"]
    assert dem[2073] + npm[2073] == pytest.approx(10.0, rel=0.02)


def test_a5_dette_qui_diverge_ne_gagne_rien():
    ref = {t: {"deficit": 20.0, "dette_pib": 100 + 10 * (t - 2029)} for t in ANNEES}
    sous_sq = {t: {"deficit": 10.0, "dette_pib": 100 + 5 * (t - 2029)} for t in ANNEES}
    assert noyau.baisse_ecart_taux(P, "optimiste", sous_sq, ref) is None


def test_a6_interets_de_l_emprunt_aux_menages():
    """Une dynamique qui doit 100 Md€ aux ménages au rendement r_f : le noyau compte (r_f − taux réel de marché) × 100."""
    class Dette:
        quasi_dette_dans_dette = True
        quasi_dette_debut = 100.0

        def taux_quasi_dette(self):
            return 0.05

        def debut(self, t, etat):
            return {}

        def fin(self, t, etat):
            pass
    a = noyau.trajectoire(P, "prudent")
    b = noyau.trajectoire(P, "prudent", [], None, [Dette()])
    reel = a[2029]["taux_apparent"] - a[2029]["inflation"] / 100
    assert b[2029]["interets_menages"] == pytest.approx((0.05 - reel) * 100.0)
    assert b[2029]["interets_reels"] - a[2029]["interets_reels"] == pytest.approx(b[2029]["interets_menages"])


def test_a4_elasticite_de_l_investissement_ordonnee():
    v = [P.val("macro.elasticite_invest", s) for s in ("crise", "prudent", "median", "optimiste")]
    assert v == sorted(v)


def test_a8_annonce_en_points_de_pib():
    from moteur.unites import annonce_en_points_pib
    m = {t: 1.0 for t in range(2028, 2033)}
    y = 3000.0
    assert annonce_en_points_pib(P, 150, 2026, "cumul", y, m) == pytest.approx(30 / y * 100)
    assert annonce_en_points_pib(P, 150, 2026, "niveau", y, m) == pytest.approx(150 / y * 100)
    assert annonce_en_points_pib(P, 101.9, 2027, "niveau", y) == pytest.approx(100 / y * 100)


def test_b2_variante_migratoire():
    """Phase B2 : une baisse du solde migratoire retire des personnes surtout jeunes, de l'emploi au taux relatif des
    immigrés, du PIB et des recettes ; les dépenses qui suivent la population baissent ; un programme sans
    déclaration n'a aucun effet ; l'ordre des scénarios est tenu (prudent : baisse la plus forte)."""
    from moteur import migrations as mg
    d = {"titres_en_moins": 100000, "debut": 2028, "montee": 3}
    v = {s: mg.variation(P, s, d) for s in sq.SCENARIOS}
    assert v["crise"] <= v["prudent"] <= v["median"] <= v["optimiste"] < 0
    r = mg.effets(P, "prudent", d)
    assert r["population"][2037] < 0 and r["emploi"][2037] < 0 and r["pib"][2037] < 0 and r["recettes"][2037] < 0
    assert sum(r["blocs"][2037].values()) < 0 and r["blocs"][2037]["sante"] < 0
    # l'emploi perdu est celui de personnes au taux relatif des immigrés : moins que la population de 18 ans ou plus
    pop = mg.ecart_population(P, "prudent", d)[2037]
    assert abs(r["emploi"][2037]) < abs(sum(pop[18:65]))
    assert all(x <= 0 for x in pop)  # une baisse des entrées ne crée personne (pas de retours de personnes âgées)
