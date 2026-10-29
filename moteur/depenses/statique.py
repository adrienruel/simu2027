"""Dépenses statiques du nouveau système (feuille Total, lignes 23 à 44), en euros de 2026.

"""
from __future__ import annotations



from ..parametres import Parametres
from ..unites import facteur
from ..recettes import tva_menages
from ..recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
from ..epargne import part_rui_salarie
from ..recettes.independants import classes as classes_independants
from . import budget_etat, ia_administration, economies_missions, quotient
from ..retraites_transition import cout_transition_moyen

MD = 1e9


def economies_sante_a_terme(p: Parametres, scenario: str = "prudent") -> float:
    return sum(p.val("sante.mesures_a_terme", scenario).values())


def autonomie(p: Parametres) -> float:
    """Aide sociale à l'autonomie reprise par l'État, moins la part de RUI déjà versée pour ces heures (Md€)."""
    if not p.val("sante.reprise_autonomie_par_etat"):
        return 0.0
    brut = p.val("sante.aide_sociale_autonomie_2024") * facteur(p, 2024, "recettes")
    h = p.val("sante.heures_apa_millions")
    heures_apa = h["montant_md"] / h["cout_horaire"] * 1000
    etp = p.val("sante.etp_aide_autonomie")
    hm = p.val("sante.heures_mensuelles_temps_plein")
    heures = (etp["emploi_direct"] + etp["prestataires"]) * hm * 12 / 1e6
    rui_par_heure = p.val("rui.montant") / hm
    return brut - min(heures_apa, heures) * rui_par_heure / 1000


def economie_hopitaux(p: Parametres) -> float:
    """Alignement du coût employeur hospitalier sur le privé (Md€)."""
    d = effectifs_public_2026(p)
    masse = sum(c * n for c, n in zip(d.milieux, d.effectifs)) / MD
    v = p.val("alignement.versants")["hospitaliere"]
    baisse = 1 - (1 + p.val("alignement.charges_patronales_prive")) / (1 + v["charges_actuelles"])
    return masse * v["part"] * baisse


def securite_sociale(p: Parametres) -> tuple[float, float]:
    """(postes absents à ajouter hors santé, dont santé), Md€."""
    s = p.val("securite_sociale.postes_absents")
    agent = budget_etat.baisse_cout_agents_etat(p)
    masse = p.val("alignement.masse_salariale_etat_2026") * (1 + agent)
    cout_agent = masse * MD / sum(p.val("ia.effectifs_etat").values())
    ft = s["france_travail_unedic"]["montant"]
    aides = p.val("securite_sociale.aides_france_travail_supprimees")
    gain_ia = p.val("securite_sociale.agents_france_travail") * cout_agent * p.val("ia.plafond_taches_automatisables") * (1 - p.val("ia.cout_services_ia")) / MD
    part_ft = 1 - gain_ia / ft - aides / ft
    total, sante = 0.0, 0.0
    for nom, x in s.items():
        montant = x["montant"]
        if montant == "calcul":
            montant = p.val("securite_sociale.gestion_total_hors_at_maladie") - s["gestion_maladie"]["montant"] - s["gestion_at"]["montant"]
        part = x["part"]
        if part == "calcul":
            part = part_ft if nom == "france_travail_unedic" else part_ft + aides / ft
        total += montant * part
        if x.get("sante"):
            sante += montant * part
    return total - sante, sante


def sante_statique(p: Parametres) -> float:
    """Ligne 40 (Md€) : ONDAM + invalidité + autonomie − économies à terme (prudent) − hôpitaux + postes santé de la Sécu."""
    return (p.val("sante.ondam_2026") + p.val("sante.pensions_invalidite_2024") * facteur(p, 2024, "recettes")
            + autonomie(p) - economies_sante_a_terme(p, "prudent") - economie_hopitaux(p) + securite_sociale(p)[1])


