"""Impôts des entreprises de la population synthétique, et mesures des programmes (phase G, premier lot).

Chaque entreprise paie, selon une législation (dict) :
- l'IS : taux réduit (15 %) sur les premiers 42 500 € de bénéfice si le chiffre d'affaires est sous 10 M€, taux normal
  (25 %) au-delà ; la condition de détention du capital n'est pas modélisée ;
- la C3S : 0,16 % du chiffre d'affaires au-delà de 19 M€ ;
- la CVAE : barème légal par chiffre d'affaires (CGI, art. 1586 quater), taux maximal de la législation, sur la VA
  plafonnée à 80 % du CA (85 % au-delà de 7,6 M€) ;
- la CFE et la taxe foncière : au prorata du capital (part industrielle : secteur industrie).
Les impôts de production sont déductibles du bénéfice : un impôt en moins augmente le résultat fiscal d'autant,
donc l'IS (effet « retour » montré à part).

Niveaux : chaque impôt de la législation actuelle est ramené à son total national
(microsimulation.entreprises_impots) ; le même facteur s'applique à la réforme. La population donne la répartition,
les comptes donnent le niveau. Montants en Md€ de l'année des sources (2023-2024).

Usage : python -m outils.entreprises_mesures  (écrit sorties/micro_entreprises.csv)
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import yaml

from moteur.parametres import Parametres

from . import population_entreprises as pe

RACINE = Path(__file__).resolve().parents[1]

ACTUELLE = {"is_normal": 0.25, "is_reduit": 0.15, "seuil_reduit": 42500.0, "ca_max_reduit": 10e6,
            "c3s_taux": 0.0016, "c3s_abattement": 19e6, "cvae_taux_max": 0.0, "cfe": 1.0, "cfe_industrie": 1.0,
            "taxe_fonciere": 1.0, "taxe_fonciere_industrie": 1.0, "taux_minimal": 0.0, "taux_minimal_ca": 1e9}
"""Législation du statu quo à partir de 2030 (CVAE supprimée) : base de comparaison des mesures."""


def cvae_taux(ca: np.ndarray, taux_max: float) -> np.ndarray:
    """Taux effectif de CVAE par chiffre d'affaires (barème de 1,5 %, ramené au taux maximal)."""
    t = np.select([ca < 5e5, ca < 3e6, ca < 1e7, ca < 5e7],
                  [0.0, 0.005 * (ca - 5e5) / 2.5e6, 0.005 + 0.009 * (ca - 3e6) / 7e6, 0.014 + 0.001 * (ca - 1e7) / 4e7],
                  0.015)
    return t * taux_max / 0.015


