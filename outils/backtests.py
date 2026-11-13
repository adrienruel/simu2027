"""Backtests du moteur sur des réformes passées dont on connaît l'effet (phase C5 de la roadmap, 13/11/2026).

Chaque réforme est rejouée comme une mesure ordinaire du canal commun, sur le statu quo, dans les quatre scénarios ;
on compare le signe et l'ordre de grandeur aux évaluations publiées.

- CICE : baisse du coût du travail de 18 Md€ (coût de 2016, France Stratégie), instrument « coût du travail » ;
  évaluations : ≈ 100 000 emplois créés ou sauvegardés sur 2013-2016 (micro-économétrie, France Stratégie, 2020),
  160 000 (macro-sectoriel, 2013-2017), 240 000 pour CICE et pacte de responsabilité (Banque de France, 2020).
- Âge légal + 2 ans (réforme de 2023, de 62 à 64 ans) : rejoué comme un report de 64 à 66 ans, au même rythme d'un
  trimestre par génération ; étude d'impact : un peu plus de 300 000 seniors en emploi en plus en 2030, PIB +1,1 point
  (Rexecode, d'après l'étude d'impact). NB : la part des reportés concernés (seniors.part_concernee) est calée sur
  l'étude d'impact : ce backtest vérifie la cohérence, pas une prévision indépendante.

    python -m outils.backtests
"""
from __future__ import annotations

from moteur import offre, statu_quo as sq
from moteur import bibliotheque as bib
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres

SCENARIOS = ("crise", "prudent", "median", "optimiste")


def cice(p: Parametres) -> dict:
    out = {}
    for s in SCENARIOS:
        w = sq.salaires(p, s)
        m = Mesure("CICE (backtest)", "recettes", {t: -18.0 * w[t] / w[2029] for t in ANNEES}, "detail",
                   instrument="cout_travail")
        ef = offre.effets(p, s, [m], annees_avant=())
        emp = {t: sum(v.get(t, 0.0) for v in ef["emplois"].values()) for t in ANNEES}
        y = sq.pib(p, s)
        out[s] = {"emplois_3_ans": emp[2032], "emplois_10_ans": emp[2039],
                  "pib_10_ans_pct": ef["dpib"][2039] / y[2039] * 100}
    return out


def age_plus_deux(p: Parametres) -> dict:
    out = {}
    for s in SCENARIOS:
        det = bib.report_age_legal_detail(p, s, 66.0, 1968, 0.25)
        sen = offre.seniors(p, s, det["non_retraites"])
        y = sq.pib(p, s)
        # 2023 : premières générations concernées en 2023, plein effet en 2030 (sept ans) ; ici : plein effet huit
        # générations après la première, même délai compté depuis la première année d'effet
        debut = min(t for t in ANNEES if sen["emplois"][t] > 1)
        t7 = min(debut + 7, ANNEES[-1])
        t11 = min(debut + 11, ANNEES[-1])
        out[s] = {"premiere_annee": debut, "emplois_7_ans": sen["emplois"][t7], "pib_7_ans_pct": sen["pib"][t7] / y[t7] * 100,
                  "pensions_7_ans_md": det["pensions"][t7], "emplois_plein_effet": sen["emplois"][t11]}
    return out


def trente_cinq_heures(p: Parametres) -> dict:
    """35 heures (lois Aubry, 1998-2002) rejouées avec la mécanique commune des 32 heures et ses paramètres (ceux de
    Roussel) : 39 → 35 heures, sans perte de salaire, pour 60 % des salariés du privé, montée en quatre ans ; plus
    les allègements propres aux 35 heures (≈ 10 Md€ de 2002 : 16 Md€ à maturité, dont 6 pour la ristourne Juppé,
    qui existait déjà), portés en euros de 2026 par le PIB nominal (× 1,95), instrument « coût du travail ».
    Pas de modération salariale (prudent). NB : la part des heures rendues par des embauches (≈ 35 %) a été choisie
    pour les 32 heures d'après ce précédent : le backtest n'est que partiellement indépendant."""
    from moteur import noyau
    rou = noyau.charger("roussel")
    c0 = rou.v("temps_travail.trente_deux_heures")
    out = {}
    for s in SCENARIOS:
        c = {**c0, "heures_actuelles": 39, "heures_cible": 35, "debut": 2029, "plein": 2032,
             "emplois_concernes": 0.6 * c0["emplois_prive"],
             "gain_productivite": c0["gain_productivite"], "part_embauches": c0["part_embauches"]}
        canaux: dict = {}
        rou.trente_deux_heures(p, s, rou.indices(p, s), c, rou.v("temps_travail.elasticite_emploi", s), "35 h", canaux)
        w = sq.salaires(p, s)
        m = Mesure("Allègements des 35 heures (backtest)", "recettes", {t: -10.0 * 1.95 * w[t] / w[2029] for t in ANNEES},
                   "detail", instrument="cout_travail")
        ef = offre.effets(p, s, [m], annees_avant=())
        t = 2035
        rtt = sum(v[t] for v in canaux.values())
        all_ = sum(v.get(t, 0.0) for v in ef["emplois"].values())
        out[s] = {"emplois_rtt": rtt, "emplois_allegements": all_, "emplois_total": rtt + all_,
                  "part_emploi_prive_pct": (rtt + all_) / c0["emplois_prive"] * 100}
    return out


def pfu(p: Parametres) -> dict:
    """PFU (2018) : baisse de la fiscalité des revenus du capital des ménages, coût ex ante ≈ 1,5 Md€ de 2018 (≈ 1,9
    Md€ de 2026 par le PIB nominal), instrument « fiscalité du capital des ménages ». Évaluations : aucun effet
    identifié sur l'investissement (France Stratégie, 3e rapport, 2021 ; rapport final, 2023) ; dividendes versés aux
    ménages +60 % en 2018, qui réduisent fortement le coût budgétaire. Le moteur doit donner un effet sur le PIB
    faible ; la réponse des dividendes n'est pas dans le canal commun (elle l'est dans les réactions des programmes)."""
    out = {}
    for s in SCENARIOS:
        w = sq.salaires(p, s)
        m = Mesure("PFU (backtest)", "recettes", {t: -1.9 * w[t] / w[2029] for t in ANNEES}, "detail",
                   instrument="capital_menages")
        ef = offre.effets(p, s, [m], annees_avant=())
        y = sq.pib(p, s)
        out[s] = {"pib_5_ans_pct": ef["dpib"][2034] / y[2034] * 100, "pib_5_ans_md": ef["dpib"][2034],
                  "emplois_5_ans": sum(v.get(2034, 0.0) for v in ef["emplois"].values())}
    return out


if __name__ == "__main__":
    p = Parametres()
    print("CICE :", {s: {k: round(v / 1e3) if "emplois" in k else round(v, 2) for k, v in x.items()} for s, x in cice(p).items()})
    print("Âge +2 ans :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 2)) for k, v in x.items()}
                           for s, x in age_plus_deux(p).items()})
    print("35 heures :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 2)) for k, v in x.items()}
                          for s, x in trente_cinq_heures(p).items()})
    print("PFU :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 3)) for k, v in x.items()} for s, x in pfu(p).items()})
