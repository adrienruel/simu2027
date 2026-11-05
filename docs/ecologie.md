# Émissions et empreinte carbone (5 novembre 2026)

Code : `moteur/ecologie/emissions.py` ; paramètres : `parametres/commun/ecologie.yaml` ; option
`ecologie_options.emissions_activite` (v235 : non) ; tests : `tests/test_ecologie.py`. Conception d'ensemble (six
familles d'indicateurs) : `claude/Ecologie_indicateurs.md` (projet).

Décision d'Adrien du 05/11/2026 : la baisse des émissions dépend de l'activité économique, du progrès technique et de
la part de l'économie importée, au lieu d'un taux fixe (`carbone.baisse_tendancielle_emissions`, −1,9 % par an).

## Le modèle

**Émissions territoriales, par secteur** (Citepa, Secten 2026 : 359 Mt hors UTCATF en 2025) :

    émissions = émissions 2025 × population × (revenu par habitant)^élasticité × intensité

- élasticité au revenu par secteur (hypothèse) : industrie 1, énergie 0,7, transports 0,5, déchets 0,3, bâtiments
  0,2, agriculture 0 ;
- intensité : −2,2 % par an dans le prudent, soit −1,9 % par an d'émissions avec la croissance du prudent, le rythme
  de 2024-2025 ; crise −1,8 %, médian −2,5 %, optimiste −2,8 % ; prudent pour tous avant 2029 ;
- l'activité est celle du statu quo ou celle d'un programme (son PIB) : la différence est l'**effet de l'activité**,
  publié à part. Une récession baisse les émissions ; ce n'est pas une politique climatique.

