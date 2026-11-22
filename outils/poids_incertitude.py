"""Roadmap 6.1 (22/11/2026) : quels paramètres incertains pèsent le plus ? Sensibilité un à un.

Pour chaque jeu de scénarios commun (moteur/incertitude.cibles), on place ce seul paramètre à son 10e puis à son
90e centile (z = ∓1,2816 : ses valeurs prudente et optimiste), tous les autres au médian, dans le scénario médian.
Poids = demi-écart du déficit 2037 du statu quo, et demi-écart moyen (en valeur absolue) de l'écart de solde primaire
2037 des programmes au statu quo. Le classement dit où des lois sourcées (au lieu des colonnes de scénario) changent
le plus la fourchette publiée.

    python -m outils.poids_incertitude        → sorties/poids_incertitude.csv

Le calcul garde chaque ligne dans sorties/poids_incertitude_lignes.jsonl et reprend là où il s'est arrêté ; il tourne
par lots de LOT cibles, un processus par lot (la mémoire grossit avec les simulations : 8 Go ne suffisent pas pour
les 78 cibles d'un coup). Effacer le fichier .jsonl pour repartir de zéro.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from moteur import incertitude as inc
from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
T = 2037
LOT = 8
LIGNES = RACINE / "sorties" / "poids_incertitude_lignes.jsonl"


def faites() -> dict[str, dict]:
    if not LIGNES.exists():
        return {}
    out = {}
    for l in LIGNES.read_text(encoding="utf-8").splitlines():
        if l.strip():
            x = json.loads(l)
            out[x["parametre"]] = x
    return out


def _deficit_sq(p) -> float:
    return noyau.simuler(p, None, scenarios=("median",), contrefactuel=False)["median"][T]["deficit"]


def _ecart(p, nom: str, base) -> float:
    r = noyau.simuler(p, noyau.charger(nom), scenarios=("median",))
    return sq.ecart(r, base)["median"][T]["solde_primaire"]


def noms_cibles() -> list[str]:
    return ["/".join((cle,) + tuple(str(k) for k in chemin)) for cle, chemin in inc.cibles(Parametres())]


def calcul(programmes: list[str] | None = None, limite: int | None = None) -> list[dict]:
    """Calcule les cibles pas encore faites (au plus `limite`), en ajoutant chaque ligne au fichier .jsonl."""
    p = Parametres()
    noms = programmes if programmes is not None else inc.programmes()
    deja = faites()
    out = []
    for cle, chemin in inc.cibles(p):
        nom = "/".join((cle,) + tuple(str(k) for k in chemin))
        if nom in deja:
            continue
        if limite is not None and len(out) >= limite:
            break
        q = {z: inc.tirer_z(p, lambda n, z=z: z if n == nom else 0.0, [(cle, chemin)]) for z in (-inc.Z90, inc.Z90)}
        d = {z: _deficit_sq(q[z]) for z in q}
        ligne = {"parametre": nom, "deficit_sq_2037": abs(d[inc.Z90] - d[-inc.Z90]) / 2}
        if noms:
            base = {z: {"median": noyau.simuler(q[z], None, scenarios=("median",))["median"]} for z in q}
            e = [abs(_ecart(q[inc.Z90], n, base[inc.Z90]) - _ecart(q[-inc.Z90], n, base[-inc.Z90])) / 2 for n in noms]
            ligne["ecart_moyen_2037"] = sum(e) / len(e)
            ligne["ecart_max_2037"] = max(e)
        out.append(ligne)
        with LIGNES.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        print(nom, {k: round(v, 3) for k, v in ligne.items() if k != "parametre"}, flush=True)
    return out


def tout(programmes: list[str] | None = None) -> list[dict]:
    """Toutes les cibles, par lots de LOT dans des processus séparés ; renvoie les lignes classées."""
    total = len(noms_cibles())
    while len(faites()) < total:
        avant = len(faites())
        code = f"from outils import poids_incertitude as m; m.calcul({programmes!r}, limite={LOT})"
        subprocess.run([sys.executable, "-c", code], cwd=RACINE, check=True)
        if len(faites()) == avant:
            raise RuntimeError("aucune cible calculée dans le dernier lot")
    lignes = [x for n, x in faites().items() if n in set(noms_cibles())]
    lignes.sort(key=lambda x: -(x.get("ecart_moyen_2037", 0) + x["deficit_sq_2037"]))
    return lignes


def ecrire(lignes: list[dict]) -> Path:
    f = RACINE / "sorties" / "poids_incertitude.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["rang", "parametre", "deficit_sq_2037", "ecart_moyen_2037", "ecart_max_2037"])
        w.writeheader()
        for i, x in enumerate(lignes, 1):
            w.writerow({"rang": i, **{k: round(v, 4) if isinstance(v, float) else v for k, v in x.items()}})
    return f


if __name__ == "__main__":
    print(ecrire(tout(sys.argv[1:] or None)))
