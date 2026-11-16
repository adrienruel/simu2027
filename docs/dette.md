# Dynamique de la dette : décomposition du déficit et variantes communes (phase 3.1)

16 novembre 2026. Code : `moteur/decomposition.py`, `outils/variantes_dette.py` ; sorties :
`sorties/comparaison_decomposition.csv` et `sorties/comparaison_variantes_dette.csv` ; tests :
`tests/test_decomposition.py`.

## Ce que mesure la décomposition

Chaque année, le déficit au sens de Maastricht est la somme du déficit primaire et des intérêts : taux apparent
nominal × dette du début d'année, rapportés au PIB. Le noyau publie désormais les cinq composantes du taux apparent
(`taux_base`, `taux_fisher`, `taux_bce`, `taux_prime`, `taux_scenario`) et la dette du début d'année
(`dette_debut`). Un écart de déficit entre deux comptes se coupe alors exactement en six parts :

| Part | Contenu |
|---|---|
| primaire | déficit primaire (recettes − dépenses hors intérêts) |
| taux | taux de base (du taux apparent de 2029 vers le taux long), effet de Fisher, BCE, écart du scénario de crise |
| prime_dette | prime liée à la dette et baisse d'écart gagnée par un programme |
| accumulation_dette | dette en plus, à taux donné |
| croissance | même dette, PIB différent |
| autres | intérêts hors taux apparent (nuls pour les programmes publiés) |

Le résidu est nul à 10⁻⁹ près (test). Deux lectures sont publiées : `depuis_2029` (comment le déficit d'une
trajectoire dérive) et `ecart_statu_quo` (d'où vient l'écart d'un programme au statu quo la même année).

## Le statu quo dérive surtout par les intérêts

Statu quo, hausse du déficit depuis 2029 (points de PIB) :

| Scénario, année | Total | Primaire | Taux | Prime de dette | Dette en plus | Croissance |
|---|---|---|---|---|---|---|
| Prudent 2037 | +3,59 | +0,11 | +1,84 | +0,53 | +1,38 | −0,27 |
| Prudent 2050 | +14,66 | +0,88 | +2,58 | +4,72 | +7,20 | −0,72 |
| Médian 2037 | +2,54 | −0,35 | +1,85 | +0,26 | +1,20 | −0,42 |
| Médian 2050 | +7,28 | −0,45 | +2,38 | +1,84 | +4,46 | −0,95 |

Le déficit primaire du statu quo bouge peu : la dérive vient du taux apparent qui rejoint le taux de marché (4 %),
puis de la boule de neige (dette en plus et prime). D'où le classement sur l'écart de solde primaire (phase 1.1) et
la prudence sur les niveaux d'après 2037.

## Variantes communes : le classement tient, les niveaux bougent

Trois variantes, appliquées au statu quo comme aux programmes : sans prime de dette, taux long à 3,3 % au lieu de
4 %, et 2027-2028 projetées avec la croissance de la Banque de France (0,9 % puis 1,2 %, projections du
15/09/2026 ; variante de la décision D3).

Déficit en 2037 au prudent, et écart au statu quo (points de PIB) :

| Programme | Calcul publié | Sans prime de dette | Taux long 3,3 % | 2027-2028 projetées |
|---|---|---|---|---|
| Statu quo | 9,50 | 8,86 | 8,18 | 9,38 |
| Bertrand | 9,51 (+0,00) | 8,84 (−0,02) | 8,17 (−0,00) | 9,38 (+0,00) |
| Retailleau | 10,20 (+0,70) | 9,44 (+0,58) | 8,84 (+0,66) | 10,07 (+0,70) |
| Philippe | 11,15 (+1,64) | 10,25 (+1,39) | 9,74 (+1,56) | 11,02 (+1,64) |
| Attal | 11,27 (+1,77) | 10,37 (+1,51) | 9,86 (+1,68) | 11,14 (+1,76) |
| Le Pen (partiel) | 13,23 (+3,73) | 11,98 (+3,12) | 11,73 (+3,55) | 13,10 (+3,72) |
| Tondelier | 13,32 (+3,81) | 12,40 (+3,54) | 11,88 (+3,71) | 13,19 (+3,81) |
| Glucksmann | 13,41 (+3,90) | 12,35 (+3,50) | 11,94 (+3,76) | 13,27 (+3,90) |
| Zemmour | 13,65 (+4,14) | 12,17 (+3,31) | 12,08 (+3,91) | 13,50 (+4,12) |
| Lisnard | 14,14 (+4,64) | 12,81 (+3,95) | 12,60 (+4,43) | 14,01 (+4,63) |
| Arthaud (partiel) | 16,82 (+7,32) | 14,85 (+5,99) | 15,14 (+6,97) | 16,66 (+7,28) |
| Mélenchon | 28,04 (+18,54) | 24,57 (+15,71) | 26,00 (+17,82) | 27,88 (+18,50) |
| Roussel | 30,06 (+20,55) | 23,59 (+14,73) | 27,59 (+19,41) | 29,87 (+20,49) |

Lecture :
- Le taux long à 3,3 % baisse tous les déficits d'environ 1,3 point en 2037, et les écarts au statu quo de 0 à
  1,1 point : l'ordre des programmes ne change pas.
- Sans prime de dette, les écarts des programmes les plus déficitaires baissent le plus (Roussel −5,8 points,
  Mélenchon −2,8) : l'écart de Roussel passe sous celui de Mélenchon, et celui de Zemmour sous ceux de Glucksmann
  et de Tondelier. La prime
  amplifie les écarts sans changer le groupe de tête.
- Projeter 2027-2028 avec la croissance (D3, option b approchée : la dette de fin 2028 rapportée à une économie
  qui a grandi de 2,1 %) ne change presque rien aux écarts (au plus 0,06 point) et baisse les niveaux de
  0,1 à 0,2 point en 2037.

## Décision D3 : ce qui est codé

`calendrier.croissance_2027_2028` vaut 0 par défaut : la convention publiée (économie de 2026 placée en 2029)
ne change pas tant qu'Adrien n'a pas tranché. La variante est approchée : seule la dette de départ est rapportée
à l'économie de 2028, les flux du statu quo restent ceux de l'économie de 2026. Une option (b) complète
demanderait de projeter aussi recettes et dépenses de 2027-2028 ; vu l'effet sur les écarts (au plus
0,06 point), ce n'est pas prioritaire.
