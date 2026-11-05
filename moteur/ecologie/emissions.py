"""Émissions de gaz à effet de serre et empreinte carbone, statu quo et programmes (5 novembre 2026).

Décision d'Adrien du 05/11/2026 : la baisse des émissions dépend de l'activité économique, du progrès technique et de
la part de l'économie importée, au lieu d'un taux fixe. Pour chaque secteur (Citepa, Secten) :

    émissions = émissions 2025 × indice de population × indice du revenu par habitant ^ élasticité × intensité

L'intensité baisse au rythme du scénario (ecologie.baisse_intensite). L'activité est celle du statu quo, ou celle
d'un programme (son PIB) : la différence est l'**effet de l'activité**, publié à part et jamais compté comme une
politique climatique (une récession baisse les émissions).

Empreinte (SDES) = part domestique (suit les émissions territoriales) + émissions importées (suivent la consommation
des ménages, la part importée et l'intensité des pays fournisseurs) − ce qu'un programme relocalise, qui revient en émissions
territoriales de l'industrie à une intensité plus faible (ecologie.intensite_relocalisee).

Réponse au prix du carbone (transports et bâtiments) : une seule équation, partagée avec la recette carbone
(moteur/carbone.py) — une tonne qui sort de l'assiette sort aussi des émissions.

Un programme passe ses effets physiques par Mesure.physique (moteur/noyau.py) :
- « emissions_mt:<secteur> » : Mt CO2e en plus (négatif : évitées) dans un secteur, année par année ;
- « relocalisation_mt » : Mt d'émissions importées remplacées par une production en France ;
- « importees_mt » : Mt d'émissions importées en plus (négatif : en moins), par exemple sous l'effet d'une taxe sur
  le contenu carbone des importations.
"""
from __future__ import annotations

import math

from ..parametres import Parametres

SECTEURS = ("transports", "batiments", "industrie", "energie", "agriculture", "dechets")
ENERGIE = ("transports", "batiments", "industrie", "energie")  # assiette des taxes carbone sur l'énergie
ANNEES = list(range(2025, 2074))
ANNEES_MODELE = list(range(2029, 2074))
LIBELLES = {"transports": "Transports", "batiments": "Bâtiments", "industrie": "Industrie", "energie": "Énergie",
            "agriculture": "Agriculture", "dechets": "Déchets et divers"}


def scenario(p: Parametres, s: str) -> str:
    """Scénario réel : dans le calcul de crise (p.en_crise()), la colonne « prudent » est celle de la crise."""
    return p.colonne_prudent if s == "prudent" else s


def _v(p: Parametres, cle: str, s: str):
    from ..statu_quo import _v as v
    return v(p, cle, s)


def activite(p: Parametres, s: str, pib: dict[int, float] | None = None) -> dict[int, tuple[float, float]]:
    """(population, PIB en Md€ de 2026) de 2024 à 2073. Avant 2029, PIB du statu quo rétropolé à la tendance du prudent
    (commun à tous) ; à partir de 2029, celui du programme s'il est donné ; population de l'Insee (2026 pour 2024 et
    2025, première année de la projection)."""
    from .. import statu_quo as sq
    y = dict(sq.pib(p, s))
    g0 = _v(p, "macro.tendance", "prudent")
    for t in range(2028, 2023, -1):
        y[t] = y[t + 1] / (1 + g0)
    if pib:
        y.update({t: v for t, v in pib.items() if t >= 2029})
    pop = sq.population(p, s)
    return {t: (float(sum(pop[max(t, 2026)])), y[t]) for t in range(2024, 2074)}


def _facteur_intensite(p: Parametres, s: str, t: int, cle: str = "ecologie.baisse_intensite", depart: int = 2025) -> float:
    """Baisse cumulée de l'intensité depuis l'année de départ : rythme du prudent jusqu'en 2029 (commun), puis du scénario."""
    b0, b = _v(p, cle, "prudent"), _v(p, cle, s)
    return (1 + b0) ** (min(t, 2029) - depart) * (1 + b) ** (max(t, 2029) - 2029)


def territoriales(p: Parametres, s: str, pib: dict[int, float] | None = None) -> dict[int, dict[str, float]]:
    """Émissions territoriales hors UTCATF par secteur (Mt CO2e), 2025-2073, à l'activité du statu quo (pib=None) ou
    à celle d'un programme."""
    s = scenario(p, s)
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("ecologie_territoriales", s)
    if pib is None and cle in cache:
        return cache[cle]
    e0, el = p.val("ecologie.emissions_2025"), p.val("ecologie.elasticite_revenu")
    a = activite(p, s, pib)
    pop0, y0 = a[2025]
    out = {}
    for t in ANNEES:
        pop, y = a[t]
        ip, ir = pop / pop0, (y / pop) / (y0 / pop0)
        f = _facteur_intensite(p, s, t)
        out[t] = {i: e0[i] * ip * ir ** el[i] * f for i in SECTEURS}
    if pib is None:
        cache[cle] = out
    return out


