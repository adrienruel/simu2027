# Relecture du moteur et feuille de route (25/11/2026)

Relecture du dépôt au commit `2f13404` (« Ménages types : montants du moteur rapportés aux totaux de la
population »). Périmètre : `moteur/` (≈ 6 800 lignes), son chargement des paramètres, la suite de tests et le Monte
Carlo. Les programmes, le comparateur et les choix de sources ne sont relus que là où ils touchent au moteur.

## 1. État des lieux

**Points forts, à garder**

- Une règle d'architecture claire et appliquée par le code : un programme = statu quo + mesures + canaux communs.
  Un programme ne peut pas redéfinir une hypothèse commune, puisque le chargeur refuse les clés en double
  (`moteur/parametres.py`).
- Des paramètres typés : statut (SOURCE / HYPOTHESE / DECISION), unité, année des euros, source et URL. Un paramètre
  SOURCE sans source est refusé.
- Le statu quo est le même calcul qu'un programme vide : `noyau.trajectoire` sans mesure donne exactement le statu
  quo.
- Quatre scénarios avec la logique du « miroir » (une relance prend les paramètres du scénario symétrique). Chaque
  scénario reste ainsi du même côté de la prudence, quel que soit le sens de la mesure.
- Une traçabilité forte : `docs/journal.md`, un point de référence (`ref-2026-11-20`) et
  `outils/ecarts_reference.py`.
- Environ 350 tests, dont des tests de propriété (`test_proprietes.py`) et d'indépendance
  (`test_independance.py`).

**Mesures faites pendant la relecture** (Python 3.13, sans OpenFisca-France installé)

| Mesure | Résultat |
|---|---|
| `pytest -q` (sans OpenFisca) | 339 réussis, 9 échecs, 4 erreurs, 1 ignoré, en 3 min 18 s |
| `python -m moteur.noyau statu_quo` | 0,36 s |
| `noyau.simuler` d'Attal (profilage) | 3,1 s, dont **≈ 40 % passés à lire du YAML** |
| `noyau.charger(<programme>)` | 0,24 s par appel, presque uniquement la lecture YAML |
| Lecture des 6 fichiers YAML (commun + Attal) | `SafeLoader` 0,211 s, `CSafeLoader` 0,018 s (**× 12**) |

## 2. Constats

### 2.1 Suite de tests : pas au vert sur `main`

