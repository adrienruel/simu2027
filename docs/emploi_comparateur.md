# Emploi et chômage au comparateur (5 novembre 2026)

Étape 2 de `claude/Ecologie_indicateurs.md` (projet).

## Ce qui passe par le noyau

`noyau.CONTEXTE` accepte deux clés de plus :

- `emploi` : personnes en emploi, année par année (statu quo : `statu_quo.effectifs`, taux d'emploi par âge de 2025) ;
- `emplois_canaux` : {année: {canal: emplois en plus ou en moins}}, contre le statu quo.

La trajectoire de chaque programme porte `emploi` et `emplois_canaux`.

## Programmes

- **Écologie de droite** : emploi = statu quo + somme des canaux du module macro (`chomage_detail`, qui publie
  désormais aussi la conjoncture et les emplois venus de l'inactivité) : chômeurs repris par les réformes, venus de
  l'inactivité (seniors, cumul, inactifs, jeunes), emplois du fonds, conjoncture (ajustement budgétaire). On ne prend
  pas actifs − chômeurs du module macro : sa base d'actifs est calée autrement que le statu quo (environ 850 000
  personnes en emploi de plus, écart constant trouvé le 05/11/2026), ce qui aurait été publié comme un effet du
  programme. Non compté : l'effet du programme sur les naissances (actifs en moins après 2048).
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

## Mesures de Tondelier sur l'emploi (05/11/2026, question d'Adrien)

Avant ce jour, le coût de la garantie d'emploi, des recrutements publics, des 32 heures et du retour sur les réformes
de l'assurance chômage était chiffré, mais pas leur effet sur l'emploi et le chômage. Groupe `tondelier_emploi` :

- **Postes publics créés** : montant des mesures qui recrutent (santé scolaire, hôpital, Ehpad, classes, AESH, justice,
  inspection, voie professionnelle, embauches compensatrices des 32 heures à l'hôpital) ÷ 55 000 € par poste ;
  environ 340 000 postes à terme.
- **Éviction d'emplois privés** (commune à tous les programmes, `emploi_public.eviction_privee`) : 1,5 emploi privé
  pour un emploi public en crise (Algan, Cahuc et Zylberberg, 2002), 1 dans le prudent, 0,5 en médian, 0,25 en
  optimiste. Les emplois privés perdus coûtent au solde.
- **Garantie d'emploi à 55 ans** : 150 000 éligibles × 30 % de recours, 10 % d'éviction, moitié venue du chômage.
- **Assurance chômage** : abroger les réformes de 2021 et 2023 remonte le chômage de 0,6 point dans le prudent (Banque
  de France, Bulletin n° 264 : ces réformes l'ont baissé de 0,2 et 0,4 point). Chaque chômeur en plus coûte au
  solde.

Relevé en passant : la source des réformes d'Écologie de droite (`emploi.reformes_directes`) cite « −0,4 et −0,6
point » pour les réformes de 2021 et 2023, alors que le Bulletin n° 264 donne −0,2 et −0,4 (−0,6 au total). La
valeur retenue (0,4 point dans le prudent pour l'allocation remplacée par le RUI) reste dans la fourchette ; la note
est à corriger.

Les emplois des réformes d'Écologie de droite sont ventilés mesure par mesure (`emploi_canaux.emplois_par_mesure`,
au prorata des emplois à terme).
