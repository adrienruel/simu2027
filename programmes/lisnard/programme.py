"""Programme de David Lisnard (Nouvelle Énergie), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : pages thématiques, carnets, « Le livre noir », discours de Bayeux, fiches « Questions » et entretiens de 2026,
recensés par programmes-2027.fr (91 mesures) ; fiche : mesures.yaml. Les économies annoncées (80 puis 200 Md€) ne sont
pas reprises : seules les mesures nommées sont estimées.

- **mesures simples** (groupe lisnard_mesures) : impôts de production −40 Md€, IS à 20 %, successions, effectifs publics
  −12 %, agences, allocation unique, prisons… ;
- **mesures calculées** : 120 Md€ rendus aux actifs (CSG de 9,2 à 6,6 % et cotisations salariales), montée en quatre ans,
  moteur/bibliotheque.baisse_prelevements_salaries ; chômage un peu plus bas (dégressivité).
- retraites : âge porté à 65 ans (moteur/bibliotheque.report_age_legal_detail, même rythme que Bertrand), emploi des
  seniors ; pensions au-delà de 2 000 € non revalorisées pendant le quinquennat (amorçage de la capitalisation, fonds
  public : l'économie reste dans les comptes publics).

    python -m moteur.noyau lisnard
"""
from __future__ import annotations

import math

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ProgrammeSimple


class Lisnard(ProgrammeSimple):
    nom = "lisnard"
    libelle = "Lisnard (Nouvelle Énergie)"

    def mesures_calculees(self, p, s, idx):
        canaux = {}
        c = bib.csg_activite(p)
        csg = self.v("actifs.csg_points") / 9.2 * (c["csg_prive"] + c["csg_public"])
        cot = self.v("actifs.baisse_totale") - csg
        k = self.v("actifs.part_ir_retrouvee", s)
        out = bib.baisse_prelevements_salaries(p, idx, csg, k, 2028, "LIS-ECO-07 — CSG sur les revenus d'activité de 9,2 à 6,6 %",
                                               deductible=6.8 / 9.2)
        out += bib.baisse_prelevements_salaries(p, idx, cot, k, 2028, "LIS-ECO-02 — 120 Md€ rendus aux actifs : cotisations salariales en moins")
        mont = {int(a): v for a, v in self.v("actifs.montee").items()}

        def f(t):
            return 0.0 if t < min(mont) else mont.get(t, 1.0)
        for m in out:
            m.valeurs = {t: v * f(t) for t, v in m.valeurs.items()}
        # LIS-RET-02 : 65 ans
        det = bib.report_age_legal_detail(p, s, self.v("retraites.age_cible"), self.v("retraites.premiere_generation"),
                                          self.v("retraites.pas_par_generation"))
        self.non_retraites = getattr(self, "non_retraites", {})
        self.non_retraites[(id(p), s)] = {"serie": det["non_retraites"], "baisse": False}
        serie = {2027: 0.0, 2028: 0.0, **{t: -det["pensions"][t] for t in ANNEES}}
        pens = sq.retraites(p, s)[2029]["depenses"]
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / pens
        out += [Mesure(f"LIS-RET-02 — âge de départ porté à {self.v('retraites.age_cible')} ans", "retraites", serie),
                Mesure("LIS-RET-02 — prélèvements sur les pensions en moins", "recettes",
                       {t: taux_prel * v for t, v in serie.items()})]
        # LIS-RET-01 : pensions au-delà de 2 000 € non revalorisées pendant le quinquennat
        infl = p.val("inflation.base")
        pi = infl["2028"]
        k_d = self.v("retraites.desindexation_part", s)
        n = int(self.v("retraites.desindexation_annees"))
        def eco(t):  # perte de niveau cumulée, qui s'éteint avec les retraités concernés (≈ 18 ans)
            return sum(pens * k_d * pi * math.exp(-(t - a) / 18) for a in range(2028, 2028 + n) if a <= t)
        ser_d = {2027: 0.0, 2028: -eco(2028), **{t: -eco(t) * idx["pib"][t] for t in ANNEES}}
        out += [Mesure("LIS-RET-01 — pensions au-delà de 2 000 € non revalorisées pendant le quinquennat", "retraites", ser_d),
                Mesure("LIS-RET-01 — prélèvements sur les pensions en moins (désindexation)", "recettes",
                       {t: taux_prel * v for t, v in ser_d.items()})]
        e = sq.effectifs(p, s)
        h = self.v("chomage.baisse_taux", s)
        canaux["Allocations chômage dégressives : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        return out, canaux


def programme() -> Lisnard:
    return Lisnard()
