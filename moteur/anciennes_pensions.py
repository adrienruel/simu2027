"""Impôt au barème sur les pensions de l'ancien système, année par année (feuille Anciennes pensions, lignes 30 à 85)."""
from __future__ import annotations

from .impot_unique import impot
from .parametres import Parametres
from .retraites_transition import ANNEES, _csv as _csv_retraites, retraites_nouveau_systeme
from .tva import consommation_ht, taux_pour_revenu


def recette_nette(p: Parametres) -> dict[int, float]:
    """Recette nette ajoutée à la trajectoire (Md€, ligne 85) : impôt au barème net de la baisse des hautes pensions,
    moins l'impôt de croisière déjà compté pour ces retraités, plus la correction de TVA."""
    from .recettes.retraites_croisiere import impot_retraites
    from .recettes.tva_menages import tva_retraites
    from .mesures import registre, effet
    from .retraites_transition import economie_hautes_pensions_2026
    anc = {int(x["annee"]): x for x in _csv_retraites("ancien_systeme_retraites.csv")}
    retraites_totaux = dict(zip(ANNEES, p.val("anciennes_pensions.retraites_ancien_2029_millions")))
    deciles = p.val("anciennes_pensions.deciles_drees_2020")
    moy = sum(deciles) / len(deciles)
    rev, k_rev = p.val("anciennes_pensions.part_reversion"), p.val("anciennes_pensions.deciles_avec_reversion")
    k_couples = p.val("independants.correction_couples")
    g = p.val("macro.tendance", "prudent")
    tm_haut = p.val("impot_unique.taux")[-1]
    nouveaux = retraites_nouveau_systeme(p)
    impot_croisiere = impot_retraites(p) / 1e9
    tva_croisiere = tva_retraites(p) / 1e9
    n_croisiere = p.val("retraites.nombre_retraites") / 1e6
    hp_2026 = economie_hautes_pensions_2026(p)
    base85 = anc[2029]["depenses_desindexees_md"]
    bareme_fort = next(m for m in registre() if m["mesure"].startswith("Ancien système : barème des hautes pensions"))
    anc_md = {t: anc[t]["depenses_desindexees_md"] * anc[t]["part_ancien_systeme"] for t in ANNEES}
    out = {}
    for t in ANNEES:
        retraites = retraites_totaux[t] * anc[t]["part_ancien_systeme"]
        depenses = anc_md[t]
        moyenne = depenses * 1e9 / (retraites * 1e6) / 12
        echelle = moyenne / moy
        index = (1 + g * 1) ** (t - 2029)
        impot_total = tva_total = 0.0
        for i, d in enumerate(deciles, start=1):
            pension = d * echelle * (1 - rev) + (moyenne * rev * 10 / k_rev if i <= k_rev else 0.0)
            imp = index * impot(12 * pension / index, p)
            net = 12 * pension - imp * k_couples
            sante, tva = taux_pour_revenu(net, p)
            impot_total += imp
            tva_total += consommation_ht(max(0.0, net), sante + tva, p) * (sante + tva)
        impot_bareme = impot_total / 10 * retraites * 1e6 * k_couples / 1e9
        baisse_hautes = hp_2026 * anc[t]["part_ancien_systeme"] * anc[t]["depenses_desindexees_md"] / base85 + effet(bareme_fort, t, p, anc_md)
        impot_net = impot_bareme - baisse_hautes * tm_haut
        tva = tva_total / 10 * retraites * 1e6 / 1e9
        impot_trop = (impot_croisiere - impot_croisiere / n_croisiere * nouveaux[t] / 1e6) * index
        tva_trop = (tva_croisiere - tva_croisiere / n_croisiere * nouveaux[t] / 1e6) * index
        out[t] = impot_net - impot_trop + (tva - tva_trop)
    return out
