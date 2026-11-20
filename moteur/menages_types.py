"""Ménages types du comparateur : définitions lues dans parametres/menages_types.yaml (outils/export_menages_types.py)."""
from __future__ import annotations

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent


def definitions() -> list[dict]:
    return yaml.safe_load((RACINE / "parametres" / "menages_types.yaml").read_text(encoding="utf-8"))["menages"]


def pensions_adultes(m: dict) -> list[float]:
    """Pension brute annuelle de chaque adulte (retraités de l'ancien système)."""
    return [12 * float(a.split(":")[1]) if isinstance(a, str) and a.startswith("retraite:") else 0.0 for a in m["adultes"]]
