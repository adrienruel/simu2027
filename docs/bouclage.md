# Phase E : macro bouclée (14 novembre 2026)

Branche `phase-e`. Modules : `moteur/bouclage.py` (demande, prix, BCE, profils par instrument, emploi de conjoncture),
`moteur/capital.py` (capital des entreprises et capital public), `moteur/noyau.py` (rétroaction des taux, pensions,
balance commerciale et courante). Paramètres `bouclage.*` et `capital_public.*` (`parametres/commun/economie.yaml`),
options `macro.bouclage`, `macro.bouclage_prime_demande`, `macro.bouclage_profils`, `macro.capital_commun`
(`parametres/commun/options.yaml` ; faux : ancien calcul). Tests : `tests/test_bouclage.py`, `tests/test_capital.py`.
Outils : `outils/calibrer_bouclage.py` (calage), `outils/banc_mesange.py` (critère de sortie),
`outils/comparer_bouclage.py` (effet sur les 14 trajectoires).

Décisions d'Adrien (14/11/2026) : bouclage actif dans le chiffrage publié ; `macro.multiplicateur` = effet maximal
(deuxième année) ; règle de la BCE active ; part de long terme de Mésange ; E5 puis le reste de E avant la fusion.

## Ce qui change

Avant : l'impulsion budgétaire d'une année agissait en entier cette année-là, puis s'éteignait linéairement en 3 à
5 ans ; l'emploi suivait le PIB par une loi d'Okun fixe ; l'inflation des programmes était celle du statu quo (sauf
Écologie de droite, avec une courbe de Phillips propre à son effort de 2029) ; les taux ne réagissaient qu'à la dette,
et seulement sur les intérêts.

| Bloc | Après | Où |
|---|---|---|
| E1 demande | Forme réduite calée sur Mésange : impact 0,86, effet maximal la deuxième année, encore 0,49 à 10 ans, 0,19 à long terme. Échelle : multiplicateur du scénario (effet maximal : crise 1,3, prudent et médian 1, optimiste 0,5), miroir pour une relance, contrainte de capacité | `bouclage.reponse` |
| E1 instruments | TVA et accises, CSG et impôts sur le travail, impôt sur le revenu, cotisations employeurs : profil de Mésange de l'instrument, moins ce que le canal d'offre compte déjà ; investissement public : effet d'impact de l'accélérateur (0,53 × 0,6^années) | `bouclage.profil_demande` |
| E1 taux | L'écart de taux de marché au statu quo (prime de dette, écart propre au programme, BCE) passe aux crédits (0,15 à 0,5 selon le scénario) puis au PIB (variante de taux de Mésange), avec le plancher du chômage commun | noyau |
| E2 prix | Courbe de Phillips et compétitivité-prix ; prix propres à chaque instrument à profil (TVA : +1,48 % la première année par point de PIB) ; pensions revalorisées en retard sur les prix | `bouclage`, noyau |
| E3 BCE | Règle de Taylor au poids de la France (19,4 %) ; les taux suivent l'inflation de la zone : une inflation propre à la France allège la dette réelle | `bouclage`, noyau |
| E4 extérieur | Balance commerciale (−0,31 × écart de PIB − 0,29 × écart de prix) et courante (moins 56 % des intérêts en plus, part des non-résidents) ; facture énergétique (0,213 Md€ par Mt de CO2 fossile déclarée par les mesures, en demande et en balance) | noyau, `bouclage.facture_energie` |
| E5 capital | Stock de capital des entreprises avec usure, valorisé au rendement net + usure (l'ancien canal comptait 2,2 fois plus) ; capital public avec usure, effet productif en plus de la demande seulement | `moteur/capital.py` |
| E6 travail | Emploi de conjoncture par les profils de Mésange : la dépense ramène l'emploi à l'équilibre en une dizaine d'années, les impôts sur le travail le changent durablement | `bouclage.reponse` (emplois) |

Remplacés : la forme linéaire du multiplicateur, de la production des postes publics (A3) et de la clause
d'Écologie de droite ; la courbe de Phillips propre à l'effort de 2029 d'Écologie de droite ; la loi d'Okun de la
demande (elle reste pour la rétroaction des taux) ; le poids de demande fixe et les prix par les coûts des
instruments à profil ; `offre.capital_entreprises_par_point` et `offre.elasticite_investissement_public` (sous les
options de la phase E).

### Deux doubles comptes corrigés en route

- **Impôt sur les entreprises** : le canal d'offre commun faisait PIB × part du capital (0,35) × capital en plus ; les
  cohortes d'Écologie de droite, capital en plus × (rendement net + usure ≈ 0,13). La part du capital s'applique à la
  valeur ajoutée des sociétés (1 545 Md€), pas à tout le PIB : taux de marge (32,2 %) × valeur ajoutée / capital des
  SNF (≈ 3 650 Md€) ≈ 0,14, comme Écologie de droite. Baisse d'IS d'un point de PIB : +0,18 % de PIB à long terme
  (0,41 avant) ; IS de 33,3 à 25 % : ≈ +0,25 %.
- **Investissement public** : son effet d'offre (0,33 en médian, présenté comme l'effet total de Mésange d'une version
  antérieure) s'ajoutait à la demande bouclée, qui garde déjà 0,19 à long terme : 0,52 au total contre 0,22 dans
  Mésange 2017. Désormais : capital public avec usure (4 %), effet en plus de la demande (crise 0, prudent 0,03,
  médian 0,06, optimiste 0,3).

