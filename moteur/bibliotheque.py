"""Bibliothèque de mesures sur le système actuel, communes à tous les programmes (6 novembre 2026).

Point 3 de la feuille de route multi-programmes (docs/architecture.md) : chaque mesure fréquente est calculée une fois,
sur les mêmes données que le statu quo, et chaque programme lui passe ses paramètres. Premières briques :

- report_age_legal : pensions en moins quand l'âge légal passe au-delà de 64 ans (même calcul et même calage que
  statu_quo.retraites, profil de départ décalé génération par génération, comme ancien_systeme._part) ;
- csg_activite : CSG sur les salaires du privé et des agents publics (OpenFisca 2026 sur les distributions de 2026)
  et impôt sur le revenu en plus quand la CSG déductible disparaît ;
- smic : relèvement du SMIC (table OpenFisca de 2026 lue au salaire relevé), privé et agents publics ;
- defense_sans_lpm : écart de la défense entre la loi de programmation (statu quo) et le niveau de 2026.

Les montants sont en Md€ de 2026 à l'économie de 2029 (économie de 2026 placée en 2029), comme le reste du noyau.
Le programme Tondelier garde pour l'instant son propre calcul du SMIC et du retour à 62 ans (à rebrancher ici).
"""
from __future__ import annotations

from . import statu_quo as sq
from .noyau import ANNEES, Mesure
from .parametres import Parametres


# ---------------------------------------------------------------------------------------------------- retraites
def report_age_legal(p: Parametres, s: str, age_cible: float, premiere_generation: int,
                     pas_par_generation: float) -> dict[int, float]:
    """Pensions en moins (Md€ de 2026, > 0 = économie) quand l'âge légal passe de 64 ans à age_cible (voir
    report_age_legal_detail)."""
    return report_age_legal_detail(p, s, age_cible, premiere_generation, pas_par_generation)["pensions"]


def _cadre_pensions(p: Parametres, s: str):
    pop = sq.population(p, s)
    w = sq.salaires(p, s)
    lag = int(p.val("statu_quo.retraites_decalage_carriere"))
    e = p.val("statu_quo.retraites_erosion_relative")
    nouveau = p.val("ancien_systeme.pension_nouveaux_relative")

    def niveau(depart: int) -> float:
        if depart < 2029:
            return 1.0
        return nouveau * w[depart - lag] / w[2029 - lag] * (1 - e) ** (depart - 2029)
    return pop, niveau


def _pensions_et_retraites(p: Parametres, s: str, part) -> tuple[dict[int, float], dict[int, float]]:
    """Pensions brutes (non calées) et retraités, part(g, b) = part de la génération g partie à l'âge b."""
    from .demographie import AGE_MAX
    pop, niveau = _cadre_pensions(p, s)
    # part(g, ·) et niveau(·) gardés en tableaux (R1, 25/11/2026) : mêmes valeurs, mêmes opérations dans le même ordre
    # (résultat identique au bit près), sans les millions d'appels de fonction de la triple boucle
    parts: dict[int, list[float]] = {}
    niv: dict[int, float] = {}
    dep_t, ret_t = {}, {}
    for t in ANNEES:
        dep = ret = 0.0
        for a in range(50, AGE_MAX + 1):
            n, g = pop[t][a], t - a
            pg = parts.get(g)
            if pg is None:
                pg = parts[g] = [part(g, b) for b in range(49, AGE_MAX + 1)]  # pg[b - 49]
            cumul = 0.0
            prec = pg[0]
            for b in range(50, a + 1):
                cur = pg[b - 49]
                d = cur - prec
                prec = cur
                if d > 0:
                    nv = niv.get(g + b)
                    if nv is None:
                        nv = niv[g + b] = niveau(g + b)
                    dep += n * d * nv
                    cumul += d
            ret += n * min(1.0, cumul)
        dep_t[t], ret_t[t] = dep, ret
    return dep_t, ret_t


def _calage(p: Parametres, s: str, b0: dict[int, float]) -> float:
    """Coefficient de calage d'un écart de pensions de droit direct : masse du statu quo en 2029 × part de droit
    direct, rapportée au calcul par génération (relecture neutre du 07/11/2026 : la réversion et le minimum
    vieillesse ne bougent pas avec l'âge de départ)."""
    return sq.retraites(p, s)[2029]["depenses"] * p.val("ancien_systeme.part_droit_direct") / b0[2029]


