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


