"""Point d'entrée : une simulation complète, quatre scénarios calculés ensemble (crise à venir).

    from moteur.simulation import simuler
    res = simuler()                       # paramètres du fichier unique
    res["prudent"][2032]["deficit"]       # en % du PIB, au sens de Maastricht
"""
from __future__ import annotations

from .macro import ANNEES, SCENARIOS, calculer
from .parametres import Parametres
from .trajectoire_annuelle import postes


def simuler(p: Parametres | None = None, scenario_retenu: str = "prudent") -> dict:
    p = p or Parametres()
    traj = postes(p, scenario_retenu)
    macro = calculer(p, scenario_retenu)
    out = {}
    for s in SCENARIOS:
        m = macro[s]
        out[s] = {}
        for t in ANNEES:
            x = traj[t]
            pib_ref = m.pib_effet[t]  # effet ; le PIB total = PIB de référence + effet
            ligne = {
                "recettes": x["recettes_hors_macro"] + m.solde_effet[t],
                "sante": x["sante"], "retraites": x["retraites"], "rui_aah": x["rui_aah"],
                "investissement": x["investissement"], "autres": x["autres"],
                "charge_dette": m.charge_dette[t], "solde": m.solde_public[t], "dette": m.dette[t],
                "deficit": -m.maastricht[t] * 100, "dette_pib": m.dette_pib[t] * 100,
                "emplois_supplementaires": m.emplois[t], "effet_pib": pib_ref, "clause": m.clause[t],
            }
            if s == "prudent":
                c = m.detail["clause"][t]
                ligne["deficit_avant_clause"] = c["avant"] * 100
            out[s][t] = ligne
    return out


def resume(res: dict, annees=(2029, 2032, 2037)) -> str:
    lignes = ["Déficit au sens de Maastricht (% du PIB)"]
    for s in SCENARIOS:
        lignes.append(f"  {s:<10}" + "  ".join(f"{t} : {res[s][t]['deficit']:.2f}" for t in annees))
    lignes.append("  prudent avant clause " + "  ".join(f"{t} : {res['prudent'][t]['deficit_avant_clause']:.2f}" for t in annees))
    return "\n".join(lignes)


if __name__ == "__main__":
    print(resume(simuler()))