| Test | Cause |
|---|---|
| `test_age_depart_micro.py` (3 tests sur 4) | `AttributeError: 'B' object has no attribute '_masse'`. Les tests appellent `Base.population` sur un `SimpleNamespace`, alors que `Base.population` appelle maintenant `self._masse` (`outils/openfisca_mesures.py:752` et `:790`). C'est une **régression réelle**, sans lien avec OpenFisca. |
| `test_age_depart_micro.py::test_formules_des_derniers_trous`, `test_microsimulation.py` (2 échecs, 4 erreurs) | `ModuleNotFoundError: openfisca_france`. Ces tests devraient être *ignorés* sans OpenFisca (`pytest.importorskip`), comme l'est déjà `test_openfisca_mesures.py`. |
| `test_sorties.py::test_sorties_produites_avec_les_parametres_actuels` | Une vingtaine de sorties (`banc_essai.csv`, `c1_*.json`, `comparaison_*`…) datent d'avant les derniers changements de paramètres et sont à régénérer. |
| `test_independance.py::test_programmes_publies_se_recalculent_a_l_identique` | Arthaud, crise, 2030 : `12.435 == 12.436`. Le test compare **à l'égalité stricte** des valeurs arrondies au millième. Il casse dès qu'un calcul flottant change de dernier chiffre (version de Python ou de numpy, ordre d'une somme). |
| `test_incertitude.py::test_rho1_dixieme_centile_retrouve_le_prudent` | Mélenchon : écart de 0,917 pour une tolérance de 0,9. Il faut décider : régénérer les tirages, ou revoir la tolérance avec une justification. |

### 2.2 Performance

1. **Le YAML est relu à chaque tirage du Monte Carlo.** `incertitude.un_tirage` appelle `noyau.charger(nom)`
   (`moteur/incertitude.py:239`) pour chaque programme et chaque tirage. Or `ProgrammeSimple.__init__` reconstruit
   `Parametres(programme=…)`, ce qui relit tous les YAML (0,24 s). Cela fait environ 3 s par tirage pour 12
   programmes, avant tout calcul, soit une part importante de l'heure 45 du Monte Carlo à 600 tirages.
2. **Le chargeur YAML est en Python pur.** `_ChargeurStrict` hérite de `yaml.SafeLoader`
   (`moteur/parametres.py:36`). `CSafeLoader` est disponible (libyaml) et lit 12 fois plus vite. Le contrôle des clés
   en double peut être gardé, car le constructeur s'ajoute de la même façon.
3. **Les caches sont indexés par `id(p)`**, avec une liste `_VIVANTES` qui garde *toutes* les instances en vie
   (`moteur/parametres.py:79`) pour éviter qu'un `id` soit réattribué. Il y a environ 80 usages de `_cache` /
   `id(p)` dans `moteur/` et `programmes/`. Conséquence : la mémoire croît sans limite. Le Monte Carlo contourne le
   problème avec `maxtasksperchild=10`, c'est-à-dire en relançant les processus.

### 2.3 Robustesse et architecture

1. **`ProgrammeSimple._calcul` fait environ 260 lignes** (`moteur/programme_simple.py:440`). Il mélange les mesures
   simples, l'IS, le PFU, les postes publics, l'éviction, la valeur d'un emploi, le multiplicateur, l'offre, les
   seniors et la démographie. Il écrit aussi des états de côté sur l'instance (`self.pib_en_plus`,
   `self.cout_postes_calcules`, `self.non_retraites`, `self.enveloppe_detail`), indexés par `(id(p), s)`. L'ordre
   des appels compte, ce qui rend le module difficile à relire et à tester par morceaux.
2. **État mutable dans la règle de trajectoire** : `Regle.declenchee` est écrit pendant le calcul
   (`noyau._appliquer_regle`). La documentation demande une règle « neuve à chaque appel ». Rien ne l'impose, donc
   réutiliser un objet `Regle` fausse le second passage sans erreur visible.
3. **Copie superficielle dans `Parametres.en_crise`** (`moteur/parametres.py:158`) : la copie partage le
   dictionnaire `_p` de l'original. Toute écriture `c._p[...] = …` sur la copie modifie aussi l'original. Ce n'est
   pas un bug aujourd'hui, mais c'est un piège.
4. **Code mort** : `Parametres._surcharges` est un dictionnaire mutable *de classe*, lu dans `val` et
   `statu_quo._v` mais jamais écrit.
5. **Accès aux attributs privés** : `p._p` est lu directement en environ 44 endroits (`moteur`, `programmes`,
   `outils`). Une méthode `p.a(cle)` / `p.get(cle, defaut)` suffirait.
6. **Constantes en dur** : le SMIC brut 2026 (`1823.03 * 12`) est écrit à 4 endroits du moteur
   (`noyau.py:468`, `programme_simple.py:405`, `bibliotheque.py:190`, `offre.py:67`) au lieu d'être un paramètre
   sourcé. C'est contraire à la règle « une hypothèse = un paramètre sourcé ».
7. **Rampe de montée incohérente** dans `ProgrammeSimple.profil` : avec `depart`, la montée vaut
   `(t − debut) / (plein − debut)` ; sans `depart`, elle vaut `(t − debut + 1) / (plein − debut + 1)`. Les deux
   conventions ne donnent pas la même année de montée en charge. Il faut en choisir une et la documenter.
8. **Exceptions avalées dans le Monte Carlo** : `except Exception` dans `un_tirage` écarte un tirage *pour un seul
   programme*. Si les tirages qui échouent sont les tirages extrêmes, les quantiles de ce programme sont biaisés vers
   le centre, et le classement se compare sur des échantillons différents.

### 2.4 Modélisation (noyau)

