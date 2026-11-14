"""Leviers : chaque levier d'économie améliore bien le solde (sens des effets)."""
from moteur import noyau
from moteur.parametres import Parametres

P = Parametres()


def _deficit(modifs, t=2037):
    return noyau.resultats(P.avec(modifs), ("prudent",))["prudent"][t]["deficit_sans_regle"]


def test_contribution_de_transition_est_une_recette():
    """Une part de l'épargne obligatoire versée à l'État réduit le déficit (elle n'était comptée que par la clause)."""
    assert _deficit({"epargne.contribution_transition": 0.1}) < _deficit({})


def test_socle_plus_bas_reduit_le_deficit_a_long_terme():
    """Déduction de l'investissement figée : sinon, un socle plus bas fait passer le déficit sous 3 %, ce qui déclenche
    la hausse conditionnée de la déduction, dont le coût l'emporte en 2073 (constaté le 05/11/2026 avec la recette
    carbone corrigée : 3,97 % sans le levier, 4,02 % avec, mais 3,00 % avec la déduction figée)."""
    fixe = {"is_investissement.hausse_part_admise": {"cible": 0.5, "debut": 2029, "fin": 2029, "duree": 1, "seuil_deficit": 0.03}}
    assert _deficit({**fixe, "retraites.socle_plein": 1100}, 2073) < _deficit(fixe, 2073)


def test_prime_de_taux_alourdit_quand_la_dette_monte():
    """Prime de taux liée à la dette : la crise (dette qui monte) paie plus d'intérêts avec la prime que sans."""
    avec = noyau.resultats(P, ("crise",))["crise"]
    sans = noyau.resultats(P.avec({"macro.prime_dette": 0.0}), ("crise",))["crise"]
    assert avec[2035]["charge_dette"] > sans[2035]["charge_dette"]  # dette au-dessus de son niveau de départ


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
    # mécanique du fonds seule : sans la rétroaction des taux sur le PIB (phase E), qui fait bouger la dette, donc la
    # part du capital placée à l'étranger
    q = P.avec({"macro.bouclage_prime_demande": False})
    avec = noyau.resultats(q, ("prudent",))["prudent"]
    sans = noyau.resultats(q.avec({"macro.usure_capital_fonds": 0.0}), ("prudent",))["prudent"]
    assert avec[2050]["pib"] > sans[2050]["pib"]
    # la recette ne bouge qu'à la marge (le capital lui-même dépend un peu de la dette, via la part placée à l'étranger)
    import pytest
    assert avec[2050]["dynamiques"]["fonds"]["solde"] == pytest.approx(sans[2050]["dynamiques"]["fonds"]["solde"], rel=0.05)


def test_baisse_du_rui_par_la_clause_respecte_le_plancher():
    """La baisse du RUI décidée par la clause ne descend pas sous le plancher, sur le RUI réel de l'année."""
    sc = noyau.resultats(P, ("prudent",))["prudent"]
    plancher = P.val("clause.plancher_rui")
    for t, c in sc.items():
        r = c["regle"]
        if r["leviers"]["Baisse du revenu universel"] > 0:
            # RUI réel de l'année (règle d'indexation, moteur/inflation.indice_reel)
            from moteur.inflation import indice_reel
            rui_t = P.val("rui.montant") * indice_reel(P)[t]
            assert r["details"]["Baisse du revenu universel"]["euros"] <= rui_t - plancher + 60, t


def test_regle_automatique_vise_3_pour_cent():
    """Règle permanente : quand ses instruments suffisent, le déficit publié du prudent ne dépasse pas 3 % ;
    sinon, ils sont au maximum (5 points d'épargne, RUI au plancher)."""
    sc = noyau.resultats(P, ("prudent",))["prudent"]
    for t, c in sc.items():
        r = c["regle"]
        if r["reste_a_couvrir"] <= 1e-6:
            # contribution en emprunt aux ménages (12/11/2026) : comptée par la règle, pas par le déficit publié
            contribution = r["leviers"]["Contribution d'épargne retraite"] / c["pib"] * 100
            assert c["deficit"] - contribution <= 3.0 + 1e-4, t
        else:
            assert r["details"]["Contribution d'épargne retraite"]["points"] >= P.val("clause.points_contribution_max") - 1e-6, t


def test_socle_supplementaire_quand_l_epargne_est_prise():
    from moteur.retraites_transition import socle_supplementaire
    assert socle_supplementaire(P, {}, 2060) == 0.0
    assert socle_supplementaire(P, {t: 0.5 for t in range(2030, 2040)}, 2060) > 0


def test_restitution_rend_l_epargne_prise():
    """Restitution : ce qui est rendu plus ce qui reste dû correspond à ce qui a été pris, avec le rendement."""
    d = noyau.resultats(P, ("prudent",))["prudent"]
    paye = sum(x["dynamiques"]["fonds"]["paiement"] for x in d.values())
    assert paye > 0 and d[2073]["dynamiques"]["fonds"]["creances"] > 0
    sans = noyau.resultats(P.avec({"clause.restitution/active": False}), ("prudent",))["prudent"]
    assert all(x["dynamiques"]["fonds"]["paiement"] == 0 for x in sans.values())


def test_contribution_des_anciens_retraites():
    """Contribution progressive (5 à 10 %) : taux moyen entre les deux bornes, recette qui s'éteint avec l'ancien système."""
    from moteur.ancien_systeme import contribution_solidarite, serie
    c, s = contribution_solidarite(P), serie(P)
    assert 0.05 < c[2030] / s[2030]["depenses_md"] < 0.10
    assert c[2030] > c[2060] > 0
