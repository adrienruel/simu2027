"""Population synthétique calculée par OpenFisca-France (phase F1-F2 de la roadmap).

Lit parametres/donnees/population_synthetique_2026.csv (outils/population_synthetique.py), construit les
foyers fiscaux, familles et ménages, calcule la législation de l'année et compare les totaux pondérés aux
comptes (microsimulation.cibles_2026). Les revenus des deux années précédentes sont pris égaux à ceux de
l'année (bases ressources des prestations) : DÉCISION, la population n'a pas d'historique.

    python -m outils.openfisca_population            # totaux contre les cibles
"""
from __future__ import annotations

import csv
import zlib
from collections import defaultdict
from pathlib import Path

import numpy as np

from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parent.parent
POPULATION = RACINE / "parametres" / "donnees" / "population_synthetique_2026.csv"
PART_PRIMES_FONCTIONNAIRES = 0.246  # comme outils/openfisca_actuel.py (DGAFP, rapport annuel 2025)

# Agrégats comparés aux comptes : nom → (variables OpenFisca, entité, signe).
AGREGATS = {
    "impot_revenu": (("impot_revenu_restant_a_payer",), "foyer_fiscal", -1),
    "prestations_entretien": (("af", "cf", "ars", "asf", "paje_base", "paje_naissance"), "famille", 1),
    "aides_logement": (("aide_logement",), "famille", 1),
    "rsa": (("rsa",), "famille", 1),
    "prime_activite": (("ppa",), "famille", 1),
    "aah": (("aah",), "individu", 1),
}


def lire(chemin: Path = POPULATION) -> list[dict]:
    with chemin.open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    for l in lignes:
        for k in ("menage", "unite", "rattache", "age", "handicap", "maries", "mois_travailles", "debut_mois"):
            l[k] = int(l[k])
        for k in ("poids", "salaire_brut", "cout_employeur", "revenu_independant", "chomage_brut", "pension_brute",
                  "dividendes", "revenus_fonciers", "loyer_mensuel"):
            l[k] = float(l[k])
    return lignes


def structure(lignes: list[dict]) -> dict:
    """Foyers fiscaux, familles et rôles de chaque personne.

    Enfant à charge : moins de 21 ans, ou étudiant de moins de 25 ans. Couple marié ou pacsé : une déclaration
    commune ; sinon chaque conjoint déclare seul, les enfants avec la personne de référence. Une seule famille
    (au sens des prestations) pour le couple et ses enfants à charge ; les autres adultes forment la leur."""
    par_menage = defaultdict(list)
    for j, l in enumerate(lignes):
        par_menage[l["menage"]].append(j)
    foyer, role_foyer = [None] * len(lignes), [None] * len(lignes)
    famille, role_famille = [None] * len(lignes), [None] * len(lignes)
    role_menage = [None] * len(lignes)
    nf = nfa = 0
    foyer_unite = {}
    ordre = sorted(par_menage, key=lambda m: lignes[par_menage[m][0]]["rattache"])  # ménages des parents d'abord
    for m in ordre:
        js = par_menage[m]
        ref = [j for j in js if lignes[j]["role"] == "ref"][0]
        if lignes[ref]["rattache"]:
            # Étudiant décohabitant : son propre ménage et sa famille, à charge dans le foyer fiscal des parents.
            role_menage[ref] = "personne_de_reference"
            famille[ref], role_famille[ref] = nfa, "demandeur"
            nfa += 1
            foyer[ref], role_foyer[ref] = foyer_unite[lignes[ref]["unite"]], "personne_a_charge"
            continue
        conj = [j for j in js if lignes[j]["role"] == "conjoint"]
        a_charge = [j for j in js if lignes[j]["role"] == "enfant" and (lignes[j]["age"] < 21 or (lignes[j]["age"] < 25 and lignes[j]["statut"] == "etudiant"))]
        autres = [j for j in js if j != ref and j not in conj and j not in a_charge]
        role_menage[ref] = "personne_de_reference"
        for j in conj:
            role_menage[j] = "conjoint"
        for j in a_charge:
            role_menage[j] = "enfant"
        for j in autres:
            role_menage[j] = "autre"
        # Famille principale
        for j, r in zip([ref, *conj], ("demandeur", "conjoint")):
            famille[j], role_famille[j] = nfa, r
        for j in a_charge:
            famille[j], role_famille[j] = nfa, "enfant"
        nfa += 1
        for j in autres:
            famille[j], role_famille[j] = nfa, "demandeur"
            nfa += 1
        # Foyers fiscaux
        commun = bool(conj) and lignes[ref]["maries"] == 1
        foyer[ref], role_foyer[ref] = nf, "declarant_principal"
        foyer_unite[lignes[ref]["unite"]] = nf
        for j in a_charge:
            foyer[j], role_foyer[j] = nf, "personne_a_charge"
        if commun:
            for j in conj:
                foyer[j], role_foyer[j] = nf, "conjoint"
        nf += 1
        if not commun:
            for j in conj:
                foyer[j], role_foyer[j] = nf, "declarant_principal"
                nf += 1
        for j in autres:
            foyer[j], role_foyer[j] = nf, "declarant_principal"
            nf += 1
    menages = sorted(par_menage)
    idx_men = {m: k for k, m in enumerate(menages)}
    return {"foyer": np.array(foyer), "role_foyer": role_foyer, "famille": np.array(famille), "role_famille": role_famille,
            "menage": np.array([idx_men[l["menage"]] for l in lignes]), "role_menage": role_menage,
            "n_foyers": nf, "n_familles": nfa, "n_menages": len(menages), "menages": menages}


