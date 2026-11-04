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
            m.append(Mesure("Recettes du programme (hors effets macro) contre recettes actuelles", "recettes",
                            {t: r[t]["recettes"] - r[t]["effet_macro"] - rec_sq[t] for t in ANNEES}, "budget"))
            m.append(Mesure("Fin des dotations versées aux collectivités (solde)", "recettes",
                            {t: -r[t]["transferts_collectivites"] for t in ANNEES}, "budget"))
            for poste, blocs in CORRESPONDANCE.items():
                if len(blocs) == 1:
                    m.append(Mesure(LIBELLES[poste], blocs[0], {t: r[t][poste] - bl_sq[t][blocs[0]] for t in ANNEES}, "budget"))
                else:
                    m.append(Mesure(LIBELLES[poste], f"nouveau:{poste}", {t: r[t][poste] for t in ANNEES}, "budget"))
                    for b in blocs:
                        m.append(Mesure(f"Remplacé par « {LIBELLES[poste]} » : {b}", b, {t: -bl_sq[t][b] for t in ANNEES}, "budget"))
            # périmètre : les collectivités, hors du budget du programme, y sont remises (dépenses et ressources propres,
            # même montant ; le besoin de financement est déjà au budget), comme dans le statu quo (toutes les
            # administrations). Évolution : salaires × population, comme le bloc « autres » du statu quo.
            col = collectivites_hors_budget(p)
            idx = {t: bl_sq[t]["autres"] / bl_sq[2029]["autres"] for t in ANNEES}
            m.append(Mesure("Périmètre : ressources propres des collectivités (impôt local unique, IS local, autres)", "recettes",
                            {t: col["ressources"] * idx[t] for t in ANNEES}, "perimetre"))
            m.append(Mesure("Périmètre : dépenses des collectivités financées par ces ressources", "autres",
                            {t: col["ressources"] * idx[t] for t in ANNEES}, "perimetre"))
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


def ecart_de_depart(p: Parametres | None = None, s: str = "prudent", annee: int = 2029) -> dict[str, float]:
    """Écart du budget du programme avec le statu quo, poste par poste (Md€ ; + = améliore le solde), hors effets
    macro, au périmètre de toutes les administrations (collectivités remises au budget du programme). Mêle les
    mesures et les différences de méthode."""
    from moteur import statu_quo as sq
    p = p or Parametres()
    prog = programme()
    out = {}
    for m in prog.mesures(p)[s]:
        if m.nature not in ("budget", "perimetre"):
            continue
        cle = m.nom.split(" : ")[0] if m.nom.startswith("Remplacé") else m.nom
        signe = 1 if m.poste == "recettes" else -1
        cle = next((LIBELLES[k] for k, b in CORRESPONDANCE.items() if m.poste in b or m.poste == f"nouveau:{k}"),
                   "Recettes du programme (hors effets macro) contre recettes actuelles" if m.poste == "recettes" and m.nature == "perimetre" else cle)
        out[cle] = out.get(cle, 0.0) + signe * m.valeurs[annee]
    # investissement et autres dépenses regroupés : le programme compte l'investissement de l'État et des
    # collectivités dans ses missions et dans les dépenses locales, le statu quo dans un bloc à part
    inv, aut = LIBELLES["investissement"], LIBELLES["autres"]
    out["Investissement et autres dépenses (ministères, collectivités, mesures)"] = out.pop(inv, 0.0) + out.pop(aut, 0.0)
    out["Total (points de PIB)"] = sum(out.values()) / sq.pib(p, s)[annee] * 100
    return out
