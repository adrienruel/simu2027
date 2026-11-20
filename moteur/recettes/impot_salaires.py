"""Effectifs de salariés du privé et du public par classe, passés en euros de 2026 (moteur/distribution.py)."""
from __future__ import annotations

from ..distribution import lire, passer_en_2026
from ..parametres import Parametres
from ..unites import facteur


def effectifs_prive_2026(p: Parametres):
    d = lire("salaries_prive.csv")
    return passer_en_2026(d, facteur(p, 2024, "salaire_prive"))


def effectifs_public_2026(p: Parametres):
    return passer_en_2026(lire("fonctionnaires.csv"), facteur(p, 2023, "salaire_public"))


