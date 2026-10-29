"""Leviers pour améliorer les comptes : chaque variante est le programme actuel avec un paramètre changé.

Mesure, dans le prudent : déficit avant clause (2029, 2037, 2050, 2060, 2073), déficit publié 2037, dette 2073,
effet du programme sur les naissances. Écrit sorties/leviers.json.

    python -m outils.leviers
"""
from __future__ import annotations

import json
from pathlib import Path

from moteur.demographie import effet_naissances
from moteur.parametres import Parametres
from moteur.simulation import simuler

RACINE = Path(__file__).resolve().parent.parent
ANS = (2029, 2037, 2050, 2060, 2073)

VARIANTES = [
    ("Programme actuel", {}),
    # Famille
    ("Famille : 2e enfant à 25 % du RUI (au lieu de 15 %)", {"rui_complements.part_enfant_rang2": 0.25}),
    ("Famille : crèches +20 points de couverture (au lieu de +10)", {"famille.creches_nouvelles/points_couverture": 0.20}),
    ("Famille : parent isolé à 50 % du RUI par enfant", {"rui_complements.part_enfant_parent_isole": 0.50}),
    # Retraites
    ("Retraites : socle annulé à 2 000 € de rente (au lieu de 2 500)", {"retraites.rente_annulant_socle": 2000}),
    ("Retraites : accès au socle à 68 ans (au lieu de 67)", {"epargne.age_acces_socle": 68}),
    ("Retraites : âge légal de l'ancien système à 66 ans", {"ancien_systeme.age_legal/programme": 66}),
    # Entreprises et emploi
    ("Entreprises : déduction gardée à 50 % (pas de hausse vers 100 %)", {"is_investissement.hausse_part_admise/cible": 0.5}),
    ("Emploi : sans la baisse du coût employeur", {"emploi.retenues_calculees/baisse_cout_travail": 0}),
    # RUI et épargne
    ("RUI à 750 € (au lieu de 800)", {"rui.montant": 750}),
    ("Épargne obligatoire : 1 point sur 10 versé à l'État", {"epargne.contribution_transition": 0.1}),
    # Canaux ajoutés le 29/10/2026 : ce qu'ils changent
    ("Sans la prime de taux liée à la dette", {"macro.prime_dette": 0.0}),
    ("Sans la participation des inactifs", {"emploi.participation_inactifs/prudent": 0.0, "emploi.participation_inactifs/median": 0.0,
                                             "emploi.participation_inactifs/optimiste": 0.0}),
    ("Sans les retombées du capital du fonds", {"macro.externalites_capital_fonds": 0.0}),
    ("Sans les effets des réformes du supérieur sur les carrières", {"carrieres.active": False}),
    # Paquet
    ("Paquet : âge légal 66 ans + 1 point d'épargne à l'État",
     {"ancien_systeme.age_legal/programme": 66, "epargne.contribution_transition": 0.1}),
    ("Paquet + 2e enfant à 25 %",
     {"ancien_systeme.age_legal/programme": 66, "epargne.contribution_transition": 0.1, "rui_complements.part_enfant_rang2": 0.25}),
]


def mesurer(nom: str, modifs: dict) -> dict:
    p = Parametres().avec(modifs)
    r = simuler(p)["prudent"]
    return {"variante": nom, "modifs": {k: v for k, v in modifs.items()},
            "deficit_sans_clause": {t: round(r[t]["deficit_avant_clause"], 2) for t in ANS},
            "deficit_publie_2037": round(r[2037]["deficit"], 2), "dette_2073": round(r[2073]["dette_pib"]),
            "naissances": round(100 * effet_naissances(p), 1)}


def main() -> list[dict]:
    out = [mesurer(n, m) for n, m in VARIANTES]
    (RACINE / "sorties" / "leviers.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    base = None
    for x in main():
        d = x["deficit_sans_clause"]
        base = base or d
        print(f"{x['variante'][:62]:62} " + " ".join(f"{d[t]:5.2f}({d[t] - base[t]:+.2f})" for t in ANS)
              + f"  publié37 {x['deficit_publie_2037']:.2f}  dette73 {x['dette_2073']}  naiss {x['naissances']:+.1f}")
