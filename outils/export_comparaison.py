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
NATURES_CACHEES = ("detail", "controle", "physique")  # sommes nulles ou sans montant : rien à montrer


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


def taux_emploi_18_66(p: Parametres, s: str, t: int, emploi: float) -> float:
    """Personnes en emploi de 18 à 66 ans / population de 18 à 66 ans (%). Tranche qui contient le report de l'âge de
    départ à 67 ans ; l'emploi après 67 ans est celui du statu quo (taux de 2025 par âge), retiré de l'emploi."""
    from moteur.demographie import _tranche
    pop = sq.population(p, s)[t]
    taux = {a: x for k, x in p.val("demographie.taux_emploi_age").items() for a in _tranche(k)}
    apres = sum(pop[a] * taux.get(a, 0.0) for a in range(67, len(pop)))
    return (emploi - apres) / sum(pop[18:67]) * 100


def lignes_ecologie(p: Parametres, lib: str, prog) -> list[dict]:
    """Émissions et empreinte d'un programme (statu quo si prog est None), par scénario et par année : le statu quo,
    l'effet de l'activité (publié à part, pas une politique climatique), l'effet des mesures, l'écart cumulé aux
    budgets carbone. Statut : « simule » pour tout ce que le modèle calcule."""
    from moteur.ecologie import emissions as em
    out = []
    mes = prog.mesures(p) if prog is not None else {}
    ctx = prog.contexte(p) if prog is not None else {}
    for s, nom_s in SCENARIOS.items():
        b = em.bilan(p, s, mes.get(s), ctx.get(s))
        cumul = em.ecart_snbc_cumule(b)
        for t in em.ANNEES_MODELE:
            x = b[t]
            out.append({"cle": f"{lib}|{nom_s}|{t}", "programme": lib, "scenario": nom_s, "annee": t,
                        "territoriales_mt": round(x["territoriales"], 2), "territoriales_hab_t": round(x["territoriales_hab"], 3),
                        "empreinte_mt": round(x["empreinte"], 2), "empreinte_hab_t": round(x["empreinte_hab"], 3),
                        "importees_mt": round(x["importees"], 2), "statu_quo_mt": round(x["statu_quo"], 2),
                        "effet_activite_mt": round(x["effet_activite"], 2), "effet_mesures_mt": round(x["effet_mesures"], 2),
                        "plafond_snbc_mt": round(x["plafond_snbc"], 1), "ecart_snbc_cumule_mt": round(cumul[t], 1),
                        **{f"secteur_{i}_mt": round(x["secteurs"][i], 2) for i in em.SECTEURS}, "statut": "simule"})
    return out


def _ecrire(nom: str, lignes: list[dict]) -> None:
    with (RACINE / "sorties" / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def main() -> None:
    p = Parametres()
    base = sq.simuler(p)
    traj, ecarts, mesures, ecologie, emploi_canaux, ecologie_mesures = [], [], [], [], [], []
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
                             "pib_md": round(x["pib"], 1),
                             "emploi_millions": round(x["emploi"] / 1e6, 4),
                             "ecart_emploi_milliers": round((x["emploi"] - base[s][t]["emploi"]) / 1e3, 1),
                             "taux_emploi_18_66": round(taux_emploi_18_66(p, s, t, x["emploi"]), 3)})
                for canal, n in x["emplois_canaux"].items():
                    emploi_canaux.append({"cle": f"{lib}|{SCENARIOS[s]}|{t}|{canal}", "programme": lib, "scenario": SCENARIOS[s],
                                          "annee": t, "canal": canal, "emplois_milliers": round(n / 1e3, 1)})
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
        ecologie.extend(lignes_ecologie(p, lib, None if nom == "statu_quo" else prog))
        if nom != "statu_quo":
            for s_, liste in tout.items():
                for i, m in enumerate(liste):
                    for k, serie in (m.physique or {}).items():
                        for t in ANNEES_MESURES:
                            ecologie_mesures.append({"cle": f"{lib}|{SCENARIOS[s_]}|{t}|{i}|{k}", "programme": lib, "scenario": SCENARIOS[s_],
                                                     "annee": t, "mesure": m.nom.replace(" (émissions)", ""),
                                                     "secteur": k.split(":", 1)[-1] if k.startswith("emissions_mt:") else "importations",
                                                     "mt": round(serie.get(t, 0.0), 3)})
    _ecrire("comparaison_trajectoire.csv", traj)
    _ecrire("comparaison_ecologie.csv", ecologie)
    _ecrire("comparaison_emploi_canaux.csv", emploi_canaux)
    _ecrire("comparaison_ecologie_mesures.csv", ecologie_mesures)
    _ecrire("comparaison_ecarts.csv", ecarts)
    _ecrire("comparaison_mesures.csv", mesures)
    print("Écrit : sorties/comparaison_trajectoire.csv, comparaison_ecarts.csv, comparaison_mesures.csv, comparaison_ecologie.csv, comparaison_emploi_canaux.csv, comparaison_ecologie_mesures.csv")


if __name__ == "__main__":
    main()
