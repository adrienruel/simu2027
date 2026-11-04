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

Recettes impôt par impôt (recettes_par_impot) : niveau du PLF 2027, réparti selon la reconstitution du système actuel
(colonne « Ancien » de la v235, à 0,27 % des comptes de l'Insee) ; chaque impôt suit son assiette (masse salariale,
pensions, PIB, décès), barèmes à législation constante (élasticité 1). Intérêts : même mécanique que le
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


IMPOTS_SALAIRES = ("salaires_prive", "salaires_public", "independants")


def deces(p: Parametres, s: str) -> dict[int, float]:
    """Décès de chaque année (projections de l'Insee, scénario de fécondité ; prolongés par le dernier niveau)."""
    import csv
    from .distribution import DONNEES
    nom = _v(p, "demographie.scenario_fecondite", s)
    d: dict[int, float] = {}
    with (DONNEES / f"deces_insee_2026_{nom}.csv").open(encoding="utf-8") as f:
        for l in csv.DictReader(f):
            d[int(l["annee"])] = d.get(int(l["annee"]), 0.0) + float(l["deces"])
    derniere = max(d)
    return {t: d.get(t, d[derniere]) for t in ANNEES}


def recettes_par_impot(p: Parametres, s: str) -> dict[int, dict[str, float]]:
    """Recettes publiques impôt par impôt (Md€ de 2026).

    Niveau de départ : recettes du PLF 2027 (statu_quo.depense_publique_base − deficit_base), dont les recettes non
    fiscales (statu_quo.recettes_non_fiscales_part_pib) ; le reste réparti entre impôts selon la reconstitution du
    système actuel (statu_quo.structure_impots). Chaque impôt suit son assiette : masse salariale (personnes en emploi
    × salaires, comme le PIB), prélèvements sur les pensions calculés par OpenFisca (prelevements_retraites), PIB,
    PIB × décès pour les successions."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("sq_recettes", s) in cache:
        return cache[("sq_recettes", s)]
    y0 = pib_2026(p)
    base = recettes_par_impot_depart(p)
    nf = base.pop("non_fiscales")
    y = pib(p, s)
    pr = prelevements_retraites(p, s)
    tv = tva(p, s)
    dc = deces(p, s)
    out = {}
    for t in ANNEES:
        masse = y[t] / y0  # personnes en emploi × salaire moyen : comme le PIB (même indice)
        x = {}
        for i, v in base.items():
            if i in IMPOTS_SALAIRES:
                x[i] = v * masse
            elif i == "retraites":
                x[i] = v * pr[t]["total"] / pr[2029]["total"]  # OpenFisca, progressivité comprise
            elif i == "tva":
                x[i] = tv[t]["total"]  # par source de revenu (statu_quo.tva)
            elif i == "successions":
                x[i] = v * y[t] / y0 * dc[t] / dc[2029]
            else:
                x[i] = v * y[t] / y0
        x["non_fiscales"] = nf * y[t] / y0
        out[t] = x
    cache[("sq_recettes", s)] = out
    return out


def prelevements_activite(p: Parametres) -> dict[str, dict[str, float]]:
    """Prélèvements sur les salaires calculés par OpenFisca-France (législation 2026), Md€ de 2026 : cotisations,
    CSG, CRDS et impôt sur le revenu (coût employeur − salaire net − impôt), et prestations versées aux salariés
    (RSA, prime d'activité, aides au logement), sur les distributions de salaires de 2026 (privé : Insee ;
    public : DGAFP, tables de chaque versant pondérées par statu_quo.versants_fonction_publique).

    Sert de contrôle de la répartition des recettes (structure_impots, reconstitution de la v235) : deux calculs
    indépendants. Cas type d'OpenFisca : personne seule (l'impôt sur le revenu des couples n'est pas représenté)."""
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
    from .systeme_actuel import _interp, _table_openfisca

    def somme(d, tables: dict[str, float]):
        r = {"cout": 0.0, "prelevements": 0.0, "impot_revenu": 0.0, "rsa_prime": 0.0, "aide_logement": 0.0}
        for c, n in zip(d.milieux, d.effectifs):
            for nom, w in tables.items():
                T = _table_openfisca() if nom == "prive" else _table_openfisca(versant=nom)
                x = T["cout_du_travail"]
                net, ir = _interp(c, x, T["salaire_net"]), _interp(c, x, T["impot_revenu_restant_a_payer"])
                r["cout"] += w * n * c
                r["prelevements"] += w * n * (c - net - ir)
                r["impot_revenu"] += -w * n * ir
                r["rsa_prime"] += w * n * (_interp(c, x, T["rsa"]) + _interp(c, x, T["ppa"]))
                r["aide_logement"] += w * n * _interp(c, x, T["aide_logement"])
        return {k: v / 1e9 for k, v in r.items()}
    cache = p.__dict__.setdefault("_cache", {})
    if "sq_activite" not in cache:
        cache["sq_activite"] = {"prive": somme(effectifs_prive_2026(p), {"prive": 1.0}),
                                "public": somme(effectifs_public_2026(p), p.val("statu_quo.versants_fonction_publique"))}
    return cache["sq_activite"]


