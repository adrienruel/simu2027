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
| `parametres`, `unites`, `trajectoire`, `demographie` (sauf l'effet sur la natalité), `inflation` (sauf l'indexation du RUI), `taux_effectifs`, `distribution`, `systeme_actuel`, `sante` (trajectoire), `incertitude`, `sensibilite`, `attribution`, `restitution`, `calendrier` (2027-2028), `recettes/successions` | `impot_unique`, `epargne`, `retraites_transition`, `ancien_systeme` (bascule), `anciennes_pensions`, `tva` (TVA écologique), `carbone`, `ascenseur_social`, `carrieres`, `objectifs`, `is_investissement`, `is_bareme`, `collectivites` (impôt local unique), `logement`, `recettes/*` (nouveau système), `depenses/quotient`, `depenses/ia_administration`, `depenses/economies_missions` | `macro` (comportements communs et clause, fonds, RUI), `trajectoire_annuelle`, `emploi` et `emploi_canaux` (canaux communs, réformes du programme), `cohortes` (cellules communes, impôt unique et comptes), `entreprises_cellules` (données communes, IS à 45 % et fonds), `hauts_revenus`, `menages_types`, `mesures`, `depenses/budget_etat`, `depenses/ministeres`, `depenses/statique`, `simulation` |

## Étapes suivantes

1. **Scénario sans réforme, 2029-2073 : fait (4 novembre 2026)**, `moteur/statu_quo.py` (docs/statu_quo.md) : le
   système actuel projeté avec la même démographie, la même macro, les retraites par répartition (calées sur le COR,
   contrôlées hors calage) et des blocs de dépense à législation constante. Reste : « programme vide = statu quo »
   (après l'étape 2) et la validation contre la Commission européenne et la Cour des comptes.
2. **Scinder les modules mêlés** : le noyau calcule l'économie et le système actuel ; un programme lui passe des
   mesures par des points d'entrée (recette, dépense, barème, transfert, choc sur le coût du travail, sur le taux
   marginal, sur le taux effectif de l'IS). « Écologie de droite » est rebranché ainsi, résultats inchangés.
3. **Bibliothèque de mesures sur le système actuel** (barèmes, CSG, cotisations, prestations, TVA, IS, retraites,
   missions), avec leurs effets micro (OpenFisca) et leurs réactions par instrument.
4. **Population représentative** passée dans OpenFisca : distribution par décile.
5. **Un deuxième programme chiffré en entier** comme test de l'architecture, puis les autres.