def simulation(lignes: list[dict], annee: int = 2026, tbs=None):
    """Simulation OpenFisca de la population (système de base, ou tbs réformé)."""
    from openfisca_core.simulation_builder import SimulationBuilder
    from openfisca_france import FranceTaxBenefitSystem
    tbs = tbs or FranceTaxBenefitSystem()
    s = structure(lignes)
    n = len(lignes)
    sb = SimulationBuilder()
    sb.create_entities(tbs)
    sb.declare_person_entity("individu", [f"i{j}" for j in range(n)])
    for cle, ids_cle, roles in (("foyer_fiscal", "foyer", "role_foyer"), ("famille", "famille", "role_famille"), ("menage", "menage", "role_menage")):
        nb = {"foyer": s["n_foyers"], "famille": s["n_familles"], "menage": s["n_menages"]}[ids_cle]
        ent = sb.declare_entity(cle, [f"{cle}{k}" for k in range(nb)])
        sb.join_with_persons(ent, [f"{cle}{k}" for k in s[ids_cle]], s[roles])
    sim = sb.build(tbs)

    col = lambda k: np.array([l[k] for l in lignes])  # noqa: E731
    statut = col("statut")
    age = col("age")
    brut = col("salaire_brut")
    mois = col("mois_travailles")
    debut = col("debut_mois")
    public = statut == "agent_public"
    rev_ind = col("revenu_independant")
    groupe = col("groupe_independant")
    activite = np.select([np.isin(statut, ["salarie_prive", "agent_public", "independant"]), statut == "chomeur",
                          statut == "etudiant", statut == "retraite"], ["actif", "chomeur", "etudiant", "retraite"], "inactif")
    couple = np.isin(col("role"), ["ref", "conjoint"]) & np.isin(col("type"), ["couple_sans_enfant", "couple_avec_enfants", "complexe"])
    marie = couple & (col("maries") == 1)
    # Grandeurs par ménage (premier individu de chaque ménage dans l'ordre de structure)
    prem = {}
    for j, m in enumerate(s["menage"]):
        prem.setdefault(int(m), j)
    pm = np.array([prem[k] for k in range(s["n_menages"])])
    logement = col("logement")[pm]
    occ = np.select([logement == "proprietaire", logement == "locataire_social", logement == "locataire_prive"],
                    ["proprietaire", "locataire_hlm", "locataire_vide"], "loge_gratuitement")
    # Capital par foyer (porté par la personne de référence)
    div_f = np.bincount(s["foyer"], weights=col("dividendes"), minlength=s["n_foyers"])
    fon_f = np.bincount(s["foyer"], weights=col("revenus_fonciers"), minlength=s["n_foyers"])

    for y in (str(annee - 3), str(annee - 2), str(annee - 1), str(annee)):
        sim.set_input("date_naissance", y, np.array([f"{annee - a}-07-01" for a in age], dtype="datetime64[D]"))
        for m in range(12):
            travaille = (m >= debut) & (m < debut + mois)
            sim.set_input("salaire_de_base", f"{y}-{m + 1:02d}", np.where(public | ~travaille, 0.0, brut / mois))
        tib = np.where(public, brut * (1 - PART_PRIMES_FONCTIONNAIRES), 0.0)
        sim.set_input("traitement_indiciaire_brut", y, tib)
        sim.set_input("primes_fonction_publique", y, np.where(public, brut - tib, 0.0))
        sim.set_input("categorie_salarie", y, np.where(public, "public_titulaire_etat", "prive_non_cadre"))
        sim.set_input("ebic_impv", y, np.where(np.isin(groupe, ["classiques", "agriculteurs"]), np.maximum(rev_ind, 0), 0.0))
        sim.set_input("mbnc_impo", y, np.where(groupe == "micro", rev_ind / 0.66, 0.0))
        sim.set_input("chomage_brut", y, col("chomage_brut"))
        sim.set_input("retraite_brute", y, col("pension_brute"))
        sim.set_input("activite", y, activite)
        sim.set_input("statut_marital", y, np.where(marie, "marie", "celibataire"))
        sim.set_input("handicap", y, col("handicap") == 1)
        sim.set_input("taux_incapacite", y, np.where(col("handicap") == 1, 0.8, 0.0))
        sim.set_input("f2dc", y, div_f)
        sim.set_input("f4ba", y, fon_f * 0.85)  # loyers nets des charges déductibles (≈ 15 %), au réel
        sim.set_input("statut_occupation_logement", y, occ)
        sim.set_input("loyer", y, col("loyer_mensuel")[pm] * 12)
        sim.set_input("zone_apl", y, col("zone")[pm])
    return sim, s


