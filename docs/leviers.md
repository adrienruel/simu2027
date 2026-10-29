# Leviers pour améliorer les comptes (29 octobre 2026)

`python -m outils.leviers` (résultats dans `sorties/leviers.json`). Chaque ligne : le programme actuel avec un
seul changement. Prudent, déficit avant clause en % du PIB, écart au programme ; déficit publié 2037 ; dette 2073.

## Décisions d'Adrien du 29 octobre 2026 (intégrées)

- Déduction immédiate de l'investissement : 50 % (atteinte en 2036), puis hausse vers 100 % de 2040 à 2049
  (calendrier proposé, à confirmer).
- Socle à 1 200 € (au lieu de 1 300).
- Baisse du coût employeur jusqu'à 1,3 SMIC : 2,5 % (au lieu de 5 %).

## Canaux ajoutés le même jour (corrections)

- **Prime de taux liée à la dette** : +3 points de base de taux long par point de dette/PIB au-dessus du niveau de
  2029 dans le prudent (CBO 2019 : 2 à 3 ; Laubach 2009 : 2,1 à 3,5), transmise au taux apparent au rythme du
  renouvellement de la dette (8,5 ans, AFT). Crise 3,5 ; médian 2 ; optimiste 1,5.
- **Participation des inactifs** : le nouveau système fait garder davantage en prenant un emploi (mi-temps au
  SMIC : 59 % gardé au lieu de 36 % aujourd'hui, OpenFisca contre moteur). Élasticité 0,1 dans le prudent (0,2
  médian, 0,3 optimiste, 0 en crise) appliquée aux 1,93 million de personnes du halo du chômage : 59 000
  emplois dans le prudent.
- **Retombées du capital du fonds** : 1 % par an du capital en PIB en plus dans le médian, 2 % en optimiste,
  rien dans le prudent et la crise (Bom et Ligthart, 2014).
- Défaut corrigé avant : la contribution de transition (part de l'épargne obligatoire versée à l'État) est
  comptée en recette.

## Résultat (prudent)

| Déficit avant clause | 2029 | 2037 | 2050 | 2060 | 2073 | Publié 2037 | Dette 2073 |
|---|---|---|---|---|---|---|---|
| Avant les décisions | 5,68 | 6,03 | 4,75 | 1,96 | 0,62 | 4,10 | 132 % |
| Après les décisions | 5,36 | 5,15 | 4,59 | 1,33 | −0,52 | 3,26 | 112 % |
| **Après décisions et corrections** | **5,35** | **5,22** | **5,18** | **2,83** | **1,77** | **3,19** | **145 %** |

Ce que pèse chaque correction (écart au programme actuel si on la retire) : prime de taux −0,11 en 2037,
−0,63 en 2050, −2,36 en 2073 (dette 111 % sans elle) ; participation des inactifs +0,04 / +0,07 / +0,29 ;
retombées du fonds +0,01 / +0,01 / +0,06 (le prudent n'en compte pas ; seul le médian, cible de la clause).

## Leviers encore ouverts (sur la base actuelle)

| Variante | 2037 | 2050 | 2073 | Publié 2037 | Dette 2073 | Naissances |
|---|---|---|---|---|---|---|
| **Programme actuel** | 5,22 | 5,18 | 1,77 | 3,19 | 145 % | −4,6 % |
| Famille : 2e enfant à 25 % du RUI | +0,19 | +0,38 | +0,92 | 3,36 | 159 % | −1,9 % |
| Famille : crèches +20 points (au lieu de +10) | +0,16 | +0,32 | +1,00 | 3,35 | 159 % | −3,2 % |
| Famille : parent isolé à 50 % | +0,28 | +0,56 | +1,42 | 3,43 | 166 % | −0,8 % |
| Retraites : socle annulé à 2 000 € de rente | −0,04 | −0,14 | −0,86 | 3,15 | 136 % | |
| Retraites : accès au socle à 68 ans | 0,00 | −0,10 | −0,80 | 3,19 | 134 % | |
| Retraites : âge légal de l'ancien système à 66 ans | −0,46 | −0,36 | −1,41 | 2,75 | 125 % | |
| Entreprises : déduction gardée à 50 % (pas de hausse) | 0,00 | −0,81 | −1,96 | 3,19 | 118 % | |
| Emploi : sans la baisse du coût employeur | −0,17 | −0,36 | −1,41 | 3,02 | 127 % | |
| RUI à 750 € | −0,23 | −0,40 | −1,18 | 3,19 | 128 % | −5,6 % |
| Épargne obligatoire : 1 point sur 10 versé à l'État | −0,31 | −0,59 | −1,86 | 2,90 | 119 % | |
| Paquet : âge légal 66 ans + 1 point d'épargne à l'État | −0,77 | −0,93 | −2,94 | 2,48 | 101 % | |
| Paquet + 2e enfant à 25 % | −0,58 | −0,57 | −2,40 | 2,65 | 112 % | −1,9 % |

Avec la prime de taux, chaque dépense en plus coûte davantage à long terme (la dette porte intérêt plus cher) :
les mesures familiales qui s'autofinançaient presque en 2073 ne le font plus.
