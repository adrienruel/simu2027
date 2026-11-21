"""Ce que rapporte un emploi au barème du programme (21/11/2026, demande d'Adrien : moduler la valeur d'un emploi selon
le manque à gagner en impôt du programme, comme l'allocation évitée l'est déjà selon la générosité de son assurance
chômage, roadmap 5.4).

La valeur d'un emploi des canaux (cellule OpenFisca du salaire du canal, 1,3 SMIC par défaut, roadmap 2.2) et celle d'un
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


def valeur_ajoutee(p: Parametres, s: str, niveau) -> float:
    """Roadmap 2.2 (21/11/2026) : valeur ajoutée d'un emploi en plus (€ de 2026 par an) selon son salaire : coût du
    travail de l'emploi type × offre.travail_part_pib / emploi.part_travail_va. Même règle que le canal d'offre :
    au prudent, capital inchangé, l'emploi produit son coût ; à l'optimiste, le capital suit et il produit davantage.
    Remplace la valeur unique de 35 000 € (programme_commun.emploi_valeur_ajoutee_emploi)."""
    return cellule(p, niveau)["cout"] * sq._v(p, "offre.travail_part_pib", s) / p.val("emploi.part_travail_va")


def niveau_canal(canal: str, defaut):
    """Nom et salaire déclaré d'un canal d'emploi (roadmap 2.2) : « nom@1.0 » (multiple du coût du SMIC) ou
    « nom@moyen » ; sans « @ », le salaire par défaut (emploi.cout_emploi_cree_smic)."""
    if "@" in canal:
        nom, n = canal.rsplit("@", 1)
        return nom, (n if n == "moyen" else float(n))
    return canal, defaut


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


INSTRUMENTS_ENTREPRISES = ("capital_entreprises",)


def excedent(p: Parametres, s: str, liste: list, niveau, va: float) -> dict[int, float]:
    """Impôts sur la part non salariale de la valeur ajoutée d'un emploi (€ de 2026 par an et par emploi) : IS et
    impôts de production non assis sur les salaires, au taux implicite emploi.taux_impots_excedent sur
    (valeur ajoutée − coût du travail de l'emploi type), au barème du programme : les mesures de recettes sur les
    entreprises (instrument capital_entreprises) le changent au prorata de l'IS et des impôts de production du statu
    quo (21/11/2026, demande d'Adrien). Rien si la valeur ajoutée ne dépasse pas le coût."""
    marge = max(0.0, va - cellule(p, niveau)["cout"])
    taux = p.val("emploi.taux_impots_excedent")
    if not marge or not taux:
        return {t: 0.0 for t in ANNEES}
    rec = sq.recettes_par_impot(p, s)
    out = {}
    for t in ANNEES:
        base = rec[t]["impot_sur_les_societes"] + rec[t]["impots_de_production"]
        d = sum(m.valeurs.get(t, 0.0) for m in liste
                if m.nature == "mesure" and m.poste == "recettes" and m.instrument in INSTRUMENTS_ENTREPRISES)
        out[t] = marge * taux * max(0.0, 1 + d / base) if p.val("emploi.prelevements_programme") else marge * taux
    return out