def prelevements_retraites(p: Parametres, s: str) -> dict[int, dict[str, float]]:
    """CSG, CRDS, CASA et impôt sur le revenu des retraités (Md€ de 2026), calculés par OpenFisca-France (table
    parametres/donnees/openfisca_retraites_2026.csv, législation 2026) sur la distribution des pensions de la DREES
    (déciles, forme seulement), recalée chaque année sur la pension moyenne du statu quo (dépenses / retraités).
    Personnes seules et couples (anciennes_pensions.couples, pension du conjoint : statu_quo.retraites_ratio_conjoint).

    statu_quo.baremes_retraites : « prix » (législation constante : seuils et barème revalorisés sur l'inflation, la
    pension est évaluée telle quelle au barème de 2026 en euros constants) ou « salaires » (barèmes qui suivent la
    croissance : la pension est divisée par l'indice des salaires ; quand elle baisse par rapport aux salaires, le
    taux moyen baisse)."""
    import csv
    from .distribution import DONNEES
    from .systeme_actuel import _interp
    cache = p.__dict__.setdefault("_cache", {})
    if "sq_table_retraites" not in cache:
        with (DONNEES / "openfisca_retraites_2026.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cache["sq_table_retraites"] = {k: [float(r[k]) for r in rows] for k in rows[0]}
    T = cache["sq_table_retraites"]
    x = T["pension_brute_mensuelle"]
    dec = p.val("anciennes_pensions.deciles_drees_2020")
    moy = sum(dec) / len(dec)
    pc = p.val("anciennes_pensions.couples")["part_en_couple"]
    ret, w = retraites(p, s), salaires(p, s)
    out = {}
    for t in ANNEES:
        n = ret[t]["retraites_millions"] * 1e6
        m = ret[t]["depenses"] * 1e9 / n / 12
        # barèmes qui suivent les salaires : pension exprimée aux barèmes de 2026 ; barèmes sur les prix : tels quels
        k = w[2029] / w[t] if p.val("statu_quo.baremes_retraites") == "salaires" else 1.0
        soc = ir = 0.0
        for d in dec:
            pm = d * m / moy
            for nom, a, b in (("soc", "seul_prelevements_sociaux", "couple_prelevements_sociaux"),
                              ("ir", "seul_impot_revenu", "couple_impot_revenu")):
                v = ((1 - pc) * _interp(pm * k, x, T[a]) + pc * _interp(pm * k, x, T[b])) / k
                if nom == "soc":
                    soc += n / len(dec) * v
                else:
                    ir += n / len(dec) * v
        out[t] = {"prelevements_sociaux": soc / 1e9, "impot_revenu": ir / 1e9, "total": (soc + ir) / 1e9}
    return out


def tva(p: Parametres, s: str) -> dict[int, dict[str, float]]:
    """TVA par source de revenu (Md€ de 2026) : la consommation est financée par des salaires, des pensions, des
    transferts, et la TVA non déductible (entreprises non assujetties, administrations, logement neuf).

    Parts de départ calculées avec la fonction de consommation actuelle du moteur (consommation.coefficient et
    exposant, Insee) et le taux moyen de TVA (systeme_actuel.taux_tva_moyen) :
    - salariés du privé et agents publics : revenu disponible actuel par OpenFisca (systeme_actuel.nets_prive ;
      tables des versants pondérées par statu_quo.versants_fonction_publique ; aides comprises) ; suit la masse salariale (le PIB) ;
    - retraités : pension nette des prélèvements calculés par OpenFisca (prelevements_retraites), distribution de la
      DREES, retraités résidant en France (retraites_actuels.donnees), recalculée chaque année ; la consommation
      suit le revenu relatif aux salaires (fonction de consommation appliquée au revenu divisé par l'indice des
      salaires, puis remultipliée) : si la pension baisse par rapport aux salaires, la TVA des retraités aussi ;
    - inactifs et étudiants (revenus actuels, RSA compris) : adultes, prix (minima revalorisés sur l'inflation) ;
    - TVA non déductible (accises_entreprises.ancienne_tva_entreprises, Md€ de 2024) : PIB.
    Le total de 2029 est calé sur la TVA de la répartition des recettes (structure_impots) : l'écart (revenus non
    représentés : indépendants, chômeurs, revenus du patrimoine, couples) est réparti au prorata des parts."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("sq_tva", s) in cache:
        return cache[("sq_tva", s)]
    import csv
    from .distribution import DONNEES
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
    from .recettes.tva_menages import lire_inactifs
    from .systeme_actuel import _interp, consommation_actuelle_ht, net_actuel, nets_prive
    from .unites import facteur
    taux = p.val("systeme_actuel.taux_tva_moyen")
    c = lambda revenu: taux * consommation_actuelle_ht(revenu, p)  # noqa: E731
    # agents publics : tables OpenFisca de chaque versant, pondérées comme dans prelevements_activite (sans les
    # pondérations d'un programme, que lit systeme_actuel.nets_public)
    from .systeme_actuel import _table_openfisca, taxe_fonciere
    poids = p.val("statu_quo.versants_fonction_publique")
    tables = {v: _table_openfisca(versant=v) for v in poids}
    public = 0.0
    dp = effectifs_public_2026(p)
    for cout, n in zip(dp.milieux, dp.effectifs):
        for v, wv in poids.items():
            T, xs = tables[v], tables[v]["cout_du_travail"]
            net = _interp(cout, xs, T["salaire_net"]) + _interp(cout, xs, T["impot_revenu_restant_a_payer"])
            aides = _interp(cout, xs, T["rsa"]) + _interp(cout, xs, T["ppa"]) + _interp(cout, xs, T["aide_logement"])
            public += wv * n * c(net + aides - taxe_fonciere(net, p, True))
    actifs = (sum(n * c(na) for n, na in zip(effectifs_prive_2026(p).effectifs, nets_prive(p)["actuel"])) + public) / 1e9
    rev, eff = lire_inactifs()
    transferts = (sum(n * c(net_actuel(x, p, False)) for x, n in zip(rev, eff))
                  + p.val("inactifs.etudiants") * c(net_actuel(0.0, p, False))) / 1e9
    non_ded = p.val("accises_entreprises.ancienne_tva_entreprises") * facteur(p, 2024, "recettes")
    # retraités : pension nette (OpenFisca), chaque année
    if "sq_table_retraites" not in cache:
        prelevements_retraites(p, s)
    T = cache["sq_table_retraites"]
    x = T["pension_brute_mensuelle"]
    dec = p.val("anciennes_pensions.deciles_drees_2020")
    moy = sum(dec) / len(dec)
    pc = p.val("anciennes_pensions.couples")["part_en_couple"]
    rd = p.val("retraites_actuels.donnees")
    part_france = rd["residents_france_2023"] / (rd["residents_france_2023"] + 900_000)
    ret, w, y, e = retraites(p, s), salaires(p, s), pib(p, s), effectifs(p, s)
    y0 = pib_2026(p)
    brut = {}
    for t in ANNEES:
        n = ret[t]["retraites_millions"] * 1e6 * part_france
        m = ret[t]["depenses"] * 1e9 / (ret[t]["retraites_millions"] * 1e6) / 12
        wr = w[t] / w[2029]
        v = 0.0
        for d in dec:
            pm = d * m / moy
            prel = sum((1 - pc) * _interp(pm, x, T[f"seul_{k}"]) + pc * _interp(pm, x, T[f"couple_{k}"])
                       for k in ("prelevements_sociaux", "impot_revenu"))
            v += n / len(dec) * wr * c((12 * pm - prel) / wr)
        brut[t] = v / 1e9
    parts0 = {"actifs": actifs, "retraites": brut[2029], "transferts": transferts, "non_deductible": non_ded}
    cible = recettes_par_impot_depart(p)["tva"]
    k = cible / sum(parts0.values())
    out = {}
    for t in ANNEES:
        out[t] = {"actifs": k * actifs * y[t] / y0,
                  "retraites": k * brut[t],
                  "transferts": k * transferts * e[t]["adultes"] / e[2029]["adultes"],
                  "non_deductible": k * non_ded * y[t] / y0}
        out[t]["total"] = sum(out[t].values())
    out["calage"] = k
    cache[("sq_tva", s)] = out
    return out


def recettes_par_impot_depart(p: Parametres) -> dict[str, float]:
    """Recettes de départ impôt par impôt (Md€ de 2026, économie de 2026) : niveau du PLF 2027 réparti selon
    statu_quo.structure_impots, plus les recettes non fiscales."""
    d = depart(p)
    nf = p.val("statu_quo.recettes_non_fiscales_part_pib") * d["pib"]
    struct = p.val("statu_quo.structure_impots")
    k = (d["recettes"] - nf) / sum(struct.values())
    return {**{i: v * k for i, v in struct.items()}, "non_fiscales": nf}


def recettes(p: Parametres, s: str) -> dict[int, float]:
    """Recettes publiques totales (Md€ de 2026), somme des impôts et des recettes non fiscales."""
    return {t: sum(x.values()) for t, x in recettes_par_impot(p, s).items()}


# --- Trajectoire --------------------------------------------------------------------------------------------

def scenario(p: Parametres, s: str) -> dict[int, dict]:
    """Comptes de chaque année d'un scénario : recettes, blocs, intérêts, solde, dette, déficit au sens de
    Maastricht. C'est le calcul du noyau sans aucune mesure (moteur/noyau.trajectoire)."""
    from .noyau import trajectoire
    out = trajectoire(p, s)
    e = effectifs(p, s)
    for t, x in out.items():
        x["emploi_millions"] = e[t]["emploi"] / 1e6
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
            # solde primaire : solde + intérêts réels (moteur du programme : charge_dette ; noyau : interets_reels)
            sp_pr = (pr["solde"] + pr.get("interets_reels", pr["charge_dette"])) / pr["pib"] * 100
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
