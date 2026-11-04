# Scénario sans réforme (statu quo projeté), 2029-2073 (4 novembre 2026)

`moteur/statu_quo.py`, paramètres `parametres/commun/statu_quo.yaml`, tests `tests/test_statu_quo.py`.
`python -m moteur.statu_quo` (sorties/statu_quo.json) ; `python -m moteur.statu_quo --ecart` ajoute l'écart avec le
programme chiffré.

Première étape de la feuille de route multi-programmes : la référence commune. Chaque programme se lit comme un
écart à ce scénario.

## Règles

- **Noyau commun** : le module ne lit que `parametres/commun/` (un test le vérifie avec un programme vide). Aucun
  effet d'un programme : ni sur la natalité, ni sur l'inflation (carbone, effort de 2029), ni sur les taux
  (`macro.baisse_spread`), ni mesures de 2028.
- **Mêmes hypothèses que les programmes** : démographie de l'Insee (2026) par scénario de fécondité, taux d'emploi
  et de chômage par âge de 2025, productivité (`macro.tendance`) et IA, inflation de base, taux d'intérêt
  (taux apparent, taux de marché, effet de Fisher, prime liée à la dette), pentes de la santé.
- **Mêmes conventions** : euros constants de 2026, économie de 2026 placée en 2029, déficit au sens de Maastricht.
- **Législation constante** : celle du PLF 2027 (déficit de 5 % en 2027), supposée votée et maintenue, comme dans
  `calendrier.deficit_tendanciel_2027_2028`. Ensuite, aucune mesure nouvelle. DÉCISION d'Adrien (4/11/2026) : point
  de départ provisoire, le PLF 2027 n'étant pas encore voté ; à actualiser avec la loi de finances votée.

## Point de départ (2029, Md€ de 2026)

Dépense publique 56,9 % du PIB, intérêts 2,9 %, déficit 5,0 % (PLF 2027, avis du HCFP n° 2026-5) : dépense primaire
54,0 %, recettes 51,9 %. La dépense primaire est découpée en blocs ; le reste est « autres ».

