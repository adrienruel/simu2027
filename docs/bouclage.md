# Phase E : macro bouclée (14 novembre 2026)

`moteur/bouclage.py`, paramètres `bouclage.*` (`parametres/commun/economie.yaml`), option `macro.bouclage`
(`parametres/commun/options.yaml`, vrai ; décisions d'Adrien du 14/11/2026). Tests :
`tests/test_bouclage.py`. Outils : `outils/calibrer_bouclage.py` (calage), `outils/banc_mesange.py` (critère de
sortie), `outils/comparer_bouclage.py` (effet sur les 14 trajectoires).

## Ce qui change

Avant : l'impulsion budgétaire d'une année agissait en entier cette année-là (multiplicateur du scénario), puis
s'éteignait linéairement en 3 à 5 ans (`macro.annees_effet_ajustement`). L'inflation des programmes était celle du
statu quo (sauf Écologie de droite, avec une courbe de Phillips propre à son effort de 2029), et les taux ne
réagissaient qu'à la dette.

Après : une forme réduite annuelle, commune à tous les programmes, calée sur Mésange 2017 :

| Bloc | Équation | Paramètres |
|---|---|---|
| E1 demande | x_t = a·g_t + b·x_{t−1} − c·q_{t−1} − z_t | a 0,86 ; b 0,29 ; c 0,27 |
| E2 prix | π_t = κ·(x_t − φ·g_t) ; q_t = q_{t−1} + π_t | κ 0,35 ; φ 0,19 |
| E2 prix par les coûts | baisse du coût du travail : prix −1,4 % à long terme par point de PIB | vitesse 0,25 |
| E3 taux | r_t = w·((φπ − 1)·π_{t−1} + φy·x_{t−1}) ; z_t = μ·z_{t−1} + σ·r_t | w 0,194 ; φπ 1,5 ; φy 0,5 ; σ 0,27 ; μ 0,84 |
| E4 (partiel) | la compétitivité-prix (q) ramène le PIB vers l'offre | c |

x : écart de production dû au programme ; g : impulsion de demande pondérée par instrument (`offre.impulsion`) ; q :
prix relatifs à l'étranger ; r : taux réel de la zone ; w : poids de la France dans la zone euro.

**Échelle par scénario.** `macro.multiplicateur` devient l'effet **maximal** d'un point de PIB de dépense (atteint la
deuxième année), au lieu de l'effet de la première année : crise 1,3, prudent et médian 1 (CAE ; Mésange 1,06), optimiste
0,5. Le sens compte comme avant (relance : scénario miroir), et la contrainte de capacité (`capacite.*`) joue toujours.

**Ce que reçoit le noyau** (deux clés de contexte nouvelles) : l'inflation du programme (statu quo + π) ;
`inflation_taux`, l'inflation que suivent les taux (statu quo + w·π : en union monétaire, les taux suivent l'inflation
de la zone) ; `taux_marche`, la hausse due à la BCE au-delà de Fisher, rejointe par le taux apparent au rythme du
renouvellement de la dette. Conséquence : une hausse des prix propre à la France allège la dette réelle, une
désinflation l'alourdit.

**Remplacé** : la courbe de Phillips d'Écologie de droite sur son effort de 2029 (`inflation.serie`), devenue un double
compte ; la forme linéaire du multiplicateur, de la production des postes publics (A3) et de l'effet récessif de la
clause d'Écologie de droite (`mult_clause`), qui prennent la forme bouclée.

**Recalé** : poids de demande du coût du travail (`demande.poids.cout_travail`) 0,4 → 0,13 (voir le banc).

## Calage (outils/calibrer_bouclage.py)

Cibles : variantes analytiques de Mésange 2017, à taux réels et change nominal constants (Bardaji et al., Insee
G2017/04, p. 100). Moindres carrés sur la dépense publique générique (PIB et prix, 1 à 10 ans et long terme, p. 105) et
la hausse de 100 points de base des taux réels (PIB, 1 à 5 ans, p. 134).

| Années | 1 | 2 | 3 | 5 | 10 | LT |
|---|---|---|---|---|---|---|
| PIB, Mésange | 0,78 | 1,06 | 1,03 | 0,86 | 0,53 | 0,16 |
| PIB, forme calée | 0,86 | 1,05 | 1,02 | 0,83 | 0,48 | 0,19 |
| Prix, Mésange | 0,20 | 0,58 | 0,94 | 1,42 | 1,88 | 2,69 |
| Prix, forme calée | 0,24 | 0,54 | 0,83 | 1,32 | 2,05 | 2,65 |
| Taux +100 pb, Mésange | −0,17 | −0,60 | −0,78 | −1,00 | | |
| Taux +100 pb, forme calée | −0,27 | −0,55 | −0,77 | −1,01 | | |

## Critère de sortie (outils/banc_mesange.py)

