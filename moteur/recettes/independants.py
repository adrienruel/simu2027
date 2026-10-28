"""Indépendants (feuille Indépendants, Total lignes 3 et 16).

Chaque indépendant exerce en société et choisit le moins cher entre : tout en salaire au
barème ; tout à l'IS (État + local) puis à la flat tax ; ou un salaire jusqu'au pivot et le
reste par la société. Une part du bénéfice des hauts revenus reste dans la société.
"""
from __future__ import annotations

import csv

from ..distribution import DONNEES
from ..impot_unique import impot
from ..parametres import Parametres
from ..tva import consommation_ht, taux_pour_revenu


def taux_is_total(p: Parametres, scenario: str = "prudent") -> float:
    return (p.val("entreprises.taux_is_etat", scenario) + p.val("impot_local_entreprises.taux_communes")
            + p.val("impot_local_entreprises.taux_regions"))


def classes(p: Parametres, scenario: str = "prudent") -> list[dict]:
    is_t = taux_is_total(p, scenario)
    ft = p.val("capital.flat_tax_dividendes")
    societe = 1 - (1 - is_t) * (1 - ft)
    pivot, seuil = p.val("independants.salaire_pivot"), p.val("independants.seuil_retention")
    k = p.val("independants.correction_couples")
    with (DONNEES / "independants.csv").open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    out = []
    for l in lignes:
        g = l["groupe"]
        effectif = float(l["part_effectif"]) * p.val(f"independants.{g}" if g != "micro" else "independants.micro_actifs")
        r = float(l["revenu_annuel"]) * (p.val("independants.passage_2023_2026") if l["annee_euros"] == "2023" else 1.0)
        j = float(l["taux_retention_societe"]) * max(0.0, r - seuil)
        d, e = impot(r, p, scenario), r * societe
        s = min(r - j, pivot)
        reste_societe = (r - j - s) * societe
        reste_bareme = impot(r - j, p, scenario) - impot(s, p, scenario)
        mixte = impot(s, p, scenario) + min(reste_societe, reste_bareme) + j * is_t
        fiscal = min(d, e, mixte) * k
        net = r - fiscal - j * (1 - is_t)
        sante, tva = taux_pour_revenu(net, p)
        tva_payee = consommation_ht(max(0.0, net), sante + tva, p) * (sante + tva)
        if abs(fiscal - e) < 0.5:
            passe_societe = r
        elif abs(fiscal - d) < 0.5:
            passe_societe = 0.0
        else:
            passe_societe = j + ((r - j - s) if reste_societe < reste_bareme else 0.0)
        out.append({"groupe": g, "effectif": effectif, "revenu": r, "impot": fiscal, "net": net,
                    "tva": tva_payee, "part_percue": p.val("independants.part_percue")[g],
                    "benefice_societe": passe_societe})
    return out


def impot_independants(p: Parametres, scenario: str = "prudent") -> float:
    return sum(c["effectif"] * c["impot"] * c["part_percue"] for c in classes(p, scenario))


def is_local_independants(p: Parametres, scenario: str = "prudent") -> float:
    base = sum(c["effectif"] * c["benefice_societe"] * c["part_percue"] for c in classes(p, scenario))
    return base * (p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions"))


def tva_independants(p: Parametres, scenario: str = "prudent") -> float:
    return sum(c["effectif"] * c["tva"] for c in classes(p, scenario))


def ligne_16(p: Parametres, scenario: str = "prudent") -> float:
    """Impôt des indépendants revenant à l'État (l'IS local va aux collectivités)."""
    return impot_independants(p, scenario) - is_local_independants(p, scenario)
