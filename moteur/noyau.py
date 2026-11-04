"""Noyau commun : un programme = le statu quo + des mesures (4 novembre 2026).

Le noyau tient la comptabilité publique de 2029 à 2073 pour tous les programmes : recettes et dépenses par bloc du
statu quo (moteur/statu_quo.py), auxquelles un programme ajoute ses mesures, puis intérêts, dette et déficit au sens
de Maastricht, avec la même mécanique pour tous (taux apparent qui rejoint le taux de marché, effet de Fisher, prime
de taux liée à la dette).

Points d'entrée d'un programme :
- **mesures** : montants (Md€ de 2026, par scénario et par année) qui s'ajoutent à un poste : « recettes », un bloc
  de dépense du statu quo (statu_quo.BLOCS), un bloc nouveau (« nouveau:<nom> », dépense que le système actuel n'a
  pas, comme un revenu universel), ou « participations » (flux de dette hors solde, par exemple des
  participations de l'État remises à un fonds) ;
- **contexte** : ce que le programme change dans l'économie : PIB, inflation, taux d'intérêt en plus ou en moins
  (points), chômage, dette au 31 décembre 2028 (mesures de 2027-2028), PIB servant au ratio de la prime de dette.

Un programme vide (aucune mesure, aucun contexte) donne exactement le statu quo : c'est le même calcul.

Un programme est un objet avec un attribut `nom` et deux méthodes, `mesures(p)` → {scénario: [Mesure]} et
`contexte(p)` → {scénario: {clé: valeur}} (clés de CONTEXTE). Voir programmes/ecologie_de_droite/programme.py.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field

from .parametres import Parametres

ANNEES = list(range(2029, 2074))
POSTES = ("recettes", "participations")  # en plus des blocs de dépense du statu quo
CONTEXTE = ("pib", "pib_prime", "inflation", "taux_supplementaire", "chomage", "dette_depart")


@dataclass
class Mesure:
    """Une mesure : un montant par année sur un poste (Md€ de 2026 ; recettes : + = recette en plus ; bloc de
    dépense : + = dépense en plus ; participations : + = dette remboursée hors solde)."""
    nom: str
    poste: str
    valeurs: dict[int, float]
    nature: str = "mesure"  # mesure, effet_macro, methode (écart de méthode avec le statu quo, à résorber)
    note: str = ""


@dataclass
class ProgrammeVide:
    nom: str = "statu_quo"
    libelle: str = "Statu quo"

    def mesures(self, p: Parametres) -> dict[str, list[Mesure]]:
        return {}

    def contexte(self, p: Parametres) -> dict[str, dict]:
        return {}


def programmes_disponibles() -> list[str]:
    """Statu quo, puis chaque dossier programmes/<nom>/ qui a un programme.py (ordre alphabétique)."""
    from .parametres import RACINE
    noms = sorted(d.name for d in (RACINE / "programmes").iterdir() if (d / "programme.py").exists())
    return ["statu_quo"] + noms


def charger(nom: str):
    """Programme du dossier programmes/<nom>/ (module programme.py, fonction programme())."""
    if nom in ("statu_quo", "vide", None):
        return ProgrammeVide()
    return importlib.import_module(f"programmes.{nom}.programme").programme()


def _valider(m: Mesure) -> None:
    """Poste connu : recettes, participations, un bloc du statu quo, ou un bloc nouveau (« nouveau:<nom> »)."""
    from .statu_quo import BLOCS
    if m.poste not in POSTES + BLOCS and not m.poste.startswith("nouveau:"):
        raise ValueError(f"Mesure « {m.nom} » : poste inconnu {m.poste}")


def trajectoire(p: Parametres, s: str, mesures: list[Mesure] | None = None, contexte: dict | None = None) -> dict[int, dict]:
    """Comptes de chaque année d'un scénario : statu quo + mesures, dans le contexte du programme."""
    from . import statu_quo as sq
    mesures, ctx = mesures or [], contexte or {}
    for m in mesures:
        _valider(m)
    for k in ctx:
        if k not in CONTEXTE:
            raise ValueError(f"Contexte inconnu : {k}")
    y = ctx.get("pib") or sq.pib(p, s)
    y_prime = ctx.get("pib_prime") or y
    infl = ctx.get("inflation") or sq.inflation(p, s)
    sup = ctx.get("taux_supplementaire") or {}
    rec_sq, bl_sq = sq.recettes(p, s), sq.blocs(p, s)
    e = sq.effectifs(p, s)
    chom = ctx.get("chomage") or {t: e[t]["taux_chomage"] * 100 for t in ANNEES}
    infl_ref = p.val("calendrier.inflation")
    app0, lt = p.val("macro.taux_apparent_2029"), p.val("macro.taux_long_terme")
    n_lt, mat = p.val("macro.annees_taux_long_terme"), p.val("macro.maturite_moyenne_dette")
    prime_par_point = sq._v(p, "macro.prime_dette", s)
    fisher_actif = p.val("inflation.active") and p.val("inflation.effet_fisher")
    dette_prec = ctx.get("dette_depart") or sq.dette_fin_2028(p)
    fisher = prime = 0.0
    ratio_ref = None
    out = {}
    for t in ANNEES:
        bl = dict(bl_sq[t])
        rec = rec_sq[t]
        part = 0.0
        for m in mesures:
            v = m.valeurs.get(t, 0.0)
            if m.poste == "recettes":
                rec += v
            elif m.poste == "participations":
                part += v
            else:
                bl[m.poste] = bl.get(m.poste, 0.0) + v
        ratio = dette_prec / y_prime[t]
        ratio_ref = ratio if ratio_ref is None else ratio_ref
        prime += (prime_par_point * (ratio - ratio_ref) - prime) / mat
        if fisher_actif:
            fisher += ((infl[t] - infl_ref) - fisher) / mat
        nominal = min(lt, app0 + (lt - app0) * (t - 2029) / n_lt) + fisher + prime + sup.get(t, 0.0)
        interets_reels = (nominal - infl[t]) * dette_prec
        primaire = sum(bl.values())
        solde = rec - primaire - interets_reels
        dette = dette_prec - solde - part
        maastricht = (solde - infl[t] * dette_prec) / y[t]
        out[t] = {
            "pib": y[t], "recettes": rec, "depenses_primaires": primaire, "blocs": bl,
            "interets_reels": interets_reels, "charge_dette": interets_reels + infl[t] * dette_prec,
            "taux_apparent": nominal, "solde_primaire": rec - primaire, "solde": solde, "dette": dette,
            "participations": part, "deficit": -maastricht * 100, "dette_pib": dette / y[t] * 100,
            "chomage": chom[t], "inflation": infl[t] * 100,
            "retraites_pib": bl["retraites"] / y[t] * 100, "sante_pib": bl["sante"] / y[t] * 100,
            "recettes_pib": rec / y[t] * 100, "depenses_primaires_pib": primaire / y[t] * 100,
        }
        dette_prec = dette
    return out


