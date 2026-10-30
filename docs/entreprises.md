# Entreprises par taille (30 octobre 2026)

`moteur/entreprises_cellules.py`, données `parametres/donnees/entreprises_tailles.csv`, paramètres
`entreprises_cellules.*`, tests `tests/test_entreprises_cellules.py`. Demande d'Adrien : le comportement des
entreprises, comme les cellules de ménages. Première étape : quatre tailles (TPE, PME, ETI, GE).

## Données

| Taille | Entreprises à l'IS | Bénéfices | IS brut | Salariés (ETP) | Valeur ajoutée | Investissement / VA | Impôts de production / VA |
|---|---|---|---|---|---|---|---|
| TPE | 2 489 000 | 65,9 Md€ | 14,0 Md€ | 2,41 M | 186 Md€ | 26,3 % | 1,0 % (hypothèse) |
| PME | 221 000 | 78,5 | 19,2 | 3,99 M | 277 | 15,2 % | 1,9 % |
| ETI | 9 000 | 64,5 | 16,2 | 3,46 M | 307 | 19,8 % | 2,9 % |
| GE | 400 | 75,0 | 19,6 | 3,98 M | 409 | 23,7 % | 3,4 % |

Sources : DGFiP, L'impôt sur le bénéfice 2024 des entreprises (Statistiques n° 39, 2025), tableau 2 ; Insee, Les
entreprises en France, catégories d'entreprises, Ésane 2021 (secteurs principalement marchands, catégories
MIC/PME/ETI/GE) ; DGFiP, Les impôts de production en 2023 (Statistiques n° 35, 2025) : poids des impôts d'origine
fiscale dans la valeur ajoutée (« très faible » pour les microentreprises).

## Ce que le module change

1. **Impôts de production des entreprises déficitaires.** Le budget statique ajoutait les 75 Md€ d'impôts de
   production supprimés (hors secteur non marchand) au bénéfice imposable des seules entreprises bénéficiaires.
   Une part est payée par des entreprises déficitaires (20 % dans le prudent, hypothèse : 36 % des entreprises à
   l'IS sont déficitaires, surtout petites) ; sa suppression réduit leurs pertes et n'est imposée que plus tard,
   quand les déficits reportés sont imputés (31 % : 35 Md€ imputés pour 112 Md€ de déficits par an, DGFiP).
   Base de l'IS nouveau : −13,8 % des impôts de production ajoutés ; IS de l'État −4,2 Md€ par an.
2. **Qui paie.** Bilan statique, avant la déduction immédiate de l'investissement et avant les réactions :

| Md€ de 2026 | IS actuel | Impôts de production | Total actuel | IS nouveau (45 %) | Écart |
|---|---|---|---|---|---|
| TPE | 14,6 | 4,7 | 19,2 | 33,2 | +14,0 (+73 %) |
| PME | 20,0 | 13,2 | 33,2 | 42,5 | +9,3 (+28 %) |
| ETI | 16,8 | 22,4 | 39,2 | 39,4 | +0,2 (0 %) |
| GE | 20,4 | 35,0 | 55,4 | 49,3 | −6,1 (−11 %) |

   Le programme déplace l'impôt des grandes entreprises vers les petites : les TPE passent du taux réduit de 15 %
   à 45 % et payaient peu d'impôts de production.

   Avec la déduction immédiate de l'investissement (au prorata de l'investissement de chaque taille) et la fin de
   la déduction des intérêts (au prorata de la valeur ajoutée, faute de données sur la dette par taille), à la
   taille de l'économie de 2029 :

