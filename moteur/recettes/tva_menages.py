"""TVA et accises payées par les ménages (feuille Total, ligne 3).

Pour chaque population, la consommation HT découle du revenu disponible et de la
fonction de consommation du modèle ; la TVA est le taux effectif du profil × consommation.
"""
from __future__ import annotations

from ..epargne import epargne_annuelle, part_rui_salarie, net_apres_impot
from ..parametres import Parametres
from ..tva import consommation_ht, taux_pour_revenu
from .impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public
from .retraites_croisiere import classes_retraites
from ..distribution import lire


def tva_actif(cout_employeur: float, p: Parametres, scenario: str, part_rui: float, base_epargne: float) -> float:
    """TVA annuelle d'un actif. base_epargne : coût employeur servant au taux d'épargne et à l'impôt local."""
    net = net_apres_impot(base_epargne, p, scenario, part_rui)
    sante, tva = taux_pour_revenu(net, p)
    t = sante + tva
    local = max(0.0, base_epargne - p.val("impot_local.abattement")) * p.val("impot_local.taux_point_fixe")
    dispo = net - local
    oblig = epargne_annuelle(base_epargne, p, scenario, part_rui, contribution=False)
    spontanee = max(0.0, dispo - consommation_ht(dispo, t, p) * (1 + t))
    volontaire = max(0.0, min(spontanee, dispo - oblig) - p.val("consommation.eviction_epargne_volontaire", scenario) * oblig)
    conso = max(0.0, dispo - oblig - volontaire) / (1 + t)
    return t * conso


def tva_prive(p: Parametres, scenario: str = "prudent") -> float:
    d = effectifs_prive_2026(p)
    return sum(n * tva_actif(c, p, scenario, part_rui_salarie(c, p), c) for c, n in zip(d.milieux, d.effectifs))


def tva_public(p: Parametres, scenario: str = "prudent") -> float:
    d = effectifs_public_2026(p)
    a = facteur_alignement_public(p)
    return sum(n * tva_actif(c * a, p, scenario, 1 - min(1.0, c / 12500), c * a)
               for c, n in zip(d.milieux, d.effectifs))


def tva_retraites(p: Parametres, scenario: str = "prudent") -> float:
    total = 0.0
    for c in classes_retraites(p, scenario):
        revenu = (c["socle"] + c["rente"]) * 12 - c["impot"]
        sante, tva = taux_pour_revenu(revenu, p)
        total += c["effectif"] * (sante + tva) * consommation_ht(revenu, sante + tva, p)
    return total


def _tva_revenu(revenu: float, p: Parametres) -> float:
    sante, tva = taux_pour_revenu(revenu, p)
    return (sante + tva) * consommation_ht(revenu, sante + tva, p)


def tva_etudiants(p: Parametres) -> float:
    return p.val("inactifs.etudiants") * _tva_revenu(p.val("rui.montant") * 12, p)


def tva_inactifs(p: Parametres) -> float:
    rui = p.val("rui.montant") * 12
    plafond = p.val("inactifs.revenu_annulant_rui") * 12
    total = 0.0
    for c, n in zip(lire_inactifs()[0], lire_inactifs()[1]):
        rui_c = max(0.0, (plafond - c) / plafond * rui)
        total += n * _tva_revenu(c + rui_c, p)
    return total


def lire_inactifs():
    import csv
    from ..distribution import DONNEES
    with (DONNEES / "inactifs.csv").open(encoding="utf-8") as f:
        l = list(csv.DictReader(f))
    return [float(x["autre_revenu_annuel"]) for x in l], [float(x["effectif"]) for x in l]


def tva_chomeurs(p: Parametres) -> float:
    """Chômeurs au RUI non comptés ailleurs : TVA d'un étudiant au RUI plein, par tête."""
    n = p.val("inactifs.chomeurs_bit") * (1 - p.val("inactifs.part_chomeurs_deja_comptee")) * p.val("inactifs.rui_moyen_chomeurs")
    return n * _tva_revenu(p.val("rui.montant") * 12, p)
