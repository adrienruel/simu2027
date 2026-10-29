"""Impôt au barème sur les pensions de l'ancien système, année par année (feuille Anciennes pensions, lignes 30 à 85)."""
from __future__ import annotations

from .impot_unique import impot
from .parametres import Parametres
from .retraites_transition import ANNEES, retraites_nouveau_systeme
from .tva import consommation_ht, taux_pour_revenu


def probabilites_paires(rho: float, n: int = 400) -> list[list[float]]:
    """Probabilité qu'un couple réunisse le décile i et le décile j (copule gaussienne de corrélation rho)."""
    import math
    from statistics import NormalDist
    nd = NormalDist()
    z = [nd.inv_cdf((k + 0.5) / n) for k in range(n)]
    m = [[0.0] * 10 for _ in range(10)]
    for a in z:
        i = min(9, int(nd.cdf(a) * 10))
        for e in z:
            j = min(9, int(nd.cdf(rho * a + math.sqrt(1 - rho * rho) * e) * 10))
            m[i][j] += 1 / (n * n)
    return m


def recette_nette(p: Parametres) -> dict[int, float]:
    """Recette nette ajoutée à la trajectoire (Md€, ligne 85) : impôt au barème net de la baisse des hautes pensions,
    moins l'impôt de croisière déjà compté pour ces retraités, plus la correction de TVA."""
    from .recettes.retraites_croisiere import impot_retraites
    from .recettes.tva_menages import tva_retraites
    from .mesures import registre, effet
    from .retraites_transition import economie_hautes_pensions_2026
    from .ancien_systeme import serie as serie_ancien
    anc = serie_ancien(p)
    deciles = p.val("anciennes_pensions.deciles_drees_2020")
    moy = sum(deciles) / len(deciles)
    rev, k_rev = p.val("anciennes_pensions.part_reversion"), p.val("anciennes_pensions.deciles_avec_reversion")
    cc = p.val("anciennes_pensions.couples")
    calcul_couples = cc != "forfait"
    k_couples = 1.0 if calcul_couples else p.val("independants.correction_couples")
    paires = probabilites_paires(cc["correlation"]) if calcul_couples else None
    g = p.val("macro.tendance", "prudent")
    tm_haut = p.val("impot_unique.taux")[-1]
    nouveaux = retraites_nouveau_systeme(p)
    fisc_cellules = None
    if p.val("cohortes.active") and p.val("demographie.active"):
        from .cohortes import fiscalite_retraites_nouveaux
        fisc_cellules = fiscalite_retraites_nouveaux(p)
    impot_croisiere = impot_retraites(p) / 1e9
    tva_croisiere = tva_retraites(p) / 1e9
    n_croisiere = p.val("retraites.nombre_retraites") / 1e6
    hp_2026 = economie_hautes_pensions_2026(p)
    base85 = anc[2029]["depenses_md"]
    bareme_fort = next(m for m in registre() if m["mesure"].startswith("Ancien système : barème des hautes pensions"))
    anc_md = {t: anc[t]["depenses_md"] for t in ANNEES}
    out = {}
    for t in ANNEES:
        retraites = anc[t]["retraites_millions"]
        depenses = anc_md[t]
        moyenne = depenses * 1e9 / (retraites * 1e6) / 12
        echelle = moyenne / moy
        index = (1 + g * 1) ** (t - 2029)
        impot_total = tva_total = 0.0
        pensions = [d * echelle * (1 - rev) + (moyenne * rev * 10 / k_rev if i <= k_rev else 0.0)
                    for i, d in enumerate(deciles, start=1)]
        if calcul_couples:
            # impôt par personne : seuls, chacun au barème ; en couple, deux fois l'impôt du revenu moyen du couple
            seul = [index * impot(12 * x / index, p) for x in pensions]
            ensemble = [sum(paires[i][j] * index * impot(6 * (pensions[i] + pensions[j]) / index, p) for j in range(10)) * 10
                        for i in range(10)]
            k_couples = ((1 - cc["part_en_couple"]) * sum(seul) + cc["part_en_couple"] * sum(ensemble)) / sum(seul)
        for i, d in enumerate(deciles, start=1):
            pension = pensions[i - 1]
            imp = index * impot(12 * pension / index, p)
            net = 12 * pension - imp * k_couples
            sante, tva = taux_pour_revenu(net, p)
            impot_total += imp
            tva_total += consommation_ht(max(0.0, net), sante + tva, p) * (sante + tva)
        impot_bareme = impot_total / 10 * retraites * 1e6 * k_couples / 1e9
        baisse_hautes = hp_2026 * anc_md[t] / base85 + effet(bareme_fort, t, p, anc_md)
        impot_net = impot_bareme - baisse_hautes * tm_haut
        tva = tva_total / 10 * retraites * 1e6 / 1e9
        if fisc_cellules:  # impôt et TVA des nouveaux retraités calculés profil par profil (cellules)
            impot_trop = (impot_croisiere - fisc_cellules[t]["impot"] / 1e9) * index
            tva_trop = (tva_croisiere - fisc_cellules[t]["tva"] / 1e9) * index
        else:
            impot_trop = (impot_croisiere - impot_croisiere / n_croisiere * nouveaux[t] / 1e6) * index
            tva_trop = (tva_croisiere - tva_croisiere / n_croisiere * nouveaux[t] / 1e6) * index
        # Le budget statique compte un forfait pour les couples de retraités (quotient conjugal) ; pour la part
        # des retraités encore dans l'ancien système, l'imposition commune est désormais calculée ici : on rend
        # cette part du forfait pour ne pas la compter deux fois.
        forfait_rendu = 0.0
        if calcul_couples:
            c = p.val("quotient.conjugal")
            forfait_rendu = c["retraites_forfait"] * c["applique"] * (1 - nouveaux[t] / 1e6 / n_croisiere)
        out[t] = impot_net - impot_trop + (tva - tva_trop) + forfait_rendu
    return out
