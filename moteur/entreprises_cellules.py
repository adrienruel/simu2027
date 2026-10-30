"""Entreprises par taille (TPE, PME, ETI, GE) : impôts actuels et nouveaux, coût du capital et investissement.

Ce que le module ajoute au budget statique, qui traite les entreprises en 16 classes de bénéfice (moteur/recettes/
entreprises.py) et leur comportement en agrégats (moteur/macro.py) :

1. Impôts de production des entreprises déficitaires. Le budget statique ajoutait tous les impôts de production
   supprimés (75 Md€ hors secteur non marchand) au bénéfice imposable des entreprises bénéficiaires. Une part est
   payée par des entreprises déficitaires (entreprises_cellules.part_production_deficitaires) : sa suppression
   réduit leurs pertes, et n'est imposée que plus tard, quand les déficits reportés sont imputés (31 %).
   facteur_production() corrige la base de l'IS nouveau.
2. Bilan par taille (pour la restitution) : IS actuel (DGFiP 2024) et impôts de production (Ésane × taux de la
   DGFiP) contre IS nouveau à 45 % (État, communes, régions) sur le bénéfice et les impôts de production supprimés.
   Le programme déplace l'impôt des grandes entreprises vers les petites : les TPE passent du taux réduit de 15 %
   à 45 % et payaient peu d'impôts de production.
3. Coût du capital et investissement par taille (canal « investissement des entreprises » du module macro) :
   chaque taille a son taux marginal actuel (TPE : mélange du taux réduit et du taux normal), sa part d'impôts de
   production sur le capital, et sa réaction (les petites entreprises réagissent davantage, Zwick et Mahon 2017).
   L'élasticité moyenne reste celle du module macro.

Montants en Md€ de 2026 (données de 2021 à 2024 ramenées au total du budget statique).
"""
from __future__ import annotations

import csv

from .distribution import DONNEES
from .parametres import Parametres


def actif(p: Parametres) -> bool:
    return bool(p.val("entreprises_cellules.active"))


def tailles(p: Parametres) -> list[dict]:
    """Une ligne par taille, avec ses parts d'impôts de production, d'investissement et de bénéfice."""
    cache = p.__dict__.setdefault("_cache", {})
    if "entreprises_tailles" in cache:
        return cache["entreprises_tailles"]
    with (DONNEES / "entreprises_tailles.csv").open(encoding="utf-8") as f:
        lignes = [{k: (v if k in ("taille", "libelle") else float(v)) for k, v in l.items()} for l in csv.DictReader(f)]
    for x in lignes:
        if x["taille"] == "TPE":
            x["impots_production_va"] = p.val("entreprises_cellules.production_va_micro")
    prod = sum(x["valeur_ajoutee_md"] * x["impots_production_va"] for x in lignes)
    inv = sum(x["valeur_ajoutee_md"] * x["taux_investissement"] for x in lignes)
    ben = sum(x["benefices_md"] for x in lignes)
    for x in lignes:
        x["part_production"] = x["valeur_ajoutee_md"] * x["impots_production_va"] / prod
        x["part_investissement"] = x["valeur_ajoutee_md"] * x["taux_investissement"] / inv
        x["part_benefices"] = x["benefices_md"] / ben
        # impôts de production rapportés à la valeur ajoutée, relatifs à la moyenne pondérée par l'investissement
        x["production_relative"] = x["impots_production_va"]
    moy = sum(x["part_investissement"] * x["impots_production_va"] for x in lignes)
    for x in lignes:
        x["production_relative"] = x["impots_production_va"] / moy
    norm = sum(x["part_investissement"] * x["elasticite_relative"] for x in lignes)
    for x in lignes:
        x["elasticite_normee"] = x["elasticite_relative"] / norm
    cache["entreprises_tailles"] = lignes
    return lignes


