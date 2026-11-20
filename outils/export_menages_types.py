"""Ménages types de chaque programme, pour le comparateur (19/11/2026, vue « Ménages types »).

Les ménages types de parametres/menages_types.yaml (plus un jeune salarié au SMIC) sont calculés par OpenFisca-France
avec la législation de 2026, puis avec les mesures codées de chaque programme (programmes/micro_mesures.yaml) : les
mêmes réformes, les mêmes opérations « population » (SMIC, pensions) et les mêmes règles ajoutées après OpenFisca
(revenu d'incitation, plafond des aides, allocation unique, capitalisation…) que la microsimulation
(outils/openfisca_mesures.py), appliquées à ces seuls ménages.

Différences avec la population synthétique, toutes écrites dans la page :
- recours complet aux aides (RSA, prime d'activité, ASF, Aspa) : un ménage type touche ce à quoi il a droit ;
- ménages de nationalité française : les conditions de nationalité ou de résidence ne les touchent pas ;
- RSA limité dans le temps : aucun ménage type ne le perd (ancienneté non représentée) ;
- capitalisation obligatoire : seul le jeune salarié (entrant sur le marché du travail) cotise ;
- allocation unique : bornes de niveau de vie (3e décile, médiane) de la population synthétique ;
- pensions (gel, indexation) : effet de l'année 2032.
Ce que ne montre pas le calcul : emploi (un ménage qui trouve un travail), prix (TVA, énergie), services publics,
impôts sur le patrimoine et les successions, assurance chômage.

Écrit sorties/comparaison_menages_types.csv (revenu disponible, actuel et programme) et
sorties/comparaison_menages_types_mesures.csv (effet de chaque mesure codée seule).

    python -m outils.export_menages_types
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import yaml

from moteur import noyau
from moteur.menages_types import definitions, pensions_adultes
from moteur.parametres import Parametres
from outils import openfisca_mesures as om
from outils import openfisca_population as op

RACINE = Path(__file__).resolve().parents[1]
ANNEE = 2032
JEUNE = {"id": "jeune_smic", "libelle": "Jeune salarié au SMIC, 24 ans, entré sur le marché du travail", "adultes": ["smic"],
         "enfants": [], "age": 24}


def _cout_en_brut(cout: float, table: list[dict]) -> float:
    xs = [float(l["cout_du_travail"]) for l in table]
    ys = [float(l["brut"]) for l in table]
    if cout <= 0:
        return 0.0
    for i in range(1, len(xs)):
        if xs[i] >= cout:
            return ys[i - 1] + (ys[i] - ys[i - 1]) * (cout - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[-1] * cout / xs[-1]


def menages() -> list[dict]:
    return [JEUNE, *definitions()]


def lignes_types() -> list[dict]:
    """Ménages types au format de la population synthétique (poids 1, locataires du parc privé en zone 2)."""
    p = Parametres()
    with (RACINE / "parametres" / "donnees" / "openfisca_prive_2026.csv").open(encoding="utf-8") as f:
        table = sorted(csv.DictReader(f), key=lambda l: float(l["cout_du_travail"]))
    from outils.population_synthetique import smic_mensuel_brut
    smic_brut = smic_mensuel_brut()
    out = []
    for k, m in enumerate(menages()):
        n_ad, n_enf = len(m["adultes"]), len(m["enfants"])
        type_ = ("couple_avec_enfants" if n_enf else "couple_sans_enfant") if n_ad == 2 else ("monoparentale" if n_enf else "seul")
        loyer = 550 if n_ad == 1 and not n_enf else 800
        base = {"menage": k, "unite": k, "rattache": 0, "poids": 1.0, "type": type_, "groupe_independant": "",
                "revenu_independant": 0.0, "mois_travailles": 12, "debut_mois": 0, "chomage_brut": 0.0, "handicap": 0,
                "maries": 1 if n_ad == 2 else 0, "dividendes": 0.0, "revenus_fonciers": 0.0, "logement": "locataire_prive",
                "loyer_mensuel": float(loyer), "zone": "zone_2", "plus_values": 0.0, "apprenti": 0}
        for j, (a, pension) in enumerate(zip(m["adultes"], pensions_adultes(m))):
            # SMIC : brut à temps plein d'OpenFisca ; médian : coût employeur commun (profils.cout_median_annuel) ;
            # nombre : coût employeur annuel ; retraité ou 0 : sans salaire
            if a == "smic":
                brut = 12 * smic_brut
            elif a == "median":
                brut = _cout_en_brut(p.val("profils.cout_median_annuel"), table)
            elif pension > 0:
                brut = 0.0
            else:
                brut = _cout_en_brut(float(a), table)
            statut = "retraite" if pension > 0 else ("salarie_prive" if brut > 0 else "inactif")
            age = 70 if pension > 0 else m.get("age", 40)
            out.append({**base, "role": "ref" if j == 0 else "conjoint", "age": age, "statut": statut,
                        "salaire_brut": brut, "cout_employeur": 0.0, "pension_brute": pension})
        for age in m["enfants"]:
            out.append({**base, "role": "enfant", "age": age, "statut": "enfant", "salaire_brut": 0.0,
                        "cout_employeur": 0.0, "pension_brute": 0.0})
    return out


def bornes_population() -> dict:
    """3e décile et médiane du niveau de vie de la population synthétique (législation actuelle), comme
    openfisca_mesures.Base, pour l'allocation unique."""
    lg = op.lire()
    sim, s = op.simulation(lg)
    rd = sim.calculate("revenu_disponible", "2026")
    nv = rd / np.maximum(sim.calculate("unites_consommation", "2026"), 1e-9)
    wm = np.zeros(s["n_menages"])
    wm[s["menage"]] = np.array([l["poids"] for l in lg])
    w = wm * np.bincount(s["menage"], minlength=s["n_menages"])
    o = np.argsort(nv)
    cw = np.cumsum(w[o]) / w.sum()
    return {"d3": float(nv[o][np.searchsorted(cw, 0.3)]), "mediane": float(nv[o][np.searchsorted(cw, 0.5)])}


