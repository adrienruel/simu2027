"""Banc d'essai de la phase E : variantes standard de Mésange 2017 passées par le pipeline commun (demande bouclée
et canal d'offre), comparées aux résultats publiés (Bardaji et al., Insee G2017/04).

Conditions de Mésange : taux réels et change nominal constants (p. 100) : la règle de la BCE est coupée. Scénario
médian (multiplicateur 1, comme le scénario miroir prudent d'une relance). Choc permanent d'un point du PIB du
statu quo, dès 2027 (« 1 an » = 2027).

Usage : python -m outils.banc_mesange
"""
from __future__ import annotations

from moteur import bouclage, offre, statu_quo as sq
from moteur.noyau import Mesure
from moteur.parametres import Parametres
from moteur.programme_simple import TOUTES

ANS = (1, 2, 3, 5, 10)
MESANGE = {
    # PIB en volume, écart en % au compte central (p. 102, 105, 107)
    "depense": (0.78, 1.06, 1.03, 0.86, 0.53),
    "investissement_public": (1.31, 1.38, 1.22, 0.93, 0.57),
    "cotisations_employeurs": (0.20, 0.55, 0.76, 0.97, 1.29),
    # hausse de 10 $ du baril, facture énergétique +0,2 point de PIB (p. 123)
    "petrole": (-0.10, -0.24, -0.18, -0.21, -0.22),
}
PRIX_MESANGE = {
    "depense": (0.20, 0.58, 0.94, 1.42, 1.88),
    "investissement_public": (0.31, 0.92, 1.37, 1.86, 2.25),
    "cotisations_employeurs": (-0.36, -0.70, -0.87, -1.09, -1.32),
    "petrole": (0.33, 0.40, 0.40, 0.37, 0.24),
}


def variante(p, nom: str, s: str = "median") -> dict:
    y = sq.pib(p, s)
    un = {t: 0.01 * y[max(t, 2029)] for t in TOUTES}
    if nom == "depense":
        m = [Mesure("Dépense publique", "etat_missions", un)]
    elif nom == "investissement_public":
        m = [Mesure("Investissement public", "investissement", un)]
    elif nom == "petrole":
        # facture payée à l'étranger (revenu perdu, poids de demande) + énergie plus chère pour les entreprises (offre)
        e = p.val("bouclage.energie_importee")
        rep = bouclage.reponse(p, s, {t: -e["poids_demande"] * 0.002 * y[max(t, 2029)] for t in TOUTES}, TOUTES)
        out = {}
        for k, t in enumerate(TOUTES[:10], start=1):
            offre_k = -e["offre_long_terme"] * 0.2 * (1 - (1 - e["vitesse_offre"]) ** k)
            out[k] = {"demande": rep["dpib"][t] / y[max(t, 2029)] * 100, "offre": offre_k, "prix": float("nan")}
            out[k]["pib"] = out[k]["demande"] + offre_k
        return out
    elif nom == "cotisations_employeurs":
        m = [Mesure("Cotisations employeurs", "recettes", {t: -v for t, v in un.items()}, instrument="cout_travail")]
    else:
        raise ValueError(nom)
    rep = bouclage.reponse(p, s, offre.impulsion(p, m, TOUTES), TOUTES, m)
    of = offre.effets(p, s, m)
    out = {}
    for k, t in enumerate(TOUTES[:10], start=1):
        out[k] = {"demande": rep["dpib"][t] / y[max(t, 2029)] * 100, "offre": of["dpib"][t] / y[max(t, 2029)] * 100,
                  "prix": rep["prix"][t] * 100}
        out[k]["pib"] = out[k]["demande"] + out[k]["offre"]
    return out


def banc(p: Parametres | None = None) -> dict:
    p = (p or Parametres()).avec({"macro.bouclage": True, "bouclage.bce/active": False})
    p.__dict__.pop("_cache", None)
    return {nom: variante(p, nom) for nom in MESANGE}


if __name__ == "__main__":
    r = banc()
    for nom, cible in MESANGE.items():
        print(f"\n{nom}")
        print("  années        " + "".join(f"{a:>8}" for a in ANS))
        print("  PIB moteur    " + "".join(f"{r[nom][a]['pib']:8.2f}" for a in ANS))
        print("    demande     " + "".join(f"{r[nom][a]['demande']:8.2f}" for a in ANS))
        print("    offre       " + "".join(f"{r[nom][a]['offre']:8.2f}" for a in ANS))
        print("  PIB Mésange   " + "".join(f"{v:8.2f}" for v in cible))
        print("  écart relatif " + "".join(f"{(r[nom][a]['pib'] - c) / abs(c) * 100:7.0f}%" for a, c in zip(ANS, cible)))
        print("  prix moteur   " + "".join(f"{r[nom][a]['prix']:8.2f}" for a in ANS))
        print("  prix Mésange  " + "".join(f"{v:8.2f}" for v in PRIX_MESANGE[nom]))
