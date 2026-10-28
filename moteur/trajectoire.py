"""Bloc comptable de la trajectoire 2029-2073 (euros constants de 2026, Md€).

Reproduit les identités de la feuille « Trajectoire 2029-2073 » de la v235 :
- dépenses = santé + retraites + RUI et AAH + investissement + autres + charge de la dette ;
- solde (intérêts réels) = recettes − dépenses ; solde primaire = solde + charge de la dette ;
- dette(t) = dette(t−1) − solde(t) − participations de l'État remises au fonds(t) ;
- solde de Maastricht = (solde − inflation × dette(t−1)) / PIB.

Les postes eux-mêmes (recettes, santé, retraites…) viendront des autres modules ;
ici ils sont des entrées.
"""
from __future__ import annotations

from dataclasses import dataclass, field

POSTES_DEPENSES = ("sante", "retraites", "rui_aah", "investissement", "autres", "charge_dette")


@dataclass
class Annee:
    annee: int
    pib: float
    recettes: float
    sante: float
    retraites: float
    rui_aah: float
    investissement: float
    autres: float
    charge_dette: float
    participations_fonds: float = 0.0
    # Résultats
    depenses: float = field(init=False, default=0.0)
    solde: float = field(init=False, default=0.0)
    solde_primaire: float = field(init=False, default=0.0)
    dette: float = field(init=False, default=0.0)
    dette_pib: float = field(init=False, default=0.0)
    solde_maastricht_pib: float = field(init=False, default=0.0)


def calculer(annees: list[Annee], dette_depart: float, inflation: float) -> list[Annee]:
    dette_prec = dette_depart
    for a in annees:
        a.depenses = sum(getattr(a, p) for p in POSTES_DEPENSES)
        a.solde = a.recettes - a.depenses
        a.solde_primaire = a.solde + a.charge_dette
        a.dette = dette_prec - a.solde - a.participations_fonds
        a.dette_pib = a.dette / a.pib
        a.solde_maastricht_pib = (a.solde - inflation * dette_prec) / a.pib
        dette_prec = a.dette
    return annees
