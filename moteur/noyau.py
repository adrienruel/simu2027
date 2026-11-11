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
  (points), chômage, dette au 31 décembre 2028 (mesures de 2027-2028). La prime de dette est calculée par le noyau seul.

Un programme vide (aucune mesure, aucun contexte) donne exactement le statu quo : c'est le même calcul.

Deux mécanismes génériques servent aux programmes dont des flux dépendent du déficit lui-même (12 novembre 2026) :
- **dynamiques** : objets à état, un par scénario, appelés chaque année (`debut(t, etat)` rend des flux en plus du
  statu quo : PIB, recettes, blocs de dépense, participations, emplois, chômage ; `fin(t, etat)` les met à jour une
  fois les comptes de l'année connus). Exemple : un fonds dont le capital grossit avec l'épargne et rapporte au PIB ;
- **règle de trajectoire** (`Regle`) : cible de déficit (points de PIB) atteinte par des leviers ordonnés, chacun avec
  sa capacité du moment et son rendement au solde. Le noyau fait l'arithmétique (écart à la cible, remplissage des
  leviers dans l'ordre, écritures budgétaires) ; ce que chaque levier fait ensuite (effet récessif, créances) est
  dans le levier. Le noyau publie les comptes avec et sans la règle.
Un programme qui en a besoin fournit `entrees(p)` → {scénario: Entree} au lieu de `mesures` et `contexte` seuls.

Un programme est un objet avec un attribut `nom` et deux méthodes, `mesures(p)` → {scénario: [Mesure]} et
`contexte(p)` → {scénario: {clé: valeur}} (clés de CONTEXTE). Voir programmes/ecologie_de_droite/programme.py.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Callable

from .parametres import Parametres

ANNEES = list(range(2029, 2074))
POSTES = ("recettes", "participations")  # en plus des blocs de dépense du statu quo
CONTEXTE = ("pib", "inflation", "taux_supplementaire", "chomage", "dette_depart", "emploi", "emplois_canaux",
            "pib_hors_consommation")
# pib_hors_consommation : {année: Md€} part du PIB du programme qui ne va pas à la consommation des ménages (épargne
# retenue, investissement), retirée du PIB pour les émissions importées, qui suivent la consommation
# emploi : personnes en emploi, année par année ; emplois_canaux : {année: {canal: emplois en plus (+) ou en moins (−)
# par rapport au statu quo}}, pour la restitution (la somme n'a pas à retrouver l'écart d'emploi : le reste est publié)


@dataclass
class Mesure:
    """Une mesure : un montant par année sur un poste (Md€ de 2026 ; recettes : + = recette en plus ; bloc de
    dépense : + = dépense en plus ; participations : + = dette remboursée hors solde)."""
    nom: str
    poste: str
    valeurs: dict[int, float]
    nature: str = "mesure"  # mesure, effet_macro, methode (écart de méthode avec le statu quo, à résorber), physique
    note: str = ""
    # effets physiques, sans montant (moteur/ecologie/emissions.py) : {"emissions_mt:<secteur>": {année: Mt}, ...}
    physique: dict[str, dict[int, float]] = field(default_factory=dict)
    vert: str = ""  # classement du budget vert : favorable, defavorable, mixte, neutre ("" : non classé)
    # instrument du canal d'offre commun (moteur/offre.py) : travail, cout_travail, capital_entreprises,
    # capital_menages, successions, consommation, transferts_actifs ("" : pas d'effet d'offre)
    instrument: str = ""
    # incidence d'une mesure sur le travail (instrument « travail ») : proportionnel, ir, bas, haut (moteur/offre.py)
    incidence: str = ""


@dataclass
class Levier:
    """Un levier de la règle de trajectoire.

    capacite(t, etat) : quantité maximale utilisable cette année (unités du levier : Md€) ;
    rendement : solde gagné par unité utilisée (1 pour une recette, moins de 1 si l'unité fait perdre de la TVA) ;
    ecritures(t, x) : [(poste, montant)] écrits dans les comptes pour x unités, mêmes conventions que les mesures
    (défaut : x × rendement de recettes) ;
    appliquer(t, x, etat) : suite propre au levier (historique, créances, retrait du capital d'un fonds…) ;
    detail(t, x, etat) : grandeurs à publier avec le levier (points de contribution, euros de revenu universel…)."""
    nom: str
    capacite: Callable
    rendement: float = 1.0
    ecritures: Callable | None = None
    appliquer: Callable | None = None
    detail: Callable | None = None


@dataclass
class Regle:
    """Règle de trajectoire : ramène le déficit au sens de Maastricht à `cible` (points de PIB) en remplissant les
    leviers dans l'ordre, jusqu'en `derniere_annee`. `automatiques` : fonctions (t, etat, declenchee) → solde (Md€,
    écrit en recettes) qui jouent d'elles-mêmes dès que la règle est déclenchée (déficit au-dessus de la cible la
    première année) et que les leviers déduisent de ce qu'ils ont à couvrir."""
    cible: float
    leviers: list
    derniere_annee: int = 2073
    automatiques: list = field(default_factory=list)
    declenchee: float | None = None


@dataclass
class Entree:
    """Ce qu'un programme donne au noyau pour un scénario."""
    mesures: list
    contexte: dict = field(default_factory=dict)
    dynamiques: list = field(default_factory=list)
    regle: Regle | None = None


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


def prime_marche(p: Parametres, s: str, ratio: float, ratio_ref: float) -> float:
    """Prime de taux de marché liée à la dette (taux) : prime_dette par point de dette/PIB au-dessus ou au-dessous
    de la référence, bornée (macro.prime_dette_bornes). Une dette négative compte pour zéro : l'État qui détient des
    actifs ne prête pas au taux de sa propre signature diminué d'une prime."""
    from .statu_quo import _v
    bas, haut = p.val("macro.prime_dette_bornes")
    brute = _v(p, "macro.prime_dette", s) * (max(ratio, 0.0) - ratio_ref)
    return max(bas, min(haut, brute))


def ecart_taux_borne(p: Parametres, prime: float, supplement: float) -> float:
    """Prime de dette + écart de taux propre à un programme, dont la baisse totale ne peut dépasser l'écart de
    l'OAT au Bund (borne basse de macro.prime_dette_bornes) : la crédibilité ne fait pas passer sous le taux
    allemand, et la prime de dette et une baisse d'écart décidée par un programme ne se cumulent pas au-delà."""
    return max(p.val("macro.prime_dette_bornes")[0], prime + supplement)


def ratio_reference(p: Parametres, s: str) -> float:
    """Dette/PIB de référence de la prime : celle du statu quo en 2029, commune à tous les programmes."""
    from . import statu_quo as sq
    return sq.dette_fin_2028(p) / sq.pib(p, s)[2029]


def trajectoire(p: Parametres, s: str, mesures: list[Mesure] | None = None, contexte: dict | None = None,
                dynamiques=(), regle: Regle | None = None) -> dict[int, dict]:
    """Comptes de chaque année d'un scénario : statu quo + mesures, dans le contexte du programme.

    Chaque année : flux des dynamiques → PIB, recettes et blocs → mesures → intérêts → règle de trajectoire (si le
    programme en a une) → dette et déficit → mise à jour des dynamiques. Les comptes publiés contiennent ce que la
    règle a fait (`regle`) et le déficit qu'on aurait eu sans elle (`deficit_sans_regle`)."""
    from . import statu_quo as sq
    mesures, ctx = mesures or [], contexte or {}
    for m in mesures:
        _valider(m)
    for k in ctx:
        if k not in CONTEXTE:
            raise ValueError(f"Contexte inconnu : {k}")
    y_base = ctx.get("pib") or sq.pib(p, s)
    y = dict(y_base)
    infl = ctx.get("inflation") or sq.inflation(p, s)
    sup = ctx.get("taux_supplementaire") or {}
    rec_sq, bl_sq = sq.recettes(p, s), sq.blocs(p, s)
    e = sq.effectifs(p, s)
    chom = ctx.get("chomage") or {t: e[t]["taux_chomage"] * 100 for t in ANNEES}
    emploi = ctx.get("emploi") or {t: e[t]["emploi"] for t in ANNEES}
    canaux = ctx.get("emplois_canaux") or {}
    infl_ref = p.val("calendrier.inflation")
    app0, lt = p.val("macro.taux_apparent_2029"), p.val("macro.taux_long_terme")
    n_lt, mat = p.val("macro.annees_taux_long_terme"), p.val("macro.maturite_moyenne_dette")
    fisher_actif = p.val("inflation.active") and p.val("inflation.effet_fisher")
    dette_prec = ctx.get("dette_depart") or sq.dette_fin_2028(p)
    fisher = prime = 0.0
    ratio_ref, pib_ref_2029 = ratio_reference(p, s), sq.pib(p, s)[2029]
    ecart_scen = sq._v(p, "macro.ecart_taux_scenario", s)
    out = {}
    for t in ANNEES:
        etat = {"s": s, "t": t, "dette_prec": dette_prec, "pib": y, "publie": out}
        flux = {"pib": 0.0, "recettes": 0.0, "blocs": {}, "participations": 0.0, "emploi": 0.0, "chomage": 0.0, "detail": {}}
        for d in dynamiques:
            for k, v in (d.debut(t, etat) or {}).items():
                if k == "blocs":
                    for b, x in v.items():
                        flux["blocs"][b] = flux["blocs"].get(b, 0.0) + x
                elif k == "detail":
                    flux["detail"].update(v)
                else:
                    flux[k] += v
        y[t] = y_base[t] + flux["pib"]
        bl = dict(bl_sq[t])
        for b, x in flux["blocs"].items():
            bl[b] = bl.get(b, 0.0) + x
        rec = rec_sq[t] + flux["recettes"]
        part = flux["participations"]
        for m in mesures:
            v = m.valeurs.get(t, 0.0)
            if m.poste == "recettes":
                rec += v
            elif m.poste == "participations":
                part += v
            else:
                bl[m.poste] = bl.get(m.poste, 0.0) + v
        # dette de fin d'année précédente sur le PIB de cette année-là (dette/PIB publiée) ; pour 2029, PIB du statu
        # quo, comme la référence
        ratio = dette_prec / (y[t - 1] if t > 2029 else pib_ref_2029)
        prime += (prime_marche(p, s, ratio, ratio_ref) - prime) / mat
        if fisher_actif:
            fisher += ((infl[t] - infl_ref) - fisher) / mat
        nominal = (min(lt, app0 + (lt - app0) * (t - 2029) / n_lt) + fisher + ecart_taux_borne(p, prime, sup.get(t, 0.0))
                   + ecart_scen * min(1.0, (t - 2029) / n_lt))
        interets_reels = (nominal - infl[t]) * dette_prec
        detail_regle = None
        sans_regle = None
        if regle is not None:
            solde_av = rec - sum(bl.values()) - interets_reels
            sans_regle = -(solde_av - infl[t] * dette_prec) / y[t] * 100
            detail_regle = _appliquer_regle(regle, t, etat, sans_regle / 100, y[t], rec, bl)
            rec, bl = detail_regle.pop("rec"), detail_regle.pop("bl")
        primaire = sum(bl.values())
        solde = rec - primaire - interets_reels
        dette = dette_prec - solde - part
        maastricht = (solde - infl[t] * dette_prec) / y[t]
        out[t] = {
            "pib": y[t], "recettes": rec, "depenses_primaires": primaire, "blocs": bl,
            "interets_reels": interets_reels, "charge_dette": interets_reels + infl[t] * dette_prec,
            "taux_apparent": nominal, "solde_primaire": rec - primaire, "solde": solde, "dette": dette,
            "participations": part, "deficit": -maastricht * 100, "dette_pib": dette / y[t] * 100,
            "chomage": chom[t] + flux["chomage"], "inflation": infl[t] * 100, "emploi": emploi[t] + flux["emploi"],
            "emplois_canaux": dict(canaux.get(t, {})),
            "retraites_pib": bl["retraites"] / y[t] * 100, "sante_pib": bl["sante"] / y[t] * 100,
            "recettes_pib": rec / y[t] * 100, "depenses_primaires_pib": primaire / y[t] * 100,
            "dynamiques": flux["detail"],
        }
        if regle is not None:
            out[t]["deficit_sans_regle"] = sans_regle
            out[t]["regle"] = detail_regle
        etat.update({"maastricht": maastricht, "dette": dette, "pib_t": y[t], "compte": out[t]})
        for d in dynamiques:
            d.fin(t, etat)
        dette_prec = dette
    return out


def _appliquer_regle(regle: Regle, t: int, etat: dict, avant: float, pib_t: float, rec: float, bl: dict) -> dict:
    """Une année de la règle : déficit `avant` (fraction du PIB, + = déficit) ramené vers la cible."""
    ecart = max(0.0, avant - regle.cible)
    if regle.declenchee is None:
        regle.declenchee = 1.0 if ecart > 0 else 0.0
    auto = sum(a(t, etat, regle.declenchee) for a in regle.automatiques)
    actif = t <= regle.derniere_annee
    # quand le déficit sans règle est sous la cible, la marge absorbe d'abord le coût éventuel des automatiques
    reste = max(0.0, (avant - regle.cible) * pib_t - auto) if actif else 0.0
    bl = dict(bl)
    rec += auto
    utilise, gain, capacites, details = {}, auto, {}, {}
    for lv in regle.leviers:
        cap = lv.capacite(t, etat)
        capacites[lv.nom] = cap
        x = max(0.0, min(reste / lv.rendement, cap)) if actif else 0.0
        reste -= x * lv.rendement
        gain += x * lv.rendement
        utilise[lv.nom] = x
        for poste, v in (lv.ecritures(t, x) if lv.ecritures else [("recettes", x * lv.rendement)]):
            if poste == "recettes":
                rec += v
            else:
                bl[poste] = bl.get(poste, 0.0) + v
        if lv.appliquer:
            lv.appliquer(t, x, etat)
        if lv.detail:
            details[lv.nom] = lv.detail(t, x, etat)
    return {"avant": avant * 100, "automatiques": auto, "leviers": utilise, "capacites": capacites, "details": details, "gain": gain,
            "reste_a_couvrir": reste, "ecart_cible": ecart * pib_t, "rec": rec, "bl": bl}


def simuler(p: Parametres | None = None, programme=None, scenarios=None) -> dict[str, dict[int, dict]]:
    """Les quatre scénarios d'un programme (statu quo si programme est None) ; `scenarios` : seulement ceux-là."""
    from .statu_quo import SCENARIOS
    p = p or Parametres()
    programme = programme or ProgrammeVide()
    noms = [s for s in SCENARIOS if scenarios is None or s in scenarios]
    if hasattr(programme, "entrees"):
        ent = programme.entrees(p, scenarios)
        return {s: trajectoire(p, s, ent[s].mesures, ent[s].contexte, ent[s].dynamiques, ent[s].regle) for s in noms}
    mes, ctx = programme.mesures(p), programme.contexte(p)
    return {s: trajectoire(p, s, mes.get(s), ctx.get(s)) for s in noms}


def resultats(p: Parametres | None = None, scenarios=None) -> dict[str, dict[int, dict]]:
    """Scénarios du programme de p.programme (dossier programmes/<nom>/) sur le noyau commun."""
    p = p or Parametres()
    return simuler(p, charger(p.programme), scenarios)


def bilan_mesures(programme, p: Parametres, s: str = "prudent", annees=(2029, 2037, 2050, 2073)) -> list[dict]:
    """Effet de chaque mesure sur le solde (Md€ ; + = améliore le solde), pour la restitution."""
    out = []
    for m in programme.mesures(p).get(s, []):
        if m.nature == "physique":
            continue
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
    from .mesures import ecartees
    ec = ecartees(p.__class__(programme=nom)) if nom not in ("statu_quo", "vide") else []
    if ec:
        print(f"Économies saisies écartées (sources insuffisantes ou déclaratives) : {sum(x['plein_effet_md'] for x in ec):.1f} Md€ à plein effet")
        for x in ec:
            print(f"  {x['plein_effet_md']:6.2f}  {x['motif']}  — {x['mesure']}")
    print("Déficit (% du PIB) : programme / statu quo")
    for s in SCENARIOS:
        print(f"  {s:<10}" + "  ".join(f"{t} : {res[s][t]['deficit']:.2f} / {sq[s][t]['deficit']:.2f}" for t in annees[:3]))
