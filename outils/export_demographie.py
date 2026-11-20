"""Démographie de chaque programme pour le comparateur : population, naissances, décès, solde migratoire,
fécondité, structure par âge, et pyramide des âges (19/11/2026, vue « Population » du comparateur).

Rien de nouveau dans le modèle : ce script relit la population que le moteur calcule déjà pour chaque programme
(moteur/migrations.population_programme : projection de l'Insee du scénario, plus l'écart migratoire déclaré, plus
l'écart de naissances du canal commun) et en tire les flux.

- Statu quo : décès de l'Insee (statu_quo.deces), solde migratoire de la projection (demographie.migrations.
  solde_central, le même dans les trois scénarios de fécondité de l'Insee), naissances déduites de l'équation de la
  population : N(t) = P(t+1) − P(t) + D(t) − M(t).
- Programme : naissances en plus = écart de population à 0 an au 1er janvier suivant ; solde migratoire en plus =
  variation déclarée × montée ; décès en plus = ce qui reste de l'écart de population. Le moteur fait commencer les
  écarts en 2030 (le statu quo rapporte ses indices à 2029) : les entrées de 2028 et 2029 d'un programme arrivent
  toutes au 1er janvier 2030. Les flux sont donc publiés à partir de 2030.
- Fécondité : indicateur du scénario de l'Insee, plus l'effet du canal commun des naissances (même interpolation
  que le moteur entre les projections centrale et haute). La fécondité plus élevée des immigrées change les
  naissances, pas cet indicateur.

Écrit sorties/comparaison_demographie.csv et sorties/comparaison_pyramide.csv.
"""
from __future__ import annotations

import csv
from pathlib import Path

from moteur import migrations, noyau
from moteur import statu_quo as sq
from moteur.demographie import AGE_MAX, _projection
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
SCENARIOS = {"crise": "Crise", "prudent": "Prudent", "median": "Médian", "optimiste": "Optimiste"}
ANNEES_FLUX = range(2030, 2073)
ANNEES_PYRAMIDE = (2029, 2037, 2050, 2060)
TRANCHES = [(a, a + 4) for a in range(0, 95, 5)] + [(95, AGE_MAX)]


def _somme(v, a: int, b: int) -> float:
    return sum(v[a:b + 1])


def _age_median(v) -> float:
    tot, cum = sum(v), 0.0
    for a, x in enumerate(v):
        if cum + x >= tot / 2:
            return a + (tot / 2 - cum) / x if x else float(a)
        cum += x
    return float(AGE_MAX)


def _ecart_migration(p: Parametres, s: str, decl: dict | None) -> dict[int, float]:
    """Entrées nettes en plus pendant l'année t (du 1er janvier t au 1er janvier t + 1), comme le moteur les
    ajoute (migrations.ecart_population) ; celles de 2029 et d'avant arrivent toutes au 1er janvier 2030."""
    if not decl:
        return {t: 0.0 for t in range(2026, 2074)}
    v = migrations.variation(p, s, decl)
    debut, montee = int(decl.get("debut", 2028)), max(1, int(decl.get("montee", 1)))
    k = lambda t: min(1.0, max(0.0, (t - debut + 1) / montee))  # noqa: E731
    out = {t: v * k(t + 1) for t in range(2026, 2074)}
    out[2029] = sum(v * k(t) for t in range(2026, 2031))  # tout l'arriéré arrive au 1er janvier 2030
    for t in range(2026, 2029):
        out[t] = 0.0
    return out


