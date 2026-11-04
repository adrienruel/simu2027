"""« Écologie de droite » branché sur le noyau commun (moteur/noyau.py), 4 novembre 2026.

Première étape du rebranchement : le programme garde son propre moteur (moteur/macro.py, moteur/trajectoire_annuelle.py,
qui chiffrent son budget ligne par ligne) et il est traduit en mesures contre le statu quo :

- chaque poste de son budget remplace les blocs correspondants du statu quo (écart = budget du programme − statu
  quo) : retraites, santé, investissement un pour un ; le revenu universel et l'AAH remplacent l'assurance chômage,
  la famille, le logement, la pauvreté et l'AAH ; les autres dépenses remplacent les missions, l'enseignement et le
  reste ;
- ses effets macroéconomiques sont des mesures de recettes, une par canal (emploi, capital du fonds, érosion de
  l'IS…), règle de trajectoire comprise ;
- son contexte : PIB, inflation (récession de 2029, carbone), baisse de l'écart de taux, chômage, dette de fin 2028
  (mesures de 2028), participations remises au fonds.

Le noyau recalcule alors les intérêts, la dette et le déficit : il doit retrouver exactement les résultats du moteur
du programme (tests/test_noyau.py). L'écart de 2029 entre le budget du programme et le statu quo, poste par poste,
mêle les mesures et les différences de méthode (budget ligne par ligne contre agrégats du PLF 2027) : il est montré
par `ecart_de_depart`. Étapes suivantes : remplacer ces écarts globaux par des mesures codées une à une sur le noyau.
"""
from __future__ import annotations

from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres

# poste du programme → blocs du statu quo qu'il remplace
CORRESPONDANCE = {
    "retraites": ("retraites",),
    "sante": ("sante",),
    "investissement": ("investissement",),
    "rui_aah": ("chomage", "famille", "logement", "pauvrete", "aah_invalidite"),
    "autres": ("missions_pib", "education", "autres"),
}
LIBELLES = {
    "retraites": "Retraites : socle, transition et ancien système",
    "sante": "Santé : trajectoire et mesures",
    "investissement": "Investissement : subventions restées à l'État, renouvelables",
    "rui_aah": "Revenu universel et AAH",
    "autres": "Autres dépenses du programme (ministères, collectivités, mesures)",
}


