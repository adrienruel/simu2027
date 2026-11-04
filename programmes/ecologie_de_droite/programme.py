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


class EcologieDeDroite:
    nom = "ecologie_de_droite"

    def __init__(self):
        self._cache = {}

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
            for cle, libelle, remplace in INSTRUMENTS:
                m.append(Mesure(libelle, "recettes", {t: ri[t].get(cle, 0.0) - sum(imp_sq[t][i] for i in remplace)
                                                       for t in ANNEES}, "budget"))
            L = lignes_traj(q, "prudent")
            statiques = ("recettes_nouveau_systeme", "recettes_croissance", "recettes_demographie")
            autres_rec = [x for x in L.lignes.values() if x["poste"] == "recettes" and x["cle"] not in statiques]
            for x in autres_rec:
                m.append(Mesure(x["libelle"], "recettes", dict(x["valeurs"]), "budget"))
            # contrôle : tout ce qui reste entre les recettes du programme et la somme des instruments et des mesures
            somme = {t: sum(ri[t].values()) + sum(x["valeurs"].get(t, 0.0) for x in autres_rec) for t in ANNEES}
            m.append(Mesure("Recettes : écart non réparti (contrôle, doit être nul)", "recettes",
                            {t: r[t]["recettes"] - r[t]["effet_macro"] - somme[t] for t in ANNEES}, "controle"))
            m.append(Mesure("Fin des dotations versées aux collectivités (solde)", "recettes",
                            {t: -r[t]["transferts_collectivites"] for t in ANNEES}, "budget"))
            # dépenses : chaque ligne du registre du programme dans un bloc nouveau de son poste, et les blocs du statu
            # quo que ce poste remplace retirés
            for poste, blocs in CORRESPONDANCE.items():
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
            mesures[s] = m
            # contexte : ce que le programme change dans l'économie
            infl = serie(q, jeu)
            spread = q.val("macro.baisse_spread", jeu)
            n_sp = q.val("macro.annees_baisse_spread")
            pib = {t: r[t]["pib"] for t in ANNEES}
            ref = {t: r[t]["pib"] - r[t]["effet_pib"] for t in ANNEES}
            contexte[s] = {
                "pib": pib,
                # module macro : ratio de la prime de dette sur le PIB de référence + effets de l'année précédente
                "pib_prime": {t: ref[t] + (r[t - 1]["effet_pib"] if t > 2029 else 0.0) for t in ANNEES},
                "inflation": {t: infl[t] for t in ANNEES},
                "taux_supplementaire": {t: -spread * min(1.0, max(0, t - 2029) / n_sp) for t in ANNEES},
                "chomage": {t: r[t]["chomage"] for t in ANNEES},
                "dette_depart": dette_fin_2028(q),
            }
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


def programme() -> EcologieDeDroite:
    return EcologieDeDroite()


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
