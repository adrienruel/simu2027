"""La réforme codée dans OpenFisca et le moteur donnent le même nouveau système (deux écritures des mêmes règles)."""
import csv
from pathlib import Path

import pytest

from moteur.menages_types import definitions, nouveau
from moteur.parametres import Parametres

P = Parametres()
TABLE = Path(__file__).resolve().parent.parent / "parametres" / "donnees" / "openfisca_menages_types_2026.csv"


def _menage_avec_couts_openfisca(m, ligne):
    couts = [float(x) for x in ligne["couts"].split(";")]
    adultes = [a if isinstance(a, str) and a.startswith("retraite") else c for a, c in zip(m["adultes"], couts)]
    return {**m, "adultes": adultes}


@pytest.mark.parametrize("champ, cle", [("nouveau_revenu_disponible", "revenu_disponible"),
                                        ("nouveau_impot_unique", "impot_unique"),
                                        ("nouveau_epargne", "epargne_obligatoire"),
                                        ("nouveau_impot_local", "impot_local")])
def test_reforme_openfisca_egale_moteur(champ, cle):
    lignes = {l["id"]: l for l in csv.DictReader(TABLE.open(encoding="utf-8"))}
    for m in definitions():
        n = nouveau(_menage_avec_couts_openfisca(m, lignes[m["id"]]), P)
        assert float(lignes[m["id"]][champ]) == pytest.approx(n[cle], abs=0.05), m["id"]


def test_reforme_recalculee_par_openfisca():
    """Si OpenFisca est installé, la table enregistrée est bien celle que la réforme produit aujourd'hui."""
    pytest.importorskip("openfisca_france")
    from outils.openfisca_menages import calculer
    frais = {l["id"]: l for l in calculer()}
    lignes = {l["id"]: l for l in csv.DictReader(TABLE.open(encoding="utf-8"))}
    for i, l in lignes.items():
        assert frais[i]["revenu_disponible"] == pytest.approx(float(l["revenu_disponible"]), abs=0.05), i
        assert frais[i]["nouveau_revenu_disponible"] == pytest.approx(float(l["nouveau_revenu_disponible"]), abs=0.05), i


def test_troisieme_enfant_openfisca_egale_moteur():
    """Familles de 3 enfants (part majorée dès le 3e) : la réforme OpenFisca et le moteur concordent."""
    pytest.importorskip("openfisca_france")
    from outils.openfisca_menages import calculer
    from outils.valeur_enfant import menages
    ms = [m for m in menages() if len(m["enfants"]) == 3]
    for l, m in zip(calculer(2026, ms), ms):
        n = nouveau(_menage_avec_couts_openfisca(m, l), P)
        assert l["nouveau_revenu_disponible"] == pytest.approx(n["revenu_disponible"], abs=0.05), m["id"]
