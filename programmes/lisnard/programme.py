"""Programme de David Lisnard (Nouvelle Énergie), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : pages thématiques, carnets, « Le livre noir », discours de Bayeux, fiches « Questions » et entretiens de 2026,
recensés par programmes-2027.fr (91 mesures) ; fiche : mesures.yaml. Les économies annoncées (80 puis 200 Md€) ne sont
pas reprises : seules les mesures nommées sont estimées.

- **mesures simples** (groupe lisnard_mesures) : impôts de production −40 Md€, IS à 20 %, successions, effectifs publics
  −12 %, agences, allocation unique, prisons… ;
- **mesures calculées** : 120 Md€ rendus aux actifs (CSG de 9,2 à 6,6 % et cotisations salariales), montée en quatre ans,
  moteur/bibliotheque.baisse_prelevements_salaries ; chômage un peu plus bas (dégressivité).
- Retraites : statu quo (réforme de 2023 gardée, pas de nouvel âge ; la capitalisation amorcée par la désindexation des
  pensions au-delà de 2 000 € est comptée neutre : l'économie sur les pensions va aux fonds).

    python -m moteur.noyau lisnard
"""
from __future__ import annotations

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES
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
        e = sq.effectifs(p, s)
        h = self.v("chomage.baisse_taux", s)
        canaux["Allocations chômage dégressives : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        return out, canaux


def programme() -> Lisnard:
    return Lisnard()
