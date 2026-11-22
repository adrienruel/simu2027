"""Roadmap 6.1 (22/11/2026) : quels paramètres incertains pèsent le plus ? Sensibilité un à un.

Pour chaque jeu de scénarios commun (moteur/incertitude.cibles), on place ce seul paramètre à son 10e puis à son
90e centile (z = ∓1,2816 : ses valeurs prudente et optimiste), tous les autres au médian, dans le scénario médian.
Poids = demi-écart du déficit 2037 du statu quo, et demi-écart moyen (en valeur absolue) de l'écart de solde primaire
2037 des programmes au statu quo. Le classement dit où des lois sourcées (au lieu des colonnes de scénario) changent
le plus la fourchette publiée.

    python -m outils.poids_incertitude        → sorties/poids_incertitude.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from moteur import incertitude as inc
from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
T = 2037


def _deficit_sq(p) -> float:
    return noyau.simuler(p, None, scenarios=("median",), contrefactuel=False)["median"][T]["deficit"]


def _ecart(p, nom: str, base) -> float:
    r = noyau.simuler(p, noyau.charger(nom), scenarios=("median",))
    return sq.ecart(r, base)["median"][T]["solde_primaire"]


def calcul(programmes: list[str] | None = None) -> list[dict]:
    p = Parametres()
    noms = programmes if programmes is not None else inc.programmes()
    out = []
    for cle, chemin in inc.cibles(p):
        nom = "/".join((cle,) + tuple(str(k) for k in chemin))
        q = {z: inc.tirer_z(p, lambda n, z=z: z if n == nom else 0.0, [(cle, chemin)]) for z in (-inc.Z90, inc.Z90)}
        d = {z: _deficit_sq(q[z]) for z in q}
        ligne = {"parametre": nom, "deficit_sq_2037": abs(d[inc.Z90] - d[-inc.Z90]) / 2}
        if noms:
            base = {z: {"median": noyau.simuler(q[z], None, scenarios=("median",))["median"]} for z in q}
            e = [abs(_ecart(q[inc.Z90], n, base[inc.Z90]) - _ecart(q[-inc.Z90], n, base[-inc.Z90])) / 2 for n in noms]
            ligne["ecart_moyen_2037"] = sum(e) / len(e)
            ligne["ecart_max_2037"] = max(e)
        out.append(ligne)
        print(nom, {k: round(v, 3) for k, v in ligne.items() if k != "parametre"}, flush=True)
    out.sort(key=lambda x: -(x.get("ecart_moyen_2037", 0) + x["deficit_sq_2037"]))
    return out


def ecrire(lignes: list[dict]) -> Path:
    f = RACINE / "sorties" / "poids_incertitude.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["rang", "parametre", "deficit_sq_2037", "ecart_moyen_2037", "ecart_max_2037"])
        w.writeheader()
        for i, x in enumerate(lignes, 1):
            w.writerow({"rang": i, **{k: round(v, 4) if isinstance(v, float) else v for k, v in x.items()}})
    return f


if __name__ == "__main__":
    print(ecrire(calcul(sys.argv[1:] or None)))
