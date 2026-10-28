"""Conversion des euros courants en euros de 2026 — en un seul endroit.

Règle (Refonte, §5) : chaque montant d'entrée porte son année ; la conversion se fait
une seule fois, ici. Un montant converti est marqué pour qu'une seconde conversion
lève une erreur (cause de trois doubles conversions trouvées dans la v235).
"""
from __future__ import annotations

from dataclasses import dataclass

from .parametres import Parametres


class DoubleConversion(RuntimeError):
    pass


@dataclass(frozen=True)
class Montant:
    valeur: float
    annee_euros: int
    converti: bool = False


def facteur(p: Parametres, de: int, nature: str) -> float:
    """Facteur de passage en euros de 2026 selon la nature du montant.

    nature : « recettes » (coefficient global du classeur), « salaire_prive »,
    « salaire_public ».
    """
    cible = p.val("unites.annee_modele")
    if de == cible:
        return 1.0
    if nature == "recettes":
        if de != 2024:
            raise NotImplementedError(f"Facteur recettes {de}→{cible} non défini")
        return p.val("unites.facteur_recettes_2024_2026")
    if nature == "salaire_prive":
        hausses = {2025: p.val("unites.salaire_prive_2025"),
                   2026: p.val("unites.salaire_prive_2026")}
    elif nature == "salaire_public":
        hausses = {2024: p.val("unites.salaire_public_2024"),
                   2025: p.val("unites.salaire_public_2025_2026"),
                   2026: p.val("unites.salaire_public_2025_2026")}
    else:
        raise ValueError(f"Nature inconnue : {nature}")
    f = 1.0
    for annee in range(de + 1, cible + 1):
        if annee not in hausses:
            raise NotImplementedError(f"Hausse {nature} {annee} non définie")
        f *= 1 + hausses[annee]
    return f


def en_euros_2026(m: Montant, p: Parametres, nature: str) -> Montant:
    if m.converti:
        raise DoubleConversion(f"Montant déjà converti : {m}")
    return Montant(m.valeur * facteur(p, m.annee_euros, nature),
                   p.val("unites.annee_modele"), converti=True)
