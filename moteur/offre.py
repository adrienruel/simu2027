"""Effets économiques communs des mesures : demande et offre, instrument par instrument (6 novembre 2026).

Demande (`poids_demande`) : le multiplicateur commun (macro.multiplicateur) vaut pour la dépense publique ; chaque
mesure entre dans l'impulsion budgétaire avec un poids selon ce qu'elle est (demande.poids : transferts ciblés,
pensions, impôts sur le travail, la consommation, les entreprises, le capital…), d'après les comparaisons de modèles
de la zone euro (Kilponen et al., 2015 ; Coenen et al., 2012).

Offre (`effets`) : effet durable d'un prélèvement ou d'un transfert sur le PIB, ajouté au multiplicateur, qui
s'efface :

- chaque mesure porte un instrument (Mesure.instrument) ; le canal additionne, année par année, le prélèvement en
  moins (recettes : −montant) ou le transfert aux actifs en moins, en points du PIB du statu quo ;
- **travail** : calculé cellule par cellule sur les distributions de salaires de 2026 (privé et public), au revenu
  net d'OpenFisca : la mesure est répartie entre cellules selon son incidence (Mesure.incidence : « proportionnel »
  aux prélèvements, « ir » à l'impôt sur le revenu, « bas » : montant égal par contribuable de l'impôt sur le revenu
  jusqu'à 2,5 SMIC, « haut » : impôt sur le revenu au-delà de 4 SMIC, « milieu » : prélèvements entre 1,6 et 3,5 SMIC
  (allègements), « plafond » : salaire au-delà du plafond de la Sécurité sociale, ou « openfisca:<réforme> » : réforme
  calculée par OpenFisca, offre (gain à travailler, personnes seules et neuf cas de couples) et demande (coût du
  travail) cellule par cellule ; « …@0,62 » : seule cette part du montant porte sur les revenus du travail) ; chaque cellule réagit au revenu net en plus
  avec l'élasticité de participation de sa tranche (plus forte en bas) et celle des heures ; effet sur le PIB = travail
  en plus pondéré par le coût × part du travail ;
- **entreprises** : même élasticité de l'investissement au coût du capital que les cohortes d'entreprises
  (macro.elasticite_invest) ; effet = part du capital × capital en plus ;
- **autres instruments** : élasticités de long terme de offre.* (coût du travail : Mésange ; capital des ménages,
  successions, consommation, transferts aux actifs) ;
- quand l'instrument joue pour le programme (baisse), l'élasticité du scénario ; quand il joue contre (hausse),
  celle du scénario miroir (crise ↔ optimiste, prudent ↔ médian) ;
- montée par ajustement partiel (offre.vitesse, ≈ 10 % de l'écart par an, profil de Mésange), à partir de 2027 ;
- recettes : le PIB en plus qui vient de l'emploi rapporte la part des recettes dans le PIB du statu quo ; celui qui
  vient de la productivité (PRODUCTIVITE, hors part d'emploi) rapporte le dividende de productivité du statu quo
  (statu_quo.dividende_productivite : les dépenses indexées sur les salaires montent aussi ; 12/11/2026) ;
- emplois : offre de travail et transferts : venus de l'inactivité (le chômage ne bouge pas) ; coût du travail,
  entreprises, consommation : pris sur le chômage.

Le canal ne remplace pas les effets propres déjà comptés par un programme (SMIC, assurance chômage de Tondelier,
postes publics, moteur d'Écologie de droite) : ces mesures ne portent pas d'instrument.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES, Mesure
from .parametres import Parametres

INSTRUMENTS = ("travail", "cout_travail", "capital_entreprises", "capital_menages", "successions", "consommation",
               "transferts_actifs", "investissement_public", "education", "recherche")
INCIDENCES = ("proportionnel", "ir", "bas", "haut", "milieu", "plafond")
LIBELLES = {"travail": "prélèvements sur le travail", "cout_travail": "coût du travail",
            "capital_entreprises": "fiscalité des entreprises", "capital_menages": "fiscalité du capital des ménages",
            "successions": "successions", "consommation": "TVA et accises", "transferts_actifs": "transferts aux actifs",
            "investissement_public": "investissement public", "education": "éducation (capital humain)",
            "recherche": "recherche publique"}
# part de l'effet sur le PIB qui est de l'emploi (hors travail, calculé par cellule), et part de ces emplois qui vient
# de l'inactivité (le reste : chômage)
EMPLOI = {"travail": (None, 1.0), "cout_travail": (1.0, 0.0), "capital_entreprises": (0.3, 0.0),
          "capital_menages": (0.0, 0.0), "successions": (0.0, 0.0), "consommation": (0.5, 0.0),
          "transferts_actifs": (1.0, 1.0), "investissement_public": (0.5, 0.0), "education": (0.0, 0.0),
          "recherche": (0.0, 0.0)}
MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}
# instruments dont l'effet sur le PIB (hors part d'emploi, EMPLOI) passe par la productivité : le salaire moyen monte,
# et avec lui les dépenses indexées ; le solde n'en garde que le dividende de productivité du statu quo
PRODUCTIVITE = ("capital_entreprises", "capital_menages", "successions", "investissement_public", "education", "recherche")
# « nouveau:rui_aah » : revenu universel d'Écologie de droite, qui remplace ces prestations (même poids de demande)
TRANSFERTS_CIBLES = ("famille", "logement", "pauvrete", "chomage", "aah_invalidite", "nouveau:rui_aah")
SMIC_BRUT_2026 = 1823.03 * 12
PLAFOND_SS_2026 = 48060.0  # plafond annuel de la Sécurité sociale 2026


def actif(p: Parametres) -> bool:
    return bool(p.val("offre.actif"))


# ------------------------------------------------------------------------------------------------ demande
def poids_demande(p: Parametres, m: Mesure) -> float:
    """Poids d'une mesure dans l'impulsion budgétaire (1 : dépense publique)."""
    w = p.val("demande.poids")
    if m.instrument:
        return w[m.instrument] if m.instrument != "transferts_actifs" else w["transferts_cibles"]
    if m.poste == "recettes":
        return w["autre_recette"]
    if m.poste == "retraites":
        return w["retraites"]
    if m.poste in TRANSFERTS_CIBLES:
        return w["transferts_cibles"]
    return w["depense"]


def impulsion(p: Parametres, mesures: list[Mesure], annees) -> dict[int, float]:
    """Coût net des mesures pondéré par leur poids de demande (Md€ ; + = relance)."""
    out = {t: 0.0 for t in annees}
    for m in mesures:
        if m.poste == "participations" or m.nature == "physique":
            continue
        k = poids_demande(p, m)
        for t in annees:
            v = m.valeurs.get(t, 0.0)
            out[t] += k * (-v if m.poste == "recettes" else v)
    return out


# ------------------------------------------------------------------------------------------------ offre : travail
def _cellules(p: Parametres) -> list[dict]:
    """Cellules de salariés de 2026 (privé et agents publics) : effectif, coût, brut, net (après IR), prélèvements,
    impôt sur le revenu (OpenFisca 2026)."""
    cache = p.__dict__.setdefault("_cache", {})
    if "offre_cellules" in cache:
        return cache["offre_cellules"]
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
    from .systeme_actuel import _interp, _table_openfisca
    out = []
    for d, tables in ((effectifs_prive_2026(p), {"prive": 1.0}),
                      (effectifs_public_2026(p), p.val("statu_quo.versants_fonction_publique"))):
        for nom, wv in tables.items():
            T = _table_openfisca() if nom == "prive" else _table_openfisca(versant=nom)
            x = T["cout_du_travail"]
            for c, n in zip(d.milieux, d.effectifs):
                net = _interp(c, x, T["salaire_net"]) + _interp(c, x, T["impot_revenu_restant_a_payer"])
                if n <= 0 or net <= 0:
                    continue
                out.append({"n": n * wv, "cout": c, "brut": _interp(c, x, T["brut"]), "net": net,
                            "prelevements": c - net, "ir": -_interp(c, x, T["impot_revenu_restant_a_payer"])})
    cache["offre_cellules"] = out
    return out


def _table_offre(nom: str) -> dict:
    """Table d'OpenFisca pour l'offre de travail (outils/openfisca_offre.py) : brut, coût, revenu disponible d'une
    personne seule et d'un couple (second apporteur)."""
    import csv
    from .distribution import DONNEES
    with (DONNEES / f"openfisca_offre_{nom}_2026.csv").open(encoding="utf-8") as f:
        lignes = sorted(({k: float(v) for k, v in l.items()} for l in csv.DictReader(f)), key=lambda l: l["brut"])
    return {k: [l[k] for l in lignes] for k in lignes[0]}


