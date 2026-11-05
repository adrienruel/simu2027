# Emploi et chômage au comparateur (5 novembre 2026)

Étape 2 de `claude/Ecologie_indicateurs.md` (projet).

## Ce qui passe par le noyau

`noyau.CONTEXTE` accepte deux clés de plus :

- `emploi` : personnes en emploi, année par année (statu quo : `statu_quo.effectifs`, taux d'emploi par âge de 2025) ;
- `emplois_canaux` : {année: {canal: emplois en plus ou en moins}}, contre le statu quo.

La trajectoire de chaque programme porte `emploi` et `emplois_canaux`.

## Programmes

- **Écologie de droite** : emploi = actifs − chômeurs du module macro (`chomage_detail`, qui publie désormais aussi la
  conjoncture et les emplois venus de l'inactivité). Canaux : chômeurs repris par les réformes, venus de l'inactivité
  (seniors, cumul, inactifs, jeunes), emplois du fonds, conjoncture (ajustement budgétaire). Le reste de l'écart au
  statu quo (effet du programme sur les naissances, calage du module macro) est publié tel quel : « Démographie et
  reste ».
- **Tondelier** : emplois perdus du SMIC à 2 000 €, et **conjoncture** : l'impulsion budgétaire change l'emploi selon la
  même règle que le moteur d'Écologie de droite (`macro.emplois_par_point_pib`, loi d'Okun : 0,45 % d'emploi pour 1 %
  de PIB dans le prudent). Avant ce jour, son multiplicateur faisait monter le PIB sans créer d'emplois ni baisser le
  chômage : une asymétrie entre programmes, corrigée.

## Export

`sorties/comparaison_trajectoire.csv` : `emploi_millions`, `ecart_emploi_milliers` (contre le statu quo),
`taux_emploi_18_66` (18 à 66 ans : la tranche contient le report de l'âge de départ à 67 ans ; l'emploi après 67 ans
est celui du statu quo). `sorties/comparaison_emploi_canaux.csv` : emplois par canal, en milliers.

Limite : le taux d'emploi par âge (seniors 55-64 ans) n'est pas encore ventilé par programme ; seuls les emplois venus
de l'inactivité, dont les seniors, apparaissent comme canal.
