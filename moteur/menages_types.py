"""Ménages types : système actuel (OpenFisca-France) contre nouveau système (moteur).

Système actuel : revenu disponible calculé par OpenFisca (outils/openfisca_menages.py), législation 2026.
Nouveau système, pour chaque ménage :
- impôt unique sur le coût employeur, couples imposés ensemble (deux parts), demi-part par enfant dont le gain
  est plafonné (quotient.plafond_demi_part) ;
- impôt local sur le coût employeur au-delà de l'abattement, par adulte ;
- RUI : part gardée par chaque actif selon son coût (RUI au prorata) ; conjoint sans emploi : RUI réduit
  selon les revenus du couple (il s'éteint quand le revenu net du couple par personne atteint deux RUI —
  lecture de la règle de la v235, feuille Quotient familial, à confirmer) ; complément par enfant ;
- épargne obligatoire versée sur le compte de chacun (un patrimoine, pas une dépense).

Pouvoir d'achat comparé : ce que le ménage peut consommer hors taxes s'il dépense tout son revenu disponible,
épargne obligatoire mise à part (revenu / (1 + taux des taxes sur la consommation)). Taux actuel : TVA moyenne
plus accises payées par les ménages ; nouveau taux : TVA, accises écologie et santé, selon le profil de revenu.
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

from .collectivites import taux_impot_local
from .distribution import DONNEES
from .epargne import epargne_annuelle, part_rui_salarie
from .impot_unique import impot
from .parametres import Parametres
from .tva import taux_pour_revenu

RACINE = Path(__file__).resolve().parent.parent


def definitions() -> list[dict]:
    return yaml.safe_load((RACINE / "parametres" / "menages_types.yaml").read_text(encoding="utf-8"))["menages"]


def couts_adultes(m: dict, p: Parametres) -> list[float]:
    """Coût employeur annuel de chaque adulte (0 pour un retraité ou un inactif)."""
    smic = p.val("epargne.cout_smic_mensuel") * 12
    median = p.val("profils.cout_median_annuel")
    out = []
    for a in m["adultes"]:
        if isinstance(a, str) and a.startswith("retraite:"):
            out.append(0.0)
        else:
            out.append(smic if a == "smic" else median if a == "median" else float(a))
    return out


def pensions_adultes(m: dict) -> list[float]:
    """Pension brute annuelle de chaque adulte (retraités de l'ancien système)."""
    return [12 * float(a.split(":")[1]) if isinstance(a, str) and a.startswith("retraite:") else 0.0 for a in m["adultes"]]


def impot_menage(couts: list[float], n_enfants: int, p: Parametres, scenario: str = "prudent") -> float:
    base_parts = len(couts)
    revenu = sum(couts)
    sans_enfant = base_parts * impot(revenu / base_parts, p, scenario)
    if n_enfants == 0:
        return sans_enfant
    parts = base_parts + p.val("quotient.parts_par_enfant") * n_enfants
    avec = parts * impot(revenu / parts, p, scenario)
    demi_parts = n_enfants * p.val("quotient.parts_par_enfant") / 0.5
    return max(avec, sans_enfant - p.val("quotient.plafond_demi_part") * demi_parts)


def parts_enfants(n: int, parent_isole: bool, p: Parametres) -> float:
    """Somme des parts de RUI versées pour n enfants (rang 3 et plus : part majorée)."""
    if parent_isole:
        return n * p.val("rui_complements.part_enfant_parent_isole")
    base = p.val("rui_complements.part_enfant")
    return min(n, 2) * base + max(0, n - 2) * max(base, p.val("rui_complements.part_enfant_rang3"))


def nouveau(m: dict, p: Parametres, scenario: str = "prudent") -> dict:
    couts = couts_adultes(m, p)
    pensions = pensions_adultes(m)
    n_enf = len(m["enfants"])
    rui = p.val("rui.montant") * 12
    imp = impot_menage([c + r for c, r in zip(couts, pensions)], n_enf, p, scenario)
    local = sum(max(0.0, c - p.val("impot_local.abattement")) * taux_impot_local(p, salaries=True) for c in couts)
    rui_actifs = sum(part_rui_salarie(c, p) * rui for c in couts if c > 0)
    net_avant_conjoint = sum(couts) + sum(pensions) - imp - local + rui_actifs
    rui_conjoint = 0.0
    sans_revenu = [c + r <= 0 for c, r in zip(couts, pensions)]
    if len(couts) == 2 and sum(sans_revenu) == 2:
        rui_conjoint = 2 * rui
    elif len(couts) == 2 and sum(sans_revenu) == 1:
        par_personne = net_avant_conjoint / 2
        rui_conjoint = rui * max(0.0, 1 - par_personne / (2 * rui))
    elif len(couts) == 1 and sans_revenu[0]:
        rui_conjoint = rui
    complements = parts_enfants(n_enf, len(couts) == 1, p) * rui
    epargne = sum(epargne_annuelle(c, p, scenario, part_rui_salarie(c, p), contribution=False) for c in couts if c > 0)
    dispo = net_avant_conjoint + rui_conjoint + complements - epargne
    sante, tva = taux_pour_revenu(dispo / max(1, len(couts)), p)
    return {"cout_employeur": sum(couts), "pensions": sum(pensions), "impot_unique": imp, "impot_local": local, "rui": rui_actifs + rui_conjoint,
            "complements_enfants": complements, "epargne_obligatoire": epargne, "revenu_disponible": dispo,
            "taux_consommation": sante + tva, "consommation_ht": dispo / (1 + sante + tva)}


def actuel(annee: int = 2026) -> dict[str, dict]:
    with (DONNEES / f"openfisca_menages_types_{annee}.csv").open(encoding="utf-8") as f:
        return {l["id"]: {k: (v if k in ("id", "couts") else float(v)) for k, v in l.items()} for l in csv.DictReader(f)}


def comparer(p: Parametres | None = None, scenario: str = "prudent") -> list[dict]:
    p = p or Parametres()
    t_actuel = p.val("systeme_actuel.taux_tva_moyen") + p.val("systeme_actuel.taux_accises_menages")
    act = actuel()
    out = []
    for m in definitions():
        a, n = act[m["id"]], nouveau(m, p, scenario)
        conso_a = a["revenu_disponible"] / (1 + t_actuel)
        out.append({"id": m["id"], "libelle": m["libelle"], "actuel": {**a, "consommation_ht": conso_a}, "nouveau": n,
                    "ecart_revenu": n["revenu_disponible"] - a["revenu_disponible"],
                    "ecart_consommation_ht": n["consommation_ht"] - conso_a,
                    "ecart_consommation_pct": n["consommation_ht"] / conso_a - 1})
    return out


if __name__ == "__main__":
    for r in comparer():
        a, n = r["actuel"], r["nouveau"]
        print(f"{r['libelle'][:60]:60} actuel {a['revenu_disponible']:8.0f}  nouveau {n['revenu_disponible']:8.0f} "
              f"(+ épargne {n['epargne_obligatoire']:6.0f})  conso HT {r['ecart_consommation_pct']*100:+5.1f} %")


def futurs_retraites(p: Parametres | None = None, scenario: str = "prudent") -> list[dict]:
    """Retraités du nouveau système en régime de croisière, après une carrière entière au même niveau de coût
    employeur (euros de 2026) : rente de leur épargne obligatoire et socle, qui décroît avec la rente."""
    from .epargne import rente_mensuelle
    p = p or Parametres()
    smic = p.val("epargne.cout_smic_mensuel") * 12
    out = []
    for libelle, c in (("Carrière au SMIC", smic), ("Carrière au salaire médian", p.val("profils.cout_median_annuel")),
                       ("Carrière de cadre (100 000 €)", 100000.0)):
        e = epargne_annuelle(c, p, scenario, part_rui_salarie(c, p), contribution=False)
        rente = rente_mensuelle(e, p)
        socle = p.val("retraites.socle_plein") * max(0.0, 1 - rente / p.val("retraites.rente_annulant_socle"))
        imp = impot(12 * rente * p.val("retraites.part_imposable_rente"), p, scenario) / 12
        if not p.val("retraites.socle_exonere"):
            imp = impot(12 * (rente * p.val("retraites.part_imposable_rente") + socle), p, scenario) / 12
        out.append({"libelle": libelle, "epargne_annuelle": e, "rente": rente, "socle": socle, "impot": imp,
                    "net_mensuel": rente + socle - imp})
    return out
