"""Roadmap 6.2 (22/11/2026) : corrélation historique entre les tendances de la productivité et de l'emploi.

Données : Insee, comptes nationaux annuels base 2020 (fichiers fournis par Adrien, parametres/sources/insee_cn2025/) :
PIB en volume (tableau 1.102, B1GQ) et emploi intérieur total en personnes (tableau 1.108, S1), 1978-2025.
Productivité par tête = croissance du PIB − croissance de l'emploi (en logarithmes).

Le Monte Carlo tire un « climat » commun à tous les paramètres (incertitude.correlation, bornes ρ = 0 et ρ = 1). La
question est de savoir si les tendances de la productivité et de l'emploi sont bonnes ou mauvaises ensemble. On mesure
la corrélation des moyennes sur 5 et 10 ans (glissantes et disjointes), et des taux annuels hors 2020-2021.

    python -m outils.correlations_historiques
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
SOURCES = RACINE / "parametres" / "sources" / "insee_cn2025"


def _ligne(fichier: Path, onglet: str, code: str) -> dict[int, float]:
    import openpyxl
    ws = openpyxl.load_workbook(fichier, read_only=True, data_only=True)[onglet]
    rows = list(ws.iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[2] and str(r[2]).isdigit())
    for r in rows:
        if r and r[0] == code:
            return {int(h): float(v) for h, v in zip(hdr[2:], r[2:]) if v is not None}
    raise KeyError(code)


def series() -> tuple[list[int], np.ndarray, np.ndarray]:
    pib = _ligne(SOURCES / "T_1101_1103.xlsx", "T_1102 en niveau", "B1GQ")
    emp = _ligne(SOURCES / "T_1108.xlsx", "T_1108 en niveau", "S1")
    ans = sorted(set(pib) & set(emp))
    g = np.array([np.log(pib[a] / pib[a - 1]) for a in ans[1:]])
    n = np.array([np.log(emp[a] / emp[a - 1]) for a in ans[1:]])
    return ans[1:], g - n, n


def correlations() -> dict[str, float]:
    ans, pr, n = series()
    m = np.array([a not in (2020, 2021) for a in ans])
    out = {"annuel_hors_2020_2021": float(np.corrcoef(pr[m], n[m])[0, 1])}
    for w in (5, 10):
        P = np.array([pr[i:i + w].mean() for i in range(len(pr) - w + 1)])
        N = np.array([n[i:i + w].mean() for i in range(len(n) - w + 1)])
        out[f"glissant_{w}_ans"] = float(np.corrcoef(P, N)[0, 1])
        k = len(pr) // w
        P2, N2 = pr[len(pr) - k * w:].reshape(k, w).mean(1), n[len(n) - k * w:].reshape(k, w).mean(1)
        out[f"disjoint_{w}_ans"] = float(np.corrcoef(P2, N2)[0, 1])
    return out


if __name__ == "__main__":
    for k, v in correlations().items():
        print(f"{k:24s} {v:+.2f}")