## Calage de la forme générique (outils/calibrer_bouclage.py)

Moindres carrés sur la dépense publique générique de Mésange 2017 (PIB et prix, p. 105) et la hausse de 100 points
de base des taux réels (PIB, p. 134), variantes à taux réels et change nominal constants (p. 100).

| Années | 1 | 2 | 3 | 5 | 10 | LT |
|---|---|---|---|---|---|---|
| PIB, Mésange | 0,78 | 1,06 | 1,03 | 0,86 | 0,53 | 0,16 |
| PIB, forme calée | 0,86 | 1,05 | 1,02 | 0,83 | 0,48 | 0,19 |
| Prix, Mésange | 0,20 | 0,58 | 0,94 | 1,42 | 1,88 | 2,69 |
| Prix, forme calée | 0,24 | 0,54 | 0,83 | 1,32 | 2,05 | 2,65 |
| Taux +100 pb, Mésange | −0,17 | −0,60 | −0,78 | −1,00 | | |
| Taux +100 pb, forme calée | −0,27 | −0,55 | −0,77 | −1,01 | | |

## Critère de sortie (outils/banc_mesange.py)

Variantes de Mésange passées par le pipeline commun (demande bouclée + canal d'offre), scénario médian, BCE coupée
comme dans Mésange. Écart relatif au PIB de Mésange :

| Variante (1 point de PIB) | 1 an | 2 ans | 3 ans | 5 ans | 10 ans |
|---|---|---|---|---|---|
| Dépense publique | +5 % | −6 % | −6 % | −7 % | −7 % |
| Investissement public | +3 % | −4 % | −4 % | −5 % | −6 % |
| Cotisations employeurs (baisse) | 0 % | 0 % | 0 % | 0 % | 0 % |
| TVA (hausse) | +3 % | +3 % | +4 % | +6 % | +9 % |
| CSG (baisse) | 0 % | 0 % | 0 % | 0 % | +1 % |
| Impôt sur le revenu (baisse) | 0 % | 0 % | 0 % | 0 % | 0 % |
| Pétrole (+10 $ le baril) | −34 % | +22 % | −17 % | −5 % | +5 % |

Les instruments à profil retrouvent Mésange par construction au médian (le profil est celui de Mésange, moins le
canal d'offre) ; l'écart de la TVA vient du scénario miroir de l'offre pour une hausse. Le test est utile hors du
médian et pour la répartition entre demande et offre. Le pétrole (revenu payé à l'étranger + énergie plus chère pour
les entreprises) ne sert qu'au banc ; il manque la première année. La balance commerciale retrouve celle de Mésange à
0,08 point près ; l'emploi (conjoncture + offre), à 10 % près.

## Effet sur les programmes (prudent : main au commit 7e0486e → phase E)

| Programme | Déficit 2037 | Chômage 2037 | Dette 2050 (% du PIB) |
|---|---|---|---|
| Statu quo | 9,50 → 9,50 | 8,32 → 8,32 | 283 → 283 |
| Écologie de droite | 4,15 → 4,66 | 8,25 → 8,38 | 144 → 158 |
| Bertrand | 9,28 → 9,32 | 8,46 → 8,45 | 281 → 282 |
| Retailleau | 10,46 → 10,37 | 8,26 → 8,20 | 317 → 316 |
| Philippe | 11,25 → 11,16 | 8,30 → 8,19 | 342 → 343 |
| Attal | 11,54 → 11,25 | 8,16 → 7,90 | 342 → 336 |
| Tondelier | 13,98 → 12,87 | 10,50 → 10,74 | 406 → 366 |
| Le Pen | 13,71 → 13,15 | 8,22 → 8,18 | 407 → 392 |
| Glucksmann | 14,44 → 13,34 | 9,03 → 8,91 | 413 → 380 |
| Zemmour | 13,99 → 13,66 | 8,63 → 8,10 | 425 → 421 |
| Lisnard | 14,73 → 14,18 | 8,20 → 7,40 | 443 → 437 |
| Arthaud | 18,44 → 16,95 | 11,89 → 12,04 | 530 → 477 |
| Mélenchon | 29,63 → 27,32 | 8,94 → 9,24 | 786 → 681 |
| Roussel | 30,82 → 29,90 | 8,26 → 8,62 | 1 003 → 920 |

Lecture :
- **Déficit.** L'effet d'une impulsion dure plus longtemps : les relances y gagnent (Mélenchon −2,3 points en 2037,
  Tondelier −1,1), la consolidation d'Écologie de droite y perd (+0,5). La prime de dette en reprend une partie aux
  programmes très endettés ; la hausse des prix allège leur dette. Les baisses d'impôts des ménages (Lisnard, Zemmour)
  rapportent plus qu'avant (profils de Mésange), les baisses d'impôt sur les entreprises moins (capital commun).
- **Chômage.** Les relances ne baissent plus le chômage durablement : l'emploi de conjoncture revient à l'équilibre
  (Mélenchon, Roussel, Tondelier, Arthaud : chômage plus haut en 2037). Les baisses d'impôt sur le travail gardent
  leurs emplois (Lisnard 8,20 → 7,40, Zemmour 8,63 → 8,10, Attal 8,16 → 7,90).
- **Classement de 2037** : Tondelier passe devant Le Pen, Glucksmann devant Zemmour ; le reste ne bouge pas.

Sensibilités (mesurées avant les profils et le capital) : sans la BCE, Mélenchon 2037 24,1 au lieu de 26,9 ; part de
long terme φ = 0 : Écologie de droite 4,59 au lieu de 4,68.

## Ce que le moteur ne fait pas (après la phase E)

- **Appariement** (offres d'emploi et chômeurs, courbe de Beveridge) : pas de bloc ; le retour à l'équilibre vient des
  profils de Mésange, le plancher du chômage commun borne le bas.
- **Chômeurs et budget** : les emplois de conjoncture changent le chômage publié, pas les prestations (comme avant).
- **Rétroaction des taux** : le PIB perdu par les taux ne fait ni inflation ni balance commerciale.
- **Capital du fonds d'Écologie de droite** : sa propre valorisation (même rendement net + usure que le capital
  commun), hors du stock public.
- **Pétrole et termes de l'échange** pour les programmes : seulement le volume de fossile importé ; une hausse du prix
  mondial n'est pas un scénario du modèle.
- **Emplois de Mésange** : salariés du secteur marchand seulement, appliqués à l'emploi total.

## Sources

- Bardaji, Campagne, Khder, Lafféter, Simon (Insee), Dufernez, Élezaar, Leblanc, Masson, Partouche (DG Trésor), « Le
  modèle macroéconométrique Mésange : réestimation et nouveautés », Insee, document de travail G2017/04, mai 2017 :
  variantes p. 100 à 134 (dépense, investissement public, cotisations employeurs et salariés, TVA, CSG, impôt sur le
  revenu, pétrole, taux).
- Kilponen et al., « Comparing fiscal multipliers across models and countries in Europe », Banque nationale de
  Belgique, WP n° 278, 2015.
- Taylor, « Discretion versus policy rules in practice », Carnegie-Rochester Conference Series, 1993.
- Neri, « The impact of the sovereign debt crisis on bank lending rates in the euro area », Banque d'Italie, 2013 ;
  Herbst, Lang et Rusnák, BCE, WP n° 3057, 2025.
- SDES, Bilan énergétique de la France pour 2024 et 2025 ; Citepa, Secten 2026.
- Agence France Trésor (d'après la Banque de France) : 56,0 % de la dette négociable de l'État détenue par des
  non-résidents au quatrième trimestre 2025.
- Bom et Ligthart, « What have we learned from three decades of research on the productivity of public capital? »,
  Journal of Economic Surveys, 2014.
- PIB de la France et de la zone euro en 2024 : Insee, Eurostat (repris par BNP Paribas, Petit atlas de l'économie
  française, mars 2025).
