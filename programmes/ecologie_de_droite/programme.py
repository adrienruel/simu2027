"""« Écologie de droite » branché sur le noyau commun (moteur/noyau.py), 4 novembre 2026.

Première étape du rebranchement : le programme garde son propre moteur (moteur/macro.py, moteur/trajectoire_annuelle.py,
qui chiffrent son budget ligne par ligne) et il est traduit en mesures contre le statu quo :

- chaque poste de son budget remplace les blocs correspondants du statu quo (écart = budget du programme − statu
  quo) : retraites, santé, investissement un pour un ; le revenu universel et l'AAH remplacent l'assurance chômage,
  la famille, le logement, la pauvreté et l'AAH ; les autres dépenses remplacent les missions, l'enseignement et le
  reste ;
- ses effets macroéconomiques sont des mesures de recettes, une par canal (emploi, capital du fonds, érosion de
  l'IS…), règle de trajectoire comprise ;
- le périmètre est aligné sur celui du statu quo (toutes les administrations) : les collectivités, que le programme
  sort de son budget, y sont remises (dépenses et ressources propres, même montant : solde inchangé) ;
- son contexte : PIB, inflation (récession de 2029, carbone), baisse de l'écart de taux, chômage, dette de fin 2028
  (mesures de 2028), participations remises au fonds.

Mesure à isoler quand le programme sera codé mesure par mesure (DÉCISION d'Adrien du 04/11/2026) : le revenu
universel revalorisé sur les prix, alors que le statu quo garde le niveau des prestations par rapport aux salaires ;
c'est un objectif assumé du programme (baisse relative de ces prestations dans le temps), pas une convention.

Le noyau recalcule alors les intérêts, la dette et le déficit : il doit retrouver exactement les résultats du moteur
du programme (tests/test_noyau.py). L'écart de 2029 entre le budget du programme et le statu quo, poste par poste,
mêle les mesures et les différences de méthode (budget ligne par ligne contre agrégats du PLF 2027) : il est montré
par `ecart_de_depart`. Étapes suivantes : remplacer ces écarts globaux par des mesures codées une à une sur le noyau.
"""
from __future__ import annotations

from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres

# poste du programme → blocs du statu quo qu'il remplace
CORRESPONDANCE = {
    "retraites": ("retraites",),
    "sante": ("sante",),
    "investissement": ("investissement",),
    "rui_aah": ("chomage", "famille", "logement", "pauvrete", "aah_invalidite"),
    "autres": ("etat_missions", "defense_ue", "collectivites", "autres"),
}
LIBELLES = {
    "retraites": "Retraites : socle, transition et ancien système",
    "sante": "Santé : trajectoire et mesures",
    "investissement": "Investissement : subventions restées à l'État, renouvelables",
    "rui_aah": "Revenu universel et AAH",
    "autres": "Autres dépenses du programme (ministères, collectivités, mesures)",
}


def collectivites_hors_budget(p: Parametres) -> dict[str, float]:
    """Collectivités dans le nouveau système (Md€ de 2026, 2029) : elles sortent du budget du programme, financées par
    l'impôt local unique, l'IS local et leurs ressources restantes ; seul leur besoin de financement reste au déficit.

    Dépenses = dépenses actuelles des administrations locales (statu_quo.apul_depenses_2026) + charges reprises par
    l'État et économies (mêmes postes que moteur/collectivites.besoin : RSA, aide sociale à l'enfance, autonomie,
    investissements repris par le fonds, alignement du coût des agents, IA, réorganisation…) − gains « même doctrine »
    + hébergement d'urgence à leur charge. Ressources propres = dépenses − besoin de financement laissé au déficit."""
    from moteur.unites import facteur
    charges = sum(x["communes"] + x["regions"] for x in p.val("collectivites_detail.charges_fixes").values())
    sante_brut = p.val("sante.aide_sociale_autonomie_2024") * facteur(p, 2024, "recettes") * (1 if p.val("sante.reprise_autonomie_par_etat") else 0)
    charges += -p.val("collectivites_detail.aide_sociale_enfance") - sante_brut
    ms = p.val("collectivites_detail.masse_salariale_agents")
    t_ = p.val("alignement.charges_patronales_prive")
    v = p.val("alignement.versants")["territoriale"]
    baisse_terr = (1 + t_) / (1 + v["charges_actuelles"]) - 1
    ia = p.val("ia.plafond_taches_automatisables") * (1 - p.val("ia.cout_services_ia"))
    charges += sum(ms[k] * baisse_terr - ms[k] * p.val("collectivites_detail.part_agents_gestion") * ia for k in ("communes", "regions"))
    gains = sum(x["gain"] for x in p.val("collectivites_detail.meme_doctrine").values())
    hu = p.val("collectivites_detail.hebergement_urgence")
    depenses = p.val("statu_quo.apul_depenses_2026") + charges - gains + hu["montant"] * (1 - hu["part_etat"])
    bf = sum(p.val("collectivites.besoin_financement_2024")) * (1 - p.val("collectivites.part_financee")) * facteur(p, 2024, "recettes")
    return {"depenses": depenses, "besoin_financement": bf, "ressources": depenses - bf}


def decomposition_collectivites(p: Parametres) -> dict[str, float]:
    """Dépenses des collectivités en 2029 (Md€ de 2026) : programme (collectivites_hors_budget) contre statu quo (bloc
    collectivités + investissement local), poste par poste. Les postes reclassés (RSA, autonomie) sont dans les deux."""
    from moteur import statu_quo as sq
    from moteur.unites import facteur
    d = sq.depart(p)["blocs"]
    inv_loc = p.val("statu_quo.investissement_parts")["collectivites"] * d["investissement"]
    cf = p.val("collectivites_detail.charges_fixes")
    ms = p.val("collectivites_detail.masse_salariale_agents")
    t_ = p.val("alignement.charges_patronales_prive")
    v = p.val("alignement.versants")["territoriale"]
    baisse_terr = (1 + t_) / (1 + v["charges_actuelles"]) - 1
    ia = p.val("ia.plafond_taches_automatisables") * (1 - p.val("ia.cout_services_ia"))
    hu = p.val("collectivites_detail.hebergement_urgence")
    out = {"statu quo (collectivités + investissement local)": d["collectivites"] + inv_loc,
           "RSA : écart de périmètre (11,5 retirés contre 11,8 dans le statu quo)":
               sum(cf["rsa"].values()) + (p.val("statu_quo.rsa") - 1.7)}
    for k, x in cf.items():
        if k != "rsa":
            out[k.replace("_", " ")] = x["communes"] + x["regions"]
    out["aide sociale à l'enfance (reprise par l'État)"] = -p.val("collectivites_detail.aide_sociale_enfance")
    out["coût des agents aligné sur le privé"] = sum(ms[k] * baisse_terr for k in ("communes", "regions"))
    out["IA (agents de gestion)"] = -sum(ms[k] * p.val("collectivites_detail.part_agents_gestion") * ia for k in ("communes", "regions"))
    for k, x in p.val("collectivites_detail.meme_doctrine").items():
        out[f"même doctrine : {k.replace('_', ' ')}"] = -x["gain"]
    out["hébergement d'urgence à leur charge"] = hu["montant"] * (1 - hu["part_etat"])
    out["programme"] = collectivites_hors_budget(p)["depenses"]
    out["contrôle (doit être nul)"] = out["programme"] - sum(v for k, v in out.items() if k != "programme")
    return out


