"""Couverture du budget « ménages » par la microsimulation (roadmap du comparateur, phase 4.2, 18/11/2026).

Les déciles de niveau de vie d'un programme ne disent quelque chose que si la microsimulation y voit l'essentiel de ce
que le programme change pour les ménages. Règle : déciles publiés seulement si les mesures codées dans OpenFisca
(programmes/micro_mesures.yaml) couvrent au moins publication.seuil_couverture_deciles (80 %) du budget « ménages »
du programme.

Budget « ménages » : mesures du programme (nature « mesure », hors lignes dérivées : prélèvements sur les
rémunérations publiques, retour d'IS des charges) qui touchent directement le revenu des ménages :
- recettes dont l'instrument est un prélèvement des ménages (travail, capital des ménages, successions, consommation,
  transferts aux actifs) ;
- dépenses des blocs de transferts aux ménages (retraites, chômage, famille, logement, pauvreté, AAH et invalidité).
Chaque mesure compte en valeur absolue (une hausse et une baisse ne se compensent pas), au scénario prudent de
l'année publication.annee_couverture_deciles. Une mesure est codée si son identifiant a une entrée dans
micro_mesures.yaml (« REC-20/21 » couvre REC-20 et REC-21).

    python -m outils.couverture_micro        # sorties/comparaison_couverture_micro.csv
"""
from __future__ import annotations

import yaml

from moteur import noyau
from moteur.parametres import RACINE, Parametres

POSTES_MENAGES = ("retraites", "chomage", "famille", "logement", "pauvrete", "aah_invalidite")
INSTRUMENTS_MENAGES = ("travail", "capital_menages", "successions", "consommation", "transferts_actifs")
LIGNES_DERIVEES = ("prélèvements sur", "impôt sur les sociétés : charges")


def identifiants_codes(nom: str, specs: dict | None = None) -> set[str]:
    """Identifiants des mesures d'un programme codées dans la microsimulation."""
    if specs is None:
        specs = yaml.safe_load((RACINE / "programmes" / "micro_mesures.yaml").read_text(encoding="utf-8"))
    out = set()
    for k in (specs.get(nom) or {}):
        tete, _, suites = k.partition("/")
        out.add(tete)
        racine = tete.rsplit("-", 1)[0]
        for x in filter(None, suites.split("/")):
            out.add(f"{racine}-{x}")
    return out


def est_menages(m) -> bool:
    if m.nature != "mesure" or " — " not in m.nom:
        return False
    if m.nom.partition(" — ")[2].startswith(LIGNES_DERIVEES):
        return False
    return m.poste in POSTES_MENAGES or (m.poste == "recettes" and m.instrument in INSTRUMENTS_MENAGES)


def couverture(p: Parametres, nom: str, prog=None, specs: dict | None = None) -> dict:
    """Budget « ménages » (Md€), part codée et mesures non codées les plus lourdes d'un programme."""
    prog = prog or noyau.charger(nom)
    t = int(p.val("publication.annee_couverture_deciles"))
    codes = identifiants_codes(nom, specs)
    total = code = 0.0
    manquantes = []
    for m in prog.mesures(p)["prudent"]:
        if not est_menages(m):
            continue
        v = abs(m.valeurs.get(t, 0.0))
        total += v
        ident = m.nom.partition(" — ")[0]
        if ident in codes:
            code += v
        elif v > 0:
            manquantes.append((v, m.nom))
    part = code / total if total else 0.0
    manquantes.sort(reverse=True)
    return {"programme": nom, "annee": t, "budget_menages_md": total, "budget_code_md": code, "part_codee": part,
            "deciles_publies": part >= p.val("publication.seuil_couverture_deciles"),
            "manquantes": manquantes}


def toutes(p: Parametres | None = None) -> dict[str, dict]:
    p = p or Parametres()
    specs = yaml.safe_load((RACINE / "programmes" / "micro_mesures.yaml").read_text(encoding="utf-8"))
    return {nom: couverture(p, nom, specs=specs) for nom in noyau.programmes_disponibles()[1:]}


def main() -> None:
    import csv
    from outils import trace
    lignes = []
    for nom, c in toutes().items():
        lignes.append({"programme": nom, "annee": c["annee"], "budget_menages_md": round(c["budget_menages_md"], 2),
                       "budget_code_md": round(c["budget_code_md"], 2), "part_codee_pct": round(c["part_codee"] * 100, 1),
                       "deciles_publies": int(c["deciles_publies"]),
                       "plus_lourdes_non_codees": " ; ".join(f"{n} ({v:.1f})" for v, n in c["manquantes"][:5])})
    with (RACINE / "sorties" / "comparaison_couverture_micro.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    trace.enregistrer("comparaison_couverture_micro.csv", script="outils.couverture_micro")
    for x in lignes:
        print(f"{x['programme']:12s} {x['part_codee_pct']:5.1f} %  {'publiés' if x['deciles_publies'] else 'non publiés'}")


if __name__ == "__main__":
    main()
