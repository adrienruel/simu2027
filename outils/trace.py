"""Traçabilité des sorties (roadmap du comparateur, chantier 1.2, 16/11/2026).

Chaque fichier de `sorties/` a une entrée dans
`sorties/MANIFESTE.json` : empreinte du fichier, commit et date de production, empreinte des paramètres utilisés et
script qui l'a écrit. `tests/test_sorties.py` échoue si un fichier n'y est pas, s'il a été modifié depuis, ou s'il a
été produit avec d'autres paramètres que les paramètres actuels.

Usage, à la fin d'un script qui écrit des sorties :
    from outils import trace
    trace.enregistrer(["comparaison_trajectoire.csv", ...], script="outils.export_comparaison")
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SORTIES = RACINE / "sorties"
MANIFESTE = SORTIES / "MANIFESTE.json"


def empreinte_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def fichiers_parametres() -> list[Path]:
    """Paramètres communs et paramètres des programmes publiés (programmes/publies.yaml)."""
    import yaml
    publies = yaml.safe_load((RACINE / "programmes" / "publies.yaml").read_text(encoding="utf-8"))["publies"]
    out = sorted((RACINE / "parametres" / "commun").glob("*.yaml"))
    out += [RACINE / "programmes" / "publies.yaml"]
    for nom in publies:
        out += sorted((RACINE / "programmes" / nom).glob("*.yaml"))
    out += sorted((RACINE / "programmes").glob("*.yaml"))
    return sorted(set(out))


def empreinte_parametres() -> str:
    """Empreinte du contenu de tous les fichiers de paramètres qui servent au comparateur."""
    h = hashlib.sha256()
    for f in fichiers_parametres():
        h.update(str(f.relative_to(RACINE)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=RACINE, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def commit() -> dict:
    """Commit courant et code modifié non commité (hors sorties/)."""
    h = _git("rev-parse", "--short", "HEAD")
    sale = _git("status", "--porcelain", "--", ".", ":(exclude)sorties")
    return {"commit": h, "code_non_commite": bool(sale)}


def lire() -> dict:
    if MANIFESTE.exists():
        return json.loads(MANIFESTE.read_text(encoding="utf-8"))
    return {"note": __doc__.strip().splitlines()[0], "fichiers": {}}


def ecrire(m: dict) -> None:
    m["fichiers"] = dict(sorted(m["fichiers"].items()))
    MANIFESTE.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _script_principal() -> str:
    import sys
    m = sys.modules.get("__main__")
    spec = getattr(m, "__spec__", None)
    if spec is not None and spec.name:
        return spec.name
    return Path(getattr(m, "__file__", "inconnu")).stem


def enregistrer(fichiers, script: str | None = None, note: str | None = None) -> None:
    """Inscrit au manifeste les fichiers que le script vient d'écrire (noms relatifs à sorties/, ou chemins).

    Verrou de fichier : plusieurs processus de la micro peuvent écrire en même temps. Un fichier hors de sorties/,
    est ignoré."""
    import fcntl
    if isinstance(fichiers, (str, Path)):
        fichiers = [fichiers]
    noms = []
    for x in fichiers:
        f = Path(x) if Path(x).is_absolute() else SORTIES / x
        try:
            rel = f.resolve().relative_to(SORTIES.resolve())
        except ValueError:
            continue
        noms.append(str(rel))
    if not noms:
        return
    script = script or _script_principal()
    c = commit()
    quand = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    emp = empreinte_parametres()
    with (SORTIES / ".manifeste.verrou").open("w") as verrou:
        fcntl.flock(verrou, fcntl.LOCK_EX)
        m = lire()
        for nom in noms:
            m["fichiers"][nom] = {"sha256": empreinte_fichier(SORTIES / nom), "script": script, "date": quand, **c,
                                  "parametres": emp, **({"note": note} if note else {})}
        ecrire(m)


def suivis() -> list[str]:
    """Fichiers de sorties/ qui doivent figurer au manifeste."""
    out = []
    for f in SORTIES.rglob("*"):
        if not f.is_file() or f == MANIFESTE or f.name == ".manifeste.verrou":
            continue
        rel = f.relative_to(SORTIES)
        out.append(str(rel))
    return sorted(out)


def verifier() -> dict[str, list[str]]:
    """Fichiers absents du manifeste, modifiés depuis, produits avec d'autres paramètres, ou d'origine inconnue."""
    m = lire()["fichiers"]
    emp = empreinte_parametres()
    r = {"absents": [], "modifies": [], "parametres_changes": [], "anterieurs": [], "disparus": []}
    for nom in suivis():
        x = m.get(nom)
        if x is None:
            r["absents"].append(nom)
        elif x["sha256"] != empreinte_fichier(SORTIES / nom):
            r["modifies"].append(nom)
        elif x.get("parametres") is None:
            r["anterieurs"].append(nom)
        elif x["parametres"] != emp:
            r["parametres_changes"].append(nom)
    r["disparus"] = sorted(set(m) - set(suivis()))
    return r


if __name__ == "__main__":
    for k, v in verifier().items():
        print(f"{k} ({len(v)}) : {', '.join(v) if v else '—'}")
