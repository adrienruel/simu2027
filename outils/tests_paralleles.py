"""Suite de tests en parallèle, sans dépendance en plus (25/11/2026).

Les fichiers de tests sont répartis en N groupes de durée proche (durées mesurées dans tests/durees.json, 1 s pour un
fichier absent), puis chaque groupe tourne dans son propre processus pytest. Les tests n'écrivent que dans tmp_path :
les groupes ne se gênent pas. Le code de retour est le plus mauvais des groupes.

    python -m outils.tests_paralleles                 # N = nombre de cœurs
    python -m outils.tests_paralleles -j 4 -m "not lent"
    python -m outils.tests_paralleles --mesurer       # suite en série, met à jour tests/durees.json

Les arguments inconnus sont transmis à pytest. Si pytest-xdist est installé, `python -m pytest -n auto` fait la même
chose, test par test.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DUREES = RACINE / "tests" / "durees.json"


def fichiers() -> list[str]:
    return sorted(f"tests/{f.name}" for f in (RACINE / "tests").glob("test_*.py"))


def repartir(noms: list[str], n: int, durees: dict[str, float]) -> list[list[str]]:
    """Plus long d'abord, chaque fichier dans le groupe le moins chargé."""
    groupes = [([], 0.0) for _ in range(n)]
    for f in sorted(noms, key=lambda f: -durees.get(f, 1.0)):
        i = min(range(n), key=lambda k: groupes[k][1])
        groupes[i] = (groupes[i][0] + [f], groupes[i][1] + durees.get(f, 1.0))
    return [g for g, _ in groupes if g]


def mesurer(reste: list[str]) -> int:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--durations=0", *reste]
    r = subprocess.run(cmd, cwd=RACINE, capture_output=True, text=True)
    d: dict[str, float] = {}
    for l in r.stdout.splitlines():
        m = re.match(r"([0-9.]+)s (setup|call|teardown)\s+(tests/[^:]+)::", l)
        if m:
            d[m.group(3)] = d.get(m.group(3), 0.0) + float(m.group(1))
    DUREES.write_text(json.dumps({k: round(v, 2) for k, v in sorted(d.items())}, indent=1) + "\n", encoding="utf-8")
    print(r.stdout.splitlines()[-1] if r.stdout else r.stderr[-2000:])
    print(f"{DUREES.relative_to(RACINE)} : {len(d)} fichiers, {sum(d.values()):.0f} s en série")
    return r.returncode


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("-j", type=int, default=os.cpu_count() or 2, help="nombre de processus")
    a.add_argument("--mesurer", action="store_true", help="mettre à jour tests/durees.json (suite en série)")
    args, reste = a.parse_known_args(argv)
    if args.mesurer:
        return mesurer(reste)
    durees = json.loads(DUREES.read_text(encoding="utf-8")) if DUREES.exists() else {}
    groupes = repartir(fichiers(), max(1, args.j), durees)
    t0 = time.time()
    procs = [subprocess.Popen([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *reste, *g],
                              cwd=RACINE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for g in groupes]
    codes, bilans = [], []
    for i, pr in enumerate(procs):
        sortie, _ = pr.communicate()
        codes.append(pr.returncode)
        lignes = sortie.rstrip().splitlines()
        bilans.append(lignes[-1] if lignes else "")
        # détail des échecs seulement (le reste n'est que des points)
        if pr.returncode not in (0, 5):
            print(f"===== groupe {i + 1} =====")
            print(sortie)
    for i, b in enumerate(bilans):
        print(f"groupe {i + 1} ({len(groupes[i])} fichiers) : {b}")
    print(f"{len(groupes)} processus, {time.time() - t0:.0f} s")
    # 5 = aucun test sélectionné dans le groupe (filtre -m ou -k) : pas un échec
    pires = [c for c in codes if c != 5]
    return max(pires) if pires else 5


if __name__ == "__main__":
    sys.exit(main())
