"""Scénario sans réforme : le système actuel projeté de 2029 à 2073 (noyau commun, 4 novembre 2026).

Référence commune à tous les programmes : chaque programme se lit comme un écart à ce scénario. Le module ne lit
que les hypothèses communes (parametres/commun/) : aucun paramètre d'un programme, aucun effet d'un programme
(natalité, carbone, effort de 2029). Mêmes conventions que le reste du modèle : euros constants de 2026, économie de
2026 placée en 2029, années 2027-2028 au déficit tendanciel (moteur/calendrier.py, sans les mesures de 2028 d'un
programme).

Point de départ : la législation du PLF 2027, en parts du PIB (dépense 56,9 %, déficit 5,0 %, intérêts 2,9 %).
La dépense primaire est découpée en blocs, chacun avec ce qui le fait vivre à législation constante :

| Bloc | Évolution |
|---|---|
| Retraites | toutes les générations : population de l'Insee × part partie à chaque âge (âge légal de 64 ans) × pension liquidée (salaire de quinze ans plus tôt, érosion relative calée sur le COR), puis revalorisée sur les prix |
| Santé | pentes communes (Assurance maladie jusqu'en 2035, puis PROMEDE), dérive de 2027 à 2029 comprise |
| Assurance chômage | chômeurs du scénario × salaires |
| Famille | enfants, prix |
| Logement | population, prix |
| Pauvreté (RSA, prime d'activité) ; AAH et invalidité | adultes de 18 à 64 ans, prix |
| Investissement ; défense, UE et missions économiques | PIB |
| Enseignement | salaires × (élèves et étudiants de 3 à 24 ans) ^ élasticité |
| Autres dépenses (reste) | salaires × population (loi de Baumol) |

Recettes : part du PIB constante (prélèvements à législation constante, élasticité 1), sauf la part prélevée sur les
pensions (CSG, CASA, impôt sur le revenu des retraités), qui suit les pensions. Intérêts : même mécanique que le
module macro (taux apparent qui rejoint le taux de marché, effet de Fisher, prime de taux liée à la dette), sans
effet d'un programme sur les taux.

    from moteur.statu_quo import simuler
    sq = simuler()                       # quatre scénarios
    sq["prudent"][2050]["deficit"]       # % du PIB, au sens de Maastricht
"""
from __future__ import annotations

from .parametres import Parametres

ANNEES = list(range(2029, 2074))
SCENARIOS = ("crise", "prudent", "median", "optimiste")
BLOCS = ("retraites", "sante", "chomage", "famille", "logement", "pauvrete", "aah_invalidite",
         "investissement", "missions_pib", "education", "autres")


def _v(p: Parametres, cle: str, s: str):
    """Valeur d'un paramètre dans le scénario s (sans le renvoi « prudent → crise » du calcul de crise)."""
    if cle in p._surcharges:
        return p._surcharges[cle]
    return p[cle].pour(s)


def pib_2026(p: Parametres) -> float:
    from .calendrier import pib_2026 as _pib
    return _pib(p)


# --- Démographie sans programme ----------------------------------------------------------------------------

def population(p: Parametres, s: str) -> dict[int, tuple[float, ...]]:
    """Projection de l'Insee du scénario de fécondité, sans effet d'un programme sur les naissances."""
    from .demographie import _projection
    return _projection(_v(p, "demographie.scenario_fecondite", s))


