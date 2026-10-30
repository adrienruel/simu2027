# Chômage jusqu'en 2073 (30 octobre 2026)

Demande d'Adrien : le chômage n'était calculé que jusqu'en 2040 (population active figée en 2026, comme la v235).
Paramètre `chomage.dynamique` (v235 : non). Chaque année :
- **sans le programme** (`demographie.chomage_tendanciel`) : population de l'Insee × taux d'emploi par âge de 2025,
  chômeurs par âge au taux de 2025 de leur âge (Insee : 19,8 % avant 25 ans, 6,9 % de 25 à 49, 5,0 % après 50),
  calés sur 8,3 % en 2026. Taux tendanciel : 8,3 % en 2037, 8,1 % en 2050, 8,0 % en 2073 (moins de jeunes) ;
- **réformes** : chômeurs repris par les réformes, proportionnels à l'écart entre le taux tendanciel et le
  chômage incompressible de 3,5 % (rendements décroissants : −6 % d'emplois des réformes en 2073, effet aussi
  sur le budget) ; effet récessif de l'ajustement de 2029 et des baisses du RUI de la règle ;
- **seniors** : 7 chômeurs en plus pour 17 emplois de seniors gardés (réforme de 2010, Insee 2017), au niveau de la
  source dans tous les scénarios : 70 000 en 2037, 195 000 à partir de 2050 avec le socle à 67 ans ;
- **population active** : grossie des emplois venus de l'inactivité (seniors, cumul, inactifs, jeunes entrés plus
  tôt), qui ne réduisent pas le nombre de chômeurs.

| Chômage (%) | 2029 | 2032 | 2037 | 2040 | 2050 | 2060 | 2073 |
|---|---|---|---|---|---|---|---|
| Crise | 9,40 | 9,16 | 8,33 | 8,29 | 8,39 | 8,32 | 8,28 |
| Prudent | 9,19 | 8,45 | 7,33 | 7,35 | 7,59 | 7,64 | 7,61 |
| Médian | 8,78 | 7,34 | 6,42 | 6,41 | 6,61 | 6,66 | 6,63 |
| Optimiste | 8,03 | 5,77 | 5,05 | 5,06 | 5,35 | 5,41 | 5,40 |

Lecture : après 2040, le chômage remonte d'environ 0,3 point, parce que le report du socle à 67 ans met des seniors
au chômage (la source de 2010 en compte 7 pour 17 emplois gardés) ; la baisse due aux réformes tient, un peu
réduite par la démographie. Effet sur les comptes : négligeable (déficit sans règle 2073 prudent −1,77 → −1,76 %).

## Pourquoi la hausse du chômage des seniors ne dégrade pas les comptes (question d'Adrien, 30/10/2026)

Le RUI est universel : il ne dépend pas du statut de chômeur ou d'inactif. Ces seniors sont déjà payés au budget
comme personnes sans emploi :
- avant 65 ans, par le RUI des adultes (qui suit la population de 18 à 64 ans) ;
- de 65 à 66 ans, par la ligne « Entre l'âge légal et 67 ans » : RUI versé à 89 % de la tranche d'âge (tous
  sauf les 11 % en emploi à 65-69 ans en 2025), 14 Md€ par an à partir de 2050 ; et RUI ou socle pour toutes les
  personnes de l'ancien système dont le départ est reporté (0,7 million en 2037), même celles qui travaillent.
Le modèle de chômage ne fait que dire combien de ces personnes cherchent un emploi : le coût (une pension
remplacée par le RUI) est déjà compté. Ce qu'il change aux comptes : les réformes reprennent un peu moins de
chômeurs quand la démographie fait baisser le chômage (effet sur le budget, faible).

**Erreur trouvée en vérifiant** : la ligne « Entre l'âge légal et 67 ans » ne comptait que les générations nées
jusqu'en 2007 (fichier des cohortes), si bien qu'en 2072-2073 il manquait les 65-66 ans nés en 2007-2008 :
0,8 million de personnes et 7 Md€ de RUI en 2073. Corrigé avec la population de l'Insee : déficit sans règle du
prudent en 2073 −1,76 → −1,64 % ; crise 2073 publiée 3,91 → 4,04 %.

Prudence restante (dans le sens défavorable) : de 65 à 66 ans, le budget paie le RUI à 89 % des personnes alors que
le bloc emploi compte des emplois de seniors en plus (300 000 dans le prudent avec le socle à 67 ans) ; ceux qui
travaillent ne toucheraient qu'une partie du RUI. Le coût est donc un peu surestimé.