| Bloc | 2029 | Évolution à législation constante | Source du niveau |
|---|---|---|---|
| Retraites | 428 | toutes les générations (voir plus bas) | COR 2026 : 14,1 % du PIB |
| Santé (ONDAM, autonomie) | 301 | pentes communes (Assurance maladie jusqu'en 2035, puis PROMEDE) | LFSS 2026, DREES |
| Assurance chômage | 47 | chômeurs × salaires | Unédic, octobre 2026 |
| Famille | 61 | enfants, prix | encadré par la DREES (2,2 %) |
| Logement | 15 | population, prix | encadré par la DREES (0,6 %) |
| Pauvreté (RSA, prime d'activité) | 30 | adultes de 18 à 64 ans, prix | encadré par la DREES (1,2 %) |
| AAH et invalidité | 24 | adultes, prix | PLF 2026 ; hors ONDAM 2024 |
| Investissement | 134 | PIB | Insee, 2025 : 4,4 % |
| Défense, UE, missions économiques | 106 | PIB | encadré (missions de l'État) |
| Enseignement | 152 | salaires × élèves et étudiants (élasticité 0,5) | encadré par Eurostat (5,2 %) |
| Autres (reste) | 346 | salaires × population (loi de Baumol) | dépense primaire − blocs |

Recettes : part du PIB constante (élasticité 1, convention du HCFP et du COR), sauf les 12 % des pensions prélevés
(CSG, CASA, impôt sur le revenu des retraités), qui suivent les pensions.

## Retraites

Génération par génération, comme l'ancien système du programme, mais pour toutes les générations : survivants
(Insee), part partie à chaque âge (âge légal de 64 ans), pension liquidée = salaire moyen de quinze ans plus tôt
(droits revalorisés sur les prix) × érosion relative de 0,46 % par an, puis revalorisée sur les prix.

L'érosion est le seul paramètre calé : sur le COR (15,3 % du PIB en 2070, productivité 0,7 %). Contrôles non calés :

| Dépenses de retraite (% du PIB) | Moteur | COR, juin 2026 |
|---|---|---|
| 2030 | 14,2 | 14,1 |
| 2045 | 14,2 | 14,2 |
| 2070, productivité 0,4 % | 15,96 | 16,1 |
| 2070, productivité 1,0 % | 14,72 | 14,5 |

La sensibilité à la productivité vient du décalage de quinze ans : elle est retrouvée sans calage.

## Résultats

| Déficit (% du PIB) / dette (% du PIB) | 2029 | 2032 | 2037 | 2045 | 2050 | 2060 |
|---|---|---|---|---|---|---|
| Crise | 5,5 / 129 | 6,5 / 139 | 8,1 / 160 | 11,1 / 207 | 16,2 / 257 | 54 / 527 |
| **Prudent** | **5,6 / 128** | **6,7 / 138** | **8,6 / 159** | **12,0 / 206** | **16,8 / 255** | **46 / 480** |
| Médian | 5,5 / 128 | 6,3 / 134 | 7,2 / 147 | 8,1 / 172 | 9,8 / 194 | 17 / 274 |
| Optimiste | 5,4 / 128 | 6,1 / 133 | 6,9 / 143 | 7,9 / 165 | 9,2 / 184 | 14 / 242 |

**Le statu quo n'est pas soutenable** : le déficit primaire reste vers 2 % du PIB jusqu'en 2050, alors que le taux
d'intérêt dépasse la croissance (taux de marché de 4 % contre une croissance en valeur d'environ 2 %, freinée par la baisse
des actifs). La dette passe 200 % du PIB vers 2045 dans le prudent (2051 dans le médian). La prime de taux liée à la dette
accélère l'emballement ; sans elle, prudent : 8,1 % de déficit en 2037, 10,8 % en 2050, dette 221 % en 2050. Au-delà
de 2050, les chiffres n'ont plus de sens économique (aucun État ne laisserait la dette aller là) : ils disent
seulement que la trajectoire diverge.

Ce qui bouge de 2029 à 2073 (prudent, points de PIB de dépense primaire) : santé +4,1 ; retraites +1,5 ; autres
(salaires × population, pour moins d'actifs) +0,9 ; prestations indexées sur les prix −1,4 (famille −0,9) ;
enseignement −0,2.

## Écart programme « Écologie de droite » − statu quo (prudent)

| | 2029 | 2032 | 2037 | 2045 | 2050 | 2060 |
|---|---|---|---|---|---|---|
| Solde primaire, sans la règle (points de PIB, + = mieux) | +0,6 | +1,2 | +2,8 | +3,6 | +2,1 | +5,8 |
| Solde primaire, règle comprise | +2,5 | +3,2 | +3,9 | +3,5 | +3,6 | +6,0 |
| Déficit : programme sans règle / statu quo | 5,0 / 5,6 | 5,2 / 6,7 | 4,0 / 8,6 | 3,0 / 12,0 | 4,9 / 16,8 | 3,2 / 46 |
| Chômage : programme / statu quo | 9,3 / 8,3 | 8,5 / 8,4 | 7,4 / 8,3 | 7,3 / 8,2 | 7,4 / 8,1 | 7,2 / 8,1 |
| PIB (écart, %) | −1,9 | +0,1 | +3,0 | +3,3 | +3,2 | +3,5 |

Lecture : l'écart de solde primaire est la mesure propre aux politiques ; l'écart de déficit et de dette grossit
surtout par les intérêts (la dette du statu quo fait boule de neige). En 2029, le programme fait plus de chômage
(récession de l'effort de bascule) et 1,9 % de PIB en moins ; à partir de 2037, moins de chômage et plus de PIB.

**À lire avec prudence** : le programme chiffre son budget de départ ligne par ligne, le statu quo part des
agrégats du PLF 2027. Une partie de l'écart de 2029 peut venir de cette différence de méthode, et non des mesures.
Le test qui le tranchera (« programme vide = statu quo ») suppose l'étape suivante : brancher le programme sur le
noyau par des mesures.

## Limites

- **Taux d'emploi par âge figés à 2025** (comme le programme) : la fin de la montée à 64 ans n'augmente pas l'emploi
  des seniors ; chômage à 8 % environ, contre 7 % dans le COR à partir de 2040. Le PIB est donc un peu plus bas que
  celui du COR ; l'érosion calée sur le COR en porte une partie.
- **Santé** : la pente commune fait suivre la santé aux salaires (et à sa part du PIB selon PROMEDE), le PIB suivant
  les actifs ; avec moins d'actifs, la part de la santé monte de 4 points d'ici 2073. PROMEDE compte déjà une partie
  du vieillissement : un recouvrement possible, commun au programme. DÉCISION d'Adrien (4/11/2026) : la trajectoire
  des dépenses de santé est gardée telle quelle (sujet important ; mieux vaut ne pas la sous-estimer).
- **Blocs encadrés, pas sourcés** : famille, logement, pauvreté, défense et missions, enseignement (parts de la DREES
  et d'Eurostat, tous financeurs ou années anciennes). Une erreur de répartition entre blocs indexés sur les prix et
  blocs indexés sur les salaires pèse environ 0,2 point de PIB en 2073 par demi-point mal classé.
- **Recettes à part du PIB constante** : pas d'effet du barème de l'impôt sur le revenu indexé sur les prix
  (convention), pas de recettes qui baissent avec la part des salaires.
- **Pas encore validé contre les projections de long terme de la Commission européenne** (rapport sur le
  vieillissement) ni contre une projection de la Cour des comptes.

## Sources

- COR, Évolutions et perspectives des retraites en France, rapport annuel de juin 2026 (et synthèse).
- HCFP, avis n° 2026-5 relatif aux projets de lois de finances et de financement de la sécurité sociale pour 2027.
- Insee, Le compte des administrations publiques en 2025, Insee Première n° 2106 (mai 2026).
- Unédic, prévisions financières d'octobre 2026.
- DREES, comptes de la protection sociale (parts par risque, 2022, citées par l'iFRAP).