# recettes du programme, instrument par instrument, contre les impôts actuels qu'elles remplacent (statu quo)
INSTRUMENTS = [
    ("iu_prive", "Impôt unique sur les salaires du privé (remplace cotisations, CSG, IR des salariés)", ("salaires_prive",)),
    ("iu_public", "Impôt unique sur les rémunérations publiques (remplace cotisations, CSG, IR des agents)", ("salaires_public",)),
    ("iu_independants", "Indépendants en société : impôt unique ou IS (remplace cotisations, CSG, IR)", ("independants",)),
    ("iu_retraites", "Impôt unique des retraités du nouveau système (remplace CSG, CASA, IR des pensions)", ("retraites",)),
    ("tva", "TVA écologique et santé, accises (remplace TVA et accises actuelles)", ("tva", "accises_et_taxes_sur_produits")),
    ("entreprises", "IS à 45 %, fin des impôts de production, accises carbone des entreprises", ("impot_sur_les_societes", "impots_de_production")),
    ("capital", "Flat tax sur les dividendes, revenus du capital, bailleurs ; fin de l'IFI", ("capital_dividendes_ifi",)),
    ("successions", "Successions (transmissions d'entreprises exonérées)", ("successions",)),
    ("contribution", "Contribution d'épargne retraite et recettes non fiscales gardées au budget", ()),
    ("fin_dmto", "Fin des droits de mutation, des taxes locales et affectées (remplacés par l'impôt local)",
     ("droits_de_mutation", "taxes_locales_et_affectees")),
    ("fin_non_fiscales", "Recettes non fiscales actuelles (versées au fonds ; part locale remise par le périmètre)", ("non_fiscales",)),
]


def recettes_par_instrument(q: Parametres) -> dict[int, dict[str, float]]:
    """Recettes du programme hors mesures datées (Md€ de 2026), instrument par instrument, chaque année : lignes du
    budget statique (recettes/total.py) et la même évolution que moteur/trajectoire_annuelle.postes (croissance ;
    impôt unique des salariés selon les cellules ; TVA des salariés selon les cellules ; retraités et part carbone
    hors TVA des retraités : indice 1 ; le reste selon les personnes en emploi). La somme est exactement celle des
    trois lignes « point de départ », « croissance » et « démographie » du registre du programme."""
    from moteur.carbone import recette_statique
    from moteur.demographie import indices
    from moteur.recettes import tva_menages
    from moteur.recettes.entreprises import tva_non_deductible
    from moteur.recettes.total import recettes_nouveau_systeme
    from moteur.unites import facteur
    r = recettes_nouveau_systeme(q)
    l = {k: v / 1e9 for k, v in r["lignes"].items()}
    fac = facteur(q, 2024, "recettes")
    tva_ent = tva_non_deductible(q) / 1e9
    tva_sal = (tva_menages.tva_prive(q) + tva_menages.tva_public(q)) / 1e9
    tva_ret = tva_menages.tva_retraites(q) / 1e9
    corr = q.val("macro.corrections_relecture")
    carb = recette_statique(q) * (1 - tva_ret / l[3]) if corr else 0.0
    tva_tot = (l[3] - tva_ent) + tva_ent * fac
    base = {  # (montant, part suivant l'emploi, part impôt des salariés, part TVA des salariés, part à indice 1)
        "iu_prive": (l[4], 0.0, l[4], 0.0, 0.0),
        "iu_public": (l[6], 0.0, l[6], 0.0, 0.0),
        "iu_independants": (l[16], l[16], 0.0, 0.0, 0.0),
        "iu_retraites": (l[5], 0.0, 0.0, 0.0, l[5] if corr else 0.0),
        "tva": (tva_tot, tva_tot - tva_sal - (tva_ret + carb if corr else 0.0), 0.0, tva_sal, (tva_ret + carb) if corr else 0.0),
        "entreprises": ((l[2] + l[15]) * fac, (l[2] + l[15]) * fac, 0.0, 0.0, 0.0),
        "capital": ((l[7] + l[19] + l[20]) * fac, (l[7] + l[19] + l[20]) * fac, 0.0, 0.0, 0.0),
        "successions": (l[8] * fac, l[8] * fac, 0.0, 0.0, 0.0),
        "contribution": (l[9], l[9], 0.0, 0.0, 0.0),
    }
    if not corr:  # sans les corrections de la relecture, les retraités suivent l'emploi
        base["iu_retraites"] = (l[5], l[5], 0.0, 0.0, 0.0)
    g = q.val("macro.tendance", "prudent")
    d = indices(q, "prudent")
    out = {}
    for t in ANNEES:
        crois = (1 + g) ** (t - 2029)
        x = d[t]
        out[t] = {k: crois * (emp * x["emploi"] + imp * x["c_impot"] + tv * x["c_tva"] + un)
                  for k, (_, emp, imp, tv, un) in base.items()}
    return out


def recalcul_noyau_salaries(p: Parametres, q: Parametres, s_cellules: str) -> dict:
    """Deuxième passe : impôt unique des salariés (privé, public aligné) et TVA des salariés recalculés sur les
    cellules communes du statu quo (statu_quo.agreger_cellules : même population, mêmes âges et salaires), au niveau
    du budget statique du programme (distributions de 2026) et avec l'évolution des cellules (salaires, hors IA,
    que le moteur du programme compte dans son canal macro).

    Rend aussi ces mêmes postes dans le moteur du programme, avec et sans son effet sur les naissances, pour isoler
    cet effet en mesure à part. Contrôle (4/11/2026) : sans l'effet sur les naissances et sans l'IA, le noyau retrouve
    le moteur du programme à 0,1 % près jusqu'en 2073."""
    from moteur import statu_quo as sq
    from moteur.demographie import indices
    from moteur.epargne import part_rui_salarie
    from moteur.impot_unique import impot
    from moteur.recettes import tva_menages as tm
    from moteur.recettes.impot_salaires import facteur_alignement_public, impot_prive, impot_public
    a = facteur_alignement_public(q)
    fns = {"iu_prive": lambda c, pub: 0.0 if pub else impot(c, q),
           "iu_public": lambda c, pub: impot(c * a, q) if pub else 0.0,
           "tva_sal": lambda c, pub: tm.tva_actif(c * a, q, "prudent", tm.part_rui_agent(c)) if pub
           else tm.tva_actif(c, q, "prudent", part_rui_salarie(c, q))}
    # sans l'IA dans les salaires : le moteur du programme compte l'IA dans son canal macro (part du PIB en plus qui
    # passe au solde) et ses dépenses n'en suivent pas la hausse ; l'ajouter ici la compterait d'un seul côté
    q_sans_ia = q.avec({"macro.ia_productivite": 0.0})
    q_sans_ia.colonne_prudent, q_sans_ia._surcharges = q.colonne_prudent, q._surcharges
    ag = sq.agreger_cellules(q_sans_ia, s_cellules, fns)
    statique = {"iu_prive": impot_prive(q) / 1e9, "iu_public": impot_public(q) / 1e9,
                "tva_sal": (tm.tva_prive(q) + tm.tva_public(q)) / 1e9}
    noyau = {t: {k: statique[k] * ag[t][k] / ag[2029][k] for k in fns} for t in ANNEES}
    g = q.val("macro.tendance", "prudent")

    def moteur(qq):
        d = indices(qq, "prudent")
        return {t: {"iu_prive": statique["iu_prive"] * (1 + g) ** (t - 2029) * d[t]["c_impot"],
                    "iu_public": statique["iu_public"] * (1 + g) ** (t - 2029) * d[t]["c_impot"],
                    "tva_sal": statique["tva_sal"] * (1 + g) ** (t - 2029) * d[t]["c_tva"]} for t in ANNEES}
    sans_nat = q.avec({"demographie.natalite_semi_elasticite": 0.0, "demographie.creches_effet": 0.0})
    sans_nat.colonne_prudent, sans_nat._surcharges = q.colonne_prudent, q._surcharges
    return {"noyau": noyau, "moteur": moteur(q), "moteur_sans_naissances": moteur(sans_nat)}


