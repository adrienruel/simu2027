"""Formation supérieure : diplômés en plus, par cohorte, et ce qu'ils changent au PIB (phase Q, 20/11/2026).

Canal commun (moteur/canaux_declares.py, canal « formation_superieure ») : un programme déclare la filière, le flux
annuel de diplômés visé et son calendrier ; tout le reste vient du barème commun (groupe formation_superieure de
parametres/commun/economie.yaml). Seule filière codée : les ingénieurs (demande d'Adrien du 20/11/2026, mesure
PHI-NUM-03 de Philippe : 100 000 ingénieurs formés par an).

Chaîne, pour chaque scénario :
1. **Flux.** Diplômés en plus l'année g = (objectif − flux du statu quo) × part de l'objectif atteinte × montée des
   places de `debut` à `plein`, décalée de la durée des études financées en plus (premiers diplômés en plus
   `delai` ans après l'ouverture des places).
2. **Absorption par la demande.** Chaque année, un besoin non pourvu de postes d'ingénieurs (Institut Montaigne,
   2025 : 28 000 ingénieurs et bac+5 de plus par an en réindustrialisation modérée, au médian) ; une part du besoin
   non utilisé se reporte à l'année suivante (le reste est pourvu autrement ou abandonné). Les diplômés en plus au-delà du besoin sont **en excédent** : une part part à l'étranger,
   les autres prennent un poste moins qualifié (déclassement) et ne gardent qu'une fraction de l'écart de
   productivité. Optimiste seulement : une part de l'excédent crée sa propre demande (changement technique orienté
   vers les compétences abondantes). Le statut d'une cohorte (absorbée ou en excédent) est fixé à sa sortie.
3. **Cohortes de travailleurs.** Chaque cohorte vieillit : survie de la projection de l'Insee (plafonnée à 1 : pas
   d'immigration propre aux diplômés), emploi des ingénieurs (taux d'emploi propre, profil par âge de la population
   pour les sorties d'activité), départ à l'étranger.
4. **PIB.** Diplômé en emploi × écart de productivité avec le cursus qu'il aurait suivi (écart de salaire observé ×
   part causale) × salaire relatif de ce cursus × profil de salaire par âge × productivité moyenne par emploi.
   Il entre comme un gain de productivité : dividende du statu quo au solde, comme les autres canaux.
5. **Entrée retardée.** Une part des étudiants en plus aurait travaillé pendant ces années d'études : PIB en moins
   (profil de salaire des 18-24 ans).
6. **Coût.** Places en plus × coût net d'une année d'études (école d'ingénieurs moins le cursus remplacé) × part
   publique. Il est compté par le programme comme une dépense (multiplicateur, prélèvements sur les rémunérations).

Ce qui n'est pas compté : la baisse de l'écart de salaire des ingénieurs déjà en poste quand l'offre monte (un
transfert entre salariés et employeurs, sans effet de premier ordre sur le PIB) ; les effets d'entraînement sur
l'innovation ; le rattrapage de carrière des déclassés.

Profils (`profils`) : stock d'ingénieurs en activité du statu quo (calé sur l'IESF, 1 000 400 fin 2024, répartition
par âge tirée des flux passés), diplômés en plus du programme, déclassés et partis, part dans l'emploi.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES
from .parametres import Parametres

FILIERES = ("ingenieurs",)
G = "formation_superieure."


def _v(p: Parametres, nom: str, s: str):
    return p.val(G + nom, s)


def _montee(t: int, debut: int, plein: int) -> float:
    return max(0.0, min(1.0, (t - debut + 1) / (plein - debut + 1)))


def _verifier(decl: dict) -> None:
    if decl.get("filiere") not in FILIERES:
        raise ValueError(f"formation_superieure : filière inconnue {decl.get('filiere')!r} (filières : {', '.join(FILIERES)})")


def flux_vise(p: Parametres, decl: dict) -> float:
    """Diplômés en plus par an visés par le programme : objectif − flux du statu quo (jamais négatif)."""
    _verifier(decl)
    return max(0.0, float(decl["objectif"]) - p.val(G + "diplomes_statu_quo"))


def places(p: Parametres, s: str, decl: dict, t: int) -> float:
    """Étudiants en plus l'année t (années d'études financées en plus)."""
    n = flux_vise(p, decl) * _v(p, "part_objectif_atteinte", s)
    return n * _montee(t, int(decl["debut"]), int(decl["plein"])) * _v(p, "delai_diplome", s)


def diplomes(p: Parametres, s: str, decl: dict, g: int) -> float:
    """Diplômés en plus sortis l'année g."""
    n = flux_vise(p, decl) * _v(p, "part_objectif_atteinte", s)
    d = int(_v(p, "delai_diplome", s))
    return n * _montee(g - d, int(decl["debut"]), int(decl["plein"]))


