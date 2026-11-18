# « Programme IA » : un programme écrit par Claude, au banc du comparateur (18 novembre 2026)

Programme de test, pour s'amuser : 20 mesures proposées par une IA (Claude), chiffrées avec les mêmes règles que
les candidats. **Non publié** : absent de `programmes/publies.yaml`, donc hors des sorties,
de l'incertitude et des tests par défaut, et sans effet sur les autres programmes. Branche : `test/programme-ia`.

```
python -m moteur.noyau programme_ia
```

Fichiers : `programmes/programme_ia/` (`mesures.yaml` : la fiche des 20 mesures ; `parametres.yaml` : les montants
par scénario ; `programme.py` : un `ProgrammeSimple` sans mesure calculée).

## Ce que le programme annonçait, ce que le modèle retient

Le programme annonçait +41,5 Md€ net par an en 2032 et un déficit ramené de 5 % à ≈ 3,6 % du PIB. Deux erreurs :

1. **La règle de dépense (30 Md€ annoncés)** n'est pas reprise, comme pour tous les candidats : elle passe par
   l'enveloppe commune (`enveloppe_economies`). Le modèle en retient ≈ 8 Md€ en 2037 (prudent), domaine par domaine.
2. **Le point de départ** : le programme partait de 5 % du PIB comme si le déficit restait stable. Dans le statu quo
   du modèle, il dérive (7,2 % en 2032 en prudent) : il faut d'abord battre cette dérive.

Les autres gains annoncés (niches, fraude, taxe sur les boissons sucrées) sont aussi pris plus bas, en fourchette.

## Résultats (déficit en % du PIB)

Calcul du 18/11/2026, tous les programmes publiés sur le même noyau.

| Programme | Prudent 2029 | Prudent 2032 | Prudent 2037 | Médian 2029 | Médian 2032 | Médian 2037 |
|---|---:|---:|---:|---:|---:|---:|
| **Programme IA, version 3** | **5,48** | **6,29** | **8,07** | **5,17** | **5,59** | **6,40** |
| Programme IA, version 2 | 5,56 | 6,49 | 8,39 | 5,23 | 5,72 | 6,62 |
| Programme IA, version 1 | 5,79 | 6,98 | 9,27 | 5,57 | 6,37 | 7,69 |
| Statu quo | 5,91 | 7,16 | 9,50 | 5,82 | 6,82 | 8,37 |
| Bertrand | 6,02 | 7,21 | 9,52 | 5,86 | 6,68 | 8,02 |
| Retailleau | 6,37 | 7,57 | 10,24 | 6,06 | 6,75 | 8,17 |
| Philippe | 6,39 | 8,15 | 11,16 | 5,98 | 7,04 | 8,57 |
| Attal | 6,67 | 8,21 | 11,22 | 6,25 | 7,24 | 8,88 |
| Tondelier | 6,47 | 9,15 | 13,20 | 5,59 | 7,38 | 9,90 |
| Glucksmann | 7,07 | 9,46 | 13,34 | 6,65 | 8,48 | 11,07 |
| Le Pen (partiel) | 7,47 | 9,48 | 13,26 | 7,06 | 8,50 | 10,78 |
| Zemmour | 8,02 | 9,81 | 13,60 | 7,59 | 8,65 | 10,56 |
| Lisnard | 7,41 | 10,00 | 14,03 | 6,97 | 8,74 | 10,78 |
| Arthaud (partiel) | 8,20 | 11,54 | 16,53 | 7,04 | 9,17 | 12,15 |
| Roussel | 9,81 | 17,02 | 29,76 | 8,37 | 13,58 | 21,46 |
| Mélenchon | 11,86 | 18,74 | 27,85 | 9,76 | 14,86 | 20,45 |

Lecture (version 1) : seul programme sous le statu quo dans les deux scénarios et les trois années, mais seulement
**0,2 point de mieux en 2032 (prudent)**, loin des 3 % visés.

## Version 2 (18/11/2026, soir) : optimisée sur le comparateur

Même règle que pour les candidats : rien n'est gonflé, chaque ajout reprend un barème ou un encadrement déjà utilisé
pour un autre programme. Effet de chaque étape sur le déficit (écart au statu quo, prudent 2032 / 2037) :

| Étape | 2032 | 2037 |
|---|---:|---:|
| Version 1 | −0,18 | −0,24 |
| + assurance chômage, canal logement (logement neuf ramené au foncier public), rail et électricité ouverts, collectivités en cible principale de la règle de dépense, plan IA | −0,49 | −0,76 |
| + âge légal à 65 ans | −0,60 | −1,01 |
| + successions, jours de carence | −0,66 | −1,09 |
| − plan IA (retiré) | **−0,67** | **−1,11** |

