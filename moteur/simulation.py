"""Point d'entrée : une simulation complète, quatre scénarios (crise, prudent, médian, optimiste).

    from moteur.simulation import simuler
    res = simuler()                       # paramètres du fichier unique
    res["prudent"][2032]["deficit"]       # en % du PIB, au sens de Maastricht
"""
from __future__ import annotations

from .macro import ANNEES, SCENARIOS, calculer
from .parametres import Parametres
from .trajectoire_annuelle import postes


ORDRE = ("crise",) + tuple(SCENARIOS)


def _bloc(m, traj, avec_clause: bool) -> dict:
    out = {}
    for t in ANNEES:
        x = traj[t]
        ligne = {
            "recettes": x["recettes_hors_macro"] + m.solde_effet[t],
            "sante": x["sante"], "retraites": x["retraites"], "rui_aah": x["rui_aah"],
            "investissement": x["investissement"], "autres": x["autres"],
            "charge_dette": m.charge_dette[t], "solde": m.solde_public[t], "dette": m.dette[t],
            "deficit": -m.maastricht[t] * 100, "dette_pib": m.dette_pib[t] * 100,
            "emplois_supplementaires": m.emplois[t], "effet_pib": m.pib_effet[t], "clause": m.clause[t],
            "chomage": m.detail["chomage"][t] * 100,
        }
        if avec_clause:
            ligne["deficit_avant_clause"] = m.detail["clause"][t]["avant"] * 100
        out[t] = ligne
    return out


def simuler(p: Parametres | None = None, scenario_retenu: str = "prudent", crise: bool = True) -> dict:
    """Le scénario de crise est le prudent recalculé avec les paramètres de crise (feuille de la v235),
    point fixe de l'impôt local compris ; il passe lui aussi par la clause de trajectoire."""
    p = p or Parametres()
    traj = postes(p, scenario_retenu)
    macro = calculer(p, scenario_retenu)
    out = {}
    if crise:
        pc = p.en_crise()
        out["crise"] = _bloc(calculer(pc, scenario_retenu)["prudent"], postes(pc, scenario_retenu), True)
    for s in SCENARIOS:
        out[s] = _bloc(macro[s], traj, s == "prudent")
    return out


def resume(res: dict, annees=(2029, 2032, 2037)) -> str:
    lignes = ["Déficit au sens de Maastricht (% du PIB)"]
    for s in [x for x in ORDRE if x in res]:
        lignes.append(f"  {s:<10}" + "  ".join(f"{t} : {res[s][t]['deficit']:.2f}" for t in annees))
    for s in [x for x in ("crise", "prudent") if x in res]:
        lignes.append(f"  {s} avant clause " + "  ".join(f"{t} : {res[s][t]['deficit_avant_clause']:.2f}" for t in annees))
    return "\n".join(lignes)


if __name__ == "__main__":
    print(resume(simuler()))