def mesures_retraites(p: Parametres, q: Parametres, s: str, L, r: dict, bl_sq: dict) -> list:
    """Retraites mesure par mesure contre le statu quo (troisième passe, 4/11/2026).

    Le statu quo paie les pensions de toutes les générations au système actuel (statu_quo.retraites) ; le programme :
    - ferme le régime aux générations nées à partir de 1980 (49 ans ou moins en 2029), qui reçoivent le socle à 67 ans
      et le remboursement de 35 % de leurs cotisations (au sens de Maastricht), plus le surcoût de la pénibilité ;
    - gèle les pensions des générations nées en 1979 ou avant (ancien système), en euros courants ;
    - et les mesures datées de son registre (âge de départ, contribution de solidarité, hautes pensions, attente
      entre l'âge légal et 67 ans, revalorisation du socle, fin du gel…).
    Contrôle (4/11/2026) : l'ancien système du programme sans le gel retrouve les pensions du statu quo des mêmes
    générations (463 contre 465 Md€ en 2037, 28 contre 29 en 2073)."""
    from moteur import statu_quo as sq
    from moteur.ancien_systeme import depenses as depenses_ancien
    from moteur.retraites_transition import cout_socle, cout_transition, remboursements
    from moteur.noyau import Mesure
    ret_sq = sq.retraites(p, s)
    anc, ct = depenses_ancien(q), cout_transition(q)
    socle, remb = cout_socle(q), remboursements(q)
    out = [
        Mesure("Retraites : gel des pensions de l'ancien système (générations nées en 1979 ou avant)", "retraites",
               {t: anc[t] - (ret_sq[t]["depenses"] - ret_sq[t]["depenses_generations_recentes"]) for t in ANNEES}, "budget"),
        Mesure("Retraites : générations nées à partir de 1980, socle et remboursement de 35 % au lieu des pensions actuelles",
               "retraites", {t: socle[t] + remb[t]["maastricht"] + ct[t]["penibilite"] - ret_sq[t]["depenses_generations_recentes"]
                             for t in ANNEES}, "budget"),
        Mesure("Retraites : baisse des hautes pensions", "retraites", {t: -ct[t]["hautes_pensions"] for t in ANNEES}, "budget"),
    ]
    statiques = ("retraites_socle", "transition_retraites")
    lignes_r = [x for x in L.lignes.values() if x["poste"] == "retraites" and x["cle"] not in statiques]
    for x in lignes_r:
        out.append(Mesure(f"Retraites : {x['libelle']}", "retraites", dict(x["valeurs"]), "budget"))
    # contrôle : statu quo + mesures = retraites du moteur du programme
    reste = {t: r[t]["retraites"] - bl_sq[t]["retraites"] - sum(mm.valeurs.get(t, 0.0) for mm in out) for t in ANNEES}
    out.append(Mesure("Retraites : écart non réparti (contrôle, doit être nul)", "retraites", reste, "controle"))
    return out


def invalidite_statu_quo(p: Parametres, bl_sq: dict) -> dict[int, float]:
    """Pensions d'invalidité dans le bloc « AAH et invalidité » du statu quo (le programme les compte en santé)."""
    from moteur.unites import facteur
    inv = p.val("sante.pensions_invalidite_2024") * facteur(p, 2024, "recettes")
    part = inv / (p.val("statu_quo.aah") + inv)
    return {t: bl_sq[t]["aah_invalidite"] * part for t in ANNEES}


def mesures_sante(p: Parametres, q: Parametres, s: str, L, r: dict, bl_sq: dict) -> list:
    """Santé mesure par mesure contre le statu quo (quatrième passe, 4/11/2026).

    Le programme compte en santé l'ONDAM, l'aide sociale à l'autonomie reprise par l'État, les pensions d'invalidité
    et la gestion de l'assurance maladie ; le statu quo met l'invalidité avec l'AAH et la gestion dans son reste
    (« autres »). La santé du programme est donc comparée à la santé + l'invalidité du statu quo (la mesure du revenu
    universel, elle, est comparée aux prestations hors invalidité) ; la gestion est une ligne de classement (le bloc
    « autres » du statu quo, retiré en entier, la contient).
    Contrôle : la somme des lignes retrouve la santé du moteur du programme."""
    from moteur import sante as ms
    from moteur.depenses.statique import autonomie, economie_hopitaux, securite_sociale
    from moteur.noyau import Mesure
    from moteur.unites import facteur
    k = ms.derive_2029(q)
    cr = {t: ms._croissance(q, "prudent", t) for t in ANNEES}
    g = q.val("macro.tendance", "prudent")
    inv = q.val("sante.pensions_invalidite_2024") * facteur(q, 2024, "recettes")
    auto_brut = (q.val("sante.aide_sociale_autonomie_2024") * facteur(q, 2024, "recettes")
                 if q.val("sante.reprise_autonomie_par_etat") else 0.0)
    gestion = securite_sociale(q)[1]
    inv_sq = invalidite_statu_quo(p, bl_sq)
    lig = {x["cle"]: x for x in L.lignes.values() if x["poste"] == "sante"}
    eco_m = q.val("sante.mesures_a_terme", "prudent")
    montee = q.val("sante_trajectoire.montee_mesures")
    options = q.val("sante_trajectoire.options")
    fg = q.val("sante_trajectoire.forfait_generalistes")

    def eco(t):  # économies à terme, avec leur montée en charge ; sante_statique les retire déjà en entier
        n = max(0, t - 2029)
        return (sum(v * min(1, n / montee[x]) for x, v in eco_m.items())
                + sum(o["montant"] * o["comptee"] * min(1, n) for o in options.values()))
    C = {t: k * cr[t] for t in ANNEES}
    out = [
        Mesure("Santé : même périmètre (ONDAM, autonomie, invalidité) sur la pente du programme, contre la santé et "
               "l'invalidité du statu quo", "sante",
               {t: (q.val("sante.ondam_2026") + inv + auto_brut) * C[t] - bl_sq[t]["sante"] - inv_sq[t] for t in ANNEES},
               "methode", note="Écart de méthode : pentes de l'assurance maladie (programme) contre salaires et âge (statu quo)."),
        Mesure("Santé : gestion de l'assurance maladie, comptée en santé (classement ; le statu quo la met dans « autres »)",
               "sante", {t: gestion * C[t] for t in ANNEES}, "classement"),
        Mesure("Santé : coût des agents hospitaliers aligné sur le privé", "sante",
               {t: -economie_hopitaux(q) * C[t] for t in ANNEES}, "budget"),
        Mesure("Santé : aide à l'autonomie, nette des heures déjà payées par le revenu universel", "sante",
               {t: (autonomie(q) - auto_brut) * C[t] for t in ANNEES}, "budget"),
        Mesure("Santé : économies à terme (fraude, arrêts de travail, transports, cures, imagerie…), en montée de charge",
               "sante", {t: -eco(t) * cr[t] for t in ANNEES}, "budget"),
        Mesure("Santé : IA dans les fonctions administratives des hôpitaux", "sante",
               {t: -ms.economie_hopitaux_ia(q, t) for t in ANNEES}, "budget"),
        Mesure("Santé : forfait des généralistes (revalorisé avec la croissance au lieu de la pente)", "sante",
               {t: -fg["revalorise_croissance"] * fg["depense_am_2024"] * k * (cr[t] - (1 + g) ** (t - 2029))
                * (1 - fg["part_perdue"]["prudent"]) for t in ANNEES}, "budget"),
    ]
    for cle, x in lig.items():
        if cle != "sante_trajectoire":
            out.append(Mesure(x['libelle'] if x['libelle'].startswith("Santé") else f"Santé : {x['libelle']}", "sante", dict(x["valeurs"]), "budget"))
    reste = {t: r[t]["sante"] - bl_sq[t]["sante"] - inv_sq[t] - sum(mm.valeurs[t] for mm in out) for t in ANNEES}
    out.append(Mesure("Santé : écart non réparti (contrôle, doit être nul)", "sante", reste, "controle"))
    # l'invalidité du statu quo, comparée ici, sort du bloc « AAH et invalidité » (rendu à la mesure du revenu universel)
    out.append(Mesure("(invalidité du statu quo, comparée à la santé du programme)", "sante", dict(inv_sq), "detail"))
    out.append(Mesure("(invalidité du statu quo : retirée du bloc AAH et invalidité)", "aah_invalidite",
                      {t: -inv_sq[t] for t in ANNEES}, "detail"))
    return out


