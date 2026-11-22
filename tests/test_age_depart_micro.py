"""Roadmap 3.3 (21/11/2026) : âge de départ dans la population de la microsimulation (sans OpenFisca)."""
import pytest

from outils import openfisca_population as op
from outils.openfisca_mesures import age_depart


@pytest.fixture(scope="module")
def pop():
    return op.lire()


def _bilan(lg):
    ret = sum(l["poids"] for l in lg if l["statut"] == "retraite")
    pen = sum(l["poids"] * l["pension_brute"] for l in lg) / 1e9
    return ret, pen


def test_age_abaisse_ou_releve(pop):
    """62 ans : ≈ +0,7 million de retraités et ≈ +18 Md€ de pensions brutes (moteur : 23,5 Md€ de pensions en 2032,
    même ordre) ; 60 ans : environ le double ; 65 ans : retraités et pensions en moins ; mêmes ménages, mêmes poids."""
    r0, p0 = _bilan(pop)
    out = {}
    for c in (60, 62, 65):
        lg = [dict(l) for l in pop]
        age_depart(lg, {"age_actuel": 64, "age_cible": c})
        assert [l["poids"] for l in lg] == [l["poids"] for l in pop]
        out[c] = _bilan(lg)
    assert 0.4e6 < out[62][0] - r0 < 1.0e6
    assert 12 < out[62][1] - p0 < 30
    assert out[60][1] - p0 > 1.8 * (out[62][1] - p0)
    assert out[65][0] < r0 and out[65][1] < p0
    lg = [dict(l) for l in pop]
    age_depart(lg, {"age_actuel": 64, "age_cible": 64})
    assert lg == pop


def test_minimum_de_pension_des_carrieres_completes(pop):
    """Pensions entre le plancher de carrière complète et 1 870 € brut portées à 1 870 € : ≈ 4 millions de retraités,
    ≈ 20 Md€ bruts (moteur, LFI-RET-03 : 22 Md€ au prudent) ; sous le plancher, inchangées."""
    from outils.openfisca_mesures import Base
    lg = Base.population(type("B", (), {"lignes": pop})(), [{"population": {"pension_minimum": {"mensuel_brut": 1870}}}])
    gain = sum(l2["poids"] * (l2["pension_brute"] - l1["pension_brute"]) for l1, l2 in zip(pop, lg)) / 1e9
    n = sum(l1["poids"] for l1, l2 in zip(pop, lg) if l2["pension_brute"] > l1["pension_brute"])
    assert 3e6 < n < 5.5e6
    assert 14 < gain < 26
    assert all(l2["pension_brute"] == l1["pension_brute"] for l1, l2 in zip(pop, lg) if l1["pension_brute"] < 12 * 1000)


def test_assurance_chomage_au_montant_du_moteur(pop):
    """Roadmap 3.4 : les allocations des chômeurs concernés baissent (ou montent) du montant donné, au prorata."""
    from outils.openfisca_mesures import Base
    b = type("B", (), {"lignes": pop})()
    m0 = sum(l["poids"] * l["chomage_brut"] for l in pop) / 1e9
    lg = Base.population(b, [{"population": {"assurance_chomage": {"montant_md": 3.0, "age_max": 50}}}])
    assert sum(l["poids"] * l["chomage_brut"] for l in lg) / 1e9 == pytest.approx(m0 - 3.0, abs=0.01)
    assert all(l2["chomage_brut"] == l1["chomage_brut"] for l1, l2 in zip(pop, lg) if l1["age"] >= 50)
    lg = Base.population(b, [{"population": {"assurance_chomage": {"montant_md": -6.0}}}])
    assert sum(l["poids"] * l["chomage_brut"] for l in lg) / 1e9 == pytest.approx(m0 + 6.0, abs=0.01)


def test_depenses_budget_de_famille():
    """Roadmap 3.1 : dépenses par décile de l'enquête Budget de famille 2017 (TF106) lues ; carburants et énergie
    croissent avec le niveau de vie moins vite que la consommation totale (part plus forte chez les modestes)."""
    from outils.openfisca_mesures import depenses_bdf
    d = depenses_bdf()
    assert d[("CTOTALE", 1)] == 16123 and d[("CTOTALE", 10)] == 48353
    for code in ("0722", "045"):
        assert d[(code, 10)] > d[(code, 1)]
        assert d[(code, 1)] / d[("CTOTALE", 1)] > d[(code, 10)] / d[("CTOTALE", 10)]