def _cas_couples(p: Parametres) -> list[tuple[str, float]]:
    """Colonnes des neuf cas de couples des tables d'OpenFisca et leur poids (offre.couples_cas)."""
    from outils.openfisca_offre import CONJOINTS, ENFANTS, colonne_couple
    w = p.val("offre.couples_cas")
    return [(colonne_couple(c, e), wc * we) for c, wc in zip(CONJOINTS, w["conjoints"]) for e, we in zip(ENFANTS, w["enfants"])]


def _reactions_openfisca(nom: str, brut: float, cas_couples: list[tuple[str, float]]) -> dict:
    """Pour une réforme calculée par OpenFisca, au salaire brut donné : variations relatives du gain à travailler
    (participation) et du taux de revenu net marginal (heures), pour une personne seule et en moyenne sur les couples
    (second apporteur) ; prélèvements en moins (salaire net après impôt sur le revenu en plus, moins coût du travail en
    plus), prestations en plus, coût du travail en plus (relatif)."""
    from .systeme_actuel import _interp
    a, r = _table_offre("actuel"), _table_offre(nom)
    h = max(1000.0, 0.02 * brut)
    dc = _interp(brut + h, a["brut"], a["cout_du_travail"]) - _interp(brut, a["brut"], a["cout_du_travail"])

    def reaction(col):
        def disp(T, b):
            return _interp(b, T["brut"], T[col])
        g0, g1 = disp(a, brut) - disp(a, 0.0), disp(r, brut) - disp(r, 0.0)
        m0 = (disp(a, brut + h) - disp(a, brut)) / dc
        m1 = (disp(r, brut + h) - disp(r, brut)) / dc
        return {"participation": (g1 - g0) / g0 if g0 > 0 else 0.0, "heures": (m1 - m0) / m0 if m0 > 0 else 0.0,
                "disponible": disp(r, brut) - disp(a, brut)}
    out = {"seul": reaction("disponible_seul")}
    cp = {"participation": 0.0, "heures": 0.0}
    for col, w in cas_couples:
        x = reaction(f"disponible_{col}")
        cp["participation"] += w * x["participation"]
        cp["heures"] += w * x["heures"]
    out["couple"] = cp
    c0, c1 = _interp(brut, a["brut"], a["cout_du_travail"]), _interp(brut, r["brut"], r["cout_du_travail"])
    di = _interp(brut, r["brut"], r["net_apres_ir_seul"]) - _interp(brut, a["brut"], a["net_apres_ir_seul"])
    out["prelevements_en_moins"] = di - (c1 - c0)
    out["prestations_en_plus"] = out["seul"]["disponible"] - di
    out["cout_relatif"] = (c1 - c0) / c0 if c0 > 0 else 0.0
    return out


