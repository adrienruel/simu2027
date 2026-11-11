"""Programme de Marine Tondelier (Les Écologistes), chiffré mesure par mesure sur le noyau (5 novembre 2026).

Premier programme d'un autre candidat. Il se lit comme le statu quo + des mesures :

- **mesures simples** (programmes/tondelier/parametres.yaml, groupe tondelier_mesures) : un montant à l'économie de 2029,
  sa montée, et ce qu'il suit ensuite (PIB, pensions, successions, un bloc du statu quo…). Une dépense de
  rémunération publique (fp) rend une part en prélèvements (57 %, OpenFisca) ;
- **mesures calculées** : hausse des rémunérations publiques (parts de masse par catégorie), retour à 62 ans (pensions
  de toutes les générations avec le profil de départ à 62 ans, même calcul que le statu quo), SMIC à 2 000 € (table
  OpenFisca de 2026 lue au salaire relevé : allègements nominalisés ; prélèvements, prime d'activité, IS, emplois
  perdus), génération sans tabac (population de l'Insee) ;
- **effets macroéconomiques** : multiplicateur commun appliqué à l'impulsion budgétaire nette des mesures (même
  mécanique que l'ajustement budgétaire du modèle), emplois perdus du SMIC ;
- **2027 et 2028** : les mesures de ces années s'ajoutent à la dette de fin 2028 (contexte dette_depart).

Règle des autres candidats : on ne reprend que les mesures ; aucune recette ni économie annoncée par le parti n'est
saisie (15 Md€ sur les successions : comparaison seulement). Fiche des mesures et citations : mesures.yaml.

    python -m moteur.noyau tondelier
"""
from __future__ import annotations

from moteur import offre
from moteur import statu_quo as sq
from moteur.noyau import ANNEES, Mesure
from moteur.parametres import Parametres
from moteur.programme_simple import multiplicateur

ANNEES_AVANT = (2027, 2028)
VERSANTS = {"etat_civils": "etat_missions", "etat_militaires": "etat_missions", "territoriale": "collectivites",
            "hospitaliere": "sante"}
RECETTE_MOTEUR = {"successions": "successions", "tva": "tva", "capital": "capital_dividendes_ifi",
                  "is": "impot_sur_les_societes"}


def _parametres_programme() -> Parametres:
    return Parametres(programme="tondelier")


