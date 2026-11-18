"""Veille des programmes (roadmap 9.2) : sans réseau, avec des pages simulées."""
from moteur import noyau
from outils import veille_programmes as vp


def test_chaque_programme_publie_a_une_page():
    p = vp.pages()
    assert set(p) == set(noyau.programmes_disponibles()[1:])
    assert all(p.values())


def test_texte_html():
    t = vp.texte("https://x/", b"<html><script>x=1</script><p>Retraite \xc3\xa0 62 ans</p><li>SMIC &agrave; 1 600 &euro;</li></html>")
    assert t.splitlines() == ["Retraite à 62 ans", "SMIC à 1 600 €"]


def test_changement_detecte(tmp_path, monkeypatch):
    monkeypatch.setattr(vp, "DOSSIER", tmp_path)
    monkeypatch.setattr(vp, "pages", lambda: {"philippe": ["https://a/"]})
    v1 = {"https://a/": b"<p>Mesure A</p><p>Mesure B</p>"}
    vp.veiller(lire=v1.__getitem__, aujourd_hui="2026-11-18")
    v2 = {"https://a/": b"<p>Mesure A</p><p>Mesure C</p>"}
    r = vp.veiller(lire=v2.__getitem__, aujourd_hui="2026-11-25")
    assert "**changée** depuis le 2026-11-18" in r and "+ Mesure C" in r and "− Mesure B" in r
    r = vp.veiller(lire=v2.__getitem__, aujourd_hui="2026-11-26")
    assert "inchangée depuis le 2026-11-25" in r


def test_page_injoignable(tmp_path, monkeypatch):
    monkeypatch.setattr(vp, "DOSSIER", tmp_path)
    monkeypatch.setattr(vp, "pages", lambda: {"attal": ["https://b/"]})

    def lire(url):
        raise OSError("hors ligne")
    assert "injoignable (OSError)" in vp.veiller(lire=lire, aujourd_hui="2026-11-18")
