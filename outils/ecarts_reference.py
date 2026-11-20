"""Écarts au point de référence (roadmap de la simulation globale, chantier 0.4, 20/11/2026).

Le point de référence est l'état de `main` au 20/11/2026 (b03ea64, étiquette `ref-2026-11-20`). Ses résultats clés
sont gardés dans `reference/ref-2026-11-20/`. Chaque phase de la roadmap publie son effet contre eux : on ne cherche
pas à les retrouver, on explique les écarts.

Usage :
    python -m outils.ecarts_reference            # tableau des écarts, 2029, 2037 et 2050, tous les scénarios
    python -m outils.ecarts_reference --figer    # (re)copie les sorties courantes comme référence
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
REF = RACINE / "reference" / "ref-2026-11-20"
SORTIES = RACINE / "sorties"
FICHIERS = ("comparaison_trajectoire.csv", "comparaison_redistribution.csv", "comparaison_couverture_micro.csv")
COLONNES = ("deficit", "ecart_solde_primaire_pib", "dette_pib", "chomage", "emploi_millions")
ANNEES = ("2029", "2037", "2050")


def figer() -> None:
    REF.mkdir(parents=True, exist_ok=True)
    for nom in FICHIERS:
        shutil.copy2(SORTIES / nom, REF / nom)
    print(f"référence figée dans {REF.relative_to(RACINE)}")


def _lire(chemin: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    with chemin.open(encoding="utf-8") as f:
        return {(l["programme"], l["scenario"], l["annee"]): l for l in csv.DictReader(f)}


def ecarts(scenarios=("Prudent",), annees=ANNEES, seuil: float = 0.0) -> list[dict]:
    ref = _lire(REF / "comparaison_trajectoire.csv")
    cour = _lire(SORTIES / "comparaison_trajectoire.csv")
    out = []
    for cle, l in cour.items():
        prog, sc, an = cle
        if sc not in scenarios or an not in annees or cle not in ref:
            continue
        ligne = {"programme": prog, "scenario": sc, "annee": an}
        bouge = False
        for c in COLONNES:
            a, b = float(ref[cle][c]), float(l[c])
            ligne[c] = b
            ligne[f"d_{c}"] = b - a
            bouge |= abs(b - a) > seuil
        if bouge:
            out.append(ligne)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--figer", action="store_true")
    ap.add_argument("--scenarios", default="Prudent")
    args = ap.parse_args()
    if args.figer:
        figer()
        return
    lignes = ecarts(tuple(args.scenarios.split(",")))
    print(f"{'programme':45} {'sc.':8} an   déficit (écart)   solde prim. (écart)   chômage (écart)")
    for l in sorted(lignes, key=lambda x: (x["annee"], x["programme"])):
        print(f"{l['programme'][:45]:45} {l['scenario'][:8]:8} {l['annee']} "
              f"{l['deficit']:6.2f} ({l['d_deficit']:+.2f})   {l['ecart_solde_primaire_pib']:6.2f} "
              f"({l['d_ecart_solde_primaire_pib']:+.2f})        {l['chomage']:5.2f} ({l['d_chomage']:+.2f})")


if __name__ == "__main__":
    main()
