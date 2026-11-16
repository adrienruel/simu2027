"""Dynamique de la dette (phase 3.1 de la roadmap, 16/11/2026) : décomposition du déficit et variantes communes.

Écrit :
- sorties/comparaison_decomposition.csv : pour le statu quo et chaque programme publié, l'écart de déficit décomposé
  (moteur/decomposition.py) entre 2029 et une année (« depuis_2029 ») et, pour les programmes, l'écart au statu quo
  la même année (« ecart_statu_quo ») ;
- sorties/comparaison_variantes_dette.csv : déficit, dette et écart au statu quo dans trois variantes communes, à
  côté du calcul central : sans prime de dette, taux long à 3,3 %, et 2027-2028 projetées avec la croissance de la
  Banque de France (variante de la décision D3). Chaque variante s'applique au statu quo comme aux programmes.

    python -m outils.variantes_dette
"""
from __future__ import annotations

import csv

from moteur import decomposition as dc
from moteur import noyau
from moteur.parametres import RACINE, Parametres

SCENARIOS = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}
ANNEES = (2032, 2037, 2050)
# Variantes communes : mêmes modifications pour le statu quo et tous les programmes
VARIANTES = {
    "centrale": {},
    "sans_prime_dette": {"macro.prime_dette": 0.0},
    "taux_long_3_3": {"macro.taux_long_terme": 0.033},
    # Banque de France, projections intermédiaires du 15/09/2026 : 0,9 % en 2027, 1,2 % en 2028
    "croissance_2027_2028": {"calendrier.croissance_2027_2028": {2027: 0.009, 2028: 0.012}},
}
LIBELLES_VARIANTES = {
    "centrale": "Calcul publié",
    "sans_prime_dette": "Sans prime de dette",
    "taux_long_3_3": "Taux long à 3,3 % (au lieu de 4 %)",
    "croissance_2027_2028": "2027-2028 projetées (0,9 % et 1,2 %, Banque de France)",
}


def _variante(p: Parametres, modifs: dict) -> Parametres:
    if not modifs:
        return p
    if "calendrier.croissance_2027_2028" in modifs:
        # valeur structurée (année → taux) : remplacée en entier, sans passer par la recopie par scénario
        import dataclasses
        q = p.avec()
        par = q._p["calendrier.croissance_2027_2028"]
        q._p["calendrier.croissance_2027_2028"] = dataclasses.replace(par, valeur=dict(modifs["calendrier.croissance_2027_2028"]))
        return q
    return p.avec(modifs)


def calcul(noms=None) -> tuple[list[dict], list[dict]]:
    p0 = Parametres()
    noms = noms or noyau.programmes_disponibles()
    decomp, variantes = [], []
    for v, modifs in VARIANTES.items():
        p = _variante(p0, modifs)
        sq = noyau.simuler(p)
        for nom in noms:
            prog = noyau.charger(nom)
            lib = getattr(prog, "libelle", nom)
            res = sq if nom == "statu_quo" else noyau.simuler(p, prog)
            for s, traj in res.items():
                for t in ANNEES:
                    x, r = traj[t], sq[s][t]
                    variantes.append({
                        "programme": lib, "scenario": SCENARIOS[s], "annee": t, "variante": v,
                        "libelle_variante": LIBELLES_VARIANTES[v],
                        "deficit": round(x["deficit"], 3), "dette_pib": round(x["dette_pib"], 2),
                        "ecart_deficit_statu_quo": round(x["deficit"] - r["deficit"], 3),
                        "ecart_solde_primaire_pib": round((x["solde_primaire"] / x["pib"] - r["solde_primaire"] / r["pib"]) * 100, 3),
                        "ecart_dette_pib_statu_quo": round(x["dette_pib"] - r["dette_pib"], 2)})
                    if v != "centrale":
                        continue
                    comparaisons = [("depuis_2029", traj[2029], x)]
                    if nom != "statu_quo":
                        comparaisons.append(("ecart_statu_quo", r, x))
                    for comp, a, b in comparaisons:
                        e = dc.ecart(a, b)
                        decomp.append({"programme": lib, "scenario": SCENARIOS[s], "annee": t, "comparaison": comp,
                                       "ecart_deficit": round(e["total"], 3),
                                       **{k: round(e[k], 3) for k in dc.COMPOSANTES},
                                       "residu": round(e["residu"], 6)})
    return decomp, variantes


def _ecrire(nom: str, lignes: list[dict]) -> None:
    with (RACINE / "sorties" / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def main() -> None:
    decomp, variantes = calcul()
    _ecrire("comparaison_decomposition.csv", decomp)
    _ecrire("comparaison_variantes_dette.csv", variantes)
    from outils import trace
    trace.enregistrer(["comparaison_decomposition.csv", "comparaison_variantes_dette.csv"], script="outils.variantes_dette")
    for x in variantes:
        if x["programme"] == "Statu quo" and x["scenario"] == "Prudent":
            print(f"statu quo prudent {x['annee']} {x['variante']:22s} déficit {x['deficit']:6.2f}  dette {x['dette_pib']:6.1f}")


if __name__ == "__main__":
    main()
