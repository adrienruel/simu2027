"""Photo au bit près du moteur : sert à vérifier qu'un changement ne bouge aucun chiffre publié.

Prend les 13 lignes (statu quo + programmes publiés) × 4 scénarios, toutes les grandeurs numériques de toutes les
années, plus quelques tirages du Monte Carlo, et les écrit en JSON (flottants en repr, donc exacts).

    python -m outils.photo prendre /tmp/avant.json        # photo
    python -m outils.photo comparer /tmp/avant.json /tmp/apres.json

Roadmap du moteur (25/11/2026), règle de R0 à R2 : « aucun chiffre publié ne change ».
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

N_TIRAGES = 6


def _aplatir(x, prefixe: str, out: dict) -> None:
    if isinstance(x, dict):
        for k, v in x.items():
            _aplatir(v, f"{prefixe}/{k}", out)
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            _aplatir(v, f"{prefixe}[{i}]", out)
    elif isinstance(x, bool) or x is None or isinstance(x, str):
        out[prefixe] = x
    elif isinstance(x, (int, float)):
        out[prefixe] = repr(float(x))


def _programme(nom: str) -> dict:
    from moteur import noyau
    from moteur.parametres import Parametres
    prog = None if nom == "statu_quo" else noyau.charger(nom)
    out: dict = {}
    _aplatir(noyau.simuler(Parametres(), prog), nom, out)
    return out


def _tirage(i: int) -> dict:
    from moteur import incertitude as inc
    noms = inc.programmes()
    base, propres, listes = inc._preparer(noms)
    out: dict = {}
    _aplatir(inc.un_tirage(i, 2029, 1.0, noms, base, propres, listes), f"tirage{i}", out)
    return out


def prendre(chemin: str) -> None:
    from moteur import noyau
    noms = ["statu_quo"] + noyau.programmes_disponibles()[1:]
    photo: dict = {}
    with ProcessPoolExecutor() as ex:
        for d in ex.map(_programme, noms):
            photo.update(d)
        for d in ex.map(_tirage, range(N_TIRAGES)):
            photo.update(d)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(photo, f, sort_keys=True)
    print(f"{len(photo)} valeurs -> {chemin}")


def comparer(a: str, b: str) -> int:
    with open(a, encoding="utf-8") as f:
        x = json.load(f)
    with open(b, encoding="utf-8") as f:
        y = json.load(f)
    cles = sorted(set(x) | set(y))
    diff = [k for k in cles if x.get(k, "absent") != y.get(k, "absent")]
    print(f"{len(cles)} valeurs, {len(diff)} différentes")
    for k in diff[:20]:
        print(f"  {k}: {x.get(k, 'absent')} -> {y.get(k, 'absent')}")
    return 1 if diff else 0


if __name__ == "__main__":
    if sys.argv[1] == "prendre":
        prendre(sys.argv[2])
    else:
        sys.exit(comparer(sys.argv[2], sys.argv[3]))