def alignement_par_groupe(q: Parametres) -> dict[str, float]:
    """Hausse du coût des agents de l'État payés au coût employeur du privé (brut + charges patronales du privé, au
    lieu du titre 2 hors CAS Pensions), par ligne du modèle (Md€ de 2026, 2029) : part conservée × (coût aligné − titre 2
    hors CAS). Sa contrepartie est l'impôt unique des agents (recettes)."""
    from moteur.depenses import budget_etat as be
    t_ = q.val("alignement.charges_patronales_prive")
    ms = be._missions()
    cas_s = sum(float(m["cas_pensions"]) for m in ms if m["cas_source"] == "s")
    t2r = sum(float(m["titre2"]) for m in ms if m["cas_source"] == "r")
    reste = q.val("budget_etat.cas_pensions_2026") - cas_s
    hc = {}
    for m in ms:
        cas = reste * float(m["titre2"]) / t2r if m["cas_pensions"] == "calcul" else float(m["cas_pensions"])
        hc[m["mission"]] = float(m["titre2"]) - cas
    bpe = q.val("alignement.remunerations_activite_etat_2026") / sum(hc.values())
    out: dict[str, float] = {}
    couts = {x["mission"]: x["cout"] for x in be.couts_par_mission(q)}
    for m in be.couts_par_mission(q):
        mm = next(x for x in ms if x["mission"] == m["mission"])
        credits = float(mm["credits"]) if mm["credits"] != "calcul" else None
        aligne = hc[m["mission"]] * bpe * (1 + t_)
        if credits is None:  # défense : crédits de la loi de programmation
            credits = q.val("budget_etat.lpm_2030_courants") / (1 + q.val("budget_etat.inflation_2026_2030"))
        hors_sal = credits - (hc[m["mission"]] if m["mission"] == "Défense" else float(mm["titre2"]))
        part = couts[m["mission"]] / (hors_sal + aligne) if hors_sal + aligne else 0.0
        out[m["ligne"]] = out.get(m["ligne"], 0.0) + part * (aligne - hc[m["mission"]])
    return out


