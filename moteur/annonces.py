"""Variante « annonce tenue » (12/11/2026, demande d'Adrien) : ce que donnerait le programme si les montants annoncés
par le candidat (programmes/annonces.yaml) étaient atteints, effets économiques compris.

Le chiffrage officiel ne reprend jamais ces montants. La variante ajoute seulement, à côté des mesures du programme,
l'écart entre l'annonce et ce que le modèle retient en 2032, comme des mesures ordinaires : elles passent par le même
multiplicateur (une dépense en moins réduit l'activité, donc la TVA et les autres recettes), le même canal d'offre
(instrument de la mesure d'origine), les mêmes intérêts. Elle n'est calculée que si le programme porte
`variante_annonces = True` (outils/export_comparaison.py) : aucun résultat publié par ailleurs ne change.

- annonce d'économies d'ensemble : l'écart (annonce − économies nommées − enveloppe retenue) est réparti entre les
  domaines que le programme vise (<nom>_enveloppe.intensite × capacité des précédents), sur les mêmes postes et au même
  rythme que l'enveloppe ;
- annonce pour une mesure précise : l'écart suit le profil et l'instrument de la plus grosse ligne de la mesure.
"""
from __future__ import annotations

from functools import lru_cache

import yaml

from . import statu_quo as sq
from .noyau import ANNEES, Mesure
from .parametres import RACINE, Parametres

ANNEE = 2032  # fin du quinquennat : horizon des annonces
ANNEES_AVANT = (2027, 2028)


@lru_cache(maxsize=1)
def liste() -> tuple:
    return tuple(yaml.safe_load((RACINE / "programmes" / "annonces.yaml").read_text(encoding="utf-8"))["annonces"])


def _signe(m: Mesure) -> int:
    return 1 if m.poste == "recettes" else -1


def retenu(a: dict, mesures: list[Mesure], enveloppe: dict | None) -> float:
    """Ce que le modèle retient en 2032 pour l'annonce a (Md€, + = améliore le solde)."""
    if a["type"] == "economies":
        e = enveloppe or {}
        return e.get("nommees", 0.0) + e.get("retenu", 0.0)
    return sum(_signe(m) * m.valeurs.get(ANNEE, 0.0) for m in mesures
               if m.nature != "effet_macro" and any(m.nom.startswith(pr) for pr in a["prefixes"]))


def mesures_tenues(nom: str, p: Parametres, s: str, mesures: list[Mesure], enveloppe: dict | None,
                   intensite: dict | None = None, debut: int = 2028, plein: int = 2032) -> list[Mesure]:
    """Mesures à ajouter pour que chaque annonce du programme `nom` soit tenue en 2032."""
    out = []
    y = sq.pib(p, s)
    for a in liste():
        if a["programme"] != nom:
            continue
        ecart = float(a["montant"]) - retenu(a, mesures, enveloppe)
        if ecart <= 0:
            continue
        if a["type"] == "economies":
            dom = p.val("enveloppe_economies.domaines")
            inten = intensite or {}
            poids = {n: d["capacite"][s] * inten.get(n, 0.0) for n, d in dom.items()}
            if sum(poids.values()) <= 0:
                poids = {n: inten.get(n, 0.0) for n in dom} if any(inten.values()) else {n: 1.0 for n in dom}
            tot = sum(poids.values())

            def mont(t):
                return min(1.0, max(0.0, (t - debut + 1) / (plein - debut + 1)))
            for n, w in poids.items():
                if w <= 0:
                    continue
                for poste, part in dom[n]["postes"].items():
                    v = -ecart * w / tot * part
                    out.append(Mesure(f"Annonce tenue : économies annoncées non démontrées ({dom[n]['libelle']}, {poste})",
                                      poste, {**{t: v * mont(t) for t in ANNEES_AVANT},
                                              **{t: v * mont(t) * y[t] / y[plein] for t in ANNEES}}, note="annonce"))
        else:
            lignes = [m for m in mesures if m.nature != "effet_macro" and any(m.nom.startswith(pr) for pr in a["prefixes"])
                      and abs(m.valeurs.get(ANNEE, 0.0)) > 1e-9]
            if not lignes:
                continue
            m0 = max(lignes, key=lambda m: abs(m.valeurs.get(ANNEE, 0.0)))
            base = m0.valeurs[ANNEE]
            out.append(Mesure(f"Annonce tenue : {a['libelle']}", m0.poste,
                              {t: _signe(m0) * ecart * v / base for t, v in m0.valeurs.items()},
                              note="annonce", instrument=m0.instrument, incidence=m0.incidence))
    return out
