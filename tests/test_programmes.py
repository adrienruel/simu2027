"""Séparation entre hypothèses communes et programme (4 novembre 2026)."""

import pytest

from moteur import parametres as mp
from moteur.parametres import ErreurParametre, Parametres


def test_programme_par_defaut_charge_les_trois_fichiers():
    p = Parametres()
    assert p.programme == "ecologie_de_droite"
    fichiers = {f.name if "commun" in str(f) else "programme" for f in p.origine.values()}
    assert fichiers == {"economie.yaml", "options.yaml", "programme"}


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
