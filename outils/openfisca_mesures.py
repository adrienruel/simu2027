"""Phase F2 : mesures des programmes dans OpenFisca-France, calculées sur la population synthétique.

Lit programmes/micro_mesures.yaml (opérations par mesure), construit une réforme d'OpenFisca par mesure et par
programme (toutes ses mesures codées ensemble), calcule la population de 2026 avant et après, et écrit :
- sorties/micro_mesures.csv : effet budgétaire statique de chaque mesure (OpenFisca) à côté du chiffrage du moteur ;
- sorties/micro_deciles.csv : variation du niveau de vie par décile, par programme (phase F3).

Effet budgétaire statique = variation du coût du travail payé par les employeurs − variation du revenu disponible des
ménages (après recours au RSA, à la prime d'activité et à l'ASF, mêmes tirages avant et après). Positif : le solde
public s'améliore. Statique : sans changement de comportement (le moteur compte, lui, les effets d'offre et
d'assiette, d'où une partie des écarts).

    python -m outils.openfisca_mesures             # toutes les mesures et tous les programmes (≈ 20 min)
    python -m outils.openfisca_mesures lisnard     # un programme
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import math

import numpy as np
import yaml

from moteur.parametres import Parametres
from outils import openfisca_population as op


def ps_smic() -> float:
    from outils.population_synthetique import smic_mensuel_brut
    return smic_mensuel_brut()

RACINE = Path(__file__).resolve().parent.parent
SPECS = RACINE / "programmes" / "micro_mesures.yaml"
DEBUT = "2020-01-01"


def specs() -> dict:
    return yaml.safe_load(SPECS.read_text(encoding="utf-8"))


# --- Réformes ------------------------------------------------------------------------------------------------

def _noeud(params, chemin: str):
    n = params
    for morceau in chemin.split("."):
        m = re.fullmatch(r"(\w+)\[(\d+)\]", morceau)
        n = getattr(n, m.group(1))[int(m.group(2))] if m else getattr(n, morceau)
    return n


def _appel(f, e, period, parameters):
    """Appelle une formule d'OpenFisca, qu'elle prenne les paramètres ou non."""
    return f(e, period, parameters) if f.__code__.co_argcount >= 3 else f(e, period)


def _formules(nom: str, x: dict):
    """Variables nouvelles ou réécrites : (nom de la variable, fabrique(tbs) → classe Variable)."""
    from openfisca_core.model_api import MONTH, YEAR, Variable, where
    from openfisca_france.entities import Famille, FoyerFiscal

    if nom == "af_premier_enfant":
        part = x["part_bmaf"]

        def fab(tbs):
            orig = tbs.variables["af"].get_formula("2026-01")

            class af(Variable):
                value_type = float
                entity = Famille
                definition_period = MONTH
                label = "Allocations familiales, dès le premier enfant (réforme)"

                def formula(famille, period, parameters):
                    base = _appel(orig, famille, period, parameters)
                    bmaf = parameters(period).prestations_sociales.prestations_familiales.bmaf.bmaf
                    mod = famille("af_taux_modulation", period)
                    return base + (famille("af_nbenf", period) == 1) * bmaf * part * mod
            return af
        return "af", fab

    if nom == "ir_jeunes":
        age_max, k = x["age_max"], x["plafond_smic"]

        def fab(tbs):
            orig = tbs.variables["impot_revenu_restant_a_payer"].get_formula("2026")

            class impot_revenu_restant_a_payer(Variable):
                value_type = float
                entity = FoyerFiscal
                definition_period = YEAR
                label = "Impôt sur le revenu, nul pour les jeunes (réforme)"

                def formula(foyer, period, parameters):
                    ir = _appel(orig, foyer, period, parameters)
                    smic = parameters(period.first_month).marche_travail.salaire_minimum.smic.smic_b_horaire * 151.67 * 12
                    age = foyer.declarant_principal("age", period.first_month)
                    jeune = (age <= age_max) & (foyer("rbg", period) <= k * smic)
                    return where(jeune, 0.0, ir)
            return impot_revenu_restant_a_payer
        return "impot_revenu_restant_a_payer", fab

    if nom == "ir_naissance":
        amax, plafond = x["age_enfant_max"], x["plafond"]

        def fab(tbs):
            orig = tbs.variables["impot_revenu_restant_a_payer"].get_formula("2026")

            class impot_revenu_restant_a_payer(Variable):
                value_type = float
                entity = FoyerFiscal
                definition_period = YEAR
                label = "Impôt sur le revenu, allégé après une naissance (réforme)"

                def formula(foyer, period, parameters):
                    ir = _appel(orig, foyer, period, parameters)  # négatif : impôt à payer
                    age = foyer.members("age", period.first_month)
                    pac = foyer.members.has_role(FoyerFiscal.PERSONNE_A_CHARGE)
                    bebe = foyer.any((age <= amax) & pac)
                    return where(bebe, np.minimum(0.0, ir + plafond), ir)
            return impot_revenu_restant_a_payer
        return "impot_revenu_restant_a_payer", fab

    if nom == "variable_facteur":
        var, k = x["nom"], x["facteur"]

        def fab(tbs):
            v0 = tbs.variables[var]
            orig = v0.get_formula("2026-01" if v0.definition_period == "month" else "2026")
            attrs = {"value_type": v0.value_type, "entity": v0.entity, "definition_period": v0.definition_period,
                     "label": f"{v0.label} (× {k}, réforme)", "formula": lambda e, period, parameters: _appel(orig, e, period, parameters) * k}
            if getattr(v0, "set_input", None):
                attrs["set_input"] = v0.set_input
            return type(var, (Variable,), attrs)
        return var, fab

    raise ValueError(f"Formule inconnue : {nom}")


def construire(operations: list[dict]):
    """Système OpenFisca réformé (operations : liste d'opérations du fichier micro_mesures.yaml)."""
    from openfisca_core.model_api import Reform
    from openfisca_core.parameters import ParameterScaleBracket
    tbs = op.systeme()
    params_ops = [o for o in operations if "parametre" in o or "tranche" in o]
    var_ops = []
    for o in operations:
        if "variable" in o:
            var_ops.append(_formules("variable_facteur", o["variable"]))
        elif "formule" in o and o["formule"]["nom"] not in POST:
            var_ops.append(_formules(o["formule"]["nom"], o["formule"]))

    def modifier(params):
        for o in params_ops:
            if "parametre" in o:
                x = o["parametre"]
                n = _noeud(params, x["chemin"])
                v0 = n("2026-01-01")
                v = x["valeur"] if "valeur" in x else v0 * x["facteur"] if "facteur" in x else v0 + x["ajout"]
                n.update(start=DEBUT, value=v)
            else:
                x = o["tranche"]
                b = _noeud(params, x["bareme"])
                b.brackets.append(ParameterScaleBracket(f"tranche_{x['seuil']}", data={
                    "threshold": {DEBUT: {"value": float(x["seuil"])}}, "rate": {DEBUT: {"value": float(x["taux"])}}}))
        return params

    class R(Reform):
        def apply(self):
            if params_ops:
                self.modify_parameters(modifier_function=modifier)
            for nom, fab in var_ops:
                # une même variable modifiée deux fois : la seconde enveloppe la première (self.variables est à jour)
                self.update_variable(fab(self))
    return R(tbs) if (params_ops or var_ops) else None


# --- Calcul --------------------------------------------------------------------------------------------------

POST = ("garantie_niveau_vie", "plafond_aides", "revenu_incitation", "condition_nationalite", "rsa_duree",
        "allocation_unique", "capitalisation")  # règles appliquées après le calcul d'OpenFisca
EMPLOI = ("salarie_prive", "agent_public", "independant")
AIDES = ("rsa", "ppa", "aide_logement", "af", "cf", "asf", "ars", "paje_base")


def _post(operations):
    return [o["formule"] for o in operations if "formule" in o and o["formule"]["nom"] in POST]


def emplois_par_scenario(pp, rel, t, bande, eta: dict, valeur) -> dict:
    """Emplois en plus et effet sur le solde (Md€), par scénario, de variations relatives du gain à travailler rel
    (personnes en emploi t, poids pp, tranche de salaire bande, élasticités eta[scénario][tranche], valeur publique
    d'un emploi). Chantier 2.1 (21/11/2026) : le scénario miroir est choisi sur le sens NET de la mesure, pas personne
    par personne. Avant, les gagnants prenaient l'élasticité du scénario et les perdants celle du miroir : une mesure
    qui fait des gagnants et des perdants (prime d'activité, qui change aussi le contrefactuel du conjoint) perdait
    des emplois au prudent dans les deux sens (+10 % et −10 % : −4 800 et −5 200)."""
    from moteur.offre import MIROIR
    w = pp * rel * t
    par = {}
    for sc in eta:
        net = float((w * eta[sc][bande]).sum())
        el = eta[sc][bande] if net >= 0 else eta[MIROIR[sc]][bande]
        d = w * el
        par[sc] = {"emplois": float(d.sum()), "budget": float((d * valeur).sum()) / 1e9}
    return par


class Base:
    """Population et simulations du système actuel (avec les deux contrefactuels « sans travail »), tirages de
    recours fixés.

    Contrefactuels : les revenus d'activité des personnes de référence en emploi (puis ceux des autres adultes en
    emploi) sont mis à zéro, le reste du ménage inchangé. Le gain à travailler d'une personne est la différence de
    revenu disponible de son ménage entre la situation réelle et son contrefactuel ; sa valeur pour les finances
    publiques, la différence de coût du travail moins ce gain."""

    def __init__(self, lignes=None, emploi: bool = True):
        self.lignes = lignes or op.lire()
        self.sim, self.s = op.simulation(self.lignes)
        self.rec = Parametres().val("microsimulation.recours")
        s = self.s
        n_f = s["n_familles"]
        self.u = {k: np.random.default_rng(i + 11).random(n_f) for i, k in enumerate(("rsa", "ppa", "asf", "aspa"))}
        self.pp = np.array([l["poids"] for l in self.lignes])
        self.public = np.array([l["statut"] == "agent_public" for l in self.lignes])
        self.wf = np.zeros(n_f)
        self.wf[s["famille"]] = self.pp
        self.wm = np.zeros(s["n_menages"])
        self.wm[s["menage"]] = self.pp
        self.pers_m = np.bincount(s["menage"], minlength=s["n_menages"])
        self.fam_men = np.zeros(n_f, int)
        self.fam_men[s["famille"]] = s["menage"]
        etud = np.zeros(s["n_menages"], bool)
        for j, l in enumerate(self.lignes):
            if l["role"] == "ref" and l["statut"] == "etudiant":
                etud[s["menage"][j]] = True
        self.menage_etudiant = etud
        # constantes de recours calées sur le système actuel
        self.c = {}
        for k, part in (("rsa", self.rec["rsa"]), ("ppa", self.rec["prime_activite"])):
            x = self.sim.calculate_add(k, "2026")
            pr = op.proba_recours(x, self.wf, part, self.rec["forme"])
            r = np.where(x > 0, np.maximum(x, 1e-9) ** self.rec["forme"], 0.0)
            m = (pr > 0) & (pr < 1)
            self.c[k] = float(np.median(pr[m] / r[m])) if m.any() else 1.0
        # Aspa : recours calé sur le nombre d'allocataires de la DREES (personnes de 65 ans ou plus des familles)
        aspa = self.sim.calculate_add("aspa", "2026")
        n65 = np.bincount(s["famille"], weights=np.array([l["age"] >= 65 for l in self.lignes], float), minlength=n_f)
        cible = Parametres().val("microsimulation.recours_aspa")["allocataires"]
        poids_a = self.wf * np.maximum(n65, 1)
        part = min(1.0, cible / float((poids_a * (aspa > 0)).sum()))
        pr = op.proba_recours(aspa, poids_a, part, self.rec["forme"])
        r = np.where(aspa > 0, np.maximum(aspa, 1e-9) ** self.rec["forme"], 0.0)
        m = (pr > 0) & (pr < 1)
        self.c["aspa"] = float(np.median(pr[m] / r[m])) if m.any() else 1.0
        asf = self.sim.calculate_add("asf", "2026")
        self.c["asf"] = Parametres().val("microsimulation.allocation_soutien_familial") * 1e6 / float((self.wf * (asf > 0)).sum())
        # travailleurs : en emploi, de 18 à 64 ans, avec un revenu d'activité
        self.travaille = np.array([l["statut"] in EMPLOI and 18 <= l["age"] <= 64
                                   and l["salaire_brut"] + max(l["revenu_independant"], 0) > 0 for l in self.lignes])
        self.est_ref = np.array([l["role"] == "ref" for l in self.lignes])
        smic_an = ps_smic() * 12
        self.bande = np.array([0 if l["salaire_brut"] + max(l["revenu_independant"], 0) <= 1.3 * smic_an else
                               (1 if l["salaire_brut"] + max(l["revenu_independant"], 0) <= 2.5 * smic_an else 2)
                               for l in self.lignes])
        exc = np.zeros(n_f, bool)
        couple = np.zeros(n_f, bool)
        enf = np.zeros(n_f, bool)
        for j, l in enumerate(self.lignes):
            fa, r = s["famille"][j], s["role_famille"][j]
            couple[fa] |= r == "conjoint"
            enf[fa] |= r == "enfant"
            if r in ("demandeur", "conjoint") and (l["handicap"] or l["age"] >= 60):
                exc[fa] = True
        self.exceptions_rsa = exc | (~couple & enf)
        self.fam_enf = enf
        self.nationalite()
        # bornes de niveau de vie du système actuel (personnes) : 3e décile et médiane, pour les barèmes dégressifs
        rd0 = self.sim.calculate("revenu_disponible", "2026")
        nv0 = rd0 / np.maximum(self.sim.calculate("unites_consommation", "2026"), 1e-9)
        w0 = self.wm * self.pers_m
        o = np.argsort(nv0)
        cw = np.cumsum(w0[o]) / w0.sum()
        self.bornes_nv = {"d3": float(nv0[o][np.searchsorted(cw, 0.3)]), "mediane": float(nv0[o][np.searchsorted(cw, 0.5)])}
        self.etat0 = self.etat(self.sim, [])
        self.emploi = emploi
        if emploi:
            self.cf0 = self.contrefactuels(None, [])

    def nationalite(self):
        """Ménages étrangers (microsimulation.nationalite) : probabilité logistique croissante quand le niveau de vie
        baisse, calée sur le nombre d'étrangers et sur leur part des prestations des Caf ; ressortissants de l'UE et
        arrivés depuis moins de cinq ans tirés au hasard parmi eux."""
        s, an = self.s, "2026"
        x = Parametres().val("microsimulation.nationalite")
        rd = self.sim.calculate("revenu_disponible", an)
        uc = self.sim.calculate("unites_consommation", an)
        nv = rd / np.maximum(uc, 1e-9)
        z = -(np.log(np.maximum(nv, 1000)) - np.log(np.median(nv)))
        caf = sum(self.sim.calculate_add(k, an) for k in AIDES)
        caf_m = np.bincount(self.fam_men, weights=caf, minlength=s["n_menages"])
        pers = self.wm * self.pers_m
        rng = np.random.default_rng(2076)
        u = rng.random(s["n_menages"])
        cible = x["etrangers"] * 1e6
        meilleur = None
        for b in np.linspace(0, 4, 41):
            lo, hi = -15.0, 5.0
            for _ in range(50):
                a = (lo + hi) / 2
                pr = 1 / (1 + np.exp(-(a + b * z)))
                lo, hi = (a, hi) if (pers * pr).sum() < cible else (lo, a)
            etr = u < pr
            part = (self.wm * caf_m * etr).sum() / (self.wm * caf_m).sum()
            if meilleur is None or abs(part - x["part_paiements_cnaf"]) < abs(meilleur[0] - x["part_paiements_cnaf"]):
                meilleur = (part, etr, b)
        self.part_caf_etrangers, etr, self.b_nationalite = meilleur
        v = rng.random(s["n_menages"])
        ue = etr & (v < x["part_ue"])
        hors_ue = etr & ~ue
        recents = hors_ue & (rng.random(s["n_menages"]) < x["part_recents_hors_ue"])
        self.groupes = {"hors_ue": hors_ue[self.fam_men], "hors_ue_recents": recents[self.fam_men],
                        "etrangers": etr[self.fam_men]}  # par famille

    # -- un état : revenu disponible des ménages après recours et règles ajoutées
    def etat(self, sim, post: list[dict], foyers: dict | None = None) -> dict:
        s, an = self.s, "2026"
        sf = foyers or s  # foyers fiscaux de la simulation (l'individualisation de l'impôt les change)
        rd = sim.calculate("revenu_disponible", an)
        montants = {k: sim.calculate_add(k, an) for k in AIDES}
        montants["aspa"] = sim.calculate_add("aspa", an)
        pris = {}
        for k in ("rsa", "ppa", "asf", "aspa"):
            x = montants[k]
            pris[k] = (self.u[k] < self.c[k]) if k == "asf" else \
                (self.u[k] < np.minimum(1, self.c[k] * np.maximum(x, 1e-9) ** self.rec["forme"]))
        percu = {k: montants[k] * pris.get(k, True) for k in (*AIDES, "aspa")}
        ajust_f = sum(percu[k] - montants[k] for k in ("rsa", "ppa", "asf", "aspa"))
        uc = sim.calculate("unites_consommation", an)
        for x in post:
            if x["nom"] == "revenu_incitation":
                # RSA et prime d'activité remplacés : base pour les éligibles à l'un des deux, majoration avec activité
                act = sim.calculate_add("salaire_net", an) + np.maximum(sim.calculate("rpns_imposables", an), 0)
                act_f = np.bincount(s["famille"], weights=act, minlength=s["n_familles"])
                # lecture retenue : les familles éligibles au RSA reçoivent le revenu d'incitation à la place du RSA et
                # de la prime d'activité ; les autres gardent la prime d'activité (lecture littérale « RSA ou prime » :
                # − 14 Md€, à l'opposé de l'économie annoncée)
                elig = montants["rsa"] > 0
                ria = elig * 12 * (x["base"] + x["avec_activite"] * (act_f > 0))
                pris_ria = elig & pris["rsa"]
                ajust_f = ajust_f - percu["rsa"] - percu["ppa"] * elig + ria * pris_ria
                percu["rsa"], percu["ppa"] = ria * pris_ria, percu["ppa"] * ~elig
            if x["nom"] == "plafond_aides":
                tot = sum(percu[k] for k in AIDES)
                cap = x["plafond_mensuel"] * 12
                if x.get("sans_activite_seulement"):
                    act = sim.calculate_add("salaire_net", an) + np.maximum(sim.calculate("rpns_imposables", an), 0)
                    sans = np.bincount(s["famille"], weights=act, minlength=s["n_familles"]) <= 0
                else:
                    sans = np.ones(s["n_familles"], bool)
                ajust_f = ajust_f - sans * np.maximum(0.0, tot - cap)
            if x["nom"] == "condition_nationalite":
                # prestations retirées aux familles du groupe (hors UE, ou hors UE arrivées depuis moins de cinq ans)
                g = self.groupes[x["groupe"]]
                for k in x["prestations"]:
                    ajust_f = ajust_f - g * percu[k]
                    percu[k] = percu[k] * ~g
            if x["nom"] == "rsa_duree":
                # RSA limité dans le temps : une part des familles au RSA le perd (ancienneté tirée au hasard), sauf
                # handicap, parent isolé et 60 ans ou plus
                if not hasattr(self, "_u_duree"):
                    self._u_duree = np.random.default_rng(45).random(s["n_familles"])
                exc = self.exceptions_rsa
                perd = (self._u_duree < x["part"]) & ~exc
                ajust_f = ajust_f - perd * percu["rsa"]
                percu["rsa"] = percu["rsa"] * ~perd
            if x["nom"] == "allocation_unique":
                # allocation par famille avec enfants, pleine jusqu'au 3e décile de niveau de vie (avant l'allocation),
                # nulle à la médiane, à la place des prestations familiales qu'elle remplace
                nv_m = (rd + np.bincount(self.fam_men, weights=ajust_f, minlength=s["n_menages"])) / np.maximum(uc, 1e-9)
                d3, med = self.bornes_nv["d3"], self.bornes_nv["mediane"]
                taux = np.clip((med - nv_m) / (med - d3), 0.0, 1.0)[self.fam_men]
                ancien = sum(percu[k] for k in x["remplace"])
                nouveau = self.fam_enf * taux * x["mensuel"] * 12
                if x.get("sans_perdant"):
                    nouveau = np.maximum(nouveau, ancien)  # chaque famille garde au moins ce qu'elle avait
                for k in x["remplace"]:
                    percu[k] = 0 * percu[k]
                ajust_f = ajust_f - ancien + nouveau
        rd = rd + np.bincount(self.fam_men, weights=ajust_f, minlength=s["n_menages"])
        fonds = 0.0
        for x in post:
            if x["nom"] == "capitalisation":
                # part salariale d'une capitalisation obligatoire (bibliotheque.capitalisation_obligatoire, mêmes
                # paramètres) : versée à un fonds hors des administrations, elle baisse le revenu disponible sans être
                # une recette publique (retirée du budget de la mesure)
                verse = self.capitalisation(sim, x)
                rd = rd - np.bincount(s["menage"], weights=verse, minlength=s["n_menages"])
                fonds += float((self.pp * verse).sum()) / 1e9
        for x in post:
            if x["nom"] == "garantie_niveau_vie":
                # niveau de vie porté au seuil, ménages dont la personne de référence n'est pas étudiante (champ de
                # l'Insee ; les jeunes ont leur propre mesure)
                champ = self.menage_etudiant if x.get("champ") == "etudiants" else ~self.menage_etudiant
                rd = rd + champ * np.maximum(0.0, x["seuil_mensuel"] * 12 * uc - rd)
        cout_i = sim.calculate_add("cout_du_travail", an)
        comp = {k: float((self.wf * percu[k]).sum()) / 1e9 for k in ("rsa", "ppa", "asf", "aide_logement", "af", "aspa")}
        comp["aah"] = float((self.pp * sim.calculate_add("aah", an)).sum()) / 1e9
        foy = np.zeros(sf["n_foyers"])
        foy[sf["foyer"]] = self.pp
        comp["impot_revenu"] = -float((foy * sim.calculate("impot_revenu_restant_a_payer", an)).sum()) / 1e9
        comp["csg"] = -float((self.pp * sim.calculate("csg", an)).sum()) / 1e9
        cout_m = np.bincount(s["menage"], weights=cout_i, minlength=s["n_menages"])
        # coût des agents publics : payé par les administrations (une hausse est une dépense, pas une recette)
        cout_pub = float((self.pp * cout_i * self.public).sum()) / 1e9
        return {"rd": rd, "uc": uc, "cout_m": cout_m, "cout": float((self.wm * cout_m).sum()) / 1e9, "cout_public": cout_pub,
                "rd_total": float((self.wm * rd).sum()) / 1e9, "comp": comp, "fonds": fonds}

    def capitalisation(self, sim, x: dict) -> np.ndarray:
        """Part salariale versée au fonds par personne (€ par an) : les salariés et agents publics les plus jeunes en
        emploi, à hauteur des entrants couverts depuis le début (entrants_par_an × taux_emploi × années), comme le
        moteur ; taux × brut, plafonné, × (1 − part employeur). Paramètres : x["parametre"], lu dans le programme
        x["programme"] (ou les paramètres communs)."""
        c = Parametres(programme=x["programme"]).val(x["parametre"]) if x.get("programme") else Parametres().val(x["parametre"])
        annee = getattr(self, "annee", 2026)
        n = c["entrants_par_an"] * c["taux_emploi"] * max(0, annee - c["debut"] + 1)
        an = "2026"
        travaille = sim.calculate_add("salaire_net", an) > 0
        brut = np.array([l["salaire_brut"] if l["statut"] in ("salarie_prive", "agent_public") else 0.0 for l in self.lignes])
        sal = travaille & (brut > 0)
        age = np.array([l["age"] for l in self.lignes], float)
        part = np.zeros(len(self.lignes))
        if n > 0 and sal.any():
            idx = np.where(sal)[0]
            o = idx[np.argsort(age[idx], kind="stable")]
            cum = np.cumsum(self.pp[o])
            avant = cum - self.pp[o]
            part[o] = np.clip((n - avant) / np.maximum(self.pp[o], 1e-9), 0.0, 1.0)
        cot = np.minimum(c["taux"] * brut, 12 * c["plafond_mensuel"])
        return part * (1 - c["part_employeur"]) * cot

    def _simuler(self, tbs, lignes=None):
        return op.simulation(lignes or self.lignes, tbs=tbs)[0]

    def contrefactuels(self, tbs, post, lignes=None) -> dict:
        """Revenu disponible et coût du travail des ménages quand les personnes de référence (puis les autres
        adultes) en emploi ne travaillent pas."""
        out = {}
        for nom, choix in (("ref", self.travaille & self.est_ref), ("autres", self.travaille & ~self.est_ref)):
            base_l = lignes or self.lignes
            lg = [dict(l, salaire_brut=0.0, cout_employeur=0.0, revenu_independant=0.0, statut="inactif") if c else l
                  for l, c in zip(base_l, choix)]
            sim = self._simuler(tbs, lg)
            e = self.etat(sim, post, op.structure(lg) if lignes is not None else None)
            out[nom] = {"rd": e["rd"], "cout_m": e["cout_m"]}
            del sim
            import gc
            gc.collect()
        return out

    def participation(self, e, cf, s: str = "prudent") -> dict:
        """Gain à travailler et valeur publique de chaque travailleur, dans un état et ses contrefactuels."""
        m = self.s["menage"]
        g = np.zeros(len(self.lignes))
        v = np.zeros(len(self.lignes))
        for nom, choix in (("ref", self.travaille & self.est_ref), ("autres", self.travaille & ~self.est_ref)):
            g[choix] = (e["rd"] - cf[nom]["rd"])[m[choix]]
            v[choix] = (e["cout_m"] - cf[nom]["cout_m"])[m[choix]] - g[choix]
        return {"gain": g, "valeur": v}

    def emploi_effet(self, e1, cf1, s: str = "prudent", releves=None) -> dict:
        """Emplois en plus (personnes) et effet sur le solde (Md€) de la variation du gain à travailler : élasticité
        de participation de la tranche de salaire (offre.travail_participation) × facteur propre aux transferts
        (offre.participation_transferts), appliquée aux personnes en emploi (Immervoll et al., 2007). Rend le
        scénario s et le détail des quatre scénarios (emplois_par_scenario : miroir sur le sens net de la mesure).
        releves : personnes dont le salaire est relevé par un nouveau SMIC ; leur gain à travailler en plus ne crée
        pas d'emploi (au SMIC, l'emploi est fixé par la demande, compté par le canal du coût horaire)."""
        from moteur.statu_quo import SCENARIOS
        p = Parametres()
        eta = {sc: np.array(p.val("offre.travail_participation", sc)) * p.val("offre.participation_transferts", sc)
               for sc in SCENARIOS}
        a = self.participation(self.etat0, self.cf0)
        b = self.participation(e1, cf1)
        t = self.travaille & (a["gain"] > 0)
        rel = np.zeros(len(self.lignes))
        rel[t] = np.clip((b["gain"][t] - a["gain"][t]) / np.maximum(a["gain"][t], 1.0), -1, 1)
        if releves is not None:
            rel[releves & (rel > 0)] = 0.0
        par = emplois_par_scenario(self.pp, rel, t, self.bande, eta, b["valeur"])
        return {**par[s], "scenarios": par}

    def population(self, operations: list[dict]) -> list[dict] | None:
        """Population modifiée par les opérations « population » (None s'il n'y en a pas) :
        - individualiser : impôt sur le revenu individuel (couples mariés ou pacsés déclarant séparément, enfants à
          charge de la personne de référence) ;
        - smic_net_2027 ou smic_brut_2026, diffusion : salaire mensuel relevé au nouveau SMIC, hausse décroissante
          jusqu'à zéro à diffusion × le nouveau SMIC (même règle que bibliotheque.smic, privé et public)."""
        pops = [o["population"] for o in operations if "population" in o]
        if not pops:
            return None
        lg = [dict(l) for l in self.lignes]
        for x in pops:
            if x.get("individualiser"):
                for l in lg:
                    l["maries"] = 0
            if "smic_net_2027" in x or "smic_brut_2026" in x:
                from moteur import bibliotheque as bib
                if "smic_brut_2026" in x:
                    cible = float(x["smic_brut_2026"])
                else:
                    infl27 = Parametres().val("inflation.base")["2027"]
                    cible = bib.brut_de_net_mensuel(x["smic_net_2027"] / (1 + infl27))
                smic0 = 1823.03  # SMIC brut mensuel de 2026 (même valeur que bibliotheque.smic)
                plafond = x["diffusion"] * cible
                for l in lg:
                    if l["statut"] not in ("salarie_prive", "agent_public") or l["salaire_brut"] <= 0:
                        continue
                    mois = max(1, int(l.get("mois_travailles", 12) or 12))
                    b = l["salaire_brut"] / mois
                    if b <= smic0:
                        b2 = b * cible / smic0  # temps partiel au SMIC horaire
                    elif b < plafond:
                        b2 = max(b + (cible - smic0) * max(0.0, 1 - (b - smic0) / (plafond - smic0)), min(cible, plafond))
                    else:
                        continue
                    l["salaire_brut"] = b2 * mois
            if "pensions" in x:
                y = x["pensions"]
                annee = getattr(self, "annee", 2026)
                if y.get("indexation_salaires"):
                    # pensions revalorisées comme le salaire moyen depuis 2029 (ou leur liquidation, ancienneté moyenne
                    # de 12 ans) au lieu des prix : gain relatif w(t) / w(max(2029, t - 12)), même calcul que le moteur
                    from moteur import statu_quo as sq
                    w = sq.salaires(Parametres(), "prudent")
                    fac = w[annee] / w[max(2029, annee - 12)] if annee > 2029 else 1.0
                    for l in lg:
                        l["pension_brute"] *= fac
                    continue
                # pensions au-delà d'un seuil mensuel brut multipliées par un facteur (gel, sous-indexation), perte qui
                # s'éteint avec les retraités concernés après la dernière année (≈ 18 ans, comme le moteur)
                fin = y.get("fin", 2032)
                k = 1 - (1 - y["facteur"]) * (math.exp(-(annee - fin) / 18) if annee > fin else 1.0)
                seuil = 12 * y.get("seuil_mensuel", 0.0)
                for l in lg:
                    if l["pension_brute"] > seuil:
                        l["pension_brute"] *= k
        return lg

    def reforme(self, operations: list[dict]) -> dict:
        tbs = construire(operations)
        post = _post(operations)
        lg = self.population(operations)
        foyers = None
        if lg is not None:
            sim = self._simuler(tbs, lg)
            foyers = op.structure(lg)
        else:
            sim = self.sim if tbs is None else self._simuler(tbs)
        e1 = self.etat(sim, post, foyers)
        if sim is not self.sim:
            del sim
            import gc
            gc.collect()
        e0 = self.etat0
        out = {"budget": (e1["cout"] - e0["cout"]) - (e1["cout_public"] - e0["cout_public"])
                         - (e1["rd_total"] - e0["rd_total"]) - (e1["fonds"] - e0["fonds"]), "etat": e1,
               "composantes": {k: e1["comp"][k] - e0["comp"][k] for k in e0["comp"]}}
        if self.emploi:
            cf1 = self.cf0 if (tbs is None and not post and lg is None) else self.contrefactuels(tbs, post, lg)
            releves = None
            if lg is not None and any("smic_net_2027" in o.get("population", {}) or "smic_brut_2026" in o.get("population", {})
                                      for o in operations):
                releves = np.array([l2["salaire_brut"] > l1["salaire_brut"] + 1.0 for l1, l2 in zip(self.lignes, lg)])
            out["emploi"] = self.emploi_effet(e1, cf1, releves=releves)
        return out

    def deciles(self, e1: dict) -> list[dict]:
        """Variation du niveau de vie par décile de niveau de vie initial (personnes pondérées)."""
        e0 = self.etat0
        nv0 = e0["rd"] / np.maximum(e0["uc"], 1e-9)
        nv1 = e1["rd"] / np.maximum(e1["uc"], 1e-9)
        w = self.wm * self.pers_m
        o = np.argsort(nv0)
        cum = np.cumsum(w[o]) / w.sum()
        dec = np.empty(len(o), int)
        dec[o] = np.minimum((cum * 10).astype(int), 9)
        out = []
        for d in range(10):
            m = dec == d
            out.append({"decile": d + 1, "niveau_vie_avant": float((w * nv0)[m].sum() / w[m].sum()),
                        "variation_eur_an": float((w * (nv1 - nv0))[m].sum() / w[m].sum()),
                        "variation_pct": float((w * (nv1 - nv0))[m].sum() / (w * nv0)[m].sum() * 100),
                        "gagnants_pct": float(w[m & (nv1 - nv0 > 10)].sum() / w[m].sum() * 100),
                        "perdants_pct": float(w[m & (nv1 - nv0 < -10)].sum() / w[m].sum() * 100)})
        return out


def montant_moteur(nom: str, ident: str, s: str = "prudent") -> float:
    """Effet sur le solde (Md€ de 2026, + = l'améliore) des mesures de cet identifiant dans le moteur, à plein effet."""
    p = Parametres(programme=nom)
    tot = 0.0
    for cle, par in p._p.items():
        if not cle.startswith(f"{nom}_mesures."):
            continue
        x = par.valeur
        if not isinstance(x, dict) or x.get("id") != ident:
            continue
        m = x["montant"][s] if isinstance(x["montant"], dict) else x["montant"]
        tot += m if x["poste"] == "recettes" else -m
    return tot


def main(programmes=None):
    """Calcule les programmes demandés (tous sinon) et écrit un fichier par programme dans sorties/micro/, puis
    réunit tous les fichiers présents dans sorties/micro_mesures.csv et micro_deciles.csv. Lancer un programme
    par processus limite la mémoire (chaque simulation garde ses calculs)."""
    sp = specs()
    dossier = RACINE / "sorties" / "micro"
    dossier.mkdir(exist_ok=True)
    base = None
    for nom, mesures in sp.items():
        if programmes and nom not in programmes:
            continue
        base = base or Base()
        lignes_m, lignes_d, lignes_e = [], [], []
        toutes = []
        for ident, spec in mesures.items():
            r = base.reforme(spec["operations"])
            toutes += spec["operations"]
            mot = montant_moteur(nom, ident)
            lignes_m.append({"programme": nom, "mesure": ident, "openfisca_md": round(r["budget"], 2),
                             "moteur_md": round(mot, 2),
                             "ecart_pct": round((r["budget"] / mot - 1) * 100) if abs(mot) > 0.05 else "",
                             "emplois_milliers": round(r["emploi"]["emplois"] / 1e3, 1) if "emploi" in r else "",
                             "budget_emploi_md": round(r["emploi"]["budget"], 2) if "emploi" in r else "",
                             **{f"d_{k}": round(v, 2) for k, v in r["composantes"].items()},
                             "note": spec.get("note", "")})
            for sc, x in r["emploi"]["scenarios"].items():
                lignes_e.append({"programme": nom, "mesure": ident, "scenario": sc, "emplois": round(x["emplois"]),
                                 "budget_md": round(x["budget"], 3), "statique_md": round(r["budget"], 3)})
            em = r.get("emploi", {"emplois": 0.0, "budget": 0.0})
            print(f"{nom:10s} {ident:11s} OpenFisca {r['budget']:+6.2f}  moteur {mot:+6.2f}  emplois {em['emplois'] / 1e3:+7.1f} k"
                  f"  ({em['budget']:+5.2f} Md€)", flush=True)
        r = base.reforme(toutes)
        em = r.get("emploi", {"emplois": 0.0, "budget": 0.0})
        for d in base.deciles(r["etat"]):
            lignes_d.append({"programme": nom, "budget_ensemble_md": round(r["budget"], 2),
                             "emplois_ensemble_milliers": round(em["emplois"] / 1e3, 1),
                             "budget_emploi_ensemble_md": round(em["budget"], 2),
                             **{k: round(v, 2) if isinstance(v, float) else v for k, v in d.items()}})
        print(f"{nom:10s} ensemble OpenFisca {r['budget']:+6.2f}", flush=True)
        for suffixe, lignes in (("mesures", lignes_m), ("deciles", lignes_d), ("emploi", lignes_e)):
            _ecrire(dossier / f"{nom}_{suffixe}.csv", lignes)
    reunir()


def _ecrire(chemin, lignes):
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    from outils import trace
    trace.enregistrer(chemin)


def reunir():
    dossier = RACINE / "sorties" / "micro"
    for suffixe in ("mesures", "deciles", "emploi"):
        lignes = []
        for nom in specs():
            f = dossier / f"{nom}_{suffixe}.csv"
            if f.exists():
                with f.open(encoding="utf-8") as g:
                    lignes += list(csv.DictReader(g))
        if lignes:
            # emplois par mesure et par scénario : lus par le moteur (moteur/offre.py, phase F4)
            cible = (RACINE / "parametres" / "donnees" / "micro_emploi_2026.csv") if suffixe == "emploi" else \
                (RACINE / "sorties" / f"micro_{suffixe}.csv")
            _ecrire(cible, lignes)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
