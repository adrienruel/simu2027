"""Nouveau nucléaire : canal commun à tous les programmes (27/11/2026, demande d'Adrien).

« Pour ceux qui ne disent rien, il faut intégrer les nouveaux EPR qui vont être livrés, avec la conséquence sur le prix
de l'électricité et la décarbonation. »

Statu quo : les six EPR2 décidés (nucleaire.epr2.nombre_statu_quo), au calendrier du scénario, avec leur coût pour
l'État (moteur/statu_quo.blocs, bloc etat_missions) :
- bonification du prêt du fonds d'épargne (60 % du coût) : encours × taux de la ressource pendant le chantier, puis
  une part de ce taux après la mise en service, jusqu'au remboursement ;
- contrat pour différence : (prix d'exercice − prix de marché) × production, pendant 40 ans.
Le prêt vient du fonds d'épargne de la Caisse des dépôts, hors des administrations publiques : il n'entre pas dans la
dette publique ; seule la bonification et le contrat passent au solde.

Un programme déclare son parc (`<nom>_canaux.nucleaire`, moteur/canaux_declares.py) :

    nucleaire: {valeur: {epr: 14, prolongation: true}}          # 14 EPR2 en tout d'ici 2050, parc prolongé > 60 ans
    nucleaire: {valeur: {epr: 0, sortie: acceleree}}             # aucun EPR2, sortie avant 2050

Écarts au statu quo :
- budget : bonification et contrat de son parc moins ceux du statu quo (mêmes règles, mêmes prix) ;
- prix de l'électricité : coût complet du système électrique de RTE (Futurs énergétiques 2050) pour son parc,
  rapporté à celui du statu quo, monté linéairement de 2035 à 2060 ;
- décarbonation : électrification des transports et des bâtiments quand l'électricité est moins chère
  (ecologie.elasticite_croisee_electricite), comme pour le prix du carbone (emissions.reponse_ratio).
Un programme qui ne déclare rien a le parc du statu quo : aucun écart.
"""
from __future__ import annotations

from .statu_quo import ANNEES
from .parametres import Parametres

SORTIES = ("aucune", "60_ans", "acceleree")


def _s(p: Parametres, s: str) -> str:
    from .ecologie.emissions import scenario
    return scenario(p, s)


def calendrier(p: Parametres, s: str, n: int) -> list[float]:
    """Année de mise en service de chacun des n réacteurs (fractionnaire : la cadence est en années)."""
    e = p.val("nucleaire.epr2")
    s = _s(p, s)
    return [e["premiere"][s] + i * e["cadence_ans"][s] for i in range(n)]


def production_twh(p: Parametres, s: str, n: int) -> dict[int, float]:
    """Production des n réacteurs, TWh par an (part de l'année en service la première année)."""
    e = p.val("nucleaire.epr2")
    un = e["puissance_gw"] * 8.76 * e["facteur_charge"]
    out = {t: 0.0 for t in ANNEES}
    for m in calendrier(p, s, n):
        for t in ANNEES:
            out[t] += un * min(1.0, max(0.0, t + 1 - m))
    return out


def budget(p: Parametres, s: str, n: int) -> dict[str, dict[int, float]]:
    """Coût pour l'État du parc de n réacteurs, Md€ de 2026 par an : {"bonification", "contrat", "total"}."""
    e, pr, cfd = p.val("nucleaire.epr2"), p.val("nucleaire.pret"), p.val("nucleaire.contrat_difference")
    s = _s(p, s)
    cout = p["nucleaire.cout_reacteur_md"].pour(s)
    un = e["puissance_gw"] * 8.76 * e["facteur_charge"]
    bon = {t: 0.0 for t in ANNEES}
    con = {t: 0.0 for t in ANNEES}
    cal = calendrier(p, s, n)
    for i, m in enumerate(cal):
        # décaissement linéaire du début du financement à la mise en service ; réacteurs en plus du statu quo :
        # décidés après l'élection
        debut = e["debut_financement"] if i < e["nombre_statu_quo"] else e["debut_supplementaires"]
        for t in ANNEES:
            milieu = t + 0.5
            if milieu < m:
                # chantier : décaissements linéaires, encours croissant, taux nul pour EDF
                encours = pr["part"] * cout * min(1.0, max(0.0, (milieu - debut) / (m - debut)))
                bon[t] += encours * pr["taux_ressource"]
            else:
                ecoule = milieu - m
                encours = pr["part"] * cout * max(0.0, 1 - ecoule / pr["duree_remboursement"])
                bon[t] += encours * pr["taux_ressource"] * pr["bonification_apres"][s]
                if ecoule < cfd["duree"]:
                    en_service = min(1.0, max(0.0, t + 1 - m))
                    con[t] += un * en_service * (cfd["prix_exercice"] - cfd["prix_marche"][s]) / 1000
    return {"bonification": bon, "contrat": con, "total": {t: bon[t] + con[t] for t in ANNEES}}


