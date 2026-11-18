"""Des choix des entreprises aux revenus des ménages (roadmap du comparateur, phase 4.3, 18/11/2026).

Architecture visée : ce qu'une mesure prend ou laisse aux entreprises ne s'arrête pas aux entreprises. Il arrive aux
ménages en salaires, en prix et en revenus des actionnaires (dividendes, plus-values). Premier lot, sans effet sur le
solde (entreprises.incidence_menages.retour_budget : false) :

1. **Montant laissé aux entreprises**, par programme et par année (Md€, + = les entreprises paient moins) : mesures
   de recettes à l'instrument capital_entreprises (IS, impôts de production), avec leur retour d'IS des charges
   (ligne « impôt sur les sociétés : charges déductibles » de la même mesure). Le coût du travail (instrument
   cout_travail) n'y est pas : son effet passe par l'emploi (moteur/offre.py), et sa répercussion sur les salaires
   à long terme n'est pas modélisée (entreprises.retour_is_charges).
2. **Partage** (entreprises.incidence_menages) : part salaires, part prix, le reste aux actionnaires.
3. **Répartition par décile** de revenu initial par unité de consommation (population synthétique : salaires,
   revenus d'indépendant, allocations de chômage, pensions, revenus du capital ; échelle de l'OCDE modifiée) :
   salaires au prorata des salaires du privé, actionnaires au prorata des dividendes et des plus-values, prix au
   prorata du revenu initial (faute de consommation dans la population).

Les déciles ne sont pas ceux de niveau de vie de la microsimulation (qui demandent OpenFisca) : ce sont des déciles de
revenu avant impôts et prestations, lisibles sans OpenFisca. À rapprocher des déciles de niveau de vie quand la
micro sera relancée.

    from moteur import incidence_entreprises as ie
    ie.montant_entreprises(p, prog, "prudent")      # {année: Md€}
    ie.par_decile(p, prog, "prudent", 2032)          # parts et euros par UC, décile par décile
"""
from __future__ import annotations

import numpy as np

from .parametres import Parametres

INSTRUMENT = "capital_entreprises"
LIGNE_IS = "impôt sur les sociétés : charges déductibles"


def mesures_entreprises(prog, p: Parametres, s: str) -> list:
    """Mesures du programme qui changent ce que paient les entreprises (et leur retour d'IS)."""
    ms = prog.mesures(p)[s]
    ids = {m.nom.partition(" — ")[0] for m in ms if m.instrument == INSTRUMENT and m.poste == "recettes"}
    return [m for m in ms if m.poste == "recettes" and m.nature == "mesure"
            and (m.instrument == INSTRUMENT
                 or (m.nom.partition(" — ")[0] in ids and m.nom.partition(" — ")[2].startswith(LIGNE_IS)))]


def montant_entreprises(p: Parametres, prog, s: str) -> dict[int, float]:
    """Md€ laissés aux entreprises chaque année (+ : elles paient moins d'impôts)."""
    out: dict[int, float] = {}
    for m in mesures_entreprises(prog, p, s):
        for t, v in m.valeurs.items():
            out[t] = out.get(t, 0.0) - v
    return out


def partage(p: Parametres, montant: float) -> dict[str, float]:
    x = p.val("entreprises.incidence_menages")
    return {"salaires": x["salaires"] * montant, "prix": x["prix"] * montant,
            "actionnaires": (1 - x["salaires"] - x["prix"]) * montant}


def _population():
    """Ménages de la population synthétique : poids, personnes, UC, revenu initial, salaires du privé, capital."""
    from outils.openfisca_population import lire
    L = lire()
    men = np.array([l["menage"] for l in L])
    _, idx = np.unique(men, return_inverse=True)
    n = idx.max() + 1
    poids = np.zeros(n)
    poids[idx] = [l["poids"] for l in L]

    def somme(f):
        return np.bincount(idx, weights=np.array([f(l) for l in L], float), minlength=n)
    personnes = somme(lambda l: 1.0)
    adultes = somme(lambda l: 1.0 if l["age"] >= 14 else 0.0)
    uc = 1 + 0.5 * np.maximum(adultes - 1, 0) + 0.3 * (personnes - adultes)
    sal_prive = somme(lambda l: l["salaire_brut"] if l["statut"] == "salarie_prive" else 0.0)
    capital = somme(lambda l: l["dividendes"] + l.get("plus_values", 0.0))
    revenu = somme(lambda l: l["salaire_brut"] + l["revenu_independant"] + l["chomage_brut"] + l["pension_brute"]
                   + l["dividendes"] + l["revenus_fonciers"] + l.get("plus_values", 0.0))
    return {"poids": poids, "personnes": personnes, "uc": uc, "revenu": revenu, "salaires": sal_prive, "capital": capital}


def deciles_population(pop: dict | None = None) -> np.ndarray:
    """Décile (1 à 10) de chaque ménage, selon le revenu initial par UC, pondéré par les personnes (Insee)."""
    pop = pop or _population()
    r = pop["revenu"] / pop["uc"]
    o = np.argsort(r)
    w = (pop["poids"] * pop["personnes"])[o]
    rang = np.cumsum(w) / w.sum()
    d = np.empty(len(r), int)
    d[o] = np.minimum(10, np.floor(rang * 10 - 1e-12).astype(int) + 1)
    return d


def par_decile(p: Parametres, prog, s: str, t: int, pop: dict | None = None) -> list[dict]:
    """Par décile : Md€ reçus (salaires, prix, actionnaires), euros par UC et par an, part du revenu initial."""
    pop = pop or _population()
    d = deciles_population(pop)
    m = montant_entreprises(p, prog, s).get(t, 0.0)
    parts = partage(p, m)
    w = pop["poids"]
    cles = {"salaires": pop["salaires"], "actionnaires": pop["capital"], "prix": pop["revenu"]}
    tot = {k: (w * v).sum() for k, v in cles.items()}
    out = []
    for k in range(1, 11):
        sel = d == k
        recu = {c: parts[c] * (w[sel] * cles[c][sel]).sum() / tot[c] if tot[c] else 0.0 for c in cles}
        total = sum(recu.values())
        uc = (w[sel] * pop["uc"][sel]).sum()
        rev = (w[sel] * pop["revenu"][sel]).sum()
        out.append({"decile": k, **{f"{c}_md": recu[c] for c in cles}, "total_md": total,
                    "eur_par_uc": total * 1e9 / uc if uc else 0.0,
                    "part_revenu_pct": total * 1e9 / rev * 100 if rev else 0.0})
    return out
