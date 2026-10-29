"""Leviers : chaque levier d'économie améliore bien le solde (sens des effets)."""
from moteur.parametres import Parametres
from moteur.simulation import simuler

P = Parametres()


def _deficit(modifs, t=2037):
    return simuler(P.avec(modifs))["prudent"][t]["deficit_avant_clause"]


def test_contribution_de_transition_est_une_recette():
    """Une part de l'épargne obligatoire versée à l'État réduit le déficit (elle n'était comptée que par la clause)."""
    assert _deficit({"epargne.contribution_transition": 0.1}) < _deficit({})


def test_socle_plus_bas_reduit_le_deficit_a_long_terme():
    assert _deficit({"retraites.socle_plein": 1100}, 2073) < _deficit({}, 2073)


def test_prime_de_taux_alourdit_quand_la_dette_monte():
    """Prime de taux liée à la dette : la crise (dette qui monte) paie plus d'intérêts avec la prime que sans."""
    from moteur.macro import calculer
    avec = calculer(P.en_crise())["prudent"]
    sans = calculer(P.en_crise().avec({"macro.prime_dette": 0.0}))["prudent"]
    assert avec.charge_dette[2050] > sans.charge_dette[2050]


def test_participation_des_inactifs():
    from moteur.emploi import participation_inactifs
    e = participation_inactifs(P)
    assert e["crise"] == 0 < e["prudent"] < e["median"] < e["optimiste"]


def test_externalites_du_fonds_nulles_dans_le_prudent():
    assert P.val("macro.externalites_capital_fonds", "prudent") == 0 == P.val("macro.externalites_capital_fonds", "crise")


def test_hausse_de_la_deduction_conditionnee_au_deficit():
    """La part déduite ne monte que les années qui suivent un déficit (prudent, avant clause, sans la hausse) sous 3 %."""
    from moteur.is_investissement import annees_sous_seuil, part_deduite
    assert all(part_deduite(P, t + 1) >= part_deduite(P, t) for t in range(2036, 2073))
    for t in range(2037, 2074):
        attendu = 0.5 + 0.5 * min(1.0, annees_sous_seuil(P, t) / 10)
        assert part_deduite(P, t) == attendu, t


def test_usure_du_fonds_dans_le_pib_pas_dans_les_impots():
    """Relecture du 29/10/2026 : l'usure du capital du fonds compte dans le PIB, mais n'est pas taxée."""
    from moteur.macro import calculer
    avec, sans = calculer(P)["prudent"], calculer(P.avec({"macro.usure_capital_fonds": 0.0}))["prudent"]
    assert avec.pib_effet[2050] > sans.pib_effet[2050]
    # la recette ne bouge qu'à la marge (le capital lui-même dépend un peu de la dette, via la part placée à l'étranger)
    import pytest
    assert avec.detail["canaux"][2050]["capital_du_fonds"] == pytest.approx(sans.detail["canaux"][2050]["capital_du_fonds"], rel=0.05)


def test_baisse_du_rui_par_la_clause_respecte_le_plancher():
    """La baisse du RUI décidée par la clause ne descend pas sous le plancher, sur le RUI réel de l'année."""
    from moteur.macro import calculer
    sc = calculer(P)["prudent"]
    plancher, infl, g = P.val("clause.plancher_rui"), P.val("calendrier.inflation"), P.val("macro.tendance")
    for t, c in sc.detail["clause"].items():
        if c["rui"] > 0:
            # RUI réel de l'année (sans le surcroît de productivité, qui ne fait que l'augmenter)
            rui_t = P.val("rui.montant") * ((1 + g) / (1 + infl)) ** (t - 2029)
            assert c["rui_euros"] <= rui_t - plancher + 60, t


def test_regle_automatique_vise_3_pour_cent():
    """Règle permanente : quand ses instruments suffisent, le déficit publié du prudent ne dépasse pas 3 % ;
    sinon, ils sont au maximum (5 points d'épargne, RUI au plancher)."""
    from moteur.macro import calculer
    sc = calculer(P)["prudent"]
    for t, c in sc.detail["clause"].items():
        if c["non_couvert"] <= 1e-6:
            assert -sc.maastricht[t] <= 0.03 + 1e-6, t
        else:
            assert c["points"] >= P.val("clause.points_contribution_max") - 1e-6, t


def test_socle_supplementaire_quand_l_epargne_est_prise():
    from moteur.retraites_transition import socle_supplementaire
    assert socle_supplementaire(P, {}, 2060) == 0.0
    assert socle_supplementaire(P, {t: 0.5 for t in range(2030, 2040)}, 2060) > 0


def test_restitution_rend_l_epargne_prise():
    """Restitution : ce qui est rendu plus ce qui reste dû correspond à ce qui a été pris, avec le rendement."""
    from moteur.macro import calculer
    d = calculer(P)["prudent"].detail
    paye = sum(x["paiement"] for x in d["restitution"].values())
    assert paye > 0 and d["restitution"][2073]["creances"] > 0
    sans = calculer(P.avec({"clause.restitution/active": False}))["prudent"].detail
    assert "restitution" not in sans or all(x["paiement"] == 0 for x in sans["restitution"].values())


def test_contribution_des_anciens_retraites():
    """Contribution progressive (5 à 10 %) : taux moyen entre les deux bornes, recette qui s'éteint avec l'ancien système."""
    from moteur.ancien_systeme import contribution_solidarite, serie
    c, s = contribution_solidarite(P), serie(P)
    assert 0.05 < c[2030] / s[2030]["depenses_md"] < 0.10
    assert c[2030] > c[2060] > 0
