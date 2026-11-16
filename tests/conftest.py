"""Tests d'« Écologie de droite » (programme de test mis de côté le 16/11/2026).

Ils sont exclus par défaut (pytest.ini : -m "not edd"). Lancés avec -m edd, ils retrouvent leur ancien réglage :
Parametres() charge alors aussi les paramètres d'Écologie de droite, comme avant le découplage. La suite par défaut
vérifie ainsi que le comparateur ne dépend plus de ce programme."""
from pathlib import Path

import pytest

ICI = Path(__file__).parent
# Fichiers entièrement propres à Écologie de droite : non collectés hors du mode -m edd (leur code de chargement
# suppose les paramètres de ce programme).
FICHIERS_EDD: set[str] = set((ICI / "fichiers_edd.txt").read_text(encoding="utf-8").split()) if (ICI / "fichiers_edd.txt").exists() else set()


def _mode_edd(config) -> bool:
    return (config.getoption("-m") or "").strip() == "edd"


def pytest_configure(config):
    if _mode_edd(config):
        from moteur import parametres
        parametres.PROGRAMME_DEFAUT = parametres.PROGRAMME_ECARTE


def pytest_ignore_collect(collection_path, config):
    if not _mode_edd(config) and collection_path.name in FICHIERS_EDD:
        return True
    return None


def pytest_collection_modifyitems(config, items):
    for it in items:
        if it.path.name in FICHIERS_EDD:
            it.add_marker(pytest.mark.edd)
