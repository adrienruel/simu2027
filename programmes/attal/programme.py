"""Programme de Gabriel Attal (Renaissance), chiffré mesure par mesure sur le noyau (7 novembre 2026).

Sources : site attalpresident.fr, « Lettre aux Français sur les finances publiques » (15 octobre 2026), entretiens et
discours de 2026, recensés par programmes-2027.fr (106 mesures) ; fiche : mesures.yaml. Les économies annoncées
(20 Md€ dès l'élection, 150 Md€ sur le quinquennat) ne sont pas reprises : seules les mesures nommées sont estimées.

- **mesures simples** (groupe attal_mesures, moteur/programme_simple.py) ;
- **mesures calculées** :
  - « droit au brut » : cotisations salariales en moins (≈ 46 Md€ en prudent), impôt sur le revenu en plus, prestations
    en moins, effet d'offre par OpenFisca (forme de la suppression de la CSG) ;
  - « année blanche » de 2028 : prestations et pensions non revalorisées une année (petites retraites protégées) ;
    l'économie sur les pensions s'éteint avec les retraités de 2028 ;
  - assurance chômage : baisse du chômage structurel.

    python -m moteur.noyau attal
"""
from __future__ import annotations

import math

from moteur import bibliotheque as bib
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.programme_simple import ANNEES_AVANT, ProgrammeSimple


class Attal(ProgrammeSimple):
    nom = "attal"
    libelle = "Attal (Renaissance)"

    def mesures_calculees(self, p, s, idx):
        out, canaux = [], {}
        e = sq.effectifs(p, s)

        # ATT-ECO-01 : « droit au brut », cotisations salariales en moins (entièrement déductibles)
        out += bib.baisse_prelevements_salaries(
            p, idx, self.v("droit_au_brut.baisse", s), self.v("droit_au_brut.part_ir_retrouvee", s),
            self.v("droit_au_brut.premiere_annee"), "ATT-ECO-01 — « droit au brut » : cotisations salariales supprimées")

        # ATT-FIS-03 : année blanche de 2028 (prestations et pensions gelées un an)
        infl = p.val("inflation.base")["2028"]
        pens = sq.retraites(p, s)[2029]["depenses"]
        prot = self.v("annee_blanche.part_pensions_protegee", s)
        d = self.v("annee_blanche.duree_pensions")
        eco_p = pens * infl * (1 - prot)
        taux_prel = sq.recettes_par_impot(p, s)[2029]["retraites"] / pens
        serie_p = {2027: 0.0, 2028: -eco_p, **{t: -eco_p * math.exp(-(t - 2028) / d) * idx["pib"][t] for t in ANNEES}}
        out += [
            Mesure("ATT-FIS-03 — année blanche de 2028 : pensions non revalorisées (petites retraites protégées)",
                   "retraites", serie_p),
            Mesure("ATT-FIS-03 — année blanche : prélèvements sur les pensions en moins", "recettes",
                   {t: taux_prel * v for t, v in serie_p.items()}),
        ]
        eco_q = self.v("annee_blanche.prestations_indexees") * infl
        out.append(Mesure("ATT-FIS-03 — année blanche de 2028 : prestations non revalorisées", "pauvrete",
                          {2027: 0.0, 2028: -eco_q, **{t: -eco_q * idx["pib"][t] for t in ANNEES}}))

        # ATT-EMP-01 : assurance chômage, chômage structurel plus bas
        h = self.v("chomage.baisse_taux", s)
        canaux["Assurance chômage resserrée : emplois en plus"] = {
            t: h * min(1.0, (t - 2027) / 3) * (e[t]["emploi"] + e[t]["chomeurs"]) for t in ANNEES}
        return out, canaux


def programme() -> Attal:
    return Attal()
