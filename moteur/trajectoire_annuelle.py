"""Trajectoire 2029-2073 : du budget statique aux comptes de chaque année (feuille Trajectoire, lignes 17 à 22 et 43).

Chaque poste part de son niveau statique (feuille Total) et évolue avec la croissance tendancielle,
les mesures datées (feuille Objectifs, coût de transition, renouvelables, IA) et les feuilles annexes.
Le solde primaire hors effets macro qui en résulte alimente le module macro.
"""
from __future__ import annotations

import json
from pathlib import Path

from .parametres import Parametres
from .recettes.total import recettes_nouveau_systeme
from .depenses.statique import depenses
from .depenses import ia_administration
from .retraites_transition import cout_transition, cout_socle, _csv as _csv_retraites

ANNEES = list(range(2029, 2074))
PROVISOIRES = Path(__file__).resolve().parents[1] / "reference" / "entrees_provisoires_trajectoire.json"


def _prov():
    return json.loads(PROVISOIRES.read_text(encoding="utf-8"))


def _macro_prov():
    from .macro import _prov as mp
    return mp()


def postes(p: Parametres, scenario_retenu: str = "prudent") -> dict[int, dict]:
    pv = _prov()
    g = p.val("macro.tendance", "prudent")
    infl = p.val("calendrier.inflation")
    rec = recettes_nouveau_systeme(p)["total"] / 1e9
    dep = depenses(p)
    l = dep["lignes"]
    ct = cout_transition(p)
    socle = cout_socle(p)
    ia = ia_administration.economie_nette(p)
    anc = {int(x["annee"]): x for x in _csv_retraites("ancien_systeme_retraites.csv")}
    serie = lambda cle: dict(zip(ANNEES, pv[cle]["serie"]))
    from .recettes import successions, autres
    succ = successions.supplement(p, autres.ligne_8_successions(p) / 1e9)
    from .ascenseur_social import annuel as ascenseur
    asc = ascenseur(p, autres.ligne_8_successions(p) / 1e9, p.val("successions.exoneration_entreprises"))
    asc_r, asc_d = {t: v["recettes"] for t, v in asc.items()}, {t: v["depenses"] for t, v in asc.items()}
    from .mesures import economies
    eco = economies(p)
    from . import sante as module_sante
    sante, gf = module_sante.depenses(p, scenario_retenu), module_sante.garde_fou(p, scenario_retenu)
    from . import objectifs
    anc_p = serie("anciennes_pensions")
    etu = objectifs.rui_etudiants(p)
    tva2028 = {t: objectifs.surcroit_tva_2028(p, t)[0] for t in ANNEES}
    rendu = {t: objectifs.surcroit_tva_2028(p, t)[1] for t in ANNEES}
    gel = {t: objectifs.fin_gel(p, t) for t in ANNEES}
    em = pv["emploi_cout_reformes"]
    is_inv = dict(zip(ANNEES, _macro_prov()["is_investissement_etalement"]["b41"]))
    # Renouvelables (Budget État 2026, lignes 136 à 144)
    soutien_2026, soutien_2029 = p.val("renouvelables.soutien_budget_2026"), p.val("renouvelables.soutien_2029")
    fin = p.val("renouvelables.derniere_signature") + p.val("renouvelables.duree_contrats")
    prod = {t: (1 + p.val("macro.productivite", scenario_retenu)) ** max(0, min(p.val("macro.annees_productivite", scenario_retenu),
                                                                            t - p.val("macro.premiere_annee_productivite") + 1)) - 1
            for t in ANNEES}
    autres_base = (dep["total"] - l["sante"] - l["retraites_socle"] - l["rui_aah"] - l["cout_transition_moyen"]
                   - l["charge_dette"] - l["subventions_restees"])
    # Total!B44 + B72 : le total compte l'IA en déduction ; on la rajoute puis on la retranche année par année
    autres_base += -l["ia_administration"]
    out = {}
    for t in ANNEES:
        n = t - 2029
        recettes_hors_macro = rec * (1 + g * 1) ** n + succ[t] + tva2028[t] - rendu[t] + asc_r[t] + anc_p[t] - is_inv[t]
        reval_rui = (((1 + g) / (1 + infl)) ** n * (1 + prod[t]) - 1) if p.val("revalorisation.rui_aah_socle_croissance") else 0.0
        ancien_86 = anc[t]["depenses_desindexees_md"] * anc[t]["part_ancien_systeme"]
        pensions_min = (p.val("revalorisation.part_pensions_sous_seuil") * ancien_86 * ((1 + g) ** (t - 2028) - 1)
                        if p.val("revalorisation.pensions_sous_minimum_vieillesse") else 0.0)
        cout_emploi = (em["g24"] - em["b155"] * (t > em["b154"])) * (1 + g) ** n
        out[t] = {
            "recettes_hors_macro": recettes_hors_macro,
            "sante": sante[t] - gf[t],
            "retraites": l["retraites_socle"] + ct[t]["net"] + pensions_min + socle[t] * reval_rui + gel[t],
            "rui_aah": l["rui_aah"] + l["rui_aah"] * reval_rui + etu[t],
            "investissement": l["subventions_restees"] - soutien_2026 + soutien_2029 * max(0, (fin - t) / (fin - 2029)),
            "autres": autres_base * (1 + g) ** n - ia[t] * (1 + g) ** n + cout_emploi + asc_d[t] - eco[t],
        }
        o = out[t]
        o["solde_primaire_hors_macro"] = o["recettes_hors_macro"] - (o["sante"] + o["retraites"] + o["rui_aah"] + o["investissement"] + o["autres"])
    return out
