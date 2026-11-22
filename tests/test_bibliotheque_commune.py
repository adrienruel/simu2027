"""Roadmap 7.1 (22/11/2026) : une même mesure, dans deux programmes, a le même coût (bibliothèque commune)."""
import pytest

from moteur import noyau
from moteur.parametres import Parametres

PAIRES = [
    (("melenchon", "LFI-RET-01"), ("roussel", "PCF-RET-01")),  # retraite à 60 ans, réforme de 2023 abrogée
    (("melenchon", "LFI-SAN-01"), ("roussel", "PCF-SAN-01")),  # soins remboursés à 100 %
    (("bertrand", "BER-FIS-01"), ("tondelier", "REC-11")),  # IR des premières tranches
]


def _effet(p, nom, ident, s="prudent", t=2037):
    ms = noyau.charger(nom).mesures(p)[s]
    lignes = [m for m in ms if m.nom.split(" — ", 1)[0] == ident and m.poste != "participations"]
    assert lignes, (nom, ident)
    return sum(m.valeurs.get(t, 0.0) * (1 if m.poste == "recettes" else -1) for m in lignes)


@pytest.mark.parametrize("a,b", PAIRES)
def test_meme_mesure_meme_cout(a, b):
    p = Parametres()
    ea, eb = _effet(p, *a), _effet(p, *b)
    assert ea != 0 and ea == pytest.approx(eb, rel=0.01)


def test_fiches_et_priorites():
    """Roadmap 7.2-7.3 : chaque fiche a son effet, ses fragilités et sa priorité."""
    from outils import priorites_mesures as pm
    lignes = [x for x in pm.fiches() if x["programme"] in ("bertrand", "lisnard")]
    assert lignes and all({"effet_prudent_pt_pib", "fragilites", "priorite", "citation"} <= set(x) for x in lignes)
    for x in lignes:
        assert x["priorite"] == pytest.approx(abs(x["effet_prudent_pt_pib"]) * (1 + x["fragilites"]), abs=1e-3)
