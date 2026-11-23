"""Roadmap 5.1 (22/11/2026) : variantes de finances publiques de FR-BDF rejouées dans le noyau, hors calage.

Le bouclage de simu2027 est calé sur Mésange : la comparaison à Mésange (outils/banc_essai.py) contrôle le codage,
pas le modèle. FR-BDF, le modèle de la Banque de France, n'a servi à aucun calage : c'est une validation.

Source : Banque de France, document de travail n° 1045 (mai 2026), « An Update of FR-BDF Basic Model Elasticities
and the FR-BMEs Model » (Aldama, Carroy, Ducoudré et al.), variantes de 1 point de PIB ex ante, permanentes :
PIB en volume (%), emploi total (%) et solde public (point de PIB) aux années 1, 2, 3, 5 et 10.
https://www.banque-france.fr/system/files/2026-05/WP1045.pdf

Chocs rejoués (permanents à partir de 2031, comme le banc d'essai ; scénarios prudent et médian) :
- consommation intermédiaire publique +1 point de PIB (bloc etat_missions) ;
- prestations sociales hors chômage +1 point (bloc pauvrete, sans effet d'offre) ;
- impôts directs des ménages +1 point (prélèvements du travail, incidence ir) ;
- cotisations employeurs +1 point (coût du travail, élasticité de Mésange) ;
- TVA +1 point (instrument consommation).
Le solde comparé est le solde primaire de simu2027 (le solde public de FR-BDF compte aussi les intérêts : écart
de quelques centièmes à 10 ans).

    python -m outils.variantes_frbdf        → sorties/variantes_frbdf.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

from moteur import noyau
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres
from moteur.programme_simple import ProgrammeSimple

RACINE = Path(__file__).resolve().parents[1]
T0 = 2031
ANS = {"A1": 0, "A2": 1, "A3": 2, "A5": 4, "A10": 9}

# FR-BDF (WP 1045, 2026) : (PIB %, emploi %, solde public pt de PIB) par année ; None : non publié
FRBDF = {
    "consommation_publique": {"A1": (0.94, 0.17, -0.63), "A2": (0.89, 0.30, -0.60), "A3": (0.79, 0.33, -0.61),
                              "A5": (0.61, 0.28, -0.67), "A10": (0.47, 0.26, -0.73)},
    "prestations": {"A1": (0.29, 0.05, -0.75), "A2": (0.34, 0.10, -0.72), "A3": (0.37, 0.13, -0.70),
                    "A5": (0.39, 0.16, -0.68), "A10": (0.36, 0.18, -0.67)},
    "impots_directs": {"A1": (-0.10, -0.01, 0.97), "A2": (-0.29, -0.07, 0.91), "A3": (-0.35, -0.11, 0.88),
                       "A5": (-0.38, -0.15, 0.88), "A10": (-0.36, -0.18, 0.93)},
    "cotisations_employeurs": {"A1": (-0.02, -0.04, 0.91), "A2": (-0.13, -0.21, 0.84), "A3": (-0.31, -0.39, 0.74),
                               "A5": (-0.62, -0.58, 0.59), "A10": (-0.69, -0.51, 0.50)},
    "tva": {"A1": (-0.16, -0.03, 0.76), "A2": (-0.27, -0.09, 0.74), "A3": (-0.34, -0.14, 0.73),
            "A5": (-0.46, -0.21, 0.69), "A10": (-0.53, -0.23, 0.68)},
}


class Variante(ProgrammeSimple):
    nom = "variante"

    def __init__(self, choc: str) -> None:
        self.pt = Parametres()
        self._cache = {}
        self.choc = choc
        self.libelle = f"FR-BDF : {choc}"

    def mesures_calculees(self, p, s, idx):
        y = sq.pib(p, s)
        un = {2027: 0.0, 2028: 0.0, **{t: 0.01 * y[t] if t >= T0 else 0.0 for t in ANNEES}}
        c = self.choc
        if c == "consommation_publique":
            return [Mesure("Variante — consommation publique +1 pt", "etat_missions", un)], {}
        if c == "prestations":
            return [Mesure("Variante — prestations +1 pt", "pauvrete", un)], {}
        # hausses d'impôt : montant positif au poste recettes (améliore le solde)
        if c == "impots_directs":
            return [Mesure("Variante — impôts directs +1 pt", "recettes", un, instrument="travail", incidence="ir")], {}
        if c == "cotisations_employeurs":
            return [Mesure("Variante — cotisations employeurs +1 pt", "recettes", un, instrument="cout_travail")], {}
        if c == "tva":
            return [Mesure("Variante — TVA +1 pt", "recettes", un, instrument="consommation")], {}
        raise ValueError(c)


def calcul(scenarios=("prudent", "median")) -> dict:
    p = Parametres()
    r0 = noyau.simuler(p, None, scenarios=list(scenarios))
    out = {}
    for c in FRBDF:
        r = noyau.simuler(p, Variante(c), scenarios=list(scenarios))
        out[c] = {}
        for s in scenarios:
            out[c][s] = {}
            for h, k in ANS.items():
                a, b = r[s][T0 + k], r0[s][T0 + k]
                out[c][s][h] = (100 * (a["pib"] / b["pib"] - 1), 100 * (a["emploi"] / b["emploi"] - 1),
                                100 * (a["solde_primaire"] / a["pib"] - b["solde_primaire"] / b["pib"]))
    return out


def ecrire(res: dict) -> Path:
    f = RACINE / "sorties" / "variantes_frbdf.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["choc", "modele", "annee", "pib_pct", "emploi_pct", "solde_pt_pib"])
        for c, par in res.items():
            for h, (y, e, b) in FRBDF[c].items():
                w.writerow([c, "FR-BDF", h, y, e, b])
            for s, d in par.items():
                for h, (y, e, b) in d.items():
                    w.writerow([c, f"simu2027 {s}", h, round(y, 3), round(e, 3), round(b, 3)])
    from outils import trace
    trace.enregistrer([f.name], script="outils.variantes_frbdf")
    return f


if __name__ == "__main__":
    res = calcul()
    print(ecrire(res))
    for c, par in res.items():
        print(c)
        for h in ANS:
            print(f"  {h}: FR-BDF {FRBDF[c][h]}  médian {tuple(round(x, 2) for x in par['median'][h])}"
                  f"  prudent {tuple(round(x, 2) for x in par['prudent'][h])}")
