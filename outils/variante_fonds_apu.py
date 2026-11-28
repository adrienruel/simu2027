"""Variante commune « fonds de capitalisation dans les administrations publiques » (moteur/fonds_apu.py), pour tous
les programmes qui ont un fonds codé. Écrit sorties/variante_fonds_apu.json et sorties/comparaison_variante_fonds.csv.

    python -m outils.variante_fonds_apu [programme ...]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from moteur import fonds_apu, noyau
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
ANS = (2029, 2037, 2050, 2073)
# Programmes publiés qui proposent un fonds de capitalisation.
PROGRAMMES = ("philippe", "retailleau", "zemmour", "le_pen")  # Bertrand retiré le 28/11/2026


def calcul(nom: str, p: Parametres | None = None) -> dict:
    p = p or Parametres()
    prog = noyau.charger(nom)
    v = fonds_apu.variante(p, prog)
    return {s: {t: {"deficit_publie": round(x["publie"][t]["deficit"], 2), "deficit_fonds_apu": round(x["apu"][t]["deficit"], 2),
                    "dette_pib_publiee": round(x["publie"][t]["dette_pib"], 1), "dette_pib_fonds_apu": round(x["apu"][t]["dette_pib"], 1),
                    "deplace_md": round(x["deplace"][t], 1)} for t in ANS} for s, x in v.items()}


def main(noms=PROGRAMMES) -> dict:
    p = Parametres()
    out = {nom: calcul(nom, p) for nom in noms}
    (RACINE / "sorties" / "variante_fonds_apu.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(RACINE / "sorties" / "comparaison_variante_fonds.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["programme", "scenario", "annee", "deficit_publie", "deficit_fonds_apu", "dette_pib_publiee",
                    "dette_pib_fonds_apu", "deplace_md"])
        for nom, v in out.items():
            lib = noyau.charger(nom).libelle
            for s, a in v.items():
                for t, x in a.items():
                    w.writerow([lib, s, t, *x.values()])
    from outils import trace
    trace.enregistrer(["variante_fonds_apu.json", "comparaison_variante_fonds.csv"], script="outils.variante_fonds_apu",
                      note=None if set(noms) == set(PROGRAMMES) else "sous-ensemble : " + ", ".join(noms))
    return out


if __name__ == "__main__":
    for nom, v in main(tuple(sys.argv[1:]) or PROGRAMMES).items():
        for s, a in v.items():
            for t, x in a.items():
                print(f"{nom:20s} {s:10s} {t}  déficit {x['deficit_publie']:6.2f} → {x['deficit_fonds_apu']:6.2f}"
                      f"  dette {x['dette_pib_publiee']:6.1f} → {x['dette_pib_fonds_apu']:6.1f}  (déplacé {x['deplace_md']:+.1f} Md€)")