def statique_openfisca(p: Parametres, nom: str) -> dict:
    """Coût statique d'une réforme du travail calculée par OpenFisca, sur les cellules de salariés de 2026 (Md€,
    économie de 2026 placée en 2029) : prélèvements en moins (impôts et cotisations des salariés, cotisations
    patronales) et prestations en plus (prime d'activité, RSA, aides au logement), cas d'une personne seule comme le
    statu quo."""
    cache = p.__dict__.setdefault("_cache", {})
    if ("offre_statique", nom) not in cache:
        cc = _cas_couples(p)
        prl = pre = 0.0
        for x in _cellules(p):
            r = _reactions_openfisca(nom, x["brut"], cc)
            prl += x["n"] * r["prelevements_en_moins"]
            pre += x["n"] * r["prestations_en_plus"]
        cache[("offre_statique", nom)] = {"prelevements_en_moins": prl / 1e9, "prestations_en_plus": pre / 1e9,
                                          "impots_en_moins": prl / 1e9}
    return cache[("offre_statique", nom)]


def ir_salaries_menages(p: Parametres, nom: str = "actuel") -> dict:
    """Impôt sur le revenu des salariés (Md€) calculé sur les cellules de 2026 : en personnes seules, et avec la part
    des salariés en couple (impôt du couple attribué au prorata des salaires, moyenne des neuf cas). Sert à caler les
    mesures d'impôt sur le revenu (OpenFisca en personne seule le surestime)."""
    from .systeme_actuel import _interp
    from outils.openfisca_offre import CONJOINTS, ENFANTS, colonne_couple
    T = _table_offre(nom)
    pc, _ = p.val("offre.travail_couples", "prudent")
    w = p.val("offre.couples_cas")
    seul = mix = 0.0
    for x in _cellules(p):
        b = x["brut"]
        i_s = _interp(b, T["brut"], T["ir_seul"])
        i_c = sum(wc * we * _interp(b, T["brut"], T[f"ir_{colonne_couple(c, e)}"]) * b / (b + c)
                  for c, wc in zip(CONJOINTS, w["conjoints"]) for e, we in zip(ENFANTS, w["enfants"]))
        seul += x["n"] * i_s
        mix += x["n"] * ((1 - pc) * i_s + pc * i_c)
    return {"seuls": seul / 1e9, "menages": mix / 1e9}


