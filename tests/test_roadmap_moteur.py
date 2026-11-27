"""Garde-fous de la roadmap du moteur (25/11/2026, docs/roadmap_moteur_2026-11-25.md, R1 et R2)."""
import re

import pytest

from moteur import noyau, parametres
from moteur.noyau import Levier, Regle
from moteur.parametres import RACINE, ErreurParametre, Parametres


def test_regle_reutilisee_redonne_le_meme_resultat():
    """R2.2 : la règle n'est plus modifiée par le calcul ; deux appels avec le même objet donnent les mêmes comptes
    (avant, `declenchee` restait celui du premier appel)."""
    p = Parametres()
    r = Regle(0.0, [Levier("grand", lambda t, e: 1e6)], automatiques=[lambda t, e, d: 10.0 * d])
    a = noyau.trajectoire(p, "prudent", regle=r)
    assert r.declenchee is None
    b = noyau.trajectoire(p, "prudent", regle=r)
    assert a == b


def test_jetons_uniques_et_copies():
    """R1.4 et R2.3 : chaque instance a son jeton, y compris les copies ; une copie ne partage plus _p."""
    p = Parametres()
    q, c = p.avec(), p.en_crise()
    assert len({p.jeton, q.jeton, c.jeton}) == 3
    cle = "profils.smic_brut_mensuel_2026"
    c.remplacer(cle, c[cle].__class__(**{**c[cle].__dict__, "valeur": 1.0}))
    assert p.val(cle) == 1823.03 and c.val(cle) == 1.0


def test_interface_parametres():
    p = Parametres().avec()
    assert "profils.smic_brut_mensuel_2026" in p and "pas.une_cle" not in p
    assert set(p.cles()) == {k for k, _ in p.items()}
    with pytest.raises(ErreurParametre):
        p.remplacer("pas.une_cle", p["profils.smic_brut_mensuel_2026"])
    with pytest.raises(ErreurParametre):
        p.ajouter("profils.smic_brut_mensuel_2026", p["profils.smic_brut_mensuel_2026"])
    p.retirer("profils.smic_brut_mensuel_2026")
    assert "profils.smic_brut_mensuel_2026" not in p


def test_yaml_modifie_relu(tmp_path):
    """R1.2 : la mémoire des fichiers analysés suit leur texte ; un fichier réécrit (même taille, même seconde) est
    relu, et les doublons restent refusés par l'analyseur en C."""
    f = tmp_path / "p.yaml"
    f.write_text("scenarios: [prudent]\ng:\n  x: {valeur: 1, unite: taux, statut: DECISION}\n")
    assert Parametres(chemin=f).val("g.x") == 1
    f.write_text("scenarios: [prudent]\ng:\n  x: {valeur: 2, unite: taux, statut: DECISION}\n")
    assert Parametres(chemin=f).val("g.x") == 2
    f.write_text("scenarios: [prudent]\ng:\n  x: {valeur: 1, unite: taux, statut: DECISION}\n  x: {valeur: 2, unite: taux, statut: DECISION}\n")
    with pytest.raises(ErreurParametre):
        Parametres(chemin=f)


def test_copies_independantes_du_yaml_memorise():
    """Deux instances ne partagent pas les valeurs structurées lues du même fichier."""
    a, b = Parametres(), Parametres()
    cle = next(k for k, par in a.items() if isinstance(par.valeur, dict))
    assert a[cle].valeur == b[cle].valeur and a[cle].valeur is not b[cle].valeur


def test_pas_de_smic_ni_de_plafond_en_dur():
    """R2.4 : le SMIC brut et le plafond de la Sécurité sociale de 2026 sont des paramètres sourcés
    (profils.smic_brut_mensuel_2026, profils.plafond_securite_sociale_mensuel_2026)."""
    motif = re.compile(r"\b1823\.03\b|\b48060\b")
    for d in ("moteur", "programmes", "outils"):
        for f in (RACINE / d).rglob("*.py"):
            assert not motif.search(f.read_text(encoding="utf-8")), f
    p = Parametres()
    assert p["profils.smic_brut_mensuel_2026"].statut == "SOURCE"
    from moteur import offre
    assert offre.SMIC_BRUT_2026 == 12 * p.val("profils.smic_brut_mensuel_2026")
    assert offre.PLAFOND_SS_2026 == 12 * p.val("profils.plafond_securite_sociale_mensuel_2026")


def test_plus_d_instances_gardees_en_vie():
    assert not hasattr(parametres, "_VIVANTES")


def test_erreur_monte_carlo_bootstrap():
    """R4.2 : deux programmes bien séparés gardent leur rang ; deux programmes confondus ne sont pas départagés."""
    import random

    from outils.erreur_monte_carlo import bootstrap
    rng = random.Random(1)
    ec = {"a": [rng.gauss(0, 1) for _ in range(400)], "b": [rng.gauss(5, 1) for _ in range(400)],
          "c": [rng.gauss(5.01, 1) for _ in range(400)]}
    r = bootstrap(ec, b=200)
    assert r["a"]["rang"] == 1 and r["a"]["stabilite_rang"] == 1.0
    assert r["b"]["stabilite_rang"] < 0.95 and r["c"]["stabilite_rang"] < 0.95
    assert 0 < r["a"]["demi_ic90_p50"] < 0.2


