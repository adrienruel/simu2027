# Dépenses sensibles au chômage du programme (phase L, roadmap du comparateur 4.1, 18/11/2026)

## Avant

Les blocs **chômage** (assurance chômage) et **pauvreté** (RSA, prime d'activité) suivaient les chômeurs du statu
quo, quel que soit le programme (`moteur/statu_quo.blocs`). Un emploi en plus ne rendait l'allocation évitée que
par la valeur d'un emploi de son canal (`emploi.valeur_emploi`, `ProgrammeSimple.valeur_emploi_cellule`), comptée en
recettes. D'où trois défauts :

- **Canaux sans allocation.** Les chômeurs en plus ou en moins de la conjoncture (multiplicateur), de l'effet
  d'offre, des taux (rétroaction de la phase E1) et des postes publics créés ou supprimés ne changeaient pas la
  dépense de chômage.
- **Asymétrie.** Pour les postes publics, l'éviction d'emplois privés comptait l'allocation, mais pas les postes
  eux-mêmes. Supprimer des postes publics faisait donc gagner l'allocation des emplois privés repris, sans coûter
  celle des agents mis au chômage. Créer des postes faisait l'inverse.
- **Plancher du chômage non suivi.** Le plancher du chômage (`emploi_canaux.plancher_chomage`) retire des emplois
  aux canaux, mais l'allocation déjà comptée en recettes ne suivait pas.

## Règle

`emploi.depenses_chomage_programme` (DÉCISION, commune) : le noyau ajoute aux blocs les chômeurs du programme par
rapport au statu quo (contexte `chomeurs_depenses`), au prix `emploi.allocation_chomeur_evitee` (9 000 €, au salaire
de l'année).

- **Partage** entre les blocs (`emploi.part_allocation_assurance_chomage`) : 70 % au bloc chômage et 30 % au bloc
  pauvreté. C'est la même décomposition que les 9 000 € : 6 300 € d'assurance chômage, le reste en RSA.
- **Chômeurs comptés** : ceux de tous les canaux, après le plancher, moins les actifs en plus (offre, personnes
  retirées de la population active), plus ceux que la rétroaction des taux ajoute dans le noyau.
- **Canaux exclus**, parce qu'ils sont déjà comptés par leur propre mesure :
  - les canaux dont la mesure compte déjà le budget (nom en « * ») : SMIC, partage du travail, garanties d'emploi,
    Territoires zéro chômeur, réquisitions ;
  - les seniors (`seniors.allocation_chomage`, 16 000 €) ;
  - la démographie (règle du statu quo sur la population du programme).
- **Postes publics** : ils sont toujours comptés, même en « * » (embauches publiques du partage du travail). Leur
  mesure paie la rémunération et en reprend les prélèvements, jamais l'allocation.
- **Pas de double compte** : l'allocation sort de la valeur d'un emploi des canaux sans « * » (20 000 € − 9 000 €
  pour `emploi.valeur_emploi`), et de la valeur d'un emploi de l'assurance chômage et de l'éviction de Tondelier.
- **Publication** : le montant de chaque année est publié dans les comptes (`depenses_chomage_programme`, Md€).
  `tests/test_proprietes.py` le compte dans l'identité « mesures = écart de solde primaire ».

## Effet (déficit public en % du PIB, 2037)

| Programme | Prudent 2037 avant | après | dépenses du bloc (Md€) | Médian 2037 avant | après | dépenses du bloc (Md€) |
|---|---|---|---|---|---|---|
| arthaud | 16,82 | 16,53 | +2,5 | 12,40 | 12,15 | -2,0 |
| attal | 11,27 | 11,22 | -1,2 | 8,92 | 8,88 | -1,8 |
| bertrand | 9,51 | 9,52 | +0,2 | 8,00 | 8,02 | -0,0 |
| glucksmann | 13,41 | 13,34 | +1,5 | 11,13 | 11,07 | +0,8 |
| le_pen | 13,23 | 13,26 | +0,6 | 10,77 | 10,78 | -0,7 |
| lisnard | 14,14 | 14,03 | -2,8 | 10,88 | 10,78 | -4,6 |
| melenchon | 28,04 | 27,85 | +4,7 | 20,64 | 20,45 | +1,0 |
| philippe | 11,15 | 11,16 | -0,6 | 8,55 | 8,57 | -1,8 |
| retailleau | 10,20 | 10,24 | -0,3 | 8,12 | 8,17 | -1,6 |
| roussel | 30,06 | 29,76 | +2,7 | 21,75 | 21,46 | -1,8 |
| tondelier | 13,32 | 13,20 | +3,1 | 10,00 | 9,90 | +1,0 |
| zemmour | 13,65 | 13,60 | -0,6 | 10,59 | 10,56 | -2,1 |

Lecture :

- **Programmes qui créent des postes publics** (Arthaud, Roussel, Mélenchon, Tondelier) : déficit plus bas de 0,1 à
  0,3 point. Leurs agents recrutés viennent du chômage, et l'allocation évitée n'était pas comptée. La dépense du
  bloc monte malgré tout en prudent : leurs pertes d'emplois privés (SMIC, coût horaire) y passent désormais.
- **Programmes qui suppriment des postes** (Retailleau, Philippe, Le Pen, Bertrand) : déficit plus haut de 0,01 à
  0,05 point. Les agents non remplacés pèsent maintenant sur l'assurance chômage, comme l'éviction le faisait déjà
  dans l'autre sens.
- **Lisnard, Attal, Zemmour** : déficit plus bas de 0,03 à 0,11 point. L'effet d'offre et la conjoncture baissent
  le chômage, et les allocations suivent.

## Décisions d'Adrien du 18/11/2026 (roadmap 5.4 et 5.5)

- **Coût d'un chômeur selon le programme** (`emploi.generosite_programme`). Chaque année, deux facteurs : (bloc du
  statu quo + mesures de législation du programme sur ce bloc) / bloc du statu quo, l'un pour le bloc chômage,
  l'autre pour le bloc pauvreté.
  - Ils multiplient tout ce qui suit le nombre de chômeurs : les dépenses de chômage du programme, les allocations
    des seniors et la variante démographique.
  - Les mesures marquées `volume: true` ne comptent pas : elles comptent des allocataires en moins, pas une
    allocation plus basse (garantie d'emploi de Mélenchon, sécurité d'emploi ou de formation de Roussel).
  - En 2037, au prudent, le facteur du bloc pauvreté vaut 2,52 pour Mélenchon (garantie d'autonomie) et 0,43 pour
    Lisnard (allocation unique plafonnée).
  - La démographie garde son coût moyen du statu quo, multiplié par le même facteur.
- **Prime d'activité des emplois en plus** (`emploi.prime_activite_emplois`) : ≈ 2 140 € par emploi et par an.
  - Le montant est lu sur la table OpenFisca de 2026 d'une personne seule, à 1,3 fois le coût du SMIC.
  - Il est indexé comme la prime du statu quo, multiplié par le facteur du bloc pauvreté, et ajouté au bloc pauvreté
    pour les mêmes emplois que la règle 4.1.

## Reste ouvert

- **Barème de la prime d'activité** : c'est celui d'une personne seule. Un couple ou des enfants changent le droit.
  La micro relancée (phase 6) pourra le remplacer.
- **Emploi spécifique jeune** (Mélenchon) : canal en « * » sans allocation évitée dans sa mesure. Il est laissé
  hors du bloc, faute de savoir si ces jeunes viennent du chômage.
