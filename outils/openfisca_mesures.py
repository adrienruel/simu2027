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

import numpy as np
import yaml

from moteur.parametres import Parametres
from outils import openfisca_population as op

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
        elif "formule" in o and o["formule"]["nom"] != "garantie_niveau_vie":
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

class Base:
    """Population et simulation du système actuel, tirages de recours fixés."""

    def __init__(self, lignes=None):
        self.lignes = lignes or op.lire()
        self.sim, self.s = op.simulation(self.lignes)
        self.rec = Parametres().val("microsimulation.recours")
        n_f = self.s["n_familles"]
        self.u = {k: np.random.default_rng(i + 11).random(n_f) for i, k in enumerate(("rsa", "ppa", "asf"))}
        pp = np.array([l["poids"] for l in self.lignes])
        self.wf = np.zeros(n_f)
        self.wf[self.s["famille"]] = pp
        self.wm = np.zeros(self.s["n_menages"])
        self.wm[self.s["menage"]] = pp
        self.pers_m = np.bincount(self.s["menage"], minlength=self.s["n_menages"])
        # constantes de recours calées sur le système actuel
        self.c = {}
        for k, part in (("rsa", self.rec["rsa"]), ("ppa", self.rec["prime_activite"])):
            x = self.sim.calculate_add(k, "2026")
            pr = op.proba_recours(x, self.wf, part, self.rec["forme"])
            r = np.where(x > 0, np.maximum(x, 1e-9) ** self.rec["forme"], 0.0)
            self.c[k] = float(np.median(pr[(pr > 0) & (pr < 1)] / r[(pr > 0) & (pr < 1)])) if ((pr > 0) & (pr < 1)).any() else 1.0
        asf = self.sim.calculate_add("asf", "2026")
        self.c["asf"] = Parametres().val("microsimulation.allocation_soutien_familial") * 1e6 / float((self.wf * (asf > 0)).sum())
        self.etat0 = self.etat(self.sim)

    def etat(self, sim, garantie: float | None = None) -> dict:
        """Revenu disponible des ménages après recours, coût du travail, composantes (Md€)."""
        s, an = self.s, "2026"
        rd = sim.calculate("revenu_disponible", an)
        non_percu = np.zeros(s["n_familles"])
        comp = {}
        for k in ("rsa", "ppa", "asf"):
            x = sim.calculate_add(k, an)
            if k == "asf":
                pris = self.u[k] < self.c[k]
            else:
                pris = self.u[k] < np.minimum(1, self.c[k] * np.maximum(x, 1e-9) ** self.rec["forme"])
            non_percu += x * ~pris
            comp[k] = float((self.wf * x * pris).sum()) / 1e9
        # famille → ménage (par la personne demandeuse)
        fam_men = np.zeros(s["n_familles"], int)
        fam_men[s["famille"]] = s["menage"]
        rd = rd - np.bincount(fam_men, weights=non_percu, minlength=s["n_menages"])
        uc = sim.calculate("unites_consommation", an)
        if garantie:
            rd = rd + np.maximum(0.0, garantie * 12 * uc - rd)
        cout = sim.calculate_add("cout_du_travail", an)
        for k in ("aide_logement", "af", "aah"):
            w = self.wf if k != "aah" else np.array([l["poids"] for l in self.lignes])
            comp[k] = float((w * sim.calculate_add(k, an)).sum()) / 1e9
        foy = np.zeros(s["n_foyers"])
        foy[s["foyer"]] = [l["poids"] for l in self.lignes]
        comp["impot_revenu"] = -float((foy * sim.calculate("impot_revenu_restant_a_payer", an)).sum()) / 1e9
        return {"rd": rd, "uc": uc, "cout": float((np.array([l["poids"] for l in self.lignes]) * cout).sum()) / 1e9,
                "rd_total": float((self.wm * rd).sum()) / 1e9, "comp": comp}

    def reforme(self, operations: list[dict]) -> dict:
        tbs = construire(operations)
        garantie = next((o["formule"]["seuil_mensuel"] for o in operations
                         if "formule" in o and o["formule"]["nom"] == "garantie_niveau_vie"), None)
        sim = self.sim if tbs is None else op.simulation(self.lignes, tbs=tbs)[0]
        e1 = self.etat(sim, garantie)
        if sim is not self.sim:
            del sim
            import gc
            gc.collect()
        e0 = self.etat0
        return {"budget": (e1["cout"] - e0["cout"]) - (e1["rd_total"] - e0["rd_total"]), "etat": e1,
                "composantes": {k: e1["comp"][k] - e0["comp"][k] for k in e0["comp"]}}

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
        lignes_m, lignes_d = [], []
        toutes = []
        for ident, spec in mesures.items():
            r = base.reforme(spec["operations"])
            toutes += spec["operations"]
            mot = montant_moteur(nom, ident)
            lignes_m.append({"programme": nom, "mesure": ident, "openfisca_md": round(r["budget"], 2),
                             "moteur_md": round(mot, 2),
                             "ecart_pct": round((r["budget"] / mot - 1) * 100) if abs(mot) > 0.05 else "",
                             **{f"d_{k}": round(v, 2) for k, v in r["composantes"].items()},
                             "note": spec.get("note", "")})
            print(f"{nom:10s} {ident:11s} OpenFisca {r['budget']:+6.2f}  moteur {mot:+6.2f}", flush=True)
        r = base.reforme(toutes)
        for d in base.deciles(r["etat"]):
            lignes_d.append({"programme": nom, "budget_ensemble_md": round(r["budget"], 2),
                             **{k: round(v, 2) if isinstance(v, float) else v for k, v in d.items()}})
        print(f"{nom:10s} ensemble OpenFisca {r['budget']:+6.2f}", flush=True)
        for suffixe, lignes in (("mesures", lignes_m), ("deciles", lignes_d)):
            _ecrire(dossier / f"{nom}_{suffixe}.csv", lignes)
    reunir()


def _ecrire(chemin, lignes):
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)


def reunir():
    dossier = RACINE / "sorties" / "micro"
    for suffixe in ("mesures", "deciles"):
        lignes = []
        for nom in specs():
            f = dossier / f"{nom}_{suffixe}.csv"
            if f.exists():
                with f.open(encoding="utf-8") as g:
                    lignes += list(csv.DictReader(g))
        if lignes:
            _ecrire(RACINE / "sorties" / f"micro_{suffixe}.csv", lignes)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
