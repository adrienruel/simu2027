"""Restitution : les résultats d'une simulation mis en forme pour le tableau de bord (JSON).

    from moteur.restitution import donnees
    d = donnees()          # dictionnaire sérialisable
"""
from __future__ import annotations

import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

from .parametres import Parametres
from .simulation import ORDRE, simuler

RACINE = Path(__file__).resolve().parent.parent

LIBELLES_CANAUX = {
    "emploi": "Emplois créés (RUI économisé, impôt, TVA)",
    "ajustement_budgetaire": "Ajustement budgétaire (multiplicateur)",
    "capital_du_fonds": "Capital du fonds souverain",
    "logement": "Logement",
    "erosion_is": "Érosion de l'assiette de l'IS",
    "fraude_tva": "Fraude à la TVA récupérée",
    "fin_aides_construction": "Fin des aides à la construction",
    "productivite": "Productivité",
    "reactions_impot": "Réactions à l'impôt",
    "ia": "Intelligence artificielle",
    "tendance_et_ecole": "Croissance tendancielle et école",
    "investissement_entreprises": "Investissement des entreprises",
    "sante": "Santé (écart au prudent, TVA santé)",
    "carbone": "Carbone",
    "eviction_epargne": "Éviction de l'épargne volontaire",
    "clause": "Clause de trajectoire",
    "demographie": "Démographie (écart au prudent)",
}

POSTES = [("recettes", "Recettes"), ("sante", "Santé"), ("retraites", "Retraites"), ("rui_aah", "RUI et AAH"),
          ("investissement", "Investissement"), ("autres", "Autres dépenses"), ("charge_dette", "Charge de la dette (réelle)"),
          ("solde", "Solde public")]


