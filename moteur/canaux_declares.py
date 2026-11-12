"""Canaux déclarés par un programme, ouverts à tous (DÉCISION d'Adrien du 12/11/2026, relecture indépendante).

Jusqu'ici, seul « Écologie de droite » comptait des effets propres hors du tronc commun (fraude à la TVA, productivité,
adoption de l'IA, niveau des élèves, baisse de l'écart de taux) et une règle de trajectoire ; les autres programmes
n'avaient droit qu'à leurs mesures. Tout programme peut maintenant déclarer les mêmes canaux, avec les mêmes formules,
dans son parametres.yaml (groupe `<nom>_canaux`). Rien n'est supposé : un canal absent vaut zéro, et chaque valeur
porte un statut et une source comme tout paramètre.

    <nom>_canaux:
      fraude_tva:        {valeur: {montant: {crise: 0, prudent: 1, median: 2, optimiste: 3}, debut: 2029, montee: 5}, ...}
      productivite:      {valeur: {taux: {par scénario : gain annuel}, debut: 2030, annees: 10}, ...}
      reformes_structurelles: {valeur: {pmr: 1.0, epl: 0.5, debut: 2028}, ...}   (barème commun, 12/11/2026)
      adoption_ia:       {valeur: {part: {par scénario : part du gain de l'IA en plus du statu quo}}, ...}
      ecole:             {valeur: {niveau_eleves: {par scénario : écart-type}, debut: 2045, annees: 40}, ...}
      regle_trajectoire: {valeur: {cible: 0.03, derniere_annee: 2073, scenarios: [crise, prudent, median, optimiste],
                                   leviers: [{nom: "…", poste: recettes, capacite_pib: 0.01}]}, ...}

Formules (celles d'Écologie de droite, programmes/ecologie_de_droite/effets.py) :
- fraude à la TVA : recette en Md€ de 2026, montée linéaire ;
- productivité : PIB du statu quo × ((1 + taux)^années écoulées − 1), années plafonnées ;
- réformes de structure : barème commun de l'OCDE (moteur/reformes_structurelles.py), nombre de réformes typiques
  déclarées par domaine (marchés de produits, protection de l'emploi) ; c'est la façon commune de compter les gains de
  productivité des réformes (le canal « productivite » libre n'est plus utilisé par aucun programme) ;
- adoption de l'IA : gain de productivité de l'IA du statu quo (macro.ia_productivite) × part, cumulé ;
- école : niveau des élèves × macro.croissance_par_ecart_type, monté linéairement, cumulé ;
- le PIB en plus rapporte au solde le dividende de productivité du statu quo (statu_quo.dividende_programme, sur le profil du programme depuis la phase A1 ; avant, statu_quo.dividende_productivite :
  recettes en plus moins dépenses indexées en plus, ≈ 12 % après dix ans), comme pour tous les gains de productivité ;
- baisse de l'écart de taux : plus un canal déclaré ; règle commune du noyau, gagnée par le résultat (chaque année de
  déficit sous le statu quo compte : noyau.baisse_ecart_taux) ;
- règle de trajectoire : celle du noyau (moteur/noyau.Regle) ; chaque levier a une capacité en part du PIB et porte
  sur les recettes (hausse) ou sur un bloc de dépenses (baisse). Les comptes sont publiés avec et sans la règle.

Ces effets ne passent pas par le multiplicateur (comme ceux d'Écologie de droite) ; ils sont publiés à part, sous le
nom « Canal déclaré : … », pour qu'un lecteur puisse les retirer.
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES, Levier, Mesure, Regle
from .parametres import Parametres

CANAUX = ("fraude_tva", "productivite", "reformes_structurelles", "adoption_ia", "ecole", "regle_trajectoire",
          "solde_migratoire")


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
    y = sq.pib(p, s)
    # gains de productivité : ce qui reste au solde quand la productivité monte, dépenses indexées comprises
    # (statu_quo.dividende_productivite ; relecture neutre n° 2, point 1, décision d'Adrien du 12/11/2026)
    # phase A1 : le dividende est recalculé par le noyau sur le profil de gain du programme (dividende_programme),
    # une fois tous les canaux réunis ; chaque canal en reçoit sa part
    pib = {t: 0.0 for t in ANNEES}
    mesures: list[Mesure] = []
    series: list[tuple[str, dict[int, float]]] = []

    def ajouter(nom: str, serie_pib: dict[int, float]) -> None:
        for t in ANNEES:
            pib[t] += serie_pib[t]
        series.append((nom, serie_pib))

    if "fraude_tva" in d:
        x = d["fraude_tva"]
        mesures.append(Mesure("Canal déclaré : fraude à la TVA", "recettes",
                              {t: x["montant"][s] * _montee(t, x.get("debut", 2029), x.get("montee", 1)) for t in ANNEES}, "effet_macro"))
    if "productivite" in d:
        x = d["productivite"]
        ajouter("productivité", {t: y[t] * ((1 + x["taux"][s]) ** max(0, min(x["annees"], t - x["debut"] + 1)) - 1) for t in ANNEES})
    if "reformes_structurelles" in d:
        from .reformes_structurelles import gain
        x = d["reformes_structurelles"]
        ajouter("réformes de structure (productivité)", {t: y[t] * gain(p, x, s, t) for t in ANNEES})
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
    emplois, actifs = {t: 0.0 for t in ANNEES}, {t: 0.0 for t in ANNEES}
    if "solde_migratoire" in d:
        # variante migratoire commune (phase B2, moteur/migrations.py) : écarts au statu quo recalculé avec la
        # population du programme ; PIB, emploi et actifs dans le contexte, recettes et dépenses en mesures
        from . import migrations
        mg = migrations.effets(p, s, d["solde_migratoire"])
        lib = f"solde migratoire ({mg['variation_solde'] / 1e3:+.0f} 000 par an)"
        mesures.append(Mesure(f"Démographie : {lib}, recettes", "recettes", dict(mg["recettes"]), "effet_macro"))
        for b in mg["blocs"][ANNEES[-1]]:
            serie = {t: mg["blocs"][t].get(b, 0.0) for t in ANNEES}
            if any(abs(v) > 1e-6 for v in serie.values()):
                mesures.append(Mesure(f"Démographie : {lib}, dépenses ({b})", b, serie, "effet_macro"))
        for t in ANNEES:
            emplois[t], actifs[t] = mg["emploi"][t], mg["actifs"][t]
        pib_m = mg["pib"]
    else:
        pib_m = None
    if series:
        dividende = sq.dividende_programme(p, s, pib)
        for nom, serie_pib in series:
            mesures.append(Mesure(f"Canal déclaré : {nom}", "recettes", {t: serie_pib[t] * dividende[t] for t in ANNEES},
                                  "effet_macro"))
    if pib_m is not None:  # ajouté après le dividende : ce PIB-là n'est pas un gain de productivité
        for t in ANNEES:
            pib[t] += pib_m[t]
    return {"mesures": mesures, "pib": pib, "taux_supplementaire": None, "emplois": emplois, "actifs": actifs}


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
