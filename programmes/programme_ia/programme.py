"""« Programme IA » : programme de test écrit par Claude pour s'amuser (18 novembre 2026).

Pas un candidat : 20 mesures proposées par une IA, passées au banc du comparateur avec les mêmes règles que les
autres. Non publié (absent de programmes/publies.yaml) : hors des sorties et des tests par défaut, sans effet sur
les programmes publiés. Fiche : mesures.yaml ; montants : parametres.yaml (groupe programme_ia_mesures).

Le programme annonce +41,5 Md€ net en 2032, dont 30 Md€ par une règle de dépense. Comme pour les candidats, ce
chiffre n'est pas repris : la règle passe par l'enveloppe commune (économies déduites domaine par domaine, l'annonce
n'est qu'un plafond) et chaque autre mesure est estimée en crise / prudent / médian / optimiste.

    python -m moteur.noyau programme_ia
"""
from __future__ import annotations

from moteur.programme_simple import ProgrammeSimple


class ProgrammeIA(ProgrammeSimple):
    nom = "programme_ia"
    libelle = "Programme IA (test)"


def programme() -> ProgrammeIA:
    return ProgrammeIA()