class Types(om.Base):
    """Ménages types : mêmes réformes et mêmes règles que la population, recours complet, nationalité française."""

    def __init__(self, bornes: dict):
        self.lignes = lignes_types()
        self.annee = ANNEE
        self.sim, self.s = op.simulation(self.lignes)
        s = self.s
        n_f = s["n_familles"]
        self.rec = Parametres().val("microsimulation.recours")
        self.u = {k: np.zeros(n_f) for k in ("rsa", "ppa", "asf", "aspa")}
        self.c = {k: 1e12 for k in ("rsa", "ppa", "asf", "aspa")}
        self.pp = np.ones(len(self.lignes))
        self.public = np.zeros(len(self.lignes), bool)
        self.wf = np.zeros(n_f)
        self.wf[s["famille"]] = 1.0
        self.wm = np.ones(s["n_menages"])
        self.pers_m = np.bincount(s["menage"], minlength=s["n_menages"])
        self.fam_men = np.zeros(n_f, int)
        self.fam_men[s["famille"]] = s["menage"]
        self.menage_etudiant = np.zeros(s["n_menages"], bool)
        enf = np.zeros(n_f, bool)
        for j in range(len(self.lignes)):
            enf[s["famille"][j]] |= s["role_famille"][j] == "enfant"
        self.fam_enf = enf
        self.exceptions_rsa = np.ones(n_f, bool)  # personne ne perd le RSA par la durée
        self._u_duree = np.ones(n_f)
        faux = np.zeros(n_f, bool)
        self.groupes = {"hors_ue": faux, "hors_ue_recents": faux, "etrangers": faux}
        self.bornes_nv = bornes
        self.emploi = False
        self.etat0 = self.etat(self.sim, [])

    def capitalisation(self, sim, x: dict) -> np.ndarray:
        """Seul le jeune salarié (entrant) cotise ; même taux, plafond et part employeur que la population."""
        c = Parametres(programme=x["programme"]).val(x["parametre"]) if x.get("programme") else Parametres().val(x["parametre"])
        if ANNEE < c["debut"]:
            return np.zeros(len(self.lignes))
        brut = np.array([l["salaire_brut"] if l["statut"] == "salarie_prive" else 0.0 for l in self.lignes])
        jeune = np.array([l["age"] <= 30 for l in self.lignes])
        return jeune * (1 - c["part_employeur"]) * np.minimum(c["taux"] * brut, 12 * c["plafond_mensuel"])


