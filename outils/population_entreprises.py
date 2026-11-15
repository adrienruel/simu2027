"""Population synthétique d'entreprises (phase F, étape 4 : premier jet).

Une entreprise synthétique par ligne, avec un poids, pour 6 secteurs × 3 tailles (Insee, Ésane 2023, champ
marchand non agricole et non financier : parametres/donnees/entreprises_secteurs_tailles.csv). Chaque cellule
reproduit exactement les totaux d'Ésane : nombre d'entreprises, emploi en EQTP, valeur ajoutée, frais de
personnel, EBE et investissement. À l'intérieur d'une cellule, la taille suit une loi log-normale (dispersion :
décision écrite, microsimulation.yaml, entreprises.dispersion) et la VA, l'EBE et l'investissement suivent la
taille avec un bruit propre, puis sont recalés sur le total de la cellule.

Impôt sur les sociétés. Une part des entreprises est à l'IS (les autres sont des entreprises individuelles ou des
micro-entrepreneurs à l'IR) : part des MIC = TPE à l'IS (DGFiP) / MIC d'Ésane, uniforme par secteur (décision).
Le résultat fiscal de chaque entreprise à l'IS est tiré par rang : on classe les entreprises par EBE (avec un
bruit, la rentabilité variant à taille égale), puis on leur attribue les quantiles de la distribution des
bénéfices de la DGFiP (parametres/donnees/entreprises.csv, 16 classes) et des pertes. La distribution des
bénéfices est donc exacte par construction ; le contrôle porte sur l'IS par taille (DGFiP 2024,
entreprises_tailles.csv), que le module ne cale pas.

Usage : python -m outils.population_entreprises  (écrit parametres/donnees/population_entreprises_2023.csv)
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
DONNEES = RACINE / "parametres" / "donnees"

TAILLES_DGFIP = {"MIC": "TPE", "PME": "PME", "GE_ETI": ("ETI", "GE")}


def _lire(nom: str) -> list[dict]:
    with (DONNEES / nom).open(encoding="utf-8") as f:
        return [{k: (v if k in ("secteur", "taille", "classe", "libelle") else float(v)) for k, v in l.items()}
                for l in csv.DictReader(f)]


def _bornes(classe: str) -> tuple[float, float]:
    """« 42,5–75 k€ » -> (42 500, 75 000) ; « 500 k€–1 M€ » -> (5e5, 1e6) ; « >500 M€ » -> (5e8, inf)."""
    def val(x, defaut):
        x = x.strip().replace(",", ".").replace(" ", "")
        unite = 1e6 if "M€" in x else (1e3 if "k€" in x else defaut)
        return float(x.replace("M€", "").replace("k€", "")), unite
    c = classe.strip()
    if c.startswith(">"):
        v, u = val(c[1:], 1.0)
        return v * u, np.inf
    a, b = c.split("–")
    vb, ub = val(b, 1.0)
    va, ua = val(a, ub)
    return va * ua, vb * ub


def _quantiles_benefices(n_benef: float) -> tuple[np.ndarray, np.ndarray]:
    """Fonction de répartition des bénéfices des entreprises bénéficiaires (classes de la DGFiP, uniforme en log
    dans chaque classe ; la première classe est uniforme en niveau) : renvoie (probabilités cumulées, bénéfices)."""
    ent = _lire("entreprises.csv")
    tot = sum(e["entreprises_beneficiaires"] for e in ent)
    p, b, cum = [0.0], [0.0], 0.0
    for e in ent:
        lo, hi = _bornes(e["classe"])
        if not np.isfinite(hi):
            hi = 2 * e["benefice_median"] - lo if e["benefice_median"] > lo else lo * 4
        cum += e["entreprises_beneficiaires"] / tot
        p.append(cum)
        b.append(hi)
    return np.array(p), np.array(b)


def _benefice(u: np.ndarray, p: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Bénéfice au quantile u : interpolation log-linéaire entre bornes de classes (linéaire dans la première)."""
    i = np.clip(np.searchsorted(p, u, side="right") - 1, 0, len(p) - 2)
    t = (u - p[i]) / (p[i + 1] - p[i])
    lo, hi = b[i], b[i + 1]
    out = np.where(lo <= 0, hi * t, np.exp(np.log(np.maximum(lo, 1)) + t * (np.log(hi) - np.log(np.maximum(lo, 1)))))
    return out


