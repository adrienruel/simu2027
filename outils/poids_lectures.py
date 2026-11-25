"""Poids des lectures de programme (roadmap du comparateur, chantier 2.4, 16/11/2026).

Chaque canal déclaré d'un programme (réformes de structure, logement, solde migratoire, IA, école, fraude) et chaque
lecture commune (capitalisation lue comme celle de Retailleau) repose sur une lecture d'une mesure floue. Pour en
montrer le poids, le programme est recalculé sans cette lecture, et l'on publie l'écart de solde primaire au statu
quo, en points de PIB, avec et sans elle (scénario prudent, 2032 et 2037). Écrit docs/lectures_poids.md et
sorties/comparaison_lectures.csv.

    python -m outils.poids_lectures
"""
from __future__ import annotations

import csv
import json

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import RACINE, Parametres

ANNEES = (2032, 2037)


def _sp(r, base, t):
    return (r["prudent"][t]["solde_primaire"] / r["prudent"][t]["pib"]
            - base["prudent"][t]["solde_primaire"] / base["prudent"][t]["pib"]) * 100


def lectures(prog) -> list[tuple[str, str]]:
    """(clé du paramètre, libellé) des lectures du programme."""
    out = []
    for cle in prog.pt.cles():
        if cle.startswith(f"{prog.nom}_canaux."):
            out.append((cle, "canal déclaré : " + cle.split(".", 1)[1].replace("_", " ")))
    for cle, par in prog.pt.items():
        if cle.startswith(f"{prog.nom}_mesures.") and isinstance(par.valeur, dict) and par.valeur.get("lecture_commune"):
            out.append((cle, "lecture commune : " + par.valeur["lecture_commune"]))
    return out


def main() -> list[dict]:
    p = Parametres()
    base = sq.simuler(p)
    lignes = []
    for nom in noyau.programmes_disponibles()[1:]:
        prog = noyau.charger(nom)
        r = noyau.simuler(p, prog, scenarios=("prudent",), contrefactuel=False)
        for cle, lib in lectures(prog):
            sans = noyau.charger(nom)
            c = prog.pt.avec()
            c.retirer(cle)
            sans.pt = c
            r2 = noyau.simuler(p, sans, scenarios=("prudent",), contrefactuel=False)
            par = prog.pt[cle]
            lignes.append({"programme": getattr(prog, "libelle", nom), "dossier": nom, "cle": cle, "lecture": lib,
                           "valeur": json.dumps(par.valeur, ensure_ascii=False)[:160],
                           **{f"ecart_sp_{t}": round(_sp(r, base, t), 3) for t in ANNEES},
                           **{f"sans_lecture_{t}": round(_sp(r2, base, t), 3) for t in ANNEES},
                           **{f"poids_{t}": round(_sp(r, base, t) - _sp(r2, base, t), 3) for t in ANNEES},
                           "statut": par.statut, "source": (par.source or "")[:200]})
    f = RACINE / "sorties" / "comparaison_lectures.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    from outils import trace
    trace.enregistrer(f, script="outils.poids_lectures")
    md = ["# Poids des lectures de programme (calculé le 16/11/2026, `python -m outils.poids_lectures`)", "",
          "Écart de solde primaire au statu quo en 2037, scénario prudent, en points de PIB (+ = meilleur) : avec la",
          "lecture, sans elle, et son poids. Une lecture est la traduction d'une mesure floue en paramètre du modèle",
          "(barème commun) ; celles qui pèsent le plus sont à faire valider en priorité.", "",
          "| Programme | Lecture | Avec | Sans | Poids 2037 | Statut |", "|---|---|---|---|---|---|"]
    for l in sorted(lignes, key=lambda x: -abs(x["poids_2037"])):
        md.append(f"| {l['programme']} | {l['lecture']} | {l['ecart_sp_2037']:+.2f} | {l['sans_lecture_2037']:+.2f} | "
                  f"{l['poids_2037']:+.2f} | {l['statut']} |")
    (RACINE / "docs" / "lectures_poids.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return lignes


if __name__ == "__main__":
    main()
