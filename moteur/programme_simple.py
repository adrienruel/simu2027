"""Programme générique sur le noyau : mesures simples + mesures de la bibliothèque (6 novembre 2026).

Pour les programmes courts (peu de mesures chiffrables), un dossier programmes/<nom>/ suffit avec :
- parametres.yaml : groupe <nom>_mesures (même format que tondelier_mesures : id, libelle, poste, moteur, debut,
  plein, fin, montant par scénario, fp, postes) et les paramètres des mesures calculées ;
- mesures.yaml : fiche des mesures (citations, sources, statut) ;
- programme.py : une sous-classe de ProgrammeSimple qui ajoute ses mesures calculées (mesures_calculees).

Ce que fait la classe, comme le programme Tondelier :
- **mesures simples** : montant à l'économie de 2029 (Md€ de 2026), montée linéaire de debut à plein, puis ce qu'il
  suit (moteur : pib, fixe, pensions, recette:<impôt du statu quo>, bloc:<bloc du statu quo>) ; « fp » : dépense de
  rémunération publique, dont une part revient en prélèvements (57 %, OpenFisca) ; « postes » : la dépense paie des
  postes publics (créés si > 0, supprimés si < 0), au coût de emploi.cout_poste_public, avec l'éviction d'emplois
  privés commune (emploi_public.eviction_privee) ;
- **effet macroéconomique** : multiplicateur commun sur l'impulsion budgétaire nette des mesures, dissipé comme
  l'ajustement budgétaire du modèle ; recettes au taux de prélèvement du statu quo ; emploi par la loi d'Okun ;
- **emploi** : les emplois en plus ou en moins viennent du chômage ou y vont (pas d'effet sur l'activité) ; chaque
  emploi vaut emploi.valeur_emploi au solde (prélèvements, TVA, allocation évitée), comme un emploi au SMIC ;
- **2027 et 2028** : ce que les mesures coûtent ou rapportent ces années s'ajoute à la dette de fin 2028.

Règle des autres candidats : on ne reprend que les mesures ; aucune recette ni économie annoncée n'est saisie.
"""
from __future__ import annotations

from . import offre
from . import statu_quo as sq
from .noyau import ANNEES, Mesure
from .parametres import Parametres

ANNEES_AVANT = (2027, 2028)
TOUTES = (*ANNEES_AVANT, *ANNEES)


