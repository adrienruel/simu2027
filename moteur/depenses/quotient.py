"""Quotient familial, quotient conjugal et RUI du conjoint sous condition de ressources (feuille Quotient familial)."""
from __future__ import annotations

from ..impot_unique import impot
from ..parametres import Parametres
from ..recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public


def gain_demi_part(revenu: float, p: Parametres) -> float:
    k = 1 + p.val("quotient.parts_par_enfant")
    return impot(revenu, p) - k * impot(revenu / k, p)


def gain_moyen_par_enfant(p: Parametres) -> float:
    plafond = p.val("quotient.plafond_demi_part")
    a = facteur_alignement_public(p)
    dp, dg = effectifs_prive_2026(p), effectifs_public_2026(p)
    total = sum(n * min(gain_demi_part(c, p), plafond) for c, n in zip(dp.milieux, dp.effectifs))
    total += sum(n * min(gain_demi_part(c * a, p), plafond) for c, n in zip(dg.milieux, dg.effectifs))
    return total / (sum(dp.effectifs) + sum(dg.effectifs))


def gains_conjugaux(p: Parametres, n: int = 300) -> tuple[float, float]:
    """Gain moyen de l'imposition commune (impôt de chacun − 2 × impôt du revenu moyen du couple), en €/an.

    Les revenus des conjoints suivent la distribution des coûts employeur (privé et public aligné) ;
    pour les couples à deux revenus, les rangs sont corrélés (copule gaussienne, corrélation du paramètre).
    Intégration sur une grille de n × n quantiles normaux (déterministe).
    """
    import bisect
    import math
    from statistics import NormalDist
    a = facteur_alignement_public(p)
    dp, dg = effectifs_prive_2026(p), effectifs_public_2026(p)
    pts = sorted([(c, k) for c, k in zip(dp.milieux, dp.effectifs)] + [(c * a, k) for c, k in zip(dg.milieux, dg.effectifs)])
    total = sum(k for _, k in pts)
    cum, s = [], 0.0
    for _, k in pts:
        s += k
        cum.append(s / total)
    nd = NormalDist()
    q = lambda u: pts[min(bisect.bisect_left(cum, u), len(pts) - 1)][0]
    z = [nd.inv_cdf((i + 0.5) / n) for i in range(n)]
    rho = p.val("quotient.conjugal")["correlation"]
    un = sum(impot(c, p) - 2 * impot(c / 2, p) for c in (q(nd.cdf(x)) for x in z)) / n
    deux = 0.0
    for x in z:
        c1 = q(nd.cdf(x))
        i1 = impot(c1, p)
        for e in z:
            c2 = q(nd.cdf(rho * x + math.sqrt(1 - rho * rho) * e))
            deux += i1 + impot(c2, p) - 2 * impot((c1 + c2) / 2, p)
    return un, deux / (n * n)


_GAINS: dict = {}  # gains conjugaux par barème et distribution (calcul de 0,3 s)


def gains(p: Parametres) -> tuple[float, float]:
    """Gains moyens de l'imposition commune (couple à un revenu, à deux revenus), en €/an, mis en cache."""
    c = p.val("quotient.conjugal")
    if "gain_un_revenu" in c:  # v235 : gains figés d'une ancienne simulation
        return c["gain_un_revenu"], c["gain_deux_revenus"]
    cle = (repr(p.val("impot_unique.seuils")), repr(p.val("impot_unique.taux")), c["correlation"],
           facteur_alignement_public(p), repr(effectifs_prive_2026(p).milieux[:3]), sum(effectifs_prive_2026(p).effectifs))
    if cle not in _GAINS:
        _GAINS[cle] = gains_conjugaux(p)
    return _GAINS[cle]


def cout(p: Parametres) -> dict[str, float]:
    from ..recettes.tva_menages import lire_inactifs
    enfants = p.val("rui_complements.enfants") + p.val("rui_complements.enfants_parent_isole")
    familial = enfants * p.val("quotient.part_enfants_parent_imposable") * gain_moyen_par_enfant(p) / 1e9
    c = p.val("quotient.conjugal")
    g1, g2 = gains(p)
    conjugal = c["couples"] * (c["part_un_revenu"] * g1 + (1 - c["part_un_revenu"]) * g2) / 1e9 + c["retraites_forfait"]
    r = p.val("quotient.rui_conjoint")
    rui = p.val("rui.montant") * 12
    plafond = p.val("inactifs.revenu_annulant_rui") * 12
    revenus, effectifs = lire_inactifs()
    rui_inactifs = sum(n * max(0.0, (plafond - x) / plafond * rui) for x, n in zip(revenus, effectifs))
    complement_moyen = rui_inactifs / r["inactifs_feuille_rui"]
    economie_rui = r["inactifs_en_couple"] * complement_moyen * r["part_supprimee"] * r["part_nette_tva"] / 1e9
    total = familial * p.val("quotient.familial_applique") + conjugal * c["applique"] - economie_rui
    return {"familial": familial, "conjugal": conjugal, "economie_rui_conjoint": economie_rui, "total": total}
