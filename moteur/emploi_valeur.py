"""Ce que rapporte un emploi au barème du programme (21/11/2026, demande d'Adrien : moduler la valeur d'un emploi selon
le manque à gagner en impôt du programme, comme l'allocation évitée l'est déjà selon la générosité de son assurance
chômage, roadmap 5.4).

La valeur d'un emploi des canaux (programme_commun.emploi_valeur_emploi, ≈ cellule OpenFisca à 1,3 SMIC) et celle d'un
senior maintenu en emploi (seniors.valeur_emploi, ≈ cellule au coût moyen) sont des prélèvements et de la TVA au
barème de 2026. Un programme qui baisse les prélèvements sur le travail ou la TVA fait rapporter moins à chaque emploi
créé (et coûter moins à chaque emploi perdu) ; un programme qui les relève, davantage. Chaque mesure de recettes du
programme (nature « mesure ») sur le travail (instruments travail et cout_travail) touche l'emploi selon son incidence,
avec la règle du canal d'offre (offre.base_incidence) : une baisse des cotisations près du SMIC pèse sur un emploi à
1,3 SMIC, une hausse de l'impôt des hauts revenus presque pas. Les mesures sur la consommation (instrument
consommation) changent la TVA et les accises payées sur le revenu dépensé, au prorata de leur produit.

facteur(t) = (prélèvements au barème du programme + TVA au barème du programme) / (les mêmes au statu quo), pour
l'emploi type ; jamais sous zéro. L'allocation évitée n'en fait pas partie : elle suit la générosité du programme
(programme_simple.generosite, bloc chômage du noyau).
"""
from __future__ import annotations

from . import offre
from . import statu_quo as sq
from .noyau import ANNEES
from .parametres import Parametres

INSTRUMENTS_TRAVAIL = ("travail", "cout_travail")


def cellule(p: Parametres, niveau) -> dict:
    """Emploi type (€ de 2026 par an) : coût, brut, net après impôt sur le revenu, prélèvements, IR, TVA sur le revenu
    dépensé. niveau : coût en multiple de celui du SMIC, ou « moyen » (coût moyen du privé) ; même calcul que
    ProgrammeSimple.valeur_emploi_cellule."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("emploi_type", niveau)
    if cle in cache:
        return cache[cle]
    from .systeme_actuel import _interp, _table_openfisca
    T = _table_openfisca()
    x = T["cout_du_travail"]
    if niveau == "moyen":
        from .recettes.impot_salaires import effectifs_prive_2026
        d = effectifs_prive_2026(p)
        c = sum(m * n for m, n in zip(d.milieux, d.effectifs)) / sum(d.effectifs)
    else:
        c = _interp(offre.SMIC_BRUT_2026, T["brut"], x) * float(niveau)
    net = _interp(c, x, T["salaire_net"]) + _interp(c, x, T["impot_revenu_restant_a_payer"])
    out = {"cout": c, "brut": _interp(c, x, T["brut"]), "net": net, "prelevements": c - net,
           "ir": -_interp(c, x, T["impot_revenu_restant_a_payer"]), "tva": p.val("systeme_actuel.taux_tva_moyen") * net}
    cache[cle] = out
    return out


def facteur(p: Parametres, s: str, liste: list, niveau) -> dict[int, float]:
    """Prélèvements et TVA d'un emploi type au barème du programme, rapportés au statu quo, chaque année."""
    if not p.val("emploi.prelevements_programme"):
        return {t: 1.0 for t in ANNEES}
    job = cellule(p, niveau)
    cel = offre._cellules(p)
    totaux: dict[str, float] = {}
    w = sq.salaires(p, s)
    rec = sq.recettes_par_impot(p, s)
    out = {}
    for t in ANNEES:
        idx = w[t] / w[2029]
        d_prel, d_conso = 0.0, 0.0
        for m in liste:
            if m.nature != "mesure" or m.poste != "recettes":
                continue
            v = m.valeurs.get(t, 0.0)
            if not v:
                continue
            if m.instrument in INSTRUMENTS_TRAVAIL:
                inc = m.incidence if m.incidence in offre.INCIDENCES else "proportionnel"
                if inc not in totaux:
                    totaux[inc] = sum(x["n"] * offre.base_incidence(inc, x) for x in cel)
                if totaux[inc]:
                    d_prel += v * 1e9 / idx * offre.base_incidence(inc, job) / totaux[inc]
            elif m.instrument == "consommation":
                d_conso += v / (rec[t]["tva"] + rec[t]["accises_et_taxes_sur_produits"])
        base = job["prelevements"] + job["tva"]
        out[t] = max(0.0, (base + d_prel + job["tva"] * d_conso) / base)
    return out
