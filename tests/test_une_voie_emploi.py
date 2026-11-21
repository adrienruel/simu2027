"""Chantier 2.1 (21/11/2026) : une seule voie d'emploi par mesure (docs/recoupements.md, section « Roadmap 2.1 »)."""

import numpy as np
import pytest

from moteur import offre
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres
from outils.openfisca_mesures import emplois_par_scenario


@pytest.fixture(scope="module")
def p():
    return Parametres()


def _mesure(nom, instrument, md, poste="recettes", incidence=""):
    return Mesure(nom, poste, {t: md for t in (2027, 2028, *ANNEES)}, instrument=instrument, incidence=incidence)


def _eta(p):
    return {sc: np.array(p.val("offre.travail_participation", sc)) * p.val("offre.participation_transferts", sc)
            for sc in sq.SCENARIOS}


def test_miroir_sur_le_sens_net_de_la_mesure(p):
    """Une mesure qui fait des gagnants et des perdants change de signe quand on l'inverse, dans chaque scénario
    (avant : miroir personne par personne, −4 800 et −5 200 emplois au prudent pour +10 % et −10 % de prime
    d'activité)."""
    pp = np.full(4, 1e6)
    t = np.ones(4, bool)
    bande = np.array([0, 0, 1, 2])
    rel = np.array([0.05, -0.03, 0.02, -0.01])
    val = np.full(4, 10_000.0)
    plus = emplois_par_scenario(pp, rel, t, bande, _eta(p), val)
    moins = emplois_par_scenario(pp, -rel, t, bande, _eta(p), val)
    for sc in sq.SCENARIOS:
        assert plus[sc]["emplois"] > 0 > moins[sc]["emplois"]
    # sens net positif : élasticité du scénario pour tous ; négatif : celle du miroir pour tous
    assert plus["prudent"]["emplois"] == pytest.approx(float((pp * rel * _eta(p)["prudent"][bande]).sum()))
    assert moins["prudent"]["emplois"] == pytest.approx(float((pp * -rel * _eta(p)["median"][bande]).sum()))


def test_cout_du_travail_au_smic_par_cellules(p):
    """Baisse au SMIC : 15 000 à 50 000 emplois par Md€ (Trésor-Éco n° 97, 2012 : 20 000 à 40 000 € bruts par
    emploi pour les allègements de 1993-1997), plus que l'élasticité agrégée de Mésange (baisse uniforme), et bien
    plus que la même somme entre 1,6 et 3,5 SMIC (rapport Bozio-Wasmer, 2024)."""
    for s in ("prudent", "median"):
        md = 0.01 * sq.pib(p, s)[2029]
        smic = offre.cout_travail_par_point(p, s, "smic")["emplois_demande"] / md
        milieu = offre.cout_travail_par_point(p, s, "milieu")["emplois_demande"] / md
        agrege = sq._v(p, "offre.elasticite_cout_travail", s) / 100 * sq.effectifs(p, s)[2029]["emploi"] / md
        assert 15_000 < smic < 50_000
        assert smic > 1.5 * agrege
        assert milieu < smic / 4
    with pytest.raises(ValueError):
        offre.cout_travail_par_point(p, "prudent", "inconnue")


def test_zone_declaree_passe_par_les_cellules_seulement(p):
    """Une mesure de coût du travail avec zone ne passe pas aussi par l'élasticité agrégée : un seul canal d'emploi."""
    r = offre.effets(p, "prudent", [_mesure("essai", "cout_travail", -3.0, incidence="smic")])
    assert set(r["emplois"]) == {"Offre : coût du travail (smic)"}
    assert r["emplois"]["Offre : coût du travail (smic)"][2040] > 30_000
    sans = offre.effets(p, "prudent", [_mesure("essai", "cout_travail", -3.0)])
    assert set(sans["emplois"]) == {"Offre : coût du travail"}


def test_transfert_code_dans_la_micro_ne_passe_pas_par_l_agrege(p):
    """Un transfert codé dans OpenFisca passe par la micro seulement, même s'il déclare l'instrument agrégé."""
    table = offre.micro_emploi()
    if not table or not p.val("offre.micro_emploi"):
        pytest.skip("table de la micro absente")
    ident = next(iter(table))
    r = offre.effets(p, "prudent", [_mesure(f"{ident} — essai", "transferts_actifs", 1.0, poste="pauvrete")])
    assert "transferts_actifs" not in r["detail"]
    assert set(r["emplois"]) <= {"Offre : gain à travailler (microsimulation)"}