def travail_par_point(p: Parametres, s: str, incidence: str = "proportionnel") -> dict:
    """Effet de long terme d'1 point de PIB (de 2029) de prélèvement sur le travail en moins, réparti selon
    l'incidence : % de PIB et emplois (personnes) en plus."""
    if incidence.startswith("openfisca:"):
        return _travail_openfisca(p, s, incidence.split(":", 1)[1])
    if incidence not in INCIDENCES:
        raise ValueError(f"incidence inconnue {incidence}")
    cel = _cellules(p)
    y29 = sq.pib(p, s)[2029]

    def base(x):
        if incidence == "proportionnel":
            return x["prelevements"]
        if incidence == "ir":
            return x["ir"]
        if incidence == "bas":
            return 1.0 if (x["ir"] > 0 and x["brut"] <= 2.5 * SMIC_BRUT_2026) else 0.0
        if incidence == "haut":
            return x["ir"] if x["brut"] > 4 * SMIC_BRUT_2026 else 0.0
        if incidence == "milieu":  # allègements entre 1,6 et 3,5 SMIC
            return x["prelevements"] if 1.6 * SMIC_BRUT_2026 < x["brut"] <= 3.5 * SMIC_BRUT_2026 else 0.0
        return max(0.0, x["brut"] - PLAFOND_SS_2026)  # cotisation au-dessus du plafond de la Sécurité sociale
    poids = [x["n"] * base(x) for x in cel]
    total = sum(poids)
    ext = sq._v(p, "offre.travail_participation", s)
    hrs = sq._v(p, "offre.travail_heures", s)
    masse = sum(x["n"] * x["cout"] for x in cel)
    montant = 0.01 * y29 * 1e9
    travail, emplois = 0.0, 0.0
    for x, w in zip(cel, poids):
        if not w:
            continue
        r = montant * w / total / x["n"] / x["net"]  # revenu net en plus, relatif
        b = x["brut"] / SMIC_BRUT_2026
        e = ext[0] if b <= 1.3 else (ext[1] if b <= 2.5 else ext[2])
        emplois += x["n"] * e * r
        travail += x["n"] * (e + hrs) * r * x["cout"]
    pct = sq._v(p, "offre.travail_part_pib", s) * travail / masse * 100
    return {"pib_pct": pct, "emplois": emplois}