def main() -> None:
    from moteur import canaux_declares
    p = Parametres()
    fv = p.val("demographie.fecondite_variantes")
    solde_sq = p.val("demographie.migrations")["solde_central"]
    haute, centrale = _projection("fec_haute"), _projection("central")
    lignes, pyramide = [], []
    for nom in noyau.programmes_disponibles():
        prog = noyau.charger(nom)
        lib = getattr(prog, "libelle", nom)
        if nom != "statu_quo":
            noyau.simuler(p, prog)  # range l'écart de naissances du canal commun dans prog.ecart_naissances
        try:
            decl = canaux_declares.declares(prog).get("solde_migratoire") if nom != "statu_quo" else None
        except (AttributeError, ValueError):
            decl = None
        for s, lab in SCENARIOS.items():
            base = sq.population(p, s)
            pop = migrations.population_programme(prog, p, s) if nom != "statu_quo" else base
            dc = sq.deces(p, s)
            em = _ecart_migration(p, s, decl)
            nc = getattr(prog, "ecart_naissances", {}).get((id(p), s))
            icf_sq = fv[sq._v(p, "demographie.scenario_fecondite", s)]
            for t in ANNEES_FLUX:
                P0, P1 = sum(base[t]), sum(base[t + 1])
                nais_sq = P1 - P0 + dc[t] - solde_sq
                e0 = [x - y for x, y in zip(pop[t], base[t])]
                e1 = [x - y for x, y in zip(pop[t + 1], base[t + 1])]
                nais_plus = e1[0]
                mig_plus = em[t]
                dec_plus = nais_plus + mig_plus - (sum(e1) - sum(e0))
                nais, dec, mig = nais_sq + nais_plus, dc[t] + dec_plus, solde_sq + mig_plus
                # fécondité : effet du canal commun des naissances sur l'indicateur (enfants par femme)
                d_icf = 0.0
                if nc is not None:
                    den = haute[t + 1][0] - centrale[t + 1][0]
                    d_icf = (fv["fec_haute"] - fv["central"]) * nc[t + 1][0] / den if den else 0.0
                v = pop[t]
                tot = sum(v)
                lignes.append({
                    "cle": f"{lib}|{lab}|{t}", "programme": lib, "scenario": lab, "annee": t,
                    "population_millions": round(tot / 1e6, 3),
                    "ecart_population_milliers": round((tot - P0) / 1e3, 1),
                    "naissances_milliers": round(nais / 1e3, 1), "deces_milliers": round(dec / 1e3, 1),
                    "solde_naturel_milliers": round((nais - dec) / 1e3, 1),
                    "solde_migratoire_milliers": round(mig / 1e3, 1),
                    "ecart_solde_migratoire_milliers": round(mig_plus / 1e3, 1),
                    "ecart_naissances_milliers": round(nais_plus / 1e3, 1),
                    "fecondite": round(icf_sq + d_icf, 3),
                    "part_moins_20_pct": round(_somme(v, 0, 19) / tot * 100, 2),
                    "part_20_64_pct": round(_somme(v, 20, 64) / tot * 100, 2),
                    "part_65_plus_pct": round(_somme(v, 65, AGE_MAX) / tot * 100, 2),
                    "part_80_plus_pct": round(_somme(v, 80, AGE_MAX) / tot * 100, 2),
                    "dependance_65_20_64": round(_somme(v, 65, AGE_MAX) / _somme(v, 20, 64) * 100, 1),
                    "age_median": round(_age_median(v), 1),
                })
            for t in ANNEES_PYRAMIDE:
                for a, b in TRANCHES:
                    tr = f"{a}-{b}" if b < AGE_MAX else f"{a}+"
                    pyramide.append({"cle": f"{lib}|{lab}|{t}|{tr}", "programme": lib, "scenario": lab, "annee": t,
                                     "tranche": tr, "age_debut": a,
                                     "milliers": round(_somme(pop[t], a, b) / 1e3, 1),
                                     "statu_quo_milliers": round(_somme(base[t], a, b) / 1e3, 1)})
    for fichier, rows in (("comparaison_demographie.csv", lignes), ("comparaison_pyramide.csv", pyramide)):
        with (RACINE / "sorties" / fichier).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        from outils import trace
        trace.enregistrer(fichier, script="outils.export_demographie")
    print("Écrit : sorties/comparaison_demographie.csv, sorties/comparaison_pyramide.csv")


if __name__ == "__main__":
    main()