Ce qui ressort :
- **Le plan IA ne paie pas** dans ce modèle : 1 Md€ par an pour +0,2 Md€ au solde en 2037 (prudent). Retiré : le
  « Programme IA » n'a plus de mesure sur l'IA.
- **L'âge légal à 65 ans** est le levier le plus fort (+6,6 Md€ en 2037, plus ≈ 2 Md€ de prélèvements des seniors
  en emploi). C'est aussi le choix le plus contesté : sans lui, le programme reste à −0,56 en 2032 et −0,86 en 2037.
- **Le multiplicateur** coûte plus en version 2 (−3,1 Md€ en 2037) : un resserrement plus fort freine la croissance.
- **3 % reste hors d'atteinte** : en prudent, le statu quo du modèle dérive à 7,2 % en 2032. Il faudrait ≈ 100 Md€
  d'effort en plus, soit des coupes ou des hausses d'impôts bien au-delà de ce qu'aucun programme propose.
- Pas essayé : une règle de trajectoire déclarée (canal `regle_trajectoire`), qui baisserait le déficit publié
  mécaniquement sans dire quelles mesures la portent.

## Ce qui pèse (prudent, Md€ de 2026, + = mieux pour le solde, 2037)

- Gagnent : sous-indexation des pensions (+4,1), niches (+4,0), enveloppe de la règle de dépense (≈ +8,2 au total),
  allègements de charges (+2,9), apprentissage (+1,7).
- Coûtent : enseignants (−3,7, dont 2,1 reviennent en prélèvements), rénovation (−3,4), logement (−2,5),
  crèches (−2,1), accès aux soins (−1,3), justice (−1,2), seniors (−1,1), leasing (−1,1).
- Effets communs : l'effet d'offre (−1,9) et le multiplicateur (−1,8) jouent contre le programme (resserrement et
  coût du travail en hausse).

## Limites

- Montants écrits par Claude à partir d'encadrements cités dans `parametres.yaml`, pas relus par Adrien.
- Microsimulation (OpenFisca) non lancée : pas d'effet par décile.
- Les mesures sans canal dans le noyau (bascule droits de mutation → taxe foncière, permis plus rapides,
  proportionnelle) ne sont pas chiffrées.

## Version 3 (18/11/2026, soir) : « le président choisit »

Dana : « fais tous les choix que tu veux ». La règle a été fixée avant de chiffrer, pour que ce soit le critère qui
choisisse et pas une préférence : **meilleur déficit prudent du simulateur**, avec deux contraintes :
émissions en baisse, petites pensions et minima sociaux intacts.

Gain du retrait de chaque dépense, mesuré une par une (écart de déficit, points de PIB, prudent 2032 / 2037) :
crèches −0,05 / −0,09 ; rénovation −0,05 / −0,09 ; enseignants −0,03 / −0,04 ; accès aux soins −0,02 / −0,04 ;
leasing −0,02 / −0,04 ; seniors −0,02 / −0,02 ; justice −0,01 / −0,02 ; foncier public −0,01 / −0,02.

Choix :
- **retirées** : enseignants, crèches, accès aux soins, justice, seniors, leasing, foncier public (le canal
  logement reste : densification et permis ne coûtent rien) ;
- **gardée** : la rénovation, seule mesure qui fait baisser les émissions (−0,36 Mt en 2037, prudent) ;
- **durcies** : pensions au-dessus de 2 000 € sous-indexées 5 ans au lieu de 3 ; santé en cible principale de la
  règle de dépense ;
- **protégées** : prestations sociales retirées de la règle de dépense (intensité 0), ce qui coûte au solde.

Résultat : 6,29 % en 2032 (prudent), −0,86 point sous le statu quo ; 8,07 % en 2037, −1,44 point ; dette 156 % du
PIB en 2037 (163 % au statu quo).

Ce que le modèle ne voit pas (corrigé le 18/11/2026 au soir, détail dans `docs/manques_simulateur.md`) : il
compte l'effet des enseignants sur les salaires futurs des élèves, mais presque rien avant 2040 (−0,06 point de
déficit en 2073, prudent), et l'effet des crèches sur les naissances, à peine positif en 2073. Il ne compte rien
sur l'emploi des mères, sur la santé ni sur la justice. Le « meilleur programme »
du simulateur est donc d'abord le plus économe : c'est une limite de la mesure, pas un verdict sur ces politiques.
Le multiplicateur le montre aussi : −7,0 Md€ au solde en 2037, le resserrement freine la croissance.