class Tondelier:
    nom = "tondelier"
    libelle = "Tondelier (Les Écologistes)"

    def __init__(self) -> None:
        self.pt = _parametres_programme()
        self._cache: dict = {}

    # ------------------------------------------------------------------ outils
    def v(self, cle: str, s: str = "prudent"):
        return self.pt.val(f"tondelier_{cle}", s)

    def _indices(self, p: Parametres, s: str) -> dict:
        y = sq.pib(p, s)
        rec = sq.recettes_par_impot(p, s)
        bl = sq.blocs(p, s)
        ret = sq.retraites(p, s)
        idx = {"pib": {t: y[t] / y[2029] for t in ANNEES}, "fixe": {t: 1.0 for t in ANNEES},
               "pensions": {t: ret[t]["depenses"] / ret[2029]["depenses"] for t in ANNEES}}
        for m, imp in RECETTE_MOTEUR.items():
            idx[m] = {t: rec[t][imp] / rec[2029][imp] for t in ANNEES}
        for b in sq.BLOCS:
            idx[f"bloc:{b}"] = {t: bl[t][b] / bl[2029][b] for t in ANNEES}
        return idx

    @staticmethod
    def _profil(x: dict, t: int) -> float:
        """Montant de l'année t (avant indice) : montée linéaire de debut à plein (de « depart » si donné), fin."""
        debut, plein, fin = x["debut"], x["plein"], x.get("fin")
        if t < debut or (fin is not None and t > fin):
            return 0.0
        m = x["_montant"]
        if "depart" in x:
            if t >= plein:
                v = m
            else:
                v = x["depart"] + (m - x["depart"]) * (t - debut) / max(1, plein - debut)
        else:
            v = m * min(1.0, (t - debut + 1) / (plein - debut + 1))
        if "apres_2032" in x and t > 2032:
            v = x["apres_2032"]
        if "hausse_2060" in x and t > plein:
            v = m + (x["hausse_2060"] - m) * min(1.0, (t - plein) / (2060 - plein))
        if x.get("moteur") == "decroit_4" and t > plein:
            v = m * 0.96 ** (t - plein)
        return v

    def _serie(self, x: dict, idx: dict) -> dict[int, float]:
        mot = x["moteur"]
        i = idx["fixe"] if mot == "decroit_4" else idx[mot]
        out = {t: self._profil(x, t) for t in ANNEES_AVANT}
        out.update({t: self._profil(x, t) * i[t] for t in ANNEES})
        return out

    def part_prelevements_fp(self, p: Parametres) -> float:
        a = sq.prelevements_activite(p)["public"]
        return (a["prelevements"] + a["impot_revenu"]) / a["cout"]

    # ------------------------------------------------------------------ mesures calculées
    def remunerations_publiques(self, p: Parametres) -> dict:
        """FP-02 : hausse de coût (Md€ de 2026, 2029) et sa répartition entre versants."""
        pm = self.v("fp.parts_masse")
        hausse = (pm["categorie_C"] * 0.10 + pm["categorie_B"] * 0.10 + pm["categorie_A_enseignants"] * 0.15
                  + pm["categorie_A_autres"] * 0.5 * 0.10)
        cout = sq.prelevements_activite(p)["public"]["cout"]
        return {"taux": hausse, "montant": cout * hausse,
                "versants": p.val("statu_quo.versants_fonction_publique")}

    def pensions_62(self, p: Parametres, s: str) -> dict[int, float]:
        """Pensions en plus avec le retour à 62 ans (Md€ de 2026) : moteur/bibliotheque.baisse_age_legal_detail (même
        calcul que Glucksmann et Mélenchon depuis la relecture neutre du 11/11/2026 : âge légal réel des générations au
        statu quo, suspension de la LFSS 2026 comprise, calage sur la masse de droit direct)."""
        from moteur import bibliotheque as bib
        det = bib.baisse_age_legal_detail(p, s, {self.v("retraites.annee_retour"): self.v("retraites.profil_62_ans")})
        # personnes pas encore retraitées en moins, pour l'emploi des seniors (offre.seniors)
        self._non_retraites = getattr(self, "_non_retraites", {})
        self._non_retraites[(id(p), s)] = {t: -v for t, v in det["retraites_en_plus"].items()}
        return det["pensions"]

    def smic(self, p: Parametres) -> dict[str, float]:
        """SMIC à 2 000 € brut (Md€ de 2026 à l'économie de 2029, effet plein) et emplois perdus, scénario par
        scénario pour l'élasticité. Table OpenFisca de 2026 lue au salaire relevé : les allègements restent au barème
        de 2026 (nominalisés), ce qui est la lecture du programme (p. 67)."""
        from moteur.recettes.impot_salaires import effectifs_prive_2026
        from moteur.systeme_actuel import _interp, _table_openfisca
        T = _table_openfisca()
        brut, cout = T["brut"], T["cout_du_travail"]
        b_smic = self.v("smic.smic_brut_mensuel_2026") * 12
        infl27 = p.val("inflation.base")["2027"]
        b_new = self.v("smic.smic_programme") * 12 / (1 + infl27)
        plafond = self.v("smic.diffusion_jusqu_a") * b_new
        taux_tva = p.val("systeme_actuel.taux_tva_moyen")
        part_marge = self.v("smic.part_marge_absorbee")

        def cout_de(b):
            return _interp(b, brut, cout)

        def brut_de(c):
            return _interp(c, cout, brut)

        def lev(c):  # prélèvements (cotisations, CSG, CRDS, IR) au coût c
            return c - (_interp(c, cout, T["salaire_net"]) + _interp(c, cout, T["impot_revenu_restant_a_payer"]))

        def net(c):
            return _interp(c, cout, T["salaire_net"]) + _interp(c, cout, T["impot_revenu_restant_a_payer"])

        def aides(c):
            return _interp(c, cout, T["ppa"]) + _interp(c, cout, T["rsa"]) + _interp(c, cout, T["aide_logement"])
        d = effectifs_prive_2026(p)
        out = {"prelevements": 0.0, "aides": 0.0, "tva": 0.0, "is": 0.0, "hausse_cout": 0.0,
               "emplois_ponderes": 0.0, "perte_par_emploi": 0.0, "salaries_touches": 0.0}
        pertes = []
        for c, n in zip(d.milieux, d.effectifs):
            b = brut_de(c)
            if b >= plafond:
                continue
            # distribution en salaire annuel : sous le SMIC annuel, temps partiel ou année incomplète, hausse
            # proportionnelle (salaire horaire au SMIC) ; au-dessus, rattrapage du nouveau SMIC puis diffusion
            # décroissante jusqu'au plafond
            if b <= b_smic:
                b2 = b * b_new / b_smic
            else:
                diff = (b_new - b_smic) * max(0.0, 1 - (b - b_smic) / (plafond - b_smic))
                b2 = max(b + diff, b_new)
            c2 = cout_de(b2)
            dc = c2 - c
            if dc <= 0:
                continue
            out["salaries_touches"] += n
            out["prelevements"] += n * (lev(c2) - lev(c))
            out["aides"] += n * (aides(c2) - aides(c))
            out["tva"] += n * taux_tva * ((net(c2) + aides(c2)) - (net(c) + aides(c)))
            out["is"] += -n * 0.25 * part_marge * dc
            out["hausse_cout"] += n * dc
            out["emplois_ponderes"] += n * dc / c  # × élasticité = emplois perdus
            pertes.append((n * dc / c, lev(c2) + taux_tva * net(c2) + self.v("smic.valeur_emploi_chomeur"), c2))
        poids = sum(x[0] for x in pertes)
        out["perte_par_emploi"] = sum(x[0] * x[1] for x in pertes) / poids
        out["cout_moyen_emploi_perdu"] = sum(x[0] * x[2] for x in pertes) / poids
        out["hausse_brut_smic"] = b_new / b_smic - 1
        out["hausse_cout_smic"] = cout_de(b_new) / cout_de(b_smic) - 1
        for k in ("prelevements", "aides", "tva", "is", "hausse_cout"):
            out[k] /= 1e9
        return out

    def tabac(self, p: Parametres, s: str) -> dict[int, float]:
        """Part des adultes nés en 2014 ou après (génération sans tabac)."""
        g0 = self.v("tabac.premiere_generation")
        pop = sq.population(p, s)
        out = {}
        for t in ANNEES:
            v = pop[t]
            adultes = sum(v[18:])
            jeunes = sum(v[a] for a in range(18, len(v)) if t - a >= g0)
            out[t] = jeunes / adultes
        return out

    # ------------------------------------------------------------------ assemblage
    def emploi_mesures(self, p: Parametres, s: str, liste: list, e: dict, valeur_emploi: float, ip: dict) -> dict:
        """Effets sur l'emploi et le chômage des mesures qui en ont (groupe tondelier_emploi), par année :
        emplois par canal (contre le statu quo), chômeurs en plus (+) ou en moins (−), actifs en plus, et mesures
        budgétaires de ces effets (effet_macro), au prix d'un emploi au SMIC comme les emplois perdus du SMIC."""
        w = sq.salaires(p, s)
        cout = self.v("emploi.cout_poste_public")
        parts = self.v("emploi.postes")
        ev = sq._v(p, "emploi_public.eviction_privee", s)
        postes = {t: 0.0 for t in ANNEES}
        for m in liste:
            if m.note in parts:
                for t in ANNEES:
                    postes[t] += parts[m.note] * m.valeurs.get(t, 0.0) * 1e9 / (cout * w[t] / w[2029])
        g = self.v("emploi.garantie_emploi")
        rec = g["recours"][s]
        tz = {t: g["eligibles"] * rec * (1 - g["eviction"]) * min(1.0, max(0.0, (t - g["debut"] + 1) / (g["plein"] - g["debut"] + 1)))
              for t in ANNEES}
        pts = self.v("emploi.assurance_chomage", s)
        actifs_sq = {t: e[t]["emploi"] + e[t]["chomeurs"] for t in ANNEES}
        ac = {t: pts * actifs_sq[t] * min(1.0, max(0.0, (t - 2027) / 3)) for t in ANNEES}
        canaux = {t: {"Postes publics créés": postes[t], "Éviction d'emplois privés par les postes publics": -ev * postes[t],
                      "Garantie d'emploi à 55 ans (Territoires zéro chômeur)": tz[t],
                      "Assurance chômage : réformes abrogées": -ac[t]} for t in ANNEES}
        net_pub = {t: (1 - ev) * postes[t] for t in ANNEES}
        chomeurs = {t: -net_pub[t] - g["part_venant_du_chomage"] * tz[t] + ac[t] for t in ANNEES}
        actifs = {t: (1 - g["part_venant_du_chomage"]) * tz[t] for t in ANNEES}
        mesures = [
            Mesure("Emploi : chômeurs en plus quand les réformes de l'assurance chômage sont abrogées", "recettes",
                   {t: -ac[t] * valeur_emploi / 1e9 * ip[t] for t in ANNEES}, nature="effet_macro"),
            Mesure("Emploi : emplois privés évincés par les postes publics", "recettes",
                   {t: -ev * postes[t] * valeur_emploi / 1e9 * ip[t] for t in ANNEES}, nature="effet_macro"),
        ]
        return {"canaux": canaux, "chomeurs": chomeurs, "actifs": actifs, "mesures": mesures}

    def ecologie(self, p: Parametres, s: str) -> list[Mesure]:
        """Effets physiques des mesures écologiques (groupe tondelier_ecologie) : une mesure sans montant chacune,
        dont le coût est déjà dans les mesures budgétaires."""
        from moteur.ecologie import emissions as em
        out = []
        for nom, par in self.pt._p.items():
            if not nom.startswith("tondelier_ecologie."):
                continue
            x = par.valeur
            serie = em.profil(p, s, x)
            out.append(Mesure(f"{x['id']} — {x['libelle']} (émissions)", "recettes", {}, "physique",
                              physique={f"emissions_mt:{x['secteur']}": serie},
                              vert="defavorable" if max(serie.values()) > 0 else "favorable"))
        return out

    def _calcul(self, p: Parametres) -> dict:
        cle = id(p)
        if cle in self._cache:
            return self._cache[cle]
        part_fp = self.part_prelevements_fp(p)
        fp2 = self.remunerations_publiques(p)
        smic = self.smic(p)
        mes_s, ctx_s, details = {}, {}, {}
        for s in sq.SCENARIOS:
            idx = self._indices(p, s)
            liste: list[Mesure] = []
            # mesures simples
            for nom, par in self.pt._p.items():
                if not nom.startswith("tondelier_mesures."):
                    continue
                x = dict(par.valeur)
                if x["montant"] == "auto":
                    continue
                x["_montant"] = x["montant"][s]
                serie = self._serie(x, idx)
                liste.append(Mesure(f"{x['id']} — {x['libelle']}", x["poste"], serie, note=nom.split(".")[1],
                                    instrument=x.get("instrument", ""), incidence=x.get("incidence", "")))
                if x.get("fp"):
                    liste.append(Mesure(f"{x['id']} — prélèvements sur ces rémunérations", "recettes",
                                        {t: x.get("fp_taux", part_fp) * v for t, v in serie.items()}, nature="mesure",
                                        note=nom.split(".")[1]))
            # FP-02 : rémunérations publiques, par versant, et pensions des fonctionnaires
            ia = idx["bloc:autres"]
            x = {"debut": 2028, "plein": 2032, "_montant": fp2["montant"], "moteur": "bloc:autres"}
            for versant, poste in VERSANTS.items():
                part = fp2["versants"][versant]
                if poste == "etat_missions" and versant == "etat_militaires":
                    continue
                if versant == "etat_civils":
                    part += fp2["versants"]["etat_militaires"]
                serie = {t: self._profil(x, t) * part * (ia[t] if t >= 2029 else 1.0) for t in (*ANNEES_AVANT, *ANNEES)}
                liste.append(Mesure(f"FP-02 — rémunérations publiques +{fp2['taux']*100:.1f} % ({poste})", poste, serie))
                liste.append(Mesure(f"FP-02 — prélèvements sur ces rémunérations ({poste})", "recettes",
                                    {t: part_fp * v for t, v in serie.items()}))
            pens = self.v("fp.pensions_fonction_publique")
            liste.append(Mesure("FP-02 — pensions des fonctionnaires (départs après la hausse)", "retraites",
                                {t: pens * fp2["taux"] * min(1.0, max(0.0, (t - 2028) / 35)) * (idx["pensions"][t] if t >= 2029 else 1.0)
                                 for t in (*ANNEES_AVANT, *ANNEES)}))
            # RET-01 : retour à 62 ans
            p62 = self.pensions_62(p, s)
            serie = {2027: 0.0, 2028: 0.5 * p62[2029], **p62}
            liste.append(Mesure("RET-01 — retour à 62 ans", "retraites", serie))
            taux_prel_ret = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
            liste.append(Mesure("RET-01 — prélèvements sur les pensions en plus", "recettes",
                                {t: taux_prel_ret * v for t, v in serie.items()}))
            # COT-04 : la CSG +1 point sur les salaires fait monter la prime d'activité et les aides (OpenFisca)
            st = offre.statique_openfisca(p, "csg_activite_plus1")
            x = dict(self.pt.val("tondelier_mesures.csg_un_point"))
            x["_montant"] = st["prestations_en_plus"]
            liste.append(Mesure("COT-04 — prime d'activité, RSA et aides au logement en plus (salaire net plus bas)",
                                "pauvrete", self._serie(x, idx)))
            # REC-45 bis : génération sans tabac
            tb = self.tabac(p, s)
            acc = self.v("tabac.accises_tabac")
            liste.append(Mesure("REC-45 — génération sans tabac (nés en 2014 et après)", "recettes",
                                {**{t: 0.0 for t in ANNEES_AVANT}, **{t: -acc * tb[t] * idx["pib"][t] for t in ANNEES}}))
            # PRE-01 : SMIC à 2 000 €
            montee = {2027: 0.5, 2028: 1.0}
            ip = idx["pib"]

            def ser(v, montee_=montee):
                return {**{t: v * montee_[t] for t in ANNEES_AVANT}, **{t: v * ip[t] for t in ANNEES}}
            liste.append(Mesure("PRE-01 — SMIC à 2 000 € : prélèvements sur les hausses de salaire", "recettes", ser(smic["prelevements"])))
            liste.append(Mesure("PRE-01 — SMIC à 2 000 € : TVA sur les revenus en plus", "recettes", ser(smic["tva"])))
            liste.append(Mesure("PRE-01 — SMIC à 2 000 € : prime d'activité et aides en moins", "pauvrete", ser(smic["aides"])))
            liste.append(Mesure("PRE-01 — SMIC à 2 000 € : IS sur les marges réduites", "recettes", ser(smic["is"])))
            el = self.v("smic.elasticite_emploi", s)
            emplois = -el * smic["emplois_ponderes"]  # emplois perdus (> 0)
            montee_emploi = {2027: 1 / 3, 2028: 2 / 3}
            perte = emplois * smic["perte_par_emploi"] / 1e9
            pe = {**{t: -perte * montee_emploi[t] for t in ANNEES_AVANT},
                  **{t: -perte * min(1.0, (t - 2026) / 3) * ip[t] for t in ANNEES}}
            liste.append(Mesure(f"PRE-01 — SMIC à 2 000 € : emplois perdus ({emplois/1e3:.0f} 000)", "recettes", pe, nature="effet_macro"))
            # effet macroéconomique : impulsion budgétaire nette
            annees = (*ANNEES_AVANT, *ANNEES)
            # chaque mesure pondérée selon ce qu'elle est (demande par instrument, moteur/offre.poids_demande)
            cout_net = offre.impulsion(p, liste, annees)
            y = sq.pib(p, s)
            rec_sq = sq.recettes(p, s)
            dpib = multiplicateur(p, s, cout_net, annees)
            part_rec = {t: rec_sq[t] / y[t] for t in ANNEES}
            part_rec.update({t: part_rec[2029] for t in ANNEES_AVANT})
            if self.v("macro.multiplicateur_actif"):
                liste.append(Mesure("Effet macro : multiplicateur sur l'impulsion budgétaire des mesures", "recettes",
                                    {t: dpib[t] * part_rec[t] for t in annees}, nature="effet_macro"))
            # PIB : multiplicateur et emplois perdus (valeur ajoutée ≈ coût de l'emploi × 1,25)
            pib_emplois = {t: -emplois * min(1.0, (t - 2026) / 3) * smic["cout_moyen_emploi_perdu"] * 1.25 / 1e9 * ip[t] for t in ANNEES}
            pib = {t: y[t] + (dpib[t] if self.v("macro.multiplicateur_actif") else 0.0) + pib_emplois[t] for t in ANNEES}
            e = sq.effectifs(p, s)
            # conjoncture : l'impulsion budgétaire change l'emploi comme l'ajustement du modèle (même règle que le moteur
            # d'Écologie de droite : macro.emplois_par_point_pib emplois pour 1 % de PIB)
            k_emp = sq._v(p, "macro.emplois_par_point_pib", s)
            conj = {t: (dpib[t] if self.v("macro.multiplicateur_actif") else 0.0) / y[t] * k_emp * e[t]["emploi"] for t in ANNEES}
            chom = {t: (e[t]["chomeurs"] + emplois * min(1.0, (t - 2026) / 3) - conj[t]) / (e[t]["emploi"] + e[t]["chomeurs"]) * 100 for t in ANNEES}
            # emploi : postes publics, garantie d'emploi, assurance chômage (tondelier_emploi)
            em = self.emploi_mesures(p, s, liste, e, smic["perte_par_emploi"], ip)
            liste.extend(em["mesures"])
            chom = {t: chom[t] + em["chomeurs"][t] / (e[t]["emploi"] + e[t]["chomeurs"] + em["actifs"][t]) * 100
                    for t in ANNEES}
            # canal d'offre commun (moteur/offre.py) : effet durable des impôts et des transferts
            canaux_offre, actifs_offre = {}, {t: 0.0 for t in ANNEES}
            if offre.actif(p):
                of = offre.effets(p, s, liste)
                liste.append(of["mesure"])
                for t in ANNEES:
                    pib[t] += of["dpib"][t]
                canaux_offre, actifs_offre = of["emplois"], of["actifs"]
                for t in ANNEES:
                    d = sum(v[t] for v in canaux_offre.values())
                    act = e[t]["emploi"] + e[t]["chomeurs"] + em["actifs"][t]
                    chom_t = chom[t] / 100 * act - (d - actifs_offre[t])
                    chom[t] = chom_t / (act + actifs_offre[t]) * 100
                details_offre = of["detail"]
            else:
                details_offre = {}
            # emploi des seniors : retour à 62 ans, moins de personnes en emploi et au chômage (offre.seniors, scénario
            # miroir : un âge abaissé fait perdre des emplois)
            sen = offre.seniors(p, s, self._non_retraites[(id(p), s)], baisse_age=True)
            liste.extend(sen["mesures"])
            for t in ANNEES:
                pib[t] += sen["pib"][t]
                act = e[t]["emploi"] + e[t]["chomeurs"] + em["actifs"][t] + actifs_offre[t]
                chom[t] = (chom[t] / 100 * act + sen["chomeurs"][t]) / (act + sen["actifs"][t]) * 100
            # dette de fin 2028 : mesures de 2027 et 2028 (recettes et dépenses), effet macro compris
            avant = sum(-(m.valeurs.get(t, 0.0)) if m.poste == "recettes" else m.valeurs.get(t, 0.0)
                        for m in liste for t in ANNEES_AVANT if m.poste != "participations")
            perdus = {t: emplois * min(1.0, (t - 2026) / 3) for t in ANNEES}
            ctx_s[s] = {"pib": pib, "chomage": chom, "dette_depart": sq.dette_fin_2028(p) + avant,
                        "emploi": {t: e[t]["emploi"] - perdus[t] + conj[t] + sum(em["canaux"][t].values())
                                   + sum(v[t] for v in canaux_offre.values()) + sen["emplois"][t] for t in ANNEES},
                        "emplois_canaux": {t: {"SMIC à 2 000 € : emplois perdus": -perdus[t],
                                               "Conjoncture (impulsion budgétaire)": conj[t], **em["canaux"][t],
                                               **{c: v[t] for c, v in canaux_offre.items()},
                                               "Seniors : emploi (âge de la retraite)": sen["emplois"][t]} for t in ANNEES}}
            liste.extend(self.ecologie(p, s))
            mes_s[s] = liste
            details[s] = {"emplois_perdus_smic": emplois, "avant_2029": avant, "dpib": dpib, "offre": details_offre}
        res = {"mesures": mes_s, "contexte": ctx_s, "details": details, "smic": smic, "fp2": fp2, "part_fp": part_fp}
        self._cache[cle] = res
        return res

    def mesures(self, p: Parametres) -> dict[str, list[Mesure]]:
        return self._calcul(p)["mesures"]

    def contexte(self, p: Parametres) -> dict[str, dict]:
        return self._calcul(p)["contexte"]


def programme() -> Tondelier:
    return Tondelier()
