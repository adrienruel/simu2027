"""Roadmap 4.3 (22/11/2026) : bénéfices déplacés par les groupes quand le taux de l'IS change (règle commune)."""
import pytest

from moteur import noyau
from moteur.parametres import Parametres


def _lignes(p, nom, s, ident):
    ms = noyau.charger(nom).mesures(p)[s]
    base = next(m for m in ms if m.nom.startswith(ident + " — ") and "déplacés" not in m.nom)
    dep = next(m for m in ms if m.nom.startswith(ident + " — impôt sur les sociétés : bénéfices déplacés"))
    return base, dep


@pytest.mark.parametrize("s,sc", [("prudent", "median"), ("crise", "optimiste"), ("optimiste", "crise")])
def test_baisse_de_l_is_en_partie_regagnee(s, sc):
    """IS à 20 % (Lisnard) : une partie de la baisse revient (bénéfices rapatriés) ; une baisse prend le miroir."""
    p = Parametres()
    base, dep = _lignes(p, "lisnard", s, "LIS-FIS-03")
    r = (p.val("macro.semi_elasticite_transfert", sc) * p.val("macro.taux_reference_is", s)
         * p.val("macro.part_grandes_entreprises", s))
    assert 0.1 < r < 0.3
    for t in (2030, 2037):
        assert dep.valeurs[t] == pytest.approx(-r * base.valeurs[t])
        assert dep.valeurs[t] > 0 > base.valeurs[t]


def test_seules_les_mesures_de_taux():
    """Sans drapeau taux_is (impôts de production, crédits d'impôt), pas de bénéfices déplacés."""
    p = Parametres()
    for nom in ("philippe", "attal", "le_pen"):
        assert not any("bénéfices déplacés" in m.nom for m in noyau.charger(nom).mesures(p)["prudent"])
