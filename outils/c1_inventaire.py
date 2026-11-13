"""Phase C1 de la roadmap (13/11/2026) : hypothèses sans source, classées par poids sur le déficit de 2037.

Pour chaque paramètre au statut HYPOTHESE sans champ « source » : +10 % (sous-champ par sous-champ, comme
moteur/sensibilite.py), écart de déficit (points de PIB) en 2037 et 2050 au prudent, sans règle de trajectoire.
- paramètres communs : sur le statu quo ;
- paramètres d'un programme : sur ce programme.

    python -m outils.c1_inventaire [programme]      # écrit sorties/c1_<programme ou commun>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from moteur import noyau
from moteur.parametres import ErreurParametre, Parametres
from moteur.sensibilite import _cibles, _numerique, _variante

RACINE = Path(__file__).resolve().parent.parent


def _deficit(p: Parametres, programme: str | None, q: Parametres | None = None) -> dict:
    """q : paramètres propres d'un programme qui les lit à part (attribut pt : Tondelier, programmes simples)."""
    prog = noyau.charger(programme) if programme else None
    if q is not None:
        prog.pt = q
    r = noyau.simuler(p, prog, scenarios=("prudent",), contrefactuel=False)["prudent"]
    return {t: r[t]["deficit"] for t in (2037, 2050)}


def _est_une_date(valeur, chemin: tuple) -> bool:
    """Sous-champ année (debut, plein…) ou valeur entière entre 1990 et 2100 : +10 % n'a pas de sens."""
    v = valeur
    for c in chemin:
        v = v[c]
    return (bool(chemin) and str(chemin[-1]) in ("debut", "plein", "fin", "annee")) or (
        isinstance(v, int) and 1990 <= v <= 2100)


def _sans_clause(p: Parametres) -> Parametres:
    try:
        return p.avec({"clause.active": False})
    except ErreurParametre:  # pas de règle de trajectoire dans ces paramètres
        return p


def inventaire(programme: str | None) -> list[dict]:
    a_part = programme is not None and hasattr(noyau.charger(programme), "pt")
    if a_part:  # le moteur tourne sur les paramètres communs, le programme lit les siens (pt)
        p, q = _sans_clause(Parametres()), Parametres(programme=programme)
    else:
        p, q = _sans_clause(Parametres(programme=programme or "ecologie_de_droite")), None
    base = _deficit(p, programme, q)
    cibles = q if a_part else p
    out = []
    for x in cibles:
        origine = str(cibles.origine[x.cle])
        dans = (f"programmes/{programme}/" in origine) if programme else ("parametres/commun" in origine)
        if not dans or x.statut != "HYPOTHESE" or x.source or x.unite == "annee" or not _numerique(x.valeur):
            continue
        for chemin in _cibles(x):
            if _est_une_date(x.valeur, chemin):
                continue
            nom = "/".join((x.cle,) + tuple(str(c) for c in chemin))
            try:
                if a_part:
                    v = _deficit(p, programme, _variante(q, x.cle, 1.1, chemin))
                else:
                    v = _deficit(_variante(p, x.cle, 1.1, chemin), programme)
                out.append({"cle": nom, "deficit_2037": v[2037] - base[2037], "deficit_2050": v[2050] - base[2050],
                            "note": (x.note or "")[:300]})
            except Exception as e:
                out.append({"cle": nom, "erreur": str(e)[:160]})
    return sorted(out, key=lambda r: -abs(r.get("deficit_2037", 0.0)))


if __name__ == "__main__":
    nom = sys.argv[1] if len(sys.argv) > 1 else None
    res = inventaire(nom)
    f = RACINE / "sorties" / f"c1_{nom or 'commun'}.json"
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Écrit : {f} ({len(res)} variantes)")
