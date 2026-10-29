"""Ménages types dans le système actuel, calculés par OpenFisca-France.

Lit parametres/menages_types.yaml, convertit les coûts employeur en salaires bruts (table OpenFisca du privé),
calcule chaque ménage avec la législation de l'année, et écrit
parametres/donnees/openfisca_menages_types_<année>.csv, que le moteur lit.

    python -m outils.openfisca_menages
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
PRESTATIONS = ("rsa", "ppa", "aide_logement", "af", "cf", "ars", "asf", "paje_base")


def _cout_en_brut(cout: float, table: list[dict]) -> float:
    xs = [float(l["cout_du_travail"]) for l in table]
    ys = [float(l["brut"]) for l in table]
    if cout <= 0:
        return 0.0
    for i in range(1, len(xs)):
        if xs[i] >= cout:
            return ys[i - 1] + (ys[i] - ys[i - 1]) * (cout - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[-1] * cout / xs[-1]


from moteur.menages_types import couts_adultes, pensions_adultes  # noqa: E402


def calculer(annee: int = 2026, menages: list[dict] | None = None) -> list[dict]:
    from openfisca_core.simulation_builder import SimulationBuilder
    from openfisca_france import FranceTaxBenefitSystem
    from moteur.parametres import Parametres
    p = Parametres()
    from outils.openfisca_reforme import construire
    tbs = construire(FranceTaxBenefitSystem(), p)
    if menages is None:
        menages = yaml.safe_load((RACINE / "parametres" / "menages_types.yaml").read_text(encoding="utf-8"))["menages"]
    with (RACINE / "parametres" / "donnees" / f"openfisca_prive_{annee}.csv").open(encoding="utf-8") as f:
        table = sorted(csv.DictReader(f), key=lambda l: float(l["cout_du_travail"]))
    an = str(annee)
    annees = [str(annee - 2), str(annee - 1), an]
    individus, foyers, familles, menages_of = {}, {}, {}, {}
    for m in menages:
        i = m["id"]
        adultes = [f"{i}_a{k}" for k in range(len(m["adultes"]))]
        enfants = [f"{i}_e{k}" for k in range(len(m["enfants"]))]
        for nom, cout, pension in zip(adultes, couts_adultes(m, p), pensions_adultes(m)):
            individus[nom] = {"salaire_de_base": {y: _cout_en_brut(cout, table) for y in annees},
                              "date_naissance": {y: "1985-01-01" if pension == 0 else "1955-01-01" for y in annees}}
            if pension > 0:
                individus[nom]["retraite_brute"] = {y: pension for y in annees}
            if len(adultes) == 2:
                individus[nom]["statut_marital"] = {y: "marie" for y in annees}
        for nom, age in zip(enfants, m["enfants"]):
            individus[nom] = {"date_naissance": {y: f"{annee - age}-01-01" for y in annees}}
        foyers[f"{i}_f"] = {"declarants": adultes, "personnes_a_charge": enfants}
        familles[f"{i}_fa"] = {"parents": adultes, "enfants": enfants}
        loyer = 550 if len(adultes) == 1 and not enfants else 800
        mo = {"personne_de_reference": adultes[:1], "enfants": enfants,
              "statut_occupation_logement": {y: "locataire_vide" for y in annees},
              "loyer": {y: 12 * loyer for y in annees}, "zone_apl": {y: "zone_2" for y in annees}}
        if len(adultes) == 2:
            mo["conjoint"] = adultes[1:]
        menages_of[f"{i}_m"] = mo
    sim = SimulationBuilder().build_from_entities(tbs, {"individus": individus, "foyers_fiscaux": foyers,
                                                         "familles": familles, "menages": menages_of})
    rd = sim.calculate_add("revenu_disponible", an)
    nouv = {v: sim.calculate(v, an) for v in ("revenu_disponible_nouveau",)}
    imp_u = sim.calculate("impot_unique", an)
    cout_i = sim.calculate("cout_employeur_annuel", an)
    rui_f = sim.calculate("rui_famille", an)
    ep_i = sim.calculate("epargne_obligatoire", an)
    loc_i = sim.calculate("impot_local_actif", an)
    rui_i = sim.calculate("rui_actif", an)
    ir = sim.calculate_add("impot_revenu_restant_a_payer", an)
    net = sim.calculate_add("salaire_net", an)
    prest = {}
    for v in PRESTATIONS:
        if v in tbs.variables:
            try:
                prest[v] = sim.calculate_add(v, an)
            except Exception:
                pass
    out = []
    ids_ind = list(individus)
    for k, m in enumerate(menages):
        i = m["id"]
        net_m = sum(float(net[ids_ind.index(n)]) for n in individus if n.startswith(i + "_a"))
        idx = [ids_ind.index(n) for n in individus if n.startswith(i + "_a")]
        ligne = {"id": i, "revenu_disponible": float(rd[k]), "impot_revenu": float(ir[k]), "salaire_net": net_m,
                 "couts": ";".join(f"{float(cout_i[j]):.2f}" for j in idx),
                 "nouveau_revenu_disponible": float(nouv["revenu_disponible_nouveau"][k]),
                 "nouveau_impot_unique": float(imp_u[k]),
                 "nouveau_impot_local": float(sum(loc_i[j] for j in idx)),
                 "nouveau_rui": float(sum(rui_i[j] for j in idx) + rui_f[k]),
                 "nouveau_epargne": float(sum(ep_i[j] for j in idx))}
        for v, x in prest.items():
            entite = tbs.variables[v].entity.key
            ligne[v] = float(x[k]) if entite in ("famille", "menage", "foyer_fiscal") else 0.0
        out.append(ligne)
    return out


def ecrire(annee: int = 2026) -> Path:
    lignes = calculer(annee)
    sortie = RACINE / "parametres" / "donnees" / f"openfisca_menages_types_{annee}.csv"
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        for l in lignes:
            w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in l.items()})
    return sortie


if __name__ == "__main__":
    print(f"Écrit : {ecrire(int(sys.argv[1]) if len(sys.argv) > 1 else 2026)}")