def report_age_legal_detail(p: Parametres, s: str, age_cible: float, premiere_generation: int,
                            pas_par_generation: float) -> dict:
    """Pensions en moins (Md€ de 2026, > 0 = économie) et personnes pas encore retraitées en plus, quand l'âge légal
    passe à age_cible.

    Référence : profil de départ de chaque génération au statu quo (ancien_systeme.profil_generation : loi de 2023 et
    suspension de la LFSS 2026). Génération g : report = min(age_cible − 64, (g − premiere_generation + 1) ×
    pas_par_generation), ajouté à l'âge légal de la génération ; le profil est décalé de ce report à partir de l'âge
    légal, mais pas au-delà de l'âge du taux plein automatique (67 ans, inchangé) : à partir de cet âge, la part
    partie est celle du statu quo. Même calcul des pensions que statu_quo.retraites, calage sur la masse de droit
    direct. Les personnes pas encore retraitées sont réparties entre emploi, chômage et inactivité par offre.seniors."""
    from .ancien_systeme import _part, profil_generation
    base, age_legal = profil_generation(p)
    ecart = age_cible - p.val("ancien_systeme.age_legal_actuel")
    a_tp = int(p.val("ancien_systeme.age_taux_plein"))

    def report(g: int) -> float:
        return min(ecart, max(0.0, (g - premiere_generation + 1) * pas_par_generation))
    cache = {}

    def avec(g: int, b: int) -> float:
        if g not in cache:
            r, rep, al = base.profil(g), report(g), int(age_legal(g))
            cache[g] = {bb: (r[bb] if bb >= a_tp else min(r[bb], _part(r, bb, rep, al))) for bb in r}
        return cache[g][b]
    (b0, n0), (b1, n1) = _pensions_et_retraites(p, s, base), _pensions_et_retraites(p, s, avec)
    k = _calage(p, s, b0)
    return {"pensions": {t: k * (b0[t] - b1[t]) for t in ANNEES}, "non_retraites": {t: n0[t] - n1[t] for t in ANNEES}}


def baisse_age_legal_detail(p: Parametres, s: str, etapes: dict[int, dict]) -> dict:
    """Pensions en plus (Md€ de 2026, > 0 = dépense) et personnes retraitées en plus quand l'âge légal baisse, profil
    de départ par année de départ.

    Référence : profil de chaque génération au statu quo (ancien_systeme.profil_generation : loi de 2023 et
    suspension de la LFSS 2026). etapes : {année de départ: profil {âge: part de la génération partie}} ; les départs
    d'avant la première étape suivent le statu quo ; entre deux étapes, mélange linéaire des deux profils selon
    l'année de départ ; après la dernière, le dernier profil. Une génération dont l'âge légal au statu quo est déjà
    plus bas que celui du programme garde le statu quo (part = max des deux). Même calcul des pensions que
    statu_quo.retraites, calage sur la masse de droit direct. Exemple : {2028: profil à 62 ans, 2032: profil à 60 ans}."""
    from .ancien_systeme import _complet, profil_generation
    base, _ = profil_generation(p)
    ans = sorted(etapes)
    prof = {a: _complet(etapes[a]) for a in ans}
    cache_a = {}

    def profil_annee(annee: int):
        if annee not in cache_a:
            if annee < ans[0]:
                cache_a[annee] = None
            elif annee >= ans[-1]:
                cache_a[annee] = prof[ans[-1]]
            else:
                i = max(k for k in range(len(ans)) if ans[k] <= annee)
                a0, a1 = ans[i], ans[i + 1]
                lam = (annee - a0) / (a1 - a0)
                cache_a[annee] = {b: (1 - lam) * prof[a0][b] + lam * prof[a1][b] for b in prof[a0]}
        return cache_a[annee]
    cache = {}

    def avec(g: int, b: int) -> float:
        # part cumulée : pour chaque âge, la part partie selon le profil en vigueur l'année de cet âge, jamais en
        # dessous de la part déjà partie (cumul croissant), ni en dessous du statu quo de la génération
        if g not in cache:
            r = base.profil(g)
            out, prec = {}, 0.0
            for bb in range(0, 106):
                pa = profil_annee(g + bb)
                v = r[bb] if pa is None else max(r[bb], pa[bb])
                prec = max(prec, v)
                out[bb] = prec
            cache[g] = out
        return cache[g][b]
    (b0, n0), (b1, n1) = _pensions_et_retraites(p, s, base), _pensions_et_retraites(p, s, avec)
    k = _calage(p, s, b0)
    return {"pensions": {t: k * (b1[t] - b0[t]) for t in ANNEES}, "retraites_en_plus": {t: n1[t] - n0[t] for t in ANNEES}}


