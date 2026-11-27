"""Variante « avec la réaction des marchés » (DÉCISION d'Adrien du 27/11/2026 : « on ne spécule pas sur les taux »).

Le calcul principal n'a ni prime de taux liée à la dette (macro.prime_dette = 0, statu quo compris) ni baisse de
l'écart de taux gagnée par un programme (macro.baisse_spread = 0) : l'écart de solde primaire, la dette et le déficit
publiés en tête ne dépendent pas de la façon dont les marchés réagiraient. Cette variante remet les valeurs d'avant
(macro.prime_dette_reaction, macro.baisse_spread_reaction) : la dette plus chère quand elle monte (3 pb par point de dette au prudent),
la crédibilité gagnée quand elle baisse. Elle est publiée à part (outils/export_comparaison.py, colonnes
*_reaction_marches) : c'est la référence du déficit au sens de Maastricht « si les marchés réagissent comme le suppose
le modèle ».
"""
from __future__ import annotations

import dataclasses

from .parametres import Parametres

CLES = {"macro.prime_dette": "macro.prime_dette_reaction", "macro.baisse_spread": "macro.baisse_spread_reaction"}


def parametres(p: Parametres) -> Parametres:
    """Copie de p avec la réaction des marchés (valeurs de macro.prime_dette_reaction et macro.baisse_spread_reaction)."""
    q = p.avec()
    for cle, source in CLES.items():
        q.remplacer(cle, dataclasses.replace(q[cle], valeur=q[source].valeur))
    return q