def indice(p: Parametres, s: str, secteurs=ENERGIE, base: int = 2029) -> dict[int, float]:
    """Émissions du statu quo des secteurs donnés, rapportées à l'année de base (sert à la recette carbone)."""
    e = territoriales(p, s)
    ref = sum(e[base][i] for i in secteurs)
    return {t: sum(e[t][i] for i in secteurs) / ref for t in ANNEES}


# --- Réponse au prix du carbone --------------------------------------------------------------------------------

def prix_statu_quo(p: Parametres, t: int) -> float:
    """Prix du carbone sur les carburants et le chauffage sans programme (€ de 2026 par tonne)."""
    r = p.val("ecologie.prix_carbone_statu_quo")
    return r["cce"] + (r["ets2"] if t >= r["debut_ets2"] else 0.0)


def reponse_long_terme(ecart_prix: float, contenu_kg_par_euro: float, elasticite: float) -> float:
    """Facteur de long terme sur les émissions (et l'assiette) quand le prix du carbone dépasse celui du statu quo de
    ecart_prix €/t : le prix final de l'énergie monte de ecart_prix × contenu / 1 000, la demande répond avec
    l'élasticité. Même formule pour la recette (moteur/carbone.py)."""
    return max(0.01, 1 + ecart_prix * contenu_kg_par_euro / 1000) ** (-elasticite)


def reponse_prix(p: Parametres, prix: dict[int, float], debut: int = 2029) -> dict[int, float]:
    """Facteur sur les émissions des secteurs ecologie.secteurs_prix, année par année, quand un programme fixe le
    prix du carbone `prix` (€ de 2026 par tonne) à partir de `debut` : ajustement partiel vers le long terme."""
    r = p.val("ecologie.reponse_prix")
    out, ln_a = {}, 0.0
    for t in ANNEES:
        if t >= debut:
            cible = math.log(reponse_long_terme(prix[t] - prix_statu_quo(p, t), r["contenu_carbone_kg_par_euro"], r["elasticite"]))
            ln_a += r["ajustement"] * (cible - ln_a)
        out[t] = math.exp(ln_a)
    return out


# --- Programmes ------------------------------------------------------------------------------------------------

def physique(mesures) -> dict[str, dict[int, float]]:
    """Somme des effets physiques des mesures, clé par clé."""
    out: dict[str, dict[int, float]] = {}
    for m in mesures or []:
        for k, v in (getattr(m, "physique", None) or {}).items():
            if k not in ("relocalisation_mt", "importees_mt") and not (k.startswith("emissions_mt:") and k.split(":", 1)[1] in SECTEURS):
                raise ValueError(f"Mesure « {m.nom} » : effet physique inconnu {k}")
            d = out.setdefault(k, {})
            for t, x in v.items():
                d[t] = d.get(t, 0.0) + x
    return out


def profil(p: Parametres, s: str, spec: dict) -> dict[int, float]:
    """Effet physique d'une mesure (Mt CO2e par an ; négatif : évitées), pour un programme qui chiffre ses mesures
    en tonnes (Mesure.physique) :

        effet(t) = effet à plein (scénario s) × montée linéaire de `debut` à `plein`
                   × extinction linéaire de `fin_debut` à `fin` (facultatif : le statu quo rattrape la mesure)
                   × intensité du statu quo rapportée à celle de `debut` (si `suit_intensite`, par défaut)

    Le dernier facteur évite de compter deux fois la décarbonation tendancielle : une tonne évitée par une
    rénovation en 2040 vaut moins qu'en 2028, puisque le chauffage du statu quo émet déjà moins."""
    s_r = scenario(p, s)
    effet = spec["effet_mt"][s_r] if isinstance(spec["effet_mt"], dict) else spec["effet_mt"]
    debut, plein = int(spec["debut"]), int(spec["plein"])
    out = {}
    for t in ANNEES:
        montee = min(1.0, max(0.0, (t - debut + 1) / (plein - debut + 1)))
        fin = 1.0
        if spec.get("fin"):
            f0, f1 = int(spec["fin_debut"]), int(spec["fin"])
            fin = min(1.0, max(0.0, (f1 - t) / (f1 - f0)))
        rel = (_facteur_intensite(p, s_r, t) / _facteur_intensite(p, s_r, debut)) if spec.get("suit_intensite", True) and t >= debut else 1.0
        out[t] = effet * montee * fin * rel
    return out