def statu_quo(p: Parametres, s: str) -> dict[int, float]:
    """Coût pour l'État des EPR2 du statu quo (Md€ de 2026), mémorisé."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("nucleaire_statu_quo", _s(p, s))
    if cle not in cache:
        cache[cle] = budget(p, s, int(p.val("nucleaire.epr2")["nombre_statu_quo"]))["total"]
    return cache[cle]


def cout_systeme(p: Parametres, decl: dict | None) -> float:
    """Coût complet annualisé du système électrique en 2060 (Md€ de 2020, RTE) pour un parc déclaré (None : statu quo).
    Lecture commune : sans nouveau réacteur, moyenne de M1 et M23 ; 8 EPR2 : N1 ; 14 : N2 ; linéaire entre ; 14 ou plus
    avec un parc prolongé au-delà de 60 ans : N03 ; jamais sous N03 ; sortie avant 2050 : M0."""
    c = p.val("nucleaire.couts_systeme_rte")
    d = decl or {}
    n = float(d.get("epr", p.val("nucleaire.epr2")["nombre_statu_quo"]))
    sortie = d.get("sortie", "aucune")
    if sortie not in SORTIES:
        raise ValueError(f"nucleaire.sortie inconnue : {sortie} ({', '.join(SORTIES)})")
    if sortie == "acceleree":
        return float(c["M0"])
    zero = (c["M1"] + c["M23"]) / 2
    if n <= 8:
        v = zero + (c["N1"] - zero) * n / 8
    else:
        v = c["N1"] + (c["N2"] - c["N1"]) * (n - 8) / 6
    if d.get("prolongation") and n >= 14:
        v = c["N03"]
    return max(float(c["N03"]), v)


def ratio_prix(p: Parametres, decl: dict | None) -> dict[int, float]:
    """Prix de l'électricité du programme rapporté à celui du statu quo, année par année (1 avant 2035, plein en 2060)."""
    r = cout_systeme(p, decl) / cout_systeme(p, None)
    e = p.val("nucleaire.electrification")
    a0, a1 = int(e["debut"]), int(e["plein"])
    return {t: 1 + (r - 1) * min(1.0, max(0.0, (t - a0 + 1) / (a1 - a0 + 1))) for t in ANNEES}


def effets(p: Parametres, s: str, decl: dict) -> dict:
    """Écarts au statu quo d'un parc déclaré : {"budget": {année: Md€, + = dépense en plus}, "emissions":
    {secteur: {année: Mt}}, "ratio_prix": {année: ratio}, "epr": n}."""
    from .ecologie import emissions as em
    n = int(decl.get("epr", p.val("nucleaire.epr2")["nombre_statu_quo"]))
    if decl.get("sortie", "aucune") != "aucune" and n:
        raise ValueError("nucleaire : une sortie du nucléaire ne construit pas d'EPR2 (epr: 0)")
    b, b0 = budget(p, s, n)["total"], statu_quo(p, s)
    ratio = ratio_prix(p, decl)
    e = p.val("nucleaire.electrification")
    facteur = em.reponse_ratio(p, {t: 1.0 for t in ANNEES}, s, ratio_electricite=ratio, debut=int(e["debut"]))
    terr = em.territoriales(p, em.scenario(p, s))
    emis = {sec: {t: terr[t][sec] * (facteur[t] - 1) for t in ANNEES} for sec in e["secteurs"]}
    # coût du système électrique en plus (Md€ de 2026, + = plus cher), payé par les ménages et les entreprises : canal
    # du prix de l'électricité vers l'activité (27/11/2026, décision d'Adrien ; moteur/bouclage.facture_electricite)
    c0 = cout_systeme(p, None) * p.val("nucleaire.euros_2020_en_2026")
    facture = {t: (ratio[t] - 1) * c0 for t in ANNEES}
    return {"budget": {t: b[t] - b0[t] for t in ANNEES}, "emissions": emis, "ratio_prix": ratio, "epr": n,
            "facture_electricite": facture}
