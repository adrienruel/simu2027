"""Banc d'essai du noyau : les chocs standard des modèles publiés, rejoués dans simu2027 (21/11/2026).

Question d'Adrien (21/11/2026) : le modèle est-il trop rigide ? On ne règle rien ici : on soumet le noyau aux chocs
dont les réponses sont publiées pour d'autres modèles, et on compare.

Chocs (permanents, à partir de 2031 = t ; même normalisation que les variantes publiées). Pas en 2029 : les
dépenses du statu quo sont indexées en rapport à 2029 (indice 1), si bien qu'un gain de productivité dès 2029
échapperait à toute indexation (constat du 21/11/2026 : dividende de 40 % au lieu de 9 %).
- dépense : dépense publique +1 point de PIB (bloc etat_missions) ;
- tva : TVA −1 point de PIB (instrument consommation) ;
- productivite : productivité du travail +1 % (salaires du statu quo, comme statu_quo.dividende_productivite) ;
- age : âge d'ouverture des droits de 64 à 65 ans (bibliotheque.report_age_legal_detail, 3 mois par génération
  à partir de 1966, comme le report de Bertrand ; toute l'économie gardée, puis la part gardée de Bertrand) ;
- productivite_cor : croissance de la productivité +0,3 point par an à partir de 2029 (variante haute du COR, 1 %
  au lieu de 0,7 %), dépenses de retraite en part de PIB.

Références :
- OFCE, document de travail 2026-9, « Comparaison des propriétés des modèles macroéconomiques français ThreeME et
  Mésange » : PIB, emploi et solde primaire à t, t+1, t+4, t+9, t+29 et long terme, pour la dépense, la productivité
  et la TVA (https://www.ofce.fr/wp/2026/9/OFCEWP2026-9.pdf) ;
- DG Trésor pour le COR (mars 2026), âge d'ouverture des droits de 64 à 65 ans : solde public +0,4 point de PIB à
  5 ans, +0,5 à 20 ans ;
- COR, rapport annuel 2026 (partie 2, chap. 5) : productivité 1 % au lieu de 0,7 % : dépenses de retraite −0,8 point
  de PIB et solde du système +0,7 point en 2070 ;
- Commission européenne (Mourre, Poissonnier et Lausegger, 2019) : semi-élasticité du solde à l'écart de production,
  0,63 pour la France (choc conjoncturel, pour mémoire : aucun choc ici n'est conjoncturel pur).

    python -m outils.banc_essai        → sorties/banc_essai.csv, docs/banc_essai.md (tableaux)
"""
from __future__ import annotations

import csv
from pathlib import Path

from moteur import bibliotheque as bib
from moteur import noyau
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres
from moteur.programme_simple import ProgrammeSimple

RACINE = Path(__file__).resolve().parents[1]
T0 = 2031
T0_AGE = 2030  # la génération 1966, première concernée, a 64 ans en 2030
HORIZONS = {"t": 0, "t+1": 1, "t+4": 4, "t+9": 9, "t+19": 19, "t+29": 29, "LT (t+42)": 42}
SCENARIOS = ("prudent", "median")

