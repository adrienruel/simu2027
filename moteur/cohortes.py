"""Cellules de ménages année par année : salariés par âge et par niveau de salaire, comptes d'épargne par génération.

Pourquoi : le budget statique est calculé une fois sur les salariés de 2026, puis suivait la croissance et le
nombre de personnes en emploi. Les cellules ajoutent ce que cette méthode ignore :
- la composition par âge des actifs (une population active plus âgée gagne plus, paie plus d'impôt, épargne
  plus, touche moins de RUI) ;
- les comptes d'épargne obligatoire, génération par génération et niveau de salaire par niveau de salaire,
  qui s'accumulent chaque année au rendement du fonds ; le socle de chaque cellule en découle à 67 ans (au lieu
  d'une moyenne sur cinq quintiles avec un taux d'emploi de carrière fixe) ;
- un flux d'épargne versé au fonds qui suit les salariés réellement en emploi.

Construction (euros de 2026, hors croissance : les montants suivent ensuite la croissance tendancielle comme le
reste du budget, le barème étant supposé suivre les salaires) :
- salariés de l'âge a l'année t = population de l'Insee × taux d'emploi par âge × part des salariés dans
  l'emploi (2026) ; répartis entre les 35 tranches de coût du privé et du public de 2026 ;
- coût employeur d'une cellule = coût de sa tranche × profil de salaire par âge (Insee, salaire moyen en EQTP
  du privé par tranche d'âge, 2024), normalisé pour que la masse de 2026 soit inchangée. Hypothèse : la
  dispersion des salaires est la même à tous les âges (elle grossit un peu la dispersion totale) ;
- impôt unique, impôt local, part de RUI gardée, consommation, TVA, épargne obligatoire et volontaire : mêmes
  fonctions que le budget statique (moteur/recettes/tva_menages.budget_actif).

Comptes et socle (générations de 22 à 49 ans en 2029, nées de 1980 à 2007) : une part de chaque génération fait
carrière (part = taux d'emploi moyen de 25 à 64 ans) et épargne chaque année d'emploi ; l'autre n'a pas de
capital et touche le socle plein. Capital à 67 ans = épargne obligatoire de chaque année au rendement du fonds,
plus le remboursement de 35 % ; socle de la tranche = socle plein × (1 − rente / rente annulant le socle).
"""
from __future__ import annotations

from .demographie import _tranche, population
from .epargne import epargne_annuelle, part_rui_salarie, revenu_par_euro_de_capital
from .parametres import Parametres

ANNEES = list(range(2029, 2074))
AGES_ACTIFS = range(18, 70)


def _profil(p: Parametres) -> dict[int, float]:
    pr = p.val("cohortes.profil_salaire_age")
    return {a: v for k, v in pr.items() for a in _tranche(k)}


def _taux_emploi(p: Parametres) -> dict[int, float]:
    return {a: v for k, v in p.val("demographie.taux_emploi_age").items() for a in _tranche(k)}


def _tranches(p: Parametres) -> list[dict]:
    """Tranches de coût de 2026 (privé et public aligné), avec leur part dans les salariés."""
    from .recettes.impot_salaires import effectifs_prive_2026, effectifs_public_2026, facteur_alignement_public
    from .recettes.tva_menages import part_rui_agent
    d, e, a = effectifs_prive_2026(p), effectifs_public_2026(p), facteur_alignement_public(p)
    out = [{"cout": c, "n": n, "public": False, "part_rui": None} for c, n in zip(d.milieux, d.effectifs)]
    out += [{"cout": c * a, "n": n, "public": True, "part_rui": part_rui_agent(c)} for c, n in zip(e.milieux, e.effectifs)]
    tot = sum(x["n"] for x in out)
    for x in out:
        x["part"] = x["n"] / tot
    return out