def rui_enfants(p: Parametres) -> float:
    """Part de la ligne 42 versée pour les enfants (compléments de RUI, Md€)."""
    rui = p.val("rui.montant") * 12
    return (p.val("rui_complements.enfants") * p.val("rui_complements.part_enfant")
            + p.val("rui_complements.enfants_rang2") * max(0.0, p.val("rui_complements.part_enfant_rang2") - p.val("rui_complements.part_enfant"))
            + p.val("rui_complements.enfants_rang3") * max(0.0, p.val("rui_complements.part_enfant_rang3") - p.val("rui_complements.part_enfant"))
            + p.val("rui_complements.enfants_parent_isole") * p.val("rui_complements.part_enfant_parent_isole")) * rui / MD


def rui_aah(p: Parametres, scenario: str = "prudent") -> float:
    """Ligne 42 (Md€) : RUI de toutes les populations + AAH."""
    rui = p.val("rui.montant") * 12
    enfants = rui_enfants(p) * MD
    plafond = p.val("inactifs.revenu_annulant_rui") * 12
    complement = lambda revenu: max(0.0, (plafond - revenu) / plafond * rui)
    agri = sum(c["effectif"] * complement(c["revenu"]) for c in classes_independants(p, scenario) if c["groupe"] == "agriculteurs")
    micro = sum(c["effectif"] * complement(c["revenu"]) for c in classes_independants(p, scenario) if c["groupe"] == "micro") * (1 - p.val("rui_complements.micro_en_complement"))
    etudiants = p.val("inactifs.etudiants") * rui
    revenus, effectifs = tva_menages.lire_inactifs()
    inactifs = sum(n * complement(c) for c, n in zip(revenus, effectifs))
    d = effectifs_prive_2026(p)
    salaries = sum(n * part_rui_salarie(c, p) * rui for c, n in zip(d.milieux, d.effectifs))
    chomeurs = p.val("inactifs.chomeurs_bit") * (1 - p.val("inactifs.part_chomeurs_deja_comptee")) * p.val("inactifs.rui_moyen_chomeurs") * rui
    aah = p.val("rui_complements.aah") + p.val("rui_complements.aide_poste_entreprises_adaptees")
    return (enfants + agri + micro + etudiants + inactifs + salaries + chomeurs) / MD + aah


def subventions_restees(p: Parametres) -> float:
    """Ligne 33 (Md€) : moitié des transports, soutien à l'énergie, moitié de France 2030."""
    m = {x["mission"]: float(x["credits"]) for x in budget_etat._missions() if x["credits"] != "calcul"}
    return (m["Infrastructures et services de transport"] * 0.5 + m["Service public de l’énergie, énergie et climat"] * 1.0
            + m["Investir pour la France de 2030"] * 0.5)


def depenses(p: Parametres, scenario: str = "prudent") -> dict:
    b = budget_etat.lignes_modele(p)
    secu_hors_sante, _ = securite_sociale(p)
    l = {
        "missions": sum(v for k, v in b.items() if k not in ("Autres", "Fonds", "Supprimé", "Retraites")),
        "charge_dette": p.val("budget_statique.charge_dette_statique"),
        "subventions_restees": subventions_restees(p),
        "sante": sante_statique(p),
        "retraites_socle": p.val("budget_statique.retraites_socle"),
        "rui_aah": rui_aah(p, scenario),
        "cout_transition_moyen": cout_transition_moyen(p),
        "ia_administration": -ia_administration.economie_moyenne(p),
        "economies_supplementaires": -sum(p.val("budget_statique.economies_supplementaires").values()),
        "autres_missions": b["Autres"] + p.val("budget_statique.concours_outre_mer")["montant"] * p.val("budget_statique.concours_outre_mer")["part"],
        "collectivites": sum(p.val("collectivites.besoin_financement_2024")) * (1 - p.val("collectivites.part_financee")) * facteur(p, 2024, "recettes"),
        "securite_sociale_hors_sante": secu_hors_sante,
        "economies_missions": -sum(economies_missions.economies(p).values()),
        "quotient_familial": quotient.cout(p)["total"],
    }
    return {"lignes": l, "total": sum(l.values())}
