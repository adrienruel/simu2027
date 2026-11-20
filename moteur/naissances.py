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

Corrections du 20/11/2026 (phase Q, décision d'Adrien) :
- congés indemnisés (`enfants: conge`) : l'indemnité remplace un salaire, le gain net du ménage n'est pas la dépense ;
  ils comptent pour demographie.conge_part_soutien (0 : pas d'élasticité sourcée pour la durée du congé) ;
- accueil du jeune enfant (`enfants: garde`) : seules les places comptent, au coût public par place de chaque mesure
  (`cout_place`, obligatoire) ; la qualité, la gratuité ou les salaires ne créent pas de place (`enfants: false`) ;
  un crédit d'impôt pour la garde est un soutien monétaire (`enfants: true`) ;
- sens de l'effet : la semi-élasticité est définie pour une baisse du soutien (crise : la plus forte) ; une hausse
  prend le scénario miroir, comme les autres canaux (crise ↔ optimiste, prudent ↔ médian). Les places, définies pour
  une hausse (crise : aucun effet), prennent le miroir quand elles baissent.

Limites : le soutien est une moyenne (les effets par rang et par revenu viendront de la microsimulation, phase F) ;
l'effet du revenu des ménages hors soutien aux enfants n'est pas encore compté.
"""
from __future__ import annotations

from . import statu_quo as sq
from .parametres import Parametres

ANNEES_PLEIN = range(2032, 2037)
MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}


def est_soutien(m) -> bool:
    """Mesure de soutien monétaire aux enfants (prestations, congés, impôt)."""
    if m.enfants is not None:
        return m.enfants is True or m.enfants == "conge"
    return m.poste == "famille" and m.nature == "mesure"


def _plein(m) -> float:
    signe = -1.0 if m.poste == "recettes" else 1.0
    return signe * sum(m.valeurs.get(t, 0.0) for t in ANNEES_PLEIN) / len(ANNEES_PLEIN)


def soutien_par_enfant(p: Parametres, s: str, mesures) -> float:
    """Soutien monétaire moyen en plus par enfant mineur (€ par an, plein effet) apporté par les mesures."""
    part_conge = p.val("demographie.conge_part_soutien")
    total = sum(_plein(m) * (part_conge if m.enfants == "conge" else 1.0) for m in mesures if est_soutien(m))
    pop = sq.population(p, s)
    enfants = sum(sum(pop[t][0:18]) for t in ANNEES_PLEIN) / len(ANNEES_PLEIN)
    return total * 1e9 / enfants


def points_couverture(p: Parametres, s: str, mesures) -> float:
    """Points de couverture des moins de 3 ans en accueil collectif ajoutés par les mesures « garde » : dépense de
    fonctionnement / coût public d'une place de la mesure (`cout_place`, € par an) / enfants de moins de 3 ans."""
    garde = [m for m in mesures if m.enfants == "garde"]
    if not garde:
        return 0.0
    sans_cout = [m.nom for m in garde if not m.cout_place]
    if sans_cout:
        raise ValueError(f"mesure de garde sans cout_place : {sans_cout}")
    places = sum(_plein(m) * 1e9 / m.cout_place for m in garde)
    pop = sq.population(p, s)
    moins3 = sum(sum(pop[t][0:3]) for t in ANNEES_PLEIN) / len(ANNEES_PLEIN)
    return places / moins3


def effet(p: Parametres, s: str, mesures) -> float:
    """Variation relative des naissances à plein effet (0 si le canal est désactivé) : soutien monétaire et places
    d'accueil, aux mêmes paramètres que le calcul d'Écologie de droite (demographie.effet_naissances)."""
    if not p.val("demographie.naissances_communes"):
        return 0.0
    soutien = soutien_par_enfant(p, s, mesures)
    points = points_couverture(p, s, mesures)
    s_soutien = MIROIR[s] if soutien > 0 else s  # semi-élasticité définie pour une baisse
    s_places = MIROIR[s] if points < 0 else s  # effet des places défini pour une hausse
    return (p.val("demographie.natalite_semi_elasticite", s_soutien) * soutien / 100
            + p.val("demographie.creches_effet", s_places) * points / 0.10)
