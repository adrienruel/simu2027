"""Impôt unique des salariés (feuille Total, ligne 4 pour le privé)."""
from __future__ import annotations

from ..distribution import lire, passer_en_2026
from ..impot_unique import impot
from ..parametres import Parametres
from ..unites import facteur


def effectifs_prive_2026(p: Parametres):
    d = lire("salaries_prive.csv")
    return passer_en_2026(d, facteur(p, 2024, "salaire_prive"))


def impot_prive(p: Parametres, scenario: str = "prudent") -> float:
    """Impôt unique des salariés du privé, en euros de 2026 (statique)."""
    d = effectifs_prive_2026(p)
    return sum(n * impot(c, p, scenario) for c, n in zip(d.milieux, d.effectifs))


def facteur_alignement_public(p: Parametres) -> float:
    """Nouveau coût employeur public / coût actuel, moyenne pondérée des versants.

    État : brut × (1 + charges du privé) rapporté à la masse CAS Pensions compris.
    Territoriale et hospitalière : (1 + charges du privé) / (1 + charges actuelles).
    """
    t = p.val("alignement.charges_patronales_prive")
    etat = p.val("alignement.remunerations_activite_etat_2026") * (1 + t) / p.val("alignement.masse_salariale_etat_2026")
    total = 0.0
    for v in p.val("alignement.versants").values():
        f = etat if v["charges_actuelles"] is None else (1 + t) / (1 + v["charges_actuelles"])
        total += v["part"] * f
    return total


def effectifs_public_2026(p: Parametres):
    return passer_en_2026(lire("fonctionnaires.csv"), facteur(p, 2023, "salaire_public"))


def impot_public(p: Parametres, scenario: str = "prudent") -> float:
    """Impôt unique des agents publics : barème appliqué au coût employeur aligné."""
    d = effectifs_public_2026(p)
    a = facteur_alignement_public(p)
    return sum(n * impot(c * a, p, scenario) for c, n in zip(d.milieux, d.effectifs))
