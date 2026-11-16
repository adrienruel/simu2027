"""Le comparateur ne dépend pas d'« Écologie de droite » (décision du 16/11/2026).

Ce programme de test est mis de côté : il reste dans le dépôt, gelé, mais aucun programme publié ne doit lire ses
paramètres ni son code. Le dernier test simule tous les programmes publiés avec son dossier rendu inaccessible et
retrouve les trajectoires publiées."""
import csv
import subprocess
import sys
import textwrap
from pathlib import Path

from moteur import noyau
from moteur.parametres import PROGRAMME_ECARTE, RACINE, Parametres


def test_aucun_programme_par_defaut():
    p = Parametres()
    assert p.programme is None
    assert not [c for c, f in p.origine.items() if "programmes" in Path(f).parts]


def test_ecarte_hors_des_programmes_publies():
    publies = noyau.programmes_disponibles()
    assert publies[0] == "statu_quo"
    assert PROGRAMME_ECARTE not in publies
    assert PROGRAMME_ECARTE in noyau.programmes_disponibles(tous=True)


def test_sorties_sans_ecarte():
    for f in (RACINE / "sorties").glob("comparaison_*.csv"):
        assert "Écologie de droite" not in f.read_text(encoding="utf-8"), f.name


SCRIPT = textwrap.dedent('''
    import importlib.abc, json, sys
    from moteur import parametres, noyau

    class Bloque(importlib.abc.MetaPathFinder):
        def find_spec(self, nom, chemin, cible=None):
            if nom.startswith("programmes." + parametres.PROGRAMME_ECARTE):
                raise ImportError("code d'Écologie de droite chargé par le comparateur : " + nom)
            return None

    sys.meta_path.insert(0, Bloque())
    dossier = parametres.dossier_programme

    def dossier_bloque(nom):
        if nom == parametres.PROGRAMME_ECARTE:
            raise FileNotFoundError("paramètres d'Écologie de droite lus par le comparateur")
        return dossier(nom)

    parametres.dossier_programme = dossier_bloque
    p = parametres.Parametres()
    out = {}
    for nom in noyau.programmes_disponibles():
        prog = noyau.charger(nom)
        res = noyau.simuler(p, None if nom == "statu_quo" else prog)
        out[getattr(prog, "libelle", nom)] = {s: {t: round(x["deficit"], 3) for t, x in v.items()} for s, v in res.items()}
    print(json.dumps(out, ensure_ascii=False))
''')

SCENARIOS = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}


def test_programmes_publies_sans_le_dossier_ecarte():
    r = subprocess.run([sys.executable, "-c", SCRIPT], cwd=RACINE, capture_output=True, text=True, timeout=1800)
    assert r.returncode == 0, r.stderr[-2000:]
    import json
    calc = json.loads(r.stdout.strip().splitlines()[-1])
    publies = {}
    with (RACINE / "sorties" / "comparaison_trajectoire.csv").open(encoding="utf-8") as f:
        for x in csv.DictReader(f):
            publies[(x["programme"], x["scenario"], int(x["annee"]))] = float(x["deficit"])
    n = 0
    for lib, v in calc.items():
        for s, a in v.items():
            for t, d in a.items():
                assert d == publies[(lib, SCENARIOS[s], int(t))], (lib, s, t)
                n += 1
    assert n == len(publies)
