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
from .retraites_transition import cout_transition, cout_socle, _csv as _csv_retraites

ANNEES = list(range(2029, 2074))


def postes(p: Parametres, scenario_retenu: str = "prudent") -> dict[int, dict]:
    g = p.val("macro.tendance", "prudent")
    infl = p.val("calendrier.inflation")
    rec = recettes_nouveau_systeme(p)["total"] / 1e9
    dep = depenses(p)
    l = dep["lignes"]
    ct = cout_transition(p)
    socle = cout_socle(p)
    ia = ia_administration.economie_nette(p)
    anc = {int(x["annee"]): x for x in _csv_retraites("ancien_systeme_retraites.csv")}
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
    L = Lignes()
    for t in ANNEES:
        n = t - 2029
        crois = (1 + g) ** n
        reval_rui = (((1 + g) / (1 + infl)) ** n * (1 + prod[t]) - 1) if p.val("revalorisation.rui_aah_socle_croissance") else 0.0
        ancien_86 = anc[t]["depenses_desindexees_md"] * anc[t]["part_ancien_systeme"]
        pensions_min = (p.val("revalorisation.part_pensions_sous_seuil") * ancien_86 * ((1 + g) ** (t - 2028) - 1)
                        if p.val("revalorisation.pensions_sous_minimum_vieillesse") else 0.0)
        # Recettes (montants positifs)
        L.ajouter(t, "recettes", "recettes_nouveau_systeme", "Recettes du nouveau système (budget statique)", "socle", rec)
        L.ajouter(t, "recettes", "recettes_croissance", "Recettes : croissance tendancielle", "croissance", rec * (crois - 1))
        L.ajouter(t, "recettes", "successions", "Successions : supplément", "mesure", succ[t])
        L.ajouter(t, "recettes", "tva_2028", "TVA de 2028 maintenue", "mesure", tva2028[t])
        L.ajouter(t, "recettes", "tva_2028_rendue", "TVA de 2028 rendue par le barème", "mesure", -rendu[t])
        L.ajouter(t, "recettes", "ascenseur_recettes", "Ascenseur social : recettes", "mesure", asc_r[t])
        L.ajouter(t, "recettes", "anciennes_pensions", "Anciennes pensions : prélèvement net", "mesure", anc_p[t])
        L.ajouter(t, "recettes", "is_investissement", "IS : déduction de l'investissement", "mesure", -is_inv[t])
        # Dépenses (montants positifs = dépense)
        L.ajouter(t, "sante", "sante_trajectoire", "Santé : trajectoire des dépenses", "trajectoire", sante[t])
        L.ajouter(t, "sante", "sante_garde_fou", "Santé : garde-fou", "mesure", -gf[t])
        L.ajouter(t, "retraites", "retraites_socle", "Retraites : socle (budget statique)", "socle", l["retraites_socle"])
        L.ajouter(t, "retraites", "transition_retraites", "Transition des retraites : coût net", "trajectoire", ct[t]["net"])
        L.ajouter(t, "retraites", "pensions_sous_minimum", "Pensions sous le minimum vieillesse : revalorisation", "mesure", pensions_min)
        L.ajouter(t, "retraites", "socle_revalorisation", "Socle : revalorisation sur la croissance", "croissance", socle[t] * reval_rui)
        L.ajouter(t, "retraites", "fin_gel", "Fin du gel des anciennes pensions", "mesure", gel[t])
        L.ajouter(t, "rui_aah", "rui_aah_socle", "RUI et AAH (budget statique)", "socle", l["rui_aah"])
        L.ajouter(t, "rui_aah", "rui_aah_revalorisation", "RUI et AAH : revalorisation sur la croissance", "croissance", l["rui_aah"] * reval_rui)
        L.ajouter(t, "rui_aah", "rui_etudiants", "RUI étudiant sous condition de ressources", "mesure", etu[t])
        L.ajouter(t, "investissement", "subventions_restees", "Subventions d'investissement restées à l'État", "socle", l["subventions_restees"] - soutien_2026)
        L.ajouter(t, "investissement", "renouvelables", "Soutien aux renouvelables (contrats en cours)", "trajectoire", soutien_2029 * max(0, (fin - t) / (fin - 2029)))
        L.ajouter(t, "autres", "autres_socle", "Autres dépenses (budget statique)", "socle", autres_base)
        L.ajouter(t, "autres", "autres_croissance", "Autres dépenses : croissance tendancielle", "croissance", autres_base * (crois - 1))
        L.ajouter(t, "autres", "ia_administration", "IA dans l'administration : économie", "mesure", -ia[t] * crois)
        L.ajouter(t, "autres", "reformes_emploi", "Réformes de l'emploi : coût", "mesure", (em["g24"] - em["b155"] * (t > em["b154"])) * crois)
        L.ajouter(t, "autres", "ascenseur_depenses", "Ascenseur social : dépenses", "mesure", asc_d[t])
        for nom, v in eco_detail.items():
            L.ajouter(t, "autres", "economie:" + nom[:60], nom, "mesure", -v[t])
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
