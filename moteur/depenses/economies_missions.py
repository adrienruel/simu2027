"""Économies sur les missions conservées et mesures d'éducation (Budget État 2026 D105 et D111 ; feuille Éducation)."""
from __future__ import annotations

from ..parametres import Parametres
from . import budget_etat


def education(p: Parametres) -> dict[str, float]:
    e = p.val("education.chefs_etablissement")
    t = p.val("education.tenue_commune")
    u = p.val("education.universite")
    r = p.val("education.connaissance_religions")
    return {
        "demographie": p.val("education.baisse_enseignants") * p.val("education.enseignants") * p.val("education.cout_enseignant_aligne") / 1e9,
        "chefs": -e["personnes"] * e["hausse_nette_mensuelle"] * 12 * e["coefficient_charge"] / 1e9,
        "plateforme_ia": -p.val("education.plateforme_ia"),
        "formation_ia": -p.val("education.formation_ia"),
        "tenue": -t["eleves"] * t["prix_kit"] / t["annees_kit"] * t["part_etat"] / 1e9,
        "annees_supplementaires": u["part_annees_supplementaires"] * u["etudiants"] * u["cout_etudiant"] / 1e9,
        "selection": u["etudiants"] * u["cout_etudiant"] / 1e9,
        "religions": -(r["professeurs"] * r["jours_formation"] * r["cout_jour"] / r["annees_amortissement"]
                       + r["professeurs"] / r["renouvellement_formation"] * r["jours_formation"] * r["cout_jour"]
                       + r["eleves_4e"] * r["prix_manuel"] / r["renouvellement_manuel"]) / 1e9,
    }


def economies(p: Parametres) -> dict[str, float]:
    """(D105, D111) : économies sur les missions et autres économies (Md€)."""
    from ..collectivites import environnement
    from ..objectifs import demi_rui_chez_parents
    couts = {m["mission"]: m["cout"] for m in budget_etat.couts_par_mission(p)}
    ed = education(p)
    d105 = 0.0
    for x in p.val("economies_missions.coupes").values():
        b = x["base"]
        if isinstance(b, str) and b.startswith("mission:"):
            b = couts[b.split(":", 1)[1]]
        elif isinstance(b, str) and b.startswith("education:"):
            b = ed[b.split(":", 1)[1]]
        d105 += b * x["part"]
    d105 += environnement(p)["economie_etat"]
    cp = p.val("collectivites_detail.carence_poids")
    carence = cp["economie_etat_hopitaux"] * (cp["etat"] + cp["hospitaliere"]) / (cp["etat"] + cp["territoriale"] + cp["hospitaliere"])
    d111 = (ed["demographie"] * p.val("economies_missions.education_demographie_part")
            + ed["chefs"] + ed["plateforme_ia"] + ed["formation_ia"] + ed["tenue"] + ed["religions"]
            + demi_rui_chez_parents(p) + carence)
    return {"missions": d105, "autres": d111}
