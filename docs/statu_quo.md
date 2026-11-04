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
| Prestations familiales | 35 | enfants, prix | branche famille 2023 (REPSS) |
| Aides personnelles au logement | 17 | population, prix | compte du logement 2025 |
| RSA ; prime d'activité | 24 | chômeurs, prix ; emploi et barème fixe face aux salaires (OpenFisca) | DREES, Sénat (PLF 2025) |
| AAH et invalidité | 24 | adultes, prix | PLF 2026 ; hors ONDAM 2024 |
| Investissement | 134 | PIB | Insee, 2025 : 4,4 % |
| Missions de l'État (crédits 2026 hors pensions, hors blocs déjà comptés) | 210 | chacune selon sa règle : salaires × public servi (population, élèves, étudiants, enfants, emploi), PIB ou prix | budget 2026 |
| Défense et contribution à l'UE | 88 | PIB | loi de programmation ; PLF 2027 |
| Collectivités (hors RSA, autonomie, investissement) | 230 | salaires × population | Insee 2025 |
| Reste (Sécurité sociale hors blocs, opérateurs) | 106 | salaires × population | dépense primaire − blocs |

Recettes impôt par impôt : le niveau du PLF 2027 (51,9 % du PIB), dont 6,3 % de recettes non fiscales (Insee 2025),
réparti entre impôts selon la reconstitution du système actuel de la v235 (colonne « Ancien », à 0,27 % des comptes de
l'Insee pour 2024). Chaque impôt suit son assiette, barèmes à législation constante (élasticité 1) :

| Impôt (% du PIB en 2029) | 2029 | Assiette |
|---|---|---|
| Cotisations, CSG et IR sur les salaires du privé | 17,1 | masse salariale (emploi × salaire) |
| Idem, agents publics | 6,9 | masse salariale |
| Idem, indépendants | 1,3 | masse salariale |
| CSG, CRDS, CASA et IR des retraités | 1,7 | OpenFisca sur la distribution des pensions |
| TVA | 7,2 | par source de revenu : salaires, pensions (OpenFisca), transferts, TVA non déductible |
| Accises et taxes sur les produits | 3,5 | PIB |
| Impôt sur les sociétés | 2,4 | PIB (bénéfices) |
| Impôts de production | 2,5 | PIB ; CVAE supprimée en 2030 (loi en vigueur) |
| Capital (dividendes, intérêts, IFI) | 1,3 | PIB |
| Successions | 0,7 | PIB × décès (Insee) |
| Droits de mutation | 0,5 | PIB |
| Taxes locales et affectées | 0,6 | PIB |
| Recettes non fiscales | 6,3 | PIB |

**Contrôle par OpenFisca** (`statu_quo.prelevements_activite`) : cotisations, CSG, CRDS et impôt sur le revenu
calculés par OpenFisca-France (législation 2026) sur les distributions de salaires de 2026 donnent 516 Md€ pour le privé
(répartition : 519, −0,6 %) et 202 Md€ pour les agents publics (répartition : 208, −2,8 %). Deux calculs
indépendants qui se recoupent ; limite : cas type d'une personne seule (l'impôt des couples n'y est pas).

**Retraités par OpenFisca** (`statu_quo.prelevements_retraites`, table `outils/openfisca_retraites.py`) : CSG, CRDS,
CASA et impôt sur le revenu sur la distribution des pensions de la DREES, personnes seules et couples (60 % en couple,
pension du conjoint à 62 %) : 51,2 Md€ en 2029 (29,4 de prélèvements sociaux, 21,8 d'impôt sur le revenu), contre
51,2 dans la répartition (−0,1 %). Le calcul est refait chaque année sur la pension moyenne du statu quo.
Convention (`statu_quo.baremes_retraites`, DÉCISION d'Adrien du 4/11/2026 : la loi actuelle) : barèmes sur les
**prix** (taux moyen stable vers 12 % des pensions), plutôt que sur les salaires ou sur les **salaires** (comme les barèmes des programmes :
le taux tombe à 7,5 % en 2073 quand les pensions baissent par rapport aux salaires, 0,7 point de PIB de recettes en
moins).

**TVA par source de revenu** (`statu_quo.tva`) : la consommation est calculée avec la fonction de consommation du
moteur (Insee) sur les revenus disponibles actuels : salariés et agents (OpenFisca, aides comprises), retraités
(pension nette des prélèvements OpenFisca, chaque année), inactifs et étudiants (RSA compris), plus la TVA non
déductible. En 2029 : salaires 82, pensions 40, transferts 10, non déductible 87 Md€ ; le calcul explique 91 % de la
TVA de la répartition (219 Md€), le reste (indépendants, chômeurs, revenus du patrimoine, couples) est réparti au
prorata. Chaque part suit sa source : la TVA passe de 7,21 % du PIB en 2029 à 7,34 % en 2073 (plus de retraités, dont
la consommation pèse plus par euro de revenu).

**Législation en vigueur appliquée** : la CVAE, à 0,28 % en 2027 (environ 3 Md€), passe à 0,19 % en 2028, 0,09 % en
2029 et disparaît en 2030 (loi de finances pour 2025, trajectoire maintenue en 2026) : −2 Md€ en 2029, −3 Md€ ensuite.
La contribution exceptionnelle sur les bénéfices des grandes entreprises (exercices 2025 et 2026) est versée surtout
en 2026 et n'existe plus après : rien à retirer des comptes de 2027.

Avec des taux d'emploi par âge figés, la masse salariale suit le PIB : les recettes restent proches de 51,9 % du PIB ;
ce qui bouge, ce sont les prélèvements sur les pensions (1,7 → 1,9 %) et les successions (0,7 → 0,8 %). Le détail
sert surtout de base aux mesures : une mesure d'un programme agit sur un impôt et son assiette.

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
| Crise | 5,6 / 129 | 6,8 / 139 | 8,7 / 163 | 12,8 / 218 | 19,4 / 280 | 73 / 632 |
| **Prudent** | **5,6 / 129** | **7,0 / 138** | **9,2 / 161** | **13,4 / 216** | **19,4 / 273** | **58 / 553** |
| Médian | 5,5 / 128 | 6,6 / 135 | 8,0 / 151 | 9,9 / 185 | 12,5 / 216 | 24 / 332 |
| Optimiste | 5,4 / 128 | 6,5 / 133 | 7,8 / 146 | 9,5 / 178 | 11,6 / 205 | 18,7 / 290 |

**Le statu quo n'est pas soutenable** : le déficit primaire reste vers 2 % du PIB jusqu'en 2050, alors que le taux
d'intérêt dépasse la croissance (taux de marché de 4 % contre une croissance en valeur d'environ 2 %, freinée par la baisse
des actifs). La dette passe 200 % du PIB vers 2045 dans le prudent (2051 dans le médian). La prime de taux liée à la dette
accélère l'emballement ; sans elle, prudent : 8,0 % de déficit en 2037, 10,5 % en 2050, dette 219 % en 2050. Au-delà
de 2050, les chiffres n'ont plus de sens économique (aucun État ne laisserait la dette aller là) : ils disent
seulement que la trajectoire diverge.

Ce qui bouge de 2029 à 2073 (prudent, points de PIB de dépense primaire) : santé +4,1 ; retraites +1,5 ; autres
(salaires × population, pour moins d'actifs) +0,9 ; prestations indexées sur les prix −1,4 (famille −0,9) ;
enseignement −0,2.

## Écart programme « Écologie de droite » − statu quo (prudent)

| | 2029 | 2032 | 2037 | 2045 | 2050 | 2060 |
|---|---|---|---|---|---|---|
| Solde primaire, sans la règle (points de PIB, + = mieux) | +0,6 | +1,2 | +2,7 | +3,4 | +1,9 | +5,6 |
| Solde primaire, règle comprise | +2,5 | +3,2 | +3,8 | +3,4 | +3,4 | +5,9 |
| Déficit : programme sans règle / statu quo | 5,0 / 5,6 | 5,2 / 6,7 | 4,0 / 8,5 | 3,0 / 11,7 | 4,9 / 16,4 | 3,2 / 44 |
| Chômage : programme / statu quo | 9,3 / 8,3 | 8,5 / 8,4 | 7,4 / 8,3 | 7,3 / 8,2 | 7,4 / 8,1 | 7,2 / 8,1 |
| PIB (écart, %) | −1,9 | +0,1 | +3,0 | +3,3 | +3,2 | +3,5 |

Lecture : l'écart de solde primaire est la mesure propre aux politiques ; l'écart de déficit et de dette grossit
surtout par les intérêts (la dette du statu quo fait boule de neige). En 2029, le programme fait plus de chômage
(récession de l'effort de bascule) et 1,9 % de PIB en moins ; à partir de 2037, moins de chômage et plus de PIB.

**Périmètre aligné (4 novembre 2026)** : le programme sort les collectivités de son budget (financées par l'impôt
local unique) ; elles y sont remises, dépenses et ressources propres pour le même montant (230 Md€ de dépenses en
2029, dont 16 Md€ de besoin de financement déjà au budget), solde inchangé. L'écart de départ, hors effets macro,
se lit alors poste par poste (prudent, Md€, + = améliore le solde) :

| | 2029 | 2037 | 2050 |
|---|---|---|---|
| Recettes (impôt unique, TVA écologique, IS à 45 %… contre impôts actuels) | −163 | −215 | −256 |
| Retraites (socle, transition, ancien système) | +31 | +93 | +100 |
| Santé | −12 | −8 | −9 |
| Revenu universel et AAH (contre chômage, famille, logement, pauvreté, AAH) | +68 | +63 | +65 |
| Investissement et autres dépenses (ministères, collectivités, fonds) | +138 | +168 | +190 |
| **Total (points de PIB)** | **+2,0** | **+3,1** | **+2,6** |

L'écart de recettes de 2029 retrouve celui que la v235 calculait elle-même entre son nouveau et son ancien système
(environ −180 Md€ en euros de 2024) : l'écart vient des mesures, pas d'une différence de méthode. Investissement et
autres dépenses sont regroupés : le programme compte l'investissement dans ses missions et ses collectivités, et sort
une partie de l'investissement public vers le fonds (transports, énergie, France 2030, investissements locaux
rentables), le statu quo le compte dans un bloc à part.

**Fonds hors budget** (DÉCISION d'Adrien, 4/11/2026) : le fonds, qui reprend des investissements publics et des
participations de l'État, reste hors des administrations publiques. À noter : en comptabilité nationale, un fonds
contrôlé par l'État qui finance des infrastructures publiques pourrait être classé parmi les administrations
(Eurostat) ; ses dépenses compteraient alors dans le déficit.

## Feuille de route du statu quo (priorité d'Adrien, 4/11/2026 : chiffrer le statu quo avant de refaire le programme)

1. Prélèvements sur les revenus d'activité par OpenFisca : contrôle fait (privé, public) ; reste les ménages réels
   (couples, enfants) et les indépendants.
2. Retraités : fait (OpenFisca sur la distribution de la DREES, personnes seules et couples).
3. TVA : faite (par source de revenu). Accises : suivent le PIB (à détailler : carburants, tabac, alcool, énergie).
4. IS et impôts de production : séparés, CVAE éteinte en 2030 (loi en vigueur) ; patrimoine : successions selon
   les décès, droits de mutation et capital selon le PIB. Reste : IS par taille d'entreprise (données DGFiP déjà là).
5. Prestations : faites (montants sourcés ; RSA selon les chômeurs ; prime d'activité au barème fixe d'OpenFisca
   face aux salaires qui montent : −52 % par personne en emploi d'ici 2073 ; famille et logement aux prix). Reste :
   prestations familiales par OpenFisca sur des ménages réels.
6. Dépenses : faites. État mission par mission (210 Md€), défense et UE (88), collectivités (230) ; reste 106 Md€
   (Sécurité sociale hors blocs, opérateurs), positif comme il se doit (un reste négatif signalerait un double compte).
7. Validation : faite (section « Validation »).

## Indexation des prestations (DÉCISION d'Adrien, 4/11/2026)

Prestations familiales, aides au logement, RSA, prime d'activité (barème compris), AAH et invalidité suivent les
salaires (`statu_quo.indexation_prestations`) : leur niveau par rapport aux revenus d'activité est gardé. La loi les
revalorise sur les prix ; appliquée pendant 45 ans, elle leur ferait perdre environ un quart par rapport aux salaires
(variante « prix » : environ 0,9 point de PIB de dépense en moins en 2060). Solde primaire du prudent : −2,3 % du PIB en
2029, −2,5 % en 2037, −3,2 % en 2050, −5,1 % en 2060 (sur les prix : −2,3 ; −2,3 ; −2,6 ; −4,3).

Point de neutralité : le programme indexe son revenu universel au minimum de l'inflation et de la croissance nominale,
donc en pratique sur les prix. Avec des prestations du statu quo qui suivent les salaires, l'écart entre les deux
compte désormais le décrochage du revenu universel par rapport aux salaires comme une économie du programme.

## Validation (4 novembre 2026)

| Contrôle | Statu quo | Référence | Lecture |
|---|---|---|---|
| Retraites 2030 / 2045 / 2070 (% du PIB) | 14,2 / 14,2 / 15,3 | COR 2026 : 14,1 / 14,2 / 15,3 | 2070 calé, le reste hors calage |
| Retraites 2070, productivité 0,4 % / 1,0 % | 16,0 / 14,7 | COR : 16,1 / 14,5 | hors calage |
| Retraites 2070 | 15,3 | Commission européenne 2024 : 13,6 | démographie plus ancienne (fécondité plus haute) dans le rapport européen |
| Dette fin 2028 (% du PIB) | 125 | HCFP : ≈ 122 fin 2027, +2,5 points par an | cohérent |
| Intérêts 2029 (Md€) | 102 | HCFP : 79 en 2026, 91 en 2027, +12 par an | cohérent |
| Prélèvements sur les salaires (privé / public, Md€) | 516 / 202 (OpenFisca) | 519 / 208 (répartition calée sur l'Insee) | −0,6 % / −2,8 % |
| Prélèvements sur les pensions (Md€) | 51,2 (OpenFisca) | 51,2 | −0,1 % |
| TVA (Md€) | 91 % expliqués par source de revenu | 219 (répartition) | calage 1,10 |
| Reste des dépenses non identifiées | 106 Md€ (positif) | Sécurité sociale hors blocs, opérateurs | pas de double compte |
| Trajectoire | déficit primaire ≈ 2 %, dette qui monte | Cour des comptes (juin 2026) : il faut un excédent primaire pour réduire la dette | même diagnostic |

Non validé : dépenses de santé et de dépendance contre le rapport européen (tableau non lu) ; projection de long terme
de la Cour des comptes (non publiée sans mesures).

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
- **Recettes impôt par impôt, mais à barème constant** : pas d'effet du barème de l'impôt sur le revenu indexé sur
  les prix (convention), pas de recettes qui baissent avec la part des salaires ; la répartition entre impôts vient
  de la v235 (2024), à remplacer par OpenFisca et les comptes détaillés de l'Insee.
- **Pas encore validé contre les projections de long terme de la Commission européenne** (rapport sur le
  vieillissement) ni contre une projection de la Cour des comptes.

## Sources

- COR, Évolutions et perspectives des retraites en France, rapport annuel de juin 2026 (et synthèse).
- HCFP, avis n° 2026-5 relatif aux projets de lois de finances et de financement de la sécurité sociale pour 2027.
- Insee, Le compte des administrations publiques en 2025, Insee Première n° 2106 (mai 2026).
- Unédic, prévisions financières d'octobre 2026.
- DREES, comptes de la protection sociale (parts par risque, 2022, citées par l'iFRAP).
