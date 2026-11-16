"""Économies et recettes nommées de chaque programme publié, scénario par scénario (roadmap du comparateur, 2.1).

Règle d'Adrien : on ne reprend jamais le chiffre d'un candidat ; chaque économie ou recette nommée est estimée par le
modèle, scénario par scénario, avec sa source. Ce tableau montre, pour chaque mesure, le montant retenu dans chaque
scénario (Md€ de 2026, économie de 2029, à plein effet), le rapport prudent / optimiste, le statut et la présence d'une
source. Les prises de participation (nationalisations) n'en font pas partie : ce sont des achats d'actifs, pas des
économies. Écrit sorties/comparaison_economies.csv.

    python -m outils.audit_economies
"""
from __future__ import annotations

import csv

from moteur import noyau
from moteur.parametres import RACINE, Parametres

SCENARIOS = ("crise", "prudent", "median", "optimiste")


def lignes() -> list[dict]:
    out = []
    for nom in noyau.programmes_disponibles()[1:]:
        q = Parametres(programme=nom)
        lib = getattr(noyau.charger(nom), "libelle", nom)
        for cle, par in q._p.items():
            if not cle.startswith(f"{nom}_mesures."):
                continue
            x = par.valeur
            m = x.get("montant")
            mt = {s: (m[s] if isinstance(m, dict) else m) for s in SCENARIOS}
            if not all(isinstance(v, (int, float)) for v in mt.values()) or x.get("poste") == "participations":
                continue
            if x.get("poste") == "recettes":
                sens = "recette" if mt["prudent"] > 0 else None
            else:
                sens = "economie" if mt["prudent"] < 0 else None
            if sens is None:
                continue
            out.append({"programme": lib, "dossier": nom, "cle": cle, "id": x.get("id", ""), "mesure": x.get("libelle", ""),
                        "poste": x.get("poste"), "sens": sens, **{f"{s}_md": round(abs(mt[s]), 3) for s in SCENARIOS},
                        "prudent_sur_optimiste": round(abs(mt["prudent"]) / abs(mt["optimiste"]), 3) if mt["optimiste"] else "",
                        "par_scenario": isinstance(m, dict), "statut": par.statut, "source": bool(par.source),
                        "note": bool(par.note)})
    return out


def main() -> None:
    ls = lignes()
    f = RACINE / "sorties" / "comparaison_economies.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ls[0]))
        w.writeheader()
        w.writerows(ls)
    from outils import trace
    trace.enregistrer(f, script="outils.audit_economies")
    print(f"Écrit : {f} ({len(ls)} mesures)")
    par = {}
    for l in ls:
        k = (l["programme"], l["sens"])
        a = par.setdefault(k, {s: 0.0 for s in SCENARIOS} | {"n": 0, "sans_source": 0})
        a["n"] += 1
        a["sans_source"] += not l["source"]
        for s in SCENARIOS:
            a[s] += l[f"{s}_md"]
    for (prog, sens), a in sorted(par.items()):
        print(f"  {prog[:30]:30s} {sens:8s} {a['n']:3d} mesures  crise {a['crise']:6.1f}  prudent {a['prudent']:6.1f}  "
              f"médian {a['median']:6.1f}  optimiste {a['optimiste']:6.1f}  prudent/optimiste "
              f"{a['prudent'] / a['optimiste']:.2f}  sans source {a['sans_source']}")


if __name__ == "__main__":
    main()