def facteur_production(p: Parametres, jeu: str = "prudent") -> float:
    """Part des impôts de production supprimés qui entre dans le bénéfice imposable (1 sans le module)."""
    if not actif(p):
        return 1.0
    d = p.val("entreprises_cellules.part_production_deficitaires", jeu)
    return 1 - d * (1 - p.val("entreprises_cellules.recuperation_reports"))


def bilan(p: Parametres) -> list[dict]:
    """Impôts des entreprises par taille, système actuel contre nouveau (Md€ de 2026, budget statique, avant
    comportements). Bénéfices et impôts de production ramenés aux totaux du budget statique."""
    from .recettes.entreprises import classes_entreprises
    from .unites import facteur
    cl = classes_entreprises(p)
    benef = sum(c["benefice_median"] * c["entreprises_beneficiaires"] for c in cl) / 1e9
    prod = sum(c["impots_production"] * c["entreprises_beneficiaires"] for c in cl) / 1e9
    taux = (p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes")
            + p.val("impot_local_entreprises.taux_regions"))
    d = p.val("entreprises_cellules.part_production_deficitaires") if actif(p) else 0.0
    recup = p.val("entreprises_cellules.recuperation_reports")
    k_is = facteur(p, 2024, "recettes")
    out = []
    for x in tailles(p):
        b = benef * x["part_benefices"]
        pr = prod * x["part_production"]
        is_actuel = x["is_brut_md"] * k_is
        base = b + pr * (1 - d * (1 - recup))
        nouveau = taux * base
        out.append({"taille": x["taille"], "libelle": x["libelle"], "entreprises": x["entreprises_is"],
                    "is_actuel": is_actuel, "production_actuelle": pr, "actuel": is_actuel + pr,
                    "is_nouveau": nouveau, "ecart": nouveau - is_actuel - pr,
                    "ecart_pct": (nouveau - is_actuel - pr) / (is_actuel + pr)})
    return out


def flux_investissement(p: Parametres, s: str, m, t_coef: float) -> float:
    """Investissement en plus de l'année (Md€, avant montée), somme des tailles : − élasticité × réaction relative ×
    (variation du coût du capital de la taille − baisse due à la déduction) × investissement de la taille.

    m : accesseur des paramètres macro du scénario ; t_coef : b4 × b20 × b21 × part déduite de l'année
    (déduction immédiate, même pour toutes les tailles, le taux nouveau étant le même)."""
    z = p.val("is_investissement.valeur_actuelle_amortissements")
    tn = (p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes")
          + p.val("impot_local_entreprises.taux_regions"))
    inv = p.val("is_investissement.investissement_snf_2025")
    total = 0.0
    for x in tailles(p):
        ta = x["taux_marginal_is_actuel"]
        cc = (((1 - tn * z) / (1 - tn)) / ((1 - ta * z) / (1 - ta)) - 1
              - m("reduction_cout_capital_autres", s) * x["production_relative"])
        total -= m("elasticite_invest", s) * x["elasticite_normee"] * (cc - t_coef) * x["part_investissement"] * inv
    return total