# ---------------------------------------------------------------------------------------------------- salaires
def _tables_publiques(p: Parametres) -> dict[str, float]:
    return p.val("statu_quo.versants_fonction_publique")


def csg_activite(p: Parametres) -> dict[str, float]:
    """CSG sur les salaires (Md€ de 2026, économie de 2026 placée en 2029), OpenFisca 2026 sur les distributions de
    2026 (privé : Insee ; public : DGAFP, versants pondérés comme statu_quo.prelevements_activite), et impôt sur le
    revenu en plus si elle disparaît : la part déductible (6,8 points sur 9,2) rentre dans le revenu imposable,
    lue sur le barème d'OpenFisca au salaire qui donne ce revenu imposable en plus."""
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
    from .systeme_actuel import _interp, _table_openfisca
    part_deductible = 6.8 / 9.2

    def somme(d, tables: dict[str, float]) -> tuple[float, float]:
        csg = ir = 0.0
        for c, n in zip(d.milieux, d.effectifs):
            for nom, w in tables.items():
                T = _table_openfisca() if nom == "prive" else _table_openfisca(versant=nom)
                x = T["cout_du_travail"]
                b = _interp(c, x, T["brut"])
                net = _interp(c, x, T["salaire_net"])
                g = -_interp(c, x, T["csg"])
                if b <= 0 or net <= 0:
                    continue
                db = part_deductible * g * b / net  # brut en plus qui donne ce revenu imposable en plus
                ir0 = _interp(b, T["brut"], T["impot_revenu_restant_a_payer"])
                ir1 = _interp(b + db, T["brut"], T["impot_revenu_restant_a_payer"])
                csg += w * n * g
                ir += w * n * -(ir1 - ir0)
        return csg / 1e9, ir / 1e9
    cp, ip = somme(effectifs_prive_2026(p), {"prive": 1.0})
    cu, iu = somme(effectifs_public_2026(p), _tables_publiques(p))
    return {"csg_prive": cp, "csg_public": cu, "ir_prive": ip, "ir_public": iu}


