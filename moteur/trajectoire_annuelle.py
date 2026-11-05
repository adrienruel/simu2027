"""Trajectoire 2029-2073 : du budget statique aux comptes de chaque année (feuille Trajectoire, lignes 17 à 22 et 43).

Chaque poste part de son niveau statique (feuille Total) et évolue avec la croissance tendancielle,
les mesures datées (feuille Objectifs, coût de transition, renouvelables, IA) et les feuilles annexes.
Le solde primaire hors effets macro qui en résulte alimente le module macro.
"""
from __future__ import annotations


from .parametres import Parametres
from .recettes.total import recettes_nouveau_systeme
from .depenses.statique import depenses
from .depenses import ia_administration
from .retraites_transition import cout_transition, cout_socle

ANNEES = list(range(2029, 2074))


def postes(p: Parametres, scenario_retenu: str = "prudent") -> dict[int, dict]:
    g = p.val("macro.tendance", "prudent")
    infl = p.val("calendrier.inflation")
    _rns = recettes_nouveau_systeme(p)
    rec = _rns["total"] / 1e9
    # parts des recettes statiques qui ne suivent pas l'emploi (relecture du 29/10/2026), indice 1 :
    # - impôt et TVA des retraités en croisière : anciennes_pensions.recette_nette les ramène déjà au nombre de
    #   retraités du nouveau système de chaque année (population de l'Insee) ;
    # - recette carbone statique (carbone.recette_statique) : carbone.effet_solde la retranche sans indice
    #   démographique ; on retire la part déjà dans la TVA des retraités (même part que dans la ligne 3).
    # Le reste suit les personnes en emploi.
    if p.val("macro.corrections_relecture"):
        from .recettes import tva_menages
        from .carbone import recette_statique as recette_carbone
        tva_ret = tva_menages.tva_retraites(p)
        part_ret = tva_ret / _rns["lignes"][3]
        rec_ret = (_rns["lignes"][5] + tva_ret) / 1e9 + recette_carbone(p) * (1 - part_ret)
    else:
        rec_ret = 0.0
    rec_pop = 0.0
    # impôt unique et TVA des salariés (privé et public) : suivent les cellules de salariés (âge, salaire)
    from .recettes import tva_menages as _tm
    from .recettes.impot_salaires import impot_prive as _ip, impot_public as _ipu
    rec_sal_impot = (_ip(p) + _ipu(p)) / 1e9
    rec_sal_tva = (_tm.tva_prive(p) + _tm.tva_public(p)) / 1e9
    rec_emp = rec - rec_ret - rec_pop - rec_sal_impot - rec_sal_tva
    dep = depenses(p)
    l = dep["lignes"]
    ct = cout_transition(p)
    socle = cout_socle(p)
    from .ancien_systeme import contribution_solidarite
    contrib_anciens = contribution_solidarite(p)
    from .retraites_transition import attente_rui_et_socle
    attente = attente_rui_et_socle(p)
    ia = ia_administration.economie_nette(p)
    from .ancien_systeme import depenses as depenses_ancien
    anc = depenses_ancien(p)
    from .recettes import successions, autres
    succ = successions.supplement(p, autres.ligne_8_successions(p) / 1e9)
    from .ascenseur_social import annuel as ascenseur
    asc = ascenseur(p, autres.ligne_8_successions(p) / 1e9, p.val("successions.exoneration_entreprises"))
    asc_r, asc_d = {t: v["recettes"] for t, v in asc.items()}, {t: v["depenses"] for t, v in asc.items()}
    from .mesures import economies_par_mesure
    eco_detail = economies_par_mesure(p)
    from . import sante as module_sante
    sante, gf = module_sante.depenses(p, scenario_retenu), module_sante.garde_fou(p, scenario_retenu)
    from . import objectifs
    from .anciennes_pensions import recette_nette
    anc_p = recette_nette(p)
    etu = objectifs.rui_etudiants(p)
    tva2028 = {t: objectifs.surcroit_tva_2028(p, t)[0] for t in ANNEES}
    rendu = {t: objectifs.surcroit_tva_2028(p, t)[1] for t in ANNEES}
    gel = {t: objectifs.fin_gel(p, t) for t in ANNEES}
    from .emploi import cout_reformes, cout_prime_jeunes
    em = {"g24": cout_reformes(p), "b155": cout_prime_jeunes(p) * p.val("emploi.retenues_calculees")["prime_jeunes"],
          "b154": p.val("emploi.prime_jeunes")["derniere_annee"]}
    from .is_investissement import cout_net_etat
    is_inv = cout_net_etat(p)
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
    from .demographie import indices
    from .depenses.statique import rui_enfants
    demo = indices(p, "prudent")
    # quotient familial et conjugal, RUI du conjoint : suivent les enfants et les couples (cellules de ménages)
    # au lieu de la population totale, comme le reste des autres dépenses
    menages_idx = None
    if p.val("cohortes.active") and p.val("demographie.active"):
        from .cohortes import menages
        from .depenses import quotient as _quotient
        qc = _quotient.cout(p)
        qcj = p.val("quotient.conjugal")
        g_conj = qc["conjugal"] - qcj["retraites_forfait"]
        mn = menages(p, "prudent")
        # coût conjugal proportionnel aux couples pondérés par leur gain moyen (un revenu / deux revenus)
        g1, g2 = _quotient.gains(p)
        conj = {t: mn[t]["couples"] * (mn[t]["part_un_revenu"] * g1 + (1 - mn[t]["part_un_revenu"]) * g2) for t in mn}
        menages_idx = {t: {"familial": qc["familial"] * p.val("quotient.familial_applique"), "conjugal": g_conj * qcj["applique"],
                           "eco_rui": qc["economie_rui_conjoint"],
                           "i_conj": conj[t] / conj[2029], "i_sans": mn[t]["sans_emploi_en_couple"] / mn[2029]["sans_emploi_en_couple"]}
                       for t in ANNEES}
    rui_enf = rui_enfants(p)
    from .depenses.statique import rui_salaries as _rui_salaries
    rui_sal = _rui_salaries(p)
    from .demographie import creches_nouvelles
    creches = creches_nouvelles(p)
    from .macro import flux_epargne_obligatoire
    contrib = p.val("epargne.contribution_transition") * flux_epargne_obligatoire(p) / 1e9 if p.val("epargne.contribution_transition") else 0.0
    # revalorisation de la RUI, de l'AAH et du socle (moteur/inflation.indice_reel : règle d'indexation)
    from .inflation import indice_reel
    idx_reel = indice_reel(p, scenario_retenu)

    def reval(t):
        return (idx_reel[t] - 1) if p.val("revalorisation.rui_aah_socle_croissance") else 0.0

    mins = None
    if p.val("ministeres.par_public") and p.val("demographie.active"):
        from .depenses.ministeres import trajectoire as _traj_ministeres
        mins = _traj_ministeres(p)
    L = Lignes()
    for t in ANNEES:
        n = t - 2029
        crois = (1 + g) ** n
        reval_rui = reval(t)
        ancien_86 = anc[t]
        pensions_min = (p.val("revalorisation.part_pensions_sous_seuil") * ancien_86 * ((1 + g) ** (t - 2028) - 1)
                        if p.val("revalorisation.pensions_sous_minimum_vieillesse") else 0.0)
        # Recettes (montants positifs)
        L.ajouter(t, "recettes", "recettes_nouveau_systeme", "Recettes du nouveau système : point de départ (2029)", "socle", rec)
        L.ajouter(t, "recettes", "recettes_croissance", "Recettes : croissance tendancielle", "croissance", rec * (crois - 1))
        d = demo[t]
        L.ajouter(t, "recettes", "recettes_demographie", "Recettes : démographie (actifs, retraités, population)", "demographie",
                  crois * (rec_emp * (d["emploi"] - 1) + rec_pop * (d["total"] - 1)
                           + rec_sal_impot * (d["c_impot"] - 1) + rec_sal_tva * (d["c_tva"] - 1)))
        L.ajouter(t, "recettes", "contribution_transition", "Épargne obligatoire versée à l'État (contribution de transition)",
                  "mesure", contrib * crois * d["emploi"])
        L.ajouter(t, "recettes", "successions", "Successions : supplément", "mesure", succ[t])
        L.ajouter(t, "recettes", "tva_2028", "TVA de 2028 maintenue", "mesure", tva2028[t])
        L.ajouter(t, "recettes", "tva_2028_rendue", "TVA de 2028 rendue par le barème", "mesure", -rendu[t])
        L.ajouter(t, "recettes", "ascenseur_recettes", "Ascenseur social : recettes", "mesure", asc_r[t])
        L.ajouter(t, "recettes", "anciennes_pensions", "Anciennes pensions : prélèvement net", "mesure", anc_p[t])
        L.ajouter(t, "recettes", "is_investissement", "IS : déduction de l'investissement", "mesure", -is_inv[t])
        # Dépenses (montants positifs = dépense)
        L.ajouter(t, "sante", "sante_trajectoire", "Santé : trajectoire des dépenses", "trajectoire", sante[t])
        L.ajouter(t, "sante", "sante_garde_fou", "Santé : accise sur les produits nocifs (surplus au-delà du PIB) et soins évités"
                  if p.val("sante_produits_nocifs.active") else "Santé : garde-fou", "mesure", -gf[t])
        L.ajouter(t, "retraites", "retraites_socle", "Retraites : socle, point de départ (2029)", "socle", l["retraites_socle"])
        L.ajouter(t, "retraites", "transition_retraites", "Transition des retraites : coût net", "trajectoire", ct[t]["net"])
        L.ajouter(t, "retraites", "contribution_anciens_retraites", "Contribution de solidarité des retraités de l'ancien système (5 à 10 %)",
                  "mesure", -contrib_anciens[t] * (1 - p.val("ancien_systeme.contribution_solidarite")["fuite"]))
        L.ajouter(t, "retraites", "pensions_sous_minimum", "Pensions sous le minimum vieillesse : revalorisation", "mesure", pensions_min)
        L.ajouter(t, "retraites", "socle_revalorisation", "Socle : revalorisation (règle d'indexation)", "croissance", socle[t] * reval_rui)
        L.ajouter(t, "retraites", "fin_gel", "Fin du gel des anciennes pensions", "mesure", gel[t])
        L.ajouter(t, "rui_aah", "rui_aah_socle", "RUI et AAH : point de départ (2029)", "socle", l["rui_aah"])
        L.ajouter(t, "rui_aah", "rui_aah_revalorisation", "RUI et AAH : revalorisation (règle d'indexation)", "croissance", l["rui_aah"] * reval_rui)
        L.ajouter(t, "rui_aah", "rui_aah_demographie", "RUI : démographie (adultes, enfants)", "demographie",
                  ((l["rui_aah"] - rui_enf - rui_sal) * (d["adultes"] - 1) + rui_sal * (d["c_rui"] - 1)
                   + rui_enf * (d["enfants"] - 1)) * (1 + reval_rui))
        L.ajouter(t, "retraites", "attente_age_legal_67", "Entre l'âge légal et 67 ans : RUI ou socle selon les annuités", "mesure",
                  attente[t] * (1 + reval_rui))
        L.ajouter(t, "rui_aah", "rui_etudiants", "RUI étudiant sous condition de ressources", "mesure", etu[t])
        L.ajouter(t, "investissement", "subventions_restees", "Subventions d'investissement restées à l'État", "socle", l["subventions_restees"] - soutien_2026)
        L.ajouter(t, "investissement", "renouvelables", "Soutien aux renouvelables (contrats en cours)", "trajectoire", soutien_2029 * max(0, (fin - t) / (fin - 2029)))
        L.ajouter(t, "autres", "autres_socle", "Autres dépenses : point de départ (2029)", "socle", autres_base)
        if mins:
            # ministères : chaque groupe de missions selon sa règle (croissance et public servi, PIB ou prix) ;
            # le quotient familial garde la croissance et la population (ses lignes de ménages font le reste)
            qf = l["quotient_familial"]
            L.ajouter(t, "autres", "autres_croissance", "Quotient familial et conjugal : croissance tendancielle", "croissance", qf * (crois - 1))
            L.ajouter(t, "autres", "autres_demographie", "Quotient familial et conjugal : démographie (population)", "demographie",
                      qf * crois * (d["total"] - 1))
            for gr_, v_ in sorted(mins["groupes"].items(), key=lambda kv: -kv[1]["depart"]):
                L.ajouter(t, "autres", "ministere:" + gr_, f"Ministères — {gr_} : évolution (croissance, public servi, PIB ou prix)",
                          "croissance", v_["valeurs"][t] - v_["depart"])
        else:
            L.ajouter(t, "autres", "autres_croissance", "Autres dépenses : croissance tendancielle", "croissance", autres_base * (crois - 1))
            L.ajouter(t, "autres", "autres_demographie", "Autres dépenses : démographie (population)", "demographie",
                      autres_base * crois * (d["total"] - 1))
        L.ajouter(t, "autres", "creches_nouvelles", "Crèches : places créées (fonctionnement et construction)", "mesure",
                  creches[t])
        if menages_idx:
            mi = menages_idx[t]
            L.ajouter(t, "autres", "menages_demographie", "Quotient familial et conjugal, RUI du conjoint : enfants et couples",
                      "demographie", crois * (mi["familial"] * (d["enfants"] - d["total"]) + mi["conjugal"] * (mi["i_conj"] - d["total"])
                                              - mi["eco_rui"] * (mi["i_sans"] - d["total"])))
        L.ajouter(t, "autres", "ia_administration", "IA dans l'administration : économie", "mesure", -ia[t] * crois)
        L.ajouter(t, "autres", "reformes_emploi", "Réformes de l'emploi : coût", "mesure", (em["g24"] - em["b155"] * (t > em["b154"])) * crois)
        L.ajouter(t, "autres", "ascenseur_depenses", "Ascenseur social : dépenses", "mesure", asc_d[t])
        for nom, v in eco_detail.items():
            # mesures sur les pensions de l'ancien système : poste « retraites » (v235 : « autres »)
            poste_ = ("retraites" if (nom.startswith("Ancien système") and p.val("ministeres.par_public"))
                      else "sante" if nom.startswith("Santé") else "autres")
            L.ajouter(t, poste_, "economie:" + nom[:60], nom, "mesure", -v[t])
    # Bases des lignes démographiques, pour recalculer l'effet dans les autres scénarios (macro)
    L.bases_demographie = {t: {"recettes": rec_emp * (1 + g) ** (t - 2029),
                               "recettes_population": rec_pop * (1 + g) ** (t - 2029),
                               "salaries_impot": rec_sal_impot * (1 + g) ** (t - 2029),
                               "salaries_tva": rec_sal_tva * (1 + g) ** (t - 2029),
                               "salaries_rui": -rui_sal * (1 + reval(t)),
                               "adultes": -(l["rui_aah"] - rui_enf - rui_sal) * (1 + reval(t)),
                               "enfants": -rui_enf * (1 + reval(t)),
                               "total": -((l["quotient_familial"] + mins["part_total"]) if mins else autres_base) * (1 + g) ** (t - 2029),
                               **({"enfants": -rui_enf * (1 + reval(t)) - mins["part_enfants"] * (1 + g) ** (t - 2029)} if mins else {})}
                          for t in ANNEES}
    p.__dict__.setdefault("_cache", {})[("lignes", scenario_retenu)] = L
    return L.postes()