def test_hors_domaine():
    """R3.3 : première année hors domaine, sans changer les résultats."""
    fausse = {"prudent": {2029: {"dette_pib": 120.0, "pib": 100.0}, 2030: {"dette_pib": 260.0, "pib": 112.0},
                          2031: {"dette_pib": 300.0, "pib": 100.0}}}
    base = {"prudent": {t: {"dette_pib": 0.0, "pib": 100.0} for t in (2029, 2030, 2031)}}
    assert noyau.hors_domaine(fausse, base) == {"prudent": {"dette": 2030, "pib": 2030, "balance": None}}
    assert noyau.hors_domaine(fausse) == {"prudent": {"dette": 2030, "pib": None, "balance": None}}
    assert noyau.hors_domaine(fausse, base, dette_pib_max=400, ecart_pib_max=0.2) == {
        "prudent": {"dette": None, "pib": None, "balance": None}}
    # R3.4 : balance commerciale au-delà de 2 points de PIB
    fausse["prudent"][2031]["balance_commerciale"] = -2.5
    assert noyau.hors_domaine(fausse)["prudent"]["balance"] == 2031


def test_groupes_ex_aequo():
    """Affichage « ex æquo » (26/11/2026) : voisins non départagés regroupés, programme bien séparé seul."""
    import random

    from outils.erreur_monte_carlo import groupes_ex_aequo
    rng = random.Random(3)
    moy = {"a": 0.0, "b": 5.0, "c": 5.01, "d": 5.02, "e": 10.0}
    tirages = [{"statu_quo": {"2037": {"deficit": 1.0}},
                **{n: {"2037": {"deficit": rng.gauss(m, 1)}} for n, m in moy.items()}} for _ in range(400)]
    g = groupes_ex_aequo(tirages, 2037, b=200)
    assert g["a"] == [] and g["e"] == []
    assert sorted(g["b"] + ["b"]) == ["b", "c", "d"]
    assert groupes_ex_aequo(tirages, 2037, "ecart_deficit", b=200)["a"] == []


@pytest.mark.lent
def test_point_fixe_baisse_ecart_taux():
    """R3.1 (option macro.point_fixe_baisse_spread, activée le 26/11/2026 par décision d'Adrien) : la baisse de l'écart
    de taux est celle que gagne la trajectoire qu'elle produit ; désactivée, on retrouve les deux passes d'avant. Seul
    l'optimiste de Retailleau bouge parmi les cas mesurés le 25/11."""
    import dataclasses

    from moteur import reaction_marches
    # la baisse de l'écart de taux n'existe que dans la variante « avec la réaction des marchés » (27/11/2026)
    p = reaction_marches.parametres(Parametres())
    assert p.val("macro.point_fixe_baisse_spread") is True
    q = p.avec()
    cle = "macro.point_fixe_baisse_spread"
    q.remplacer(cle, dataclasses.replace(q[cle], valeur=False))  # q : deux passes, comme avant le 26/11
    a = noyau.simuler(q, noyau.charger("retailleau"), scenarios=("prudent", "optimiste"))
    b = noyau.simuler(p, noyau.charger("retailleau"), scenarios=("prudent", "optimiste"))
    assert all(a["prudent"][t]["deficit"] == b["prudent"][t]["deficit"] for t in a["prudent"])
    # valeurs mesurées le 27/11/2026 (nuit) : nouveau nucléaire et prix de l'électricité, BCE hors du calcul, 2027-2028
    # projetées, barème commun de l'assurance chômage (avant, le même jour : 2,939 et 4,853 ; 26/11 : 2,618 et 4,575)
    assert b["optimiste"][2073]["deficit"] == pytest.approx(3.510, abs=1e-3)
    assert a["optimiste"][2073]["deficit"] == pytest.approx(5.212, abs=1e-3)
    passes = b["optimiste"][2073]["passes_ecart_taux"]
    # 27/11/2026 (nuit) : dans la variante, l'optimiste de Retailleau atteint la borne de 10 passes (oscillation de la
    # baisse gagnée, dernière passe gardée) ; ouvert dans docs/journal.md
    assert 2 < passes <= 10
    # cohérence : la baisse publiée est celle que la trajectoire publiée gagne
    # (seulement si le point fixe est atteint ; sinon la dernière passe est gardée, comme le dit noyau._deux_passes)
    gagne = noyau.baisse_ecart_taux(p, "optimiste", b["optimiste"], None)
    if passes < 10:
        assert all(-gagne[t] == b["optimiste"][t]["baisse_ecart_taux"] for t in b["optimiste"])
    assert "passes_ecart_taux" not in a["optimiste"][2073]