def smic(p: Parametres, brut_cible_2026: float, diffusion_jusqu_a: float, part_marge: float,
         valeur_emploi_chomeur: float, smic_brut_mensuel_2026: float | None = None,
         allegements_suivent_smic: bool = False) -> dict:
    """Relèvement du SMIC à brut_cible_2026 € brut par mois (euros de 2026), même mécanique que le programme Tondelier
    (table OpenFisca de 2026 lue au salaire relevé : les allègements restent au barème de 2026).

    Privé : prélèvements et TVA en plus, aides en moins, IS sur les marges prises (25 % de part_marge), emplois perdus
    pondérés (× élasticité dans le programme). Agents publics : hausse de coût (dépense), prélèvements et TVA en plus,
    aides en moins ; pas d'emploi perdu (l'employeur public paie). La hausse décroît linéairement jusqu'à zéro à
    diffusion_jusqu_a × le nouveau SMIC."""
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
    from .systeme_actuel import _interp, _table_openfisca
    if smic_brut_mensuel_2026 is None:
        smic_brut_mensuel_2026 = p.val("profils.smic_brut_mensuel_2026")
    b_smic, b_new = smic_brut_mensuel_2026 * 12, brut_cible_2026 * 12
    plafond = diffusion_jusqu_a * b_new
    taux_tva = p.val("systeme_actuel.taux_tva_moyen")
    rc_is = p.val("entreprises.retour_is_charges")  # même règle que les autres charges des employeurs privés
    taux_is = rc_is["taux_is_effectif"] * rc_is["part_employeurs_is"]

    def calcul(d, tables: dict[str, float], prive: bool) -> dict:
        out = {"prelevements": 0.0, "aides": 0.0, "tva": 0.0, "is": 0.0, "hausse_cout": 0.0,
               "emplois_ponderes": 0.0, "salaries_touches": 0.0, "chocs": []}
        pertes = []
        for nom, wv in tables.items():
            T = _table_openfisca() if nom == "prive" else _table_openfisca(versant=nom)
            brut, cout = T["brut"], T["cout_du_travail"]

            def lev0(c):
                return c - (_interp(c, cout, T["salaire_net"]) + _interp(c, cout, T["impot_revenu_restant_a_payer"]))

            def net0(c):
                return _interp(c, cout, T["salaire_net"]) + _interp(c, cout, T["impot_revenu_restant_a_payer"])
            # les allègements ne concernent que le privé : la grille des agents publics reste en euros
            k = b_new / b_smic if (allegements_suivent_smic and prive) else 1.0
            tau3 = _interp(3 * b_smic, brut, cout) / (3 * b_smic)  # coût / brut sans allègement (fin à 3 SMIC)

            def allegement(b):  # allègement de 2026 au brut b (coût sans allègement − coût)
                return max(0.0, b * tau3 - _interp(b, brut, cout))

            def extra(b2):  # allègement en plus quand le barème est lu en multiples du nouveau SMIC
                return k * allegement(b2 / k) - allegement(b2) if k != 1.0 else 0.0

            def cout_de(b2):
                return _interp(b2, brut, cout) - extra(b2)

            def lev(c, b2=None):  # prélèvements au coût c ; après la mesure : au brut b2, allègement en plus déduit
                if b2 is None:
                    return lev0(c)
                return lev0(_interp(b2, brut, cout)) - extra(b2)

            def net(c, b2=None):
                return net0(c) if b2 is None else net0(_interp(b2, brut, cout))

            def aides(c):
                return _interp(c, cout, T["ppa"]) + _interp(c, cout, T["rsa"]) + _interp(c, cout, T["aide_logement"])
            for c, n in zip(d.milieux, d.effectifs):
                n = n * wv
                b = _interp(c, cout, brut)
                if b >= plafond:
                    if k == 1.0:
                        continue
                    b2 = b  # salaire inchangé, mais allègements (en multiples du SMIC) qui s'étendent jusqu'à lui
                    if b >= 3 * b_new:
                        continue
                elif b <= b_smic:
                    b2 = b * b_new / b_smic
                else:
                    diff = (b_new - b_smic) * max(0.0, 1 - (b - b_smic) / (plafond - b_smic))
                    b2 = max(b + diff, min(b_new, plafond))
                c2 = cout_de(b2)
                dc = c2 - c
                if dc == 0 or (dc < 0 and k == 1.0):
                    continue
                if b2 > b:
                    out["salaries_touches"] += n
                out["prelevements"] += n * (lev(c2, b2) - lev(c))
                out["aides"] += n * (aides(c2) - aides(c))
                out["tva"] += n * taux_tva * ((net(c2, b2) + aides(c2)) - (net(c) + aides(c)))
                out["hausse_cout"] += n * dc
                if prive:
                    out["is"] += -n * taux_is * part_marge * dc
                    out["emplois_ponderes"] += n * dc / c
                    out["chocs"].append((n, c2 / c))
                    pertes.append((n * dc / c, lev(c2, b2) + taux_tva * net(c2, b2) + valeur_emploi_chomeur, c2))
        if pertes:
            poids = sum(x[0] for x in pertes)
            out["perte_par_emploi"] = sum(x[0] * x[1] for x in pertes) / poids
            out["cout_moyen_emploi_perdu"] = sum(x[0] * x[2] for x in pertes) / poids
        for k in ("prelevements", "aides", "tva", "is", "hausse_cout"):
            out[k] /= 1e9
        return out
    T = _table_openfisca()
    return {"prive": calcul(effectifs_prive_2026(p), {"prive": 1.0}, True),
            "public": calcul(effectifs_public_2026(p), _tables_publiques(p), False),
            "hausse_brut_smic": b_new / b_smic - 1,
            "hausse_cout_smic": _interp(b_new, T["brut"], T["cout_du_travail"]) / _interp(b_smic, T["brut"], T["cout_du_travail"]) - 1}


def brut_de_net_mensuel(net_mensuel_2026: float) -> float:
    """Salaire brut mensuel (euros de 2026) qui donne ce net mensuel, barème OpenFisca 2026 du privé."""
    from .systeme_actuel import _interp, _table_openfisca
    T = _table_openfisca()
    return _interp(net_mensuel_2026 * 12, T["salaire_net"], T["brut"]) / 12