def generer(n_par_cellule: dict | None = None, graine: int = 2027,
            dispersion: dict | None = None, bruit_rentabilite: float = 0.8, caler: bool = True) -> list[dict]:
    """Une liste d'entreprises synthétiques (dict par entreprise). caler : décale le rang des MIC et des PME
    pour que les bénéfices par taille rejoignent ceux de la DGFiP (les GE et ETI servent de référence)."""
    from moteur.parametres import Parametres
    p_ = Parametres()
    rng = np.random.default_rng(graine)
    n_par_cellule = n_par_cellule or {"MIC": 1500, "PME": 1000, "GE_ETI": 400}
    d_ = p_.val("microsimulation.entreprises_dispersion")
    dispersion = dispersion or {t: d_[t] for t in ("MIC", "PME", "GE_ETI")}
    capital_etp = p_.val("microsimulation.entreprises_capital_par_etp")
    inv_taille = {t: sum(c["investissement_m"] for c in _lire("entreprises_secteurs_tailles.csv") if c["taille"] == t)
                  for t in ("MIC", "PME", "GE_ETI")}
    etp_taille = {t: sum(c["etp"] for c in _lire("entreprises_secteurs_tailles.csv") if c["taille"] == t)
                  for t in ("MIC", "PME", "GE_ETI")}
    cellules = _lire("entreprises_secteurs_tailles.csv")
    tailles = {t["taille"]: t for t in _lire("entreprises_tailles.csv")}
    sortie = []
    for c in cellules:
        t = c["taille"]
        n = n_par_cellule[t]
        w = np.full(n, c["entreprises"] / n)
        s = dispersion[t]
        # emploi : log-normale de moyenne la moyenne de la cellule
        x = rng.lognormal(-s * s / 2, s, n)
        etp = x / (w @ x) * c["etp"]
        # VA, frais de personnel, investissement : suivent l'emploi avec un bruit propre, puis recalage
        def suit(total, bruit):
            v = etp * rng.lognormal(-bruit * bruit / 2, bruit, n)
            return v / (w @ v) * total * 1e6
        va = suit(c["va_m"], 0.35)
        ca = va * rng.lognormal(-0.18, 0.6, n)
        ca = ca / (w @ ca) * c["ca_m"] * 1e6
        # capital : capital par EQTP de la taille (Insee), réparti entre secteurs selon l'investissement
        fp = suit(c["frais_personnel_m"], 0.2)
        inv = suit(c["investissement_m"], 0.9)
        capital = inv / (w @ inv) * capital_etp[t] * 1e3 * etp_taille[t] * c["investissement_m"] / inv_taille[t]
        ebe_brut = va - fp
        # EBE : recalé sur Ésane (l'écart VA - FP - EBE = impôts de production nets des subventions)
        ip = (w @ ebe_brut - c["ebe_m"] * 1e6) / (w @ va) * va
        ebe = ebe_brut - ip
        for i in range(n):
            sortie.append({"secteur": c["secteur"], "taille": t, "poids": w[i], "etp": etp[i], "va": va[i],
                           "frais_personnel": fp[i], "ca": ca[i], "capital": capital[i], "impots_production_nets": ip[i], "ebe": ebe[i],
                           "investissement": inv[i]})
    # part à l'IS
    mic_insee = sum(c["entreprises"] for c in cellules if c["taille"] == "MIC")
    part_is = {"MIC": min(1.0, tailles["TPE"]["entreprises_is"] / mic_insee), "PME": 1.0, "GE_ETI": 1.0}
    for e in sortie:
        e["part_is"] = part_is[e["taille"]]
    # résultat fiscal par rang (entreprises à l'IS, pondérées par poids × part_is)
    ent = _lire("entreprises.csv")
    defi = _lire("entreprises_deficitaires.csv")
    n_benef = sum(e["entreprises_beneficiaires"] for e in ent)
    n_is = sum(e["poids"] * e["part_is"] for e in sortie)
    part_benef = min(1.0, n_benef / n_is)
    bruit = rng.normal(0, bruit_rentabilite, len(sortie))
    base_score = np.array([np.log(max(e["ebe"], 1.0)) for e in sortie]) + bruit
    poids = np.array([e["poids"] * e["part_is"] for e in sortie])
    taille = np.array([e["taille"] for e in sortie])
    etp = np.array([e["etp"] for e in sortie])
    p, b = _quantiles_benefices(n_benef)
    perte_moy = sum(d["effectif"] * d["perte_mediane"] for d in defi) / sum(d["effectif"] for d in defi)
    seuil = 1 - part_benef
    tailles_dg = {t["taille"]: t for t in tailles.values()}
    cible = {"MIC": tailles_dg["TPE"]["benefices_md"], "PME": tailles_dg["PME"]["benefices_md"]}

    def attribuer(decal):
        score = base_score + np.select([taille == "MIC", taille == "PME"], [decal["MIC"], decal["PME"]], 0.0)
        ordre = np.argsort(score)
        cum = np.cumsum(poids[ordre]) / poids.sum()
        rang = np.empty(len(score))
        rang[ordre] = cum - poids[ordre] / poids.sum() / 2
        u = np.clip((rang - seuil) / (1 - seuil), 0, 1)
        res = np.where(rang < seuil, -perte_moy * 2 * (1 - rang / seuil), _benefice(u, p, b))
        return res

    decal = {"MIC": 0.0, "PME": 0.0}
    res = attribuer(decal)
    if caler:
        for _ in range(60):
            ecart = 0.0
            for t in ("MIC", "PME"):
                m = taille == t
                tot = poids[m] @ np.maximum(res[m], 0) / 1e9
                decal[t] += 0.8 * np.log(cible[t] / tot)
                ecart = max(ecart, abs(tot / cible[t] - 1))
            res = attribuer(decal)
            if ecart < 0.002:
                break
    for i, e in enumerate(sortie):
        e["resultat_fiscal"] = float(res[i])
    generer.decalage = decal
    return sortie