def cohortes(p: Parametres, s: str, decl: dict) -> dict[int, dict[str, float]]:
    """Par année de sortie g : diplômés, absorbés par le besoin, en excédent (étape 2 du module)."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("qualif_cohortes", s, tuple(sorted(decl.items())))
    if cle in cache:
        return cache[cle]
    besoin, fin = _v(p, "besoin_annuel", s), int(p.val(G + "besoin_annee_fin"))
    apres, suit = _v(p, "besoin_apres", s), _v(p, "besoin_suit_offre", s)
    garde = _v(p, "besoin_report", s)
    report, out = 0.0, {}
    for g in range(int(decl["debut"]), ANNEES[-1] + 1):
        dispo = report + besoin * (1.0 if g <= fin else apres)
        n = diplomes(p, s, decl, g)
        absorbe = min(n, dispo)
        absorbe += suit * (n - absorbe)  # demande créée par l'offre (optimiste)
        report = garde * max(0.0, dispo - n)  # poste non pourvu : pourvu autrement ou abandonné, en partie
        out[g] = {"diplomes": n, "absorbes": absorbe, "excedent": n - absorbe}
    cache[cle] = out
    return out


def _profil_age(p: Parametres) -> dict[int, float]:
    from .demographie import _tranche
    return {a: v for k, v in p.val("cohortes.profil_salaire_age").items() for a in _tranche(k)}


def _emploi_relatif(p: Parametres, t: int) -> dict[int, float]:
    """Emploi par âge rapporté à celui des 30-49 ans (sorties d'activité des seniors), plafonné à 1."""
    from .demographie import taux_emploi_par_age
    taux = taux_emploi_par_age(p, t)
    ref = sum(taux.get(a, 0.0) for a in range(30, 50)) / 20
    return {a: min(1.0, taux.get(a, 0.0) / ref) for a in range(18, 106)}


def _survie(pop: dict, t: int, g: int, age_d: int) -> float:
    a = age_d + t - g
    if a > 105:
        return 0.0
    t0 = max(g, ANNEES[0])
    a0 = age_d + t0 - g
    if pop[t0][a0] <= 0:
        return 0.0
    return min(1.0, pop[t][a] / pop[t0][a0])


def detail(p: Parametres, s: str, decl: dict) -> dict[int, dict[str, float]]:
    """Par année : diplômés en plus en emploi en France (absorbés, déclassés), partis à l'étranger, étudiants en plus,
    PIB en plus (Md€ de 2026) : gain de productivité et entrée retardée."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("qualif_detail", s, tuple(sorted(decl.items())))
    if cle in cache:
        return cache[cle]
    coh = cohortes(p, s, decl)
    pop, y, eff = sq.population(p, s), sq.pib(p, s), sq.effectifs(p, s)
    prof = _profil_age(p)
    age_d = int(p.val(G + "age_diplome"))
    pi = p.val(G + "ecart_salaire_observe") * _v(p, "part_causale", s)
    cf = p.val(G + "salaire_relatif_contrefactuel")
    tau = p.val(G + "taux_emploi")
    e_base, e_exc = p.val(G + "part_etranger"), _v(p, "part_etranger_excedent", s)
    delta = _v(p, "prime_declasses", s)
    jeunes = _v(p, "part_etudiants_sinon_en_emploi", s) * prof.get(20, 0.593)
    out = {}
    for t in ANNEES:
        rel = _emploi_relatif(p, t)
        prod = y[t] * 1e9 / eff[t]["emploi"]  # € de PIB par emploi
        abs_, dec, etr, gain = 0.0, 0.0, 0.0, 0.0
        for g, c in coh.items():
            if g > t:
                break
            a = age_d + t - g
            sv = _survie(pop, t, g, age_d)
            emp = tau * rel.get(a, 0.0) * sv
            na = c["absorbes"] * (1 - e_base) * emp
            nd = c["excedent"] * (1 - e_exc) * emp
            etr += (c["absorbes"] * e_base + c["excedent"] * e_exc) * sv
            abs_, dec = abs_ + na, dec + nd
            gain += (na + delta * nd) * pi * cf * prof.get(a, 1.0) * prod
        etu = places(p, s, decl, t)
        retard = -etu * jeunes * prod
        out[t] = {"absorbes_en_emploi": abs_, "declasses_en_emploi": dec, "partis": etr, "etudiants": etu,
                  "pib_gain_md": gain / 1e9, "pib_retard_md": retard / 1e9}
    cache[cle] = out
    return out


def par_age(p: Parametres, s: str, decl: dict, annees) -> dict[int, dict[int, dict[str, float]]]:
    """Diplômés en plus en emploi en France par âge, les années demandées : {année: {âge: {absorbes, declasses}}}."""
    coh = cohortes(p, s, decl)
    pop = sq.population(p, s)
    age_d = int(p.val(G + "age_diplome"))
    tau = p.val(G + "taux_emploi")
    e_base, e_exc = p.val(G + "part_etranger"), _v(p, "part_etranger_excedent", s)
    out = {}
    for t in annees:
        rel = _emploi_relatif(p, t)
        out[t] = {}
        for g, c in coh.items():
            if g > t:
                break
            a = age_d + t - g
            emp = tau * rel.get(a, 0.0) * _survie(pop, t, g, age_d)
            out[t][a] = {"absorbes": c["absorbes"] * (1 - e_base) * emp, "declasses": c["excedent"] * (1 - e_exc) * emp}
    return out


def pib(p: Parametres, s: str, decl: dict) -> dict[str, dict[int, float]]:
    """PIB en plus (Md€) : {"productivite": …, "entree_retardee": …}."""
    d = detail(p, s, decl)
    return {"productivite": {t: d[t]["pib_gain_md"] for t in ANNEES},
            "entree_retardee": {t: d[t]["pib_retard_md"] for t in ANNEES}}


def cout(p: Parametres, s: str, decl: dict, annees) -> dict[int, float]:
    """Dépense publique en plus (Md€ de 2026, indexée sur les salaires à partir de 2029)."""
    c = _v(p, "cout_net_annee_etudiant", s) * _v(p, "part_publique", s)
    w = sq.salaires(p, s)
    return {t: places(p, s, decl, t) * c / 1e9 * (w[t] / w[2029] if t >= 2029 else 1.0) for t in annees}


# --- Profils des travailleurs : stock d'ingénieurs du statu quo et du programme --------------------------------

def _flux_historique(p: Parametres, g: int) -> float:
    pts = {int(k): float(v) for k, v in p.val(G + "flux_historique").items()}
    ans = sorted(pts)
    if g <= ans[0]:
        return pts[ans[0]]
    if g >= ans[-1]:
        return p.val(G + "diplomes_statu_quo")
    for a, b in zip(ans, ans[1:]):
        if a <= g <= b:
            return pts[a] + (pts[b] - pts[a]) * (g - a) / (b - a)
    return pts[ans[-1]]


def stock_statu_quo(p: Parametres, s: str) -> dict[int, dict[int, float]]:
    """Ingénieurs en activité en France par âge, statu quo : cohortes passées (flux historiques) et futures (flux du
    statu quo constant), calées sur l'effectif de l'IESF (fin 2024) la première année du modèle."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("qualif_stock_sq", s) in cache:
        return cache[("qualif_stock_sq", s)]
    pop = sq.population(p, s)
    age_d = int(p.val(G + "age_diplome"))
    tau, e = p.val(G + "taux_emploi"), p.val(G + "part_etranger")
    brut = {}
    for t in ANNEES:
        rel = _emploi_relatif(p, t)
        par_age = {}
        for a in range(age_d, 75):
            g = t - a + age_d
            sv = _survie(pop, t, g, age_d)  # cohortes passées : survie depuis la première année du modèle
            par_age[a] = _flux_historique(p, g) * (1 - e) * tau * rel.get(a, 0.0) * sv
        brut[t] = par_age
    k = p.val(G + "stock_en_activite") / sum(brut[ANNEES[0]].values())
    out = {t: {a: v * k for a, v in x.items()} for t, x in brut.items()}
    cache[("qualif_stock_sq", s)] = out
    return out


def profils(p: Parametres, s: str, decl: dict | None) -> dict[int, dict[str, float]]:
    """Par année : ingénieurs en activité (statu quo, en plus absorbés, déclassés), partis, part dans l'emploi,
    âge moyen des ingénieurs en activité, et part des moins de 35 ans."""
    st = stock_statu_quo(p, s)
    eff = sq.effectifs(p, s)
    d = detail(p, s, decl) if decl else None
    out = {}
    for t in ANNEES:
        n_sq = sum(st[t].values())
        plus = (d[t]["absorbes_en_emploi"] + d[t]["declasses_en_emploi"]) if d else 0.0
        out[t] = {
            "ingenieurs_statu_quo": n_sq,
            "en_plus_postes_ingenieur": d[t]["absorbes_en_emploi"] if d else 0.0,
            "en_plus_declasses": d[t]["declasses_en_emploi"] if d else 0.0,
            "en_plus_partis": d[t]["partis"] if d else 0.0,
            "etudiants_en_plus": d[t]["etudiants"] if d else 0.0,
            "part_emploi_statu_quo": n_sq / eff[t]["emploi"],
            "part_emploi_programme": (n_sq + plus) / eff[t]["emploi"],
            "age_moyen_statu_quo": sum(a * v for a, v in st[t].items()) / n_sq,
            "part_moins_35_statu_quo": sum(v for a, v in st[t].items() if a < 35) / n_sq,
        }
    return out
