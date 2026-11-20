"""Module de population, places de crèche et pensions de l'ancien système par génération."""
import pytest

from moteur import demographie
from moteur.parametres import Parametres

P = Parametres()


def test_population_insee_totaux():
    """Totaux publiés par l'Insee (Insee Première n° 2108) : 69,08 millions en 2026, 65,89 en 2070 (central)."""
    pop = demographie._projection("central")
    assert sum(pop[2026]) / 1e6 == pytest.approx(69.082, abs=0.01)
    assert sum(pop[2070]) / 1e6 == pytest.approx(65.887, abs=0.01)
    assert sum(demographie._projection("fec_basse")[2070]) < sum(pop[2070]) < sum(demographie._projection("fec_haute")[2070])


