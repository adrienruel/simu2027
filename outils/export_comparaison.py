"""Exporte la comparaison de tous les programmes chiffrés sur le noyau (sorties/comparaison_*.csv), pour le tableau
de bord de comparaison. Un nouveau programme (dossier programmes/<nom>/ avec programme.py) y entre sans rien changer
ici.

    python -m outils.export_comparaison

- comparaison_trajectoire.csv : déficit, dette, solde primaire, intérêts, recettes, dépenses primaires… par
  programme, scénario et année ;
- comparaison_ecarts.csv : écart avec le statu quo par grand poste (+ = améliore le solde), Md€ de 2026 et % du PIB ;
- comparaison_mesures.csv : chaque mesure, à quelques années (même signe).
"""
from __future__ import annotations

import csv

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import RACINE, Parametres

SCENARIOS = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}
ANNEES_MESURES = (2029, 2032, 2037, 2045, 2050, 2060, 2073)
# grand poste de chaque mesure (poste du noyau → groupe affiché)
GROUPES = {
    "recettes": "Recettes", "retraites": "Retraites", "sante": "Santé",
    "chomage": "Prestations et revenu universel", "famille": "Prestations et revenu universel",
    "logement": "Prestations et revenu universel", "pauvrete": "Prestations et revenu universel",
    "aah_invalidite": "Prestations et revenu universel",
    "etat_missions": "État et défense", "defense_ue": "État et défense",
    "collectivites": "Collectivités", "investissement": "Investissement", "autres": "Autres dépenses",
}
NATURES_CACHEES = ("detail", "controle")  # sommes nulles : rien à montrer


def groupe(m: noyau.Mesure) -> str:
    nom = m.nom.lower()
    if m.nature == "perimetre":  # ressources au périmètre : des recettes ; dépenses : leur poste
        if m.poste == "recettes":
            return "Recettes"
        return "Collectivités" if "collectivités" in nom else "Autres dépenses"
    if "investissement local" in nom:  # laissé dans les dépenses des collectivités
        return "Collectivités"
    if m.nature == "effet_macro":
        return "Effets économiques"
    if m.nature == "methode":
        return "Écarts de méthode"
    if m.poste == "participations":
        return "Participations (fonds)"
    if m.poste.startswith("nouveau:"):
        base = m.poste.split(":", 1)[1]
        return {"rui_aah": "Prestations et revenu universel"}.get(base, GROUPES.get(base, "Autres dépenses"))
    return GROUPES.get(m.poste, "Autres dépenses")


def _ecrire(nom: str, lignes: list[dict]) -> None:
    with (RACINE / "sorties" / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def main() -> None:
    p = Parametres()
    base = sq.simuler(p)
    traj, ecarts, mesures = [], [], []
    for nom in noyau.programmes_disponibles():
        prog = noyau.charger(nom)
        lib = getattr(prog, "libelle", nom)
        res = base if nom == "statu_quo" else noyau.simuler(p, prog)
        tout = prog.mesures(p)
        for s, v in res.items():
            for t, x in v.items():
                traj.append({"programme": lib, "scenario": SCENARIOS[s], "annee": t,
                             "deficit": round(x["deficit"], 3), "dette_pib": round(x["dette_pib"], 2),
                             "solde_primaire_pib": round(x["solde_primaire"] / x["pib"] * 100, 3),
                             "interets_pib": round(x["charge_dette"] / x["pib"] * 100, 3),
                             "recettes_pib": round(x["recettes_pib"], 3),
                             "depenses_primaires_pib": round(x["depenses_primaires_pib"], 3),
                             "retraites_pib": round(x["retraites_pib"], 3), "chomage": round(x["chomage"], 3),
                             "pib_md": round(x["pib"], 1)})
            if nom == "statu_quo":
                continue
            ms = [m for m in tout.get(s, []) if m.nature not in NATURES_CACHEES]
            signe = lambda m: 1 if m.poste == "recettes" else (0 if m.poste == "participations" else -1)  # noqa: E731
            for t in v:
                y = v[t]["pib"]
                par = {}
                for m in ms:
                    par[groupe(m)] = par.get(groupe(m), 0.0) + signe(m) * m.valeurs.get(t, 0.0)
                # intérêts : ce que la trajectoire du programme change à la charge de la dette
                par["Intérêts de la dette"] = base[s][t]["charge_dette"] - v[t]["charge_dette"]
                par.pop("Participations (fonds)", None)
                # le reste de l'écart de déficit : ratios rapportés à un PIB différent, inflation sur la dette
                reste = (base[s][t]["deficit"] - v[t]["deficit"]) - sum(par.values()) / y * 100
                par["Effet du PIB sur les ratios"] = reste * y / 100
                for g, val in par.items():
                    ecarts.append({"cle": f"{lib}|{SCENARIOS[s]}|{t}|{g}", "programme": lib, "scenario": SCENARIOS[s], "annee": t, "groupe": g,
                                   "md": round(val, 2), "part_pib": round(val / y * 100, 3)})
            for i, m in enumerate(ms):
                if signe(m) == 0:
                    continue
                for t in ANNEES_MESURES:
                    val = signe(m) * m.valeurs.get(t, 0.0)
                    mesures.append({"cle": f"{lib}|{SCENARIOS[s]}|{t}|{i}", "programme": lib, "scenario": SCENARIOS[s], "annee": t, "groupe": groupe(m),
                                    "mesure": m.nom, "nature": m.nature, "md": round(val, 2),
                                    "part_pib": round(val / v[t]["pib"] * 100, 3)})
    _ecrire("comparaison_trajectoire.csv", traj)
    _ecrire("comparaison_ecarts.csv", ecarts)
    _ecrire("comparaison_mesures.csv", mesures)
    print("Écrit : sorties/comparaison_trajectoire.csv, comparaison_ecarts.csv, comparaison_mesures.csv")


if __name__ == "__main__":
    main()
