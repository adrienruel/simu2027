"""Affiche l'arbre des précédents d'une cellule du classeur v235 (formule + valeur).

Usage : python outils/arbre.py "Feuille!B17" [profondeur] [largeur_formule]
Les plages (A1:B9) ne sont pas dépliées : on indique leur somme.
"""
import pickle
import re
import sys
from pathlib import Path

import openpyxl

XLSX = Path(__file__).resolve().parent.parent / "reference" / "Chiffrage_programme_complet_v235.xlsx"
CACHE = XLSX.with_suffix(".pkl")

REF = re.compile(r"(?:'([^']+)'|([A-Za-zÀ-ÿ_][\wÀ-ÿ&\.]*))?!?\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?")
TOKEN = re.compile(r"(?:(?:'[^']+'|[A-Za-zÀ-ÿ_][\wÀ-ÿ&\.]*)!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?")


def charger():
    if CACHE.exists() and CACHE.stat().st_mtime > XLSX.stat().st_mtime:
        return pickle.loads(CACHE.read_bytes())
    f = openpyxl.load_workbook(XLSX, data_only=False, read_only=True)
    v = openpyxl.load_workbook(XLSX, data_only=True, read_only=True)
    form, val = {}, {}
    for ws in f.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and hasattr(c, "coordinate"):
                    form[(ws.title, c.coordinate)] = c.value
    for ws in v.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and hasattr(c, "coordinate"):
                    val[(ws.title, c.coordinate)] = c.value
    d = (form, val)
    CACHE.write_bytes(pickle.dumps(d))
    return d


FORM, VAL = charger()


def refs(formule, feuille):
    out = []
    for t in TOKEN.findall(formule):
        if "!" in t:
            f, a = t.rsplit("!", 1)
            f = f.strip("'")
        else:
            f, a = feuille, t
        out.append((f, a.replace("$", "")))
    return out


def libelle(f, a):
    ligne = re.sub(r"[A-Z]+", "", a.split(":")[0])
    lab = VAL.get((f, "A" + ligne))
    return str(lab)[:70] if isinstance(lab, str) else ""


def montrer(f, a, prof, larg, vu, indent=0):
    if ":" in a:
        print("  " * indent + f"{f}!{a}  [plage]")
        return
    key = (f, a)
    fo, va = FORM.get(key), VAL.get(key)
    vs = f"{va:.6g}" if isinstance(va, (int, float)) else repr(va)[:40]
    est_f = isinstance(fo, str) and fo.startswith("=")
    print("  " * indent + f"{f}!{a} = {vs}  « {libelle(f, a)} »" + (f"  {fo[:larg]}" if est_f else "  [saisie]"))
    if est_f and prof > 0 and key not in vu:
        vu.add(key)
        for r in dict.fromkeys(refs(fo, f)):
            montrer(*r, prof - 1, larg, vu, indent + 1)


if __name__ == "__main__":
    cible = sys.argv[1]
    f, a = cible.rsplit("!", 1)
    montrer(f.strip("'"), a, int(sys.argv[2]) if len(sys.argv) > 2 else 1,
            int(sys.argv[3]) if len(sys.argv) > 3 else 160, set())
