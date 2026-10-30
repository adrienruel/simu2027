"""Réaction des revenus déclarés à l'impôt : hauts revenus, classes moyennes, localisation (feuille Hauts revenus).

Le revenu après réaction suit (1 − taux marginal nouveau) / (1 − taux marginal actuel) à la puissance de l'élasticité.
La perte de recettes nette ce qui passe par une société (IS, règle nordique du dirigeant-actionnaire).
"""
from __future__ import annotations

import csv
import math

from .distribution import DONNEES
from .impot_unique import impot, taux_marginal
from .parametres import Parametres
from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026

SCENARIOS = ("prudent", "median", "optimiste")


def _taux_local(p):
    from .collectivites import taux_impot_local
    return taux_impot_local(p)


def _classes_hautes(p: Parametres):
    with (DONNEES / "hauts_revenus_taux_marginaux.csv").open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    prive, public = effectifs_prive_2026(p), effectifs_public_2026(p)
    for l in lignes:
        d = prive if l["population"] == "prive" else public
        i = int(l["indice_classe"])
        yield d.milieux[i], d.effectifs[i], float(l["taux_marginal_actuel"]), l["population"]


def revenu_apres_reaction(cout: float, tm_actuel: float, p: Parametres, s: str) -> float:
    tm_nouveau = taux_marginal(cout + 1e-9, p) + _taux_local(p)
    return cout * ((1 - tm_nouveau) / (1 - tm_actuel)) ** p.val("hauts_revenus.elasticite_revenu", s)


def perte_hauts_revenus(p: Parametres, s: str) -> float:
    loc = _taux_local(p)
    from .is_bareme import actif as _bareme_actif, taux_marginal_etat
    is_total = p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    soc, nord = p.val("hauts_revenus.part_par_societe", s), p.val("hauts_revenus.regle_nordique", s)
    total = 0.0
    for c, n, tm, pop in _classes_hautes(p):
        g = revenu_apres_reaction(c, tm, p, s)
        di = impot(c, p) - impot(g, p)
        ecart = c - g
        # Un agent public ne peut pas faire passer son revenu par une société (Hauts revenus, lignes 35 à 44)
        if _bareme_actif(p):  # IS progressif : la société d'un haut revenu paie le taux de la tranche de ce revenu
            is_total = (taux_marginal_etat(p, ecart) + p.val("impot_local_entreprises.taux_communes")
                        + p.val("impot_local_entreprises.taux_regions"))
        recupere = (pop == "prive") * soc * ecart * ((1 - nord) * is_total + nord * di / (ecart if abs(ecart) >= 1 else 1) + nord * loc)
        total += n * (di + loc * ecart - recupere)
    return total / 1e9


def perte_croisee_capital(p: Parametres, s: str) -> float:
    """Un taux plus élevé sur le capital fait baisser les revenus du travail des mêmes foyers (Md€)."""
    loc = _taux_local(p)
    masse = sum(c * n for c, n, _, _ in _classes_hautes(p)) / 1e9
    tm = sum(c * n * (taux_marginal(c + 1e-9, p) + loc) for c, n, _, _ in _classes_hautes(p)) / (masse * 1e9)
    return -masse * tm * p.val("hauts_revenus.elasticite_croisee_travail", s) * math.log(
        (1 - p.val("revenus_capital.plafond")) / (1 - p.val("revenus_capital.taux_actuel")))


def perte_classes_moyennes(p: Parametres, s: str) -> float:
    lo, hi = p.val("hauts_revenus.classes_moyennes_bornes")
    d = effectifs_prive_2026(p)
    from .systeme_actuel import nets_prive
    nets = nets_prive(p)["actuel"]
    loc = _taux_local(p)
    total = 0.0
    for i in range(len(d.milieux) - 1):
        c = d.milieux[i]
        if not lo <= c < hi:
            continue
        tm_actuel = 1 - (nets[i + 1] - nets[i]) / (d.milieux[i + 1] - c)
        t_etat = taux_marginal(c + 1e-9, p)
        tm_nouveau = t_etat + loc
        total += -p.val("hauts_revenus.elasticite_classes_moyennes", s) * math.log((1 - tm_nouveau) / (1 - tm_actuel)) * d.effectifs[i] * c * t_etat
    return total / 1e9


