"""TVA écologique et santé : accises par produit et taux effectifs par profil de ménage.

Reproduit la feuille « Barème TVA » de la v235 (lignes 5 à 30 et blocs de calcul des accises).
"""
from __future__ import annotations

import bisect
import csv
from dataclasses import dataclass

from .distribution import DONNEES
from .parametres import Parametres

PROFILS = ("modeste", "median", "aise", "tres_aise")


def prix_carbone(p: Parametres) -> float:
    f = 1.0
    for g in p.val("tva.croissance_prix_carbone"):
        f *= 1 + g
    return p.val("tva.prix_carbone_2024") * f


def accises_calculees(p: Parametres) -> dict[str, float]:
    """Accises en % du prix hors taxe, calculées à partir du prix du carbone et des paramètres."""
    pc = prix_carbone(p) / 1000  # €/kg
    c, g, ag = p.val("tva.carburants"), p.val("tva.gaz_fioul"), p.val("tva.agriculture")
    av, tx, pe, al = p.val("tva.aerien"), p.val("tva.textile"), p.val("tva.pesticides"), p.val("tva.alcool")
    recette_agri = ag["emissions_mt"] * ag["part_hors_energie"] * pc * (1 - ag["baisse_volumes"]) * (1 - ag["abattement_modulation"])
    pesticides = pe["accise_pleine"] * (1 - pe["part_bio"])
    recette_alcool = al["cout_soins_md"] * (1 - al["part_vin"] * al["abattement_vin"])
    tva_alcool = 0.2  # TVA légale de l'alcool (ligne 10)
    return {
        "carburants": pc * (c["co2_essence"] * (1 - c["part_gazole"]) + c["co2_gazole"] * c["part_gazole"]) / c["prix_ht"],
        "gaz_fioul": pc * (g["co2_gaz_kwh"] / g["prix_gaz_kwh"] * g["part_gaz"] + c["co2_gazole"] / g["prix_fioul_litre"] * (1 - g["part_gaz"])),
        "agriculture_transformee": recette_agri * ag["part_transformes"] / ag["assiette_transformes_md"],
        "agriculture_brute": recette_agri * (1 - ag["part_transformes"]) / ag["assiette_brute_md"],
        "aerien": av["g_co2_par_pkm"] * prix_carbone(p) / 1000 / 10 / av["recette_centimes_pkm"] * av["effets_hors_co2"],
        "textile": tx["accise_max"] * (tx["part_ultra_ephemere"] + tx["part_autres_faible_durabilite"]),
        "pesticides": pesticides,
        "alcool_sante": (1 + tva_alcool + pesticides) * recette_alcool / (al["depense_ttc_md"] - recette_alcool),
    }


@dataclass(frozen=True)
class Produit:
    categorie: str
    tva: float
    accise_ecologie: float
    accise_sante: float
    parts: dict[str, float]

    @property
    def taux_total(self) -> float:
        return self.tva + self.accise_ecologie + self.accise_sante


def produits(p: Parametres) -> list[Produit]:
    calc = accises_calculees(p)
    val = lambda x: calc[x.split(":", 1)[1]] if x.startswith("calcul:") else float(x)
    out = []
    with (DONNEES / "tva_produits.csv").open(encoding="utf-8") as f:
        for l in csv.DictReader(f):
            out.append(Produit(l["categorie"], val(l["tva"]), val(l["accise_ecologie"]), val(l["accise_sante"]),
                               {pr: float(l[f"part_{pr}"]) for pr in PROFILS}))
    return out


def taux_effectifs(p: Parametres) -> dict[str, tuple[float, float]]:
    """Par profil : (accise santé, TVA légale + accise écologie), en % de la consommation HT."""
    out = {}
    pr_ = produits(p)
    for pr in PROFILS:
        somme = sum(x.parts[pr] for x in pr_)
        part_taxes = sum(x.parts[pr] * x.taux_total / (1 + x.taux_total) for x in pr_) / somme
        total_ht = part_taxes / (1 - part_taxes)
        sante = total_ht * (sum(x.parts[pr] * x.accise_sante / (1 + x.taux_total) for x in pr_) / somme) / part_taxes
        out[pr] = (sante, total_ht - sante)
    return out


def taux_pour_revenu(revenu_net: float, p: Parametres) -> tuple[float, float]:
    """Profil choisi par le revenu net annuel (équivalent du MATCH approché d'Excel)."""
    seuils = p.val("tva.seuils_profils")
    i = max(0, bisect.bisect_right(seuils, revenu_net) - 1)
    return taux_effectifs(p)[PROFILS[i]]


def consommation_ht(revenu_ttc: float, taux: float, p: Parametres) -> float:
    """Fonction de consommation du modèle, en euros hors taxe."""
    return p.val("consommation.coefficient") * (revenu_ttc / (1 + taux)) ** p.val("consommation.exposant")