def totaux(lignes: list[dict], annee: int = 2026, tbs=None) -> dict:
    sim, s = simulation(lignes, annee, tbs)
    an = str(annee)
    poids_p = np.array([l["poids"] for l in lignes])
    poids = {"individu": poids_p}
    for ent, cle, nb in (("foyer_fiscal", "foyer", "n_foyers"), ("famille", "famille", "n_familles"), ("menage", "menage", "n_menages")):
        w = np.zeros(s[nb])
        w[s[cle]] = poids_p  # poids du ménage, identique pour toutes ses personnes
        poids[ent] = w
    recours = Parametres().val("microsimulation.recours")
    asf = Parametres().val("microsimulation.allocation_soutien_familial")
    res = {}
    for nom, (variables, ent, signe) in AGREGATS.items():
        x = 0.0
        for var in variables:
            y = sim.calculate_add(var, an) if sim.tax_benefit_system.variables[var].definition_period != "year" else sim.calculate(var, an)
            if var == "asf":  # l'autre parent verse souvent une pension : seule une part des éligibles la perçoit
                y = y * recourt(y, poids[ent], asf * 1e6 / float((poids[ent] * (y > 0)).sum()), graine=7, forme="uniforme")
            x = x + y
        if nom in recours:
            x = x * recourt(x, poids[ent], recours[nom], graine=zlib.crc32(nom.encode()) % 1000)
        res[nom] = signe * float((x * poids[ent]).sum()) / 1e9
    return res


def recourt(montant, poids, part, graine=0, forme="racine"):
    """Tirage du recours : probabilité min(1, c·√montant), c calé pour que la part pondérée des éligibles qui
    perçoivent soit « part » (microsimulation.recours)."""
    rng = np.random.default_rng(graine)
    u = rng.random(len(montant))
    elig = montant > 0
    r = np.sqrt(np.maximum(montant, 0)) if forme == "racine" else elig.astype(float)
    lo, hi = 0.0, 10.0
    for _ in range(60):
        c = (lo + hi) / 2
        pris = elig & (u < np.minimum(1, c * r))
        if (poids * pris).sum() / (poids * elig).sum() < part:
            lo = c
        else:
            hi = c
    return pris.astype(float)


if __name__ == "__main__":
    import time
    t = time.time()
    lignes = lire()
    res = totaux(lignes)
    cibles = Parametres().val("microsimulation.cibles_2026")
    print(f"OpenFisca : {time.time() - t:.0f} s")
    for k, x in res.items():
        print(f"  {k:24s} {x:7.1f} Md€   cible {cibles[k]:6.1f}   écart {x / cibles[k] - 1:+.1%}")
