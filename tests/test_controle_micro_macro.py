"""Audit I5 (27/11/2026) : tout écart de plus de 30 % entre OpenFisca et le moteur sur une mesure est expliqué.

sorties/controle_micro_macro.csv (outils/controle_micro_macro.py) compare toutes les mesures passées dans OpenFisca,
y compris celles que le moteur calcule par une fonction. Les écarts au-delà du seuil figurent dans
parametres/controles/ecarts_micro_macro.yaml, avec une raison (périmètre, montée en charge, assiette) ou, à défaut,
dans l'arriéré « a_expliquer », qu'il faut vider.
"""
import csv
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[1]


def _ecarts():
    doc = yaml.safe_load((RACINE / "parametres" / "controles" / "ecarts_micro_macro.yaml").read_text(encoding="utf-8"))
    return doc.get("expliques") or {}, set(doc.get("a_expliquer") or [])


def test_ecarts_expliques_ou_dans_l_arriere():
    expliques, arriere = _ecarts()
    hors = {f"{r['programme']}.{r['mesure']}" for r in csv.DictReader((RACINE / "sorties" / "controle_micro_macro.csv").open(encoding="utf-8"))
            if r["hors_seuil"] == "1"}
    connus = set(expliques) | arriere
    assert hors - connus == set(), f"écarts micro/macro sans explication : {sorted(hors - connus)}"
    assert connus - hors == set(), f"à retirer de ecarts_micro_macro.yaml (écart résorbé) : {sorted(connus - hors)}"
    assert not set(expliques) & arriere
    for cle, raison in expliques.items():
        assert isinstance(raison, str) and len(raison) > 20, f"{cle} : raison trop courte"
