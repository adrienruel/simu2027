"""Profils des travailleurs : ingénieurs en activité par année, statu quo et programmes qui déclarent le canal
« formation_superieure » (phase Q, moteur/qualifications.py). Écrit sorties/profils_formation.csv (par année) et
sorties/profils_formation_ages.csv (par âge, quelques années).

    python -m outils.profils_formation
"""
from __future__ import annotations

import csv
from pathlib import Path

from moteur import canaux_declares, noyau, qualifications
from moteur import statu_quo as sq
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
SORTIES = RACINE / "sorties"
ANS_AGES = (2029, 2037, 2050, 2073)
LIB = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}


def programmes_concernes() -> list[str]:
    out = []
    for nom in noyau.programmes_disponibles():
        if nom == "statu_quo":
            continue
        if "formation_superieure" in canaux_declares.declares(noyau.charger(nom)):
            out.append(nom)
    return out


def calcul() -> tuple[list[dict], list[dict]]:
    lignes, ages = [], []
    p0 = Parametres()
    for s in sq.SCENARIOS:
        for t, x in qualifications.profils(p0, s, None).items():
            lignes.append({"programme": "Statu quo", "scenario": LIB[s], "annee": t, **{k: round(v, 4) for k, v in x.items()}})
        st = qualifications.stock_statu_quo(p0, s)
        for t in ANS_AGES:
            for a, v in st[t].items():
                ages.append({"programme": "Statu quo", "scenario": LIB[s], "annee": t, "age": a,
                             "ingenieurs_statu_quo": round(v), "en_plus_postes_ingenieur": 0, "en_plus_declasses": 0})
    for nom in programmes_concernes():
        prog = noyau.charger(nom)
        p = Parametres(programme=nom)
        decl = canaux_declares.declares(prog)["formation_superieure"]
        for s in sq.SCENARIOS:
            for t, x in qualifications.profils(p, s, decl).items():
                lignes.append({"programme": prog.libelle, "scenario": LIB[s], "annee": t, **{k: round(v, 4) for k, v in x.items()}})
            st, par_age = qualifications.stock_statu_quo(p, s), qualifications.par_age(p, s, decl, ANS_AGES)
            for t in ANS_AGES:
                for a, v in st[t].items():
                    pa = par_age[t].get(a, {"absorbes": 0.0, "declasses": 0.0})
                    ages.append({"programme": prog.libelle, "scenario": LIB[s], "annee": t, "age": a,
                                 "ingenieurs_statu_quo": round(v), "en_plus_postes_ingenieur": round(pa["absorbes"]),
                                 "en_plus_declasses": round(pa["declasses"])})
    return lignes, ages


def ecrire(lignes: list[dict], nom: str) -> None:
    with (SORTIES / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


if __name__ == "__main__":
    lignes, ages = calcul()
    ecrire(lignes, "profils_formation.csv")
    ecrire(ages, "profils_formation_ages.csv")
    from outils import trace
    trace.enregistrer(["profils_formation.csv", "profils_formation_ages.csv"], script="outils.profils_formation")
    print("Écrit : sorties/profils_formation.csv, profils_formation_ages.csv")
