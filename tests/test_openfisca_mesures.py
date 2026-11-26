"""Phase F2 : mesures des programmes codées dans OpenFisca (outils/openfisca_mesures.py)."""
import pytest

pytest.importorskip("openfisca_france")

from outils import openfisca_mesures as om  # noqa: E402
from outils import population_synthetique as ps  # noqa: E402


def test_toutes_les_reformes_se_construisent():
    for mesures in om.specs().values():
        for spec in mesures.values():
            om.construire(spec["operations"])


@pytest.fixture(scope="module")
def base():
    return om.Base(ps.generer(n_menages=1500, caler_beneficiaires=False))


def test_signes(base):
    qf = base.reforme(om.specs()["lisnard"]["LIS-SOC-01"]["operations"])
    assert qf["budget"] < 0 and qf["composantes"]["impot_revenu"] < 0  # baisse d'impôt
    apl = base.reforme([{"variable": {"nom": "aide_logement", "facteur": 1.10}}])
    assert apl["composantes"]["aide_logement"] == pytest.approx(0.10 * base.etat0["comp"]["aide_logement"], rel=0.05)
    assert apl["budget"] < 0
    rien = base.reforme([])
    assert rien["budget"] == pytest.approx(0.0, abs=1e-6)


def test_emploi_signes(base):
    # moins d'aide sans activité : gain à travailler en hausse, emplois en plus
    r = base.reforme([{"formule": {"nom": "plafond_aides", "plafond_mensuel": 500, "sans_activite_seulement": True}}])
    assert r["budget"] > 0 and r["emploi"]["emplois"] > 0
    # garantie de niveau de vie : taux marginal de 100 % sous le seuil, emplois en moins
    g = base.reforme([{"formule": {"nom": "garantie_niveau_vie", "seuil_mensuel": 1337}}])
    assert g["budget"] < 0 and g["emploi"]["emplois"] < 0
