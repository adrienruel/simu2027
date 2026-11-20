"""Plancher du chômage commun à tous les programmes (13/11/2026) : un programme ne descend jamais sous le chômage
incompressible (emploi.chomage_incompressible), avec un raccord continu au-dessus d'une marge."""
from __future__ import annotations

import math

from .parametres import Parametres

__all__ = ["plancher_chomage"]


def plancher_chomage(p: Parametres, ctx: dict, valeur_emploi: dict[int, float],
                     exclus: tuple[str, ...] = ("Démographie",)) -> dict[int, float]:
    """Chômage d'un programme ramené au-dessus du plancher incompressible (13/11/2026), commun à tous les programmes.

    Au-dessus de plancher + marge, rien ne change. En dessous, le chômage suit u* = plancher + marge × exp((u − plancher
    − marge) / marge) : même valeur et même pente au raccord, jamais sous le plancher. Les emplois en plus manquants
    (ΔN = (u* − u) × population active) sont retirés des canaux positifs au prorata (sauf démographie), de l'emploi
    et du PIB (valeur_emploi : Md€ par emploi et par an). Modifie ctx en place ; rend le facteur k appliqué aux
    canaux positifs, à appliquer aussi par l'appelant aux recettes de ses effets d'offre."""
    u_inc = p.val("emploi.chomage_incompressible") * 100
    b = p.val("emploi.marge_plancher") * 100
    k = {}
    for t, u in ctx["chomage"].items():
        k[t] = 1.0
        if u >= u_inc + b:
            continue
        u_star = u_inc + b * math.exp((u - u_inc - b) / b)
        actifs = ctx["emploi"][t] / (1 - u / 100)
        dn = (u_star - u) / 100 * actifs
        canaux = ctx["emplois_canaux"][t]
        pos = sum(v for c, v in canaux.items() if v > 0 and not c.startswith(exclus))
        if pos <= 0:
            continue
        dn = min(dn, pos)
        k[t] = 1 - dn / pos
        for c, v in canaux.items():
            if v > 0 and not c.startswith(exclus):
                canaux[c] = v * k[t]
        ctx["chomage"][t] = u + dn / actifs * 100
        ctx["emploi"][t] -= dn
        ctx["pib"][t] -= dn * valeur_emploi[t]
    return k