# ---------------------------------------------------------------------------------------------------- dépenses
def defense_sans_lpm(p: Parametres, s: str) -> dict[int, float]:
    """Dépense de défense en moins (Md€ de 2026, > 0) si elle reste au niveau du PLF 2027 au lieu de suivre la loi de
    programmation militaire actualisée (statu_quo.defense_trajectoire : « 2026 » contre « lpm »)."""
    a = sq.blocs(p, s)
    b = sq.blocs(p.avec({"statu_quo.defense_trajectoire": "2026"}), s)
    return {t: a[t]["defense_ue"] - b[t]["defense_ue"] for t in ANNEES}


def baisse_prelevements_salaries(p: Parametres, idx: dict, montant: float, part_ir: float, debut: int, nom: str,
                                 deductible: float = 1.0) -> list:
    """Baisse uniforme de prélèvements salariaux (Md€ de 2026, > 0) sur les revenus d'activité, répartie entre privé et
    agents publics comme la CSG (csg_activite), avec l'impôt sur le revenu en plus (part déductible des prélèvements
    supprimés, rapportée aux 6,8 points déductibles de la CSG sur 9,2, × part_ir : part retrouvée dans l'impôt réel) et
    la prime d'activité, le RSA et les aides au logement en moins (OpenFisca, à proportion de la suppression de la CSG).
    Forme d'incidence : celle de la suppression de la CSG (OpenFisca). Utilisée par Attal (« droit au brut ») et
    Retailleau (restitution aux salariés). Cotisations salariales : deductible = 1 ; CSG : deductible = 6,8 / 9,2."""
    from . import offre
    inc = "openfisca:csg_activite_supprimee"
    c = csg_activite(p)
    f = montant / (c["csg_prive"] + c["csg_public"])
    k_ded = deductible * 9.2 / 6.8
    st = offre.statique_openfisca(p, "csg_activite_supprimee")

    def ser(v, indice):
        return {**{t: (v if t >= debut else 0.0) for t in (2027, 2028)}, **{t: v * idx[indice][t] for t in ANNEES}}
    return [
        Mesure(f"{nom} (privé)", "recettes", ser(-f * c["csg_prive"], "recette:salaires_prive"),
               instrument="travail", incidence=inc),
        Mesure(f"{nom} (agents publics)", "recettes", ser(-f * c["csg_public"], "recette:salaires_public"),
               instrument="travail", incidence=inc),
        Mesure(f"{nom} : impôt sur le revenu en plus (prélèvements déductibles en moins)", "recettes",
               ser(f * part_ir * k_ded * (c["ir_prive"] + c["ir_public"]), "recette:salaires_prive"),
               instrument="travail", incidence=inc),
        Mesure(f"{nom} : prime d'activité, RSA et aides au logement en moins", "pauvrete",
               ser(f * st["prestations_en_plus"], "recette:salaires_prive")),
    ]


def capitalisation_obligatoire(p: Parametres, s: str, c: dict, ident: str) -> tuple[list[Mesure], dict[int, float]]:
    """Part de retraite par capitalisation obligatoire, versée par les salariés et les employeurs à un fonds hors des
    administrations publiques (règle commune, 16/11/2026 ; première lecture : RET-RET-02 de Retailleau).

    c : {taux, part_employeur, plafond_mensuel, brut_moyen_mensuel, entrants_par_an, taux_emploi, part_public, debut} ;
    entrants sur le marché du travail depuis `debut`. Budget : seulement la part des employeurs publics (versement au
    fonds, consolidé dans la variante moteur/fonds_apu.py) et l'IS perdu sur la charge déductible des employeurs
    privés. Emplois : canal d'offre commun sur la part employeur du privé (coût du travail) et la part salariale
    (prélèvement sur le travail). La part salariale baisse le revenu disponible des ménages : codée dans la micro
    (outils/openfisca_mesures.py, formule « capitalisation »), avec les mêmes paramètres."""
    from . import offre
    w = sq.salaires(p, s)
    e = sq.effectifs(p, s)
    par_tete = 12 * min(c["taux"] * c["brut_moyen_mensuel"], c["plafond_mensuel"]) / 1e9  # Md€ de 2026 par an
    couverts = {t: min(e[t]["emploi"], c["entrants_par_an"] * c["taux_emploi"] * max(0, t - c["debut"] + 1))
                for t in ANNEES}
    total = {t: couverts[t] * par_tete * w[t] / w[2029] for t in ANNEES}
    pe, pp = c["part_employeur"], c["part_public"]
    employeur_prive = Mesure("capitalisation (part employeur, privé)", "recettes",
                             {t: pe * (1 - pp) * total[t] for t in ANNEES}, instrument="cout_travail")
    salariale = Mesure("capitalisation (part salariale)", "recettes",
                       {t: (1 - pe) * total[t] for t in ANNEES}, instrument="travail")
    of = offre.effets(p, s, [employeur_prive, salariale], annees_avant=())
    emplois = {t: sum(serie.get(t, 0.0) for serie in of["emplois"].values()) for t in ANNEES}
    rc = p.val("entreprises.retour_is_charges")
    r_is = rc["taux_is_effectif"] * rc["part_marge"] * rc["part_employeurs_is"]
    pct = f"{100 * c['taux']:g}".replace(".", ",")
    out = [Mesure(f"{ident} — part de capitalisation : cotisation des employeurs publics ({pct} % du brut des entrants)",
                  "etat_missions", {2027: 0.0, 2028: 0.0, **{t: pe * pp * total[t] for t in ANNEES}}, fonds="versement"),
           # charge déductible des employeurs privés : IS en moins (règle commune, entreprises.retour_is_charges)
           Mesure(f"{ident} — impôt sur les sociétés : charges déductibles des entreprises", "recettes",
                  {t: -r_is * pe * (1 - pp) * total[t] for t in ANNEES})]
    return out, emplois