def mesures_autres(p: Parametres, q: Parametres, s: str, L, r: dict, bl_sq: dict) -> list:
    """Autres dépenses (missions de l'État, défense et UE, collectivités, reste) contre les blocs du statu quo
    (quatrième passe, 4/11/2026), au lieu d'un bloc unique.

    - Missions de l'État, ministère par ministère : le coût du programme (alignement des rémunérations, parts
      conservées, évolution selon la règle du ministère) contre les mêmes missions dans le statu quo (hors CAS
      Pensions, hors part d'investissement) ; les missions financées par le fonds ou supprimées (remplacées par le
      revenu universel) retirées ; l'aide sociale à l'enfance, reprise des départements, en classement.
    - Défense (loi de programmation) et contribution à l'UE contre le bloc « défense et UE ».
    - Collectivités : le besoin de financement laissé au budget (la dépense financée par leurs ressources propres est
      au périmètre) contre le bloc du statu quo ; l'investissement local, que le statu quo compte dans son bloc
      investissement et que le programme laisse aux collectivités, en classement.
    - Le reste (sécurité sociale hors santé, quotient familial, mesures datées) contre le reste du statu quo.
    Contrôle : la somme retrouve les autres dépenses et l'investissement du moteur du programme."""
    from moteur import statu_quo as sq
    from moteur.depenses import budget_etat as be
    from moteur.depenses.ministeres import _regle
    from moteur.depenses.statique import depenses as dep_statiques
    from moteur.noyau import Mesure
    e, w, y = sq.effectifs(p, s), sq.salaires(p, s), sq.pib(p, s)
    el = p.val("ministeres.elasticite_eleves_etudiants")
    groupe = {m["mission"]: m["ligne_modele"] for m in be._missions()}
    sq_gr: dict[str, dict[int, float]] = {}
    for x in sq.missions_etat(p):
        g = groupe[x["mission"]]
        d = sq_gr.setdefault(g, {t: 0.0 for t in ANNEES})
        for t in ANNEES:
            d[t] += x["cout"] * sq.indice_mission(x["regle"], x["public"], t, e, w, y, el)
    # le statu quo retire des missions, au prorata, la part de l'État dans l'investissement public (son bloc
    # investissement) ; le programme la laisse dans les ministères : les missions du statu quo sont comparées avec elle
    inv_etat = p.val("statu_quo.investissement_parts")["etat"] * p.val("statu_quo.investissement_part_pib") * sq.pib_2026(p)
    tot = sum(x["cout"] for x in sq.missions_etat(p))
    k_inv = (tot + inv_etat) / tot
    inv_missions = {t: sum(d[t] for d in sq_gr.values()) * (k_inv - 1) for t in ANNEES}
    sq_gr = {g: {t: v * k_inv for t, v in d.items()} for g, d in sq_gr.items()}
    b = be.lignes_modele(q)
    dl = dep_statiques(q)["lignes"]
    b["Autres"] = dl["autres_missions"]  # avec le concours aux outre-mer
    ase = next(m for m in be.couts_par_mission(q) if m["mission"].startswith("Aide sociale à l’enfance"))["cout"]
    lig = [x for x in L.lignes.values() if x["poste"] == "autres" and x["cle"] != "autres_socle"]
    evol = {x["cle"].split(":", 1)[1]: x for x in lig if x["cle"].startswith("ministere:")}
    y0 = sq.pib_2026(p)
    d0 = sq.depart(p)["blocs"]
    defense0 = sq.defense_depart(p) + sq.hausse_defense(p)
    ue0 = d0["defense_ue"] - sq.defense_depart(p)
    al = alignement_par_groupe(q)
    out = [Mesure("Agents de l'État payés au coût employeur du privé (brut + charges du privé ; contrepartie : impôt unique "
                  "des agents)", "etat_missions", {t: 0.0 for t in ANNEES}, "budget")]
    for g in sorted(set(b) | set(sq_gr), key=lambda g: -b.get(g, 0.0)):
        if g in ("Retraites",):
            continue
        prog = {t: b.get(g, 0.0) + (evol[g]["valeurs"][t] if g in evol else 0.0) for t in ANNEES}
        if al.get(g) and b.get(g):  # l'alignement, à part (même évolution que le ministère)
            for t in ANNEES:
                a = al[g] * prog[t] / b[g]
                out[0].valeurs[t] += a
                prog[t] -= a
        if g in ("Armées", "Contribution UE"):
            base_sq = defense0 if g == "Armées" else ue0
            ref = {t: base_sq * y[t] / y0 for t in ANNEES}
            nom = ("Défense : loi de programmation militaire (niveau de 2030, comme le statu quo), coût des militaires aligné" if g == "Armées"
                   else "Contribution à l'Union européenne")
            out.append(Mesure(f"{nom}, contre le statu quo", "defense_ue", {t: prog[t] - ref[t] for t in ANNEES}, "budget"))
            continue
        ref = sq_gr.get(g, {t: 0.0 for t in ANNEES})
        if g == "Fonds":
            out.append(Mesure("Missions financées par le fonds (transports, énergie, France 2030) : retirées du budget",
                              "etat_missions", {t: -ref[t] for t in ANNEES}, "budget"))
            continue
        if g == "Supprimé":
            out.append(Mesure("Missions supprimées (cohésion des territoires, hors aides au logement déjà au revenu universel)",
                              "etat_missions", {t: -ref[t] for t in ANNEES}, "budget"))
            continue
        if g == "Justice":  # l'aide sociale à l'enfance, comptée par le statu quo chez les départements
            k_ase = {t: (prog[t] / b[g]) for t in ANNEES}
            out.append(Mesure("Aide sociale à l'enfance reprise par l'État (classement : le statu quo la compte chez les départements, "
                              "dans le bloc collectivités retiré plus bas)",
                              "etat_missions", {t: ase * k_ase[t] for t in ANNEES}, "classement"))
            prog = {t: prog[t] - ase * k_ase[t] for t in ANNEES}
        out.append(Mesure(f"Ministères — {g} : coût du programme contre le statu quo", "etat_missions",
                          {t: prog[t] - ref[t] for t in ANNEES}, "budget",
                          note=f"2029 : {prog[2029]:.1f} contre {ref[2029]:.1f} Md€"))
    # collectivités
    inv_loc = {t: p.val("statu_quo.investissement_parts")["collectivites"] * bl_sq[t]["investissement"] for t in ANNEES}
    out.append(Mesure("Collectivités : besoin de financement laissé au budget (le reste de leurs dépenses est au périmètre)",
                      "collectivites", {t: dl["collectivites"] for t in ANNEES}, "budget"))
    out.append(Mesure("Remplacé : collectivités (statu quo)", "collectivites", {t: -bl_sq[t]["collectivites"] for t in ANNEES}, "budget"))
    out.append(Mesure("Remplacé : investissement local du statu quo (le programme le laisse dans les dépenses des "
                      "collectivités, au périmètre)", "investissement", {t: -inv_loc[t] for t in ANNEES}, "budget"))
    # investissement du programme contre le reste du bloc du statu quo (État, opérateurs, sécurité sociale)
    for x in L.lignes.values():
        if x["poste"] == "investissement":
            out.append(Mesure(f"Investissement — {x['libelle']}", "investissement", dict(x["valeurs"]), "budget"))
    out.append(Mesure("Investissement des opérateurs, des hôpitaux et de la sécurité sociale : financé par le fonds, hors "
                      "budget (statu quo retiré ; celui de l'État est comparé avec ses ministères)", "investissement",
                      {t: -(bl_sq[t]["investissement"] - inv_loc[t] - inv_missions[t]) for t in ANNEES}, "budget"))
    # reste : sécurité sociale hors santé, quotient familial, économies du budget statique, mesures datées
    statiques = [("securite_sociale_hors_sante", "Sécurité sociale hors santé : gestion des caisses et France Travail conservés"),
                 ("quotient_familial", "Quotient familial et conjugal (crédit d'impôt du programme)"),
                 ("economies_missions", "Économies sur les missions (budget statique)"),
                 ("economies_supplementaires", "Économies supplémentaires (budget statique)")]
    for k, nom in statiques:
        out.append(Mesure(nom, "autres", {t: dl[k] for t in ANNEES}, "budget"))
    for x in lig:
        if not x["cle"].startswith("ministere:"):
            out.append(Mesure(x["libelle"], "autres", dict(x["valeurs"]), "budget"))
    out.append(Mesure("Remplacé : reste du statu quo (gestion de la sécurité sociale, opérateurs, dépenses financées par "
                      "des ventes et tarifs…)", "autres", {t: -bl_sq[t]["autres"] for t in ANNEES}, "budget"))
    reste = {t: r[t]["autres"] + r[t]["investissement"]
             - sum(bl_sq[t][k] for k in ("etat_missions", "defense_ue", "collectivites", "autres", "investissement"))
             - sum(mm.valeurs[t] for mm in out) for t in ANNEES}
    out.append(Mesure("Autres dépenses : écart non réparti (contrôle, doit être nul)", "autres", reste, "controle"))
    return out


def mesures_revenu_universel(p: Parametres, q: Parametres, s: str, L, r: dict, bl_sq: dict) -> list:
    """Revenu universel et AAH mesure par mesure contre le statu quo (troisième passe, 4/11/2026).

    - « RUI et AAH revalorisés comme les prestations du statu quo (salaires) » : le RUI de 2029 et sa démographie
      (adultes, enfants, salariés), hors effet du programme sur les naissances, au salaire moyen de l'année ;
      contre les prestations qu'il remplace (assurance chômage, famille, logement, RSA et prime d'activité, AAH) ;
    - « RUI revalorisé sur les prix plutôt que sur les salaires » (DÉCISION d'Adrien du 04/11/2026 : baisse relative
      assumée) : la différence entre la règle du programme (minimum de l'inflation et de la croissance nominale) et
      les salaires ;
    - effet du programme sur les naissances (moins d'enfants, donc moins de compléments de RUI) ;
    - RUI étudiant sous condition de ressources (ligne du registre)."""
    from moteur import statu_quo as sq
    from moteur.inflation import indice_reel
    from moteur.noyau import Mesure
    from moteur.trajectoire_annuelle import lignes as lignes_traj
    s_cel = "crise" if s == "crise" else "prudent"
    w = sq.salaires(p, s_cel)
    lig = {x["cle"]: x for x in L.lignes.values() if x["poste"] == "rui_aah"}
    reval = {t: (indice_reel(q)[t] - 1) if q.val("revalorisation.rui_aah_socle_croissance") else 0.0 for t in ANNEES}
    sans_nat = q.avec({"demographie.natalite_semi_elasticite": 0.0, "demographie.creches_effet": 0.0})
    sans_nat.colonne_prudent, sans_nat._surcharges = q.colonne_prudent, q._surcharges
    lig0 = {x["cle"]: x for x in lignes_traj(sans_nat, "prudent").lignes.values() if x["poste"] == "rui_aah"}
    base = {t: lig["rui_aah_socle"]["valeurs"][t] + lig0["rui_aah_demographie"]["valeurs"][t] / (1 + reval[t]) for t in ANNEES}
    nat = {t: (lig["rui_aah_demographie"]["valeurs"][t] - lig0["rui_aah_demographie"]["valeurs"][t]) for t in ANNEES}
    blocs = CORRESPONDANCE["rui_aah"]
    inv = invalidite_statu_quo(p, bl_sq)  # comparée à la santé du programme (mesures_sante)
    out = [
        Mesure("Revenu universel et AAH, revalorisés sur les salaires comme les prestations actuelles, contre ces "
               "prestations (chômage, famille, logement, RSA et prime d'activité, AAH ; l'invalidité est comparée à la santé)", "nouveau:rui_aah",
               {t: base[t] * w[t] / w[2029] - sum(bl_sq[t][b] for b in blocs) + inv[t] for t in ANNEES}, "budget"),
        Mesure("Revenu universel revalorisé sur les prix plutôt que sur les salaires (baisse relative assumée)",
               "nouveau:rui_aah", {t: base[t] * ((1 + reval[t]) - w[t] / w[2029]) for t in ANNEES}, "budget"),
        Mesure("Effet du programme sur les naissances : compléments de revenu universel des enfants", "nouveau:rui_aah",
               nat, "budget"),
        Mesure("Revenu universel : " + lig["rui_etudiants"]["libelle"], "nouveau:rui_aah", dict(lig["rui_etudiants"]["valeurs"]), "budget"),
    ]
    for b in blocs:  # les prestations remplacées sont déjà retirées dans la première mesure (invalidité : en santé)
        v = {t: bl_sq[t][b] - (inv[t] if b == "aah_invalidite" else 0.0) for t in ANNEES}
        out.append(Mesure(f"(prestation remplacée, comptée dans la mesure du revenu universel) : {b}", b,
                          {t: -v[t] for t in ANNEES}, "detail"))
        out.append(Mesure(f"(contrepartie) : {b}", "nouveau:rui_aah", v, "detail"))
    reste = {t: r[t]["rui_aah"] - sum(bl_sq[t][b] for b in blocs) + inv[t] - sum(mm.valeurs.get(t, 0.0) for mm in out if mm.nature == "budget")
             for t in ANNEES}
    out.append(Mesure("Revenu universel : écart non réparti (contrôle, doit être nul)", "nouveau:rui_aah", reste, "controle"))
    return out