class EcologieDeDroite:
    nom = "ecologie_de_droite"

    def __init__(self):
        self._cache = {}

    def _calcul(self, p: Parametres) -> dict:
        cle = id(p)
        if cle in self._cache:
            return self._cache[cle]
        from moteur import statu_quo as sq
        from moteur.calendrier import dette_fin_2028
        from moteur.inflation import serie
        from moteur.retraites_transition import cout_transition
        from moteur.simulation import simuler
        res = simuler(p)
        pc = p.en_crise()
        jeux = {"crise": (pc, "prudent"), "prudent": (p, "prudent"), "median": (p, "median"), "optimiste": (p, "optimiste")}
        mesures, contexte = {}, {}
        for s, (q, jeu) in jeux.items():
            r = res[s]
            rec_sq, bl_sq = sq.recettes(p, s), sq.blocs(p, s)
            m = []
            # budget hors effets macro : recettes, puis chaque poste contre les blocs qu'il remplace
            m.append(Mesure("Recettes du programme (hors effets macro) contre recettes actuelles", "recettes",
                            {t: r[t]["recettes"] - r[t]["effet_macro"] - rec_sq[t] for t in ANNEES}, "budget"))
            m.append(Mesure("Fin des dotations versées aux collectivités (solde)", "recettes",
                            {t: -r[t]["transferts_collectivites"] for t in ANNEES}, "budget"))
            for poste, blocs in CORRESPONDANCE.items():
                if len(blocs) == 1:
                    m.append(Mesure(LIBELLES[poste], blocs[0], {t: r[t][poste] - bl_sq[t][blocs[0]] for t in ANNEES}, "budget"))
                else:
                    m.append(Mesure(LIBELLES[poste], f"nouveau:{poste}", {t: r[t][poste] for t in ANNEES}, "budget"))
                    for b in blocs:
                        m.append(Mesure(f"Remplacé par « {LIBELLES[poste]} » : {b}", b, {t: -bl_sq[t][b] for t in ANNEES}, "budget"))
            # effets macroéconomiques, canal par canal (le reste : épargne rendue et socle supplémentaire de la règle)
            canaux = sorted({k for t in ANNEES for k in r[t]["canaux"]})
            for k in canaux:
                m.append(Mesure(f"Effet macro : {k}", "recettes", {t: r[t]["canaux"].get(k, 0.0) for t in ANNEES}, "effet_macro"))
            m.append(Mesure("Effet macro : épargne rendue et socle supplémentaire (règle)", "recettes",
                            {t: r[t]["effet_macro"] - sum(r[t]["canaux"].values()) for t in ANNEES}, "effet_macro"))
            m.append(Mesure("Participations de l'État remises au fonds", "participations",
                            {t: v["participations"] for t, v in cout_transition(q).items()}, "mesure"))
            mesures[s] = m
            # contexte : ce que le programme change dans l'économie
            infl = serie(q, jeu)
            spread = q.val("macro.baisse_spread", jeu)
            n_sp = q.val("macro.annees_baisse_spread")
            pib = {t: r[t]["pib"] for t in ANNEES}
            ref = {t: r[t]["pib"] - r[t]["effet_pib"] for t in ANNEES}
            contexte[s] = {
                "pib": pib,
                # module macro : ratio de la prime de dette sur le PIB de référence + effets de l'année précédente
                "pib_prime": {t: ref[t] + (r[t - 1]["effet_pib"] if t > 2029 else 0.0) for t in ANNEES},
                "inflation": {t: infl[t] for t in ANNEES},
                "taux_supplementaire": {t: -spread * min(1.0, max(0, t - 2029) / n_sp) for t in ANNEES},
                "chomage": {t: r[t]["chomage"] for t in ANNEES},
                "dette_depart": dette_fin_2028(q),
            }
        out = {"mesures": mesures, "contexte": contexte, "resultats": res}
        self._cache = {cle: out}
        return out

    def mesures(self, p: Parametres) -> dict[str, list[Mesure]]:
        return self._calcul(p)["mesures"]

    def contexte(self, p: Parametres) -> dict[str, dict]:
        return self._calcul(p)["contexte"]

    def resultats_moteur(self, p: Parametres) -> dict:
        """Résultats du moteur propre au programme (moteur/simulation.simuler), pour la reproduction."""
        return self._calcul(p)["resultats"]


def programme() -> EcologieDeDroite:
    return EcologieDeDroite()


def ecart_de_depart(p: Parametres | None = None, s: str = "prudent", annee: int = 2029) -> dict[str, float]:
    """Écart du budget du programme avec le statu quo, poste par poste (Md€ ; + = améliore le solde), hors effets
    macro : mêle les mesures et les différences de méthode. Seul le total est comparable : le budget du programme
    est consolidé autrement (les collectivités n'y figurent que par leur besoin de financement, quand le statu quo
    compte toutes les recettes et dépenses des administrations), d'où de gros écarts de sens contraire entre
    recettes, investissement et autres dépenses."""
    from moteur import statu_quo as sq
    p = p or Parametres()
    prog = programme()
    out = {}
    for m in prog.mesures(p)[s]:
        if m.nature != "budget":
            continue
        cle = m.nom.split(" : ")[0] if m.nom.startswith("Remplacé") else m.nom
        signe = 1 if m.poste == "recettes" else -1
        cle = next((LIBELLES[k] for k, b in CORRESPONDANCE.items() if m.poste in b or m.poste == f"nouveau:{k}"), cle)
        out[cle] = out.get(cle, 0.0) + signe * m.valeurs[annee]
    out["Total (points de PIB)"] = sum(out.values()) / sq.pib(p, s)[annee] * 100
    return out