1. **La baisse de l'écart de taux se calcule en deux passes, sans point fixe** (`noyau._deux_passes`). La deuxième
   passe change la trajectoire de dette, donc les « années acquises » qui ont servi à la calculer. Rien ne vérifie
   que le résultat est cohérent avec sa propre trajectoire.
2. **La rétroaction des taux n'agit que sur les recettes**, à élasticité 1 (`dy_r × rec_sq / y_sq`). Les dépenses
   indexées sur le PIB et les dépenses sensibles au chômage hors du canal `chomeurs_depenses` ne réagissent pas.
3. **Horizon long (2029-2073) avec des paramètres stables** : une dette qui dépasse 400 % du PIB en crise ne change
   ni la croissance ni les comportements, en dehors de la prime de dette bornée. Les résultats au-delà de 2050 sont à
   présenter comme des trajectoires mécaniques, pas comme des prévisions.
4. **Balance commerciale linéaire** (`_balance`) : correcte pour de petits chocs, à borner ou signaler pour les
   programmes qui déplacent fortement le PIB ou les prix.

## 3. Feuille de route

Chaque chantier indique son critère de fin. L'ordre suit le rapport utilité / effort. Les phases R0 et R1 ne
changent aucun résultat publié, ce qui se vérifie avec `outils/ecarts_reference.py`.

### R0 — Remettre `main` au vert (½ journée)

- **R0.1** Corriger les 3 tests `test_age_depart_micro` : fournir `_masse` au stub (ou appeler une instance réelle
  de `Base`), ou rendre `_masse` statique.
- **R0.2** Ajouter `pytest.importorskip("openfisca_france")` en tête des tests qui en dépendent
  (`test_microsimulation.py`, `test_formules_des_derniers_trous`).
- **R0.3** Régénérer les sorties signalées par `test_sorties.py` et commiter avec leur raison.
- **R0.4** `test_independance` : comparer avec une tolérance (par exemple `abs(d − pub) ≤ 1e-3`) plutôt qu'à
  l'égalité stricte sur des arrondis.
- **R0.5** `test_incertitude` (Mélenchon) : régénérer les tirages ; si l'écart reste au-dessus de 0,9, documenter la
  nouvelle tolérance dans `docs/incertitude.md`.
- **R0.6** Intégration continue (GitHub Actions) avec deux tâches : suite rapide sans OpenFisca à chaque push, suite
  complète la nuit.

*Fin : `pytest -q` vert avec et sans OpenFisca ; badge de l'intégration continue dans le README.*

### R1 — Performance (1 à 2 jours)

- **R1.1** Chargeur YAML en C : `class _ChargeurStrict(getattr(yaml, "CSafeLoader", yaml.SafeLoader))`.
- **R1.2** Mémoriser le YAML brut par fichier (dictionnaire de module indexé par chemin et date de modification) :
  un seul passage du parseur par processus.
