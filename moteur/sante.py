"""Dépenses de santé année par année et volet santé de la TVA (feuille Santé, sections 3 à 8)."""
from __future__ import annotations

from .parametres import Parametres
from .depenses.statique import sante_statique, economies_sante_a_terme
from .depenses import ia_administration
from .tva import produits as produits_tva

ANNEES = list(range(2029, 2074))
SCENARIOS = ("prudent", "median", "optimiste")


def pente_assurance_maladie(p: Parametres, nom: str) -> float:
    """Croissance réelle annuelle : PIB + écart qui porte la part de la santé dans le PIB au repère 2030."""
    d = p.val("sante_trajectoire.depenses_2024")
    part = d["sante_md"] / d["pib_md"]
    ecart = ((part + p.val("sante_trajectoire.scenarios_assurance_maladie")[nom]) / part) ** (1 / 6) - 1
    return (1 + p.val("macro.tendance", "prudent")) * (1 + ecart) - 1


def pente_promede(p: Parametres, nom: str) -> float:
    x = p.val("sante_trajectoire.promede")[nom]
    return (1 + p.val("macro.tendance", "prudent")) * (1 + (x["part_2060"] / x["part_2011"]) ** (1 / 49) - 1) - 1


def pente_1(p, s):
    return pente_assurance_maladie(p, p.val("sante_trajectoire.pente_phase_1", s))


def pente_2(p, s):
    return pente_promede(p, p.val("sante_trajectoire.pente_phase_2", s))


def _croissance(p, s, t):
    d = p.val("sante_trajectoire.derniere_annee_phase_1")
    a, b = pente_1(p, s), pente_2(p, s)
    return (1 + a) ** (t - 2029) if t <= d else (1 + a) ** (d - 2029) * (1 + b) ** (t - d)


def derive_2029(p: Parametres) -> float:
    g = p.val("macro.tendance", "prudent")
    return ((1 + pente_assurance_maladie(p, p.val("sante_trajectoire.scenario_2027_2029"))) / (1 + g)) ** 3 if p.val("sante_trajectoire.derive_prise_en_compte") else 1.0


def economie_hopitaux_ia(p: Parametres, t: int) -> float:
    h = p.val("sante_trajectoire.hopitaux_administratifs")
    masse = h["postes"] * h["cout_aligne"] / 1e9
    baisse = min(p.val("ia.plafond_taches_automatisables"),
                 max(0, t - p.val("ia.premiere_annee") + 1) * p.val("ia.departs_retraite_annuels") * p.val("ia.part_departs_non_remplaces"))
    return baisse * masse * (1 - p.val("ia.cout_services_ia"))


def depenses(p: Parametres, s: str) -> dict[int, float]:
    base = sante_statique(p) + economies_sante_a_terme(p, "prudent")  # Santé!B5
    k = derive_2029(p)
    mesures = p.val("sante.mesures_a_terme", s)
    montee = p.val("sante_trajectoire.montee_mesures")
    options = p.val("sante_trajectoire.options")
    fg = p.val("sante_trajectoire.forfait_generalistes")
    g = p.val("macro.tendance", "prudent")
    out = {}
    for t in ANNEES:
        n = max(0, t - 2029)
        eco = sum(v * min(1, n / montee[m]) for m, v in mesures.items())
        eco += sum(o["montant"] * o["comptee"] * min(1, n) for o in options.values())
        cr = _croissance(p, s, t)
        forfait = fg["revalorise_croissance"] * fg["depense_am_2024"] * k * (cr - (1 + g) ** (t - 2029)) * (1 - fg["part_perdue"][s])
        out[t] = (base * k - eco) * cr - economie_hopitaux_ia(p, t) - forfait
    return out


def garde_fou(p: Parametres, s: str = "prudent") -> dict[int, float]:
    """Recette du garde-fou : dépassement de la pente d'engagement, repris l'année suivante par l'accise santé."""
    base = sante_statique(p) + economies_sante_a_terme(p, "prudent")
    k = derive_2029(p)
    d = p.val("sante_trajectoire.derniere_annee_phase_1")
    engagement = pente_1(p, "median")
    pente = pente_1(p, s)
    b = pente_2(p, s)
    depas = {t: max(0.0, base * k * ((1 + pente) ** (min(t, d) - 2029) - (1 + engagement) ** (min(t, d) - 2029)) * (1 + b) ** max(0, t - d)) for t in ANNEES}
    return {t: (0.0 if t == 2029 else depas[t - 1]) for t in ANNEES}


def tva_sante(p: Parametres) -> dict[str, dict[int, float]]:
    """Effet sur le solde du volet santé de la TVA : perte de recette (baisse des ventes) et soins évités."""
    pr = {x.categorie: x for x in produits_tva(p)}
    al = p.val("tva.alcool")
    recette_alcool = al["cout_soins_md"] * (1 - al["part_vin"] * al["abattement_vin"])
    ht = p.val("tva_sante_long_terme.hausse_prix_tabac")
    hausse = {"tabac": ht["prix_apres"] / ht["prix_avant"] - 1}
    import csv
    from .distribution import DONNEES
    ancien = {l["categorie"]: float(l["ancien_taux"]) for l in csv.DictReader((DONNEES / "tva_produits.csv").open(encoding="utf-8"))}
    hausse["alcool"] = (1 + pr["Alcool"].taux_total) / (1 + ancien["Alcool"]) - 1
    hausse["sucres"] = (1 + pr["Produits sucrés et ultra-transformés"].taux_total) / (1 + ancien["Produits sucrés et ultra-transformés"]) - 1
    pp = p.val("tva_sante_long_terme.produits")
    recettes = {"tabac": pp["tabac"]["recette"], "alcool": recette_alcool, "sucres": pp["sucres"]["recette"]}
    couts = {"tabac": pp["tabac"]["cout_soins"], "alcool": al["cout_soins_md"], "sucres": pp["sucres"]["cout_soins"]}
    eps = p.val("tva_sante_long_terme.elasticite_prix")
    baisse = {k: (1 + h) ** eps - 1 for k, h in hausse.items()}
    perte = sum(recettes[k] * baisse[k] for k in recettes)
    g = p.val("macro.tendance", "prudent")
    out = {"perte": {}, **{s: {} for s in SCENARIOS}}
    for s in SCENARIOS:
        vb = p.val("tva_sante_long_terme.vraie_baisse_consommation", s)
        a_terme = -sum(couts[k] * baisse[k] * vb[k] for k in couts)
        annees = p.val("tva_sante_long_terme.annees_plein_effet", s)
        for t in ANNEES:
            pt = perte * (1 + g) ** (t - 2029)
            evites = a_terme * min(1, max(0, t - 2028) / annees) * (1 + g) ** (t - 2029)
            out["perte"][t] = pt
            out[s][t] = pt + evites if s == "prudent" else pt  # médian et optimiste : perte seule (leur pente compte la prévention)
    return out
