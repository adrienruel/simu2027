"""Affiche une feuille : libellé en colonne A, puis formules des colonnes demandées (complètes).

Usage : python outils/feuille.py "Feuille" [colonnes=BC] [lignes=1-200]
"""
import sys
from arbre import FORM, VAL

f = sys.argv[1]
cols = sys.argv[2] if len(sys.argv) > 2 else "BC"
a, b = (sys.argv[3] if len(sys.argv) > 3 else "1-400").split("-")
rows = sorted({int(x[len(x.rstrip('0123456789')):]) for (g, x) in FORM if g == f})
for r in rows:
    if not int(a) <= r <= int(b):
        continue
    parts = []
    for c in cols.split(",") if "," in cols else cols:
        v = FORM.get((f, f"{c}{r}"))
        if v is not None:
            vv = VAL.get((f, f"{c}{r}"))
            parts.append(f"{c}: {v}" + (f"  → {vv:.6g}" if isinstance(v, str) and v.startswith("=") and isinstance(vv, (int, float)) else ""))
    lab = VAL.get((f, f"A{r}"))
    if parts or lab:
        print(r, "«", str(lab)[:90], "»", " | ".join(parts))