def _travail_openfisca(p: Parametres, s: str, nom: str) -> dict:
    """Effet de long terme d'une réforme du travail calculée par OpenFisca, ramené à 1 point de PIB de prélèvements en
    moins (statique) : offre (gain à travailler et taux marginal, personnes seules et couples) et demande (coût du
    travail, élasticité de sa tranche), cellule par cellule."""
    cel = _cellules(p)
    cc = _cas_couples(p)
    y29 = sq.pib(p, s)[2029]
    ext = sq._v(p, "offre.travail_participation", s)
    hrs = sq._v(p, "offre.travail_heures", s)
    dem = sq._v(p, "offre.demande_travail", s)
    pc, kc = sq._v(p, "offre.travail_couples", s)
    masse = sum(x["n"] * x["cout"] for x in cel)
    travail = emplois_offre = emplois_demande = 0.0
    for x in cel:
        r = _reactions_openfisca(nom, x["brut"], cc)
        b = x["brut"] / SMIC_BRUT_2026
        i = 0 if b <= 1.3 else (1 if b <= 2.5 else 2)
        part = (1 - pc) * ext[i] * r["seul"]["participation"] + pc * kc * ext[i] * r["couple"]["participation"]
        heures = hrs * ((1 - pc) * r["seul"]["heures"] + pc * r["couple"]["heures"])
        demande = -dem[i] * r["cout_relatif"]
        emplois_offre += x["n"] * part
        emplois_demande += x["n"] * demande
        travail += x["n"] * (part + heures + demande) * x["cout"]
    prl = statique_openfisca(p, nom)["prelevements_en_moins"]
    if abs(prl) < 1e-3:
        return {"pib_pct": 0.0, "emplois": 0.0, "emplois_demande": 0.0}
    points = prl * 1e9 / (0.01 * y29 * 1e9)
    pct = sq._v(p, "offre.travail_part_pib", s) * travail / masse * 100
    return {"pib_pct": pct / points, "emplois": emplois_offre / points, "emplois_demande": emplois_demande / points,
            "prelevements_en_moins_md": prl}


def capital_entreprises_par_point(p: Parametres, s: str) -> float:
    """Effet de long terme sur le PIB (%) d'1 point de PIB d'impôt sur les entreprises en moins, avec l'élasticité de
    l'investissement au coût du capital des cohortes d'entreprises (macro.elasticite_invest)."""
    rec = sq.recettes_par_impot(p, s)[2029]
    y29 = sq.pib(p, s)[2029]
    tau, z = 0.25, p.val("is_investissement.valeur_actuelle_amortissements")
    dtau = tau / (rec["impot_sur_les_societes"] / y29 * 100)  # baisse du taux pour 1 point de PIB
    cc = (1 - tau * z) / (1 - tau)
    cc2 = (1 - (tau - dtau) * z) / (1 - (tau - dtau))
    dk = sq._v(p, "macro.elasticite_invest", s) * (1 - cc2 / cc)
    return p.val("offre.part_capital") * dk * 100


