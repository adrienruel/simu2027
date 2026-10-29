"""Levier : taux de l'IS et part de l'investissement déduite immédiatement.

Pour chaque combinaison, le prudent sans clause (pour voir l'effet propre du levier) et le déficit publié.

    python -m outils.levier_is
"""
from __future__ import annotations

import json
from pathlib import Path

from moteur.emploi_canaux import tableau
from moteur.is_investissement import cout_net_etat
from moteur.macro import calculer
from moteur.parametres import Parametres
from moteur.recettes.total import recettes_nouveau_systeme
from moteur.simulation import simuler
from moteur.taux_effectifs import eatr_nouveau

TAUX_ETAT = (0.40, 0.35, 0.30, 0.25, 0.20)
DEDUCTION = (1.0, 0.5, 0.0)


def mesurer(p: Parametres) -> dict:
    sans = p.avec({"clause.active": False})
    sc = calculer(sans)["prudent"]
    pub = simuler(p, crise=False)["prudent"]
    loc = next(x for x in tableau(p) if x["mesure"] == "entreprises_localisation")
    c = sc.detail["canaux"]
    return {
        "taux_legal": p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions"),
        "eatr_prudent": eatr_nouveau(p, "prudent"),
        "recettes_statiques_md": recettes_nouveau_systeme(p)["total"] / 1e9,
        "cout_deduction_2037": cout_net_etat(p)[2037],
        "erosion_is_2037": c[2037]["erosion_is"],
        "investissement_2037": c[2037]["investissement_entreprises"],
        "investissement_2050": c[2050]["investissement_entreprises"],
        "emplois_localisation": loc["emplois_prudent"],
        "deficit_sans_clause": {t: -sc.maastricht[t] * 100 for t in (2029, 2032, 2037, 2050)},
        "deficit_publie": {t: pub[t]["deficit"] for t in (2029, 2032, 2037, 2050)},
        "dette_2050_sans_clause": sc.dette_pib[2050] * 100,
    }


def grille(p: Parametres | None = None) -> list[dict]:
    p = p or Parametres()
    out = []
    for te in TAUX_ETAT:
        for d in DEDUCTION:
            v = p.avec({"entreprises.taux_is_etat": te, "is_investissement.part_admise": d, "is_investissement.hausse_part_admise/cible": d})
            out.append({"taux_etat": te, "deduction": d, **mesurer(v)})
    return out


if __name__ == "__main__":
    g = grille()
    Path("sorties").mkdir(exist_ok=True)
    Path("sorties/levier_is.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'IS':>4} {'déd.':>4} {'EATR':>5} {'recettes':>8} {'déduc.':>6} {'érosion':>7} {'invest.':>7} {'emplois loc':>11} | sans clause 2029 2032 2037 2050 | publié 2029 2037 | dette 50")
    for x in g:
        d, q = x["deficit_sans_clause"], x["deficit_publie"]
        print(f"{x['taux_legal']*100:4.0f} {x['deduction']*100:4.0f} {x['eatr_prudent']*100:5.1f} {x['recettes_statiques_md']:8.1f} {x['cout_deduction_2037']:6.1f} {x['erosion_is_2037']:7.1f} {x['investissement_2037']:7.2f} {x['emplois_localisation']:11.0f} | {d[2029]:5.2f} {d[2032]:5.2f} {d[2037]:5.2f} {d[2050]:5.2f} | {q[2029]:5.2f} {q[2037]:5.2f} | {x['dette_2050_sans_clause']:5.1f}")
