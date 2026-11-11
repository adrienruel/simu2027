"""Canaux déclarés par un programme, ouverts à tous (DÉCISION d'Adrien du 12/11/2026, relecture indépendante).

Jusqu'ici, seul « Écologie de droite » comptait des effets propres hors du tronc commun (fraude à la TVA, productivité,
adoption de l'IA, niveau des élèves, baisse de l'écart de taux) et une règle de trajectoire ; les autres programmes
n'avaient droit qu'à leurs mesures. Tout programme peut maintenant déclarer les mêmes canaux, avec les mêmes formules,
dans son parametres.yaml (groupe `<nom>_canaux`). Rien n'est supposé : un canal absent vaut zéro, et chaque valeur
porte un statut et une source comme tout paramètre.

    <nom>_canaux:
      fraude_tva:        {valeur: {montant: {crise: 0, prudent: 1, median: 2, optimiste: 3}, debut: 2029, montee: 5}, ...}
      productivite:      {valeur: {taux: {par scénario : gain annuel}, debut: 2030, annees: 10}, ...}
      adoption_ia:       {valeur: {part: {par scénario : part du gain de l'IA en plus du statu quo}}, ...}
      ecole:             {valeur: {niveau_eleves: {par scénario : écart-type}, debut: 2045, annees: 40}, ...}
      baisse_ecart_taux: {valeur: {baisse: {par scénario : points de taux, en fraction}, annees: 8}, ...}
      regle_trajectoire: {valeur: {cible: 0.03, derniere_annee: 2073, scenarios: [crise, prudent, median, optimiste],
                                   leviers: [{nom: "…", poste: recettes, capacite_pib: 0.01}]}, ...}

Formules (celles d'Écologie de droite, programmes/ecologie_de_droite/effets.py) :
- fraude à la TVA : recette en Md€ de 2026, montée linéaire ;
- productivité : PIB du statu quo × ((1 + taux)^années écoulées − 1), années plafonnées ;
- adoption de l'IA : gain de productivité de l'IA du statu quo (macro.ia_productivite) × part, cumulé ;
- école : niveau des élèves × macro.croissance_par_ecart_type, monté linéairement, cumulé ;
- le PIB en plus rapporte la part des recettes dans le PIB du statu quo (règle du canal d'offre commun) ;
- baisse de l'écart de taux : retirée du taux de la dette, montée linéaire ;
- règle de trajectoire : celle du noyau (moteur/noyau.Regle) ; chaque levier a une capacité en part du PIB et porte
  sur les recettes (hausse) ou sur un bloc de dépenses (baisse). Les comptes sont publiés avec et sans la règle.

Ces effets ne passent pas par le multiplicateur (comme ceux d'Écologie de droite) ; ils sont publiés à part, sous le
nom « Canal déclaré : … », pour qu'un lecteur puisse les retirer.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES, Levier, Mesure, Regle
from .parametres import Parametres

CANAUX = ("fraude_tva", "productivite", "adoption_ia", "ecole", "baisse_ecart_taux", "regle_trajectoire")


def declares(prog) -> dict:
    """Canaux déclarés par le programme : {nom: valeur du paramètre}. Un nom inconnu est une erreur."""
    prefixe = f"{prog.nom}_canaux."
    out = {}
    for cle, par in prog.pt._p.items():
        if cle.startswith(prefixe):
            nom = cle[len(prefixe):]
            if nom not in CANAUX:
                raise ValueError(f"Canal déclaré inconnu : {cle} (canaux : {', '.join(CANAUX)})")
            out[nom] = par.valeur
    return out


def _montee(t: int, debut: int, annees: float) -> float:
    return max(0.0, min(1.0, (t - debut + 1) / annees)) if annees else float(t >= debut)


def effets(prog, p: Parametres, s: str) -> dict:
    """Mesures de recettes, PIB en plus (Md€) et écart de taux des canaux déclarés, dans le scénario s."""
    d = declares(prog)
    y, rec = sq.pib(p, s), sq.recettes(p, s)
    part_rec = {t: rec[t] / y[t] for t in ANNEES}
    pib = {t: 0.0 for t in ANNEES}
    mesures: list[Mesure] = []

    def ajouter(nom: str, serie_pib: dict[int, float]) -> None:
        for t in ANNEES:
            pib[t] += serie_pib[t]
        mesures.append(Mesure(f"Canal déclaré : {nom}", "recettes", {t: serie_pib[t] * part_rec[t] for t in ANNEES}, "effet_macro"))

    if "fraude_tva" in d:
        x = d["fraude_tva"]
        mesures.append(Mesure("Canal déclaré : fraude à la TVA", "recettes",
                              {t: x["montant"][s] * _montee(t, x.get("debut", 2029), x.get("montee", 1)) for t in ANNEES}, "effet_macro"))
    if "productivite" in d:
        x = d["productivite"]
        ajouter("productivité", {t: y[t] * ((1 + x["taux"][s]) ** max(0, min(x["annees"], t - x["debut"] + 1)) - 1) for t in ANNEES})
    if "adoption_ia" in d:
        g, debut, duree = sq._v(p, "macro.ia_productivite", s), p.val("macro.premiere_annee_ia"), p.val("macro.annees_ia")
        r, serie = 0.0, {}
        for t in ANNEES:
            r = (1 + r) * (1 + g * (debut <= t < debut + duree) * d["adoption_ia"]["part"][s]) - 1
            serie[t] = y[t] * r
        ajouter("adoption de l'IA", serie)
    if "ecole" in d:
        x = d["ecole"]
        k = sq._v(p, "macro.croissance_par_ecart_type", s)
        r, serie = 0.0, {}
        for t in ANNEES:
            r = (1 + r) * (1 + x["niveau_eleves"][s] * k * _montee(t, x["debut"], x["annees"])) - 1
            serie[t] = y[t] * r
        ajouter("école (niveau des élèves)", serie)
    taux = None
    if "baisse_ecart_taux" in d:
        x = d["baisse_ecart_taux"]
        taux = {t: -x["baisse"][s] * min(1.0, max(0, t - 2029) / x["annees"]) for t in ANNEES}
    return {"mesures": mesures, "pib": pib, "taux_supplementaire": taux}


def regle(prog, p: Parametres, s: str) -> Regle | None:
    """Règle de trajectoire déclarée (objet neuf à chaque appel : la règle garde un état), ou None."""
    x = declares(prog).get("regle_trajectoire")
    if not x or s not in x.get("scenarios", sq.SCENARIOS):
        return None
    leviers = []
    for lv in x["leviers"]:
        cap, poste = lv["capacite_pib"], lv.get("poste", "recettes")
        ecritures = None if poste == "recettes" else (lambda t, v, poste=poste: [(poste, -v)])
        leviers.append(Levier(lv["nom"], lambda t, etat, cap=cap: cap * etat["pib"][t], 1.0, ecritures))
    return Regle(x["cible"], leviers, int(x.get("derniere_annee", ANNEES[-1])))
