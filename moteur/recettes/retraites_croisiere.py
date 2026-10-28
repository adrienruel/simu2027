"""Impôt des retraités en régime de croisière (feuille Retraités, Total ligne 5).

Les retraités de demain reproduisent la distribution des actifs d'aujourd'hui,
recalée sur 17,3 M. Chacun touche la rente de son épargne obligatoire et le socle,
dégressif avec cette rente. Socle exonéré ; gains de la rente à la flat tax.
"""
from __future__ import annotations

from ..epargne import epargne_annuelle, rente_mensuelle
from ..impot_unique import impot
from ..parametres import Parametres
from .impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public


def rentes_des_actifs(p: Parametres, scenario: str = "prudent") -> list[tuple[float, float]]:
    """(rente mensuelle, effectif) pour chaque classe d'actifs, privé puis public."""
    out = []
    d = effectifs_prive_2026(p)
    for c, n in zip(d.milieux, d.effectifs):
        out.append((rente_mensuelle(epargne_annuelle(c, p, scenario), p), n))
    d = effectifs_public_2026(p)
    a = facteur_alignement_public(p)
    for c, n in zip(d.milieux, d.effectifs):
        # v235 : la part de RUI des agents s'éteint à 12 500 € (et non au SMIC) et la
        # contribution de transition n'est pas retirée. Reproduit tel quel ; voir le journal.
        part_rui = 1 - min(1.0, c / 12500)
        out.append((rente_mensuelle(epargne_annuelle(c * a, p, scenario, part_rui, contribution=False), p), n))
    return out


def socle(rente_mensuelle_: float, p: Parametres) -> float:
    plein, plafond = p.val("retraites.socle_plein"), p.val("retraites.rente_annulant_socle")
    return max(0.0, (plafond - rente_mensuelle_) / plafond * plein)


def classes_retraites(p: Parametres, scenario: str = "prudent") -> list[dict]:
    """Une ligne par classe de rente : effectif, rente et socle mensuels, impôt annuel par tête."""
    bornes = p.val("retraites.bornes_rente_annuelle")
    rentes = rentes_des_actifs(p, scenario)
    echelle = p.val("retraites.nombre_retraites") / sum(n for _, n in rentes)
    flat = p.val("capital.flat_tax_dividendes")
    part_imposable = p.val("retraites.part_imposable_rente")
    out = []
    for bas, haut in zip(bornes[:-1], bornes[1:]):
        effectif = sum(n for r, n in rentes if bas <= r * 12 < haut) * echelle
        rente = (bas + haut) / 2 / 12  # rente au milieu de la classe
        s = socle(rente, p)
        base_socle = 0.0 if p.val("retraites.socle_exonere") else s * 12
        imp = impot(base_socle, p, scenario) + rente * 12 * part_imposable * flat
        out.append({"effectif": effectif, "rente": rente, "socle": s, "impot": imp})
    return out


def impot_retraites(p: Parametres, scenario: str = "prudent") -> float:
    return sum(c["effectif"] * c["impot"] for c in classes_retraites(p, scenario))
