"""Table de l'incertitude chiffrée (phase D) pour le comparateur : sorties/comparaison_incertitude.csv.

Une ligne par programme, année et grandeur : centiles 10, 50 et 90 des tirages (scénario médian tiré, règle de
trajectoire comprise), écart de déficit au statu quo tirage par tirage, probabilité de faire mieux que le statu quo,
et les cinq hypothèses qui pèsent le plus sur le déficit de 2037. Lit sorties/incertitude.json
(python -m moteur.incertitude 1000) et, s'ils existent, les variantes rho0 et rho1.

    python outils/export_incertitude.py
"""
from __future__ import annotations

import csv
import sys
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))


def libelles() -> dict:
    """Libellés des programmes, comme dans comparaison_trajectoire.csv."""
    from moteur import noyau
    return {nom: getattr(noyau.charger(nom), "libelle", nom) for nom in noyau.programmes_disponibles()}


def main() -> None:
    lib = libelles()
    lignes = []
    for suffixe, rho_lib in (("", None), ("_rho0", "0"), ("_rho1", "1")):
        f = RACINE / "sorties" / f"incertitude{suffixe}.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        for nom, x in r["programmes"].items():
            sens = "; ".join(f"{k} ({v:+.2f})" for k, v in x.get("sensibilite_deficit_2037", [])[:5])
            for cle, v in x.items():
                if not isinstance(v, dict) or "p10" not in v:
                    continue
                grandeur, annee = cle.rsplit("_", 1)
                lignes.append({"programme": lib.get(nom, nom), "dossier": nom, "rho": rho_lib or f"{r['rho']:g}",
                               "n": r["n"], "grandeur": grandeur, "annee": annee,
                               "p10": round(v["p10"], 3), "p50": round(v["p50"], 3), "p90": round(v["p90"], 3),
                               "proba_mieux_que_statu_quo": (round(x[f"proba_mieux_que_statu_quo_{annee}"], 3)
                                                             if grandeur == "deficit" and f"proba_mieux_que_statu_quo_{annee}" in x else ""),
                               "hypotheses_deficit_2037": sens if (grandeur == "deficit" and annee == "2037") else ""})
    out = RACINE / "sorties" / "comparaison_incertitude.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    print(f"Écrit : {out} ({len(lignes)} lignes)")


if __name__ == "__main__":
    main()
