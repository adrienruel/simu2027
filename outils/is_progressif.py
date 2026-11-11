"""Test d'un IS progressif (demande d'Adrien du 30/10/2026) : barèmes comparés au taux unique de 40 % (État).

Pour chaque barème, le taux de la dernière tranche est calé pour que l'IS de l'État du budget statique soit le
même qu'avec le taux unique (neutre avant réactions). Puis la simulation complète dit ce que changent les
réactions : investissement par taille, dirigeants payés en salaire, transfert de bénéfices et localisation des
grandes entreprises (taux de la dernière tranche), emplois et chômage. Écrit sorties/is_progressif.json.

    python -m outils.is_progressif
"""
from __future__ import annotations

import json
from pathlib import Path

from moteur.emploi_canaux import emplois_par_mesure
from moteur.entreprises_cellules import arbitrage_tpe, bilan
from moteur.parametres import Parametres
from moteur.recettes.entreprises import is_beneficiaires
from moteur import noyau

RACINE = Path(__file__).resolve().parent.parent
ANS = (2029, 2037, 2050, 2073)

# (nom, tranches sans la dernière, seuil de la dernière tranche) ; le taux de la dernière est calé
BAREMES = [
    ("Taux réduit PME : 15 % jusqu'à 42 500 €, 30 % jusqu'à 250 000 €", [(0, 0.15), (42500, 0.30)], 250000),
    ("Trois paliers : 20 % jusqu'à 100 000 €, 35 % jusqu'à 5 M€", [(0, 0.20), (100000, 0.35)], 5_000_000),
    ("Doux : 25 % jusqu'à 42 500 €, 35 % jusqu'à 1 M€", [(0, 0.25), (42500, 0.35)], 1_000_000),
    ("Fort : 10 % jusqu'à 42 500 €, 25 % jusqu'à 500 000 €, 40 % jusqu'à 50 M€", [(0, 0.10), (42500, 0.25), (500000, 0.40)], 50_000_000),
]


def parametres(tranches) -> Parametres:
    return Parametres().avec({"entreprises.is_progressif": {"active": True, "tranches": [list(x) for x in tranches]}})


def caler(tranches, seuil) -> float:
    """Taux de la dernière tranche qui garde l'IS de l'État du budget statique (bissection)."""
    cible = is_beneficiaires(Parametres())
    lo, hi = 0.0, 0.95
    for _ in range(40):
        mid = (lo + hi) / 2
        if is_beneficiaires(parametres(list(tranches) + [(seuil, mid)])) < cible:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def mesurer(nom: str, p: Parametres, taux_haut: float | None = None) -> dict:
    prog = noyau.charger(p.programme)
    r = noyau.simuler(p, prog)
    pr, me = r["prudent"], r["median"]
    can = prog.canaux_courts(p, "prudent")
    e = emplois_par_mesure(p)
    loc = {j: e[j].get("entreprises_localisation", 0.0) for j in e}
    return {"bareme": nom, "taux_haut_etat": taux_haut,
            "is_etat_statique": round(is_beneficiaires(p) / 1e9, 1),
            "deficit_sans_regle": {t: round(pr[t]["deficit_sans_regle"], 2) for t in ANS},
            "deficit_publie": {t: round(pr[t]["deficit"], 2) for t in ANS},
            "dette_2073": round(pr[2073]["dette_pib"]),
            "chomage": {t: round(pr[t]["chomage"], 2) for t in ANS},
            "median_sans_regle": {t: round(me[t]["deficit_sans_regle"], 2) for t in ANS},
            "median_chomage": {t: round(me[t]["chomage"], 2) for t in ANS},
            "crise_publie_2073": round(r["crise"][2073]["deficit"], 2),
            "emplois_localisation": {j: round(v) for j, v in loc.items()},
            "salaires_dirigeants_perte": round(arbitrage_tpe(p)["perte"], 2),
            "ecart_par_taille": {x["taille"]: round(x["ecart"], 1) for x in bilan(p)},
            "canaux_2050": {**{k: round(can[c][2050], 2) for k, c in (("investissement_entreprises", "investissement"), ("erosion_is", "erosion_is"),
                                                               ("emploi", "emploi"), ("salaires_dirigeants", "dirigeants"))},
                            "emplois_fonds": round(pr[2050]["dynamiques"]["fonds"]["solde"], 2)}}


# barèmes non neutres (le haut reste à 40 % ou baisse) et taux uniques plus bas, pour situer
FIXES = [
    ("PME allégées, 40 % gardé au-delà de 250 000 € (15 / 30 / 40 %)", [(0, 0.15), (42500, 0.30), (250000, 0.40)]),
    ("25 % jusqu'à 100 000 €, 40 % au-delà", [(0, 0.25), (100000, 0.40)]),
    ("15 / 30 % jusqu'à 250 000 €, 35 % au-delà", [(0, 0.15), (42500, 0.30), (250000, 0.35)]),
]
UNIQUES = [0.35, 0.30]


def main() -> list[dict]:
    out = [mesurer("Taux unique de 40 % (programme)", Parametres(), 0.40)]
    for nom, tr, seuil in BAREMES:
        t = caler(tr, seuil)
        out.append(mesurer(nom + f", {round(100 * t, 1)} % au-delà (neutre)", parametres(list(tr) + [(seuil, t)]), round(t, 4)))
    for nom, tr in FIXES:
        out.append(mesurer(nom, parametres(tr), tr[-1][1]))
    for t in UNIQUES:
        out.append(mesurer(f"Taux unique de {round(100 * t)} %", Parametres().avec({"entreprises.taux_is_etat": t}), t))
    (RACINE / "sorties" / "is_progressif.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    for x in main():
        print(x["bareme"])
        print("   IS État statique", x["is_etat_statique"], " sans règle", x["deficit_sans_regle"], " publié", x["deficit_publie"], " dette73", x["dette_2073"])
        print("   chômage", x["chomage"], " médian", x["median_sans_regle"], x["median_chomage"], " crise73", x["crise_publie_2073"])
        print("   localisation", x["emplois_localisation"], " dirigeants", x["salaires_dirigeants_perte"], " tailles", x["ecart_par_taille"])
        print("   canaux 2050", x["canaux_2050"])
