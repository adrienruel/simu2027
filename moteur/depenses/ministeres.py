"""Dépenses des ministères année par année, chacune selon ce qui la fait vivre (demande d'Adrien du 30/10/2026).

Avant : toutes les « autres dépenses » (missions de l'État, collectivités, Sécurité sociale hors santé…) suivaient la
croissance tendancielle et la population totale. Désormais, chaque mission suit :
- la croissance (salaires publics et coûts qui suivent les salaires du privé, loi de Baumol) ;
- et le public qu'elle sert : population totale (police, justice, administration…), élèves de 3 à 17 ans
  (enseignement scolaire), jeunes de 18 à 24 ans (enseignement supérieur), enfants (aide sociale à l'enfance),
  personnes en emploi (travail et emploi) ;
- ou le PIB (défense, contribution à l'Union européenne, aide au développement, économie, écologie, agriculture,
  recherche) : une part constante de la richesse produite ;
- ou les prix seulement, à la règle d'indexation (engagements financiers, monde combattant : montants qui ne
  suivent pas la croissance).

Enseignement scolaire : la baisse du nombre d'élèves jusqu'en 2035 est déjà comptée dans les mesures (enseignants
ajustés à la baisse des élèves, moteur/depenses/economies_missions.py et registre des économies) ; la mission ne
suit les élèves qu'après 2035, pour ne pas compter deux fois.
"""
from __future__ import annotations

from ..parametres import Parametres

ANNEES = list(range(2029, 2074))

# mission (début du nom) → (règle, public servi)
REGLES = [
    ("Sécurités", "croissance", "total"),
    ("Administration générale", "croissance", "total"),
    ("Immigration", "croissance", "total"),
    ("Justice", "croissance", "total"),
    ("Gestion des finances publiques", "croissance", "total"),
    ("Économie", "pib", None),
    ("Engagements financiers", "prix", None),
    ("Action extérieure", "pib", None),
    ("Aide publique au développement", "pib", None),
    ("Enseignement scolaire public", "croissance", "eleves"),
    ("Enseignement privé", "croissance", "eleves"),
    ("Recherche et enseignement supérieur", "recherche", "etudiants"),
    ("Agriculture", "pib", None),
    ("Culture", "croissance", "total"),
    ("Audiovisuel", "croissance", "total"),
    ("Écologie", "pib", None),
    ("Sport", "croissance", "total"),
    ("Conseil et contrôle", "croissance", "total"),
    ("Direction de l’action", "croissance", "total"),
    ("Pouvoirs publics", "croissance", "total"),
    ("Transformation publique", "croissance", "total"),
    ("Outre-mer", "croissance", "total"),
    ("Monde combattant", "prix", None),
    ("Santé (aide médicale", "croissance", "total"),
    ("Aide sociale à l’enfance", "croissance", "enfants"),
    ("Protection de l’enfance", "croissance", "total"),
    ("Solidarité", "croissance", "total"),
    ("Travail, emploi", "croissance", "emploi"),
    ("Défense", "pib", None),
]

LIBELLES = {"total": "population", "eleves": "élèves de 3 à 17 ans", "etudiants": "jeunes de 18 à 24 ans",
            "enfants": "enfants", "emploi": "personnes en emploi"}


def _regle(mission: str) -> tuple[str, str | None]:
    for debut, regle, public in REGLES:
        if mission.startswith(debut):
            return regle, public
    return "croissance", "total"


def publics(p: Parametres, jeu: str = "prudent") -> dict[str, dict[int, float]]:
    """Indices des publics servis, 1 en 2029."""
    from ..demographie import effectifs, population
    pop = population(p, jeu)
    e = effectifs(p, jeu)
    brut = {"total": {t: sum(pop[t]) for t in ANNEES},
            "eleves": {t: sum(pop[t][3:18]) for t in ANNEES},
            "etudiants": {t: sum(pop[t][18:25]) for t in ANNEES},
            "enfants": {t: sum(pop[t][0:18]) for t in ANNEES},
            "emploi": {t: e[t]["emploi"] for t in ANNEES}}
    out = {k: {t: v[t] / v[2029] for t in ANNEES} for k, v in brut.items()}
    # élèves et étudiants : les moyens ne baissent pas un pour un avec les effectifs (classes, établissements,
    # encadrement par élève qui monte) ; élasticité prudente (ministeres.elasticite_eleves_etudiants)
    e_ = p.val("ministeres.elasticite_eleves_etudiants")
    for k in ("eleves", "etudiants"):
        out[k] = {t: out[k][t] ** e_ for t in ANNEES}
    # enseignement scolaire : élèves après 2035 seulement (la baisse d'ici 2035 est dans les mesures)
    out["eleves"] = {t: (out["eleves"][t] / out["eleves"][2035] if t > 2035 else 1.0) for t in ANNEES}
    return out


