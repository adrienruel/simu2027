"""Canal d'offre commun : effets de long terme des impôts et des transferts sur le PIB (6 novembre 2026).

Le multiplicateur commun ne compte que la demande : l'effet d'une baisse d'impôt s'efface en quelques années. Ce module
ajoute ce qu'elle change durablement à l'offre (travail, capital), instrument par instrument, avec les élasticités de
parametres/commun/economie.yaml (groupe offre) :

- chaque mesure porte un instrument (Mesure.instrument) ; le canal additionne, année par année, le prélèvement en
  moins (recettes : −montant) ou le transfert aux actifs en moins (dépense : −montant), en points du PIB du statu quo ;
- l'effet de long terme sur le PIB (%) = élasticité de l'instrument × ces points ; l'élasticité est celle du scénario
  quand l'instrument joue pour le programme, celle du scénario miroir quand il joue contre (prudent ↔ médian,
  crise ↔ optimiste), comme l'éviction des postes publics supprimés ;
- le PIB rejoint cet effet par ajustement partiel (offre.vitesse, ≈ 10 % de l'écart par an, profil de Mésange), à
  partir de 2027 ;
- recettes : le PIB en plus rapporte la part des recettes dans le PIB du statu quo (même règle que le multiplicateur) ;
- emplois : part de l'effet sur le PIB selon l'instrument ; ceux qui viennent de l'inactivité (offre de travail)
  s'ajoutent aussi aux actifs, sans changer le chômage ; les autres sont pris sur le chômage.

Le canal ne remplace pas les effets propres déjà comptés par un programme (SMIC, assurance chômage de Tondelier,
moteur d'Écologie de droite) : ces mesures ne portent pas d'instrument.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES, Mesure
from .parametres import Parametres

INSTRUMENTS = ("travail", "cout_travail", "capital_entreprises", "capital_menages", "successions", "consommation",
               "transferts_actifs")
LIBELLES = {"travail": "prélèvements sur le travail", "cout_travail": "coût du travail",
            "capital_entreprises": "fiscalité des entreprises", "capital_menages": "fiscalité du capital des ménages",
            "successions": "successions", "consommation": "TVA et accises", "transferts_actifs": "transferts aux actifs"}
# part de l'effet sur le PIB qui est de l'emploi, et part de ces emplois qui vient de l'inactivité (le reste : chômage)
EMPLOI = {"travail": (1.0, 1.0), "cout_travail": (1.0, 0.0), "capital_entreprises": (0.3, 0.0),
          "capital_menages": (0.0, 0.0), "successions": (0.0, 0.0), "consommation": (0.5, 0.0),
          "transferts_actifs": (1.0, 1.0)}
MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}


def actif(p: Parametres) -> bool:
    return bool(p.val("offre.actif"))


def effets(p: Parametres, s: str, mesures: list[Mesure], annees_avant=(2027, 2028)) -> dict:
    """Effets d'offre d'une liste de mesures dans le scénario s.

    Renvoie dpib {année: Md€}, recettes (Mesure, effet_macro), emplois {canal: {année: personnes}}, actifs en plus
    {année: personnes} (emplois venus de l'inactivité), et le détail par instrument (points de PIB, effet visé)."""
    y = sq.pib(p, s)
    rec = sq.recettes(p, s)
    e = sq.effectifs(p, s)
    annees = (*annees_avant, *ANNEES)
    pts = {i: {t: 0.0 for t in annees} for i in INSTRUMENTS}
    for m in mesures:
        if not m.instrument:
            continue
        if m.instrument not in INSTRUMENTS:
            raise ValueError(f"Mesure « {m.nom} » : instrument inconnu {m.instrument}")
        for t in annees:  # recette en plus ou transfert en plus : contre l'offre (points < 0)
            pts[m.instrument][t] -= m.valeurs.get(t, 0.0) / y[max(t, 2029)] * 100
    vit = sq._v(p, "offre.vitesse", s)
    out = {"dpib": {t: 0.0 for t in annees}, "emplois": {}, "actifs": {t: 0.0 for t in ANNEES}, "detail": {}}
    for i in INSTRUMENTS:
        if not any(pts[i].values()):
            continue
        cle = f"offre.elasticite_{i}"
        effet, cumul = {}, 0.0
        for t in annees:
            el = sq._v(p, cle, s if pts[i][t] >= 0 else MIROIR[s])
            cible = el * pts[i][t]  # % de PIB à long terme
            cumul += vit * (cible - cumul)
            effet[t] = cumul
        part_emploi, part_inactifs = EMPLOI[i]
        for t in annees:
            out["dpib"][t] += effet[t] / 100 * y[max(t, 2029)]
        if part_emploi:
            serie = {t: part_emploi * effet[t] / 100 * e[t]["emploi"] for t in ANNEES}
            out["emplois"][f"Offre : {LIBELLES[i]}"] = serie
            for t in ANNEES:
                out["actifs"][t] += part_inactifs * serie[t]
        out["detail"][i] = {"points_pib": pts[i], "effet_pib_pct": effet}
    part_rec = {t: rec[max(t, 2029)] / y[max(t, 2029)] for t in annees}
    out["mesure"] = Mesure("Effet d'offre : impôts et transferts, effet durable sur le PIB (canal commun)", "recettes",
                           {t: out["dpib"][t] * part_rec[t] for t in annees}, nature="effet_macro")
    return out
