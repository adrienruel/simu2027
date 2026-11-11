# Architecture : un noyau commun, un dossier par programme (4 novembre 2026)

Objectif : chiffrer tous les programmes de la présidentielle avec les mêmes hypothèses. Décision d'Adrien : un seul
dépôt, un noyau commun et un dossier par programme (`programmes/<candidat>/`).

## Règles

1. **Un programme ne redéfinit jamais une hypothèse commune.** Le chargeur des paramètres refuse une clé présente
   dans deux fichiers (`moteur/parametres.py`, test `tests/test_programmes.py`).
2. **Une mécanique nouvelle va dans le noyau** et sert à tous les programmes ; un programme ne contient que ses
   mesures et l'interprétation de son texte.
3. **Les hypothèses communes sont figées avant de chiffrer les autres candidats**, et chaque changement du noyau
   recalcule tous les programmes.
4. Le résultat d'un programme se lit comme un **écart au scénario sans réforme** (`moteur/statu_quo.ecart`).

## Où en est le découpage

### Paramètres : fait (première passe)

| Fichier | Contenu | Nombre |
|---|---|---|
| `parametres/commun/economie.yaml` | Données et hypothèses communes : économie, démographie, système actuel, comportements, entreprises, santé, inflation | 171 |
| `parametres/commun/options.yaml` | Options du modèle : unités, modules activés, corrections de méthode | 21 |
| `parametres/commun/statu_quo.yaml` | Scénario sans réforme : point de départ (PLF 2027), blocs de dépense, retraites | 15 |
| `programmes/ecologie_de_droite/parametres.yaml` | Mesures du programme et hypothèses propres à ses mesures | 263 |

Le classement est écrit dans `outils/decouper_parametres.py` (utilisé une fois). Les 263 paramètres du programme
comprennent 179 sources et hypothèses qui décrivent l'effet de ses mesures (réformes de l'emploi, logement,
seniors, capital du fonds, coupes par mission…) : elles iront dans la bibliothèque de mesures quand chaque mesure y
sera codée de façon générique. Classement à relire paramètre par paramètre ; points discutables :
`macro.annees_effet_ajustement` (commun), `macro.baisse_spread` et `macro.adoption_ia` (programme),
`tva.*` (le barème de la TVA écologique est au programme, alors que certaines données d'émissions sont communes).

Aussi déplacés dans le dossier du programme : `registre_lois.yaml` (mesures séparables) et `mesures_economies.csv`
(économies datées). Les ménages types (`parametres/menages_types.yaml`) restent communs.

### Code : à faire

Le code est encore dans `moteur/`, qui mêle le noyau et le programme. Carte des modules :

| Noyau (commun) | Programme « Écologie de droite » | Mêlé : à scinder |
|---|---|---|
| `parametres`, `unites`, `trajectoire`, `demographie` (sauf l'effet sur la natalité), `inflation` (sauf l'indexation du RUI), `taux_effectifs`, `distribution`, `systeme_actuel`, `sante` (trajectoire), `incertitude`, `sensibilite`, `attribution`, `restitution`, `calendrier` (2027-2028), `recettes/successions` | `impot_unique`, `epargne`, `retraites_transition`, `ancien_systeme` (bascule), `anciennes_pensions`, `tva` (TVA écologique), `carbone`, `ascenseur_social`, `carrieres`, `objectifs`, `is_investissement`, `is_bareme`, `collectivites` (impôt local unique), `logement`, `recettes/*` (nouveau système), `depenses/quotient`, `depenses/ia_administration`, `depenses/economies_missions` | `emploi` et `emploi_canaux` (canaux communs, réformes du programme), `cohortes` (cellules communes, impôt unique et comptes), `entreprises_cellules` (données communes, IS à 45 % et fonds), `hauts_revenus`, `menages_types`, `mesures`, `depenses/budget_etat`, `depenses/ministeres`, `depenses/statique` |

## Étapes suivantes

1. **Scénario sans réforme, 2029-2073 : fait (4 novembre 2026)**, `moteur/statu_quo.py` (docs/statu_quo.md) : le
   système actuel projeté avec la même démographie, la même macro, les retraites par répartition (calées sur le COR,
   contrôlées hors calage) et des blocs de dépense à législation constante. Reste : « programme vide = statu quo »
   (après l'étape 2) et la validation contre la Commission européenne et la Cour des comptes.
2. **Scinder les modules mêlés.** Première partie faite le 4 novembre 2026 : le **noyau** (`moteur/noyau.py`) tient
   la comptabilité de tous les programmes (statu quo + mesures, puis intérêts, dette, déficit) ; un programme lui
   passe des **mesures** (recettes, blocs de dépense du statu quo, blocs nouveaux, participations) et un **contexte**
   (PIB, inflation, écart de taux, chômage, dette de fin 2028). Tests (`tests/test_noyau.py`) : programme vide =
   statu quo, à l'identique ; « Écologie de droite » (`programmes/ecologie_de_droite/programme.py`) rebranché sur le
   noyau retrouve les résultats de son moteur à 1e-13 près.
   Périmètres alignés (même jour) : les collectivités, que le programme sort de son budget, y sont remises (dépenses et
   ressources propres, solde inchangé) ; l'écart de départ se lit poste par poste (docs/statu_quo.md). Les recettes
   du statu quo sont détaillées impôt par impôt, chacune avec son assiette.
   **Plus de moteur propre (12 novembre 2026).** `moteur/macro.py`, `moteur/trajectoire_annuelle.py` et
   `moteur/simulation.py` sont supprimés. Le programme « Écologie de droite » passe entièrement par le noyau :
   son budget (`programmes/ecologie_de_droite/budget.py`) et ses effets économiques
   (`programmes/ecologie_de_droite/effets.py`) sont des mesures ; le multiplicateur, l'offre (seniors), les taux, le
   chômage et la conjoncture viennent du pipeline commun. Deux mécanismes génériques sont ajoutés au noyau :
   les **dynamiques** (objets à état par scénario, comme le fonds d'épargne, qui donnent chaque année PIB, recettes,
   blocs, emploi et chômage) et la **règle de trajectoire** (`Regle` : cible de déficit, leviers ordonnés avec leur
   capacité et leur rendement, mesures automatiques). Les comptes sont publiés avec et sans règle
   (`deficit_sans_regle`, `regle`, `dynamiques`). Détail des écarts avec l'ancien moteur : docs/journal.md.
   **Canaux déclarés (12 novembre 2026).** Les effets propres qu'Écologie de droite était seul à compter (fraude à
   la TVA, productivité, adoption de l'IA, niveau des élèves, baisse de l'écart de taux) et la règle de trajectoire
   sont ouverts à tous : un programme les déclare dans le groupe `<nom>_canaux` de ses paramètres
   (`moteur/canaux_declares.py`). Le noyau publie tout programme à règle avec et sans la règle (`sans_regle`), et la
   quasi-dette qu'une dynamique déclare (`quasi_dette`).
   Reste : les mesures « méthode » (pont entre le registre du programme, bâti sur la tendance et la population
   prudentes, et chaque scénario) à retirer en bâtissant le registre par scénario. Question ouverte : classement du
   fonds (dans ou hors des administrations publiques).
3. **Bibliothèque de mesures sur le système actuel** (barèmes, CSG, cotisations, prestations, TVA, IS, retraites,
   missions), avec leurs effets micro (OpenFisca) et leurs réactions par instrument.
4. **Population représentative** passée dans OpenFisca : distribution par décile.
5. **Un deuxième programme chiffré en entier** comme test de l'architecture, puis les autres.
