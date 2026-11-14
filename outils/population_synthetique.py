"""Population synthétique de ménages pour la microsimulation (phase F1 de la roadmap).

DÉCISION d'Adrien du 14/11/2026 : faute d'accès à une enquête (ERFS, EFL), les ménages sont tirés et calés sur
des tableaux publics. Étapes :

1. tirage des ménages (type, âges, enfants) selon microsimulation.structure_menages et formes_tirage ;
2. statut de chaque adulte (emploi par âge, chômage par âge, retraite par âge, études) ;
3. revenus tirés dans les distributions déjà utilisées par le moteur (classes de salaires du privé et du public,
   indépendants, déciles de pensions de la Drees), rangés selon un score latent qui suit l'âge et corrèle les
   conjoints (copule gaussienne) ;
4. logement (statut, loyer, zone), capital (dividendes, loyers perçus) ;
5. calage des poids (raking) sur les marges : population par âge, types de ménages, effectifs par statut,
   classes de salaires du privé, statuts d'occupation.

Écrit parametres/donnees/population_synthetique_2026.csv (une ligne par personne). Graine fixe.

    python -m outils.population_synthetique
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "parametres" / "donnees"
SORTIE = DONNEES / "population_synthetique_2026.csv"
GRAINE = 2027
ECARTS_CALAGE: list = []  # écart relatif de chaque marge après calage


def _lire(nom):
    with (DONNEES / nom).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _bande(age: int, bornes: dict) -> str:
    """Clé d'un dictionnaire « a-b », « a+ », « <a » ou « a » contenant l'âge."""
    for k in bornes:
        if k.startswith("<") and age < int(k[1:]):
            return k
        if k.endswith("+") and age >= int(k[:-1]):
            return k
        if "-" in k:
            a, b = k.split("-")
            if int(a) <= age <= int(b):
                return k
        elif k.isdigit() and age == int(k):
            return k
    raise KeyError(age)


def _interp_table(x, table, cle_x, cle_y):
    xs = np.array([float(l[cle_x]) for l in table])
    ys = np.array([float(l[cle_y]) for l in table])
    o = np.argsort(xs)
    xs, ys = xs[o], ys[o]
    x = np.asarray(x, float)
    y = np.interp(x, xs, ys)
    haut = x > xs[-1]
    y[haut] = ys[-1] * x[haut] / xs[-1]
    return np.where(x > 0, y, 0.0)


def _tirer_classes(rng, n, milieux, effectifs):
    """Tire n montants dans des classes (milieu, effectif), log-uniformes entre les bornes géométriques."""
    m = np.asarray(milieux, float)
    w = np.asarray(effectifs, float)
    w = w / w.sum()
    bas = np.concatenate([[m[0] * 0.15], np.sqrt(m[:-1] * m[1:])])
    haut = np.concatenate([np.sqrt(m[:-1] * m[1:]), [m[-1] * 1.5]])
    k = rng.choice(len(m), size=n, p=w)
    u = rng.random(n)
    return np.exp(np.log(bas[k]) + u * (np.log(haut[k]) - np.log(bas[k])))


def _ranger(valeurs, score):
    """Affecte les valeurs (triées) aux personnes dans l'ordre de leur score."""
    out = np.empty(len(score))
    out[np.argsort(score)] = np.sort(valeurs)
    return out


