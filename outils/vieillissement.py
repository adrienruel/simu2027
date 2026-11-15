"""Vieillissement statique de la population synthétique (phase F4, 14/11/2026, décision d'Adrien).

Pour des années clés et pour chaque programme, les poids des ménages de 2026 sont recalés (ratissage, à partir des
poids de 2026) sur les marges que donne le moteur pour ce programme cette année-là :
- population par âge : population du programme (projection de l'Insee, naissances et immigration du programme,
  migrations.population_programme), hors ménages ordinaires comme en 2026 ;
- personnes en emploi (trajectoire du programme), réparties entre privé, public et indépendants comme en 2026 ;
  chômeurs (taux de chômage du programme) ; retraités (série du COR, retraités totaux, rapportée à 2026) ;
- ménages : leur nombre suit la population adulte.

Revenus en unités de 2026 : le moteur fait suivre les salaires aux barèmes (statu quo à législation constante,
statu_quo.recettes_par_impot) ; garder les revenus et la législation de 2026 revient à la même convention, en euros
« de salaire » de 2026. OpenFisca calcule ensuite le système actuel et les mesures codées du programme.

Écrit sorties/micro_vieillissement.csv (budget des mesures codées, IR, CSG, pauvreté, Gini, rapport D9/D1) et
sorties/micro_vieillissement_deciles.csv.

    python -m outils.vieillissement lisnard      # un programme (statu_quo : le statu quo)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

from moteur import migrations, noyau
from moteur import statu_quo as sq
from moteur.parametres import Parametres
from outils import openfisca_mesures as om
from outils import openfisca_population as op
from outils.population_synthetique import _raking

RACINE = Path(__file__).resolve().parent.parent
ANNEES = (2029, 2032, 2037, 2050)
# mesures de recettes dont le profil dans le temps vient de la micro (moteur : microsimulation.recettes_vieillies)
RECETTES = ("BER-FIS-01", "REC-11", "REC-13", "LIS-SOC-01", "PCF-RET-03", "PHI-FIS-02", "RN-FIS-03", "REC-10",
            "BER-FIS-02")
BANDES = [(0, 2), (3, 5), (6, 10), (11, 14), (15, 17), (18, 19), (20, 24)] + [(a, a + 4) for a in range(25, 85, 5)] + [(85, 120)]


def _hors_menage(p, a):
    so = p.val("microsimulation.sortie_menages_ordinaires")
    return so["85+"] if a >= 85 else so["75-84"] if a >= 75 else so["autres"]


def recaler(lignes: list[dict], prog, p: Parametres, annee: int, traj: dict, emploi_ref: float,
            s: str = "prudent") -> list[dict]:
    """Lignes avec les poids recalés sur les marges du programme en `annee`."""
    unite = np.array([l["unite"] for l in lignes])
    n_u = int(unite.max()) + 1
    w0 = np.zeros(n_u)
    w0[unite] = [l["poids"] for l in lignes]
    age = np.array([l["age"] for l in lignes])
    statut = np.array([l["statut"] for l in lignes])
    pop = migrations.population_programme(prog, p, s)[annee]
    A, c = [], []
    for lo, hi in BANDES:
        A.append(np.bincount(unite, weights=((age >= lo) & (age <= hi)).astype(float), minlength=n_u))
        c.append(sum(pop[a] * (1 - _hors_menage(p, a)) for a in range(lo, min(hi, len(pop) - 1) + 1)))
    compte = lambda m: np.bincount(unite, weights=m.astype(float), minlength=n_u)  # noqa: E731
    pers0 = lambda m: float((w0 * compte(m)).sum())  # noqa: E731
    # emploi : évolution du moteur (programme, rapporté au statu quo de 2029, qui porte l'économie de 2026), appliquée
    # à l'emploi de la population de 2026 (définitions différentes : le moteur compte l'emploi par les taux par âge)
    e26 = {k: pers0(statut == k) for k in ("salarie_prive", "agent_public", "independant")}
    tot26 = sum(e26.values())
    emploi = tot26 * traj[annee]["emploi"] / emploi_ref
    for k, v in e26.items():
        A.append(compte(statut == k))
        c.append(emploi * v / tot26)
    u = traj[annee]["chomage"] / 100
    A.append(compte(statut == "chomeur"))
    c.append(emploi * u / (1 - u))
    cor = dict(zip(range(2029, 2074), p.val("anciennes_pensions.retraites_ancien_2029_millions")))
    A.append(compte(statut == "retraite"))
    c.append(pers0(statut == "retraite") * cor[annee] / cor[2029] * (1.012 ** 3 if annee >= 2029 else 1.0) / 1.012 ** 3)
    # ménages : suivent les adultes
    menages_u = np.bincount(unite, weights=np.array([1.0 if l["role"] == "ref" else 0.0 for l in lignes]), minlength=n_u)
    adultes = sum(pop[18:])
    adultes26 = pers0(age >= 18)
    A.append(menages_u)
    c.append(float((w0 * menages_u).sum()) * adultes * (1 - 0.01) / adultes26)
    w = _raking(np.array(A), np.array(c), w0, bornes=(0.25, 4.0))
    # pensions en unités de salaire : pension moyenne du moteur (bloc retraites / salaires / retraités du COR), qui
    # baisse quand les pensions suivent les prix et les salaires la productivité
    b, sal = sq.blocs(p, s), sq.salaires(p, s)
    r = lambda t: b[t]["retraites"] / sal[t] / cor[t]  # noqa: E731
    k_pen = r(annee) / r(2029)
    return [dict(l, poids=round(float(w[l["unite"]]), 3), pension_brute=l["pension_brute"] * k_pen) for l in lignes]


def indicateurs(base: om.Base, etat: dict) -> dict:
    nv = etat["rd"] / np.maximum(etat["uc"], 1e-9)
    champ = ~base.menage_etudiant  # champ de l'Insee
    w = (base.wm * base.pers_m)[champ]
    nv = nv[champ]
    o = np.argsort(nv)
    cw = np.cumsum(w[o]) / w.sum()
    q = lambda x: float(nv[o][np.searchsorted(cw, x)])  # noqa: E731
    med = q(0.5)
    xs, ws = nv[o], w[o]
    cum = np.cumsum(xs * ws) / (xs * ws).sum()
    gini = 1 - float(((np.concatenate([[0], cum[:-1]]) + cum) * ws).sum() / ws.sum())
    return {"pauvrete_pct": float(w[nv < 0.6 * med].sum() / w.sum() * 100), "gini": gini, "d9_d1": q(0.9) / q(0.1),
            "mediane": med, "ir_md": etat["comp"]["impot_revenu"], "csg_md": etat["comp"]["csg"]}


def main(noms):
    p = Parametres()
    specs = om.specs()
    lignes0 = op.lire()
    dossier = RACINE / "sorties" / "micro"
    dossier.mkdir(exist_ok=True)
    for arg in noms:
        # « programme » ou « programme:année » (une année par processus : limite la mémoire)
        nom, _, an = arg.partition(":")
        annees = (int(an),) if an else ANNEES
        prefixe = arg.replace(":", "_")
        prog = noyau.charger(nom)
        res = sq.simuler(p) if nom == "statu_quo" else noyau.simuler(p, prog, scenarios=("prudent",))
        traj = res["prudent"]
        emploi_ref = sq.simuler(p)["prudent"][2029]["emploi"]
        ops = [o for spec in specs.get(nom, {}).values() for o in spec["operations"]]
        out, dec, rec = [], [], []
        statique26 = {}
        if any(i in RECETTES for i in specs.get(nom, {})):
            base26 = om.Base(lignes0, emploi=False)
            for ident, spec in specs[nom].items():
                if ident in RECETTES:
                    statique26[ident] = base26.reforme(spec["operations"])["budget"]
            del base26
        for annee in annees:
            lg = recaler(lignes0, prog, p, annee, traj, emploi_ref)
            base = om.Base(lg, emploi=False)
            i0 = indicateurs(base, base.etat0)
            ligne = {"programme": nom, "annee": annee, **{f"{k}_sq": round(v, 3) for k, v in i0.items()}}
            if ops:
                r = base.reforme(ops)
                i1 = indicateurs(base, r["etat"])
                ligne.update({"budget_mesures_md": round(r["budget"], 2), **{k: round(v, 3) for k, v in i1.items()}})
                for d in base.deciles(r["etat"]):
                    dec.append({"programme": nom, "annee": annee, **{k: round(v, 2) if isinstance(v, float) else v
                                                                     for k, v in d.items()}})
            for ident, v26 in statique26.items():
                v = base.reforme(specs[nom][ident]["operations"])["budget"]
                rec.append({"programme": nom, "mesure": ident, "annee": annee, "statique_md": round(v, 3),
                            "indice": round(v / v26, 4) if abs(v26) > 1e-6 else 1.0})
            out.append(ligne)
            print(nom, annee, {k: v for k, v in ligne.items() if k not in ("programme", "annee")}, flush=True)
            del base
            import gc
            gc.collect()
        om._ecrire(dossier / f"{prefixe}_vieillissement.csv", out)
        if dec:
            om._ecrire(dossier / f"{prefixe}_vieillissement_deciles.csv", dec)
        if rec:
            om._ecrire(dossier / f"{prefixe}_vieillissement_recettes.csv", rec)
    reunir()


def reunir():
    dossier = RACINE / "sorties" / "micro"
    for suffixe, cible in (("vieillissement", RACINE / "sorties" / "micro_vieillissement.csv"),
                           ("vieillissement_deciles", RACINE / "sorties" / "micro_vieillissement_deciles.csv"),
                           ("vieillissement_recettes", RACINE / "parametres" / "donnees" / "micro_recettes_annees.csv")):
        lignes = []
        for f in sorted(dossier.glob(f"*_{suffixe}.csv")):
            with f.open(encoding="utf-8") as g:
                lignes += list(csv.DictReader(g))
        if lignes:
            om._ecrire(cible, lignes)


if __name__ == "__main__":
    main(sys.argv[1:] or ["statu_quo"])
