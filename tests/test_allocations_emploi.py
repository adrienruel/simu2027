"""Roadmap 2.4 (22/11/2026) : allocations et prime d'activité d'un emploi en plus, selon la famille (micro)."""
import pytest

from moteur import noyau
from moteur.parametres import Parametres


def test_prime_activite_selon_la_famille():
    p = Parametres()
    seul = noyau.ppa_par_emploi(p.avec({"emploi.prime_activite_familles": 1.0}), "prudent")
    fam = noyau.ppa_par_emploi(p, "prudent")
    assert abs(fam[2030] / seul[2030] - p.val("emploi.prime_activite_familles")) < 1e-9
    assert 0 < fam[2030] < seul[2030]


def test_parts_des_allocations_evitees():
    p = Parametres()
    ac, al = p.val("emploi.part_allocation_assurance_chomage"), p.val("emploi.part_allocation_logement")
    assert 0 < al < ac < 1 and ac + al < 1
    # 11 491 + 665 + 1 694 € par chômeur (outils/ppa_emplois.py, population recalée en 3.6, 4.4, le 25/11 et le 26/11)
    assert abs(p.val("emploi.allocation_chomeur_evitee") - (11491 + 665 + 1694)) < 10


def test_aides_au_logement_evitees_dans_le_bloc_logement():
    """Un programme qui crée des emplois baisse le bloc logement d'autant plus que part_allocation_logement est
    grande."""
    p = Parametres()
    r = {a: noyau.simuler(p.avec({"emploi.part_allocation_logement": a}), noyau.charger("attal"),
                          scenarios=("prudent",))["prudent"][2037] for a in (0.0, 0.050)}
    # emplois créés par les mesures, hors rétroaction des taux (comptée dans l'emploi publié depuis R3.2, 26/11/2026 :
    # 27/11/2026 : Attal, qui crée des emplois au prudent ; Lisnard n'en crée plus en 2037 depuis le barème commun
    # de l'assurance chômage)
    hors_taux = r[0.050]["emploi"] - r[0.050]["emplois_canaux"].get("Taux d'intérêt (bouclage)", 0.0)
    assert hors_taux > noyau.simuler(p, None, scenarios=("prudent",))["prudent"][2037]["emploi"]
    assert r[0.050]["blocs"]["logement"] < r[0.0]["blocs"]["logement"]


def test_taux_emploi_des_jeunes_et_des_25_54_suivent_l_insee():
    """Roadmap 2.3 : les 15-24 et 25-54 ans suivent la projection de l'Insee (figure 2), comme les seniors."""
    from moteur.demographie import taux_emploi_par_age
    p = Parametres()
    t25, t40 = taux_emploi_par_age(p, 2025), taux_emploi_par_age(p, 2040)
    assert abs(t40[20] / t25[20] - 40.8 / (40.0 - (40.0 - 39.7) * 5 / 9)) < 1e-6
    assert abs(t40[40] / t25[40] - 1) < 0.002


def test_pfu_regle_commune():
    """Roadmap 4.4 : hausse du PFU chiffrée par la règle commune ; la réponse des dividendes mange une partie du
    statique, plus au prudent qu'à l'optimiste ; une baisse prend le scénario miroir."""
    from moteur.capital_dirigeants import recette_pfu
    p = Parametres()
    r = {s: recette_pfu(p, s, 2)["total"] for s in ("crise", "prudent", "median", "optimiste")}
    statique = 0.02 * sum(p.val("dividendes.bases_2026")[k] for k in ("dividendes", "interets"))
    assert r["crise"] < r["prudent"] < r["median"] < r["optimiste"] < statique
    b = recette_pfu(p, "prudent", -2)
    assert b["total"] < 0 and abs(b["total"]) < statique
    assert recette_pfu(p, "prudent", 0, 3)["autres_patrimoine"] == pytest.approx(0.03 * p.val("dividendes.bases_2026")["autres_csg"])


def test_entrepreneurs_individuels_et_is():
    """Roadmap 4.4 : une baisse de l'IS fait passer des entrepreneurs individuels à l'IS (recette en moins), plus
    au scénario crise (miroir)."""
    from moteur.capital_dirigeants import facteur_ei_vers_is
    p = Parametres()
    k = {s: facteur_ei_vers_is(p, s, -10) for s in ("crise", "prudent", "median", "optimiste")}
    assert k["crise"] > k["prudent"] > k["optimiste"] > 0
    ms = noyau.charger("lisnard").mesures(p)["prudent"]
    ei = next(m for m in ms if m.nom.startswith("LIS-FIS-03 — entrepreneurs individuels"))
    assert ei.valeurs[2037] < 0