def _normalisation(p: Parametres, tr: list[dict]) -> float:
    """Facteur qui garde la masse salariale de 2026 quand on applique le profil par âge."""
    pop, te, pr = population(p, "prudent")[2026], _taux_emploi(p), _profil(p)
    emploi = {a: pop[a] * te.get(a, 0.0) for a in AGES_ACTIFS}
    return sum(emploi.values()) / sum(emploi[a] * pr.get(a, 1.0) for a in AGES_ACTIFS)


def _par_cellule(p: Parametres, scenario: str = "prudent") -> dict[float, dict[str, float]]:
    """Grandeurs annuelles par salarié, pour chaque multiplicateur de profil (5 tranches d'âge) et chaque tranche."""
    from .collectivites import taux_impot_local
    from .impot_unique import impot
    from .recettes.tva_menages import budget_actif
    tr = _tranches(p)
    k = _normalisation(p, tr)
    taux_local = taux_impot_local(p, salaries=True)
    rui = p.val("rui.montant") * 12
    out = {}
    for m in sorted(set(_profil(p).values())):
        agr = {"impot": 0.0, "local": 0.0, "rui": 0.0, "tva": 0.0, "epargne": 0.0, "masse": 0.0}
        par_tranche = []
        for x in tr:
            c = x["cout"] * m * k
            pr = x["part_rui"] if x["public"] else part_rui_salarie(c, p)
            b = budget_actif(c, p, scenario, pr)
            ep = epargne_annuelle(c, p, scenario, pr, contribution=False)
            vals = {"impot": impot(c, p, scenario), "local": max(0.0, c - p.val("impot_local.abattement")) * taux_local,
                    "rui": pr * rui, "tva": b["tva"], "epargne": ep, "masse": c}
            for key, v in vals.items():
                agr[key] += x["part"] * v
            par_tranche.append({"part": x["part"], "epargne": ep})
        out[m] = {**agr, "tranches": par_tranche}
    return out


def agregats(p: Parametres, jeu: str = "prudent", carrieres: bool = True) -> dict[int, dict[str, float]]:
    """Totaux annuels des salariés (euros de 2026, hors croissance) : impôt unique, impôt local, RUI gardé,
    TVA, épargne obligatoire, masse salariale, nombre de salariés. carrieres : avec les effets des réformes du
    supérieur (moteur/carrieres.py : entrée plus tôt dans l'emploi, gain de salaire des générations diplômées ;
    le gain est appliqué en proportion à l'impôt, ce qui sous-estime un peu l'effet de la progressivité)."""
    from .carrieres import emplois_entree_plus_tot, prime_salaire
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("cohortes_agregats", jeu, p.colonne_prudent, carrieres)
    if cle in cache:
        return cache[cle]
    cell = _par_cellule(p)
    pr, te = _profil(p), _taux_emploi(p)
    pops = population(p, jeu)
    part_sal = p.val("cohortes.part_salaries_emploi")
    if part_sal == "calcul":
        emploi_2026 = sum(population(p, "prudent")[2026][a] * te.get(a, 0.0) for a in AGES_ACTIFS)
        part_sal = sum(x["n"] for x in _tranches(p)) / emploi_2026
    out = {}
    for t in range(2026, 2074):
        tot = {"impot": 0.0, "local": 0.0, "rui": 0.0, "tva": 0.0, "epargne": 0.0, "masse": 0.0, "salaries": 0.0}
        plus = emplois_entree_plus_tot(p, jeu, t) if carrieres else {}
        for a in AGES_ACTIFS:
            n = (pops[t][a] * te.get(a, 0.0) + plus.get(a, 0.0)) * part_sal
            c = cell[pr.get(a, 1.0)]
            g = 1 + (prime_salaire(p, jeu, t, a) if carrieres else 0.0)
            tot["salaries"] += n
            for key in ("impot", "local", "rui", "tva", "epargne", "masse"):
                tot[key] += n * c[key] * (g if key != "rui" else 1.0)
        out[t] = tot
    cache[cle] = out
    return out


