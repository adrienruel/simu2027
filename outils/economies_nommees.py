"""Économies nommées et précédents historiques, par programme et par domaine (analyse indépendante, point M4 ;
décision d'Adrien du 27/11/2026 : afficher l'indicateur, sans changer les chiffres).

Les économies non détaillées d'un programme sont plafonnées, domaine par domaine, par ce que les gouvernements passés
ont obtenu en un quinquennat (`enveloppe_economies.domaines`, capacité par scénario). Les économies nommées, elles,
sont chiffrées mesure par mesure, sans plafond. L'indicateur rapporte les secondes à la capacité entière du domaine
(sans l'intensité propre au programme) : au-delà de 1, le programme nomme plus d'économies que les précédents n'en
ont jamais faites dans ce domaine.

Économies nommées : dépenses en moins à l'année pleine (2032, fin du quinquennat), mesures du programme sur les postes
du domaine, hors effets économiques, hors économies non détaillées et hors prestations en moins induites par une
hausse du salaire net (SMIC, CSG, cotisations). Un poste partagé entre domaines (prestations :
pauvreté, famille, logement) compte au prorata des poids de `enveloppe_economies.domaines`. État et opérateurs
partagent le poste etat_missions : ils sont réunis. Écrit sorties/comparaison_economies_nommees.csv.
"""
from __future__ import annotations

import csv
from pathlib import Path

from moteur import noyau
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "sorties" / "comparaison_economies_nommees.csv"
ANNEE = 2032
SCENARIOS = {"prudent": "Prudent", "median": "Médian"}
NON_DETAILLEES = "Économies annoncées non détaillées"


def induite(nom: str) -> bool:
    """Prestations en moins induites par une autre mesure (salaire net plus élevé : SMIC, CSG, cotisations), pas une
    économie nommée."""
    n = nom.lower()
    return "en moins" in n and ("prime d'activité" in n or "aides en moins" in n)


def groupes(p: Parametres) -> dict[str, dict]:
    """Domaines réunis par postes communs : {libellé : {postes: {poste: poids}, capacite: {scénario: Md€}}}."""
    dom = p.val("enveloppe_economies.domaines")
    out: dict[tuple, dict] = {}
    for d in dom.values():
        cle = tuple(sorted(d["postes"]))
        g = out.setdefault(cle, {"libelles": [], "postes": dict(d["postes"]), "capacite": {}})
        g["libelles"].append(d["libelle"])
        for s, v in d["capacite"].items():
            g["capacite"][s] = g["capacite"].get(s, 0.0) + v
    return {" ; ".join(g["libelles"]): g for g in out.values()}


def lignes() -> list[dict]:
    p = Parametres()
    gr = groupes(p)
    out = []
    for nom in noyau.programmes_disponibles()[1:]:
        prog = noyau.charger(nom)
        lib = getattr(prog, "libelle", nom)
        tout = prog.mesures(p)
        for s, sc in SCENARIOS.items():
            par_poste: dict[str, float] = {}
            for m in tout.get(s, []):
                if m.nature in ("effet_macro", "physique") or m.poste in ("recettes", "participations"):
                    continue
                if m.nom.startswith(NON_DETAILLEES) or induite(m.nom):
                    continue
                par_poste[m.poste] = par_poste.get(m.poste, 0.0) - min(0.0, m.valeurs.get(ANNEE, 0.0))
            for dom, g in gr.items():
                nommees = sum(par_poste.get(x, 0.0) * w for x, w in g["postes"].items())
                cap = g["capacite"][s]
                out.append({"cle": f"{lib}|{sc}|{dom}", "programme": lib, "scenario": sc, "domaine": dom,
                            "nommees_md": round(nommees, 2), "capacite_md": round(cap, 2),
                            "ratio": round(nommees / cap, 2) if cap else ""})
    return out


def main() -> None:
    rows = lignes()
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from outils import trace
    trace.enregistrer(SORTIE.name, script="outils.economies_nommees")


if __name__ == "__main__":
    main()