**Empreinte** (SDES, 2024 : 563 Mt, dont 284 importées) = part domestique (279 Mt en 2024, suit les émissions
territoriales) + émissions importées (suivent le PIB, la part importée — stable dans le statu quo, commune à tous —
et l'intensité des pays fournisseurs, −1 % par an dans le prudent). Une **relocalisation** (`relocalisation_mt`)
retire des émissions importées et en ajoute moins à l'industrie (70 % dans le prudent).

**Réponse au prix du carbone** (transports et bâtiments, périmètre de l'ETS2) : facteur de long terme
(1 + 0,35 × (prix du programme / prix du statu quo − 1))^−0,6, atteint par ajustement partiel (35 % de l'écart
refermé chaque année, rapport court terme / long terme de la méta-analyse de Labandeira et al., 2017). Prix du
statu quo : composante carbone gelée (37 € de 2026) + ETS2 à partir de 2028 (54 €).

**Budgets carbone** : décret n° 2026-636 (SNBC-3) : 342 Mt par an en 2024-2028, 262 en 2029-2033, 194 en 2034-2038,
puis ligne droite jusqu'à 80 Mt en 2050 (hypothèse, SNBC-2).

## Une seule équation pour la recette et les émissions : erreur trouvée

La recette carbone d'Écologie de droite (`carbone.effet_solde`) faisait répondre l'assiette au prix **à partir du
prix de 2029** (269 €). Le saut depuis le prix du statu quo (≈ 90 €) jusqu'à 269 € n'érodait jamais l'assiette :
la recette statique de 2029 est calculée sur les volumes d'avant la réforme, et rien ne les faisait baisser
ensuite. Le budget comptait donc des tonnes que le programme faisait disparaître.

Avec l'option, l'assiette = recette statique × prix / prix de 2029 × réponse au prix (contre le statu quo, saut
compris, ajustement progressif) × émissions du statu quo (activité et progrès technique). La même réponse donne
l'effet physique du programme (`mesure_prix_carbone`, Mesure.physique). L'ETS2 perdu et le poids des taxes carbone
dans l'inflation suivent les mêmes émissions.

| Déficit publié (% du PIB) | 2029 | 2032 | 2037 | 2050 | 2073 |
|---|---|---|---|---|---|
| Prudent, avant | 3,21 | 3,57 | 3,01 | 3,08 | 2,67 |
| **Prudent, après** | **3,40** | **4,06** | **3,39** | **3,72** | **3,08** |
| Médian, avant / après | 3,00 / 3,00 | 3,01 / 3,01 | 2,08 / 2,68 | 0,31 / 0,40 | −7,26 / −7,50 |
| Optimiste, avant / après | 3,00 / 3,00 | 2,20 / 2,66 | 0,49 / 1,12 | −1,46 / −1,59 | −11,57 / −12,01 |
| Crise, avant / après | 3,22 / 3,41 | 4,64 / 5,14 | 4,75 / 5,52 | 7,65 / 9,84 | 43,3 / 57,1 |

Réponse au prix (facteur sur les émissions des transports et des bâtiments) : 0,90 en 2029, 0,82 en 2030, 0,65 en
2037, 0,54 en 2050. Le coût budgétaire est la contrepartie de l'effet climatique : environ 30 Mt de moins dès 2030
et 50 Mt à partir de 2037 (prudent), mais une assiette taxée plus étroite.

**Correction validée par Adrien le 05/11/2026** et fusionnée dans `main`. Restent des extrapolations à garder en
tête : l'élasticité de long terme (0,6) appliquée à des prix huit fois plus élevés que le statu quo en 2060, la
vitesse d'ajustement (0,35), le prix de l'ETS2 gardé constant.

Conséquence relevée par les tests : avec la recette corrigée, le déficit du prudent avant clause ne passe plus sous
3 %, si bien que la déduction de l'investissement reste à 50 % (la hausse conditionnée ne se déclenche pas). Un
levier qui fait passer le déficit sous 3 % la déclenche, et son coût peut l'emporter à long terme : l'effet des
leviers n'est plus monotone (`tests/test_leviers.py`, déduction figée pour isoler un levier).

## Tondelier : effets en tonnes (05/11/2026)

`programmes/tondelier/parametres.yaml`, groupe `tondelier_ecologie` : dix mesures, chacune estimée par scénario avec
sa méthode et ses sources (Anah, DGAC, évaluation du Deutschlandticket, ADEME pour le fonds chaleur, T&E pour les
voitures de fonction, SNCF pour le report modal, The Shift Project pour l'agriculture, RTE pour la sortie du
nucléaire). Profil commun : `moteur/ecologie/emissions.profil` (montée, extinction quand le statu quo rattrape la
mesure, réduction au rythme de la décarbonation du statu quo). Hypothèse de gaz fossile en secours pendant la sortie
du nucléaire (+4 Mt dans le prudent vers 2047) validée par Adrien.

## Comparateur

`outils/export_comparaison.py` écrit `sorties/comparaison_ecologie.csv` : émissions territoriales et empreinte
(totales et par habitant), émissions importées, statu quo, effet de l'activité, effet des mesures, plafond SNBC,
dépassement cumulé depuis 2029, émissions par secteur ; statut « simule ».

## Limites

- Intensité commune à tous les secteurs, faute de série sectorielle sourcée ; à remplacer par les tendances de
  Secten par secteur.
- Industrie et énergie (ETS1) : pas de réponse à un prix national ; agriculture : l'accise du programme a sa propre
  baisse des volumes (`tva.agriculture.baisse_volumes`), non reliée aux émissions.
- Puits de carbone, sols, énergie importée, air, investissement climat : étapes suivantes (`claude/Ecologie_indicateurs.md`).
- La population par habitant est celle du statu quo (l'effet d'un programme sur les naissances n'y est pas).

## Investissements du fonds et mesures oubliées (05/11/2026, question d'Adrien)

Les investissements du fonds d'Écologie de droite dans l'énergie et l'industrie verte n'avaient pas d'effet sur les
émissions. Ajoutés (`ecologie_fonds`), avec une règle commune aux deux programmes : seul l'investissement en plus du
statu quo réduit les émissions.

- **Décarbonation de l'industrie** (3 Md€ par an contre 1,1 investi en 2024, I4CE) : 0,42 t évitée par an pour
  1 000 € investis (fonds chaleur, ADEME), part additionnelle 25 % dans le prudent ; −4 Mt en 2048.
- **Renouvelables et réseaux de chaleur** (3,4 Md€, un quart de l'existant) : le fonds remplace surtout un financement
  privé ; zéro dans le prudent, −7 Mt en médian.
- **Régénération ferroviaire** (+1,5 Md€) : même rendement par milliard que la mesure ferroviaire de Tondelier.
- **EPR2, RTE, Enedis** : prévus dans le statu quo et financés par EDF ou les tarifs ; le fonds change qui paie, pas
  les émissions. Pas d'effet compté.

Tondelier, mesures qui manquaient : **Fonds vert** renforcé (rénovation des bâtiments publics ; zéro dans le prudent
faute de tonnes publiées) et **plan vélo** (Cnam et al., 2025 : 250 000 t de potentiel). Non chiffrés faute de
montant : fonds souverain « livret industrie » et « France Verte 2040 ». Biodiversité (1 Md€) : effet sur les puits de
carbone, pas encore modélisé.

Recouvrement possible chez Écologie de droite : le prix du carbone et la régénération ferroviaire poussent tous deux
au report modal ; l'effet du rail est faible au regard du prix (−0,6 contre environ −30 Mt).

## Correction de la réponse au prix (05/11/2026, question d'Adrien : « les gains du prix carbone paraissent très élevés »)

Erreur trouvée : la réponse au prix appliquait la part de l'accise au prix du programme (35 %, paramètre de
`carbone.py`, valable pour une hausse à partir du prix de 2029) à l'écart avec le prix du statu quo. La hausse du prix
de l'essence était ainsi triplée : +86 % au lieu de +28 % en 2030, +277 % au lieu de +90 % en 2060.

Corrigé : hausse du prix final = (prix du programme − prix du statu quo) × contenu carbone de la dépense d'énergie
(1,3 kg de CO2 par euro : essence et gazole ≈ 2,3 à 2,6 kg par litre à ≈ 1,8 €). Facteur sur les émissions des
transports et des bâtiments : 0,92 en 2030, 0,83 en 2037, 0,75 en 2050, 0,69 en 2060 (avant : 0,82 ; 0,65 ; 0,54 ;
0,45). Repère : la taxe carbone suédoise (≈ 120 € par tonne) a baissé les émissions des transports d'environ 11 %
(Andersson, 2019) ; ici, 225 € d'écart en 2030 donnent −8 % la première année et −14 % à long terme.

La recette carbone suit la même équation : son érosion est moins forte, le déficit s'améliore (voir le journal).

## Empreinte : accise sur le contenu carbone des importations (05/11/2026, question d'Adrien)

Constat : chez Écologie de droite, les émissions territoriales sont plus basses, mais l'empreinte par habitant pouvait
être plus haute que chez Tondelier ou le statu quo (médian, optimiste). Deux raisons :

1. le PIB est plus élevé (+3 % en 2050 dans le prudent) : plus de consommation, donc plus d'importations ; les
   émissions importées suivent le PIB. Effet réel, qui joue contre le programme ;
2. l'accise sur le contenu carbone des importations était comptée en recette (`carbone._importe`) mais pas en
   émissions. Ajouté (`mesure_carbone_importe`, clé physique `importees_mt`) avec la même réponse que la recette,
   appliquée à 60 % des émissions importées (biens manufacturés et véhicules, hypothèse) : −5,5 Mt en 2030, −6,7 en
   2037, −9,2 en 2050 dans le prudent. La substitution vers des biens français ou européens n'est pas comptée.

L'effet de l'activité sur l'empreinte (via les importations) n'est pas encore séparé de l'effet des mesures dans le
comparateur ; seul l'effet sur les émissions territoriales l'est.

## Importations : elles suivent la consommation des ménages (05/11/2026, décision d'Adrien)

Les émissions importées suivaient le PIB. Elles suivent désormais la consommation des ménages : écart de PIB avec le
statu quo, moins ce qui ne va pas à la consommation (contexte `pib_hors_consommation`, commun à tous les programmes).
Écologie de droite : la valeur ajoutée du capital du fonds (rendement net gardé sur les comptes et usure réinvestie)
n'est pas consommée ; ses retombées sur le reste de l'économie le sont. Tondelier : son écart de PIB (multiplicateur)
est compté en entier comme consommation, faute de décomposition ; sa part d'investissement public le surestime un peu.
Les émissions territoriales, elles, suivent toujours le PIB (la production émet, qu'elle soit consommée ou investie).