def generer(p: Parametres | None = None, n_menages: int | None = None, graine: int = GRAINE,
            caler_beneficiaires: bool | None = None) -> list[dict]:
    p = p or Parametres()
    v = lambda c: p.val("microsimulation." + c)  # noqa: E731
    rng = np.random.default_rng(graine)
    n = n_menages or int(v("taille_echantillon"))
    formes = v("formes_tirage")

    pop = {int(l["age"]): float(l["population"]) for l in _lire("population_insee_2026_central.csv") if l["annee"] == "2026"}
    sortie = v("sortie_menages_ordinaires")
    def hors(a):
        return sortie["85+"] if a >= 85 else sortie["75-84"] if a >= 75 else sortie["autres"]
    pop_men = {a: x * (1 - hors(a)) for a, x in pop.items()}
    ages = np.array(sorted(pop_men))
    poids_age = np.array([pop_men[a] for a in ages])

    lois = {}

    def tirer_age(lo, hi, forme=None, cle=None):
        if cle not in lois or cle is None:
            m = (ages >= lo) & (ages <= hi)
            w = poids_age * m
            if forme is not None:
                w = w * np.array([forme(a) if lo <= a <= hi else 0.0 for a in ages])
            lois[cle] = w / w.sum()
        return rng.choice(ages, p=lois[cle])

    struct = v("structure_menages")
    types = ["seul", "couple_sans_enfant", "couple_avec_enfants", "monoparentale", "complexe"]
    pt = np.array([struct[t] for t in types])
    t_men = rng.choice(len(types), size=n, p=pt / pt.sum())
    enf = v("enfants_par_famille")
    n_enf_choix = np.array([int(k) for k in enf])
    n_enf_p = np.array(list(enf.values()))
    ecart_c = formes["ecart_age_conjoints"]
    mere_lo, mere_hi = formes["ecart_age_mere_enfant"]
    ap = formes["age_parent"]
    seul_age = formes["seul_par_age"]

    personnes = []  # dictionnaires, un par personne
    for i in range(n):
        t = types[t_men[i]]
        adultes, enfants = [], []
        if t == "seul":
            adultes = [int(tirer_age(18, 105, lambda a: seul_age[_bande(a, seul_age)], "seul"))]
        elif t in ("couple_sans_enfant", "complexe"):
            a = int(tirer_age(20, 100, lambda a: 0.5 if 30 <= a <= 54 else 1.0, "couple"))
            adultes = [a, max(18, a + int(round(rng.normal(ecart_c["moyenne"], ecart_c["ecart"]))))]
            if t == "complexe":
                adultes.append(int(tirer_age(18, 30, cle="jeune")) if rng.random() < 0.6 else int(tirer_age(75, 100, cle="vieux")))
        else:
            a = int(tirer_age(20, 65, lambda a: math.exp(-0.5 * ((a - ap["moyenne"]) / ap["ecart"]) ** 2), "parent"))
            adultes = [a] if t == "monoparentale" else [a, max(18, a + int(round(rng.normal(ecart_c["moyenne"], ecart_c["ecart"]))))]
            k = int(rng.choice(n_enf_choix, p=n_enf_p / n_enf_p.sum()))
            for _ in range(k):
                for _essai in range(20):
                    e = a - int(rng.integers(mere_lo, mere_hi + 1))
                    if 0 <= e <= 24:
                        break
                else:
                    e = int(rng.integers(0, 18))
                enfants.append(e)
        for r, age in enumerate(adultes):
            role = "ref" if r == 0 else ("conjoint" if r == 1 and t != "seul" else "autre")
            personnes.append({"menage": i, "type": t, "role": role, "age": age})
        for e in enfants:
            personnes.append({"menage": i, "type": t, "role": "enfant", "age": e})

    N = len(personnes)
    age = np.array([q["age"] for q in personnes])
    role = np.array([q["role"] for q in personnes])
    men = np.array([q["menage"] for q in personnes])
    adulte = (role != "enfant") | (age >= 18)

    # --- Statuts ---------------------------------------------------------------------------------------------
    te = p.val("demographie.taux_emploi_age")
    tc = p.val("chomage.taux_par_age")
    dep = v("depart_par_age")
    def taux(a, d):
        try:
            return d[_bande(a, d)]
        except KeyError:
            return 0.0
    def cle_te(a):
        return 0.0 if a < 15 else taux(a, te)
    def cle_tc(a):
        return tc["15-24"] if a < 25 else tc["25-49"] if a < 50 else tc["50+"]
    u = rng.random(N)
    conf = v("emploi_par_configuration")
    typ_p = np.array([q["type"] for q in personnes])
    coef = np.where(typ_p == "monoparentale", conf["monoparentale"], np.where(typ_p == "couple_avec_enfants", conf["couple_avec_enfants"], conf["sans_enfant"]))
    coef = np.where(typ_p == "seul", conf["seul"], coef)
    coef = np.where((role != "enfant") & (age < 65), coef, 1.0)
    sans_conjoint = np.isin(typ_p, ["seul", "monoparentale"]) | (role == "autre")
    coef_ch = np.where(role == "enfant", 1.0, np.where(sans_conjoint, conf["chomage_sans_conjoint"], conf["chomage_en_couple"]))
    p_emploi = np.minimum(0.98, np.array([cle_te(a) for a in age]) * coef)
    p_chom = np.array([cle_te(a) * cle_tc(a) / (1 - cle_tc(a)) if a < 67 else 0.0 for a in age]) * coef_ch
    p_ret = np.array([taux(a, dep) if a >= 55 else 0.0 for a in age])
    enfant_jeune = (role == "enfant") & (age < 16)
    statut = np.full(N, "inactif", dtype=object)
    emploi = (u < p_emploi) & ~enfant_jeune
    chom = ~emploi & (u < p_emploi + p_chom) & ~enfant_jeune
    statut[emploi] = "emploi"
    statut[chom] = "chomeur"
    reste = ~emploi & ~chom
    ret = reste & (rng.random(N) < p_ret)
    statut[ret] = "retraite"
    statut[reste & ~ret & (age >= 16) & (age <= 25)] = "etudiant"
    statut[enfant_jeune] = "enfant"

    emp = v("emploi_2026")
    tot = sum(emp.values())
    idx_emp = np.where(statut == "emploi")[0]
    choix = rng.choice(3, size=len(idx_emp), p=[emp["salaries_prives"] / tot, emp["agents_publics"] / tot, emp["independants"] / tot])
    for k, nom in enumerate(("salarie_prive", "agent_public", "independant")):
        statut[idx_emp[choix == k]] = nom
    statut[(statut == "agent_public") & (age >= 63)] = "salarie_prive"  # rares au-delà de la limite d'âge

    # Étudiants décohabitants : ménage d'une personne, rattaché au foyer fiscal des parents, même poids.
    deco = (role == "enfant") & (statut == "etudiant") & (age >= 18) & (age <= 24) & (rng.random(N) < v("etudiants_decohabitants"))
    menage_final = men.copy()
    menage_final[deco] = n + np.arange(deco.sum())
    n_deco = np.bincount(men[deco], minlength=n).astype(float)

    # --- Score latent : âge et corrélation des conjoints -----------------------------------------------------
    corr = v("correlation_conjoints")
    g_men = rng.normal(size=n)
    g_pen = rng.normal(size=n)
    rho_s = math.sqrt(corr["salaires"])
    rho_p = math.sqrt(corr["pensions"])
    prof = p.val("cohortes.profil_salaire_age")
    def profil(a):
        return prof["18-24"] if a < 25 else prof["25-39"] if a < 40 else prof["40-49"] if a < 50 else prof["50-54"] if a < 55 else prof["55+"]
    en_couple = np.isin(role, ["ref", "conjoint"]) & np.isin(typ_p, ["couple_sans_enfant", "couple_avec_enfants", "complexe"])
    eps = rng.normal(size=N)
    z = np.where(en_couple, rho_s * g_men[men] + math.sqrt(1 - rho_s ** 2) * eps, eps)
    score = z + np.log([profil(a) for a in age]) / 0.8
    zp = np.where(en_couple, rho_p * g_pen[men] + math.sqrt(1 - rho_p ** 2) * eps, eps)

    # --- Revenus ---------------------------------------------------------------------------------------------
    salaire_brut = np.zeros(N); cout = np.zeros(N); rev_ind = np.zeros(N)
    chomage_brut = np.zeros(N); pension = np.zeros(N)
    groupe_ind = np.full(N, "", dtype=object)
    prive = _lire("salaries_prive.csv")
    table_prive = _lire("openfisca_prive_2026.csv")
    i_pr = np.where(statut == "salarie_prive")[0]
    c = _tirer_classes(rng, len(i_pr), [float(l["cout_employeur_milieu"]) for l in prive], [float(l["effectif_origine"]) for l in prive])
    cout[i_pr] = _ranger(c, score[i_pr])
    salaire_brut[i_pr] = _interp_table(cout[i_pr], table_prive, "cout_du_travail", "brut")
    # Mois travaillés : un bas salaire annuel est en partie un travail sur quelques mois (microsimulation.mois_travailles).
    mt = v("mois_travailles")
    smic = smic_mensuel_brut()
    mois = np.full(N, 12, int)
    debut = np.zeros(N, int)
    taux_m = np.maximum(salaire_brut[i_pr] / 12, rng.uniform(mt["taux_mensuel_min"], mt["taux_mensuel_max"], len(i_pr)) * smic)
    mois[i_pr] = np.clip(np.ceil(salaire_brut[i_pr] / taux_m), 1, 12).astype(int)
    debut[i_pr] = rng.integers(0, 13 - mois[i_pr])
    pub = [l for l in _lire("fonctionnaires.csv") if float(l["effectif_origine"]) > 0]
    table_pub = _lire("openfisca_public_etat_civils_2026.csv")
    i_pu = np.where(statut == "agent_public")[0]
    c = _tirer_classes(rng, len(i_pu), [float(l["cout_employeur_milieu"]) for l in pub], [float(l["effectif_origine"]) for l in pub])
    cout[i_pu] = _ranger(c, score[i_pu])
    salaire_brut[i_pu] = _interp_table(cout[i_pu], table_pub, "cout_du_travail", "brut")

    indep = _lire("independants.csv")
    eff = {"classiques": p.val("independants.classiques"), "agriculteurs": p.val("independants.agriculteurs")}
    eff["micro"] = max(0.0, emp["independants"] * 1e6 - eff["classiques"] - eff["agriculteurs"])
    i_in = np.where(statut == "independant")[0]
    gs = list(eff)
    gi = rng.choice(len(gs), size=len(i_in), p=np.array([eff[g] for g in gs]) / sum(eff.values()))
    passage = p.val("independants.passage_2023_2026")
    for k, g in enumerate(gs):
        ii = i_in[gi == k]
        lignes = [l for l in indep if l["groupe"] == g]
        montants = np.array([float(l["revenu_annuel"]) * (passage if l["annee_euros"] == "2023" else 1.0) for l in lignes])
        parts = np.array([float(l["part_effectif"]) for l in lignes])
        tir = montants[rng.choice(len(lignes), size=len(ii), p=parts / parts.sum())] * np.exp(rng.normal(0, 0.15, len(ii)))
        rev_ind[ii] = _ranger(tir, score[ii])
        groupe_ind[ii] = g

    ci = v("chomeurs_indemnises")
    i_ch = np.where(statut == "chomeur")[0]
    perdu = _interp_table(_ranger(_tirer_classes(rng, len(i_ch), [float(l["cout_employeur_milieu"]) for l in prive],
                                                 [float(l["effectif_origine"]) for l in prive]), score[i_ch]),
                          table_prive, "cout_du_travail", "brut")
    alloc = 0.57 * np.minimum(perdu, 4 * 47100)
    indem = rng.random(len(i_ch)) < ci["part"]
    alloc = np.where(indem, alloc, 0.0)
    if indem.any():
        alloc *= ci["allocation_brute_mensuelle"] * 12 / alloc[indem].mean()
    chomage_brut[i_ch] = alloc

    dec = np.array(p.val("anciennes_pensions.deciles_drees_2020"), float)
    i_re = np.where(statut == "retraite")[0]
    q = rng.random(len(i_re)) * 10
    k = np.minimum(q.astype(int), 9)
    bas = np.concatenate([[dec[0] * 0.3], dec[:-1]])[k]
    pen = bas + (q - k) * (dec[k] - bas)
    pen[k == 9] = dec[8] + rng.pareto(2.5, (k == 9).sum()) * (dec[9] - dec[8])
    pen *= v("pension_brute_moyenne") / pen.mean()
    pension[i_re] = _ranger(pen * 12, zp[i_re] + 0.02 * (age[i_re] < 75))

    # Handicap (AAH) : parmi les inactifs et chômeurs de 20 à 64 ans, de préférence non indemnisés.
    hand = v("handicap")
    handicap = np.zeros(N, bool)

    # --- Revenu du ménage (pour le logement et le capital) ---------------------------------------------------
    rev_pers = salaire_brut + rev_ind + chomage_brut + pension
    rev_men = np.bincount(men, weights=rev_pers, minlength=n)

    # Logement
    so = v("statut_occupation")
    prop_age = formes["proprietaire_par_age"]
    soc = formes["social_parmi_locataires"]
    ref_age = np.zeros(n, int); ref_age[men[role == "ref"]] = age[role == "ref"]
    taille = np.bincount(men[~deco], minlength=n)
    rang_rev = np.argsort(np.argsort(rev_men / np.sqrt(taille))) / n
    p_prop = np.array([prop_age[_bande(a, prop_age)] for a in ref_age]) * (0.6 + 0.8 * rang_rev)
    tir = rng.random(n)
    logement = np.where(tir < np.clip(p_prop, 0, 0.97), "proprietaire", "locataire").astype(object)
    gratuit = (logement == "locataire") & (rng.random(n) < so["loge_gratuitement"] / (so["locataire_prive"] + so["locataire_social"] + so["loge_gratuitement"]))
    logement[gratuit] = "loge_gratuitement"
    types_m = np.array(types)[t_men]
    p_soc = np.where(rang_rev < 1 / 3, soc["bas"], np.where(rang_rev < 2 / 3, soc["milieu"], soc["haut"])) + soc["monoparentale"] * (types_m == "monoparentale")
    loc = logement == "locataire"
    logement[loc] = np.where(rng.random(loc.sum()) < p_soc[loc], "locataire_social", "locataire_prive")
    lm2 = v("loyer_m2")
    surface = np.minimum(45 + 15 * (taille - 1), 100)
    loyer = np.where(logement == "locataire_social", lm2["social"], np.where(logement == "locataire_prive", lm2["prive"], 0.0)) * surface
    loyer *= np.exp(rng.normal(0, 0.2, n))
    zn = v("zones_apl")
    zone = rng.choice(["zone_1", "zone_2", "zone_3"], size=n, p=[zn["zone_1"], zn["zone_2"], zn["zone_3"]])
    nd = int(deco.sum())
    loyer_et = lm2["prive"] * 20 * np.exp(rng.normal(0, 0.2, nd))
    zone_et = rng.choice(["zone_1", "zone_2"], size=nd, p=[1 / 3, 2 / 3])

    # --- Calage des poids ------------------------------------------------------------------------------------
    marges, matrice = [], []
    def ajouter(cible, indic_menage):
        marges.append(cible)
        matrice.append(indic_menage)
    bandes = [(0, 2), (3, 5), (6, 10), (11, 14), (15, 17), (18, 19), (20, 24)] + [(a, a + 4) for a in range(25, 85, 5)] + [(85, 110)]
    for lo, hi in bandes:
        cible = sum(x for a, x in pop_men.items() if lo <= a <= hi)
        ajouter(cible, np.bincount(men, weights=((age >= lo) & (age <= hi)).astype(float), minlength=n))
    nm = v("menages_2026") * 1e6
    regroup = {"seul": ["seul"], "couple_sans_enfant": ["couple_sans_enfant", "complexe"], "couple_avec_enfants": ["couple_avec_enfants"], "monoparentale": ["monoparentale"]}
    for t, ts in regroup.items():
        ajouter(nm * sum(struct[x] for x in ts), np.isin(types_m, ts).astype(float) + (n_deco if t == "seul" else 0.0))
    fm = v("familles_enfants_mineurs")
    mineurs = np.bincount(men, weights=((role == "enfant") & (age < 18)).astype(float), minlength=n)
    for k in ("1", "2", "3", "4"):
        ind = (mineurs >= 4) if k == "4" else (mineurs == int(k))
        ajouter(fm["total"] * fm[k] * 1e6, ind.astype(float))
    enf20 = np.bincount(men, weights=((role == "enfant") & ~deco & (age < 20)).astype(float), minlength=n)
    ajouter(v("familles_allocations_familiales") * 1e6, (enf20 >= 2).astype(float))
    def compte(masque):
        return np.bincount(men, weights=masque.astype(float), minlength=n)
    ajouter(emp["agents_publics"] * 1e6, compte(statut == "agent_public"))
    ajouter(emp["independants"] * 1e6, compte(statut == "independant"))
    ajouter(p.val("inactifs.chomeurs_bit"), compte(statut == "chomeur"))
    ajouter(v("retraites_residents_2026") * 1e6, compte(statut == "retraite"))
    bornes_cout = [0, 10e3, 20e3, 30e3, 40e3, 60e3, 100e3, 200e3, 1e12]
    milieux = np.array([float(l["cout_employeur_milieu"]) for l in prive])
    effp = np.array([float(l["effectif_origine"]) for l in prive])
    for lo, hi in zip(bornes_cout[:-1], bornes_cout[1:]):
        ajouter(effp[(milieux >= lo) & (milieux < hi)].sum(), compte((statut == "salarie_prive") & (cout >= lo) & (cout < hi)))
    for s, cle in (("proprietaire", "proprietaire"), ("locataire_prive", "locataire_prive"), ("locataire_social", "locataire_social"), ("loge_gratuitement", "loge_gratuitement")):
        ajouter(nm * so[cle], (logement == s).astype(float) + (n_deco if s == "locataire_prive" else 0.0))
    A = np.array(matrice)  # contraintes × ménages
    cibles = np.array(marges)
    w0 = np.full(n, nm / n)
    w = _raking(A, cibles, w0)
    ECARTS_CALAGE[:] = list((A @ w) / cibles - 1)

    # Handicap tiré après calage (les poids donnent le nombre d'adultes).
    c1 = np.where((statut == "inactif") & (age >= 20) & (age <= 64))[0]
    c2 = np.where((statut == "chomeur") & (chomage_brut == 0) & (age >= 20) & (age <= 64))[0]
    c3 = np.where((statut == "salarie_prive") & (cout < 25e3) & (age >= 20) & (age <= 64))[0]
    rng.shuffle(c1); rng.shuffle(c2); rng.shuffle(c3)
    part_emploi = v("aah_en_emploi")
    cum3 = np.cumsum(w[men[c3]])
    handicap[c3[cum3 <= part_emploi * hand["adultes"] * 1e6]] = True
    cand = np.concatenate([c1, c2])
    cum = np.cumsum(w[men[cand]])
    handicap[cand[cum <= (1 - part_emploi) * hand["adultes"] * 1e6]] = True
    statut[handicap & (statut == "chomeur")] = "inactif"
    chomage_brut[handicap] = 0.0

    # Capital : dividendes et loyers perçus selon le rang du revenu du ménage (Pareto), propriétaires surtout.
    cap = v("capital_menages")
    F = (np.argsort(np.argsort(rev_men)) + 0.5) / n
    alpha = cap["concentration"]
    base = np.where(F > 0.4, (1 - F) ** (-1 / alpha) - (0.6) ** (-1 / alpha), 0.0)
    div = base * rng.lognormal(0, 0.5, n)
    fon = base * (logement == "proprietaire") * rng.lognormal(0, 0.5, n)
    div *= cap["dividendes"] * 1e9 / (w * div).sum()
    fon *= cap["revenus_fonciers"] * 1e9 / (w * fon).sum()

    # --- Écriture --------------------------------------------------------------------------------------------
    maries = rng.random(n) < v("couples_maries")
    lignes = []
    k_et = {j: k for k, j in enumerate(np.where(deco)[0])}
    for j, q in enumerate(personnes):
        i = q["menage"]
        et = j in k_et
        lignes.append({
            "menage": int(menage_final[j]), "unite": i, "rattache": int(et), "poids": round(float(w[i]), 3),
            "type": "seul" if et else q["type"], "role": "ref" if et else q["role"], "age": int(age[j]),
            "statut": statut[j], "groupe_independant": groupe_ind[j], "salaire_brut": round(float(salaire_brut[j]), 2),
            "cout_employeur": round(float(cout[j]), 2), "revenu_independant": round(float(rev_ind[j]), 2),
            "mois_travailles": int(mois[j]), "debut_mois": int(debut[j]), "chomage_brut": round(float(chomage_brut[j]), 2), "pension_brute": round(float(pension[j]), 2),
            "handicap": int(handicap[j]), "maries": int(maries[i]),
            "dividendes": round(float(div[i]), 2) if q["role"] == "ref" else 0.0,
            "revenus_fonciers": round(float(fon[i]), 2) if q["role"] == "ref" else 0.0,
            "logement": "locataire_prive" if et else logement[i],
            "loyer_mensuel": round(float(loyer_et[k_et[j]] if et else loyer[i]), 2), "zone": zone_et[k_et[j]] if et else zone[i],
        })
    # --- Second calage : effectifs de bénéficiaires publiés (OpenFisca dans la boucle) ------------------------
    if caler_beneficiaires is None:
        caler_beneficiaires = bool(v("calage_beneficiaires"))
    if caler_beneficiaires:
        from outils import openfisca_population as op
        ind = op.indicateurs(lignes)
        ben = v("beneficiaires")
        hand_u = np.bincount(men, weights=handicap.astype(float), minlength=n)  # garde l'effectif tiré
        A2 = np.vstack([A] + [ind[k][None, :] for k in ben] + [hand_u[None, :]])
        c2 = np.concatenate([cibles, [ben[k] * 1e6 for k in ben], [hand["adultes"] * 1e6]])
        w = _raking(A2, c2, w0)
        ECARTS_CALAGE[:] = list((A2 @ w) / c2 - 1)
        k_div = cap["dividendes"] * 1e9 / (w * div).sum()
        k_fon = cap["revenus_fonciers"] * 1e9 / (w * fon).sum()
        for l in lignes:
            l["poids"] = round(float(w[l["unite"]]), 3)
            l["dividendes"] = round(l["dividendes"] * k_div, 2)
            l["revenus_fonciers"] = round(l["revenus_fonciers"] * k_fon, 2)
    return lignes


