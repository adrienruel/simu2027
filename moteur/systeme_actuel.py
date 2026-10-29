"""Système actuel par classe : approximé comme dans la v235, ou calculé par OpenFisca-France (salariés du privé).

Net actuel = net avant aides + RSA et prime d'activité + APL − taxe foncière estimée.
"""
from __future__ import annotations

from .parametres import Parametres


def rsa_et_prime_prive(net_annuel: float, p: Parametres) -> float:
    """RSA et prime d'activité d'une personne seule (barèmes d'avril 2026), annuels."""
    m = net_annuel / 12
    rsa_m, fl = p.val("systeme_actuel.rsa_personne_seule"), p.val("systeme_actuel.rsa_forfait_logement")
    pa = p.val("systeme_actuel.prime_activite")
    rsa = max(0.0, rsa_m - m - fl)
    bonus = 0.0 if m <= pa["bonus_debut"] else pa["bonus_max"] * min(1, (m - pa["bonus_debut"]) / (pa["bonus_max_a"] - pa["bonus_debut"]))
    prime = max(0.0, pa["forfaitaire"] + pa["part_revenus"] * m + bonus - max(pa["forfaitaire"], m + pa["forfait_logement"] + rsa))
    if prime < pa["seuil_versement"]:
        prime = 0.0
    return 12 * (rsa + prime)


def prime_agents(net_annuel: float, p: Parametres) -> float:
    m = net_annuel / 12
    a = p.val("systeme_actuel.prime_activite_agents")
    if m <= a["revenu_max"]:
        return 12 * a["montant_max"] * m / a["revenu_max"]
    if m <= a["revenu_extinction"]:
        return 12 * a["montant_max"] * (a["revenu_extinction"] - m) / (a["revenu_extinction"] - a["revenu_max"])
    return 0.0


def apl(net_annuel: float, p: Parametres) -> float:
    m = net_annuel / 12
    a = p.val("systeme_actuel.apl")
    if m <= a["revenu_plein"]:
        return 12 * a["montant_plein"]
    if m <= a["revenu_extinction"]:
        return 12 * a["montant_plein"] * (a["revenu_extinction"] - m) / (a["revenu_extinction"] - a["revenu_plein"])
    return 0.0


def taxe_fonciere(net_annuel: float, p: Parametres, public: bool) -> float:
    if not public and net_annuel < p.val("systeme_actuel.exoneration_taxe_fonciere_prive"):
        return 0.0
    t = p.val("systeme_actuel.taxe_fonciere")
    return t["coef_public" if public else "coef_prive"] * net_annuel ** t["exposant"]


def net_actuel(net_avant_aides: float, p: Parametres, public: bool) -> float:
    aides = (prime_agents(net_avant_aides, p) if public else rsa_et_prime_prive(net_avant_aides, p)) + apl(net_avant_aides, p)
    return net_avant_aides + aides - taxe_fonciere(net_avant_aides, p, public)


def consommation_actuelle_ht(net: float, p: Parametres) -> float:
    t = p.val("systeme_actuel.taux_tva_moyen")
    return p.val("consommation.coefficient") * (net / (1 + t)) ** p.val("consommation.exposant")


def _table_openfisca(annee: int = 2026, versant: str | None = None) -> dict:
    import csv
    from .distribution import DONNEES
    nom = f"openfisca_prive_{annee}.csv" if versant is None else f"openfisca_public_{versant}_{annee}.csv"
    with (DONNEES / nom).open(encoding="utf-8") as f:
        lignes = sorted((dict((k, float(v)) for k, v in l.items()) for l in csv.DictReader(f)), key=lambda l: l["cout_du_travail"])
    return {k: [l[k] for l in lignes] for k in lignes[0]}


def _interp(x: float, xs: list[float], ys: list[float]) -> float:
    import bisect
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1] * x / xs[-1]  # au-delà de la grille : proportionnel
    i = bisect.bisect_right(xs, x)
    return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1])


def nets_prive(p: Parametres) -> dict[str, list[float]]:
    """Par classe de salariés du privé (coûts employeur de 2026) : net après impôt sur le revenu (« net avant
    aides ») et net actuel (aides comprises, taxe foncière estimée retirée).

    Source : OpenFisca-France (table parametres/donnees/openfisca_prive_2026.csv, personne seule locataire)
    si systeme_actuel.source vaut « openfisca » ; sinon les nets saisis de la v235."""
    from .recettes.impot_salaires import effectifs_prive_2026
    from .recettes.entreprises import _net_avant_aides
    d = effectifs_prive_2026(p)
    if p.val("systeme_actuel.source") != "openfisca":
        avant = _net_avant_aides("salaries_prive.csv")
        return {"avant_aides": avant, "actuel": [net_actuel(a, p, False) for a in avant]}
    cache = p.__dict__.setdefault("_cache", {})
    if "nets_prive" not in cache:
        T = _table_openfisca()
        x = T["cout_du_travail"]
        avant, actuel = [], []
        for c in d.milieux:
            net = _interp(c, x, T["salaire_net"]) + _interp(c, x, T["impot_revenu_restant_a_payer"])
            aides = _interp(c, x, T["rsa"]) + _interp(c, x, T["ppa"]) + _interp(c, x, T["aide_logement"])
            avant.append(net)
            actuel.append(net + aides - taxe_fonciere(net, p, False))
        cache["nets_prive"] = {"avant_aides": avant, "actuel": actuel}
    return cache["nets_prive"]


def nets_public(p: Parametres) -> dict[str, list[float]]:
    """Par classe d'agents publics (coût employeur actuel de 2026) : net après impôt et net actuel.

    OpenFisca : fonctionnaires titulaires de chaque versant (primes à 24,6 % du brut), moyenne pondérée par la
    part de chaque versant dans la masse salariale ; sinon les nets saisis de la v235."""
    from .recettes.impot_salaires import effectifs_public_2026
    from .recettes.entreprises import _net_avant_aides
    d = effectifs_public_2026(p)
    if p.val("systeme_actuel.source") != "openfisca":
        avant = _net_avant_aides("fonctionnaires.csv")
        return {"avant_aides": avant, "actuel": [net_actuel(a, p, True) for a in avant]}
    cache = p.__dict__.setdefault("_cache", {})
    if "nets_public" not in cache:
        versants = p.val("alignement.versants")
        poids = {v: x["part"] for v, x in versants.items()}
        tables = {v: _table_openfisca(versant=v) for v in poids}
        total_poids = sum(poids.values())
        avant, actuel = [], []
        for c in d.milieux:
            a = r = 0.0
            for v, w in poids.items():
                T, x = tables[v], tables[v]["cout_du_travail"]
                net = _interp(c, x, T["salaire_net"]) + _interp(c, x, T["impot_revenu_restant_a_payer"])
                aides = _interp(c, x, T["rsa"]) + _interp(c, x, T["ppa"]) + _interp(c, x, T["aide_logement"])
                a += w * net
                r += w * (net + aides - taxe_fonciere(net, p, True))
            avant.append(a / total_poids)
            actuel.append(r / total_poids)
        cache["nets_public"] = {"avant_aides": avant, "actuel": actuel}
    return cache["nets_public"]