def effectifs(p: Parametres, s: str) -> dict[int, dict[str, float]]:
    """Personnes en emploi (taux par âge de 2025, figés), chômeurs (taux par âge de 2025, calés sur 2026) et
    publics des dépenses, par année (2026-2073). Même méthode que demographie.chomage_tendanciel."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("sq_effectifs", s) in cache:
        return cache[("sq_effectifs", s)]
    from .demographie import AGE_MAX, _tranche
    taux = {a: x for k, x in p.val("demographie.taux_emploi_age").items() for a in _tranche(k)}
    u = {a: x for k, x in p.val("chomage.taux_par_age").items() for a in _tranche(k)}
    brut = {}
    for t, v in population(p, s).items():
        e = sum(v[a] * taux.get(a, 0.0) for a in range(18, AGE_MAX + 1))
        c = sum(v[a] * taux.get(a, 0.0) * u.get(a, 0.0) / (1 - u.get(a, 0.0)) for a in range(18, AGE_MAX + 1))
        brut[t] = {"emploi": e, "chomeurs_bruts": c, "total": sum(v), "enfants": sum(v[0:18]),
                   "adultes": sum(v[18:65]), "jeunes_3_24": sum(v[3:25]), "seniors": sum(v[65:])}
    u26 = p.val("chomage.taux_2026")
    k = u26 / (1 - u26) * brut[2026]["emploi"] / brut[2026]["chomeurs_bruts"]
    for x in brut.values():
        x["chomeurs"] = x.pop("chomeurs_bruts") * k
        x["taux_chomage"] = x["chomeurs"] / (x["emploi"] + x["chomeurs"])
    cache[("sq_effectifs", s)] = brut
    return brut


# --- Productivité, PIB, inflation ---------------------------------------------------------------------------

def salaires(p: Parametres, s: str) -> dict[int, float]:
    """Indice du salaire réel moyen (productivité par emploi), 1 en 2029 avant l'IA.

    Tendance du scénario à partir de 2030 ; IA (macro.ia_productivite) pendant macro.annees_ia ans à partir de
    macro.premiere_annee_ia, comme le module macro ; avant 2029, tendance du prudent (historique, commun à tous)."""
    g, g0 = _v(p, "macro.tendance", s), _v(p, "macro.tendance", "prudent")
    ia, debut, duree = _v(p, "macro.ia_productivite", s), p.val("macro.premiere_annee_ia"), p.val("macro.annees_ia")
    out, w = {}, 1.0
    for t in range(1990, 2029):
        out[t] = (1 + g0) ** (t - 2029)
    for t in ANNEES:
        if t > 2029:
            w *= 1 + g
        if debut <= t < debut + duree:
            w *= 1 + ia
        out[t] = w
    return out


def pib(p: Parametres, s: str) -> dict[int, float]:
    """PIB (Md€ de 2026) : économie de 2026 placée en 2029 × productivité × personnes en emploi."""
    e, w, base = effectifs(p, s), salaires(p, s), pib_2026(p)
    return {t: base * w[t] * e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}


def inflation(p: Parametres, s: str) -> dict[int, float]:
    """Inflation de base (Banque de France, puis convergence vers le long terme du scénario), sans effet d'un
    programme (ni carbone ni écart de production) ; 1,8 % fixe si le module d'inflation est désactivé."""
    if not p.val("inflation.active"):
        return {t: p.val("calendrier.inflation") for t in range(2027, 2074)}
    b, lt = p.val("inflation.base"), _v(p, "inflation.long_terme", s)
    out = {2027: b["2027"], 2028: b["2028"]}
    for t in range(2029, 2074):
        out[t] = b["2028"] + (lt - b["2028"]) * min(1.0, (t - 2028) / b["convergence_annees"])
    return out


def dette_fin_2028(p: Parametres) -> float:
    """Dette au 31 décembre 2028 (Md€ de 2026) : déficit tendanciel en 2027 et 2028 (PLF 2027), sans mesure d'un
    programme ; même calcul que moteur/calendrier.annees_2027_2028."""
    base = pib_2026(p)
    dette = p.val("calendrier.dette_fin_2026_pib") * base
    infl = inflation(p, "prudent")
    for an in (2027, 2028):
        dette = dette + p.val("calendrier.deficit_tendanciel_2027_2028") * base - infl[an] * dette
    return dette


# --- Retraites ----------------------------------------------------------------------------------------------