def indices(p: Parametres, jeu: str = "prudent") -> dict[int, dict[str, float]]:
    """Agrégats rapportés à 2029 (1 partout si le module est désactivé ou la population figée)."""
    cles = ("impot", "local", "rui", "tva", "epargne", "masse", "salaries")
    if not (p.val("cohortes.active") and p.val("demographie.active")):
        return {t: {k: 1.0 for k in cles} for t in range(2026, 2074)}
    ag = agregats(p, jeu)
    # base sans les effets des réformes du supérieur : référence de 2029 et effet de composition par âge (ces
    # effets ne sont pas de la composition par âge et ne doivent pas en être retirés)
    ag0 = agregats(p, jeu, carrieres=False)
    w = p.val("cohortes.effet_composition_salaires", jeu)
    out = {}
    for t in range(2026, 2074):
        brut = {k: ag[t][k] / ag0[2029][k] for k in cles}
        # salaire moyen relatif à 2029 (composition par âge) ; retiré en partie (double compte avec la tendance)
        comp = ((ag0[t]["masse"] / ag0[2029]["masse"]) / (ag0[t]["salaries"] / ag0[2029]["salaries"])) ** (1 - w)
        out[t] = {k: (v / comp if k not in ("salaries", "rui") else v) for k, v in brut.items()}
        # RUI gardé par les salariés : même logique (moins de jeunes à bas salaire) ; prudent : suit le nombre de salariés
        out[t]["rui"] = brut["salaries"] ** (1 - w) * brut["rui"] ** w
    return out


def socle_par_cellule(p: Parametres) -> list[dict]:
    """Socle annuel moyen par personne de chaque génération du nouveau système (22 à 49 ans en 2029), en euros
    de 2026 : moyenne entre ceux qui font carrière (capital accumulé) et ceux qui n'en ont pas (socle plein)."""
    from .retraites_transition import _csv
    cell = _par_cellule(p)
    pr, te = _profil(p), _taux_emploi(p)
    r = p.val("epargne.rendement_fonds")
    rev = revenu_par_euro_de_capital(p)
    socle, seuil = p.val("retraites.socle_plein") * 12, p.val("retraites.rente_annulant_socle") * 12
    acces = int(p.val("epargne.age_acces_socle"))
    ratio = p.val("transition.taux_remboursement") / p.val("transition.taux_implicite_fichier_source")
    q = sum(te.get(a, 0.0) for a in range(25, 65)) / 40  # part qui fait carrière
    out = []
    for g in _csv("cohortes_2029.csv"):
        age0 = int(g["age_2029"])
        depart = 2029 + acces - age0
        # épargne de chaque année, par tranche, pour un salarié de carrière (probabilité d'emploi / q)
        capitaux = [0.0] * len(next(iter(cell.values()))["tranches"])
        for y in range(2029, depart):
            a = age0 + y - 2029
            if a < 18 or a >= acces:
                continue
            tranches = cell[pr.get(a, 1.0)]["tranches"]
            w = min(1.0, te.get(a, 0.0) / q)
            for i, x in enumerate(tranches):
                capitaux[i] += w * x["epargne"] * (1 + r) ** (depart - 1 - y)
        remb = g["remboursement_par_actif"] * ratio  # par actif de carrière
        tranches = cell[1.0]["tranches"] if 1.0 in cell else next(iter(cell.values()))["tranches"]
        socle_carriere = sum(x["part"] * socle * max(0.0, 1 - (k + remb) * rev / seuil) for x, k in zip(tranches, capitaux))
        moyen = q * socle_carriere + (1 - q) * socle
        # profils de retraite (annuels) : chaque tranche de ceux qui ont fait carrière, et ceux sans capital
        profils = [{"poids": q * x["part"], "rente": (k + remb) * rev, "socle": socle * max(0.0, 1 - (k + remb) * rev / seuil)}
                   for x, k in zip(tranches, capitaux)]
        profils.append({"poids": 1 - q, "rente": 0.0, "socle": socle})
        out.append({**g, "socle_moyen": moyen, "socle_carriere": socle_carriere, "part_carriere": q, "profils": profils})
    return out