POSTES_DEPENSES = ("sante", "retraites", "rui_aah", "investissement", "autres")


class Lignes:
    """Le budget d'une année comme une liste de lignes datées (registre) : poste, nature, montant (Md€ de 2026).

    nature : socle (budget statique de la feuille Total), croissance (évolution tendancielle du socle),
    trajectoire (dépense qui suit sa propre dynamique), mesure (loi ou décision datée).
    Les recettes sont comptées positivement, les dépenses aussi (le solde est recettes − dépenses).
    """

    def __init__(self):
        self.lignes: dict[str, dict] = {}

    def ajouter(self, t: int, poste: str, cle: str, libelle: str, nature: str, montant: float) -> None:
        x = self.lignes.setdefault(cle, {"cle": cle, "libelle": libelle, "poste": poste, "nature": nature, "valeurs": {}})
        x["valeurs"][t] = x["valeurs"].get(t, 0.0) + montant

    def postes(self) -> dict[int, dict]:
        out = {t: {"recettes_hors_macro": 0.0, **{k: 0.0 for k in POSTES_DEPENSES}} for t in ANNEES}
        for x in self.lignes.values():
            k = "recettes_hors_macro" if x["poste"] == "recettes" else x["poste"]
            for t, v in x["valeurs"].items():
                out[t][k] += v
        for o in out.values():
            o["solde_primaire_hors_macro"] = o["recettes_hors_macro"] - sum(o[k] for k in POSTES_DEPENSES)
        return out

    def effet_sur_solde(self, cle: str, t: int) -> float:
        x = self.lignes[cle]
        return x["valeurs"].get(t, 0.0) * (1 if x["poste"] == "recettes" else -1)


def lignes(p: Parametres, scenario_retenu: str = "prudent") -> Lignes:
    """Le registre des lignes de la trajectoire (calculé une fois par jeu de paramètres)."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("lignes", scenario_retenu) not in cache:
        postes(p, scenario_retenu)
    return cache[("lignes", scenario_retenu)]