| Md€ | Écart avant déduction | Déduction 2037 | Intérêts 2037 | Écart net 2037 | Écart net 2073 |
|---|---|---|---|---|---|
| TPE | +13,9 | −4,5 | +1,4 | +10,9 (+57 %) | +12,1 (+63 %) |
| PME | +9,3 | −3,9 | +2,1 | +7,5 (+23 %) | +8,6 (+26 %) |
| ETI | +0,1 | −5,6 | +2,3 | −3,1 (−8 %) | −1,5 (−4 %) |
| GE | −6,1 | −8,9 | +3,1 | −11,9 (−21 %) | −9,4 (−17 %) |
| Total | +17,2 | −22,9 | +8,9 | +3,4 | +9,9 |

   La déduction n'est qu'un avantage de trésorerie (déduire plus tôt ce qui aurait été amorti) : elle pèse le plus
   pendant la montée (2032-2037), puis surtout l'effet de la croissance. Elle profite d'abord aux grandes
   entreprises, qui investissent le plus.

   **Le fonds comme aide à l'appareil productif** (demandes d'Adrien) : le capital nouveau du fonds finance les
   entreprises à 3,2 % réel (rendement de son capital dans le prudent) au lieu d'environ 5,3 % sur le marché
   (moitié fonds propres à 8,6 % réel, Banque de France ; moitié dette à 2 %, hypothèse). L'écart joue comme une
   aide, payée par les épargnants (rendement plus bas), pas par l'État.

   **Stratégie d'investissement du fonds** (DÉCISION d'Adrien : celle qui réduit le plus le chômage, donc le RUI,
   et augmente les impôts) : le fonds investit d'abord là où un euro de capital fait le plus d'emplois, c'est-à-
   dire là où il y a le moins de capital par salarié (immobilisations corporelles par ETP, Insee Ésane 2021 : PME
   108 k€, TPE 134 k€, ETI 222 k€, GE 363 k€), jusqu'à 25 % du capital de chaque taille (capacité d'absorption,
   hypothèse), puis passe à la suivante.

   **Effet sur le chômage** : le chômage d'équilibre baisse quand le ratio capital/production monte (seule
   estimation : −0,46 % de chômage pour +1 % de capital/production, États-Unis 1964-2003, Arestis, Baddeley et
   Sawyer ; aucun effet à long terme selon Layard et Nickell avec une fonction Cobb-Douglas, un effet si la
   substitution capital-travail est faible, ce que trouvent la plupart des estimations selon Rowthorn). Crise 0,
   prudent la moitié (0,23), médian et optimiste 0,46. Le capital est pondéré par l'intensité en emploi des
   entreprises où il va. Chaque emploi rapporte au budget comme un emploi au SMIC (RUI économisé, impôt, TVA).

| Emplois du capital du fonds | 2037 | 2050 | 2073 |
|---|---|---|---|
| Prudent, stratégie emploi | 17 000 | 68 000 | 104 000 |
| Prudent, au prorata de l'investissement | 10 000 | 45 000 | 116 000 |
| Médian, stratégie emploi | 96 000 | 187 000 | 210 000 |
| Optimiste, stratégie emploi | 133 000 | 201 000 | 262 000 |

   La stratégie emploi fait plus d'emplois tant que le fonds est petit ; en 2073, les plafonds de 25 % sont
   atteints (PME, TPE) et le reste va aux ETI et aux grandes entreprises, d'où un peu moins d'emplois que la
   répartition au prorata de l'investissement, qui dépasse ces plafonds (47 % du capital des TPE).

| Md€ (économie de 2029) | Capital du fonds 2037 | Avantage 2037 | Écart avec le fonds 2037 | Capital 2073 | Avantage 2073 | Écart avec le fonds 2073 |
|---|---|---|---|---|---|---|
| TPE | 0 | 0 | +10,9 (+57 %) | 97 | 2,0 | +10,1 (+53 %) |
| PME | 58 | 1,2 | +6,3 (+19 %) | 129 | 2,7 | +5,9 (+18 %) |
| ETI | 0 | 0 | −3,1 (−8 %) | 231 | 4,8 | −6,4 (−16 %) |
| GE | 0 | 0 | −11,9 (−21 %) | 434 | 9,1 | −18,5 (−33 %) |

| Sans règle / publié, chômage | 2037 | 2050 | 2073 |
|---|---|---|---|
| Prudent | 4,68 / 3,00 ; 7,32 % | 4,08 / 3,04 ; 7,22 % | 0,03 / 0,03 ; 7,08 % |
| Médian | 2,58 / 2,34 ; 6,08 % | −0,39 / −0,33 ; 5,88 % | −8,12 ; 5,74 % |
| Optimiste | 0,77 / 0,54 ; 4,60 % | −2,64 / −2,58 ; 4,57 % | −10,20 ; 4,40 % |
| Crise | 5,30 / 3,58 ; 8,28 % | 4,70 / 3,64 ; 8,22 % | 6,23 / 5,10 ; 8,10 % |

   **Correction trouvée en faisant ce tableau** (`is_investissement.assiette_locale`) : l'IS local (5 %) a la même
   assiette que l'IS de l'État, mais la déduction de l'investissement et la fin de la déduction des intérêts ne
   jouaient que sur l'IS de l'État (40 %). Elles jouent désormais sur les 45 % : coût net de la déduction +12,5 %.