# Références publiées (OFCE WP 2026-9, tableaux des variantes) : {choc: {horizon: (PIB %, emploi milliers, solde primaire pt)}}
REF = {
    "depense": {
        "Mésange": {"t": (0.76, 33, -0.53), "t+1": (1.01, 88, -0.34), "t+4": (0.88, 48, -0.53), "t+9": (0.54, -8, -0.68), "t+29": (0.27, -31, -0.79), "LT (t+42)": (0.17, -42, -0.85)},
        "ThreeME": {"t": (0.68, 55, -0.72), "t+1": (0.79, 124, -0.57), "t+4": (0.90, 195, -0.49), "t+9": (0.80, 142, -0.53), "t+29": (0.46, 73, -0.69), "LT (t+42)": (0.45, 83, -0.71)},
    },
    "productivite": {
        "Mésange": {"t": (0.04, -15, -0.04), "t+1": (0.16, -59, -0.10), "t+4": (0.43, -56, 0.00), "t+9": (0.61, -35, 0.05), "t+29": (0.82, -15, 0.14), "LT (t+42)": (0.89, -8, 0.18)},
        "ThreeME": {"t": (0.02, -8, -0.01), "t+1": (0.04, -109, -0.18), "t+4": (0.24, -133, -0.14), "t+9": (0.51, -50, -0.05), "t+29": (0.76, 0, 0.06), "LT (t+42)": (0.76, -1, 0.07)},
    },
    "tva": {  # baisse de la TVA de 1 point de PIB
        "Mésange": {"t": (0.30, 31, -0.80), "t+1": (0.65, 115, -0.37), "t+4": (0.81, 113, -0.37), "t+9": (0.78, 71, -0.44), "t+29": (0.71, 66, -0.46), "LT (t+42)": (0.70, 64, -0.47)},
        "ThreeME": {"t": (0.46, 35, -0.89), "t+1": (0.63, 98, -0.68), "t+4": (1.08, 237, -0.40), "t+9": (1.36, 296, -0.33), "t+29": (1.38, 303, -0.29), "LT (t+42)": (1.38, 343, -0.29)},
    },
    "age": {"DG Trésor (COR, 2026)": {"t+4": (None, None, 0.4), "t+19": (None, None, 0.5)}},
    "age (part gardée de Bertrand)": {"DG Trésor (COR, 2026)": {"t+4": (None, None, 0.4), "t+19": (None, None, 0.5)}},
}


class Choc(ProgrammeSimple):
    """Programme fictif : hypothèses communes seules, une mesure de choc."""
    nom = "banc"

    def __init__(self, choc: str, part_gardee: float | None = None) -> None:
        self.pt = Parametres()
        self._cache = {}
        self.choc = choc
        self.part_gardee = part_gardee
        self.libelle = f"Banc : {choc}"

    def mesures_calculees(self, p, s, idx):
        y = sq.pib(p, s)
        zero = {2027: 0.0, 2028: 0.0}
        un = {t: 0.01 * y[t] if t >= T0 else 0.0 for t in ANNEES}
        if self.choc == "depense":
            return [Mesure("Banc — dépense publique +1 point de PIB", "etat_missions", {**zero, **un})], {}
        if self.choc == "tva":
            return [Mesure("Banc — TVA −1 point de PIB", "recettes", {**zero, **{t: -v for t, v in un.items()}},
                           instrument="consommation")], {}
        if self.choc == "age":
            det = bib.report_age_legal_detail(p, s, 65, 1966, 0.25)
            k = 1.0 if self.part_gardee is None else self.part_gardee
            self.non_retraites = getattr(self, "non_retraites", {})
            self.non_retraites[(id(p), s)] = {"serie": {t: k * v for t, v in det["non_retraites"].items()}, "baisse": False}
            serie = {**zero, **{t: -k * det["pensions"][t] for t in ANNEES}}
            taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
            return [Mesure("Banc — âge d'ouverture des droits porté à 65 ans", "retraites", serie),
                    Mesure("Banc — prélèvements sur les pensions en moins", "recettes", {t: taux_prel * v for t, v in serie.items()})], {}
        raise ValueError(self.choc)


def _ecarts(r, r0, s, t0=T0):
    out = {}
    for h, k in HORIZONS.items():
        t = t0 + k
        if t not in r[s]:
            continue
        a, b = r[s][t], r0[s][t]
        out[h] = (100 * (a["pib"] / b["pib"] - 1), (a["emploi"] - b["emploi"]) / 1e3,
                  100 * (a["solde_primaire"] / a["pib"] - b["solde_primaire"] / b["pib"]))
    return out


def _productivite(p, choc):
    q = p.avec({})
    q._choc_productivite = choc
    return q


