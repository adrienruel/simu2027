"""Contrôle micro/macro de toutes les mesures passées dans OpenFisca (audit I5, 27/11/2026).

sorties/micro_mesures.csv ne compare au moteur que les mesures codées en montant (`*_mesures.*`) : pour les mesures
calculées par une fonction (SMIC, âge de départ, cotisations…), `moteur_md` vaut 0 et l'écart est vide. Ce script
prend le montant du moteur dans `noyau.bilan_mesures` (toutes les lignes dont le nom commence par l'identifiant, donc
avec les prélèvements induits), scénario prudent, et écrit sorties/controle_micro_macro.csv.

Comparaison : OpenFisca chiffre la mesure à plein effet sur l'économie de 2026, que le moteur place en 2029. Le
montant du moteur retenu est le plus grand en valeur absolue entre 2029 et 2037 ramené à l'économie de 2029 (divisé
par le PIB nominal du statu quo rapporté à 2029) : une mesure qui monte en charge (retraites) est ainsi lue à son
plein effet, sans l'effet de la croissance. Les mesures dont l'écart dépasse SEUIL doivent figurer dans
parametres/controles/ecarts_micro_macro.yaml avec la raison de l'écart (tests/test_controle_micro_macro.py).
"""
from __future__ import annotations

import csv
from pathlib import Path

from moteur import noyau
from moteur import statu_quo as sq
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "sorties" / "controle_micro_macro.csv"
SEUIL = 0.30  # écart relatif admis sans explication
PLANCHER_MD = 0.5  # en dessous, l'écart relatif n'a pas de sens
ANNEES = range(2029, 2038)
S = "prudent"


def montants_moteur(nom: str) -> dict[str, float]:
    """Identifiant → effet sur le solde (Md€, + = l'améliore) à plein effet, économie de 2029."""
    p = Parametres(programme=nom)
    pib = sq.pib(p, S)
    par_id: dict[str, dict[int, float]] = {}
    for x in noyau.bilan_mesures(noyau.charger(nom), p, S, annees=tuple(ANNEES)):
        ident, sep, _ = x["nom"].partition(" — ")
        if not sep:
            continue
        serie = par_id.setdefault(ident.strip(), {t: 0.0 for t in ANNEES})
        for t in ANNEES:
            serie[t] += x[t] * pib[2029] / pib[t]
    return {i: max(v.values(), key=abs) for i, v in par_id.items()}


def lignes() -> list[dict]:
    micro = list(csv.DictReader((RACINE / "sorties" / "micro_mesures.csv").open(encoding="utf-8")))
    cache: dict[str, dict[str, float]] = {}
    out = []
    for r in micro:
        nom = r["programme"]
        if nom not in cache:
            cache[nom] = montants_moteur(nom)
        of = float(r["openfisca_md"])
        mot = cache[nom].get(r["mesure"])
        ecart = (of / mot - 1) if mot is not None and abs(mot) >= PLANCHER_MD else None
        out.append({"programme": nom, "mesure": r["mesure"], "openfisca_md": round(of, 2),
                    "moteur_md": "" if mot is None else round(mot, 2),
                    "ecart_pct": "" if ecart is None else round(ecart * 100),
                    "hors_seuil": "1" if ecart is not None and abs(ecart) > SEUIL else "0"})
    return out


def main() -> None:
    rows = lignes()
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    hors = [r for r in rows if r["hors_seuil"] == "1"]
    print(f"{len(rows)} mesures, {sum(r['ecart_pct'] != '' for r in rows)} comparées, {len(hors)} au-delà de {SEUIL:.0%}")
    for r in sorted(hors, key=lambda r: -abs(r["openfisca_md"])):
        print(f"  {r['programme']:11s} {r['mesure']:12s} OpenFisca {r['openfisca_md']:+7.1f}  moteur {r['moteur_md']:+7.1f}  {r['ecart_pct']:+d} %")
    from outils import trace
    trace.enregistrer(SORTIE.name, script="outils.controle_micro_macro")


if __name__ == "__main__":
    main()