# ------------------------------------------------------------------------------------------------ offre : ensemble
def effets(p: Parametres, s: str, mesures: list[Mesure], annees_avant=(2027, 2028)) -> dict:
    """Effets d'offre d'une liste de mesures dans le scénario s.

    Renvoie dpib {année: Md€}, recettes (Mesure, effet_macro), emplois {canal: {année: personnes}}, actifs en plus
    {année: personnes} (emplois venus de l'inactivité), et le détail par instrument (points de PIB, effet sur le PIB)."""
    y = sq.pib(p, s)
    rec = sq.recettes(p, s)
    e = sq.effectifs(p, s)
    annees = (*annees_avant, *ANNEES)
    cles = {}
    for m in mesures:
        instrument = m.instrument or ("investissement_public" if (m.poste == "investissement" and m.nature == "mesure") else "")
        if not instrument:
            continue
        if instrument not in INSTRUMENTS:
            raise ValueError(f"Mesure « {m.nom} » : instrument inconnu {instrument}")
        inc = (m.incidence or "proportionnel") if instrument == "travail" else ""
        part = 1.0
        if "@" in inc:  # « réforme@part » : seule cette part du montant porte sur les revenus du travail
            inc, x = inc.split("@", 1)
            part = float(x)
        cle = (instrument, inc)
        cles.setdefault(cle, {t: 0.0 for t in annees})
        # recette en plus ou transfert en plus : contre l'offre (points < 0) ; investissement public en plus : pour
        signe = 1.0 if instrument in ("investissement_public", "education", "recherche") else -1.0
        for t in annees:
            cles[cle][t] += signe * part * m.valeurs.get(t, 0.0) / y[max(t, 2029)] * 100
    vit = sq._v(p, "offre.vitesse", s)
    out = {"dpib": {t: 0.0 for t in annees}, "emplois": {}, "actifs": {t: 0.0 for t in ANNEES}, "detail": {}}
    # PIB en plus qui vient de la productivité (capital, éducation, recherche ; hors part d'emploi) : il rapporte au
    # solde le dividende de productivité du statu quo, pas la part des recettes (relecture neutre n° 2, point 1)
    dpib_productivite = {t: 0.0 for t in annees}
    for (i, inc), pts in cles.items():
        if not any(pts.values()):
            continue
        el = {}

        def elasticite(sc):
            if i == "travail":
                x = travail_par_point(p, sc, inc)
                return x["pib_pct"], x["emplois"], x.get("emplois_demande", 0.0)
            if i == "capital_entreprises":
                return capital_entreprises_par_point(p, sc), None
            return sq._v(p, f"offre.elasticite_{i}", sc), None
        effet, emp, emp_d, cumul, cumul_e, cumul_d = {}, {}, {}, 0.0, 0.0, 0.0
        if i in ("education", "recherche"):
            # dépense publique d'éducation ou de recherche en plus : effet durable de long terme, sans emploi direct
            effet = (education if i == "education" else recherche)(p, s, pts, annees)
            for t in annees:
                out["dpib"][t] += effet[t] / 100 * y[max(t, 2029)]
                dpib_productivite[t] += effet[t] / 100 * y[max(t, 2029)]
            out["detail"][i] = {"points_pib": pts, "effet_pib_pct": effet}
            continue
        el = {sc: elasticite(sc) for sc in {s, MIROIR[s]}}
        for t in annees:
            sc = s if pts[t] >= 0 else MIROIR[s]
            cumul += vit * (el[sc][0] * pts[t] - cumul)
            effet[t] = cumul
            if i == "travail":
                cumul_e += vit * (el[sc][1] * pts[t] - cumul_e)
                cumul_d += vit * (el[sc][2] * pts[t] - cumul_d)
                emp[t], emp_d[t] = cumul_e, cumul_d
        part_emploi, part_inactifs = EMPLOI[i]
        for t in annees:
            out["dpib"][t] += effet[t] / 100 * y[max(t, 2029)]
            if i in PRODUCTIVITE:
                dpib_productivite[t] += (1 - (part_emploi or 0.0)) * effet[t] / 100 * y[max(t, 2029)]
        if i == "travail":
            serie = {t: emp[t] * e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}
            dem = {t: emp_d[t] * e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}
            if any(abs(v) > 1 for v in dem.values()):
                canal = f"Offre : coût du travail ({inc.split(':', 1)[-1]})"
                prec = out["emplois"].get(canal, {t: 0.0 for t in ANNEES})
                out["emplois"][canal] = {t: prec[t] + dem[t] for t in ANNEES}  # pris sur le chômage
        elif part_emploi:
            serie = {t: part_emploi * effet[t] / 100 * e[t]["emploi"] for t in ANNEES}
        else:
            serie = None
        nom = LIBELLES[i] + (f" ({inc})" if inc and inc != "proportionnel" else "")
        if serie:
            canal = f"Offre : {nom}"
            prec = out["emplois"].get(canal, {t: 0.0 for t in ANNEES})
            out["emplois"][canal] = {t: prec[t] + serie[t] for t in ANNEES}
            for t in ANNEES:
                out["actifs"][t] += part_inactifs * serie[t]
        out["detail"][f"{i}:{inc}" if inc else i] = {"points_pib": pts, "effet_pib_pct": effet}
    part_rec = {t: rec[max(t, 2029)] / y[max(t, 2029)] for t in annees}
    div = sq.dividende_productivite(p, s)
    out["mesure"] = Mesure("Effet d'offre : impôts et transferts, effet durable sur le PIB (canal commun)", "recettes",
                           {t: (out["dpib"][t] - dpib_productivite[t]) * part_rec[t]
                            + dpib_productivite[t] * div[max(t, 2029)] for t in annees}, nature="effet_macro")
    return out


# ------------------------------------------------------------------------------------------------ long terme
def recherche(p: Parametres, s: str, pts: dict[int, float], annees) -> dict[int, float]:
    """Effet durable de la recherche publique en plus (% du PIB, phase 2 du 11/11/2026) : la dépense en plus forme
    un stock de connaissances (amorti de `depreciation` par an) qui rapporte, après `delai` ans, `rendement` par an
    de PIB. Une baisse prend le scénario miroir. pts : dépense en points de PIB du statu quo."""
    c = p.val("offre.recherche")
    y = sq.pib(p, s)
    d, k = c["depreciation"], int(c["delai"])
    stock, out = 0.0, {}
    for t in annees:
        v = pts.get(t - k, 0.0)
        stock = (1 - d) * stock + v / 100 * y[max(t - k, 2029)]
        sc = s if stock >= 0 else MIROIR[s]
        out[t] = c["rendement"][sc] * stock / y[max(t, 2029)] * 100
    return out