def test_patrimoine_histoire_de_vie():
    """Roadmap 3.2 : patrimoine moyen par tranche de revenu disponible (Histoire de vie et Patrimoine 2020-2021) lu ;
    il croît avec le revenu à partir du 2e dixième (le premier compte des indépendants à faible revenu et fort patrimoine
    professionnel) ; un impôt réservé au 1 % du haut ne touche que lui et le montant total est conservé."""
    import types

    import numpy as np

    from outils.openfisca_mesures import Base, patrimoine_hvp, tranche_hvp
    pat = patrimoine_hvp()
    assert pat["D1"]["brut"] == 104400 and pat["P99"]["brut"] == 2828000
    ordre = [f"D{k}" for k in range(1, 10)] + ["P90_95", "P95_99", "P99"]
    assert all(pat[a]["brut"] < pat[b]["brut"] for a, b in zip(ordre[1:], ordre[2:]))
    assert all(0 < pat[t]["immobilier"] < pat[t]["net"] <= pat[t]["brut"] for t in ordre)
    assert list(tranche_hvp([0.05, 0.85, 0.92, 0.97, 0.995])) == ["D1", "D9", "P90_95", "P95_99", "P99"]
    n = 1000
    b = types.SimpleNamespace(wm=np.full(n, 30.0))
    rd = np.arange(n, dtype=float)
    g = Base.gain_patrimoine(b, rd, {"montant_md": 2.0, "composante": "net", "tranches": ["P99"]})
    assert (g[:990] == 0).all() and (g[990:] < 0).all()
    assert abs((b.wm * g).sum() / 1e9 + 2.0) < 1e-9
    g = Base.gain_patrimoine(b, rd, {"montant_md": -1.0, "composante": "net"})
    assert (g > 0).all() and g[-1] > g[0] and abs((b.wm * g).sum() / 1e9 - 1.0) < 1e-9


def test_pensions_calees_sur_le_moteur(pop):
    """Pensions au-delà d'un seuil multipliées par un facteur calé sur le montant du moteur (ART-RET-01 : sous-
    indexation du budget 2027 annulée, ≈ 5,5 Md€ au prudent) : les pensions sous le seuil ne bougent pas."""
    import types

    from outils.openfisca_mesures import Base, montant_moteur
    b = types.SimpleNamespace(lignes=pop, annee=2032)
    lg = Base.population(b, [{"population": {"pensions": {"seuil_mensuel": 1550, "programme": "arthaud",
                                                           "mesure": "ART-RET-01", "fin": 2200}}}])
    gain = sum(n["poids"] * (n["pension_brute"] - a["pension_brute"]) for n, a in zip(lg, pop)) / 1e9
    assert abs(gain + montant_moteur("arthaud", "ART-RET-01")) < 0.01 and gain > 5
    assert all(n["pension_brute"] == a["pension_brute"] for n, a in zip(lg, pop) if a["pension_brute"] <= 12 * 1550)


def test_formules_des_derniers_trous():
    """Derniers trous de la micro (22/11/2026) : cotisations des employeurs (part de long terme sur les salaires de la
    bande), heures supplémentaires (salariés de 1 à 2,5 SMIC), jeunes enfants (par enfant) ; montant conservé."""
    import types

    import numpy as np

    from moteur.parametres import Parametres
    from outils.openfisca_mesures import Base, ps_smic
    smic = ps_smic() * 12
    lignes = [{"statut": "salarie_prive", "salaire_brut": f * smic, "role": "ref", "age": 40} for f in (1.2, 2.0, 3.0)]
    lignes += [{"statut": "retraite", "salaire_brut": 0.0, "role": "ref", "age": 70},
               {"statut": "enfant", "salaire_brut": 0.0, "role": "enfant", "age": 0}]
    b = types.SimpleNamespace(lignes=lignes, s={"menage": np.arange(5)}, wm=np.full(5, 1000.0))
    g = Base.gain_cotisations_employeur(b, {"montant_md": 1.0, "bande_smic": (1.6, 3.5)})
    part = Parametres().val("entreprises.incidence_menages")["salaires"]
    assert g[0] == 0 and g[1] < 0 and g[2] < 0 and g[3] == 0
    assert abs((b.wm * g).sum() / 1e9 + part) < 1e-9
    h = Base.gain_cotisations_employeur(b, {"montant_md": -1.0, "bande_smic": (1.0, 2.5), "directe": True})
    assert h[0] > 0 and h[1] > 0 and h[2] == 0 and abs((b.wm * h).sum() / 1e9 - 1.0) < 1e-9
    j = Base.gain_jeunes_enfants(b, {"montant_md": -0.5, "age_max": 0})
    assert j[4] > 0 and (j[:4] == 0).all() and abs((b.wm * j).sum() / 1e9 - 0.5) < 1e-9