def arbitrage_tpe(p: Parametres, jeu: str = "prudent") -> dict:
    """Dirigeants de petites sociétés qui se versent un salaire au lieu de laisser le bénéfice dans la société
    (réaction à l'IS à 45 %). Pour chaque classe de bénéfice des petites sociétés (bénéfice jusqu'à 150 000 €) et
    chaque niveau de rémunération actuelle du dirigeant (déciles des indépendants classiques, Insee), on cherche le
    montant x passé en salaire qui minimise l'impôt total : barème de l'impôt unique et impôt local sur le salaire,
    contre IS (État et local) et flat tax sur la part distribuée du bénéfice gardé. Le barème est linéaire par
    morceaux : l'optimum est à un seuil. Renvoie la perte de recettes (Md€ de 2026, positive = perte) et le
    bénéfice passé en salaire (Md€), à plein effet."""
    from .collectivites import taux_impot_local
    from .impot_unique import impot
    from .recettes.entreprises import classes_entreprises
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("arbitrage_tpe", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    a = p.val("entreprises_cellules.arbitrage_tpe")
    if not actif(p) or not a["active"]:
        cache[cle] = {"perte": 0.0, "salaire": 0.0}
        return cache[cle]
    tau = (p.val("entreprises.taux_is_etat") + p.val("impot_local_entreprises.taux_communes")
           + p.val("impot_local_entreprises.taux_regions"))
    ft = p.val("capital.flat_tax_dividendes")
    d = p.val("entreprises_cellules.arbitrage_tpe_part_distribuee", jeu)
    recours = p.val("entreprises_cellules.arbitrage_tpe_recours", jeu)
    garde = tau + d * (1 - tau) * ft  # impôt par euro de bénéfice laissé dans la société
    t_loc = taux_impot_local(p, salaries=True)
    ab = p.val("impot_local.abattement")
    seuils = list(p.val("impot_unique.seuils")) + [ab]
    with (DONNEES / "independants.csv").open(encoding="utf-8") as f:
        dirigeants = [l for l in csv.DictReader(f) if l["groupe"] == "classiques"]
    passage = p.val("independants.passage_2023_2026")
    rem = [(float(l["part_effectif"]), float(l["revenu_annuel"]) * passage) for l in dirigeants]

    def impot_salaire(s):
        return impot(s, p) + max(0.0, s - ab) * t_loc

    perte = salaire = 0.0
    for c in classes_entreprises(p):
        pi = c["benefice_median"]
        if pi > a["benefice_max"]:
            continue
        n = c["entreprises_beneficiaires"] * a["part_avec_dirigeant"]
        for w, s0 in rem:
            base = impot_salaire(s0)
            def total(x):
                return impot_salaire(s0 + x) - base + (pi - x) * garde
            candidats = {0.0, pi} | {min(pi, max(0.0, sj - s0)) for sj in seuils}
            x = min(candidats, key=total)
            perte += n * w * recours * (total(0.0) - total(x))
            salaire += n * w * recours * x
    cache[cle] = {"perte": perte / 1e9, "salaire": salaire / 1e9}
    return cache[cle]


def bilan_annees(p: Parametres, annees=(2032, 2037, 2050, 2073)) -> dict:
    """Bilan par taille avec la déduction immédiate de l'investissement et la fin de la déduction des intérêts
    (moteur/is_investissement.py), certaines années, ramené à la taille de l'économie de 2029 (Md€ de 2026, hors
    croissance) pour être comparable au bilan statique. Déduction : au prorata de l'investissement de chaque taille ;
    intérêts : au prorata de la valeur ajoutée (faute de données sur la dette par taille, hypothèse)."""
    from .is_investissement import cout_net_etat, interets_non_deduits
    g = p.val("macro.tendance", "prudent")
    t_is = p.val("entreprises.taux_is_etat")
    if p.val("is_investissement.assiette_locale"):
        t_is += p.val("impot_local_entreprises.taux_communes") + p.val("impot_local_entreprises.taux_regions")
    net, interets = cout_net_etat(p), interets_non_deduits(p, t_is)
    tl = tailles(p)
    va = sum(x["valeur_ajoutee_md"] for x in tl)
    base = bilan(p)
    out = {}
    for t in annees:
        k = (1 + g) ** (t - 2029)
        ded, it = (net[t] + interets[t]) / k, interets[t] / k
        lignes = []
        for x, b in zip(tl, base):
            d_ = ded * x["part_investissement"]
            i_ = it * x["valeur_ajoutee_md"] / va
            e = b["ecart"] - d_ + i_
            lignes.append({"taille": x["taille"], "deduction": d_, "interets": i_, "ecart": e, "ecart_pct": e / b["actuel"]})
        out[t] = lignes
    return out