def simuler(p: Parametres | None = None, programme=None) -> dict[str, dict[int, dict]]:
    """Les quatre scénarios d'un programme (statu quo si programme est None)."""
    from .statu_quo import SCENARIOS
    p = p or Parametres()
    programme = programme or ProgrammeVide()
    mes, ctx = programme.mesures(p), programme.contexte(p)
    return {s: trajectoire(p, s, mes.get(s), ctx.get(s)) for s in SCENARIOS}


def bilan_mesures(programme, p: Parametres, s: str = "prudent", annees=(2029, 2037, 2050, 2073)) -> list[dict]:
    """Effet de chaque mesure sur le solde (Md€ ; + = améliore le solde), pour la restitution."""
    out = []
    for m in programme.mesures(p).get(s, []):
        signe = 1 if m.poste == "recettes" else (0 if m.poste == "participations" else -1)
        out.append({"nom": m.nom, "poste": m.poste, "nature": m.nature,
                    **{t: signe * m.valeurs.get(t, 0.0) for t in annees}})
    return out


if __name__ == "__main__":
    import sys
    from .statu_quo import SCENARIOS, simuler as simuler_sq
    nom = sys.argv[1] if len(sys.argv) > 1 else "ecologie_de_droite"
    p = Parametres()
    prog = charger(nom)
    res, sq = simuler(p, prog), simuler_sq(p)
    annees = (2029, 2037, 2050, 2073)
    print(f"{nom} contre le statu quo (prudent) — effet de chaque mesure sur le solde (Md€ de 2026, + = mieux)")
    for x in sorted(bilan_mesures(prog, p, annees=annees), key=lambda x: -abs(x[2050])):
        print(f"  {x['nature']:<12}" + "".join(f"{x[t]:9.1f}" for t in annees) + f"  {x['nom']}")
    print("Déficit (% du PIB) : programme / statu quo")
    for s in SCENARIOS:
        print(f"  {s:<10}" + "  ".join(f"{t} : {res[s][t]['deficit']:.2f} / {sq[s][t]['deficit']:.2f}" for t in annees[:3]))
