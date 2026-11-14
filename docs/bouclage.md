# Phase E : macro bouclée (14 novembre 2026)

`moteur/bouclage.py`, paramètres `bouclage.*` (`parametres/commun/economie.yaml`), option `macro.bouclage`
(`parametres/commun/options.yaml`, vrai sur la branche `phase-e`, **à valider par Adrien**). Tests :
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
| Choc pétrolier | non fait (demande E4 : termes de l'échange) | | | | |

- Dépense : retrouvée à 7 % près.
- Investissement public : manqué la première année (0,86 contre 1,31). Dans Mésange, l'investissement a un effet
  d'impact plus fort (moins d'importations) ; le moteur n'a qu'une forme de demande. Reste de E4 : contenu en
  importations par instrument.
- Cotisations : avec l'ancien poids de demande (0,4), +140 % la première année : le canal d'offre, calé sur Mésange,
  porte déjà l'effet de compétitivité, et l'entreprise garde d'abord la baisse en marge. Poids ramené à 0,13 (dans la
  fourchette de Kilponen et al., 0,04 à 0,51) : les cinq horizons passent, de justesse à 3 ans (−29,6 %). Prix : −0,32
  / −0,55 / −0,71 / −0,91 / −1,09, contre −0,36 / −0,70 / −0,87 / −1,09 / −1,32 dans Mésange (même signe ; avant : en
  hausse, par la demande seule).

## Effet sur les programmes (déficit, % du PIB, prudent : main au commit 7c511dc → phase E)

| Programme | 2032 | 2037 | 2050 |
|---|---|---|---|
| Statu quo | 7,16 → 7,16 | 9,50 → 9,50 | 20,57 → 20,57 |
| Écologie de droite | 4,16 → 4,54 | 4,15 → 4,68 | 4,89 → 6,12 |
| Bertrand | 7,09 → 7,09 | 9,28 → 9,33 | 20,24 → 20,37 |
| Retailleau | 7,73 → 7,70 | 10,46 → 10,36 | 24,29 → 24,03 |
| Philippe | 8,34 → 8,27 | 11,25 → 11,16 | 26,92 → 26,74 |
| Attal | 8,66 → 8,42 | 11,54 → 11,31 | 26,82 → 26,13 |
| Tondelier | 9,63 → 9,08 | 13,98 → 12,79 | 33,85 → 30,63 |
| Le Pen | 9,99 → 9,58 | 13,71 → 13,16 | 33,47 → 32,06 |
| Glucksmann | 10,23 → 9,59 | 14,44 → 13,33 | 34,18 → 31,38 |
| Zemmour | 10,52 → 10,20 | 13,99 → 13,80 | 35,11 → 34,57 |
| Lisnard | 10,90 → 10,66 | 14,73 → 14,36 | 37,23 → 36,31 |
| Arthaud | 12,56 → 11,88 | 18,44 → 16,70 | 45,43 → 41,35 |
| Mélenchon | 19,40 → 18,77 | 29,63 → 26,90 | 71,35 → 65,73 |
| Roussel | 17,50 → 17,18 | 30,82 → 28,94 | 84,22 → 80,09 |

Lecture : l'effet d'une impulsion dure plus longtemps (Mésange : encore 0,53 au bout de dix ans, contre zéro après
4,5 ans dans l'ancienne forme). Les relances y gagnent (de 1 à 3 points de déficit en 2037), la consolidation
d'Écologie de droite y perd (+0,5 point en 2037, +1,2 en 2050). Le classement de 2037 bouge peu : Tondelier passe
devant Le Pen, Glucksmann devant Zemmour.

Décomposition (prudent, 2037) :
- **Persistance de la demande** : l'essentiel.
- **Prix** : allège la dette des relances (Mélenchon : 269 → 247 % du PIB en 2037, à déficit presque égal).
- **BCE** : resserre un peu les taux quand la France relance ; sur une dette de 250 % du PIB, c'est beaucoup
  (Mélenchon : 24,1 % sans la BCE, 26,9 % avec).
- **Part gardée à long terme** (φ, Mésange 0,16) : peu d'effet ; à φ = 0, Écologie de droite 4,59 au lieu de 4,68 en
  2037, Mélenchon 26,80 au lieu de 26,90.

## Décisions à prendre par Adrien

1. Activer le bouclage (`macro.bouclage`) dans le chiffrage publié.
2. `macro.multiplicateur` lu comme l'effet maximal (deuxième année) plutôt que comme l'effet de la première année.
3. Poids de demande du coût du travail 0,4 → 0,13 (calé sur Mésange).
4. Règle de la BCE active (par défaut) ou taux réels constants comme Mésange.
5. Part gardée à long terme : celle de Mésange (φ = 0,19) ou zéro (modèle d'offre pur à long terme).

## Reste de la phase E

- E1 : la prime de dette ne pèse pas encore sur la demande (elle est calculée dans le noyau, après le multiplicateur).
- E2 : revalorisation des pensions en retard sur les prix (érosion d'un an) ; TVA et accises comme chocs de prix ;
  boucle prix-salaires explicite (salaires indexés sur les prix avec retard).
- E4 : balance courante publiée ; contenu en importations par instrument (investissement public) ; termes de
  l'échange (choc pétrolier de Mésange : −0,10 / −0,24 / −0,18 / −0,21 / −0,22 % de PIB pour +10 $ le baril).
- E5 : accumulation du capital (aujourd'hui par canal).
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
