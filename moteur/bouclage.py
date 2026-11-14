"""Macro bouclée : demande, prix et taux réagissent aux programmes (phase E de la roadmap, 14/11/2026).

Remplace la forme linéaire du multiplicateur (effet entier l'année de l'impulsion, éteint en
macro.annees_effet_ajustement ans) par une forme réduite annuelle calée sur les variantes de Mésange 2017
(Bardaji et al., Insee G2017/04 ; outils/calibrer_bouclage.py), en écart au statu quo :

    z_t = μ·z_{t-1} + σ·r_t                               effet retardé du taux réel (investissement)
    x_t = a·g_t + b·x_{t-1} − c·q_{t-1} − z_t              écart de production (% du PIB)
    π_t = κ·(x_t − φ·g_t)                                  inflation en plus (courbe de Phillips, E2)
    q_t = q_{t-1} + π_t                                     prix relatifs à l'étranger (compétitivité-prix, E4)
    r_t = w·((φπ − 1)·π_{t-1} + φy·x_{t-1})                 taux réel de la zone : règle de Taylor de la BCE (E3)

g : impulsion de demande permanente (points de PIB, pondérée par instrument : offre.impulsion). La demande en plus
fait monter les prix ; la perte de compétitivité-prix ramène peu à peu le PIB vers son niveau d'offre (φ : part
gardée à long terme, Mésange : 0,16 pour 1). La BCE ne voit la France que pour son poids dans la zone (w).

Échelle par scénario (E1) : macro.multiplicateur est désormais l'effet MAXIMAL d'un point de PIB de dépense
(Mésange : 1,06 la deuxième année ; CAE : 1), atteint en deux ans, au lieu de l'effet de la première année. La forme
(montée, dissipation par les prix) est commune ; le sens compte comme avant (relance : scénario miroir). La
contrainte de capacité (capacite.*) joue sur le PIB en plus, comme avant.

Sorties pour le noyau (`contexte`) :
- inflation du programme = celle du statu quo (ou du programme) + π ;
- inflation_taux : inflation que suivent les taux de marché (effet de Fisher) : celle du statu quo + w·π (en union
  monétaire, les taux suivent l'inflation de la zone, pas celle de la France seule) ;
- taux_marche : hausse du taux de marché due à la BCE au-delà de Fisher, w·((φπ − 1)·π + φy·x), rejointe par le
  taux apparent au rythme du renouvellement de la dette, comme Fisher.

Une inflation française plus haute que celle de la zone allège donc la dette réelle (et une désinflation l'alourdit) :
c'est l'effet du niveau des prix sur une dette nominale, que l'ancien calcul (inflation du statu quo pour tous les
programmes sauf Écologie de droite) ignorait.

Dans le noyau (moteur/noyau.trajectoire) : l'écart de taux de marché au statu quo pèse sur le PIB
(bouclage.prime_demande, E1) ; les pensions perdent l'inflation due au programme l'année où elle survient (E2).
Balance commerciale publiée par le noyau (bouclage.exterieur, E4). Reste de la phase E : termes de l'échange (choc
pétrolier), contenu en importations par instrument (E4) ; accumulation du capital (E5) ; marché du travail (E6).
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES

MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}
HORIZON = 60


def actif(p) -> bool:
    return bool(p.val("macro.bouclage"))


def reponses_unitaires(p) -> dict:
    """Réponses à une impulsion permanente d'un point de PIB, normalisées pour que l'effet maximal sur le PIB vaille
    1 (le multiplicateur du scénario les met à l'échelle). Clés : pib, prix (niveau, %), inflation (points),
    inflation_taux (points), taux_marche (points), pic (année de l'effet maximal, 0 = année de l'impulsion)."""
    cache = p.__dict__.setdefault("_cache", {})
    if "bouclage_unitaire" in cache:
        return cache["bouclage_unitaire"]
    f = p.val("bouclage.forme")
    b_ = p.val("bouclage.bce")
    a, b, c, k, phi = f["a"], f["b"], f["c"], f["kappa"], f["phi"]
    sig, mu = f["sigma"], f["mu"]
    w, fp, fy = (b_["poids_france"], b_["phi_pi"], b_["phi_y"]) if b_["active"] else (0.0, 0.0, 0.0)
    x = pi = q = z = 0.0
    X, Q, P, R = [], [], [], []
    for _ in range(HORIZON):
        r = w * ((fp - 1) * pi + fy * x)  # réaction à l'année écoulée
        z = mu * z + sig * r
        x = a + b * x - c * q - z
        pi = k * (x - phi)
        q += pi
        X.append(x), Q.append(q), P.append(pi), R.append(w * (fp * pi + fy * x) - w * pi)
    pic = max(X)
    out = {"pib": [v / pic for v in X], "prix": [v / pic for v in Q], "inflation": [v / pic for v in P],
           "inflation_taux": [w * v / pic for v in P], "taux_marche": [v / pic for v in R],
           "pic": X.index(pic), "pic_brut": pic}
    cache["bouclage_unitaire"] = out
    return out


def _h(serie: list, tau: int) -> float:
    return serie[tau] if 0 <= tau < len(serie) else serie[-1]


def prix_offre(p, mesures, annees) -> dict:
    """Prix par les coûts (E2) : une baisse du coût du travail fait baisser les prix (bouclage.prix_offre, Mésange),
    sans toucher au PIB (déjà dans le canal d'offre). Rend {année: fraction du niveau des prix}."""
    par = p.val("bouclage.prix_offre")
    annees = list(annees)
    y = sq.pib(p, "prudent")
    out = {t: 0.0 for t in annees}
    for m in mesures or []:
        if m.instrument not in par:
            continue
        lt, v = par[m.instrument]["long_terme"], par[m.instrument]["vitesse"]
        # points de PIB de baisse : une recette en moins (montant < 0) est une baisse
        pts = {t: (-m.valeurs.get(t, 0.0) if m.poste == "recettes" else 0.0) / y[max(t, 2029)] for t in annees}
        prec = 0.0
        for i_t, t in enumerate(annees):
            d = pts[t] - prec
            prec = pts[t]
            if d:
                for j, u in enumerate(annees[i_t:]):
                    out[u] += lt * d * (1 - (1 - v) ** (j + 1))
    return out


def facture_energie(p, mesures, annees) -> dict:
    """Importations de pétrole et de gaz en plus (Md€ de 2026, + = facture plus lourde) dues aux tonnes de CO2 fossile
    que les mesures déclarent dans les secteurs énergétiques (bouclage.energie_importee, phase E4)."""
    from .ecologie.emissions import ENERGIE
    k = p.val("bouclage.energie_importee")["md_par_mt"]
    out = {t: 0.0 for t in annees}
    for m in mesures or []:
        for cle, serie in (getattr(m, "physique", None) or {}).items():
            if cle.startswith("emissions_mt:") and cle.split(":", 1)[1] in ENERGIE:
                for t in annees:
                    out[t] += k * serie.get(t, 0.0)
    return out


def reponse(p, s: str, cout_net: dict, annees, mesures=None, physiques=None) -> dict:
    """Réponse de l'économie à l'impulsion budgétaire nette (cout_net : coût net cumulé des mesures, Md€, + = relance),
    année par année. Chaque variation d'impulsion prend le multiplicateur de son scénario (resserrement) ou du
    scénario miroir (relance). Rend dpib (Md€, après contrainte de capacité), et en écart au statu quo : prix (niveau,
    fraction), inflation, inflation_taux, taux_marche (fractions par an)."""
    from .programme_simple import contrainte_capacite
    u = reponses_unitaires(p)
    m = {sc: sq._v(p, "macro.multiplicateur", sc) for sc in (s, MIROIR[s])}
    # facture énergétique (E4) : revenu payé à l'étranger, impulsion de demande négative
    fe = facture_energie(p, physiques if physiques is not None else mesures, annees)
    w_fe = p.val("bouclage.energie_importee")["poids_demande"]
    cout_net = {t: cout_net[t] - w_fe * fe[t] for t in annees}
    y = sq.pib(p, s)
    annees = list(annees)
    # g : impulsion en fraction du PIB ; les réponses unitaires sont en % pour 1 % de PIB, donc m × g × h est une
    # fraction (prix) ou une fraction par an (inflation, taux)
    chocs, prec = [], 0.0
    dpib, prix, infl, infl_t, taux = {}, {}, {}, {}, {}
    for i_t, t in enumerate(annees):
        i = cout_net[t] - prec
        prec = cout_net[t]
        mk = m[MIROIR[s]] if i > 0 else m[s]
        chocs.append((i_t, i, mk, i / y[max(t, 2029)]))
        dpib[t] = sum(mk * x * _h(u["pib"], i_t - j) for j, x, mk, _ in chocs)
        prix[t] = sum(mk * g * _h(u["prix"], i_t - j) for j, _, mk, g in chocs)
        infl[t] = sum(mk * g * _h(u["inflation"], i_t - j) for j, _, mk, g in chocs)
        infl_t[t] = sum(mk * g * _h(u["inflation_taux"], i_t - j) for j, _, mk, g in chocs)
        taux[t] = sum(mk * g * _h(u["taux_marche"], i_t - j) for j, _, mk, g in chocs)
    # prix par les coûts (cotisations employeurs…) : en niveau ; l'inflation en est la variation, et les taux de
    # marché suivent la part de la zone (w), comme pour la demande
    po = prix_offre(p, mesures, annees)
    w = p.val("bouclage.bce")["poids_france"] if p.val("bouclage.bce")["active"] else 0.0
    for i_t, t in enumerate(annees):
        d = po[t] - (po[annees[i_t - 1]] if i_t else 0.0)
        prix[t] += po[t]
        infl[t] += d
        infl_t[t] += w * d
    return {"dpib": contrainte_capacite(p, s, dpib), "dpib_avant_capacite": dpib, "prix": prix, "inflation": infl,
            "facture_energie": fe,
            "inflation_taux": infl_t, "taux_marche": taux}


def contexte(p, s: str, rep: dict | None, inflation_programme: dict | None = None) -> dict:
    """Clés du contexte du noyau tirées de la réponse : inflation (celle du programme, ou du statu quo, + π),
    inflation_taux et taux_marche. Vide si le bouclage est désactivé ou sans réponse."""
    if rep is None or not actif(p):
        return {}
    base = inflation_programme or sq.inflation(p, s)
    return {"inflation": {t: base[t] + rep["inflation"].get(t, 0.0) for t in ANNEES},
            "inflation_taux": {t: base[t] + rep["inflation_taux"].get(t, 0.0) for t in ANNEES},
            "taux_marche": {t: rep["taux_marche"].get(t, 0.0) for t in ANNEES},
            "inflation_bouclage": {t: rep["inflation"].get(t, 0.0) for t in ANNEES},
            "prix_bouclage": {t: rep["prix"].get(t, 0.0) for t in ANNEES},
            "facture_energie": {t: rep.get("facture_energie", {}).get(t, 0.0) for t in ANNEES}}


def forme_production_non_marchande(p, tau: int) -> float:
    """Part d'une dépense de postes publics sortie du multiplicateur au bout de tau années (phase A3, forme bouclée) :
    0 jusqu'à l'effet maximal, puis 1 − effet restant (le PIB garde à long terme le coût des postes)."""
    u = reponses_unitaires(p)
    if tau <= u["pic"]:
        return 0.0
    return max(0.0, 1.0 - _h(u["pib"], tau))


def forme_clause(p, tau: int) -> float:
    """Effet sur le PIB, tau années après, d'une impulsion de 1 au multiplicateur maximal de 1 (pour les leviers qui
    calculent leur propre effet récessif, comme la clause d'Écologie de droite)."""
    return _h(reponses_unitaires(p)["pib"], tau)