def smic_mensuel_brut(annee: int = 2026) -> float:
    """Smic brut mensuel à temps plein (151,67 heures), lu dans la législation d'OpenFisca-France."""
    from openfisca_france import FranceTaxBenefitSystem
    h = FranceTaxBenefitSystem().parameters(f"{annee}-01-01").marche_travail.salaire_minimum.smic.smic_b_horaire
    return float(h) * 151.67


def _raking(A, cibles, w0, iterations=200, bornes=(0.2, 5.0)):
    """Calage par ratissage (méthode de Deville et Särndal, fonction raking bornée) : poids w = w0 · exp(Aᵀλ)."""
    w = w0.copy()
    for _ in range(iterations):
        for k in range(len(cibles)):
            tot = A[k] @ w
            if tot <= 0:
                continue
            f = cibles[k] / tot
            m = A[k] > 0
            w[m] *= f ** (A[k][m] / A[k][m].max())
        w = np.clip(w, w0 * bornes[0], w0 * bornes[1])
    return w


def ecrire(lignes, chemin=SORTIE):
    with chemin.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(lignes[0]))
        wr.writeheader()
        wr.writerows(lignes)


def controler(lignes, p=None):
    """Marges obtenues contre leurs cibles (en millions)."""
    p = p or Parametres()
    import collections
    poids = {l["menage"]: l["poids"] for l in lignes}  # poids de l'unité de tirage, porté par chaque ménage
    W = sum(poids.values())
    st = collections.Counter()
    for l in lignes:
        st[l["statut"]] += l["poids"]
    pers = sum(l["poids"] for l in lignes)
    print(f"ménages {W / 1e6:.2f} M, personnes {pers / 1e6:.2f} M")
    for k, x in sorted(st.items()):
        print(f"  {k:15s} {x / 1e6:6.2f} M")
    masse = lambda c: sum(l[c] * l["poids"] for l in lignes) / 1e9  # noqa: E731
    for c in ("salaire_brut", "cout_employeur", "revenu_independant", "chomage_brut", "pension_brute", "dividendes", "revenus_fonciers"):
        print(f"  masse {c:20s} {masse(c):7.1f} Md€")
    hand = sum(l["poids"] for l in lignes if l["handicap"])
    print(f"  marges : écart maximal {max(abs(x) for x in ECARTS_CALAGE):.2%}")
    print(f"  handicap {hand / 1e6:.2f} M ; dispersion des poids {min(poids.values()):.0f}–{max(poids.values()):.0f}")


if __name__ == "__main__":
    lignes = generer()
    ecrire(lignes)
    controler(lignes)
    print(f"→ {SORTIE.relative_to(RACINE)} ({len(lignes)} personnes)")