def calcul() -> dict:
    p = Parametres()
    r0 = noyau.simuler(p, None, scenarios=list(SCENARIOS))
    res = {}
    for choc in ("depense", "tva"):
        res[choc] = {s: _ecarts(noyau.simuler(p, Choc(choc), scenarios=list(SCENARIOS)), r0, s) for s in SCENARIOS}
    res["age"] = {s: _ecarts(noyau.simuler(p, Choc("age"), scenarios=list(SCENARIOS)), r0, s, T0_AGE) for s in SCENARIOS}
    k_ber = Parametres(programme="bertrand").val("bertrand_retraites.part_economie_gardee", "prudent")
    res["age (part gardée de Bertrand)"] = {s: _ecarts(noyau.simuler(p, Choc("age", k_ber), scenarios=list(SCENARIOS)), r0, s, T0_AGE)
                                           for s in SCENARIOS}
    q = _productivite(p, {t: 0.01 for t in range(T0, 2074)})
    res["productivite"] = {s: _ecarts(noyau.simuler(q, None, scenarios=list(SCENARIOS)), r0, s) for s in SCENARIOS}
    # variante haute du COR : +0,3 point de croissance de la productivité par an (à partir de T0)
    q = _productivite(p, {t: (1.003 ** (t - T0 + 1) - 1) for t in range(T0, 2074)})
    rc = noyau.simuler(q, None, scenarios=list(SCENARIOS))
    res["productivite_cor"] = {s: {t: (rc[s][t]["retraites_pib"] - r0[s][t]["retraites_pib"],
                                       100 * (rc[s][t]["solde_primaire"] / rc[s][t]["pib"] - r0[s][t]["solde_primaire"] / r0[s][t]["pib"]),
                                       100 * (rc[s][t]["pib"] / r0[s][t]["pib"] - 1))
                                   for t in (2037, 2050, 2070)} for s in SCENARIOS}
    # dividende de productivité du statu quo (part d'un euro de PIB en plus gardée au solde)
    res["dividende"] = {s: {t: sq.dividende_productivite(p, s)[t] for t in (2030, 2033, 2038, 2050, 2073)} for s in SCENARIOS}
    # où part le PIB en plus du choc de productivité : recettes et blocs de dépense, par euro de PIB en plus
    rp = noyau.simuler(_productivite(p, {t: 0.01 for t in range(T0, 2074)}), None, scenarios=["median"])["median"]
    b = r0["median"]
    res["productivite_postes"] = {}
    for k in (0, 9, 29, 42):
        t = T0 + k
        dy = rp[t]["pib"] - b[t]["pib"]
        x = {"recettes": (rp[t]["recettes"] - b[t]["recettes"]) / dy}
        x.update({f"bloc:{n}": (rp[t]["blocs"][n] - b[t]["blocs"][n]) / dy for n in b[t]["blocs"]})
        res["productivite_postes"][t] = x
    return res


def ecrire(res: dict) -> None:
    lignes = []
    for choc, par_s in res.items():
        if choc in ("productivite_cor", "dividende", "productivite_postes"):
            continue
        for s, x in par_s.items():
            for h, (dy, de, ds) in x.items():
                lignes.append({"choc": choc, "source": "simu2027", "scenario": s, "horizon": h,
                               "pib_pct": round(dy, 3), "emploi_milliers": round(de, 1), "solde_primaire_pt": round(ds, 3)})
        for src, x in REF.get(choc, {}).items():
            for h, (dy, de, ds) in x.items():
                lignes.append({"choc": choc, "source": src, "scenario": "", "horizon": h,
                               "pib_pct": dy, "emploi_milliers": de, "solde_primaire_pt": ds})
    with (RACINE / "sorties" / "banc_essai.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


if __name__ == "__main__":
    import json
    res = calcul()
    ecrire(res)
    def r3(v):
        return [round(x, 3) for x in v] if isinstance(v, tuple) else round(v, 3)
    print(json.dumps({k: {str(s): ({str(h): r3(v) for h, v in d.items()} if isinstance(d, dict) else r3(d)) for s, d in vs.items()}
                      for k, vs in res.items()}, ensure_ascii=False))
    from outils import trace
    trace.enregistrer(["banc_essai.csv"], script="outils.banc_essai")
