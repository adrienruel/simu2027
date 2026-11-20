"""Le comparateur ne garde rien d'« Écologie de droite » (supprimé le 20/11/2026, à refaire un jour sur le noyau
commun comme un programme ordinaire), et les sorties publiées se recalculent à l'identique."""
import csv
import subprocess
import sys
import textwrap
from pathlib import Path

from moteur import noyau
from moteur.parametres import RACINE, Parametres


def test_aucun_programme_par_defaut():
    p = Parametres()
    assert p.programme is None
    assert not [c for c, f in p.origine.items() if "programmes" in Path(f).parts]


def test_plus_de_code_ni_de_sortie_d_ecologie_de_droite():
    assert not (RACINE / "programmes" / "ecologie_de_droite").exists()
    assert not (RACINE / "sorties" / "ecologie_de_droite").exists()
    assert "ecologie_de_droite" not in noyau.programmes_disponibles(tous=True)
    for d in ("moteur", "outils", "programmes", "tests"):
        for f in (RACINE / d).rglob("*.py"):
            if f.name != Path(__file__).name:
                assert "ecologie_de_droite" not in f.read_text(encoding="utf-8"), f


def test_sorties_sans_ecologie_de_droite():
    for f in (RACINE / "sorties").glob("comparaison_*.csv"):
        assert "Écologie de droite" not in f.read_text(encoding="utf-8"), f.name


SCRIPT = textwrap.dedent('''
    import json
    from moteur import parametres, noyau
    p = parametres.Parametres()
    out = {}
    for nom in noyau.programmes_disponibles():
        prog = noyau.charger(nom)
        res = noyau.simuler(p, None if nom == "statu_quo" else prog)
        out[getattr(prog, "libelle", nom)] = {s: {t: round(x["deficit"], 3) for t, x in v.items()} for s, v in res.items()}
    print(json.dumps(out, ensure_ascii=False))
''')

SCENARIOS = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}


def test_programmes_publies_se_recalculent_a_l_identique():
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
