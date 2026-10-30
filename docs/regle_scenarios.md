# Règle de trajectoire dans tous les scénarios (29 octobre 2026)

DÉCISION d'Adrien : même point de départ pour tous les scénarios. Le médian et l'optimiste passaient au-dessus du
prudent en déficit publié (4,27 % et 3,65 % en 2029 contre 3,00 %), seul le prudent ayant la règle. La règle
s'applique désormais aussi au médian et à l'optimiste (`clause.scenarios`), qui sont publiés avec et sans règle :
tous partent de 3,00 % en 2029. Le médian sort de la contribution et de la baisse du RUI en 2033, l'optimiste dès
2030 ; le prudent en 2051 ; la crise jamais. L'étalement de la déduction, une fois déclenché, reste acquis (règle
inchangée), d'où un déficit publié sous le déficit sans règle quelques années après la sortie ; l'épargne prise est
rendue à 67 ans dans chaque scénario.

Correction faite en passant : quand le déficit sans règle était sous 3 % mais que l'étalement coûtait cette
année-là, la règle prélevait quand même ce coût sur l'épargne (prudent, 2044-2051 : jusqu'à 7 Md€ par an pris sans
nécessité ; aussi quelques dizaines de millions en fin de période). Elle ne prend plus que ce qui dépasse la marge
sous la cible. Effet : prudent 2073 −1,79 → −1,77 % (moins d'épargne prise, donc moins à rendre et plus de capital).

| Déficit sans règle / publié | 2029 | 2032 | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|---|---|
| Crise | 4,81 / 3,00 | 5,62 / 3,69 | 4,95 / 3,25 | 4,29 / 3,22 | 5,05 / 3,93 | 152 % |
| Prudent | 4,68 / 3,00 | 5,06 / 3,14 | 4,28 / 3,00 | 3,66 / 3,00 | −1,77 / −1,77 | 85 % |
| Médian | 4,27 / 3,00 | 3,50 / 3,00 | 2,35 / 2,14 | −0,78 / −0,73 | −8,81 / −8,81 | −64 % |
| Optimiste | 3,65 / 3,00 | 2,14 / 1,89 | 0,54 / 0,34 | −3,02 / −2,98 | −10,75 / −10,75 | −122 % |

## Point de départ commun (30 octobre 2026)

DÉCISION d'Adrien : les quatre scénarios partent du même point. Avant, dès 2029, l'optimiste avait 70 Md€ de PIB,
1,2 point de déficit et 1,4 point de chômage d'avance sur la crise : le multiplicateur, les montées des réformes,
les réactions à l'impôt, l'érosion de l'IS, l'IA, la tendance jouaient déjà à leur valeur propre la première année.

Désormais (`macro.depart_commun`, `macro.convergence_scenarios_annees` = 3) : en 2029, toutes les hypothèses
macro prennent leur valeur prudente dans tous les scénarios, crise comprise (recalculée avec la colonne prudente) ;
chaque scénario rejoint ses propres valeurs en trois ans (poids 0 en 2029, 1/3 en 2030, 2/3 en 2031, 1 en 2032).
Sans cette montée, l'optimiste perdait près de 2 points de chômage entre 2029 et 2030.

| Sans règle / publié | 2029 | 2030 | 2031 | 2032 | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|---|---|---|---|
| Crise | 4,67 / 3,00 | 5,05 / 3,13 | 5,68 / 3,74 | 5,61 / 3,68 | 4,91 / 3,22 | 4,23 / 3,16 | 5,03 / 3,91 | 151 % |
| Prudent | 4,68 / 3,00 | 4,93 / 3,02 | 5,34 / 3,41 | 5,06 / 3,14 | 4,28 / 3,00 | 3,66 / 3,00 | −1,64 / −1,64 | 85 % |
| Médian | 4,67 / 3,00 | 4,70 / 3,00 | 4,49 / 3,00 | 3,59 / 3,00 | 2,49 / 2,27 | −0,58 / −0,52 | −8,65 / −8,65 | −59 % |
| Optimiste | 4,67 / 3,00 | 4,39 / 3,00 | 3,48 / 3,00 | 2,40 / 2,15 | 0,87 / 0,67 | −2,63 / −2,58 | −10,67 / −10,67 | −114 % |

| Chômage (%) | 2029 | 2030 | 2031 | 2032 | 2033 | 2037 | 2050 | 2073 |
|---|---|---|---|---|---|---|---|---|
| Crise | 9,19 | 9,25 | 9,25 | 9,18 | 8,88 | 8,33 | 8,39 | 8,28 |
| Prudent | 9,19 | 9,08 | 8,82 | 8,45 | 8,04 | 7,33 | 7,59 | 7,61 |
| Médian | 9,19 | 8,89 | 8,21 | 7,31 | 6,73 | 6,42 | 6,61 | 6,63 |
| Optimiste | 9,19 | 8,54 | 7,30 | 5,75 | 5,02 | 5,05 | 5,35 | 5,40 |

La durée de trois ans est une hypothèse (l'information sur les comportements arrive en deux à trois ans). Le long
terme ne change presque pas ; la crise de 2073 s'améliore un peu (3,91 % publié contre 4,04 %), parce qu'elle
n'a plus le choc de 2029 en plus.