3. **Investissement par taille.** Chaque taille a son taux marginal actuel (TPE 19 %, mélange du taux réduit et du
   taux normal ; autres 25 %), sa part d'impôts de production sur le capital (relative à la moyenne) et sa
   réaction : les petites entreprises réagissent 95 % plus que les grandes (Zwick et Mahon, AER 2017 ; PME et ETI
   interpolées), l'élasticité moyenne restant celle du module macro. Effet : le canal reste petit (la déduction
   compense le taux), un peu plus défavorable (−0,3 Md€ en 2037 dans le prudent, contre −0,2).

4. **Dirigeants qui se versent un salaire** (`entreprises_cellules.arbitrage_tpe`, demande d'Adrien). Avec l'IS à
   45 % (63 % avec la flat tax sur la part distribuée), un dirigeant peu payé a intérêt à se verser davantage de
   salaire : barème de 0 % jusqu'à 12 500 €, 17,9 % jusqu'à 24 000 €, 57 % jusqu'à 32 000 €. Pour chaque classe
   de bénéfice des petites sociétés (jusqu'à 150 000 €, 1,5 million de sociétés) et chaque niveau de rémunération
   actuelle du dirigeant (déciles des indépendants classiques, Insee), le modèle cherche le salaire qui minimise
   l'impôt total. Sociétés avec un dirigeant actif : 69 % (hors sociétés immobilières et holdings, DGFiP).
   Hypothèses : part du bénéfice gardé qui serait distribuée (75 % dans le prudent) ; part des dirigeants qui font
   l'arbitrage (75 % dans le prudent, 100 % en crise, 25 % en optimiste).

| Par an, à plein effet | Crise | Prudent | Médian | Optimiste |
|---|---|---|---|---|
| Bénéfice passé en salaire | 3,1 Md€ | 2,4 Md€ | 1,6 Md€ | 0,8 Md€ |
| Recettes perdues | 1,3 Md€ | 0,9 Md€ | 0,5 Md€ | 0,3 Md€ |

   L'effet est limité : les dirigeants déjà payés plus de 32 000 € (la moitié) n'y gagnent rien (66 % au barème),
   et les petites sociétés ont de petits bénéfices.

## Effet sur les résultats

| Sans règle / publié | 2029 | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|---|
| Prudent avant | 4,76 / 3,00 | 4,34 / 3,00 | 3,83 / 3,00 | −0,84 / −0,84 | 95 % |
| Prudent après | 4,90 / 3,01 | 4,59 / 3,00 | 4,08 / 3,03 | −0,16 / −0,16 | 104 % |
| Crise après | 4,97 / 3,09 | 5,18 / 3,48 | 4,56 / 3,49 | 5,80 / 4,67 | 157 % |
| Prudent avec les salaires des dirigeants | 4,91 / 3,03 | 4,63 / 3,00 | 4,07 / 3,02 | −0,02 / −0,02 | 105 % |
| Crise avec les salaires des dirigeants | 4,99 / 3,11 | 5,24 / 3,55 | 4,67 / 3,60 | 6,14 / 5,01 | 159 % |
| Prudent avec la déduction sur l'IS local | 4,93 / 3,04 | 4,69 / 3,00 | 4,12 / 3,08 | 0,18 / 0,18 | 108 % |
| Crise avec la déduction sur l'IS local | 5,01 / 3,12 | 5,30 / 3,58 | 4,70 / 3,64 | 6,23 / 5,10 | 160 % |

En 2029, la règle est au maximum dans le prudent (5 points d'épargne pris, RUI baissé de 148 € par mois jusqu'au
plancher) et ne suffit plus tout à fait (3,01 %).

## Ce qui manque (étapes suivantes)

- **Passage à l'impôt sur le revenu** (entreprise individuelle) : proche de l'arbitrage par le salaire, non
  compté à part.
- **Secteurs** (industrie, commerce, construction, services) : impôts de production très inégaux (industrie
  16 %, commerce et transports 18 %).
- **Démographie des entreprises** : créations, défaillances, passage de PME à ETI.
- **Incidence** : part des impôts répercutée sur les salaires et les prix (Fuest, Peichl et Siegloch, 2018 :
  environ la moitié de l'impôt local sur les entreprises retombe sur les salaires).
- **Localisation et transfert de bénéfices** par taille (aujourd'hui en agrégat, part des grandes entreprises).
