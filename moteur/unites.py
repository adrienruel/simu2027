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
        return ((1 + p.val("unites.pib_valeur_2025")) * (1 + p.val("unites.pib_volume_2026"))
                * (1 + p.val("unites.deflateur_2026")))
    if nature == "salaire_prive":
        hausses = {2025: p.val("unites.salaire_prive_2025"),
                   2026: p.val("unites.salaire_prive_2026")}
    elif nature == "salaire_public":
        v = p.val("unites.salaire_public_2024")
        h2024 = sum(x["hausse"] * x["effectif"] for x in v.values()) / sum(x["effectif"] for x in v.values())
        hausses = {2024: h2024,
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


def annonce_en_points_pib(p: Parametres, valeur_md: float, annee_euros: int, forme: str, pib_2029: float,
                          montee: dict[int, float] | None = None) -> float:
    """Annonce d'économies d'un candidat en points de PIB de 2029, rythme annuel à plein effet — en un seul endroit
    (phase A8 du 12/11/2026, relecture neutre n° 2, point 11). forme : « niveau » (économie annuelle atteinte en fin
    de quinquennat) ou « cumul » (somme des économies sur le quinquennat, comme Attal ou Bertrand) : le cumul est
    ramené au niveau annuel par la somme de la montée (montee : {année: part du plein}, 2028 à 2032). Euros de 2027
    ramenés à ceux de 2026 par l'inflation de 2027 (inflation.base). Ne sert que de plafond (jamais de chiffre retenu)."""
    if forme not in ("niveau", "cumul"):
        raise ValueError(f"Forme d'annonce inconnue : {forme}")
    cible = p.val("unites.annee_modele")
    v = valeur_md
    if annee_euros == cible + 1:
        v /= 1 + p.val("inflation.base")[str(annee_euros)]
    elif annee_euros != cible:
        raise NotImplementedError(f"Annonce en euros de {annee_euros}")
    if forme == "cumul":
        poids = sum((montee or {}).get(t, 0.0) for t in range(2028, 2033)) or 5.0
        v /= poids
    return v / pib_2029 * 100