class ProgrammeSimple:
    nom = ""
    libelle = ""

    def __init__(self) -> None:
        self.pt = Parametres(programme=self.nom)
        self._cache: dict = {}

    # ------------------------------------------------------------------ outils
    def v(self, cle: str, s: str = "prudent"):
        return self.pt[f"{self.nom}_{cle}"].pour(s)

    def a(self, cle: str) -> bool:
        return f"{self.nom}_{cle}" in self.pt._p

    def indices(self, p: Parametres, s: str) -> dict:
        y = sq.pib(p, s)
        rec = sq.recettes_par_impot(p, s)
        bl = sq.blocs(p, s)
        ret = sq.retraites(p, s)
        idx = {"pib": {t: y[t] / y[2029] for t in ANNEES}, "fixe": {t: 1.0 for t in ANNEES},
               "pensions": {t: ret[t]["depenses"] / ret[2029]["depenses"] for t in ANNEES}}
        for imp in rec[2029]:
            idx[f"recette:{imp}"] = {t: rec[t][imp] / rec[2029][imp] if rec[2029][imp] else 1.0 for t in ANNEES}
        for b in sq.BLOCS:
            idx[f"bloc:{b}"] = {t: bl[t][b] / bl[2029][b] for t in ANNEES}
        return idx

    @staticmethod
    def profil(x: dict, t: int) -> float:
        """Montant de l'année t avant indice : montée linéaire de debut à plein (de « depart » si donné), puis fin."""
        debut, plein, fin = x["debut"], x["plein"], x.get("fin")
        if t < debut or (fin is not None and t > fin):
            return 0.0
        m = x["_montant"]
        if "depart" in x and t < plein:
            return x["depart"] + (m - x["depart"]) * (t - debut) / max(1, plein - debut)
        return m * min(1.0, (t - debut + 1) / (plein - debut + 1))

    def serie(self, x: dict, idx: dict) -> dict[int, float]:
        i = idx[x["moteur"]]
        out = {t: self.profil(x, t) for t in ANNEES_AVANT}
        out.update({t: self.profil(x, t) * i[t] for t in ANNEES})
        return out

    def part_prelevements_fp(self, p: Parametres) -> float:
        a = sq.prelevements_activite(p)["public"]
        return (a["prelevements"] + a["impot_revenu"]) / a["cout"]

    # ------------------------------------------------------------------ à compléter par chaque programme
    def mesures_calculees(self, p: Parametres, s: str, idx: dict) -> tuple[list[Mesure], dict[str, dict[int, float]]]:
        """Mesures de la bibliothèque (montants) et emplois qu'elles changent ({canal: {année: emplois}}), hors
        effets budgétaires de ces emplois, ajoutés par la classe au prix emploi.valeur_emploi (sauf canal dont le nom
        commence par « * » : effet budgétaire déjà compté par la mesure). Un programme qui change l'âge de la retraite
        range les personnes pas encore retraitées en plus dans self.non_retraites[(id(p), s)] = {"serie": {année:
        personnes}, "baisse": bool} : la classe en tire l'emploi des seniors (offre.seniors)."""
        return [], {}

    # ------------------------------------------------------------------ assemblage
    def _calcul(self, p: Parametres) -> dict:
        cle = id(p)
        if cle in self._cache:
            return self._cache[cle]
        part_fp = self.part_prelevements_fp(p)
        mes_s, ctx_s, details = {}, {}, {}
        prefixe = f"{self.nom}_mesures."
        for s in sq.SCENARIOS:
            idx = self.indices(p, s)
            w = sq.salaires(p, s)
            liste: list[Mesure] = []
            crees = {t: 0.0 for t in ANNEES}
            supprimes = {t: 0.0 for t in ANNEES}
            cout_poste = self.v("emploi.cout_poste_public")
            for nom, par in self.pt._p.items():
                if not nom.startswith(prefixe):
                    continue
                x = dict(par.valeur)
                x["_montant"] = x["montant"][s] if isinstance(x["montant"], dict) else x["montant"]
                serie = self.serie(x, idx)
                court = nom.split(".")[1]
                liste.append(Mesure(f"{x['id']} — {x['libelle']}", x["poste"], serie, note=court,
                                    instrument=x.get("instrument", ""), incidence=x.get("incidence", "")))
                if x.get("fp"):
                    liste.append(Mesure(f"{x['id']} — prélèvements sur ces rémunérations", "recettes",
                                        {t: part_fp * v for t, v in serie.items()}, note=court))
                if x.get("postes"):
                    cible = crees if x["_montant"] >= 0 else supprimes
                    for t in ANNEES:
                        cible[t] += serie[t] * 1e9 / (x.get("cout_poste", cout_poste) * w[t] / w[2029])
            calc, canaux_calc = self.mesures_calculees(p, s, idx)
            liste.extend(calc)
            # emplois : postes publics, éviction, canaux des mesures calculées
            # éviction : prise au scénario du même côté de la prudence, pour chaque sens. Créer des postes publics :
            # l'éviction forte est prudente ; en supprimer : c'est la reprise faible par le privé qui l'est (scénario miroir)
            miroir = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}
            ev_c = sq._v(p, "emploi_public.eviction_privee", s)
            ev_s = sq._v(p, "emploi_public.eviction_privee", miroir[s])
            valeur = self.v("emploi.valeur_emploi")
            canaux = {t: {} for t in ANNEES}
            postes = {t: crees[t] + supprimes[t] for t in ANNEES}
            evince = {t: -(ev_c * crees[t] + ev_s * supprimes[t]) for t in ANNEES}
            if any(postes.values()):
                for t in ANNEES:
                    canaux[t]["Postes publics créés ou supprimés"] = postes[t]
                    canaux[t]["Éviction d'emplois privés par les postes publics"] = evince[t]
                liste.append(Mesure("Emploi : emplois privés évincés (ou libérés) par les postes publics", "recettes",
                                    {t: evince[t] * valeur * idx["pib"][t] / 1e9 for t in ANNEES}, nature="effet_macro"))
            for canal, serie in canaux_calc.items():
                for t in ANNEES:
                    canaux[t][canal.lstrip("*")] = serie.get(t, 0.0)
                if not canal.startswith("*"):
                    liste.append(Mesure(f"Emploi : {canal}", "recettes",
                                        {t: serie.get(t, 0.0) * valeur * idx["pib"][t] / 1e9 for t in ANNEES}, nature="effet_macro"))
            # effet macroéconomique : impulsion budgétaire nette, chaque mesure pondérée selon ce qu'elle est (demande
            # par instrument, moteur/offre.poids_demande : 1 pour la dépense publique)
            cout_net = offre.impulsion(p, liste, TOUTES)
            y = sq.pib(p, s)
            rec_sq = sq.recettes(p, s)
            mult, duree = sq._v(p, "macro.multiplicateur", s), sq._v(p, "macro.annees_effet_ajustement", s)
            actif = self.v("macro.multiplicateur_actif")
            dpib, prec, impulsions = {}, 0.0, []
            for t in TOUTES:
                impulsions.append((t, cout_net[t] - prec))
                prec = cout_net[t]
                dpib[t] = (mult * sum(i * max(0.0, 1 - (t - k) / duree) for k, i in impulsions)) if actif else 0.0
            part_rec = {t: rec_sq[t] / y[t] for t in ANNEES}
            part_rec.update({t: part_rec[2029] for t in ANNEES_AVANT})
            if actif:
                liste.append(Mesure("Effet macro : multiplicateur sur l'impulsion budgétaire des mesures", "recettes",
                                    {t: dpib[t] * part_rec[t] for t in TOUTES}, nature="effet_macro"))
            e = sq.effectifs(p, s)
            k_emp = sq._v(p, "macro.emplois_par_point_pib", s)
            conj = {t: dpib[t] / y[t] * k_emp * e[t]["emploi"] for t in ANNEES}
            for t in ANNEES:
                canaux[t]["Conjoncture (impulsion budgétaire)"] = conj[t]
            # canal d'offre commun (moteur/offre.py) : effet durable des impôts et des transferts
            actifs = {t: 0.0 for t in ANNEES}
            d_offre = {t: 0.0 for t in TOUTES}
            if offre.actif(p):
                of = offre.effets(p, s, liste)
                liste.append(of["mesure"])
                d_offre = of["dpib"]
                actifs = of["actifs"]
                for canal, serie in of["emplois"].items():
                    for t in ANNEES:
                        canaux[t][canal] = serie[t]
                details_offre = of["detail"]
            else:
                details_offre = {}
            # emploi des seniors quand l'âge de la retraite change (offre.seniors) : emplois, chômeurs, inactifs
            d_seniors = {t: 0.0 for t in ANNEES}
            nr = getattr(self, "non_retraites", {}).get((id(p), s))
            if nr is not None:
                sen = offre.seniors(p, s, nr["serie"], baisse_age=nr["baisse"])
                liste.extend(sen["mesures"])
                d_seniors = sen["pib"]
                for t in ANNEES:
                    canaux[t]["Seniors : emploi (âge de la retraite)"] = sen["emplois"][t]
                    actifs[t] += sen["actifs"][t]
            # PIB : multiplicateur, offre, et valeur ajoutée des emplois en plus ou en moins hors conjoncture et offre
            # (les postes publics sont déjà dans le PIB par leur dépense et le multiplicateur)
            va = self.v("emploi.valeur_ajoutee_emploi")
            hors_conj = {t: sum(v for c, v in canaux[t].items()
                                if not c.startswith(("Conjoncture", "Postes publics", "Offre", "Seniors")))
                         for t in ANNEES}
            pib = {t: y[t] + dpib[t] + d_offre[t] + d_seniors[t] + hors_conj[t] * va * idx["pib"][t] / 1e9 for t in ANNEES}
            demploi = {t: sum(canaux[t].values()) for t in ANNEES}
            chom = {t: (e[t]["chomeurs"] - (demploi[t] - actifs[t])) / (e[t]["emploi"] + e[t]["chomeurs"] + actifs[t]) * 100
                    for t in ANNEES}
            avant = sum(-(m.valeurs.get(t, 0.0)) if m.poste == "recettes" else m.valeurs.get(t, 0.0)
                        for m in liste for t in ANNEES_AVANT if m.poste != "participations")
            ctx_s[s] = {"pib": pib, "chomage": chom, "dette_depart": sq.dette_fin_2028(p) + avant,
                        "emploi": {t: e[t]["emploi"] + demploi[t] for t in ANNEES}, "emplois_canaux": canaux}
            mes_s[s] = liste
            details[s] = {"avant_2029": avant, "dpib": dpib, "emplois": demploi, "offre": details_offre,
                          "dpib_offre": d_offre}
        res = {"mesures": mes_s, "contexte": ctx_s, "details": details}
        self._cache[cle] = res
        return res

    def mesures(self, p: Parametres) -> dict[str, list[Mesure]]:
        return self._calcul(p)["mesures"]

    def contexte(self, p: Parametres) -> dict[str, dict]:
        return self._calcul(p)["contexte"]
