"""Calage de la forme réduite du bouclage macro (phase E, 14/11/2026) sur les variantes de Mésange 2017.

Forme réduite annuelle, en écart au compte central (moteur/bouclage.py) :
    x_t = a·g_t + b·x_{t-1} − c·q_{t-1} − σ·r_{t-1}      écart de production (% du PIB)
    π_t = λ·π_{t-1} + κ·x_t                               inflation en plus (points)
    q_t = q_{t-1} + π_t                                    niveau des prix relatif à l'étranger (compétitivité-prix)
g : impulsion de demande permanente (points de PIB), r : taux réel en plus (points).

Cibles (Bardaji et al., Insee G2017/04, variantes à taux réels et change nominal constants, r = 0) :
- dépense publique générique de 1 point de PIB (p. 105) : PIB 0,78 / 1,06 / 1,03 / 0,86 / 0,53 à 1, 2, 3, 5 et
  10 ans ; prix de consommation 0,20 / 0,58 / 0,94 / 1,42 / 1,88 ;
- hausse permanente de 100 points de base des taux réels (p. 134) : PIB −0,17 / −0,60 / −0,78 / −1,00 à 1, 2, 3 et
  5 ans (la suite, −1,52 à 10 ans, est surtout l'effet d'offre du coût du capital, compté par le canal d'offre).

Usage : python -m outils.calibrer_bouclage (imprime les paramètres à reporter dans parametres/commun/economie.yaml).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares

ANS = (1, 2, 3, 5, 10)
PIB_DEP = (0.78, 1.06, 1.03, 0.86, 0.53)
PRIX_DEP = (0.20, 0.58, 0.94, 1.42, 1.88)
ANS_TAUX = (1, 2, 3, 5)
PIB_TAUX = (-0.17, -0.60, -0.78, -1.00)


def simuler(a, b, c, k, lam, sig, g=0.0, r=0.0, n=10):
    x = pi = q = 0.0
    xs, qs = [], []
    for _ in range(n):
        x = a * g + b * x - c * q - sig * r
        pi = lam * pi + k * x
        q += pi
        xs.append(x)
        qs.append(q)
    return xs, qs


def ecarts(v):
    a, b, c, k, lam, sig = v
    xs, qs = simuler(a, b, c, k, lam, sig, g=1.0)
    e = [xs[t - 1] - y for t, y in zip(ANS, PIB_DEP)] + [qs[t - 1] - y for t, y in zip(ANS, PRIX_DEP)]
    xr, _ = simuler(a, b, c, k, lam, sig, r=1.0, n=5)
    e += [xr[t - 1] - y for t, y in zip(ANS_TAUX, PIB_TAUX)]
    return np.array(e)


def caler():
    r = least_squares(ecarts, x0=[0.8, 0.4, 0.1, 0.25, 0.3, 0.3],
                      bounds=([0, 0, 0, 0, 0, 0], [2, 0.95, 1, 1, 0.95, 2]))
    return r.x


if __name__ == "__main__":
    a, b, c, k, lam, sig = caler()
    print(f"a={a:.4f} b={b:.4f} c={c:.4f} kappa={k:.4f} lambda={lam:.4f} sigma={sig:.4f}")
    xs, qs = simuler(a, b, c, k, lam, sig, g=1.0, n=30)
    print("dépense : PIB ", [round(xs[t - 1], 2) for t in ANS], "cible", PIB_DEP)
    print("dépense : prix", [round(qs[t - 1], 2) for t in ANS], "cible", PRIX_DEP)
    print("dépense : PIB à 15, 20, 30 ans", [round(xs[t - 1], 2) for t in (15, 20, 30)])
    xr, _ = simuler(a, b, c, k, lam, sig, r=1.0, n=10)
    print("taux    : PIB ", [round(xr[t - 1], 2) for t in ANS_TAUX], "cible", PIB_TAUX)
