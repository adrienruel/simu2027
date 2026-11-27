"""Décomposition du déficit au sens de Maastricht (phase 3.1 de la roadmap, 16/11/2026).

Chaque année, le noyau calcule (moteur/noyau.trajectoire, en points de PIB) :

    déficit = − solde primaire / PIB + taux apparent nominal × dette du début d'année / PIB + autres intérêts / PIB

et le taux apparent est la somme de cinq composantes publiées : taux de base (qui glisse du taux apparent de 2029
vers le taux long), effet de Fisher, réaction de la BCE, prime de dette et écart de taux propre au programme
(`taux_prime`), écart du scénario de crise. La décomposition d'un écart entre deux comptes A et B (deux années d'une
même trajectoire, ou un programme et le statu quo la même année) est exacte, par la moyenne des deux points :

    Δ(i × d) = Δi × (d_A + d_B) / 2 + (i_A + i_B) / 2 × Δd,   d = dette du début d'année / PIB

et Δd se coupe en accumulation de dette (dette en plus, au PIB de B) et croissance (même dette, PIB différent).
La somme des composantes redonne l'écart de déficit à l'arrondi près (test : tests/test_decomposition.py).
"""
from __future__ import annotations

TAUX_HORS_PRIME = ("taux_base", "taux_fisher", "taux_bce", "taux_scenario")
COMPOSANTES = ("primaire", "taux", "prime_dette", "accumulation_dette", "croissance", "autres")
LIBELLES = {
    "primaire": "déficit primaire",
    "taux": "taux hors prime (taux long, Fisher, BCE, crise)",
    "prime_dette": "prime de dette et écart de taux du programme",
    "accumulation_dette": "dette en plus à taux donné",
    "croissance": "PIB en plus à dette donnée",
    "autres": "autres intérêts",
}


def _autres(c: dict) -> float:
    """Intérêts hors taux apparent × dette (emprunt aux ménages : nul pour les programmes publiés), en points de PIB."""
    i = c["taux_apparent"]
    return (c["interets_reels"] - (i - c["inflation"] / 100) * c["dette_debut"]) / c["pib"] * 100


def ecart(a: dict, b: dict) -> dict[str, float]:
    """Écart de déficit de B par rapport à A (points de PIB, + = B plus en déficit), décomposé."""
    da, db = a["dette_debut"] / a["pib"], b["dette_debut"] / b["pib"]
    dm = (da + db) / 2
    out = {"primaire": (-b["solde_primaire"] / b["pib"] + a["solde_primaire"] / a["pib"]) * 100}
    out["taux"] = sum(b[k] - a[k] for k in TAUX_HORS_PRIME) * dm * 100
    out["prime_dette"] = (b["taux_prime"] - a["taux_prime"]) * dm * 100
    im = (a["taux_apparent"] + b["taux_apparent"]) / 2
    out["accumulation_dette"] = im * (b["dette_debut"] - a["dette_debut"]) / b["pib"] * 100
    out["croissance"] = im * a["dette_debut"] * (1 / b["pib"] - 1 / a["pib"]) * 100
    out["autres"] = _autres(b) - _autres(a)
    out["total"] = b["deficit"] - a["deficit"]
    out["residu"] = out["total"] - sum(out[k] for k in COMPOSANTES)
    return out


def niveau(c: dict) -> dict[str, float]:
    """Déficit d'une année en ses parts (points de PIB) : primaire, intérêts au taux hors prime, intérêts de la prime."""
    d = c["dette_debut"] / c["pib"] * 100
    out = {"primaire": -c["solde_primaire"] / c["pib"] * 100,
           "taux": sum(c[k] for k in TAUX_HORS_PRIME) * d,
           "prime_dette": c["taux_prime"] * d,
           "autres": _autres(c)}
    out["total"] = c["deficit"]
    out["residu"] = c["deficit"] - (out["primaire"] + out["taux"] + out["prime_dette"] + out["autres"])
    return out


def aux_taux_statu_quo(v: dict[int, dict], base: dict[int, dict]) -> dict[int, dict[str, float]]:
    """Dette et déficit d'un programme aux taux du statu quo (26/11/2026, demande d'Adrien : lire la dette que crée le
    solde primaire, sans parier sur la réaction des marchés au programme).

    Même solde primaire, mêmes participations et même PIB que le programme ; mais chaque année le taux réel est celui
    du statu quo (`base` : taux apparent nominal et inflation du statu quo), sans la prime de dette, l'écart de taux, la
    baisse d'écart ni l'effacement par une inflation propres au programme (27/11/2026 : l'inflation du programme
    n'efface plus sa dette, le taux nominal ne la suivant pas). Les intérêts de la dette en plus restent comptés :
    s'endetter coûte, même à taux inchangé. Comptes en euros de 2026, comme le noyau :

        dette_fin = dette_debut × (1 + i_sq − π_sq) − solde primaire − participations
        déficit   = (i_sq × dette_debut − solde primaire) / PIB

    Pour le statu quo lui-même, redonne sa dette et son déficit (test). Les autres intérêts (emprunt aux ménages,
    nuls pour les programmes publiés) sont gardés tels quels. Rend {année: {dette, dette_pib, deficit}}."""
    out: dict[int, dict[str, float]] = {}
    dette = None
    for t in sorted(v):
        c, i_sq = v[t], base[t]["taux_apparent"]
        debut = c["dette_debut"] if dette is None else dette
        # 27/11/2026 (analyse indépendante, I1) : taux réel du statu quo (son taux nominal moins SON inflation) ; avant,
        # l'inflation propre au programme effaçait sa dette alors que le taux nominal ne la suit pas
        pi_sq = base[t]["inflation"] / 100
        autres = _autres(c) / 100 * c["pib"]
        solde = c["solde_primaire"] - (i_sq - pi_sq) * debut - autres
        dette = debut - solde - c["participations"]
        out[t] = {"dette": dette, "dette_pib": dette / c["pib"] * 100,
                  "deficit": -(solde - pi_sq * debut) / c["pib"] * 100}
    return out
