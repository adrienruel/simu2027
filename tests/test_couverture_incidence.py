"""Phase L (roadmap du comparateur, 4.2 et 4.3, 18/11/2026) : couverture du budget « ménages » par la micro et
incidence des mesures sur les entreprises."""
import csv

import pytest

from moteur import incidence_entreprises as ie
from moteur import noyau
from moteur.parametres import RACINE, Parametres
from outils import couverture_micro as cm


@pytest.fixture(scope="module")
def p():
    return Parametres()


def test_identifiants_groupes():
    specs = {"x": {"REC-20/21": {}, "BER-FIS-01": {}}}
    assert cm.identifiants_codes("x", specs) == {"REC-20", "REC-21", "BER-FIS-01"}


def test_seuil_des_deciles(p):
    c = cm.toutes(p)
    for nom, x in c.items():
        assert 0.0 <= x["part_codee"] <= 1.0
        assert x["deciles_publies"] == (x["part_codee"] >= p.val("publication.seuil_couverture_deciles")), nom
    # programme sans mesure codée : rien n'est couvert
    vide = cm.couverture(p, "lisnard", specs={})
    assert vide["part_codee"] == 0.0 and not vide["deciles_publies"]


def test_deciles_publies_selon_la_couverture():
    """Le comparateur ne publie les déciles que des programmes au-dessus du seuil."""
    with (RACINE / "sorties" / "comparaison_redistribution.csv").open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    publies = {l["programme"] for l in lignes if l["deciles_publies"] == "1" and l["programme"] != "Statu quo"}
    with (RACINE / "sorties" / "comparaison_redistribution_deciles.csv").open(encoding="utf-8") as f:
        avec_deciles = {l["programme"] for l in csv.DictReader(f)}
    assert avec_deciles == publies


@pytest.mark.parametrize("nom", ["melenchon", "lisnard"])
def test_incidence_repartit_tout_le_montant(p, nom):
    prog = noyau.charger(nom)
    m = ie.montant_entreprises(p, prog, "prudent")[2032]
    d = ie.par_decile(p, prog, "prudent", 2032)
    assert sum(x["total_md"] for x in d) == pytest.approx(m, rel=1e-9)
    x = p.val("entreprises.incidence_menages")
    assert sum(x_["salaires_md"] for x_ in d) == pytest.approx(x["salaires"] * m, rel=1e-9)


def test_incidence_signe(p):
    """Une hausse d'impôt sur les entreprises (Mélenchon) leur prend ; une baisse (Lisnard) leur laisse."""
    assert ie.montant_entreprises(p, noyau.charger("melenchon"), "prudent")[2032] < 0
    assert ie.montant_entreprises(p, noyau.charger("lisnard"), "prudent")[2032] > 0


def test_deciles_de_population():
    pop = ie._population()
    d = ie.deciles_population(pop)
    w = pop["poids"] * pop["personnes"]
    parts = [w[d == k].sum() / w.sum() for k in range(1, 11)]
    assert all(abs(x - 0.1) < 0.01 for x in parts)