Variantes passées par le pipeline commun (demande bouclée + canal d'offre), scénario médian, BCE coupée comme dans
Mésange. Écart relatif au PIB de Mésange :

| Variante | 1 an | 2 ans | 3 ans | 5 ans | 10 ans |
|---|---|---|---|---|---|
| Dépense publique +1 point de PIB | +5 % | −6 % | −6 % | −7 % | −7 % |
| Investissement public +1 point | **−35 %** | −23 % | −13 % | 0 % | +25 % |
| Cotisations employeurs −1 point | +28 % | −25 % | −30 % | −26 % | −19 % |
| Choc pétrolier (+10 $ le baril) | −34 % | +22 % | −17 % | −5 % | +5 % |

- Dépense : retrouvée à 7 % près.
- Investissement public : manqué la première année (0,86 contre 1,31). Dans Mésange, l'investissement a un effet
  d'impact plus fort (moins d'importations) ; le moteur n'a qu'une forme de demande. Reste de E4 : contenu en
  importations par instrument.
- Cotisations : avec l'ancien poids de demande (0,4), +140 % la première année : le canal d'offre, calé sur Mésange,
  porte déjà l'effet de compétitivité, et l'entreprise garde d'abord la baisse en marge. Poids ramené à 0,13 (dans la
  fourchette de Kilponen et al., 0,04 à 0,51) : les cinq horizons passent, de justesse à 3 ans (−29,6 %). Prix : −0,32
  / −0,55 / −0,71 / −0,91 / −1,09, contre −0,36 / −0,70 / −0,87 / −1,09 / −1,32 dans Mésange (même signe ; avant : en
  hausse, par la demande seule).

## Suite du 14/11 (après « go ») : décisions appliquées, trois canaux de plus

Décisions d'Adrien (14/11, 11 h 28) : les cinq propositions validées telles quelles (bouclage actif, multiplicateur
= effet maximal, poids du coût du travail 0,13, BCE active, part de long terme de Mésange).

- **E1, prime de dette → demande** (`moteur/noyau.trajectoire`) : l'écart du taux de marché de l'État au statu quo
  (prime de dette, écart propre au programme, BCE) passe aux taux des crédits (`bouclage.prime_demande` : crise 0,5,
  prudent 0,35, médian 0,25, optimiste 0,15 ; miroir quand le taux est plus bas), puis au PIB par la variante de taux
  de Mésange ; recettes au taux du statu quo, chômage par la loi d'Okun, plancher du chômage commun. Le statu quo est
  le repère (son propre emballement ne pèse pas sur son PIB). Publié : `pib_taux`, `ecart_marche`. Option
  `macro.bouclage_prime_demande`.
- **E2, pensions en retard sur les prix** : revalorisées en janvier sur l'inflation passée, les pensions perdent
  l'inflation due au programme l'année où elle survient (−dπ_t × bloc retraites). Commun à tous les programmes, dans le
  noyau. Publié : `erosion_pensions`.
- **E4, balance commerciale** publiée (`balance_commerciale`, points de PIB, écart au statu quo) : −0,31 × écart de PIB
  (%) − 0,29 × écart de prix (%), calée sur Mésange ; retrouve ses trois variantes à 0,08 point près. Exemple 2037 au
  prudent : Mélenchon −4,7 points, Tondelier −0,9, Écologie de droite +0,5.
- **E4, facture énergétique** (suite, 14/11 après-midi) : les tonnes de CO2 fossile que les mesures déclarent
  (`Mesure.physique`, transports, bâtiments, industrie, énergie) changent les importations de pétrole et de gaz, à
  0,213 Md€ par Mt (57 Md€ de facture fossile, SDES, pour 267 Mt, Citepa). Ce revenu payé à l'étranger (ou gardé)
  entre dans la demande au poids 0,46, calé sur la variante pétrole de Mésange, et dans la balance commerciale. La
  réponse au prix du carbone n'y entre pas (déjà dans l'impulsion de la taxe). 2037 au prudent : Écologie de droite
  −1,5 Md€ de facture, Tondelier −1,5, Mélenchon −1,5, Zemmour +1,6 ; effet sur le déficit ≤ 0,02 point. Publié :
  `facture_energie`.
- **Choc pétrolier au banc** : revenu perdu (poids 0,46) + énergie plus chère pour les entreprises (perte d'offre de
  0,83 point de PIB par point de facture, vitesse 0,35) : −0,13 / −0,19 / −0,21 / −0,22 / −0,21 contre −0,10 / −0,24 /
  −0,18 / −0,21 / −0,22 dans Mésange ; 30 % près à partir de la deuxième année (première : −34 %).

## E5 : stock de capital commun (14/11, après-midi)

`moteur/capital.py`, option `macro.capital_commun`, tests `tests/test_capital.py`.

Constat : deux mécaniques chiffraient le même effet (impôt sur les entreprises → investissement → PIB). Le canal
d'offre commun faisait PIB × part du capital (0,35) × capital en plus ; les cohortes d'entreprises d'Écologie de droite,
un stock de capital avec usure (10 %), dont chaque euro produit son rendement net plus son usure (0,132 en prudent).
Pour le même capital en plus, le premier comptait 2,2 fois plus : la part du capital s'applique à la valeur ajoutée
des sociétés (1 545 Md€), pas à tout le PIB. Contrôle sur les comptes : taux de marge des SNF (32,2 %) × valeur
ajoutée / capital des SNF (365 / 0,10 ≈ 3 650 Md€) ≈ 0,14 par euro, comme la mécanique d'Écologie de droite.

