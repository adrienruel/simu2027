"""Incidence des mesures sur les entreprises, par décile de revenu initial (roadmap du comparateur, phase 4.3).

    python -m outils.export_incidence     # sorties/comparaison_incidence_entreprises.csv

Une ligne par programme, année et décile (scénario prudent) : Md€ laissés aux entreprises (+) ou pris (−), arrivés
aux ménages en salaires, en prix et en revenus des actionnaires (moteur/incidence_entreprises.py). Sans effet sur le
solde publié."""
from __future__ import annotations

import csv

from moteur import incidence_entreprises as ie
from moteur import noyau
from moteur.parametres import RACINE, Parametres

ANNEES = (2032, 2037)


def main() -> None:
    from outils import trace
    p = Parametres()
    pop = ie._population()
    lignes = []
    for nom in noyau.programmes_disponibles()[1:]:
        prog = noyau.charger(nom)
        mont = ie.montant_entreprises(p, prog, "prudent")
        for t in ANNEES:
            for x in ie.par_decile(p, prog, "prudent", t, pop):
                lignes.append({"programme": nom, "scenario": "prudent", "annee": t, "decile": x["decile"],
                               "entreprises_md": round(mont.get(t, 0.0), 3),
                               **{k: round(v, 4) if k.endswith("_md") else round(v, 2) for k, v in x.items() if k != "decile"}})
    chemin = RACINE / "sorties" / "comparaison_incidence_entreprises.csv"
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    trace.enregistrer(chemin.name, script="outils.export_incidence")
    for nom in sorted({l["programme"] for l in lignes}):
        ls = [l for l in lignes if l["programme"] == nom and l["annee"] == 2032]
        print(f"{nom:12s} entreprises {ls[0]['entreprises_md']:+7.2f} Md€ ; D1 {ls[0]['eur_par_uc']:+7.1f} €/UC ; "
              f"D10 {ls[-1]['eur_par_uc']:+8.1f} €/UC")


if __name__ == "__main__":
    main()
