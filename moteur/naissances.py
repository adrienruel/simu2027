"""Canal commun des naissances (14/11/2026, DÉCISION d'Adrien : mêmes règles pour tous les programmes).

Avant, seul Écologie de droite avait un effet sur les naissances (soutien par enfant de ses ménages types et places
de crèche, moteur/demographie.effet_naissances). Désormais tout programme dont les mesures changent le soutien aux
familles reçoit le même calcul :

1. soutien moyen par enfant mineur (€ de 2026 par an) = montant des mesures de soutien aux enfants à plein effet
   (moyenne 2032-2036) / enfants mineurs du statu quo. Mesure de soutien : poste « famille » (prestations, congés,
   garde), sauf `enfants: false` ; une mesure de recettes compte si elle porte `enfants: true` (quotient familial,
   crédit d'impôt par enfant), une baisse d'impôt étant un soutien en plus ;
2. variation relative des naissances = demographie.natalite_semi_elasticite (par 100 € par an et par enfant) ×
   soutien / 100, en montée sur trois ans à partir de 2030 ;
3. la population du programme est recalculée (migrations.effets, avec la variante migratoire s'il y en a une) :
   prestations, école, santé, puis emploi à partir de 18 ans.

Limites : le soutien est une moyenne (les effets par rang et par revenu viendront de la microsimulation, phase F) ;
l'effet du revenu des ménages hors soutien aux enfants n'est pas encore compté.
"""
from __future__ import annotations

from . import statu_quo as sq
from .parametres import Parametres

ANNEES_PLEIN = range(2032, 2037)


def est_soutien(m) -> bool:
    """Mesure de soutien monétaire aux enfants (prestations, congés, impôt)."""
    if m.enfants is not None:
        return m.enfants is True
    return m.poste == "famille" and m.nature == "mesure"


def _plein(m) -> float:
    signe = -1.0 if m.poste == "recettes" else 1.0
    return signe * sum(m.valeurs.get(t, 0.0) for t in ANNEES_PLEIN) / len(ANNEES_PLEIN)


def soutien_par_enfant(p: Parametres, s: str, mesures) -> float:
    """Soutien monétaire moyen en plus par enfant mineur (€ par an, plein effet) apporté par les mesures."""
    total = sum(_plein(m) for m in mesures if est_soutien(m))
    pop = sq.population(p, s)
    enfants = sum(sum(pop[t][0:18]) for t in ANNEES_PLEIN) / len(ANNEES_PLEIN)
    return total * 1e9 / enfants


def points_couverture(p: Parametres, s: str, mesures) -> float:
    """Points de couverture des moins de 3 ans en accueil collectif ajoutés par les mesures « garde » : dépense de
    fonctionnement / coût d'une place (demographie.cout_place_accueil, Onape) / enfants de moins de 3 ans."""
    total = sum(_plein(m) for m in mesures if m.enfants == "garde")
    if not total:
        return 0.0
    pop = sq.population(p, s)
    moins3 = sum(sum(pop[t][0:3]) for t in ANNEES_PLEIN) / len(ANNEES_PLEIN)
    return total * 1e9 / p.val("demographie.cout_place_accueil") / moins3


def effet(p: Parametres, s: str, mesures) -> float:
    """Variation relative des naissances à plein effet (0 si le canal est désactivé) : soutien monétaire et places
    d'accueil, aux mêmes paramètres que le calcul d'Écologie de droite (demographie.effet_naissances)."""
    if not p.val("demographie.naissances_communes"):
        return 0.0
    return (p.val("demographie.natalite_semi_elasticite", s) * soutien_par_enfant(p, s, mesures) / 100
            + p.val("demographie.creches_effet", s) * points_couverture(p, s, mesures) / 0.10)
