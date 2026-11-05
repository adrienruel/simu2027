"""Séparation entre hypothèses communes et programme (4 novembre 2026)."""

import pytest

from moteur import parametres as mp
from moteur.parametres import ErreurParametre, Parametres


def test_programme_par_defaut_charge_les_trois_fichiers():
    p = Parametres()
    assert p.programme == "ecologie_de_droite"
    fichiers = {f.name if "commun" in str(f) else "programme" for f in p.origine.values()}
    assert fichiers == {"economie.yaml", "options.yaml", "statu_quo.yaml", "programme"}


def test_hypotheses_communes_sans_mesure_du_programme():
    """Les fichiers communs ne contiennent que des sources, des hypothèses et des options de modèle :
    aucune décision de programme (les trois décisions admises sont des choix entre sources)."""
    p = Parametres()
    decisions = sorted(x.cle for x in p if x.statut == "DECISION" and p.origine[x.cle].name == "economie.yaml")
    assert decisions == ["calendrier.inflation", "demographie.scenario_fecondite", "sante_trajectoire.pente_phase_1"]


def _programme_temporaire(tmp_path, monkeypatch, texte_en_plus: str) -> str:
    racine = tmp_path / "racine"
    (racine / "programmes" / "essai").mkdir(parents=True)
    source = mp.dossier_programme() / "parametres.yaml"
    (racine / "programmes" / "essai" / "parametres.yaml").write_text(
        source.read_text(encoding="utf-8") + texte_en_plus, encoding="utf-8")
    monkeypatch.setattr(mp, "RACINE", racine)
    return "essai"


def test_un_programme_ne_redefinit_pas_une_hypothese_commune(tmp_path, monkeypatch):
    nom = _programme_temporaire(tmp_path, monkeypatch, (
        "\nmacro_essai_bis:\n  x:\n    valeur: 1\n    unite: taux\n    statut: HYPOTHESE\n"
        "\nchomage:\n  taux_2026:\n    valeur: 0.05\n    unite: taux\n    statut: HYPOTHESE\n"))
    with pytest.raises(ErreurParametre, match="chomage.taux_2026 défini deux fois"):
        Parametres(programme=nom)


def test_programme_inconnu():
    with pytest.raises(FileNotFoundError):
        Parametres(programme="inexistant")


def test_copie_garde_le_programme():
    p = Parametres()
    assert p.avec({"clause.active": False}).programme == p.programme
    assert p.en_crise().programme == p.programme


def test_economies_saisies_sourcees_et_recoupees():
    """Décision du 05/11/2026 : une économie saisie sans deux sources indépendantes, ou citant le programme d'un
    candidat, compte pour zéro ; une économie retenue est multipliée par le taux de réalisation du scénario."""
    from moteur.mesures import motif_ecartee, effet
    from moteur.parametres import Parametres
    p = Parametres()
    m = {"mesure": "x", "retenue": "1", "plein_effet_md": "10", "premiere_annee": "2029", "annee_plein_effet": "2029",
         "indexation": "pib", "nature": "montant", "sources": ""}
    assert motif_ecartee(m, p) and effet(m, 2029, p, {}) == 0.0
    m["sources"] = "Cour des comptes, rapport X ; Programme du candidat Y"
    assert "déclarative" in motif_ecartee(m, p)
    m["sources"] = "Cour des comptes, rapport X (2024) ; IGF, revue de dépenses Y (2023)"
    assert motif_ecartee(m, p) is None
    assert effet(m, 2029, p, {}) == pytest.approx(10 * p.val("economies.taux_realisation", "prudent"))
    m["sources"] = "Loi de programmation des finances publiques ; Programme de stabilité 2026"
    assert motif_ecartee(m, p) is None