def noms_mesures() -> dict[tuple[str, str], str]:
    """Libellé de chaque mesure (« ID — nom »), lu dans l'export du comparateur."""
    out = {}
    with (RACINE / "sorties" / "comparaison_mesures.csv").open(encoding="utf-8") as f:
        for l in csv.DictReader(f):
            nom = l["mesure"]
            ident = nom.split(" — ")[0].strip()
            out.setdefault((l["programme"], ident), nom)
    return out


def main() -> None:
    sp = om.specs()
    t = Types(bornes_population())
    rd0 = t.etat0["rd"]
    defs = menages()
    publies = [n for n in noyau.programmes_disponibles() if n != "statu_quo"]
    noms = noms_mesures()
    lignes, detail = [], []
    for k, m in enumerate(defs):
        lignes.append({"cle": f"Statu quo|{m['id']}", "programme": "Statu quo", "menage": m["id"], "libelle": m["libelle"],
                       "ordre": k, "revenu_disponible_actuel": round(float(rd0[k]), 0), "revenu_disponible": round(float(rd0[k]), 0),
                       "ecart_an": 0.0, "ecart_mois": 0.0, "ecart_pct": 0.0, "mesures_codees": 0})
    for nom in publies:
        lib = getattr(noyau.charger(nom), "libelle", nom)
        mesures = sp.get(nom, {})
        toutes = [o for spec in mesures.values() for o in spec["operations"]]
        rd1 = t.reforme(toutes)["etat"]["rd"] if toutes else rd0
        for k, m in enumerate(defs):
            e = float(rd1[k] - rd0[k])
            lignes.append({"cle": f"{lib}|{m['id']}", "programme": lib, "menage": m["id"], "libelle": m["libelle"], "ordre": k,
                           "revenu_disponible_actuel": round(float(rd0[k]), 0), "revenu_disponible": round(float(rd1[k]), 0),
                           "ecart_an": round(e, 0), "ecart_mois": round(e / 12, 0),
                           "ecart_pct": round(e / float(rd0[k]) * 100, 2) if rd0[k] else 0.0, "mesures_codees": len(mesures)})
        for ident, spec in mesures.items():
            r = t.reforme(spec["operations"])["etat"]["rd"]
            mot = ident.split("/")[0]
            libm = noms.get((lib, ident)) or noms.get((lib, mot)) or ident
            for k, m in enumerate(defs):
                e = float(r[k] - rd0[k])
                if abs(e) >= 1:
                    detail.append({"cle": f"{lib}|{m['id']}|{ident}", "programme": lib, "menage": m["id"], "mesure": libm,
                                   "ecart_an": round(e, 0), "ecart_mois": round(e / 12, 0)})
        print(f"{lib:45s} {len(mesures):3d} mesures codées", flush=True)
    from outils import trace
    for fichier, rows in (("comparaison_menages_types.csv", lignes), ("comparaison_menages_types_mesures.csv", detail)):
        with (RACINE / "sorties" / fichier).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        trace.enregistrer(fichier, script="outils.export_menages_types")
    print("Écrit : sorties/comparaison_menages_types.csv, sorties/comparaison_menages_types_mesures.csv")


if __name__ == "__main__":
    main()