def snbc(p: Parametres) -> dict[int, float]:
    """Plafond annuel moyen des budgets carbone (hors UTCATF) : SNBC-3 jusqu'en 2038, puis ligne droite jusqu'à
    l'objectif de 2050, puis stable."""
    b = {int(k): v for k, v in p.val("ecologie.budgets_carbone").items()}
    debuts = sorted(b)
    fin, obj = debuts[-1] + 4, p.val("ecologie.objectif_2050")
    out = {}
    for t in range(debuts[0], 2074):
        if t <= fin:
            out[t] = b[max(d for d in debuts if d <= t)]
        else:
            out[t] = b[debuts[-1]] + (obj - b[debuts[-1]]) * min(1.0, (t - fin) / (2050 - fin))
    return out


def bilan(p: Parametres, s: str, mesures=None, contexte: dict | None = None) -> dict[int, dict]:
    """Émissions d'un programme (statu quo si mesures et contexte sont vides), année par année :
    territoriales par secteur et au total, décomposées en statu quo + effet de l'activité + effet des mesures ;
    empreinte (domestique + importée) ; par habitant ; plafond SNBC."""
    sq_e = territoriales(p, s)
    pib = (contexte or {}).get("pib")
    act_e = territoriales(p, s, pib) if pib else sq_e
    ph = physique(mesures)
    reloc = ph.get("relocalisation_mt", {})
    s_r = scenario(p, s)
    imp = p.val("ecologie.importations_2024")
    e2024 = p.val("ecologie.emissions_2024_total")
    ratio_reloc = _v(p, "ecologie.intensite_relocalisee", s_r)
    pen = p.val("ecologie.penetration_importations")
    a, a_sq = activite(p, s_r, pib), activite(p, s_r)
    # importations : elles suivent la consommation des ménages ; l'écart de consommation avec le statu quo est l'écart
    # de PIB moins ce qui n'y va pas (épargne retenue, investissement : contexte pib_hors_consommation). Décision
    # d'Adrien du 05/11/2026, commune à tous les programmes.
    hors = (contexte or {}).get("pib_hors_consommation") or {}
    a_imp = {t: (pop, y - hors.get(t, 0.0)) for t, (pop, y) in a.items()}
    plafond = snbc(p)
    out = {}
    for t in ANNEES:
        secteurs = {i: act_e[t][i] + ph.get(f"emissions_mt:{i}", {}).get(t, 0.0) for i in SECTEURS}
        r = reloc.get(t, 0.0)
        secteurs["industrie"] += r * ratio_reloc
        total, total_sq, total_act = sum(secteurs.values()), sum(sq_e[t].values()), sum(act_e[t].values())
        domestique = imp["domestique"] * total / e2024
        importees = (imp["importees"] * a_imp[t][1] / a_sq[2024][1] * (1 + pen) ** (t - 2024)
                     * _facteur_intensite(p, s_r, t, "ecologie.baisse_intensite_importations", 2024) - r
                     + ph.get("importees_mt", {}).get(t, 0.0))
        pop = a[t][0]
        out[t] = {
            "secteurs": secteurs, "territoriales": total, "statu_quo": total_sq,
            "effet_activite": total_act - total_sq, "effet_mesures": total - total_act,
            "domestique": domestique, "importees": importees, "empreinte": domestique + importees,
            "population": pop, "territoriales_hab": total * 1e6 / pop, "empreinte_hab": (domestique + importees) * 1e6 / pop,
            "plafond_snbc": plafond.get(t),
        }
    return out


def ecart_snbc_cumule(b: dict[int, dict], depuis: int = 2029) -> dict[int, float]:
    """Dépassement cumulé des plafonds de la SNBC depuis `depuis` (Mt ; négatif : en dessous)."""
    out, cumul = {}, 0.0
    for t in sorted(b):
        if t >= depuis:
            cumul += b[t]["territoriales"] - b[t]["plafond_snbc"]
            out[t] = cumul
    return out


if __name__ == "__main__":
    from ..statu_quo import SCENARIOS
    p = Parametres()
    print("Statu quo : émissions territoriales (Mt CO2e), empreinte par habitant (t), plafond SNBC")
    for s in SCENARIOS:
        b = bilan(p, s)
        print(f"  {s:<10}" + "  ".join(f"{t} : {b[t]['territoriales']:5.0f} / {b[t]['empreinte_hab']:4.1f} t / {b[t]['plafond_snbc']:4.0f}"
                                       for t in (2025, 2030, 2037, 2050, 2073)))
