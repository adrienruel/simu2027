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
