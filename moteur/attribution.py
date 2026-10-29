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

from .macro import ANNEES, calculer
from .mesures import registre as registre_economies
from .parametres import Parametres
from .trajectoire_annuelle import lignes

REGISTRE = Path(__file__).resolve().parent.parent / "parametres" / "registre_lois.yaml"


def mesures() -> list[dict]:
    """Le registre complet : entrées du fichier registre_lois.yaml, puis une entrée par économie datée."""
    out = list(yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))["mesures"])
    for m in registre_economies():
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
    sc = calculer(p)[scenario]
    reg = lignes(p)
    out = {}
    for t in ANNEES:
        statique = sum(reg.effet_sur_solde(k, t) for k in reg.lignes)
        canaux = {k: v for k, v in sc.detail["canaux"][t].items() if k != "clause"}
        clause = sc.clause[t]
        pib = sc.detail["pib_reference"][t] + sc.pib_effet[t]
        out[t] = {"statique": statique, "economie": sum(canaux.values()), "canaux": canaux,
                  "dette_interets": -sc.charge_dette[t], "solde_avant_clause": sc.solde_public[t] - clause,
                  "deficit_avant_clause": (sc.detail["clause"][t]["avant"] if "clause" in sc.detail else -sc.maastricht[t]) * 100,
                  "pib": pib, "chomage": sc.detail["chomage"][t] * 100, "emplois": sc.emplois[t]}
    return out


def attribuer(p: Parametres | None = None, selection: list[str] | None = None) -> dict:
    p = (p or Parametres()).avec({"clause.active": False})
    base = _etat(p)
    resultats = []
    for m in mesures():
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
        for m in mesures():
            if "economie" in m:
                eco.add(m["economie"])
            else:
                modifs.update(m["neutraliser"])
        v = _etat(p.avec(modifs, mesures_desactivees=eco))
        ensemble = {t: {k: base[t][k] - v[t][k] for k in ("statique", "economie", "dette_interets", "solde_avant_clause",
                                                          "deficit_avant_clause", "chomage", "emplois")} for t in ANNEES}
    return {"base": base, "mesures": resultats, "ensemble": ensemble}
