"""Génère le tableau de bord (une page HTML autonome) à partir du moteur.

    python -m outils.tableau_de_bord            # écrit sorties/tableau_de_bord.html
"""
from __future__ import annotations

import json
from pathlib import Path

from moteur.restitution import donnees

RACINE = Path(__file__).resolve().parent.parent
GABARIT = Path(__file__).resolve().parent / "gabarit_tableau.html"
SORTIE = RACINE / "sorties" / "tableau_de_bord.html"


def generer(chemin: Path = SORTIE) -> Path:
    d = json.dumps(donnees(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = GABARIT.read_text(encoding="utf-8").replace("/*DONNEES*/", d)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(html, encoding="utf-8")
    return chemin


if __name__ == "__main__":
    print(f"Écrit : {generer()}")
