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


def is_33_25(p: Parametres) -> dict:
    """Baisse du taux normal de l'IS de 33,3 % à 25 % (2018-2022), backtest hors calage (phase 3.3, 16/11/2026) :
    coût ex ante ≈ 11 Md€ par an (FIPECO, 01/09/2017 ; Institut Montaigne, 2022), porté en euros de 2026 par le PIB
    nominal (≈ +15 % de 2022 à 2026, HYPOTHESE), instrument « capital des entreprises », montée en cinq ans comme la
    réforme. Évaluations ex post : aucun effet agrégé sur l'investissement isolé à ce jour (France Stratégie, comité
    d'évaluation des réformes de la fiscalité du capital, rapport final d'octobre 2023) ; création d'entreprises +1
    point par point de taux d'imposition des bénéfices en moins (IPP, rapport n° 47, 2023, PFU et IS ensemble) ; taux
    implicite de l'IS passé de 20,7 % à 17,5 % de l'excédent net d'exploitation de 2016 à 2022 (Insee, document de
    travail n° 2025-18), la base ayant crû plus vite que l'excédent. Aucun paramètre du moteur n'a été calé sur
    cette réforme."""
    out = {}
    for s in SCENARIOS:
        w = sq.salaires(p, s)
        m = Mesure("Baisse de l'IS 33,3 → 25 % (backtest)", "recettes",
                   {t: -11.0 * 1.15 * min(1.0, (t - 2028) / 5) * w[t] / w[2029] for t in ANNEES}, "detail",
                   instrument="capital_entreprises")
        ef = offre.effets(p, s, [m], annees_avant=())
        y = sq.pib(p, s)
        out[s] = {"pib_5_ans_pct": ef["dpib"][2033] / y[2033] * 100, "pib_10_ans_pct": ef["dpib"][2038] / y[2038] * 100,
                  "emplois_10_ans": sum(v.get(2038, 0.0) for v in ef["emplois"].values()),
                  "pib_10_ans_md": ef["dpib"][2038], "cout_statique_md": 11.0 * 1.15}
    return out


def assurance_chomage_2019(p: Parametres) -> dict:
    """Réforme de l'assurance chômage de 2019-2021, backtest hors calage des lectures communes de « chômage
    structurel en moins » (phase 3.3, 16/11/2026). Le moteur n'a pas de mécanisme commun pour l'assurance chômage :
    chaque programme qui la resserre (Attal, Philippe, Retailleau, Lisnard) déclare une baisse du taux de chômage
    (<programme>_chomage.baisse_taux). On la confronte à l'ordre de grandeur qui découle des effets mesurés de la
    réforme de 2019-2021 (Dares, rapport final du comité d'évaluation, avril 2025, p. 2, 17 et 25) :
    - salaire journalier de référence : 1,1 million d'allocataires touchés, durée sans emploi −10 jours (Paris-Cité) ;
    - dégressivité : 70 000 personnes par an, durée de non-emploi −1,5 mois ;
    - condition d'affiliation : 475 000 personnes, retour à l'emploi à 2 mois +3 points (base 30 %), compté ici
      comme 2 mois d'avance pour ces 3 % ;
    soit un stock de chômeurs plus bas de ≈ 1,1 M × 10 / 365 + 70 000 × 1,5 / 12 + 475 000 × 3 % × 2 / 12. Le
    rapport ne donne pas d'effet sur le niveau d'emploi (p. 9) : c'est un ordre de grandeur, pas une évaluation
    macroéconomique. Repère macro : réformes de 2021 et 2023 ensemble ≈ 0,6 point de chômage structurel (Banque de
    France, bulletin n° 264, 2026, cité dans les paramètres des programmes). La réforme de 2019-2021 représentait
    ≈ 2,3 Md€ d'économies par an ex ante, environ 7 % des allocations (même rapport, p. 16-17)."""
    from moteur import noyau
    e = sq.effectifs(p, "prudent")[2029]
    actifs = e["emploi"] + e["chomeurs"]
    stock = 1.1e6 * 10 / 365 + 70_000 * 1.5 / 12 + 475_000 * 0.03 * 2 / 12
    out = {"reforme_2019_2021": {"chomeurs_en_moins": stock, "points_de_chomage": stock / actifs * 100,
                                 "economies_ex_ante_md": 2.3}}
    for nom in ("attal", "philippe", "retailleau", "lisnard"):
        prog = noyau.charger(nom)
        out[nom] = {s: prog.v("chomage.baisse_taux", s) * 100 for s in SCENARIOS}
    return out


def ampleur_assurance_chomage(p: Parametres, annee: int = 2032) -> dict:
    """Roadmap 8.3 (18/11/2026) : l'ampleur de chaque réforme de l'assurance chômage, mesurée par ses économies de
    législation (mesures du bloc chômage, prudent), rapportée à celle de 2019-2021 (2,3 Md€ ex ante), contre sa
    lecture de chômage en moins rapportée à l'effet de 2019-2021 (0,13 point). Un rapport proche de 1 : la lecture
    est proportionnée à l'ampleur de la réforme. Les 2,3 Md€ sont en euros de 2019-2021, les économies des
    programmes en euros de 2026 à l'économie de 2032 : la comparaison est un ordre de grandeur."""
    from moteur import noyau
    ref = assurance_chomage_2019(p)
    pts_ref, eco_ref = ref["reforme_2019_2021"]["points_de_chomage"], ref["reforme_2019_2021"]["economies_ex_ante_md"]
    out = {}
    for nom in ("attal", "philippe", "retailleau", "lisnard"):
        prog = noyau.charger(nom)
        eco = -sum(m.valeurs.get(annee, 0.0) for m in prog.mesures(p)["prudent"]
                   if m.poste == "chomage" and m.nature == "mesure")
        a = eco / eco_ref
        lec = ref[nom]["prudent"] / pts_ref
        out[nom] = {"economies_md": eco, "ampleur": a, "lecture_relative": lec, "rapport": lec / a if a else None}
    return out


if __name__ == "__main__":
    p = Parametres()
    print("CICE :", {s: {k: round(v / 1e3) if "emplois" in k else round(v, 2) for k, v in x.items()} for s, x in cice(p).items()})
    print("Âge +2 ans :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 2)) for k, v in x.items()}
                           for s, x in age_plus_deux(p).items()})
    print("35 heures :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 2)) for k, v in x.items()}
                          for s, x in trente_cinq_heures(p).items()})
    print("PFU :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 3)) for k, v in x.items()} for s, x in pfu(p).items()})
    print("IS 33,3 → 25 % :", {s: {k: (round(v / 1e3) if "emplois" in k else round(v, 3)) for k, v in x.items()} for s, x in is_33_25(p).items()})
    ac = assurance_chomage_2019(p)
    print("Assurance chômage 2019-2021 :", {k: round(v, 3) for k, v in ac.pop("reforme_2019_2021").items()})
    print("  lectures des programmes (points de chômage) :", {k: {s: round(x, 2) for s, x in v.items()} for k, v in ac.items()})
    print("  ampleur des réformes (économies / 2,3 Md€) et lecture rapportée :",
          {k: {c: round(x, 2) for c, x in v.items()} for k, v in ampleur_assurance_chomage(p).items()})
