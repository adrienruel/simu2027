"""Sources vérifiables (phase 3.4 de la roadmap, 16/11/2026) : paramètres au statut SOURCE classés par poids.

Pour chaque paramètre sourcé (communs sur le statu quo, propres à un programme sur ce programme) : +10 %, sous-champ
par sous-champ, et écart de déficit (points de PIB) en 2037 et 2050 au prudent (même méthode que
outils/c1_inventaire.py). Le classement dit quelles sources rendre vérifiables d'abord (champs `url` et `page`).
Écrit sorties/sources_poids.csv.

    python -m outils.sources_poids
"""
from __future__ import annotations

import csv

from moteur import noyau
from moteur.parametres import RACINE, Parametres
from outils.c1_inventaire import inventaire


def calcul() -> list[dict]:
    lignes = []
    for nom in [None] + noyau.programmes_disponibles()[1:]:
        p = Parametres(programme=nom)
        par_cle = {}
        for r in inventaire(nom, statut="SOURCE"):
            cle = r["cle"].split("/")[0]
            if "erreur" in r:
                continue
            # poids d'un paramètre : son sous-champ qui pèse le plus
            if cle not in par_cle or abs(r["deficit_2037"]) > abs(par_cle[cle]["deficit_2037"]):
                par_cle[cle] = r
        for cle, r in par_cle.items():
            x = p[cle]
            lignes.append({"cle": cle, "dossier": nom or "commun", "sous_champ": r["cle"],
                           "deficit_2037": round(r["deficit_2037"], 4), "deficit_2050": round(r["deficit_2050"], 4),
                           "url": x.url or "", "page": x.page or "", "source": (x.source or "")[:200]})
    lignes.sort(key=lambda r: -abs(r["deficit_2037"]))
    for i, r in enumerate(lignes, 1):
        r["rang"] = i
    return lignes


def main() -> None:
    lignes = calcul()
    f = RACINE / "sorties" / "sources_poids.csv"
    champs = ["rang", "cle", "dossier", "sous_champ", "deficit_2037", "deficit_2050", "url", "page", "source"]
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)
    from outils import trace
    trace.enregistrer(f, script="outils.sources_poids")
    n = sum(1 for r in lignes[:20] if r["url"] and r["page"])
    print(f"Écrit : {f} ({len(lignes)} paramètres ; vingt premiers vérifiables : {n}/20)")


if __name__ == "__main__":
    main()
