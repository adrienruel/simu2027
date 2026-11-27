"""Roadmap 6.2 (22/11/2026) : corrélation historique entre les tendances de la productivité et de l'emploi.

Données : Insee, comptes nationaux annuels base 2020 (fichiers fournis par Adrien, parametres/sources/insee_cn2025/) :
PIB en volume (tableau 1.102, B1GQ) et emploi intérieur total en personnes (tableau 1.108, S1), 1978-2025.
Productivité par tête = croissance du PIB − croissance de l'emploi (en logarithmes).

Le Monte Carlo tire un « climat » commun à tous les paramètres (incertitude.correlation, bornes ρ = 0 et ρ = 1). La
question est de savoir si les tendances de la productivité et de l'emploi sont bonnes ou mauvaises ensemble. On mesure
la corrélation des moyennes sur 5 et 10 ans (glissantes et disjointes), et des taux annuels hors 2020-2021.

Roadmap du moteur R4.3 (27/11/2026) : taux. OAT à 10 ans, moyenne annuelle (OCDE, Main Economic Indicators, série
IRLTLT01FRA156N reprise par la Fed de Saint-Louis, parametres/donnees/oat10_annuel_ocde.csv) ; taux réel = OAT − hausse du
déflateur du PIB (Insee, T_1101 / T_1102). Même mesure de corrélation avec la productivité et l'emploi.

    python -m outils.correlations_historiques
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
SOURCES = RACINE / "parametres" / "sources" / "insee_cn2025"
OAT = RACINE / "parametres" / "donnees" / "oat10_annuel_ocde.csv"


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


def taux_reel(ans: list[int]) -> np.ndarray:
    """OAT à 10 ans moins la hausse du déflateur du PIB (en logarithme), année par année."""
    import csv
    val = _ligne(SOURCES / "T_1101_1103.xlsx", "T_1101 en niveau", "B1GQ")
    vol = _ligne(SOURCES / "T_1101_1103.xlsx", "T_1102 en niveau", "B1GQ")
    with open(OAT, encoding="utf-8") as f:
        oat = {int(r["annee"]): float(r["oat10_pct"]) / 100 for r in csv.DictReader(f)}
    return np.array([oat[a] - np.log((val[a] / vol[a]) / (val[a - 1] / vol[a - 1])) for a in ans])


def _mesures(ans: list[int], x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    m = np.array([a not in (2020, 2021) for a in ans])
    out = {"annuel_hors_2020_2021": float(np.corrcoef(x[m], y[m])[0, 1])}
    for w in (5, 10):
        X = np.array([x[i:i + w].mean() for i in range(len(x) - w + 1)])
        Y = np.array([y[i:i + w].mean() for i in range(len(y) - w + 1)])
        out[f"glissant_{w}_ans"] = float(np.corrcoef(X, Y)[0, 1])
        k = len(x) // w
        X2, Y2 = x[len(x) - k * w:].reshape(k, w).mean(1), y[len(y) - k * w:].reshape(k, w).mean(1)
        out[f"disjoint_{w}_ans"] = float(np.corrcoef(X2, Y2)[0, 1])
    if w == 10:  # moyennes sur 5 ans glissantes, hors tendance linéaire commune (la baisse des taux et de la productivité)
        X = np.array([x[i:i + 5].mean() for i in range(len(x) - 4)])
        Y = np.array([y[i:i + 5].mean() for i in range(len(y) - 4)])
        t = np.arange(len(X))
        out["glissant_5_ans_hors_tendance"] = float(np.corrcoef(X - np.polyval(np.polyfit(t, X, 1), t),
                                                                Y - np.polyval(np.polyfit(t, Y, 1), t))[0, 1])
    return out


def correlations() -> dict[str, dict[str, float]]:
    """Corrélations historiques, par paire. Signe des grandeurs, pas de leur côté « favorable » : un taux élevé est
    défavorable au solde, une productivité élevée favorable ; une corrélation positive entre les deux veut donc dire
    qu'ils se compensent."""
    ans, pr, n = series()
    rr = taux_reel(ans)
    return {"productivite_emploi": _mesures(ans, pr, n), "taux_reel_productivite": _mesures(ans, rr, pr),
            "taux_reel_emploi": _mesures(ans, rr, n)}


if __name__ == "__main__":
    for paire, d in correlations().items():
        print(paire)
        for k, v in d.items():
            print(f"  {k:30s} {v:+.2f}")