CANAUX_EMPLOI = {"population_active": "Venus de l'inactivité (seniors, cumul, inactifs, jeunes)",
                 "fonds": "Emplois du fonds", "conjoncture": "Conjoncture (ajustement budgétaire)"}
# chômeurs repris par les réformes, mesure par mesure (moteur/emploi_canaux.emplois_par_mesure)
REFORMES_EMPLOI = {
    "allocation_chomage_rui": "Allocation chômage remplacée par le RUI", "france_travail_conseil": "France Travail recentré sur le conseil",
    "selection_universite_apprentissage": "Sélection à l'université et apprentissage", "droit_a_construire": "Droit à construire",
    "accompagnement_ia": "Accompagnement par l'IA", "alternance": "Alternance", "contrat_assoupli": "Contrat de travail assoupli",
    "bas_salaires": "RUI au prorata des bas salaires", "entreprises_cout_travail": "Réforme des entreprises : coût du travail",
    "entreprises_localisation": "Réforme des entreprises : localisation (IS à 45 %)", "baisse_cout_travail": "Baisse du coût du travail jusqu'à 1,3 SMIC",
    "commerces": "Horaires des commerces", "smic_croissance": "SMIC revalorisé sur la croissance", "prime_jeunes": "Prime d'embauche des jeunes",
    "accords_branche": "Accords d'entreprise",
}


def contexte_emploi(p: Parametres, s: str, r: dict) -> dict:
    """Emplois par canal, lus dans le module macro du programme ; emploi = statu quo + somme des canaux.

    Le moteur du programme a sa propre base d'actifs, calée autrement que le statu quo (environ 850 000 personnes en
    emploi de plus, constant) : prendre ses actifs − chômeurs mélangerait cet écart de calage avec les effets du
    programme. Non compté : l'effet du programme sur les naissances (actifs en moins après 2048)."""
    from moteur import statu_quo as sq
    from moteur.emploi_canaux import emplois_par_mesure
    e = sq.effectifs(p, s)
    epm = emplois_par_mesure(p)
    # parts de chaque réforme dans les chômeurs repris (le prudent mêle les jeux crise et médian)
    jeux = {"crise": ("crise",), "prudent": ("crise", "median"), "median": ("median",), "optimiste": ("optimiste",)}[s]
    brut = {k: sum(epm[j][k] for j in jeux) / len(jeux) for k in REFORMES_EMPLOI}
    tot = sum(brut.values()) or 1.0
    emploi, canaux = {}, {}
    for t in ANNEES:
        d = r[t].get("chomage_detail") or {}
        if not d:
            return {}
        c = {lib: d["reformes"] * brut[k] / tot for k, lib in REFORMES_EMPLOI.items()}
        c.update({lib: d[k] for k, lib in CANAUX_EMPLOI.items()})
        emploi[t] = e[t]["emploi"] + sum(c.values())
        canaux[t] = c
    return {"emploi": emploi, "emplois_canaux": canaux}


def energie_entreprises(p: Parametres, q: Parametres, s: str, ctx: dict) -> dict:
    """Canal de l'énergie des entreprises (remarque d'Adrien du 06/11/2026) : moins de taxes sur l'énergie, plus de
    marges, plus d'impôt sur les bénéfices, plus d'emplois — et l'inverse quand le prix du carbone dépasse les taxes
    actuelles.

    1. Impôt sur les bénéfices : les nouvelles accises des entreprises sont déjà nettes de l'IS (recettes, ligne 15),
       mais les taxes actuelles supprimées ne sont pas réintégrées dans l'assiette de l'IS (contrairement aux impôts
       de production) : + taux moyen de l'IS × taxes actuelles supprimées.
    2. Emploi industriel : − élasticité × écart de l'indice de prix de l'énergie des entreprises, ajustement
       progressif ; un emploi gagné rapporte comme un emploi du coût du travail (au SMIC), un emploi perdu coûte
       comme un emploi perdu par localisation (coût moyen du privé), comme dans le bloc emploi ; les emplois passent
       par le chômage (même règle que le coût du travail) et ajoutent leur valeur ajoutée au PIB."""
    import math
    from moteur import statu_quo as sq
    from moteur.carbone import couts_energie_entreprises
    from moteur.emploi_canaux import gains_par_canal
    from moteur.is_bareme import taux_moyen
    from moteur.ecologie import emissions as em
    jeu = em.scenario(q, s)
    ce = couts_energie_entreprises(q, s)
    t_is = taux_moyen(q, s)
    gains = gains_par_canal(q, s)
    eps = sq._v(q, "energie_entreprises.elasticite_emploi_prix", jeu)
    n_ind = q.val("energie_entreprises.emploi_industrie")
    ajust = q.val("ecologie.reponse_prix")["ajustement"]
    e = sq.effectifs(p, s)
    is_sup, emplois, budget = {}, {}, {}
    ln_a = 0.0
    for t in ANNEES:
        if t not in ce:
            is_sup[t] = emplois[t] = budget[t] = 0.0
            continue
        is_sup[t] = t_is * ce[t]["statu_quo"]
        ln_a += ajust * (-eps * math.log(ce[t]["indice_prix"]) - ln_a)
        emplois[t] = n_ind * (math.exp(ln_a) - 1)
        g = gains["cout_travail"] if emplois[t] >= 0 else gains["localisation"]
        budget[t] = emplois[t] * g / 1e9
    mesures = [
        Mesure("Effet macro : impôt sur les bénéfices des taxes sur l'énergie supprimées (marges des entreprises)", "recettes",
               is_sup, nature="effet_macro"),
        Mesure("Effet macro : emploi industriel selon le prix de l'énergie des entreprises", "recettes", budget, nature="effet_macro"),
    ]
    va = {t: ctx["pib"][t] / e[t]["emploi"] for t in ANNEES}
    actifs = {t: e[t]["emploi"] + e[t]["chomeurs"] for t in ANNEES}
    nouveau = dict(ctx)
    nouveau["chomage"] = {t: ctx["chomage"][t] - emplois[t] / actifs[t] * 100 for t in ANNEES}
    if "emploi" in ctx:
        nouveau["emploi"] = {t: ctx["emploi"][t] + emplois[t] for t in ANNEES}
        nouveau["emplois_canaux"] = {t: {**ctx["emplois_canaux"][t], "Prix de l'énergie des entreprises": emplois[t]} for t in ANNEES}
    nouveau["pib"] = {t: ctx["pib"][t] + emplois[t] * va[t] for t in ANNEES}
    return {"mesures": mesures, "contexte": nouveau, "couts": ce, "emplois": emplois}


