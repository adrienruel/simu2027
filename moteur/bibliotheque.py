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
from .noyau import ANNEES
from .parametres import Parametres


# ---------------------------------------------------------------------------------------------------- retraites
def report_age_legal(p: Parametres, s: str, age_cible: float, premiere_generation: int,
                     pas_par_generation: float) -> dict[int, float]:
    """Pensions en moins (Md€ de 2026, > 0 = économie) quand l'âge légal passe de 64 ans à age_cible (voir
    report_age_legal_detail)."""
    return report_age_legal_detail(p, s, age_cible, premiere_generation, pas_par_generation)["pensions"]


def report_age_legal_detail(p: Parametres, s: str, age_cible: float, premiere_generation: int,
                            pas_par_generation: float) -> dict:
    """Pensions en moins (Md€ de 2026, > 0 = économie) et personnes pas encore retraitées en plus, quand l'âge légal
    passe de 64 ans à age_cible.

    Génération g : report = min(age_cible − 64, (g − premiere_generation + 1) × pas_par_generation) ; la part partie à
    chaque âge suit le profil commun décalé de ce report au-delà de 64 ans (ancien_systeme._part). Même calcul que
    statu_quo.retraites (survivants de l'Insee, pension liquidée sur le salaire de quinze ans plus tôt, érosion), même
    coefficient de calage. Les personnes pas encore retraitées sont réparties entre emploi, chômage et inactivité par
    offre.seniors."""
    from .ancien_systeme import _part, _part_age
    from .demographie import AGE_MAX
    r = _part_age(p)
    actuel = p.val("ancien_systeme.age_legal")["actuel"]
    ecart = age_cible - actuel
    pop = sq.population(p, s)
    w = sq.salaires(p, s)
    lag = int(p.val("statu_quo.retraites_decalage_carriere"))
    e = p.val("statu_quo.retraites_erosion_relative")
    nouveau = p.val("ancien_systeme.pension_nouveaux_relative")

    def niveau(depart: int) -> float:
        if depart < 2029:
            return 1.0
        return nouveau * w[depart - lag] / w[2029 - lag] * (1 - e) ** (depart - 2029)

    def report(g: int) -> float:
        return min(ecart, max(0.0, (g - premiere_generation + 1) * pas_par_generation))

    def brut(avec: bool) -> tuple[dict[int, float], dict[int, float]]:
        dep_t, ret_t = {}, {}
        for t in ANNEES:
            dep = ret = 0.0
            for a in range(50, AGE_MAX + 1):
                n, g = pop[t][a], t - a
                rep = report(g) if avec else 0.0
                ret += n * _part(r, a, rep, actuel)
                for b in range(50, a + 1):
                    d = _part(r, b, rep, actuel) - _part(r, b - 1, rep, actuel)
                    if d > 0:
                        dep += n * d * niveau(g + b)
            dep_t[t], ret_t[t] = dep, ret
        return dep_t, ret_t
    (b0, n0), (b1, n1) = brut(False), brut(True)
    k = sq.retraites(p, s)[2029]["depenses"] / b0[2029]
    return {"pensions": {t: k * (b0[t] - b1[t]) for t in ANNEES}, "non_retraites": {t: n0[t] - n1[t] for t in ANNEES}}


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
         valeur_emploi_chomeur: float, smic_brut_mensuel_2026: float = 1823.03,
         allegements_suivent_smic: bool = False) -> dict:
    """Relèvement du SMIC à brut_cible_2026 € brut par mois (euros de 2026), même mécanique que le programme Tondelier
    (table OpenFisca de 2026 lue au salaire relevé : les allègements restent au barème de 2026).

    Privé : prélèvements et TVA en plus, aides en moins, IS sur les marges prises (25 % de part_marge), emplois perdus
    pondérés (× élasticité dans le programme). Agents publics : hausse de coût (dépense), prélèvements et TVA en plus,
    aides en moins ; pas d'emploi perdu (l'employeur public paie). La hausse décroît linéairement jusqu'à zéro à
    diffusion_jusqu_a × le nouveau SMIC."""
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026
    from .systeme_actuel import _interp, _table_openfisca
    b_smic, b_new = smic_brut_mensuel_2026 * 12, brut_cible_2026 * 12
    plafond = diffusion_jusqu_a * b_new
    taux_tva = p.val("systeme_actuel.taux_tva_moyen")

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
                    out["is"] += -n * 0.25 * part_marge * dc
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