def comptes(p: Parametres, jeu: str = "prudent") -> dict[int, dict[str, float]]:
    """Comptes d'épargne obligatoire de tous les ménages, génération par génération (euros de 2026, hors
    croissance, comme le flux du fonds dans le module macro).

    Avant 67 ans : chaque génération verse l'épargne obligatoire de ses salariés (cellules), capitalisée au
    rendement du fonds. À 67 ans : la moitié du capital part en rente viagère (prix de la rente : mortalité de
    Gompertz), l'autre moitié reste placée et verse ses rendements (epargne.part_rente_viagere) ; au décès, elle
    passe aux héritiers et reste placée. Sorties du fonds chaque année : rentes viagères + rendements de la
    moitié placée. Les points pris par la règle et l'épargne rendue sont comptés à part, dans le module macro.

    Renvoie par année : encours (début d'année), versements, rendements, paiements aux retraités."""
    from .carrieres import emplois_entree_plus_tot, prime_salaire
    from .epargne import capital_par_euro_de_rente
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("comptes", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    cell = _par_cellule(p)
    pr, te = _profil(p), _taux_emploi(p)
    pops = population(p, jeu)
    r = p.val("epargne.rendement_fonds")
    part_rente = p.val("epargne.part_rente_viagere")
    af = capital_par_euro_de_rente(p)
    acces = int(p.val("epargne.age_acces_socle"))
    emploi_2026 = sum(population(p, "prudent")[2026][a] * te.get(a, 0.0) for a in AGES_ACTIFS)
    part_sal = sum(x["n"] for x in _tranches(p)) / emploi_2026
    s_age = {a: te.get(a, 0.0) * part_sal * cell[pr.get(a, 1.0)]["epargne"] for a in AGES_ACTIFS}
    actif, pool, place, rente = {}, {}, {}, {}  # par année de naissance
    out = {}
    for t in range(2029, 2074):
        encours = sum(actif.values()) + sum(pool.values()) + sum(place.values())
        versements = paiements = 0.0
        # versements des actifs (18 à 66 ans)
        plus = emplois_entree_plus_tot(p, jeu, t)
        for a in AGES_ACTIFS:
            if a >= acces:
                continue
            c = t - a
            # salariés de l'âge (avec l'entrée plus tôt) × épargne par salarié (avec le gain de salaire)
            v = (pops[t][a] + (plus.get(a, 0.0) / te[a] if te.get(a) else 0.0)) * s_age.get(a, 0.0) * (1 + prime_salaire(p, jeu, t, a))
            actif[c] = actif.get(c, 0.0) * (1 + r) + v if c in actif else v
            versements += v
        # générations qui atteignent 67 ans : la moitié en rente, l'autre placée
        c67 = t - acces
        if c67 in actif:
            k = actif.pop(c67) * (1 + r)
            pool[c67] = part_rente * k
            place[c67] = (1 - part_rente) * k
            n67 = pops[t][acces] if acces <= 105 else 0.0
            rente[c67] = pool[c67] / (n67 * af) if n67 > 0 else 0.0
        # retraités : rente viagère aux survivants, rendements de la part placée versés
        for c in list(pool):
            age = t - c
            n = pops[t][min(age, 105)] if age <= 105 else 0.0
            versee = n * rente[c]
            paiements += versee + r * place[c]
            pool[c] = max(0.0, pool[c] * (1 + r) - versee)
        out[t] = {"encours": encours, "versements": versements, "rendements": r * encours, "paiements": paiements}
    cache[cle] = out
    return out


def fiscalite_retraites_nouveaux(p: Parametres) -> dict[int, dict[str, float]]:
    """Impôt et TVA des retraités du nouveau système (générations de 22 à 49 ans en 2029, à partir de 67 ans),
    calculés sur la rente et le socle de chaque profil (euros de 2026, hors croissance). Mêmes règles que le
    budget de croisière (moteur/recettes/retraites_croisiere.py) : socle exonéré ou au barème, rente imposée à
    la flat tax sur sa part imposable ; TVA sur la consommation du revenu net."""
    from .impot_unique import impot
    from .recettes.tva_menages import consommation_ht
    from .retraites_transition import survivants
    from .tva import taux_pour_revenu
    cache = p.__dict__.setdefault("_cache", {})
    if "fiscalite_retraites_nouveaux" in cache:
        return cache["fiscalite_retraites_nouveaux"]
    flat, part_imp = p.val("capital.flat_tax_dividendes"), p.val("retraites.part_imposable_rente")
    exonere = p.val("retraites.socle_exonere")
    acces = int(p.val("epargne.age_acces_socle"))
    gens = socle_par_cellule(p)
    par_gen = []
    for g in gens:
        imp = tva = 0.0
        for x in g["profils"]:
            i = (0.0 if exonere else impot(x["socle"], p)) + x["rente"] * part_imp * flat
            net = x["rente"] + x["socle"] - i
            sante, t = taux_pour_revenu(net, p)
            imp += x["poids"] * i
            tva += x["poids"] * (sante + t) * consommation_ht(max(0.0, net), sante + t, p)
        par_gen.append((g, imp, tva))
    out = {}
    for an in ANNEES:
        imp = tva = n = 0.0
        for g, i, v in par_gen:
            if g["age_2029"] + an - 2029 >= acces:
                k = survivants(p, g, an)
                imp, tva, n = imp + k * i, tva + k * v, n + k
        out[an] = {"impot": imp, "tva": tva, "effectif": n}
    cache["fiscalite_retraites_nouveaux"] = out
    return out


def menages(p: Parametres, jeu: str = "prudent") -> dict[int, dict[str, float]]:
    """Couples d'âge actif (20 à 66 ans) chaque année : nombre, part des couples à un seul revenu, personnes sans
    emploi en couple. Forme par âge de l'Insee ; emploi des conjoints indépendant (prudent : plus de couples à un
    revenu, donc un quotient conjugal plus coûteux) ; niveaux calés en 2026 sur les paramètres du quotient."""
    cache = p.__dict__.setdefault("_cache", {})
    cle = ("menages", jeu, p.colonne_prudent)
    if cle in cache:
        return cache[cle]
    couple = {a: v for k, v in p.val("cohortes.part_en_couple_age").items() for a in _tranche(k)}
    te = _taux_emploi(p)
    pops = population(p, jeu)
    brut = {}
    for t in range(2026, 2074):
        n = un = deux = sans = 0.0
        for a in range(18, 67):
            c = pops[t][a] * couple.get(a, 0.0) / 2  # couples (une personne sur deux compte le couple)
            e = te.get(a, 0.0)
            n += c
            un += c * 2 * e * (1 - e)
            deux += c * e * e
            sans += 2 * c * (1 - e)
        brut[t] = {"couples": n, "un": un, "deux": deux, "sans_emploi": sans}
    q = p.val("quotient.conjugal")
    k_n = q["couples"] / brut[2026]["couples"]
    part0 = brut[2026]["un"] / (brut[2026]["un"] + brut[2026]["deux"])
    k_u = q["part_un_revenu"] / part0
    out = {}
    for t, b in brut.items():
        part = min(1.0, k_u * b["un"] / (b["un"] + b["deux"]))
        out[t] = {"couples": b["couples"] * k_n, "part_un_revenu": part,
                  "couples_avec_revenu": b["couples"] * k_n * (b["un"] + b["deux"]) / b["couples"],
                  "sans_emploi_en_couple": b["sans_emploi"] / brut[2026]["sans_emploi"]}
    cache[cle] = out
    return out