def mesure_prix_carbone(p: Parametres, q: Parametres, s: str) -> Mesure:
    """Effet physique du prix du carbone (300 € en 2030, puis valeur de l'action pour le climat) sur les émissions
    des transports et des bâtiments, contre le prix du statu quo : la même réponse que l'assiette de la recette
    carbone (moteur/carbone.py), sans montant (la recette est déjà dans les instruments et l'effet macro carbone)."""
    from moteur.carbone import reponse_energie
    from moteur.ecologie import emissions as em
    rep = reponse_energie(q, s)
    e = em.territoriales(p, s)
    phys = {f"emissions_mt:{i}": {t: e[t][i] * (rep[i][t] - 1) for t in em.ANNEES} for i in rep}
    return Mesure("Fiscalité de l'énergie (prix du carbone à la place des taxes actuelles) : transports et bâtiments",
                  "recettes", {}, "physique", physique=phys, vert="favorable")


def mesure_carbone_importe(p: Parametres, q: Parametres, s: str) -> Mesure:
    """Effet physique de l'accise sur le contenu carbone des importations : la même réponse que sa recette
    (moteur/carbone._importe) — le prix moyen des biens manufacturés monte de x / passage_prix_vente, la demande
    baisse avec l'élasticité — appliquée aux émissions importées liées à ces biens. La substitution vers des biens
    français ou européens n'est pas comptée (prudent)."""
    from moteur.carbone import prix
    from moteur.ecologie import emissions as em
    b = em.bilan(p, s)
    c = {k: q.val(f"carbone_importe.{k}") for k in ("intensite_kg_par_euro", "part_importee", "part_hors_ue",
                                                   "abattement_preuve", "elasticite_prix", "passage_prix_vente",
                                                   "part_empreinte_couverte")}
    serie = {}
    for t in em.ANNEES:
        if t < 2029:
            serie[t] = 0.0
            continue
        x = prix(q, t) / 1000 * c["intensite_kg_par_euro"] * c["part_importee"] * c["part_hors_ue"] * (1 - c["abattement_preuve"])
        facteur = (1 + x / c["passage_prix_vente"]) ** (-c["elasticite_prix"])
        serie[t] = b[t]["importees"] * c["part_empreinte_couverte"] * (facteur - 1)
    return Mesure("Accise sur le contenu carbone des importations", "recettes", {}, "physique",
                  physique={"importees_mt": serie}, vert="favorable")


def mesures_physiques_fonds(p: Parametres, q: Parametres, s: str) -> list[Mesure]:
    """Effets physiques des investissements du fonds (groupe ecologie_fonds), sans montant : leur financement est
    déjà dans le fonds et ses rendements."""
    from moteur.ecologie import emissions as em
    out = []
    for nom, par in q._p.items():
        if not nom.startswith("ecologie_fonds."):
            continue
        x = par.valeur
        out.append(Mesure(f"{x['id']} — {x['libelle']} (émissions)", "recettes", {}, "physique",
                          physique={f"emissions_mt:{x['secteur']}": em.profil(p, s, x)}, vert="favorable"))
    return out


