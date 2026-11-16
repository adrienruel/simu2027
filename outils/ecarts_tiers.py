"""Écarts aux chiffrages tiers, mesure par mesure (phase 3.3, chantier C4 ; 16/11/2026).

Quand un chiffrage indépendant des programmes 2027 paraît (Institut Montaigne : annoncé pour le premier trimestre
2027, communiqué du 06/10/2026), ses montants se saisissent dans parametres/sources/chiffrages_tiers.csv, une ligne
par mesure : programme (dossier), mesure telle que nommée par le tiers, montant en Md€ (+ = coût pour les finances
publiques), année, source, url, page, et le nom de la mesure du moteur qui lui correspond (mesure_moteur, vide si
le moteur ne l'a pas). L'outil écrit sorties/comparaison_tiers.csv : montant du tiers, montant du moteur au médian
et au prudent la même année (Md€ de 2026, même signe), écart.

    python -m outils.ecarts_tiers
"""
from __future__ import annotations

import csv

from moteur import noyau
from moteur.parametres import RACINE, Parametres

ENTREE = RACINE / "parametres" / "sources" / "chiffrages_tiers.csv"


def calcul() -> list[dict]:
    lignes = list(csv.DictReader(ENTREE.open(encoding="utf-8")))
    if not lignes:
        return []
    p = Parametres()
    cache, out = {}, []
    for l in lignes:
        nom, t = l["programme"], int(l["annee"])
        if nom not in cache:
            prog = noyau.charger(nom)
            cache[nom] = prog.mesures(p) if not hasattr(prog, "entrees") else {s: e.mesures for s, e in prog.entrees(p).items()}
        r = {**l}
        for s in ("median", "prudent"):
            ms = [m for m in cache[nom].get(s, []) if l["mesure_moteur"] and m.nom == l["mesure_moteur"]]
            # coût pour les finances publiques : dépense en plus, ou recette en moins
            v = sum((-1 if m.poste == "recettes" else 1) * m.valeurs.get(t, 0.0) for m in ms) if ms else None
            r[f"moteur_{s}_md"] = round(v, 2) if v is not None else ""
            r[f"ecart_{s}_md"] = round(v - float(l["montant_tiers_md"]), 2) if v is not None else ""
        out.append(r)
    return out


def main() -> None:
    out = calcul()
    if not out:
        print(f"Aucun chiffrage tiers saisi dans {ENTREE.relative_to(RACINE)} : rien à comparer.")
        return
    f = RACINE / "sorties" / "comparaison_tiers.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    from outils import trace
    trace.enregistrer(f, script="outils.ecarts_tiers")
    print(f"Écrit : {f} ({len(out)} mesures)")


if __name__ == "__main__":
    main()
