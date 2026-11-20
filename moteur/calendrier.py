"""PIB de 2026 (Md€ de 2026), point de départ commun."""
from __future__ import annotations

from .parametres import Parametres
from .unites import facteur


def pib_2026(p: Parametres) -> float:
    return 2920 * facteur(p, 2024, "recettes")