class Base:
    """Population d'entreprises et facteurs de niveau, calculés une fois sur la législation actuelle."""

    def __init__(self, pop: list[dict] | None = None):
        self.pop = pop or pe.generer()
        g = lambda k: np.array([e[k] for e in self.pop], dtype=float)  # noqa: E731
        self.w, self.w_is = g("poids"), g("poids") * g("part_is")
        self.eligible = 1.0
        self.ca, self.va, self.capital, self.r0 = g("ca"), g("va"), g("capital"), g("resultat_fiscal")
        self.industrie = np.array([e["secteur"] == "industrie" for e in self.pop])
        self.taille = np.array([e["taille"] for e in self.pop])
        t = Parametres().val("microsimulation.entreprises_impots")
        # niveaux nationaux de chaque impôt, contre la population brute
        brut = self._bruts(ACTUELLE)
        cap = self.w @ self.capital
        cfe_tf = (t["cfe"] + t["taxe_fonciere"]) * (1 - t["part_financier_capital"]) * 1e9
        self.k = {"c3s": t["c3s"] * 1e9 / (self.w @ brut["c3s"]),
                  "cfe": cfe_tf * t["cfe"] / (t["cfe"] + t["taxe_fonciere"]) / cap,
                  "taxe_fonciere": cfe_tf * t["taxe_fonciere"] / (t["cfe"] + t["taxe_fonciere"]) / cap,
                  "cvae": t["cvae_taux_075"] * 1e9 / (self.w @ (cvae_taux(self.ca, 0.0075) * np.minimum(self.va, 0.8 * self.ca)))}
        # part éligible au taux réduit (détention du capital) : base au taux réduit de 2022 (Insee, DGFiP)
        tr = Parametres().val("microsimulation.entreprises_base_taux_reduit")
        self.eligible = 1.0
        self.k["is"] = 1.0
        for _ in range(20):
            k_base = self.k["is"]
            base22 = self.w_is @ np.where(self.ca < 10e6, np.clip(self.r0, 0, tr["seuil"]), 0.0)
            self.eligible = min(1.0, tr["benefice_md"] * 1e9 / (base22 * k_base))
            k_new = t["is"] * 1e9 / (self.w_is @ (self.impots(ACTUELLE)["is"] / self.k["is"]))
            self.k["is"] = k_new
            if abs(k_new / k_base - 1) < 1e-6:
                break

    def _bruts(self, leg: dict) -> dict:
        va_plaf = np.minimum(self.va, np.where(self.ca > 7.6e6, 0.85, 0.8) * self.ca)
        return {"c3s": leg["c3s_taux"] * np.maximum(0.0, self.ca - leg["c3s_abattement"]),
                "cvae": cvae_taux(self.ca, leg["cvae_taux_max"]) * np.maximum(va_plaf, 0.0),
                "cfe": self.capital * np.where(self.industrie, leg["cfe_industrie"], leg["cfe"]),
                "taxe_fonciere": self.capital * np.where(self.industrie, leg["taxe_fonciere_industrie"], leg["taxe_fonciere"])}

    def impots(self, leg: dict) -> dict:
        """Impôts de chaque entreprise (€, niveaux nationaux) ; l'IS tient compte des impôts de production déductibles."""
        b = self._bruts(leg)
        prod = {k: v * self.k.get(k, 1.0) for k, v in b.items()}
        b0 = self._bruts(ACTUELLE)
        prod0 = {k: v * self.k.get(k, 1.0) for k, v in b0.items()}
        # impôts de production payés par les entreprises à l'IS : déductibles
        delta = sum(prod0[k] - prod[k] for k in prod)
        r = self.r0 + delta
        reduit = self.ca < leg["ca_max_reduit"]
        base_r = np.where(reduit, np.clip(r, 0, leg["seuil_reduit"]), 0.0) * self.eligible
        is_ = leg["is_reduit"] * base_r + leg["is_normal"] * np.maximum(0.0, r - base_r)
        is_ = np.maximum(is_, leg["taux_minimal"] * np.maximum(r, 0) * (self.ca >= leg["taux_minimal_ca"]))
        return {"is": is_ * self.k.get("is", 1.0), **prod}

    def totaux(self, leg: dict) -> dict:
        x = self.impots(leg)
        out = {"is": float(self.w_is @ x["is"]) / 1e9}
        for k in ("c3s", "cvae", "cfe", "taxe_fonciere"):
            out[k] = float(self.w @ x[k]) / 1e9
        return out

    def reforme(self, changements: dict) -> dict:
        """Effet d'une réforme sur les recettes (Md€, + = recette en plus), impôt par impôt, et part de l'IS."""
        leg = {**ACTUELLE, **changements}
        a, b = self.totaux(ACTUELLE), self.totaux(leg)
        d = {k: b[k] - a[k] for k in a}
        d["total"] = sum(d.values())
        par_taille = {}
        xa, xb = self.impots(ACTUELLE), self.impots(leg)
        for t in ("MIC", "PME", "GE_ETI"):
            m = self.taille == t
            par_taille[t] = float(sum((self.w_is if k == "is" else self.w)[m] @ (xb[k][m] - xa[k][m]) for k in xa)) / 1e9
        d["par_taille"] = par_taille
        return d


def specs() -> dict:
    return yaml.safe_load((RACINE / "programmes" / "micro_entreprises.yaml").read_text(encoding="utf-8"))


def montant_moteur(prog: str, ident: str, filtre: str | None = None, s: str = "prudent") -> float:
    """Effet sur le solde dans le moteur (Md€ de 2026) des lignes de cet identifiant, filtrées par libellé."""
    p = Parametres(programme=prog)
    tot = 0.0
    for cle, par in p.items():
        x = par.valeur
        if not cle.startswith(f"{prog}_mesures.") or not isinstance(x, dict) or x.get("id") != ident:
            continue
        if filtre and filtre not in x.get("libelle", ""):
            continue
        m = x["montant"][s] if isinstance(x["montant"], dict) else x["montant"]
        tot += m if x["poste"] == "recettes" else -m
    return tot


def main() -> None:
    base = Base()
    print("Législation actuelle (2030, CVAE supprimée), Md€ :", {k: round(v, 2) for k, v in base.totaux(ACTUELLE).items()})
    lignes = []
    for prog, mesures in specs().items():
        for ident, spec in mesures.items():
            r = base.reforme(spec["changements"])
            mot = montant_moteur(prog, ident, spec.get("moteur_filtre"))
            # le moteur chiffre les impôts de production en brut et ajoute le retour d'IS à part (deductible_is)
            prod = not any(k.startswith(("is_", "seuil_", "ca_max", "taux_minimal")) for k in spec["changements"])
            comparable = r["total"] - r["is"] if prod else r["total"]
            lignes.append({"programme": prog, "mesure": ident, "micro_md": round(r["total"], 2),
                           "micro_comparable_md": round(comparable, 2), "moteur_md": round(mot, 2),
                           "ecart_pct": round((comparable / mot - 1) * 100) if abs(mot) > 0.05 else "",
                           **{f"d_{k}": round(r[k], 2) for k in ("is", "c3s", "cvae", "cfe", "taxe_fonciere")},
                           **{f"taille_{k}": round(v, 2) for k, v in r["par_taille"].items()},
                           "note": spec.get("note", "")})
            print(f"{prog:10s} {ident:12s} micro {r['total']:+7.2f} (brut {comparable:+7.2f})  moteur {mot:+7.2f}  (IS {r['is']:+.2f})")
    with (RACINE / "sorties" / "micro_entreprises.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    from outils import trace
    trace.enregistrer("micro_entreprises.csv", script="outils.entreprises_mesures")


if __name__ == "__main__":
    main()
