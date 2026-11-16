"""Sorties tracées (roadmap du comparateur, chantier 1.2, 16/11/2026) : chaque fichier de sorties/ figure au
manifeste (sorties/MANIFESTE.json), n'a pas été modifié depuis sa production et, s'il a été produit depuis la mise en
place du manifeste, l'a été avec les paramètres actuels. Les sorties antérieures au manifeste sont listées, sans
faire échouer le test : elles portent une note qui dit d'où elles viennent."""
from outils import trace


def test_toute_sortie_au_manifeste_et_inchangee():
    r = trace.verifier()
    assert not r["absents"], f"sorties absentes du manifeste : {r['absents']}"
    assert not r["modifies"], f"sorties modifiées hors des scripts : {r['modifies']}"
    assert not r["disparus"], f"entrées du manifeste sans fichier : {r['disparus']}"


def test_sorties_produites_avec_les_parametres_actuels():
    r = trace.verifier()
    assert not r["parametres_changes"], (
        "sorties produites avec d'autres paramètres (à régénérer) : " + ", ".join(r["parametres_changes"]))


def test_sorties_anterieures_documentees():
    m = trace.lire()["fichiers"]
    for nom in trace.verifier()["anterieurs"]:
        assert m[nom].get("note", "").startswith("Antérieur au manifeste"), nom