def perte_localisation(p: Parametres, s: str) -> float:
    """Emplois perdus par la localisation : recette en moins par rapport à l'emploi moyen créé (Md€)."""
    from .emploi import gain_par_emploi
    from .emploi import _taux_local as tl
    from .epargne import taux_epargne
    loc_emplois = _localisation(p)
    cout = effectifs_prive_2026(p).milieux[13]  # emploi au salaire médian (Salariés du privé!C15, 42 500 €)
    def gain_median(sc):
        part = p.val("emploi.gain_par_emploi", sc)
        rui = p.val("rui.montant") * 12
        imp = impot(cout, p)
        conso = (cout - imp - max(0.0, cout - p.val("impot_local.abattement")) * tl(p)) * (1 - taux_epargne(cout, p)) - rui * part
        return part * rui + imp + p.val("systeme_actuel.taux_tva_moyen") * conso
    ecart = gain_median(s) - gain_par_emploi(p, s)
    emplois = (loc_emplois["crise"] + loc_emplois["median"]) / 2 if s == "prudent" else loc_emplois[s]
    return -emplois * ecart / 1e9


def _localisation(p: Parametres) -> dict[str, float]:
    """Emplois gagnés ou perdus par la localisation des activités (Emploi ligne 234)."""
    from .emploi import JEUX
    from .recettes import entreprises
    d = effectifs_prive_2026(p)
    ent = entreprises._lire("entreprises.csv")
    ia = p.val("entreprises.is_actuel")
    is_actuel = sum((e["benefice_median"] * ia["taux_reduit"] if e["benefice_median"] <= ia["seuil_reduit"]
                     else ia["seuil_reduit"] * ia["taux_reduit"] + (e["benefice_median"] - ia["seuil_reduit"]) * ia["taux_normal"])
                    * e["entreprises_beneficiaires"] for e in ent) / 1e9
    assiette = sum(e["benefice_median"] * e["entreprises_beneficiaires"] for e in ent) / 1e9
    prod = p.val("entreprises.impots_production_2023") - p.val("entreprises.impots_production_hors_marchand")
    part_sal = p.val("emploi.impots_production_salaires") / p.val("entreprises.impots_production_2023")
    taux_actuel = (is_actuel + prod * (1 - part_sal)) / (assiette + prod * (1 - part_sal))
    taux_nouveau = p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    ecart = (taux_nouveau - taux_actuel) * 100
    out = {}
    for j in JEUX:
        l = p.val("emploi.localisation", j)
        out[j] = -ecart * (l["hausse"] if ecart > 0 else l["baisse"]) * l["part"] * l["mobilite"] * sum(d.effectifs)
    return out


def reactions(p: Parametres) -> dict[str, dict]:
    """Ce que lit la feuille Effets macro : perte à terme (Md€) et années de montée en charge, par scénario."""
    out = {}
    for s in SCENARIOS:
        out[s] = {"montant": perte_hauts_revenus(p, s) + perte_croisee_capital(p, s) + perte_classes_moyennes(p, s)
                  + perte_localisation(p, s), "montee": p.val("hauts_revenus.montee", s)}
    return out


def baisse_revenus_declares(p: Parametres) -> dict[str, float]:
    """Baisse des revenus déclarés des hauts revenus, hors passage par une société (Md€, Effets macro ligne 226)."""
    out = {}
    for s in SCENARIOS:
        out[s] = sum(n * (c - revenu_apres_reaction(c, tm, p, s)) for c, n, tm, _ in _classes_hautes(p)) / 1e9 * (1 - p.val("hauts_revenus.part_par_societe", s))
    return out
