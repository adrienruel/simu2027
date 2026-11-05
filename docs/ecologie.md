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