def indice(p: Parametres, regle: str, public: str | None, t: int, idx: dict, g: float) -> float:
    n = t - 2029
    if regle == "prix":
        from ..inflation import indice_reel
        return indice_reel(p)[t]
    if regle == "pib":
        return (1 + g) ** n * idx["emploi"][t]
    if regle == "recherche":  # moitié recherche (PIB), moitié universités (étudiants)
        return 0.5 * (1 + g) ** n * idx["emploi"][t] + 0.5 * (1 + g) ** n * idx["etudiants"][t]
    return (1 + g) ** n * idx[public or "total"][t]


def postes(p: Parametres) -> list[dict]:
    """Postes de départ (Md€ de 2026, 2029) avec leur règle : missions de l'État (y compris les compléments de leur
    ligne du modèle), contribution à l'UE, et les autres dépenses hors quotient familial."""
    from . import budget_etat
    from .statique import depenses
    lignes = budget_etat.lignes_modele(p)
    out = []
    par_ligne = {}
    for m in budget_etat.couts_par_mission(p):
        if m["ligne"] in ("Fonds", "Supprimé", "Retraites") or abs(m["cout"]) < 1e-9:
            continue
        regle, public = _regle(m["mission"])
        out.append({"nom": m["mission"], "groupe": m["ligne"], "cout": m["cout"], "regle": regle, "public": public})
        par_ligne[m["ligne"]] = par_ligne.get(m["ligne"], 0.0) + m["cout"]
    # compléments des lignes (Éducation : apprentissage et élèves du privé revenus au public ; Recherche ; UE)
    for ligne, total in lignes.items():
        if ligne in ("Fonds", "Supprimé", "Retraites"):
            continue
        reste = total - par_ligne.get(ligne, 0.0)
        if abs(reste) > 1e-6:
            regle, public = {"Éducation": ("croissance", "eleves"), "Recherche": ("recherche", "etudiants"),
                             "Contribution UE": ("pib", None)}.get(ligne, ("croissance", "total"))
            nom = "Contribution à l'Union européenne" if ligne == "Contribution UE" else f"{ligne} : compléments"
            out.append({"nom": nom, "groupe": ligne, "cout": reste, "regle": regle, "public": public})
    d = depenses(p)["lignes"]
    from ..unites import facteur  # noqa: F401
    autres = {"collectivites": ("Collectivités : besoin de financement restant", "croissance", "total"),
              "securite_sociale_hors_sante": ("Sécurité sociale hors santé", "croissance", "total"),
              "economies_missions": ("Économies sur les missions (budget de départ)", "croissance", "total"),
              "economies_supplementaires": ("Économies supplémentaires (budget de départ)", "croissance", "total")}
    concours = d["autres_missions"] - lignes.get("Autres", 0.0)
    if abs(concours) > 1e-6:
        out.append({"nom": "Concours aux outre-mer", "groupe": "Autres", "cout": concours, "regle": "croissance", "public": "total"})
    for k, (nom, regle, public) in autres.items():
        out.append({"nom": nom, "groupe": "Autres", "cout": d[k], "regle": regle, "public": public})
    return out


def trajectoire(p: Parametres) -> dict:
    """Coût de chaque poste année par année (Md€ de 2026) et évolution par groupe (ligne du modèle)."""
    cache = p.__dict__.setdefault("_cache", {})
    if "ministeres" in cache:
        return cache["ministeres"]
    g = p.val("macro.tendance", "prudent")
    idx = publics(p)
    ps = postes(p)
    par_poste = {x["nom"]: {t: x["cout"] * indice(p, x["regle"], x["public"], t, idx, g) for t in ANNEES} for x in ps}
    groupes = {}
    for x in ps:
        gr = groupes.setdefault(x["groupe"], {"depart": 0.0, "valeurs": {t: 0.0 for t in ANNEES}})
        gr["depart"] += x["cout"]
        for t in ANNEES:
            gr["valeurs"][t] += par_poste[x["nom"]][t]
    base = sum(x["cout"] for x in ps)
    # parts qui suivent la population totale et les enfants (écart entre scénarios de population, module macro)
    part_total = sum(x["cout"] for x in ps if x["regle"] == "croissance" and x["public"] == "total")
    part_enfants = sum(x["cout"] for x in ps if x["regle"] == "croissance" and x["public"] in ("enfants", "eleves"))
    out = {"postes": ps, "par_poste": par_poste, "groupes": groupes, "base": base,
           "part_total": part_total, "part_enfants": part_enfants}
    cache["ministeres"] = out
    return out
