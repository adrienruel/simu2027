# Inflation, indexation et âge de départ à 67 ans (30 octobre 2026)

Décisions d'Adrien du 30/10/2026 :
- **Indexation** : RUI, AAH, socle et seuils de la contribution des retraités revalorisés du **minimum de
  l'inflation et de la croissance nominale** (`revalorisation.regle`). Les pensions de l'ancien système restent
  gelées en euros courants.
- **Âge de départ à 67 ans**, quatre trimestres de plus par génération à partir de celle qui a 64 ans en 2029
  (67 ans pour la génération née en 1967, en 2034). Avant 67 ans : RUI pour les personnes sans emploi ; rente de
  leur capital en plus si elles ont leurs annuités (sans coût pour l'État).
- **Inflation modélisée** année par année (`moteur/inflation.py`).

## Inflation

| % | 2027 | 2028 | 2029 | 2030 | 2032 | 2035 | 2050 |
|---|---|---|---|---|---|---|---|
| Crise | 1,90 | 1,60 | 0,85 | 1,64 | 1,40 | 1,40 | 1,40 |
| Prudent | 1,90 | 1,60 | 1,29 | 1,78 | 1,80 | 1,80 | 1,80 |
| Médian | 1,90 | 1,60 | 1,42 | 2,13 | 1,96 | 1,95 | 1,94 |
| Optimiste | 1,90 | 1,60 | 1,62 | 2,45 | 2,11 | 2,11 | 2,08 |

- Base : Banque de France, projections de septembre 2026 (1,9 % en 2027, 1,6 % en 2028), puis convergence en
  quatre ans vers le long terme : 1,8 % dans le prudent (décision du 29/10), 1,4 % en crise (inflation sous la
  cible comme en 2013-2020), 1,9 % en médian, 2 % en optimiste (cible de la BCE).
- **Inflation due au programme** :
  - bascule de la TVA et des taxes sur les produits : **neutre** par construction (l'accise de transition cale les
    nouvelles taxes sur la consommation sur les anciennes) ;
  - fin des impôts de production : **pas de baisse des prix comptée**, par cohérence avec le budget statique, qui
    la garde en bénéfice taxé à l'IS ;
  - **récession de l'ajustement de 2029** : −1,8 % de PIB dans le prudent, l'inflation baisse de 0,35 point en
    2029 (pente de Phillips de 0,2 ; hypothèse : 0,1 à 0,3 selon les estimations, courbe plate en zone euro) ;
  - **prix du carbone** (saut à 300 € en 2030, puis +3,2 % réel par an jusqu'en 2060) : rien dans le prudent (les
    taxes carbone européennes et canadiennes n'ont pas fait monter significativement l'inflation globale,
    Konradt et Weder di Mauro, 2023) ; la moitié en médian (+0,3 point en 2030), en entier en optimiste.
- **Effet de Fisher** : les taux nominaux suivent l'écart d'inflation à 1,8 %, au rythme du renouvellement de la
  dette (8,5 ans). Sans lui, une inflation plus basse relèverait le taux réel pendant cinquante ans.
- Ce que l'inflation change : l'érosion des pensions gelées de l'ancien système (plus d'inflation, plus de
  baisse de leur valeur réelle), les intérêts de la dette, le déficit au sens de Maastricht.

## Indexation

En euros constants, la nouvelle règle garde la valeur réelle des montants indexés (l'inflation est presque toujours
sous la croissance nominale), sauf les années de croissance réelle négative, sans rattrapage : la récession de
2029 coûte **−1,1 % de pouvoir d'achat au RUI dans le prudent en 2030** (−1,6 % en crise, −0,7 % en médian, rien en
optimiste). L'ancienne règle (croissance réelle sans l'inflation) faisait perdre environ 1,1 % de pouvoir d'achat
par an au RUI : −19 % en 2050, −37 % en 2073 (c'est elle qui mettait le RUI sous le RSA vers 2050, point de la
relecture).

## Effet sur les résultats (prudent, déficit sans règle / publié ; dette 2073)

| | 2029 | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|---|
| Avant (1,8 % fixe, ancienne indexation, 65 ans) | 5,16 / 3,26 | 4,69 / 3,00 | 4,05 / 3,00 | −0,14 | 105 % |
| + inflation modélisée | 5,08 / 3,19 | 4,68 / 3,00 | 4,11 / 3,07 | −0,12 | 105 % |
| + nouvelle indexation | 5,08 / 3,19 | 5,01 / 3,12 | 5,17 / 3,66 | 5,51 / 4,02 | 140 % |
| + départ à 67 ans | 4,98 / 3,09 | 4,12 / 3,00 | 5,05 / 3,55 | 5,17 / 3,68 | 137 % |

| Avec les trois | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|
| Crise | 5,02 / 3,12 | 6,20 / 4,68 | 20,10 / 18,58 | 284 % |
| Médian | 2,24 / 2,00 | 0,22 / 0,28 | −5,48 | −22 % |
| Optimiste | 0,48 / 0,26 | −2,10 / −2,04 | −8,28 | −89 % |

Lecture :
1. **La nouvelle indexation coûte environ 5,6 points de PIB en 2073 dans le prudent** : garder le pouvoir d'achat
   du RUI, de l'AAH et du socle, au lieu de le faire baisser de 1,1 % par an, coûte de plus en plus cher.
2. **Le départ à 67 ans rapporte beaucoup pendant la transition** (économie sur les pensions de 34 à 38 Md€ par an
   en 2034-2037, moins le RUI versé aux personnes sans emploi), puis plus rien quand l'ancien système s'éteint
   (vers 2050). Il ne compense pas l'indexation à long terme.
3. **La crise s'emballe** : avec une inflation basse (1,4 %), les pensions gelées s'érodent moins vite, et la dette
   part en boule de neige.
4. Dans le prudent, la règle au maximum ne tient pas 3 % en 2029-2032 (jusqu'à 3,59 % en 2031), en 2047-2051 (jusqu'à
   4,11 % en 2048, pic des remboursements) et à partir de 2070 (3,68 % en 2073).
