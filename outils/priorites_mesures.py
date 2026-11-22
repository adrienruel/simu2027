"""Roadmap 7.2 et 7.3 (22/11/2026) : fiche de chaque mesure et ordre de travail des programmes.

Pour chaque mesure de chaque programme publié :
- le texte cité (`mesures.yaml` : intitulé, source, traitement) ;
- la lecture retenue (instrument, statut et source du chiffrage, depuis `parametres.yaml`) ;
- son effet sur le solde en 2037 au prudent et dans les quatre scénarios, en points de PIB, calculé par le noyau (toutes
  les lignes de la mesure, retours d'IS et bénéfices déplacés compris) ;
- si elle est codée dans la microsimulation des ménages (`micro_mesures.yaml`) ou des entreprises ;
- ses fragilités : chiffrage sans source (statut HYPOTHESE ou DECISION), lecture d'une mesure floue (traitement ou
  source qui parle de lecture), non codée dans la micro, montant identique dans les quatre scénarios.

Priorité = |effet au prudent| × (1 + nombre de fragilités). Le classement des programmes somme les priorités de leurs
mesures.

    python -m outils.priorites_mesures   → sorties/fiches_mesures.csv, sorties/priorites_mesures.csv,
                                           sorties/priorites_programmes.csv
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import yaml

from moteur import noyau
from moteur.parametres import Parametres
from moteur.statu_quo import SCENARIOS

RACINE = Path(__file__).resolve().parents[1]
SORTIES = RACINE / "sorties"
T = 2037


def _entrees(arbre, chemin=()):
    """(clé, entrée de paramètre, spécification de mesure) pour chaque mesure déclarée dans parametres.yaml."""
    if isinstance(arbre, dict):
        v = arbre.get("valeur")
        specs = [v] if isinstance(v, dict) and "id" in v else ([x for x in v if isinstance(x, dict) and "id" in x]
                                                               if isinstance(v, list) else [])
        for sp in specs:
            yield ".".join(chemin), arbre, sp
        for k, x in arbre.items():
            if k != "valeur":
                yield from _entrees(x, chemin + (str(k),))


def _ident(nom: str) -> str:
    return nom.split(" — ", 1)[0].strip()


def fiches(p: Parametres | None = None) -> list[dict]:
    p = p or Parametres()
    micro = yaml.safe_load((RACINE / "programmes" / "micro_mesures.yaml").read_text(encoding="utf-8")) or {}
    micro_e = yaml.safe_load((RACINE / "programmes" / "micro_entreprises.yaml").read_text(encoding="utf-8")) or {}
    pib = {s: noyau.simuler(p, None, scenarios=(s,))[s][T]["pib"] for s in SCENARIOS}
    out = []
    for nom in [n for n in noyau.programmes_disponibles() if (RACINE / "programmes" / n / "parametres.yaml").exists()]:
        d = RACINE / "programmes" / nom
        texte = {}
        if (d / "mesures.yaml").exists():
            for m in (yaml.safe_load((d / "mesures.yaml").read_text(encoding="utf-8")) or {}).get("mesures", []):
                texte[m["id"]] = m
        lecture = {}
        for cle, ent, sp in _entrees(yaml.safe_load((d / "parametres.yaml").read_text(encoding="utf-8")) or {}):
            lecture.setdefault(sp["id"], (cle, ent, sp))
        prog = noyau.charger(nom)
        ms = prog.mesures(p)
        effet = {s: defaultdict(float) for s in SCENARIOS}
        for s in SCENARIOS:
            for m in ms[s]:
                if m.poste == "participations" or getattr(m, "nature", "") == "physique":
                    continue  # achats d'actifs (dette, pas solde) et lignes en effectifs
                i = _ident(m.nom)
                v = m.valeurs.get(T, 0.0)
                effet[s][i] += (v if m.poste == "recettes" else -v) / pib[s] * 100
        ids = list(dict.fromkeys(list(texte) + [i for i in effet["prudent"] if i in lecture or i in texte]))
        codees = set((micro.get(nom) or {}).keys()) | set((micro_e.get(nom) or {}).keys())
        for i in ids:
            t = texte.get(i, {})
            cle, ent, sp = lecture.get(i, ("", {}, {}))
            src = " ".join(str(x) for x in (ent.get("source", ""), ent.get("note", ""), t.get("traitement", "")))
            mont = sp.get("montant") if isinstance(sp.get("montant"), dict) else None
            frag = {
                "sans_source": bool(ent) and ent.get("statut") in ("HYPOTHESE", "DECISION"),
                "lecture": "lecture" in src.lower() or "lectures_communes" in src,
                "non_codee_micro": i not in codees and sp.get("instrument") in (
                    "transferts_actifs", "travail", "capital_menages", "consommation", "successions"),
                "identique_scenarios": mont is not None and len({round(float(x), 6) for x in mont.values()}) == 1,
            }
            e = {s: effet[s].get(i, 0.0) for s in SCENARIOS}
            out.append({
                "programme": nom, "id": i, "intitule": t.get("intitule", sp.get("libelle", "")),
                "citation": t.get("source", ""), "traitement": t.get("traitement", ""), "parametre": cle,
                "instrument": sp.get("instrument", ""), "statut": ent.get("statut", ""),
                "source_chiffrage": ent.get("source", ""),
                **{f"effet_{s}_pt_pib": round(e[s], 4) for s in SCENARIOS},
                "codee_micro": i in codees, **frag, "fragilites": sum(frag.values()),
                "priorite": round(abs(e["prudent"]) * (1 + sum(frag.values())), 4),
            })
    return out


def ecrire(lignes: list[dict]) -> list[Path]:
    SORTIES.mkdir(exist_ok=True)
    f1, f2, f3 = (SORTIES / n for n in ("fiches_mesures.csv", "priorites_mesures.csv", "priorites_programmes.csv"))
    with f1.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    tri = sorted((x for x in lignes if x["priorite"] > 0), key=lambda x: -x["priorite"])
    champs = ["rang", "programme", "id", "intitule", "effet_prudent_pt_pib", "fragilites", "sans_source", "lecture",
              "non_codee_micro", "identique_scenarios", "priorite"]
    with f2.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        for k, x in enumerate(tri, 1):
            w.writerow({"rang": k, **x})
    par = defaultdict(lambda: [0.0, 0, 0])
    for x in lignes:
        par[x["programme"]][0] += x["priorite"]
        par[x["programme"]][1] += 1
        par[x["programme"]][2] += x["fragilites"] > 0
    with f3.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rang", "programme", "priorite_totale", "mesures", "mesures_fragiles"])
        for k, (n, v) in enumerate(sorted(par.items(), key=lambda kv: -kv[1][0]), 1):
            w.writerow([k, n, round(v[0], 3), v[1], v[2]])
    from outils import trace
    trace.enregistrer([f.name for f in (f1, f2, f3)], script="outils.priorites_mesures")
    return [f1, f2, f3]


if __name__ == "__main__":
    for f in ecrire(fiches()):
        print(f.relative_to(RACINE))