def retraites(p: Parametres, s: str) -> dict[int, dict[str, float]]:
    """Pensions de toutes les générations (Md€ de 2026) et retraités (millions), par année.

    Pour chaque génération : survivants (Insee), part partie à chaque âge (ancien_systeme.part_retraites_age, âge
    légal de 64 ans), pension liquidée = 1 avant 2029 (stock calé), sinon pension des nouveaux retraités
    (ancien_systeme.pension_nouveaux_relative) × salaire de statu_quo.retraites_decalage_carriere ans plus tôt
    × (1 − érosion relative) par année depuis 2029 ; revalorisée sur les prix ensuite (constante en euros de
    2026). Niveau calé sur statu_quo.retraites_part_pib_base en 2029 ; effectif calé sur les retraités du COR."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("sq_retraites", s) in cache:
        return cache[("sq_retraites", s)]
    from .demographie import AGE_MAX
    from .ancien_systeme import _part_age
    pop = population(p, s)
    r = _part_age(p)
    w = salaires(p, s)
    lag = int(p.val("statu_quo.retraites_decalage_carriere"))
    e = p.val("statu_quo.retraites_erosion_relative")
    nouveau = p.val("ancien_systeme.pension_nouveaux_relative")

    def niveau(depart: int) -> float:
        if depart < 2029:
            return 1.0
        return nouveau * w[depart - lag] / w[2029 - lag] * (1 - e) ** (depart - 2029)

    brut = {}
    for t in ANNEES:
        dep = eff = 0.0
        for a in range(50, AGE_MAX + 1):
            n = pop[t][a]
            for b in range(50, a + 1):
                d = r[b] - r[b - 1]
                if d > 0:
                    dep += n * d * niveau(t - a + b)
                    eff += n * d
        brut[t] = (dep, eff)
    k = p.val("statu_quo.retraites_part_pib_base") * pib_2026(p) / brut[2029][0]
    kn = p.val("anciennes_pensions.retraites_ancien_2029_millions")[0] / (brut[2029][1] / 1e6)
    out = {t: {"depenses": d * k, "retraites_millions": n / 1e6 * kn} for t, (d, n) in brut.items()}
    cache[("sq_retraites", s)] = out
    return out


# --- Santé --------------------------------------------------------------------------------------------------

def _ecart_sante_am(p: Parametres, nom: str) -> float:
    d = p.val("sante_trajectoire.depenses_2024")
    part = d["sante_md"] / d["pib_md"]
    return ((part + p.val("sante_trajectoire.scenarios_assurance_maladie")[nom]) / part) ** (1 / 6) - 1


def _ecart_sante_promede(p: Parametres, nom: str) -> float:
    x = p.val("sante_trajectoire.promede")[nom]
    return (x["part_2060"] / x["part_2011"]) ** (1 / 49) - 1


def sante(p: Parametres, s: str) -> dict[int, float]:
    """ONDAM et aide à l'autonomie (Md€ de 2026) : base de 2026, dérive jusqu'en 2029 (régulation de 2027-2029),
    puis salaires × hausse de la part de la santé (pentes communes : sante_trajectoire.pente_phase_1 jusqu'en
    derniere_annee_phase_1, pente_phase_2 ensuite), comme moteur/sante.py."""
    from .unites import facteur
    base = p.val("sante.ondam_2026") + p.val("sante.aide_sociale_autonomie_2024") * facteur(p, 2024, "recettes")
    e_derive = _ecart_sante_am(p, p.val("sante_trajectoire.scenario_2027_2029")) if p.val("sante_trajectoire.derive_prise_en_compte") else 0.0
    e1 = _ecart_sante_am(p, _v(p, "sante_trajectoire.pente_phase_1", s))
    e2 = _ecart_sante_promede(p, _v(p, "sante_trajectoire.pente_phase_2", s))
    fin = p.val("sante_trajectoire.derniere_annee_phase_1")
    w = salaires(p, s)
    out = {}
    for t in ANNEES:
        out[t] = (base * (1 + e_derive) ** 3 * w[t] / w[2029]
                  * (1 + e1) ** (min(t, fin) - 2029) * (1 + e2) ** max(0, t - fin))
    return out


def sante_2027(p: Parametres) -> float:
    """Santé au niveau de 2027 (une année de dérive), pour découper la dépense primaire de départ."""
    from .unites import facteur
    base = p.val("sante.ondam_2026") + p.val("sante.aide_sociale_autonomie_2024") * facteur(p, 2024, "recettes")
    e = _ecart_sante_am(p, p.val("sante_trajectoire.scenario_2027_2029")) if p.val("sante_trajectoire.derive_prise_en_compte") else 0.0
    return base * (1 + e)


# --- Budget de départ et blocs ------------------------------------------------------------------------------

def depart(p: Parametres) -> dict[str, float]:
    """Dépense primaire de départ par bloc (Md€ de 2026, législation du PLF 2027 sur l'économie de 2026) et
    recettes. Le reste (« autres ») est la dépense primaire moins les blocs identifiés."""
    from .unites import facteur
    y = pib_2026(p)
    sq = lambda k: p.val(f"statu_quo.{k}")  # noqa: E731
    primaire = (sq("depense_publique_base") - sq("charge_interets_base")) * y
    blocs = {
        "retraites": sq("retraites_part_pib_base") * y,
        "sante": sante_2027(p),
        "chomage": sq("chomage_indemnisation"),
        "famille": sq("famille_part_pib") * y,
        "logement": sq("logement_part_pib") * y,
        "pauvrete": sq("pauvrete_part_pib") * y,
        "aah_invalidite": sq("aah") + p.val("sante.pensions_invalidite_2024") * facteur(p, 2024, "recettes"),
        "investissement": sq("investissement_part_pib") * y,
        "missions_pib": sq("missions_pib_part_pib") * y,
        "education": sq("education_part_pib") * y,
    }
    blocs["autres"] = primaire - sum(blocs.values())
    if blocs["autres"] <= 0:
        raise ValueError(f"Statu quo : blocs identifiés ({sum(blocs.values()):.0f} Md€) au-dessus de la dépense primaire")
    recettes = (sq("depense_publique_base") - sq("deficit_base")) * y
    return {"blocs": blocs, "primaire": primaire, "recettes": recettes, "pib": y}


def blocs(p: Parametres, s: str) -> dict[int, dict[str, float]]:
    """Dépense primaire par bloc, chaque année (Md€ de 2026)."""
    d = depart(p)["blocs"]
    e, w, y, y0 = effectifs(p, s), salaires(p, s), pib(p, s), pib_2026(p)
    ret, san = retraites(p, s), sante(p, s)
    el = p.val("ministeres.elasticite_eleves_etudiants")

    def i(cle, t):
        return e[t][cle] / e[2029][cle]
    out = {}
    for t in ANNEES:
        wt = w[t] / w[2029]
        out[t] = {
            "retraites": ret[t]["depenses"],
            "sante": san[t],
            "chomage": d["chomage"] * i("chomeurs", t) * wt,
            "famille": d["famille"] * i("enfants", t),
            "logement": d["logement"] * i("total", t),
            "pauvrete": d["pauvrete"] * i("adultes", t),
            "aah_invalidite": d["aah_invalidite"] * i("adultes", t),
            "investissement": d["investissement"] * y[t] / y0,
            "missions_pib": d["missions_pib"] * y[t] / y0,
            "education": d["education"] * wt * i("jeunes_3_24", t) ** el,
            "autres": d["autres"] * wt * i("total", t),
        }
    return out


def recettes(p: Parametres, s: str) -> dict[int, float]:
    """Recettes publiques (Md€ de 2026) : part du PIB constante, sauf les prélèvements sur les pensions."""
    d = depart(p)
    taux = p.val("statu_quo.prelevements_sur_pensions")
    ret, y = retraites(p, s), pib(p, s)
    sur_pensions_0 = taux * ret[2029]["depenses"]
    part_reste = (d["recettes"] - sur_pensions_0) / d["pib"]  # part du PIB de départ (économie de 2026)
    return {t: part_reste * y[t] + taux * ret[t]["depenses"] for t in ANNEES}


# --- Trajectoire --------------------------------------------------------------------------------------------

def scenario(p: Parametres, s: str) -> dict[int, dict]:
    """Comptes de chaque année d'un scénario : recettes, blocs, intérêts, solde, dette, déficit au sens de
    Maastricht (même identité que moteur/macro.py : intérêts réels sur la dette en euros constants, plus
    l'inflation × la dette de l'année précédente)."""
    y, infl, rec, bl = pib(p, s), inflation(p, s), recettes(p, s), blocs(p, s)
    e = effectifs(p, s)
    infl_ref = p.val("calendrier.inflation")
    app0, lt = p.val("macro.taux_apparent_2029"), p.val("macro.taux_long_terme")
    n_lt, mat = p.val("macro.annees_taux_long_terme"), p.val("macro.maturite_moyenne_dette")
    prime_par_point = _v(p, "macro.prime_dette", s)
    fisher_actif = p.val("inflation.active") and p.val("inflation.effet_fisher")
    dette_prec = dette_fin_2028(p)
    fisher = prime = 0.0
    ratio_ref = None
    out = {}
    for t in ANNEES:
        ratio = dette_prec / y[t]
        ratio_ref = ratio if ratio_ref is None else ratio_ref
        prime += (prime_par_point * (ratio - ratio_ref) - prime) / mat
        if fisher_actif:
            fisher += ((infl[t] - infl_ref) - fisher) / mat
        nominal = min(lt, app0 + (lt - app0) * (t - 2029) / n_lt) + fisher + prime
        interets_reels = (nominal - infl[t]) * dette_prec
        primaire = sum(bl[t].values())
        solde = rec[t] - primaire - interets_reels
        dette = dette_prec - solde
        maastricht = (solde - infl[t] * dette_prec) / y[t]
        out[t] = {
            "pib": y[t], "recettes": rec[t], "depenses_primaires": primaire, "blocs": dict(bl[t]),
            "charge_dette": interets_reels + infl[t] * dette_prec, "taux_apparent": nominal,
            "solde_primaire": rec[t] - primaire, "solde": solde, "dette": dette,
            "deficit": -maastricht * 100, "dette_pib": dette / y[t] * 100,
            "chomage": e[t]["taux_chomage"] * 100, "emploi_millions": e[t]["emploi"] / 1e6,
            "retraites_pib": bl[t]["retraites"] / y[t] * 100, "sante_pib": bl[t]["sante"] / y[t] * 100,
            "recettes_pib": rec[t] / y[t] * 100, "depenses_primaires_pib": primaire / y[t] * 100,
            "inflation": infl[t] * 100,
        }
        dette_prec = dette
    return out


def simuler(p: Parametres | None = None) -> dict[str, dict[int, dict]]:
    p = p or Parametres()
    return {s: scenario(p, s) for s in SCENARIOS}


def ecart(programme: dict, statu_quo: dict, avant_regle: bool = False) -> dict[str, dict[int, dict[str, float]]]:
    """Écart programme − statu quo par scénario et par année : déficit (points de PIB), solde primaire (points de
    PIB, hors intérêts : l'écart propre aux politiques, sans l'effet boule de neige de la dette), dette (points de
    PIB), chômage (points), PIB (%). avant_regle : déficit du programme sans sa règle de trajectoire (le solde
    primaire, lui, est toujours celui du déficit publié)."""
    out = {}
    for s in statu_quo:
        if s not in programme:
            continue
        out[s] = {}
        for t, x in statu_quo[s].items():
            pr = programme[s][t]
            d_pr = pr["deficit_avant_clause"] if (avant_regle and "deficit_avant_clause" in pr) else pr["deficit"]
            sp_pr = (pr["solde"] + pr["charge_dette"]) / pr["pib"] * 100
            out[s][t] = {"deficit": d_pr - x["deficit"], "solde_primaire": sp_pr - x["solde_primaire"] / x["pib"] * 100,
                         "dette_pib": pr["dette_pib"] - x["dette_pib"],
                         "chomage": pr["chomage"] - x["chomage"], "pib": (pr["pib"] / x["pib"] - 1) * 100}
    return out


def annee_seuil_dette(sq_s: dict[int, dict], seuil: float = 200.0) -> int | None:
    """Première année où la dette dépasse le seuil (% du PIB), ou None."""
    return next((t for t, x in sq_s.items() if x["dette_pib"] > seuil), None)


def resume(sq: dict, annees=(2029, 2032, 2037, 2045, 2050, 2060)) -> str:
    l = ["Statu quo (système actuel projeté) — déficit au sens de Maastricht (% du PIB) / dette (% du PIB)"]
    for s, v in sq.items():
        seuil = annee_seuil_dette(v)
        l.append(f"  {s:<10}" + "  ".join(f"{t} : {v[t]['deficit']:5.2f} / {v[t]['dette_pib']:4.0f}" for t in annees)
                 + (f"   dette > 200 % en {seuil}" if seuil else ""))
    l.append("Prudent : solde primaire, retraites, santé (% du PIB), chômage (%)")
    v = sq["prudent"]
    l.append("  " + "  ".join(f"{t} : {v[t]['solde_primaire'] / v[t]['pib'] * 100:+.1f}, {v[t]['retraites_pib']:.1f}, "
                              f"{v[t]['sante_pib']:.1f}, {v[t]['chomage']:.1f}" for t in annees))
    return "\n".join(l)


if __name__ == "__main__":
    import json
    import sys
    from .parametres import RACINE
    p = Parametres()
    sq = simuler(p)
    print(resume(sq))
    (RACINE / "sorties").mkdir(exist_ok=True)
    (RACINE / "sorties" / "statu_quo.json").write_text(
        json.dumps({s: {str(t): x for t, x in v.items()} for s, v in sq.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
    if "--ecart" in sys.argv:
        from .simulation import simuler as simuler_programme
        e = ecart(simuler_programme(p), sq)
        ea = ecart(simuler_programme(p), sq, avant_regle=True)
        print("\nÉcart programme − statu quo : solde primaire (points de PIB, + = meilleur) ; déficit sans règle ; chômage (points)")
        for s in e:
            print(f"  {s:<10}" + "  ".join(f"{t} : {e[s][t]['solde_primaire']:+.2f} ; {ea[s][t]['deficit']:+.2f} ; {e[s][t]['chomage']:+.1f}"
                                           for t in (2029, 2037, 2050, 2073)))
