"""Propriétés communes à tous les programmes publiés (roadmap du comparateur, chantier 2.3, 16/11/2026).

Ces tests vérifient l'identité « mesures = écart de solde primaire » pour chaque programme du comparateur, avec l'ordre des scénarios et le sens
de l'effet d'une mesure."""
import pytest

from moteur import noyau
from moteur import statu_quo as sq
from moteur.noyau import ANNEES
from moteur.parametres import Parametres

PROGRAMMES = noyau.programmes_disponibles()[1:]


@pytest.fixture(scope="module")
def p():
    return Parametres()


@pytest.fixture(scope="module")
def base(p):
    return sq.simuler(p)


def _simuler(p, nom):
    prog = noyau.charger(nom)
    return prog, noyau.simuler(p, prog)


@pytest.mark.parametrize("nom", PROGRAMMES)
def test_mesures_expliquent_l_ecart_de_solde_primaire(nom, p, base):
    """Somme des mesures (budget et effets économiques), plus les recettes du PIB perdu ou gagné par les taux et
    l'érosion des pensions par l'inflation du programme (phase E), plus le fonds et la règle s'il y en a : exactement
    l'écart de solde primaire avec le statu quo."""
    prog, r = _simuler(p, nom)
    for s in ("crise", "prudent", "optimiste"):
        y, rec = sq.pib(p, s), sq.recettes(p, s)
        bilan = noyau.bilan_mesures(prog, p, s, annees=(2029, 2037, 2050))
        for t in (2029, 2037, 2050):
            x = r[s][t]
            effet = sum(m[t] for m in bilan) + x.get("pib_taux", 0.0) * rec[t] / y[t] + x.get("erosion_pensions", 0.0)
            # phase L (4.1) : dépenses sensibles au chômage sur les chômeurs du programme (blocs chômage et pauvreté)
            effet -= x.get("depenses_chomage_programme", 0.0)
            if "fonds" in x.get("dynamiques", {}):
                effet += x["dynamiques"]["fonds"]["solde"]
            if x.get("regle"):
                effet += x["regle"]["gain_comptes"]
            assert effet == pytest.approx(x["solde_primaire"] - base[s][t]["solde_primaire"], abs=1e-6), (s, t)


@pytest.mark.parametrize("nom", PROGRAMMES)
def test_ordre_des_scenarios_chaque_annee(nom, p):
    """Déficit : crise ≥ prudent ≥ médian ≥ optimiste, chaque année de 2029 à 2073."""
    _, r = _simuler(p, nom)
    for t in ANNEES:
        d = [r[s][t]["deficit"] for s in ("crise", "prudent", "median", "optimiste")]
        assert d[0] >= d[1] - 1e-9 and d[1] >= d[2] - 1e-9 and d[2] >= d[3] - 1e-9, (t, d)


@pytest.mark.parametrize("nom", PROGRAMMES)
def test_retirer_la_plus_grosse_mesure_deplace_le_solde_dans_le_bon_sens(nom, p, base):
    """La plus grosse mesure simple du programme (en valeur absolue, prudent, 2032), mise à zéro dans tous les
    scénarios : le solde primaire de 2032 bouge dans le sens opposé à son effet direct, d'au moins un tiers de cet effet
    (les effets économiques peuvent en reprendre une partie, pas l'inverser). Parmi les recettes et les dépenses en
    plus seulement : une économie nommée retirée serait en partie remplacée par les économies non détaillées
    (enveloppe_economies), ce qui est voulu."""
    prog, r = _simuler(p, nom)
    prefixe = f"{nom}_mesures."
    cand = []
    for m in prog.mesures(p)["prudent"]:
        if m.note and f"{prefixe}{m.note}" in prog.pt and m.nature not in ("effet_macro", "perimetre", "classement"):
            signe = 1 if m.poste == "recettes" else (0 if m.poste == "participations" else -1)
            if signe == 1 or (signe == -1 and m.valeurs.get(2032, 0.0) > 0):
                cand.append((abs(m.valeurs.get(2032, 0.0)), signe * m.valeurs.get(2032, 0.0), m.note))
    if not cand:
        pytest.skip("aucune mesure simple")
    _, direct, cle = max(cand)
    # la même mesure peut porter plusieurs lignes (dépense, prélèvements, IS) : effet direct de toutes ses lignes
    direct = sum((1 if m.poste == "recettes" else -1) * m.valeurs.get(2032, 0.0)
                 for m in prog.mesures(p)["prudent"] if m.note == cle and m.poste != "participations")
    par = prog.pt[f"{prefixe}{cle}"]
    val = dict(par.valeur)
    val["montant"] = {s: 0.0 for s in sq.SCENARIOS} if isinstance(val["montant"], dict) else 0.0
    prog2 = noyau.charger(nom)
    prog2.pt = prog.pt.avec({f"{prefixe}{cle}": val})
    r2 = noyau.simuler(p, prog2, scenarios=("prudent",))
    ecart = r2["prudent"][2032]["solde_primaire"] - r["prudent"][2032]["solde_primaire"]
    assert ecart * direct < 0 and abs(ecart) >= abs(direct) / 3, (cle, direct, ecart)
