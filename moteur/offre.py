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
  (allègements), « plafond » : salaire au-delà du plafond de la Sécurité sociale) ; chaque cellule réagit au revenu net en plus
  avec l'élasticité de participation de sa tranche (plus forte en bas) et celle des heures ; effet sur le PIB = travail
  en plus pondéré par le coût × part du travail ;
- **entreprises** : même élasticité de l'investissement au coût du capital que les cohortes d'entreprises
  (macro.elasticite_invest) ; effet = part du capital × capital en plus ;
- **autres instruments** : élasticités de long terme de offre.* (coût du travail : Mésange ; capital des ménages,
  successions, consommation, transferts aux actifs) ;
- quand l'instrument joue pour le programme (baisse), l'élasticité du scénario ; quand il joue contre (hausse),
  celle du scénario miroir (crise ↔ optimiste, prudent ↔ médian) ;
- montée par ajustement partiel (offre.vitesse, ≈ 10 % de l'écart par an, profil de Mésange), à partir de 2027 ;
- recettes : le PIB en plus rapporte la part des recettes dans le PIB du statu quo ;
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
               "transferts_actifs")
INCIDENCES = ("proportionnel", "ir", "bas", "haut", "milieu", "plafond")
LIBELLES = {"travail": "prélèvements sur le travail", "cout_travail": "coût du travail",
            "capital_entreprises": "fiscalité des entreprises", "capital_menages": "fiscalité du capital des ménages",
            "successions": "successions", "consommation": "TVA et accises", "transferts_actifs": "transferts aux actifs"}
# part de l'effet sur le PIB qui est de l'emploi (hors travail, calculé par cellule), et part de ces emplois qui vient
# de l'inactivité (le reste : chômage)
EMPLOI = {"travail": (None, 1.0), "cout_travail": (1.0, 0.0), "capital_entreprises": (0.3, 0.0),
          "capital_menages": (0.0, 0.0), "successions": (0.0, 0.0), "consommation": (0.5, 0.0),
          "transferts_actifs": (1.0, 1.0)}
MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}
TRANSFERTS_CIBLES = ("famille", "logement", "pauvrete", "chomage", "aah_invalidite")
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


def travail_par_point(p: Parametres, s: str, incidence: str = "proportionnel") -> dict:
    """Effet de long terme d'1 point de PIB (de 2029) de prélèvement sur le travail en moins, réparti selon
    l'incidence : % de PIB et emplois (personnes) en plus."""
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
        if not m.instrument:
            continue
        if m.instrument not in INSTRUMENTS:
            raise ValueError(f"Mesure « {m.nom} » : instrument inconnu {m.instrument}")
        inc = (m.incidence or "proportionnel") if m.instrument == "travail" else ""
        cle = (m.instrument, inc)
        cles.setdefault(cle, {t: 0.0 for t in annees})
        for t in annees:  # recette en plus ou transfert en plus : contre l'offre (points < 0)
            cles[cle][t] -= m.valeurs.get(t, 0.0) / y[max(t, 2029)] * 100
    vit = sq._v(p, "offre.vitesse", s)
    out = {"dpib": {t: 0.0 for t in annees}, "emplois": {}, "actifs": {t: 0.0 for t in ANNEES}, "detail": {}}
    for (i, inc), pts in cles.items():
        if not any(pts.values()):
            continue

        def elasticite(sc):
            if i == "travail":
                x = travail_par_point(p, sc, inc)
                return x["pib_pct"], x["emplois"]
            if i == "capital_entreprises":
                return capital_entreprises_par_point(p, sc), None
            return sq._v(p, f"offre.elasticite_{i}", sc), None
        el = {sc: elasticite(sc) for sc in {s, MIROIR[s]}}
        effet, emp, cumul, cumul_e = {}, {}, 0.0, 0.0
        for t in annees:
            sc = s if pts[t] >= 0 else MIROIR[s]
            cumul += vit * (el[sc][0] * pts[t] - cumul)
            effet[t] = cumul
            if i == "travail":
                cumul_e += vit * (el[sc][1] * pts[t] - cumul_e)
                emp[t] = cumul_e
        for t in annees:
            out["dpib"][t] += effet[t] / 100 * y[max(t, 2029)]
        part_emploi, part_inactifs = EMPLOI[i]
        if i == "travail":
            serie = {t: emp[t] * e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}
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
    out["mesure"] = Mesure("Effet d'offre : impôts et transferts, effet durable sur le PIB (canal commun)", "recettes",
                           {t: out["dpib"][t] * part_rec[t] for t in annees}, nature="effet_macro")
    return out


# ------------------------------------------------------------------------------------------------ seniors
def seniors(p: Parametres, s: str, non_retraites: dict[int, float], baisse_age: bool = False) -> dict:
    """Personnes de plus (ou de moins) qui ne sont pas encore retraitées quand l'âge de la retraite change : une part
    reste en emploi, une part au chômage, le reste inactif (seniors.devenir). Renvoie les emplois, les chômeurs, les
    actifs en plus, les mesures budgétaires (prélèvements, allocations, autres prestations) et la valeur ajoutée (Md€)."""
    sc = MIROIR[s] if baisse_age else s
    pe, pc = sq._v(p, "seniors.devenir", sc)
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