- **R1.3** Monte Carlo : construire chaque programme **une fois** dans `_preparer` et ne remplacer que `prog.pt` à
  chaque tirage (c'est déjà fait pour `pt`, mais `charger` est rappelé). Si l'état d'instance l'empêche, voir R2.1.
- **R1.4** Caches : remplacer `id(p)` + `_VIVANTES` par un jeton stable posé à la construction
  (`p.jeton = uuid4()` ou un compteur), ou par un cache attaché à l'objet qui disparaît avec lui. On peut alors
  supprimer `_VIVANTES` et `maxtasksperchild`.
- **R1.5** Mesurer avant et après : temps d'un tirage, temps total `moteur.incertitude 600`, mémoire maximale.

*Fin : Monte Carlo au moins 2 fois plus rapide, mémoire stable ; sorties identiques au bit près
(`ecarts_reference`).*

### R2 — Architecture et robustesse (3 à 5 jours)

- **R2.1** Découper `ProgrammeSimple._calcul` en étapes pures qui prennent et rendent un objet `Calcul` explicite
  (mesures, canaux d'emploi, PIB en plus, coût des postes, non-retraités) au lieu d'attributs posés sur l'instance.
  Ordre proposé : `mesures_simples → mesures_calculees → enveloppe → emploi → demande → offre → seniors →
  démographie → contexte`. Chaque étape devient testable seule.
- **R2.2** `Regle` sans état : `declenchee` passe dans `etat`, ou la règle est copiée (`dataclasses.replace`) au
  début de `trajectoire`.
- **R2.3** `Parametres` : `en_crise` copie `_p` ; supprimer `_surcharges` ; ajouter `p.a(cle)` et
  `p.get(cle, defaut)`, puis remplacer les accès à `p._p` hors de `parametres.py`.
- **R2.4** Sortir les constantes en dur (SMIC brut 2026, etc.) dans `parametres/commun/economie.yaml` avec leur
  source. Ajouter un test qui cherche les nombres magiques connus dans `moteur/`.
- **R2.5** Unifier la rampe de `profil` et la documenter. Mesurer l'effet sur les programmes qui utilisent `depart`.
- **R2.6** Typage progressif (`mypy --strict` sur `noyau`, `parametres`, `statu_quo`) et `ruff` dans l'intégration
  continue.

*Fin : `_calcul` ≤ 60 lignes, aucun attribut d'état sur `ProgrammeSimple` ; aucun `p._p` hors de `parametres.py` ;
résultats identiques ou écarts expliqués dans le journal.*

### R3 — Modélisation du noyau (1 à 2 semaines, chaque point commité avec son effet)

- **R3.1** Baisse de l'écart de taux en point fixe : itérer `_deux_passes` jusqu'à ce que les « années acquises » ne
  changent plus (au plus 5 itérations), et publier le nombre d'itérations et l'écart résiduel.
- **R3.2** Rétroaction des taux : faire passer `dy_r` par les mêmes canaux que le multiplicateur (blocs indexés sur
  le PIB, chômage), au lieu des seules recettes.
- **R3.3** Garde-fous de long terme : drapeau « hors domaine » quand la dette dépasse un seuil (par exemple 250 %
  du PIB) ou quand un choc de PIB ou de prix sort du domaine de calage de Mésange. Ce drapeau est affiché dans le
  comparateur.
- **R3.4** Balance commerciale : borner l'approximation linéaire ou signaler son domaine de validité.
- **R3.5** Une passe de propriétés économiques automatisées (étendre `test_proprietes.py`) : monotonie (une recette
  en plus n'augmente jamais le déficit à PIB donné), symétrie par miroir, additivité approchée des mesures, programme
  vide = statu quo pour chaque sortie.

### R4 — Incertitude (1 semaine)

- **R4.1** Tirages en échec : publier leur nombre par programme ; au-delà d'un seuil (par exemple 1 %), le résultat du
  programme est signalé. Comparer les programmes sur les tirages communs réussis.
- **R4.2** Quantiles : afficher l'erreur de Monte Carlo (intervalle des quantiles par bootstrap) pour savoir si 600
  tirages suffisent à départager deux programmes.
- **R4.3** Finir le point ouvert de la roadmap 6.2 (corrélation des taux) dès que la série de l'OAT à 10 ans est
  disponible, et remplacer la borne ρ = 1, non soutenue par les données, par une corrélation estimée.

### R5 — Points ouverts du journal à fermer

- Pauvreté de la population vieillie ≈ 18,4 %, contre 15,4 % pour l'Insee (journal, 23/11/2026).
- IR de la population : 123,7 Md€ contre 119,5 Md€ visés (+3,5 %).
- Mélenchon : sortie du nucléaire à 60 ans et EPR2 non chiffrés (`docs/melenchon.md`).
- Archivage des tableaux sources hors ligne (`docs/sourcage.md`), pour que chaque SOURCE reste vérifiable.

## 4. Ordre conseillé

R0 (tout de suite) → R1.1 à R1.3 (gain immédiat, sans risque) → R2.2 et R2.3 (petits correctifs) → R1.4 et R2.1
(gros chantier, à faire ensemble) → R3 et R4, point par point, chacun mesuré contre `ref-2026-11-20`.
