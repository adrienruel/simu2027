"""Système actuel, approximé par classe comme dans la v235 (remplacé par OpenFisca à l'étape 3).

Net actuel = net avant aides + RSA et prime d'activité + APL − taxe foncière estimée.
"""
from __future__ import annotations

from .parametres import Parametres


def rsa_et_prime_prive(net_annuel: float, p: Parametres) -> float:
    """RSA et prime d'activité d'une personne seule (barèmes d'avril 2026), annuels."""
    m = net_annuel / 12
    rsa_m, fl = p.val("systeme_actuel.rsa_personne_seule"), p.val("systeme_actuel.rsa_forfait_logement")
    pa = p.val("systeme_actuel.prime_activite")
    rsa = max(0.0, rsa_m - m - fl)
    bonus = 0.0 if m <= pa["bonus_debut"] else pa["bonus_max"] * min(1, (m - pa["bonus_debut"]) / (pa["bonus_max_a"] - pa["bonus_debut"]))
    prime = max(0.0, pa["forfaitaire"] + pa["part_revenus"] * m + bonus - max(pa["forfaitaire"], m + pa["forfait_logement"] + rsa))
    if prime < pa["seuil_versement"]:
        prime = 0.0
    return 12 * (rsa + prime)


def prime_agents(net_annuel: float, p: Parametres) -> float:
    m = net_annuel / 12
    a = p.val("systeme_actuel.prime_activite_agents")
    if m <= a["revenu_max"]:
        return 12 * a["montant_max"] * m / a["revenu_max"]
    if m <= a["revenu_extinction"]:
        return 12 * a["montant_max"] * (a["revenu_extinction"] - m) / (a["revenu_extinction"] - a["revenu_max"])
    return 0.0


def apl(net_annuel: float, p: Parametres) -> float:
    m = net_annuel / 12
    a = p.val("systeme_actuel.apl")
    if m <= a["revenu_plein"]:
        return 12 * a["montant_plein"]
    if m <= a["revenu_extinction"]:
        return 12 * a["montant_plein"] * (a["revenu_extinction"] - m) / (a["revenu_extinction"] - a["revenu_plein"])
    return 0.0


def taxe_fonciere(net_annuel: float, p: Parametres, public: bool) -> float:
    if not public and net_annuel < p.val("systeme_actuel.exoneration_taxe_fonciere_prive"):
        return 0.0
    t = p.val("systeme_actuel.taxe_fonciere")
    return t["coef_public" if public else "coef_prive"] * net_annuel ** t["exposant"]


def net_actuel(net_avant_aides: float, p: Parametres, public: bool) -> float:
    aides = (prime_agents(net_avant_aides, p) if public else rsa_et_prime_prive(net_avant_aides, p)) + apl(net_avant_aides, p)
    return net_avant_aides + aides - taxe_fonciere(net_avant_aides, p, public)


def consommation_actuelle_ht(net: float, p: Parametres) -> float:
    t = p.val("systeme_actuel.taux_tva_moyen")
    return p.val("consommation.coefficient") * (net / (1 + t)) ** p.val("consommation.exposant")