def is_brut(resultat: float, taux_reduit: float = 0.15, seuil: float = 42500.0, taux: float = 0.25) -> float:
    """IS 2023-2026 : 15 % jusqu'à 42 500 € pour les PME éligibles, 25 % au-delà (taux réduit appliqué à tous les
    bénéficiaires sous le seuil : simplification, documentée)."""
    if resultat <= 0:
        return 0.0
    return taux_reduit * min(resultat, seuil) + taux * max(0.0, resultat - seuil)


def controler(pop: list[dict]) -> dict:
    """Totaux par taille contre la DGFiP : nombre d'entreprises à l'IS, résultat fiscal positif, IS brut (Md€)."""
    tailles = {t["taille"]: t for t in _lire("entreprises_tailles.csv")}
    res = {}
    for t, dg in (("MIC", ["TPE"]), ("PME", ["PME"]), ("GE_ETI", ["ETI", "GE"])):
        sel = [e for e in pop if e["taille"] == t]
        w = np.array([e["poids"] * e["part_is"] for e in sel])
        r = np.array([e["resultat_fiscal"] for e in sel])
        imp = np.array([is_brut(x, 0.15 if t != "GE_ETI" else 0.0) for x in r])
        res[t] = {"entreprises_is": float(w.sum()), "entreprises_is_dgfip": sum(tailles[d]["entreprises_is"] for d in dg),
                  "benefices_md": float(w @ np.maximum(r, 0)) / 1e9,
                  "benefices_md_dgfip": sum(tailles[d]["benefices_md"] for d in dg),
                  "is_brut_md": float(w @ imp) / 1e9, "is_brut_md_dgfip": sum(tailles[d]["is_brut_md"] for d in dg)}
    return res


def ecrire(pop: list[dict], nom: str = "population_entreprises_2023.csv") -> None:
    with (DONNEES / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pop[0]))
        w.writeheader()
        for e in pop:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in e.items()})


if __name__ == "__main__":
    pop = generer()
    ecrire(pop)
    for t, v in controler(pop).items():
        print(t, {k: round(x, 1) for k, x in v.items()})
