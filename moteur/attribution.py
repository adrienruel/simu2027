"""Attribution : ce que chaque mesure séparable apporte au solde, année par année.

Méthode : contribution d'une mesure = résultat avec tout le programme − résultat sans cette mesure
(toutes choses égales par ailleurs). On compare le solde avant la clause de trajectoire, parce que
la clause compense ce qui manque et masquerait l'effet de la mesure.

La contribution se décompose en trois parts :
- statique : les lignes du budget (coût ou économie directe de la mesure) ;
- économie : les effets sur l'activité (emplois, PIB, recettes induites), canal par canal ;
- dette : la charge d'intérêts, qui cumule les soldes des années passées.

Les contributions ne s'additionnent pas exactement : les réformes de l'emploi ont des rendements
décroissants et l'impôt local se recale à chaque variante. L'écart est donné à part.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from . import noyau
from .mesures import registre as registre_economies
from .noyau import ANNEES
from .parametres import PROGRAMME_DEFAUT, Parametres, dossier_programme

def mesures(programme: str = PROGRAMME_DEFAUT) -> list[dict]:
    """Le registre complet du programme : entrées de registre_lois.yaml, puis une entrée par économie datée."""
    fichier = dossier_programme(programme) / "registre_lois.yaml"
    out = list(yaml.safe_load(fichier.read_text(encoding="utf-8"))["mesures"])
    for m in registre_economies(programme):
        if float(m["retenue"]) == 0:
            continue
        domaine = "retraites" if m["mesure"].startswith("Ancien système") else "economies"
        out.append({"id": "eco:" + m["mesure"][:50], "libelle": m["mesure"], "domaine": domaine,
                    "debut": int(m["premiere_annee"]), "economie": m["mesure"]})
    return out


def variante(p: Parametres, m: dict) -> Parametres:
    if "economie" in m:
        return p.avec(mesures_desactivees={m["economie"]})
    return p.avec(m["neutraliser"])


def _etat(p: Parametres, scenario: str = "prudent") -> dict:
    """Comptes d'un scénario du programme sur le noyau, sans règle de trajectoire (p porte clause.active = False).

    statique : mesures budgétaires (lignes du budget, périmètre) ; économie : effets sur l'activité, mesure par
    mesure (effets et écarts de méthode) et dynamiques du noyau (fonds)."""
    prog = noyau.charger(p.programme)
    res = noyau.simuler(p, prog, scenarios=(scenario,))[scenario]
    mes = prog.mesures(p)[scenario]
    out = {}
    for t in ANNEES:
        statique, canaux = 0.0, {}
        for m in mes:
            if m.nature == "physique" or m.poste == "participations":
                continue
            v = (1 if m.poste == "recettes" else -1) * m.valeurs.get(t, 0.0)
            if m.nature in ("budget", "perimetre", "mesure", "classement", "detail"):
                statique += v
            else:
                canaux[m.nom] = canaux.get(m.nom, 0.0) + v
        canaux["Fonds : capital, rendements, créances"] = res[t]["dynamiques"]["fonds"]["solde"]
        out[t] = {"statique": statique, "economie": sum(canaux.values()), "canaux": canaux,
                  "dette_interets": -res[t]["charge_dette"], "solde_avant_clause": res[t]["solde"],
                  "deficit_avant_clause": res[t]["deficit"],
                  "pib": res[t]["pib"], "chomage": res[t]["chomage"], "emplois": res[t]["emploi"]}
    return out


def attribuer(p: Parametres | None = None, selection: list[str] | None = None) -> dict:
    p = (p or Parametres()).avec({"clause.active": False})
    base = _etat(p)
    resultats = []
    for m in mesures(p.programme):
        if selection and m["id"] not in selection:
            continue
        v = _etat(variante(p, m))
        d = {t: {k: base[t][k] - v[t][k] for k in ("statique", "economie", "dette_interets", "solde_avant_clause",
                                                   "deficit_avant_clause", "chomage", "emplois")} for t in ANNEES}
        canaux = {t: {k: base[t]["canaux"][k] - v[t]["canaux"][k] for k in base[t]["canaux"]} for t in ANNEES}
        sans_ligne = all(abs(d[t]["statique"]) < 1e-6 for t in ANNEES)
        resultats.append({**{k: m[k] for k in ("id", "libelle", "domaine", "debut")}, "annees": d, "canaux": canaux,
                          "sans_ligne_budgetaire": sans_ligne})
    # Toutes les mesures retirées ensemble : l'écart avec la somme mesure par mesure donne les interactions
    ensemble = None
    if not selection:
        modifs, eco = {}, set()
        for m in mesures(p.programme):
            if "economie" in m:
                eco.add(m["economie"])
            else:
                modifs.update(m["neutraliser"])
        v = _etat(p.avec(modifs, mesures_desactivees=eco))
        ensemble = {t: {k: base[t][k] - v[t][k] for k in ("statique", "economie", "dette_interets", "solde_avant_clause",
                                                          "deficit_avant_clause", "chomage", "emplois")} for t in ANNEES}
    return {"base": base, "mesures": resultats, "ensemble": ensemble}