Désormais commun : investissement en plus = − élasticité au coût du capital × variation du coût (montée en
`macro.montee_invest` ans) × investissement des SNF ; capital accumulé avec usure ; PIB = capital × (rendement net +
usure). Une baisse d'IS d'un point de PIB donne +0,18 % de PIB à long terme (+0,41 % avant). Contrôle : la baisse
de l'IS de 33,3 à 25 % (coût du capital −3,8 %, élasticité de Mésange) donne ≈ +0,25 % de PIB. Écologie de droite
garde ses cohortes par taille, qui suivent déjà cette mécanique. Les taux d'intérêt ne passent pas par ce module :
leur effet, capital compris, est dans la variante de taux de Mésange (rétroaction du noyau).

Effet sur le déficit 2037 au prudent : Lisnard +0,08 point, Philippe +0,04, Le Pen +0,04, Retailleau +0,02 (leurs
baisses d'impôt sur les entreprises rapportent moins) ; Mélenchon −0,06, Tondelier −0,04 (leurs hausses coûtent
moins) ; Écologie de droite inchangée.

## Effet sur les programmes (déficit, % du PIB, prudent : main au commit 7c511dc → phase E complète)

| Programme | 2032 | 2037 | 2050 |
|---|---|---|---|
| Statu quo | 7,16 → 7,16 | 9,50 → 9,50 | 20,57 → 20,57 |
| Écologie de droite | 4,16 → 4,54 | 4,15 → 4,61 | 4,89 → 5,64 |
| Bertrand | 7,09 → 7,09 | 9,28 → 9,33 | 20,24 → 20,37 |
| Retailleau | 7,73 → 7,72 | 10,46 → 10,41 | 24,29 → 24,27 |
| Philippe | 8,34 → 8,30 | 11,25 → 11,26 | 26,92 → 27,13 |
| Attal | 8,66 → 8,43 | 11,54 → 11,37 | 26,82 → 26,35 |
| Tondelier | 9,63 → 9,00 | 13,98 → 12,76 | 33,85 → 30,61 |
| Le Pen | 9,99 → 9,62 | 13,71 → 13,33 | 33,47 → 32,50 |
| Glucksmann | 10,23 → 9,55 | 14,44 → 13,38 | 34,18 → 31,53 |
| Zemmour | 10,52 → 10,26 | 13,99 → 14,00 | 35,11 → 34,94 |
| Lisnard | 10,90 → 10,71 | 14,73 → 14,61 | 37,23 → 36,91 |
| Arthaud | 12,56 → 11,89 | 18,44 → 16,95 | 45,43 → 41,53 |
| Mélenchon | 19,40 → 18,62 | 29,63 → 27,27 | 71,35 → 65,33 |
| Roussel | 17,50 → 17,19 | 30,82 → 29,85 | 84,22 → 79,88 |

Lecture : l'effet d'une impulsion dure plus longtemps (Mésange : encore 0,53 au bout de dix ans, contre zéro après
4,5 ans dans l'ancienne forme). Les relances y gagnent, la consolidation d'Écologie de droite y perd (+0,5 point en
2037). La prime de dette en reprend une partie aux programmes très endettés (Mélenchon 2037 : 26,90 → 27,82 avec ce
canal), et rend un peu à ceux dont la dette baisse ; les pensions en retard sur les prix allègent les relances
(Mélenchon : 27,82 → 27,34). Classement de 2037 : Tondelier passe devant Le Pen, Glucksmann devant Zemmour.

Sensibilités (avant les trois canaux de la suite, prudent 2037) : sans la BCE, Mélenchon 24,1 au lieu de 26,9 ; part
de long terme φ = 0 : Écologie de droite 4,59 au lieu de 4,68.

## Reste de la phase E

- E2 : TVA et accises comme chocs de prix ; boucle prix-salaires explicite.
- E4 : contenu en importations par instrument (investissement public, manqué
  de 35 % la première année) ; balance courante (revenus versés aux non-résidents).
- E5 : capital public (investissement public, fonds d'Écologie de droite) sur le même stock.
- E6 : appariement, chômage d'équilibre, participation par âge.

## Sources

- Bardaji, Campagne, Khder, Lafféter, Simon (Insee), Dufernez, Élezaar, Leblanc, Masson, Partouche (DG Trésor), « Le
  modèle macroéconométrique Mésange : réestimation et nouveautés », Insee, document de travail G2017/04, mai 2017 :
  variantes p. 100 à 134.
- Kilponen et al., « Comparing fiscal multipliers across models and countries in Europe », Banque nationale de
  Belgique, WP n° 278, 2015.
- Taylor, « Discretion versus policy rules in practice », Carnegie-Rochester Conference Series, 1993.
- PIB de la France et de la zone euro en 2024 : Insee, Eurostat (repris par BNP Paribas, Petit atlas de l'économie
  française, mars 2025).
