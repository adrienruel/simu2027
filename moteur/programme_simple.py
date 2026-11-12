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

Canaux déclarés (12 novembre 2026, moteur/canaux_declares.py) : tout programme peut déclarer, dans le groupe
`<nom>_canaux` de ses paramètres, les effets propres qu'Écologie de droite était seul à compter (fraude à la TVA,
productivité, adoption de l'IA, niveau des élèves, baisse de l'écart de taux) et une règle de trajectoire, avec les
mêmes formules. Absent : zéro. Chaque valeur est sourcée et datée comme tout paramètre.
"""
from __future__ import annotations

from . import offre
from . import statu_quo as sq
from .noyau import ANNEES, Mesure
from .parametres import Parametres

ANNEES_AVANT = (2027, 2028)
TOUTES = (*ANNEES_AVANT, *ANNEES)


MIROIR = {"crise": "optimiste", "prudent": "median", "median": "prudent", "optimiste": "crise"}


def multiplicateur(p, s: str, cout_net: dict, annees) -> dict:
    """PIB en plus (Md€) dû à l'impulsion budgétaire nette (cout_net : coût net cumulé des mesures, + = relance).

    Chaque impulsion annuelle agit avec le multiplicateur commun (macro.multiplicateur) et s'efface linéairement en
    macro.annees_effet_ajustement années. Comme l'éviction et le canal d'offre, le sens compte (décision d'Adrien du
    07/11/2026) : un resserrement prend les valeurs de son scénario, une relance celles du scénario miroir (crise ↔
    optimiste, prudent ↔ médian), pour que chaque scénario reste du même côté de la prudence quel que soit le sens."""
    par = {sc: (sq._v(p, "macro.multiplicateur", sc), sq._v(p, "macro.annees_effet_ajustement", sc))
           for sc in (s, MIROIR[s])}
    dpib, prec, impulsions = {}, 0.0, []
    for t in annees:
        i = cout_net[t] - prec
        prec = cout_net[t]
        impulsions.append((t, i, par[MIROIR[s]] if i > 0 else par[s]))
        dpib[t] = sum(m * i * max(0.0, 1 - (t - k) / d) for k, i, (m, d) in impulsions)
    return contrainte_capacite(p, s, dpib)


def contrainte_capacite(p, s: str, dpib: dict) -> dict:
    """Relance qui bute sur l'offre (décision d'Adrien du 07/11/2026) : au-delà de capacite.seuil_pib points de PIB,
    seule la part capacite.effet_au_dela du PIB en plus dû au multiplicateur passe dans le PIB (le reste fuit vers les
    prix et les importations). Ne touche pas un PIB en moins (resserrement)."""
    y = sq.pib(p, s)
    seuil, k = sq._v(p, "capacite.seuil_pib", s), sq._v(p, "capacite.effet_au_dela", s)
    out = {}
    for t, v in dpib.items():
        lim = seuil / 100 * y[max(t, 2029)]
        out[t] = v if v <= lim else lim + k * (v - lim)
    return out


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

    # ------------------------------------------------------------------ économies annoncées sans mesures
    def enveloppe_economies(self, p: Parametres, s: str, idx: dict, liste: list[Mesure]) -> list[Mesure]:
        """Économies annoncées mais non détaillées, déduites du programme domaine par domaine (décision d'Adrien du
        11/11/2026), jamais du chiffre du candidat.

        Pour chaque domaine de dépense (enveloppe_economies.domaines : État, opérateurs, collectivités, santé,
        prestations), capacité d'économie en fin de quinquennat tirée des précédents (Md€ de 2026, par scénario) ×
        intensité que le programme lui donne (<nom>_enveloppe.intensite : 0 si le domaine n'est pas visé ou est
        protégé, 0,5 s'il est cité, 1 s'il est une cible principale), moins les économies déjà nommées et chiffrées
        dans ce domaine (pas de double compte, plancher à 0). Le total ne dépasse pas l'annonce du candidat
        (<nom>_enveloppe.annonce), qui ne sert que de plafond. Montée de debut à plein."""
        if f"{self.nom}_enveloppe.intensite" not in self.pt._p:
            return []
        dom = p.val("enveloppe_economies.domaines")
        inten = self.v("enveloppe.intensite")
        annonce = self.v("enveloppe.annonce")
        d0, d1 = int(self.v("enveloppe.debut")), int(self.v("enveloppe.plein"))
        y = sq.pib(p, s)
        # économies déjà nommées par poste (dépenses en moins à l'année pleine, hors effets économiques)
        nommees: dict[str, float] = {}
        for m in liste:
            if m.poste != "recettes" and m.nature != "effet_macro":
                nommees[m.poste] = nommees.get(m.poste, 0.0) - min(0.0, m.valeurs.get(d1, 0.0))
        # domaines regroupés par ensemble de postes (État et opérateurs partagent le poste etat_missions)
        groupes: dict[tuple, list[str]] = {}
        for nom_d, d in dom.items():
            groupes.setdefault(tuple(sorted(d["postes"])), []).append(nom_d)
        retenu, detail = {}, {}
        for postes, noms in groupes.items():
            cap = {n: dom[n]["capacite"][s] * inten.get(n, 0.0) for n in noms}
            deja = sum(nommees.get(x, 0.0) for x in postes)
            reste = max(0.0, sum(cap.values()) - deja)
            for n in noms:
                retenu[n] = reste * cap[n] / sum(cap.values()) if sum(cap.values()) > 0 else 0.0
            detail[" + ".join(noms)] = {"capacite": sum(cap.values()), "deja_nommees": deja, "retenu": reste}
        total = sum(retenu.values())
        k = min(1.0, max(0.0, annonce - sum(nommees.values())) / total) if total > 0 else 0.0
        self.enveloppe_detail = getattr(self, "enveloppe_detail", {})
        self.enveloppe_detail[(id(p), s)] = {"domaines": detail, "nommees": sum(nommees.values()),
                                              "retenu": total * k, "plafond_annonce": total > 0 and k < 1.0}

        def mont(t):
            return min(1.0, max(0.0, (t - d0 + 1) / (d1 - d0 + 1)))
        out = []
        for n, v in retenu.items():
            if v * k <= 0:
                continue
            postes = dom[n]["postes"]
            for poste, part in postes.items():
                w = -v * k * part
                out.append(Mesure(f"Économies annoncées non détaillées : {dom[n]['libelle']} ({poste})", poste,
                                  {**{t: w * mont(t) for t in ANNEES_AVANT},
                                   **{t: w * mont(t) * y[t] / y[d1] for t in ANNEES}}, note="enveloppe"))
        return out

    # ------------------------------------------------------------------ émissions
    def mesures_ecologie(self, p: Parametres, s: str) -> list[Mesure]:
        """Effets physiques des mesures (groupe <nom>_ecologie, Mt CO2e par an, négatif = évitées), même méthode que
        Tondelier (moteur/ecologie/emissions.profil) : une mesure sans montant chacune, dont le coût est déjà dans les
        mesures budgétaires. Commun à tous les programmes simples depuis le 11/11/2026 (phase 2 de la roadmap)."""
        from .ecologie import emissions as em
        out = []
        prefixe = f"{self.nom}_ecologie."
        for nom, par in self.pt._p.items():
            if not nom.startswith(prefixe):
                continue
            x = par.valeur
            serie = em.profil(p, s, x)
            out.append(Mesure(f"{x['id']} — {x['libelle']} (émissions)", "recettes", {}, "physique",
                              physique={f"emissions_mt:{x['secteur']}": serie},
                              vert="defavorable" if max(serie.values()) > 0 else "favorable"))
        return out

    # ------------------------------------------------------------------ 32 heures (privé)
    def trente_deux_heures(self, p: Parametres, s: str, idx: dict, c: dict, el_t: float, prefixe: str,
                           canaux: dict) -> list[Mesure]:
        """Passage aux 32 heures sans perte de salaire pour c["emplois_concernes"] salariés du privé (11/11/2026).

        Heures par salarié −(1 − 32/35) ; coût horaire + (35/32 − 1) × (1 − gain de productivité) : emplois perdus
        (élasticité el_t) ; une part des heures est rendue par des embauches de partage du travail ; le reste est de la
        production marchande en moins (self.pib_en_plus), avec ses recettes. Montée de c["debut"] à c["plein"]."""
        e = sq.effectifs(p, s)
        y = sq.pib(p, s)
        rec = sq.recettes(p, s)
        ip = idx["pib"]
        baisse = 1 - c["heures_cible"] / c["heures_actuelles"]
        gp, ge = c["gain_productivite"][s], c["part_embauches"][s]
        n = c["emplois_concernes"]
        part = n / c["emplois_prive"]

        def m(t):
            return min(1.0, max(0.0, (t - c["debut"] + 1) / (c["plein"] - c["debut"] + 1)))
        k = 1 + (c["heures_actuelles"] / c["heures_cible"] - 1) * (1 - gp)
        perdus = n * (1 - k ** el_t)
        embauches = n * baisse * ge
        r = {t: e[t]["emploi"] / e[2029]["emploi"] for t in ANNEES}
        canaux[f"{prefixe} : emplois perdus par le coût horaire"] = {t: -perdus * m(t) * r[t] for t in ANNEES}
        canaux[f"*{prefixe} : embauches de partage du travail"] = {t: embauches * m(t) * r[t] for t in ANNEES}
        d = {t: -y[t] * c["part_marchande"] * part * baisse * (1 - gp - ge) * m(t) for t in ANNEES}
        d28 = -y[2029] * c["part_marchande"] * part * baisse * (1 - gp - ge) * m(2028)
        self.ajouter_pib(p, s, d)
        part_rec = {t: rec[t] / y[t] for t in ANNEES}
        valeur = self.v("emploi.valeur_emploi")
        return [
            Mesure(f"{prefixe} : production et recettes en moins (heures non compensées)", "recettes",
                   {2027: 0.0, 2028: d28 * part_rec[2029], **{t: d[t] * part_rec[t] for t in ANNEES}},
                   nature="effet_macro"),
            Mesure(f"{prefixe} : prélèvements des embauches de partage du travail", "recettes",
                   {2027: 0.0, 2028: embauches * m(2028) * valeur / 1e9,
                    **{t: embauches * m(t) * valeur * ip[t] / 1e9 for t in ANNEES}}, nature="effet_macro"),
        ]

    def heures_fonction_publique(self, p: Parametres, s: str, idx: dict, c: dict, prefixe: str,
                                 canaux: dict) -> list[Mesure]:
        """Même baisse d'heures dans la fonction publique (11/11/2026, repris de Roussel) : embauches pour garder le
        service, c["part_compensee_fp"] des heures perdues, avec leurs prélèvements et la même éviction que les autres
        postes publics créés (emploi_public.eviction_privee)."""
        versant_poste = {"etat_civils": "etat_missions", "etat_militaires": "defense_ue", "territoriale": "collectivites",
                         "hospitaliere": "sante"}
        ip = idx["pib"]
        versants = p.val("statu_quo.versants_fonction_publique")
        tot = sum(versants.values())
        cout_public = sq.prelevements_activite(p)["public"]["cout"]
        part_fp = self.part_prelevements_fp(p)

        def m(t):
            return min(1.0, max(0.0, (t - c["debut"] + 1) / (c["plein"] - c["debut"] + 1)))
        hausse = cout_public * (c["heures_actuelles"] / c["heures_cible"] - 1) * c["part_compensee_fp"][s]
        out = [Mesure(f"{prefixe} dans la fonction publique : embauches ({versant_poste[v]})", versant_poste[v],
                      {2027: 0.0, 2028: hausse * part / tot * m(2028),
                       **{t: hausse * part / tot * m(t) * ip[t] for t in ANNEES}}) for v, part in versants.items()]
        out.append(Mesure(f"{prefixe} dans la fonction publique : prélèvements sur ces embauches", "recettes",
                          {2027: 0.0, 2028: part_fp * hausse * m(2028),
                           **{t: part_fp * hausse * m(t) * ip[t] for t in ANNEES}}))
        n_fp = hausse * 1e9 / self.v("emploi.cout_poste_public")
        canaux[f"*Postes publics : {prefixe} dans la fonction publique"] = {t: n_fp * m(t) for t in ANNEES}
        ev = sq._v(p, "emploi_public.eviction_privee", s)
        canaux[f"{prefixe} : emplois privés évincés par les embauches publiques"] = {t: -ev * n_fp * m(t) for t in ANNEES}
        return out

    def ajouter_pib(self, p: Parametres, s: str, d: dict) -> None:
        """Production en plus ou en moins hors des canaux d'emploi (Md€ par année), lue dans le calcul du PIB."""
        self.pib_en_plus = getattr(self, "pib_en_plus", {})
        prec = self.pib_en_plus.get((id(p), s), {})
        self.pib_en_plus[(id(p), s)] = {t: prec.get(t, 0.0) + d.get(t, 0.0) for t in ANNEES}

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
                    # fp_taux : part revenant en prélèvements propre à la mesure (emplois payés au SMIC : ni CAS
                    # pensions ni impôt sur le revenu, ≈ 0,39 ; relecture neutre du 11/11/2026)
                    taux = x.get("fp_taux", part_fp)
                    liste.append(Mesure(f"{x['id']} — prélèvements sur ces rémunérations", "recettes",
                                        {t: taux * v for t, v in serie.items()}, note=court))
                if x.get("postes"):
                    cible = crees if x["_montant"] >= 0 else supprimes
                    for t in ANNEES:
                        cible[t] += serie[t] * 1e9 / (x.get("cout_poste", cout_poste) * w[t] / w[2029])
            calc, canaux_calc = self.mesures_calculees(p, s, idx)
            liste.extend(calc)
            liste.extend(self.mesures_ecologie(p, s))
            liste.extend(self.enveloppe_economies(p, s, idx, liste))
            if getattr(self, "variante_annonces", False):
                # variante « annonce tenue » (moteur/annonces.py) : jamais dans le chiffrage publié
                from . import annonces as ann
                env = f"{self.nom}_enveloppe.intensite" in self.pt._p
                liste.extend(ann.mesures_tenues(
                    self.nom, p, s, liste, getattr(self, "enveloppe_detail", {}).get((id(p), s)),
                    self.v("enveloppe.intensite") if env else None,
                    int(self.v("enveloppe.debut")) if env else 2028, int(self.v("enveloppe.plein")) if env else 2032))
            # emplois : postes publics, éviction, canaux des mesures calculées
            # éviction : prise au scénario du même côté de la prudence, pour chaque sens. Créer des postes publics :
            # l'éviction forte est prudente ; en supprimer : c'est la reprise faible par le privé qui l'est (scénario miroir)
            miroir = MIROIR
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
            actif = self.v("macro.multiplicateur_actif")
            dpib = multiplicateur(p, s, cout_net, TOUTES) if actif else {t: 0.0 for t in TOUTES}
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
            # personnes retirées de la population active par une mesure calculée (ex. service civique obligatoire) :
            # leurs emplois perdus ne font pas de chômeurs
            for t, v in getattr(self, "actifs_en_plus", {}).get((id(p), s), {}).items():
                actifs[t] += v
            # PIB : multiplicateur, offre, et valeur ajoutée des emplois en plus ou en moins hors conjoncture et offre
            # (les postes publics sont déjà dans le PIB par leur dépense et le multiplicateur)
            va = self.v("emploi.valeur_ajoutee_emploi")
            hors_conj = {t: sum(v for c, v in canaux[t].items()
                                if not c.startswith(("Conjoncture", "Postes publics", "Offre", "Seniors")))
                         for t in ANNEES}
            # PIB en plus ou en moins hors emploi (ex. heures travaillées en moins par salarié, 32 heures) : rangé par une
            # mesure calculée dans self.pib_en_plus[(id(p), s)] = {année: Md€}, avec sa mesure de recettes (11/11/2026)
            d_autre = getattr(self, "pib_en_plus", {}).get((id(p), s), {})
            # canaux déclarés par le programme (ouverts à tous : moteur/canaux_declares.py)
            from . import canaux_declares
            decl = canaux_declares.effets(self, p, s)
            liste.extend(decl["mesures"])
            pib = {t: y[t] + dpib[t] + d_offre[t] + d_seniors[t] + d_autre.get(t, 0.0) + decl["pib"][t]
                   + hors_conj[t] * va * idx["pib"][t] / 1e9 for t in ANNEES}
            demploi = {t: sum(canaux[t].values()) for t in ANNEES}
            chom = {t: (e[t]["chomeurs"] - (demploi[t] - actifs[t])) / (e[t]["emploi"] + e[t]["chomeurs"] + actifs[t]) * 100
                    for t in ANNEES}
            avant = sum(-(m.valeurs.get(t, 0.0)) if m.poste == "recettes" else m.valeurs.get(t, 0.0)
                        for m in liste for t in ANNEES_AVANT if m.poste != "participations")
            ctx_s[s] = {"pib": pib, "chomage": chom, "dette_depart": sq.dette_fin_2028(p) + avant,
                        "emploi": {t: e[t]["emploi"] + demploi[t] for t in ANNEES}, "emplois_canaux": canaux}
            if decl["taux_supplementaire"]:
                ctx_s[s]["taux_supplementaire"] = decl["taux_supplementaire"]
            mes_s[s] = liste
            details[s] = {"avant_2029": avant, "dpib": dpib, "emplois": demploi, "offre": details_offre,
                          "dpib_offre": d_offre}
        res = {"mesures": mes_s, "contexte": ctx_s, "details": details}
        self._cache[cle] = res
        return res

    def entrees(self, p: Parametres, scenarios=None) -> dict:
        """Entrées du noyau : mesures, contexte et, si le programme en déclare une, sa règle de trajectoire (objet
        neuf à chaque appel)."""
        from . import canaux_declares
        from .noyau import Entree
        c = self._calcul(p)
        return {s: Entree(c["mesures"][s], c["contexte"][s], [], canaux_declares.regle(self, p, s))
                for s in sq.SCENARIOS if scenarios is None or s in scenarios}

    def mesures(self, p: Parametres) -> dict[str, list[Mesure]]:
        return self._calcul(p)["mesures"]

    def contexte(self, p: Parametres) -> dict[str, dict]:
        return self._calcul(p)["contexte"]
