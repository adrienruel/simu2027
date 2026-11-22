"""Roadmap 2.4 (22/11/2026) : allocations et prime d'activité d'un emploi en plus, selon la famille (micro)."""
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
    # 8 010 + 785 + 1 866 € par chômeur (outils/ppa_emplois.py)
    assert abs(p.val("emploi.allocation_chomeur_evitee") - (8010 + 785 + 1866)) < 10


def test_aides_au_logement_evitees_dans_le_bloc_logement():
    """Un programme qui crée des emplois baisse le bloc logement d'autant plus que part_allocation_logement est
    grande."""
    p = Parametres()
    r = {a: noyau.simuler(p.avec({"emploi.part_allocation_logement": a}), noyau.charger("lisnard"),
                          scenarios=("prudent",))["prudent"][2037] for a in (0.0, 0.074)}
    assert r[0.074]["emploi"] > noyau.simuler(p, None, scenarios=("prudent",))["prudent"][2037]["emploi"]
    assert r[0.074]["blocs"]["logement"] < r[0.0]["blocs"]["logement"]


def test_taux_emploi_des_jeunes_et_des_25_54_suivent_l_insee():
    """Roadmap 2.3 : les 15-24 et 25-54 ans suivent la projection de l'Insee (figure 2), comme les seniors."""
    from moteur.demographie import taux_emploi_par_age
    p = Parametres()
    t25, t40 = taux_emploi_par_age(p, 2025), taux_emploi_par_age(p, 2040)
    assert abs(t40[20] / t25[20] - 40.8 / (40.0 - (40.0 - 39.7) * 5 / 9)) < 1e-6
    assert abs(t40[40] / t25[40] - 1) < 0.002
