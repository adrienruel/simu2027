"""Table d'offre de travail d'Écologie de droite (14 novembre 2026), au format des tables d'OpenFisca-France
(outils/openfisca_offre.py), pour que l'emploi du programme passe par le canal d'offre commun (moteur/offre.py),
cellule par cellule, comme les réformes du travail des autres programmes.

OpenFisca ne sait pas calculer le système du programme (impôt unique sur le coût employeur, revenu universel
individuel qui remplace le RSA, la prime d'activité, les aides au logement et les allocations familiales) : la table
est calculée par le moteur du programme (moteur/menages_types.nouveau), sur la même grille de salaires bruts et les
mêmes cas types que la table du système actuel :
- le coût employeur d'un salaire brut est celui d'aujourd'hui (table actuelle), moins la baisse ciblée du coût du
  travail du programme (emploi.baisse_cout_travail, plafonnée à l'impôt dû) ;
- personne seule sans enfant ; couples : second apporteur au salaire de la grille, conjoint à 18 000, 30 000 ou
  55 000 € brut, zéro, un ou deux enfants (8 et 11 ans) ;
- revenu disponible hors épargne obligatoire (un patrimoine bloqué jusqu'à la retraite, comme dans les ménages
  types) ; le loyer n'est retiré dans aucun des deux systèmes.

    python -m outils.table_offre_ecologie_de_droite
"""
from __future__ import annotations

import csv
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "parametres" / "donnees"


def cout_programme(cout_actuel: float, p) -> float:
    """Coût employeur dans le programme pour un salaire brut donné : coût actuel moins la baisse ciblée."""
    from moteur.emploi import cout_smic_annuel
    from moteur.impot_unique import impot
    b = p.val("emploi.baisse_cout_travail")
    x = cout_actuel / cout_smic_annuel(p)
    taux = (b["taux"] if x <= b["plein_jusqu_a"] else
            (b["taux"] * (b["nulle_a"] - x) / (b["nulle_a"] - b["plein_jusqu_a"]) if x < b["nulle_a"] else 0.0))
    return cout_actuel - min(taux * cout_actuel, impot(cout_actuel, p))


def calculer(p=None) -> list[dict]:
    from moteur.menages_types import nouveau
    from moteur.offre import _table_offre
    from moteur.parametres import Parametres
    from moteur.systeme_actuel import _interp
    from outils.openfisca_offre import CONJOINTS, ENFANTS, colonne_couple
    p = p or Parametres()
    a = _table_offre("actuel")

    def cout(brut):
        return cout_programme(_interp(brut, a["brut"], a["cout_du_travail"]), p) if brut > 0 else 0.0

    def dispo(adultes, enfants):
        m = {"adultes": [c if c > 0 else "retraite:0" for c in adultes], "enfants": [8, 11][:enfants]}
        return nouveau(m, p)

    lignes = []
    for brut in a["brut"]:
        c = cout(brut)
        seul = dispo([c], 0)
        l = {"brut": brut, "cout_du_travail": round(c, 2),
             "net_apres_ir_seul": round(seul["cout_employeur"] - seul["impot_unique"] - seul["impot_local"], 2),
             "disponible_seul": round(seul["revenu_disponible"], 2), "ir_seul": round(seul["impot_unique"], 2)}
        for conj in CONJOINTS:
            for e in ENFANTS:
                r = dispo([cout(conj), c], e)
                col = colonne_couple(conj, e)
                l[f"disponible_{col}"] = round(r["revenu_disponible"], 2)
                l[f"ir_{col}"] = round(r["impot_unique"], 2)
        lignes.append(l)
    return lignes


def ecrire() -> Path:
    lignes = calculer()
    f = DONNEES / "openfisca_offre_ecologie_de_droite_2026.csv"
    with f.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    return f


if __name__ == "__main__":
    print(ecrire())