def education(p: Parametres, s: str, pts: dict[int, float], annees) -> dict[int, float]:
    """Effet durable de la dépense d'éducation en plus (% du PIB, phase 2 du 11/11/2026), par le capital humain des
    générations scolarisées pendant la hausse : `gain_par_10pct` de salaire pour 10 % de dépense par élève en plus,
    en moyenne sur les années d'école (Jackson et Mackevicius, 2021 ; Jackson, Johnson et Persico, 2016). Effet sur le
    PIB = part du travail × gain moyen des actifs, à mesure que ces générations entrent sur le marché du travail.
    Une baisse prend le scénario miroir."""
    c = p.val("offre.education")
    y = sq.pib(p, s)
    a0, a1 = c["age_scolaire"]
    b0, b1 = c["age_actif"]
    # part de dépense en plus par élève : dépense en plus / dépense publique d'éducation (qui suit le PIB)
    sigma = {t: pts.get(t, 0.0) / 100 * y[2029] / c["base_md"] for t in annees}
    out = {}
    for t in annees:
        tot = 0.0
        for a in range(b0, b1 + 1):
            ecole = [sigma.get(t - a + x, 0.0) for x in range(a0, a1 + 1)]
            m = sum(ecole) / len(ecole)
            sc = s if m >= 0 else MIROIR[s]
            tot += c["gain_par_10pct"][sc] / 100 * m / 0.10
        out[t] = c["part_travail"] * tot / (b1 - b0 + 1) * 100
    return out


# ------------------------------------------------------------------------------------------------ seniors
def seniors(p: Parametres, s: str, non_retraites: dict[int, float], baisse_age: bool = False) -> dict:
    """Personnes de plus (ou de moins) qui ne sont pas encore retraitées quand l'âge de la retraite change : une part
    reste en emploi, une part au chômage, le reste inactif (seniors.devenir). Renvoie les emplois, les chômeurs, les
    actifs en plus, les mesures budgétaires (prélèvements, allocations, autres prestations) et la valeur ajoutée (Md€)."""
    sc = MIROIR[s] if baisse_age else s
    pe, pc = sq._v(p, "seniors.devenir", sc)
    k_c = p.val("seniors.part_concernee")  # calé sur l'étude d'impact de la réforme de 2023
    non_retraites = {t: k_c * v for t, v in non_retraites.items()}
    w = sq.salaires(p, s)
    k = {t: w[t] / w[2029] for t in ANNEES}
    em = {t: pe * non_retraites[t] for t in ANNEES}
    ch = {t: pc * non_retraites[t] for t in ANNEES}
    ina = {t: (1 - pe - pc) * non_retraites[t] for t in ANNEES}
    v, a, c, va = (p.val("seniors.valeur_emploi"), p.val("seniors.allocation_chomage"), p.val("seniors.cout_inactif"),
                   p.val("seniors.valeur_ajoutee_emploi"))
    mesures = [
        Mesure("Seniors : prélèvements des emplois en plus (âge de la retraite)", "recettes",
               {t: em[t] * v * k[t] / 1e9 for t in ANNEES}, nature="effet_macro"),
        Mesure("Seniors : allocations chômage en plus (âge de la retraite)", "chomage",
               {t: ch[t] * a * k[t] / 1e9 for t in ANNEES}, nature="effet_macro"),
        Mesure("Seniors : invalidité et minima sociaux en plus (âge de la retraite)", "aah_invalidite",
               {t: ina[t] * c * k[t] / 1e9 for t in ANNEES}, nature="effet_macro"),
    ]
    return {"emplois": em, "chomeurs": ch, "actifs": {t: em[t] + ch[t] for t in ANNEES}, "mesures": mesures,
            "pib": {t: em[t] * va * k[t] / 1e9 for t in ANNEES}}
