"""Découpe l'export texte du classeur (une section « ## Sheet: » par feuille) en un TSV par feuille.

Usage : python outils/decouper_export.py <export.txt> <dossier_sortie>
L'export ne contient que les valeurs (ni formules ni adresses de cellules) :
il sert de référence chiffrée, pas de source des formules.
"""
import re
import sys
import unicodedata
from pathlib import Path


def slug(nom: str) -> str:
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()


def main(src: str, dest: str) -> None:
    out = Path(dest)
    out.mkdir(parents=True, exist_ok=True)
    feuille, lignes, n = None, [], 0
    def ecrire():
        nonlocal n
        if feuille:
            (out / f"{slug(feuille)}.tsv").write_text("\n".join(lignes).strip() + "\n", encoding="utf-8")
            n += 1
    for ligne in Path(src).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## Sheet: (.+)$", ligne)
        if m:
            ecrire()
            feuille, lignes = m.group(1).strip(), []
        else:
            lignes.append(ligne)
    ecrire()
    print(f"{n} feuilles écrites dans {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
