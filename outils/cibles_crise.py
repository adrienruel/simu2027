"""Régénère reference/cibles/crise.csv : le scénario de crise de la v235, recalculé en pleine précision.

La feuille « Scénario de crise » ne garde que six décimales. On refait sa procédure (paramètres de la
colonne B recopiés, Effets macro!B8 = RUI!B34, recalcul, lecture du bloc prudent) dans LibreOffice.

    python -m outils.cibles_crise
"""
from __future__ import annotations

import csv
from pathlib import Path

from outils.recalcul import Classeur, appliquer_crise

SORTIE = Path(__file__).resolve().parent.parent / "reference" / "cibles" / "crise.csv"


def main() -> None:
    with Classeur() as c:
        appliquer_crise(c)
        c.recalculer(1)
        em = {r: c.plage("Effets macro", f"B{r}:AT{r}")[0] for r in (73, 74, 107, 114, 115)}
        chomage = c.plage("Emploi", "B28:M28")[0]
    with SORTIE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["annee", "deficit", "dette_pib", "pib", "chomage"])
        for i, an in enumerate(em[73]):
            w.writerow([int(an), repr(-em[114][i]), repr(em[115][i]), repr(em[74][i] + em[107][i]),
                        repr(chomage[i]) if i < len(chomage) else ""])
    print(f"Écrit : {SORTIE}")


if __name__ == "__main__":
    main()