def _version() -> str:
    try:
        return subprocess.run(["git", "describe", "--always", "--dirty"], cwd=RACINE, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "inconnue"


def _r(x: float, n: int = 4) -> float:
    return round(float(x), n)


def donnees(p: Parametres | None = None) -> dict:
    p = p or Parametres()
    res = simuler(p)
    annees = sorted(res["prudent"])
    scen = [s for s in ORDRE if s in res]
    series = {}
    for s in scen:
        b = res[s]
        series[s] = {
            "deficit": [_r(b[t]["deficit"]) for t in annees],
            "dette_pib": [_r(b[t]["dette_pib"], 3) for t in annees],
            "chomage": [_r(b[t]["chomage"]) for t in annees],
            "pib": [_r(b[t]["pib"], 2) for t in annees],
            "emplois": [round(b[t]["emplois_supplementaires"]) for t in annees],
            "postes": {k: [_r(b[t][k], 3) for t in annees] for k, _ in POSTES},
            "canaux": {k: [_r(b[t]["canaux"][k], 3) for t in annees] for k in LIBELLES_CANAUX},
        }
        if "deficit_avant_clause" in b[annees[0]]:
            series[s]["deficit_avant_clause"] = [_r(b[t]["deficit_avant_clause"]) for t in annees]
            series[s]["clause"] = {k: [_r(b[t]["clause_detail"][k], 3) for t in annees]
                                   for k in ("etalement", "contribution", "points", "rui", "rui_euros", "reste")}
    from .trajectoire_annuelle import lignes as lignes_traj
    registres = {"prudent": lignes_traj(p), "crise": lignes_traj(p.en_crise())}
    for s in scen:
        reg = registres["crise" if s == "crise" else "prudent"]
        series[s]["lignes"] = [{"cle": x["cle"], "libelle": x["libelle"], "poste": x["poste"], "nature": x["nature"],
                                "valeurs": [_r(x["valeurs"].get(t, 0.0), 3) for t in annees]}
                               for x in reg.lignes.values() if any(abs(v) > 1e-6 for v in x["valeurs"].values())]
        series[s]["postes"]["transferts_collectivites"] = [_r(res[s][t]["transferts_collectivites"], 3) for t in annees]
    from .attribution import attribuer
    att = attribuer(p)
    cles = ("solde_avant_clause", "statique", "economie", "dette_interets", "deficit_avant_clause", "chomage")
    attribution = {
        "mesures": [{"id": m["id"], "libelle": m["libelle"], "domaine": m["domaine"], "debut": m["debut"],
                     "sans_ligne": m["sans_ligne_budgetaire"],
                     **{k: [_r(m["annees"][t][k], 3) for t in annees] for k in cles}} for m in att["mesures"]],
        "ensemble": {k: [_r(att["ensemble"][t][k], 3) for t in annees] for k in cles},
        "somme": {k: [_r(sum(m["annees"][t][k] for m in att["mesures"]), 3) for t in annees] for k in cles},
    }
    def categorie(x):
        if x.statut == "HYPOTHESE":
            return "HYPOTHESE_ENCADREE" if x.source else "HYPOTHESE"
        return x.statut
    # Sensibilité : lue dans sorties/sensibilite.json (python -m moteur.sensibilite, quelques minutes)
    import json
    fichier = RACINE / "sorties" / "sensibilite.json"
    brut = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else []
    sens = [r for r in brut if "erreur" not in r and r.get("parametre", r["cle"]) in p._p
            and p[r.get("parametre", r["cle"])].statut == "HYPOTHESE"][:15]
    sensibilite = [{"cle": r["cle"], "note": (p[r.get("parametre", r["cle"])].note or "")[:200], "encadree": bool(p[r.get("parametre", r["cle"])].source),
                    "deficit_2037": _r(r["deficit_2037"], 3), "deficit_2050": _r(r["deficit_2050"], 3)} for r in sens]
    fichier_inc = RACINE / "sorties" / "incertitude.json"
    incertitude = json.loads(fichier_inc.read_text(encoding="utf-8")) if fichier_inc.exists() else None
    if incertitude:
        incertitude = {"n": incertitude["n"], "resume": incertitude["resume"],
                       "influence": [[k, round(v, 3)] for k, v in list(incertitude["influence_deficit_2037"].items())[:10]],
                       "notes": {k: (p[k].note or "")[:160] for k in list(incertitude["influence_deficit_2037"])[:10] if k in p._p}}
    from .menages_types import comparer
    menages = [{"libelle": x["libelle"], "actuel": round(x["actuel"]["revenu_disponible"]),
                "nouveau": round(x["nouveau"]["revenu_disponible"]), "epargne": round(x["nouveau"]["epargne_obligatoire"]),
                "impot_unique": round(x["nouveau"]["impot_unique"]), "impot_local": round(x["nouveau"]["impot_local"]),
                "rui": round(x["nouveau"]["rui"] + x["nouveau"]["complements_enfants"]),
                "ecart_conso": round(100 * x["ecart_consommation_pct"], 1)} for x in comparer(p)]
    from .menages_types import futurs_retraites, nouveau
    actifs = {"Carrière au SMIC": "smic", "Carrière au salaire médian": "median", "Carrière de cadre (100 000 €)": 100000}
    retraites_futurs = []
    for x in futurs_retraites(p):
        net_actif = nouveau({"adultes": [actifs[x["libelle"]]], "enfants": []}, p)["revenu_disponible"] / 12
        retraites_futurs.append({"libelle": x["libelle"], "rente": round(x["rente"]), "socle": round(x["socle"]),
                                 "net": round(x["net_mensuel"]), "net_actif": round(net_actif),
                                 "remplacement": round(100 * x["net_mensuel"] / net_actif)})
    from .emploi_canaux import tableau as tableau_emploi
    from .attribution import mesures as registre_mesures
    libelles = {m["id"]: m["libelle"] for m in registre_mesures()}
    alias = {"bas_salaires": "bas_salaires_rui", "entreprises_cout_travail": "reforme_entreprises_emploi",
             "droit_a_construire": "droit_a_construire_emploi"}
    libelles["reforme_entreprises_emploi"] = "Réforme des entreprises : fin des impôts de production sur les salaires"
    libelles["entreprises_localisation"] = "Réforme des entreprises : activités qui partent avec l'IS à 45 %"
    emploi_mesures = [{"libelle": libelles.get(alias.get(x["mesure"], x["mesure"]), x["mesure"]),
                       "canal": x["canal"], "crise": round(x["emplois_crise"]), "prudent": round(x["emplois_prudent"]),
                       "median": round(x["emplois_median"]), "optimiste": round(x["emplois_optimiste"]),
                       "gain": round(x["gain_par_emploi"]), "solde": round(x["solde_md"], 2)} for x in tableau_emploi(p)]
    from . import demographie as demo_m
    population = None
    if p.val("demographie.active"):
        jalons = [2029, 2037, 2050, 2060, 2073]
        population = {"jalons": jalons, "ecart_soutien": round(demo_m.ecart_soutien_enfant(p)),
                      "effet_naissances": {j: round(100 * demo_m.effet_naissances(p, j), 1) for j in ("crise", "prudent", "optimiste")},
                      "scenarios": {}}
        for j in ("crise", "prudent", "optimiste"):
            e = demo_m.effectifs(p, j)
            population["scenarios"][j] = {k: [round(e[t][k] / 1e6, 2) for t in jalons] for k in ("emploi", "enfants", "seniors", "total")}
        from .ancien_systeme import serie as serie_ancien
        from .retraites_transition import retraites_nouveau_systeme, cout_socle
        sa, rn, cs = serie_ancien(p), retraites_nouveau_systeme(p), cout_socle(p)
        population["retraites"] = {"ancien": [round(sa[t]["retraites_millions"], 2) for t in jalons],
                                   "depenses_ancien": [round(sa[t]["depenses_md"]) for t in jalons],
                                   "nouveau": [round(rn[t] / 1e6, 2) for t in jalons],
                                   "socle": [round(cs[t]) for t in jalons]}
        population["valeur_enfant"] = [{**x, "nouveau": round(x["nouveau"], 2)} for x in demo_m.valeur_enfant(p)]
    corriges = sorted(x.cle for x in p if x.v235 is not None)
    statuts = Counter(categorie(x) for x in p)
    hypotheses = sorted((x.cle for x in p if x.statut == "HYPOTHESE" and not x.source))
    groupes = Counter(c.split(".")[0] for c in hypotheses)
    return {
        "meta": {"version": _version(), "date": date.today().isoformat(), "euros": "euros constants de 2026",
                 "scenario_publie": "prudent", "chomage_jusqu_a": 2040},
        "annees": annees,
        "scenarios": scen,
        "series": series,
        "libelles_canaux": LIBELLES_CANAUX,
        "postes": POSTES,
        "attribution": attribution,
        "incertitude": incertitude,
        "menages": menages,
        "emploi_mesures": emploi_mesures,
        "retraites_futurs": retraites_futurs,
        "population": population,
        "parametres": {"total": sum(statuts.values()), "statuts": dict(statuts), "sensibilite": sensibilite, "corriges": corriges,
                       "hypotheses_par_groupe": groupes.most_common()},
    }