def effet_assurance_chomage(p: Parametres, s: str, decl: dict) -> float:
    """Variation du taux de chômage structurel (fraction ; négative = baisse) d'une réforme de l'assurance chômage,
    par le barème commun `assurance_chomage.*` (27/11/2026, demande d'Adrien : la baisse du chômage dépend du type de
    réforme et chaque type a sa source). Déclaration du programme (`<nom>_chomage.reforme`) :

    - duree : variation relative de la durée maximale d'indemnisation (−0,25 = un quart de moins), et part_duree :
      part des allocataires concernés (1 par défaut) ; effet linéaire, calé sur la réforme de 2023 ;
    - degressivite_md : économie de la dégressivité (Md€ de 2026), effet proportionnel, calé sur celle de 2021 ;
    - abroge : réformes annulées, parmi `reforme_2021` (salaire journalier de référence) et `reforme_2023` (durée) ;
    - affiliation, non_evalues : composantes sans effet durable chiffré (zéro, pour mémoire).

    Facteur de scénario : un effet qui baisse le chômage prend `facteurs.baisse`, un effet qui le monte
    `facteurs.hausse` (scénario miroir), comme le multiplicateur d'une relance."""
    b = {k: p.val(f"assurance_chomage.{k}") for k in ("duree", "degressivite", "reformes")}
    brut = 0.0
    if decl.get("duree"):
        d = b["duree"]
        brut += d["effet_reference"] * decl["duree"] / d["variation_reference"] * decl.get("part_duree", 1.0)
    if decl.get("degressivite_md"):
        g = b["degressivite"]
        brut += g["effet_reference"] * decl["degressivite_md"] / g["economie_reference_md"]
    for r in decl.get("abroge", ()):
        brut -= b["reformes"][r]  # annuler une réforme rend son effet
    f = p.val("assurance_chomage.facteurs")
    return brut * f["baisse" if brut < 0 else "hausse"][s]


def prelevements_pensions(p: Parametres, s: str, x: dict, serie: dict, note: str = "") -> list:
    """Règle commune (28/11/2026, contrôle micro/macro) : une mesure codée en montant sur les pensions (poste
    retraites) change aussi les prélèvements sur ces pensions (CSG, CRDS, Casa, cotisation maladie), au taux moyen du
    statu quo (recettes sur les pensions / pensions, 2029), comme les mesures de retraite calculées. Exception :
    `hors_prelevements` (minimum vieillesse, petites pensions exonérées ou au taux réduit). L'impôt sur le revenu des
    retraités n'est pas compté (même règle que les mesures calculées)."""
    if x.get("poste") != "retraites" or x.get("hors_prelevements"):
        return []
    taux = sq.recettes_par_impot(p, s)[2029]["retraites"] / sq.retraites(p, s)[2029]["depenses"]
    return [Mesure(f"{x['id']} — prélèvements sur les pensions", "recettes", {t: taux * v for t, v in serie.items()},
                   note=note)]
