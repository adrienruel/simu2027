"""Séparation entre hypothèses communes et programme (4 novembre 2026)."""

import pytest

from moteur import parametres as mp
from moteur.parametres import ErreurParametre, Parametres


def test_sans_programme_seulement_les_fichiers_communs():
    """Depuis le 16/11/2026, Parametres() ne charge que les hypothèses communes ; un programme s'ajoute par son nom."""
    p = Parametres()
    assert p.programme is None
    assert {f.name for f in p.origine.values()} == {"economie.yaml", "options.yaml", "statu_quo.yaml", "ecologie.yaml", "microsimulation.yaml"}
    q = Parametres(programme="philippe")
    fichiers = {f.name if "commun" in str(f) else "programme" for f in q.origine.values()}
    assert q.programme == "philippe" and fichiers == {f.name for f in p.origine.values()} | {"programme"}


def test_hypotheses_communes_sans_mesure_du_programme():
    """Les fichiers communs ne contiennent que des sources, des hypothèses et des options de modèle :
    aucune décision de programme (les décisions admises sont des choix entre sources ou de modèle ; l'élasticité des
    moyens de l'enseignement aux effectifs, sans source, est devenue une décision de modèle en C1, le 13/11/2026 ; la corrélation des tirages de l'incertitude publie ses
    deux bornes, décision du 14/11/2026 ; la lecture commune des capitalisations sans taux, règle identique pour
    tous les programmes, décision du 16/11/2026)."""
    p = Parametres()
    decisions = sorted(x.cle for x in p if x.statut == "DECISION" and p.origine[x.cle].name == "economie.yaml")
    # programme_commun (16/11/2026, phase J2) : lectures communes à tous, rangées là au lieu d'être recopiées dans
    # chaque programme (multiplicateur actif pour tous ; allègements qui suivent le SMIC selon la loi actuelle ;
    # calendrier des économies non détaillées)
    # emploi.depenses_chomage_programme (18/11/2026, phase L, roadmap 4.1) : règle de modèle commune
    # 18/11/2026, roadmap 5.4 à 5.6 : générosité des allocations, prime d'activité des emplois, retour de l'incidence
    # demographie.ecole_cohortes et taux_emploi_tendance (19/11/2026, phase P) : options de modèle communes
    # demographie.conge_part_soutien (20/11/2026, phase Q) : règle commune du canal des naissances (congés indemnisés)
    assert decisions == ["calendrier.inflation", "demographie.conge_part_soutien", "demographie.ecole_cohortes",
                         "demographie.scenario_fecondite",
                         "demographie.taux_emploi_tendance", "emploi.depenses_chomage_programme",
                         "emploi.generosite_programme", "emploi.prelevements_programme", "emploi.prime_activite_emplois", "entreprises.incidence_retour_budget",
                         "incertitude.correlation",
                         "lectures_communes.capitalisation", "ministeres.elasticite_eleves_etudiants", "offre.micro_emploi",
                         "programme_commun.enveloppe_debut", "programme_commun.enveloppe_plein",
                         "programme_commun.macro_multiplicateur_actif", "programme_commun.smic_allegements_suivent_smic", "sante_trajectoire.pente_phase_1"]


def _programme_temporaire(tmp_path, monkeypatch, texte_en_plus: str) -> str:
    racine = tmp_path / "racine"
    (racine / "programmes" / "essai").mkdir(parents=True)
    source = mp.dossier_programme("philippe") / "parametres.yaml"
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
    p = Parametres(programme="philippe")
    assert p.avec({"macro.prime_dette": 0}).programme == p.programme == "philippe"
    assert p.en_crise().programme == p.programme


