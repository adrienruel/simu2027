"""Exporte les résultats du statu quo en tables (sorties/statu_quo_*.csv) pour le tableau de bord.

    python -m outils.export_statu_quo
"""
from __future__ import annotations

import csv

from moteur import statu_quo as sq
from moteur.parametres import RACINE, Parametres

LIBELLES_BLOCS = {
    "retraites": "Retraites", "sante": "Santé et autonomie", "chomage": "Assurance chômage",
    "famille": "Prestations familiales", "logement": "Aides au logement", "pauvrete": "RSA et prime d'activité",
    "aah_invalidite": "AAH et invalidité", "investissement": "Investissement public",
    "etat_missions": "Missions de l'État", "defense_ue": "Défense et UE", "collectivites": "Collectivités",
    "autres": "Sécurité sociale et opérateurs (reste)",
}
LIBELLES_IMPOTS = {
    "salaires_prive": "Cotisations, CSG, IR : salariés du privé", "salaires_public": "Cotisations, CSG, IR : agents publics",
    "independants": "Cotisations, CSG, IR : indépendants", "retraites": "CSG, CASA, IR : retraités",
    "tva": "TVA", "accises_et_taxes_sur_produits": "Accises et taxes sur les produits",
    "impot_sur_les_societes": "Impôt sur les sociétés", "impots_de_production": "Impôts de production",
    "capital_dividendes_ifi": "Capital (dividendes, intérêts, IFI)", "successions": "Successions",
    "droits_de_mutation": "Droits de mutation", "taxes_locales_et_affectees": "Taxes locales et affectées",
    "non_fiscales": "Recettes non fiscales",
}
SCENARIOS = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}


def _ecrire(nom: str, lignes: list[dict]) -> None:
    with (RACINE / "sorties" / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def main() -> None:
    p = Parametres()
    res = sq.simuler(p)
    traj = []
    for s, v in res.items():
        for t, x in v.items():
            traj.append({"scenario": SCENARIOS[s], "annee": t, "deficit": round(x["deficit"], 3),
                         "dette_pib": round(x["dette_pib"], 2), "solde_primaire_pib": round(x["solde_primaire"] / x["pib"] * 100, 3),
                         "interets_pib": round(x["charge_dette"] / x["pib"] * 100, 3), "chomage": round(x["chomage"], 3),
                         "recettes_pib": round(x["recettes_pib"], 3), "depenses_primaires_pib": round(x["depenses_primaires_pib"], 3),
                         "retraites_pib": round(x["retraites_pib"], 3), "sante_pib": round(x["sante_pib"], 3),
                         "pib_md": round(x["pib"], 1)})
    _ecrire("statu_quo_trajectoire.csv", traj)
    v = res["prudent"]
    blocs = [{"annee": t, "bloc": LIBELLES_BLOCS[b], "md": round(m, 2), "part_pib": round(m / v[t]["pib"] * 100, 3)}
             for t in sq.ANNEES for b, m in v[t]["blocs"].items()]
    _ecrire("statu_quo_depenses.csv", blocs)
    r = sq.recettes_par_impot(p, "prudent")
    rec = [{"annee": t, "impot": LIBELLES_IMPOTS[i], "md": round(m, 2), "part_pib": round(m / v[t]["pib"] * 100, 3)}
           for t in sq.ANNEES for i, m in r[t].items()]
    _ecrire("statu_quo_recettes.csv", rec)
    print("Écrit : sorties/statu_quo_trajectoire.csv, statu_quo_depenses.csv, statu_quo_recettes.csv")


if __name__ == "__main__":
    main()