class EcologieDeDroite:
    nom = "ecologie_de_droite"
    libelle = "Écologie de droite"

    def __init__(self, recalcul_noyau: bool = True):
        """recalcul_noyau : impôt unique et TVA des salariés recalculés sur le noyau (deuxième passe) ; False : tout
        est lu dans le moteur du programme (reproduction exacte, sert de test du pont)."""
        self._cache = {}
        self.recalcul_noyau = recalcul_noyau

    def _calcul(self, p: Parametres) -> dict:
        cle = id(p)
        if cle in self._cache:
            return self._cache[cle]
        from moteur import statu_quo as sq
        from moteur.calendrier import dette_fin_2028
        from moteur.inflation import serie
        from moteur.retraites_transition import cout_transition
        from moteur.simulation import simuler
        res = simuler(p)
        pc = p.en_crise()
        jeux = {"crise": (pc, "prudent"), "prudent": (p, "prudent"), "median": (p, "median"), "optimiste": (p, "optimiste")}
        mesures, contexte = {}, {}
        for s, (q, jeu) in jeux.items():
            r = res[s]
            rec_sq, bl_sq = sq.recettes(p, s), sq.blocs(p, s)
            m = []
            # budget hors effets macro : recettes, puis chaque poste contre les blocs qu'il remplace
            # recettes : chaque instrument du programme contre les impôts actuels qu'il remplace
            from moteur.trajectoire_annuelle import lignes as lignes_traj
            ri = recettes_par_instrument(q)
            imp_sq = sq.recettes_par_impot(p, s)
            # deuxième passe : impôt unique et TVA des salariés recalculés sur les cellules du noyau ; l'effet du
            # programme sur les naissances, que le moteur du programme mettait dans chaque ligne, devient une mesure
            rn = recalcul_noyau_salaries(p, q, "crise" if s == "crise" else "prudent")
            if not self.recalcul_noyau:  # pont exact : le noyau prend les valeurs du moteur
                rn["noyau"] = rn["moteur_sans_naissances"]
            for t in ANNEES:
                for k in ("iu_prive", "iu_public"):
                    ri[t][k] += rn["noyau"][t][k] - rn["moteur"][t][k]
                ri[t]["tva"] += rn["noyau"][t]["tva_sal"] - rn["moteur"][t]["tva_sal"]
            m.append(Mesure("Effet du programme sur les naissances : impôt unique et TVA des salariés", "recettes",
                            {t: sum(rn["moteur"][t][k] - rn["moteur_sans_naissances"][t][k] for k in rn["moteur"][t])
                             for t in ANNEES}, "budget"))
            for cle, libelle, remplace in INSTRUMENTS:
                m.append(Mesure(libelle, "recettes", {t: ri[t].get(cle, 0.0) - sum(imp_sq[t][i] for i in remplace)
                                                       for t in ANNEES}, "budget"))
            L = lignes_traj(q, "prudent")
            statiques = ("recettes_nouveau_systeme", "recettes_croissance", "recettes_demographie")
            autres_rec = [x for x in L.lignes.values() if x["poste"] == "recettes" and x["cle"] not in statiques]
            for x in autres_rec:
                m.append(Mesure(x["libelle"], "recettes", dict(x["valeurs"]), "budget"))
            # contrôle : tout ce qui reste entre les recettes du programme et la somme des instruments et des mesures
            # contrôle : les recettes du moteur du programme = instruments (valeurs du moteur) + mesures datées
            remplace_ = {t: sum(rn["noyau"][t][k] - rn["moteur"][t][k] for k in rn["noyau"][t]) for t in ANNEES}
            ecart_noyau = {t: sum(rn["noyau"][t][k] - rn["moteur_sans_naissances"][t][k] for k in rn["noyau"][t]) for t in ANNEES}
            somme = {t: sum(ri[t].values()) - remplace_[t] + sum(x["valeurs"].get(t, 0.0) for x in autres_rec) for t in ANNEES}
            m.append(Mesure("Recettes : écart non réparti (contrôle, doit être nul)", "recettes",
                            {t: r[t]["recettes"] - r[t]["effet_macro"] - somme[t] for t in ANNEES}, "controle"))
            m.append(Mesure("Recalcul sur le noyau : impôt unique et TVA des salariés (contrôle)",
                            "recettes", {t: 0.0 for t in ANNEES}, "controle",
                            note=f"écart au moteur du programme hors naissances, 2073 : {ecart_noyau[2073]:+.1f} Md€"))
            m.append(Mesure("Fin des dotations versées aux collectivités (solde)", "recettes",
                            {t: -r[t]["transferts_collectivites"] for t in ANNEES}, "budget"))
            # dépenses : chaque ligne du registre du programme dans un bloc nouveau de son poste, et les blocs du statu
            # quo que ce poste remplace retirés
            for poste, blocs in CORRESPONDANCE.items():
                if poste == "retraites":
                    m.extend(mesures_retraites(p, q, s, L, r, bl_sq))
                    continue
                if poste == "rui_aah":
                    m.extend(mesures_revenu_universel(p, q, s, L, r, bl_sq))
                    continue
                if poste == "sante":
                    m.extend(mesures_sante(p, q, s, L, r, bl_sq))
                    continue
                if poste == "autres":
                    m.extend(mesures_autres(p, q, s, L, r, bl_sq))
                    continue
                if poste == "investissement":  # avec les autres dépenses (investissement local)
                    continue
                lignes_p = [x for x in L.lignes.values() if x["poste"] == poste]
                for x in lignes_p:
                    m.append(Mesure(f"{LIBELLES[poste]} — {x['libelle']}", f"nouveau:{poste}", dict(x["valeurs"]), "budget"))
                reste = {t: r[t][poste] - sum(x["valeurs"].get(t, 0.0) for x in lignes_p) for t in ANNEES}
                if any(abs(v) > 1e-9 for v in reste.values()):
                    m.append(Mesure(f"{LIBELLES[poste]} — écart non réparti (contrôle, doit être nul)", f"nouveau:{poste}", reste, "controle"))
                for b in blocs:
                    m.append(Mesure(f"Remplacé par « {LIBELLES[poste]} » : {b} (statu quo)", b, {t: -bl_sq[t][b] for t in ANNEES}, "budget"))
            # périmètre : les collectivités, hors du budget du programme, y sont remises (dépenses et ressources propres,
            # même montant ; le besoin de financement est déjà au budget), comme dans le statu quo (toutes les
            # administrations). Évolution : salaires × population, comme le bloc « autres » du statu quo.
            col = collectivites_hors_budget(p)
            idx = {t: bl_sq[t]["autres"] / bl_sq[2029]["autres"] for t in ANNEES}
            m.append(Mesure("Périmètre : ressources propres des collectivités (impôt local unique, IS local, autres)", "recettes",
                            {t: col["ressources"] * idx[t] for t in ANNEES}, "perimetre"))
            m.append(Mesure("Périmètre : dépenses des collectivités financées par ces ressources", "autres",
                            {t: col["ressources"] * idx[t] for t in ANNEES}, "perimetre"))
            # périmètre : ventes et tarifs de l'État, des opérateurs et des hôpitaux. Le statu quo les compte en brut
            # (recettes non fiscales et dépenses) ; le programme chiffre ses dépenses nettes (missions, ONDAM) : ils sont
            # remis des deux côtés, au PIB comme dans le statu quo.
            y_sq = sq.pib(p, s)
            ventes = {t: p.val("statu_quo.recettes_production_hors_apul_part_pib") * y_sq[t] for t in ANNEES}
            m.append(Mesure("Périmètre : ventes et tarifs de l'État, des opérateurs et des hôpitaux", "recettes", ventes, "perimetre"))
            m.append(Mesure("Périmètre : dépenses financées par ces ventes et tarifs", "autres", dict(ventes), "perimetre"))
            # effets macroéconomiques, canal par canal (le reste : épargne rendue et socle supplémentaire de la règle)
            canaux = sorted({k for t in ANNEES for k in r[t]["canaux"]})
            for k in canaux:
                m.append(Mesure(f"Effet macro : {k}", "recettes", {t: r[t]["canaux"].get(k, 0.0) for t in ANNEES}, "effet_macro"))
            m.append(Mesure("Effet macro : épargne rendue et socle supplémentaire (règle)", "recettes",
                            {t: r[t]["effet_macro"] - sum(r[t]["canaux"].values()) for t in ANNEES}, "effet_macro"))
            m.append(Mesure("Participations de l'État remises au fonds", "participations",
                            {t: v["participations"] for t, v in cout_transition(q).items()}, "mesure"))
            m.append(mesure_prix_carbone(p, q, s))
            m.append(mesure_carbone_importe(p, q, s))
            m.extend(mesures_physiques_fonds(p, q, s))
            mesures[s] = m
            # contexte : ce que le programme change dans l'économie
            infl = serie(q, jeu)
            spread = q.val("macro.baisse_spread", jeu)
            n_sp = q.val("macro.annees_baisse_spread")
            pib = {t: r[t]["pib"] for t in ANNEES}
            contexte[s] = {
                "pib": pib,
                "inflation": {t: infl[t] for t in ANNEES},
                "taux_supplementaire": {t: -spread * min(1.0, max(0, t - 2029) / n_sp) for t in ANNEES},
                "chomage": {t: r[t]["chomage"] for t in ANNEES},
                "dette_depart": dette_fin_2028(q),
                **contexte_emploi(p, s, r),
                "pib_hors_consommation": {t: r[t].get("pib_epargne_fonds", 0.0) for t in ANNEES},
            }
            en = energie_entreprises(p, q, s, contexte[s])
            contexte[s] = en["contexte"]
            mesures[s].extend(en["mesures"])
        out = {"mesures": mesures, "contexte": contexte, "resultats": res}
        self._cache = {cle: out}
        return out

    def mesures(self, p: Parametres) -> dict[str, list[Mesure]]:
        return self._calcul(p)["mesures"]

    def contexte(self, p: Parametres) -> dict[str, dict]:
        return self._calcul(p)["contexte"]

    def resultats_moteur(self, p: Parametres) -> dict:
        """Résultats du moteur propre au programme (moteur/simulation.simuler), pour la reproduction."""
        return self._calcul(p)["resultats"]


def programme(recalcul_noyau: bool = True) -> EcologieDeDroite:
    return EcologieDeDroite(recalcul_noyau)


def ecart_de_depart(p: Parametres | None = None, s: str = "prudent", annee: int = 2029, detail: bool = False) -> dict[str, float]:
    """Écart du budget du programme avec le statu quo, hors effets macro (Md€ ; + = améliore le solde), au périmètre
    de toutes les administrations : par grand poste, ou mesure par mesure (detail=True). Mêle les mesures et les
    différences de méthode qui resteraient."""
    from moteur import statu_quo as sq
    p = p or Parametres()
    out: dict[str, float] = {}
    for m in programme().mesures(p)[s]:
        if m.nature not in ("budget", "perimetre", "controle"):
            continue
        signe = 1 if m.poste == "recettes" else -1
        if detail:
            cle = m.nom
        elif m.poste == "recettes":
            cle = "Recettes"
        else:
            cle = next((LIBELLES[k] for k, b in CORRESPONDANCE.items() if m.poste in b or m.poste == f"nouveau:{k}"), m.nom)
            if cle in (LIBELLES["investissement"], LIBELLES["autres"]):
                cle = "Investissement et autres dépenses (ministères, collectivités, mesures)"
        out[cle] = out.get(cle, 0.0) + signe * m.valeurs.get(annee, 0.0)
    out["Total (points de PIB)"] = sum(out.values()) / sq.pib(p, s)[annee] * 100
    return out
