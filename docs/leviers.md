# Leviers pour améliorer les comptes (29 octobre 2026)

`python -m outils.leviers` (résultats dans `sorties/leviers.json`). Chaque ligne : le programme actuel avec un
seul changement. Prudent, déficit avant clause en % du PIB, écart au programme ; déficit publié 2037 ; dette 2073.

## Décisions d'Adrien du 29 octobre 2026 (intégrées)

- Déduction immédiate de l'investissement : 50 % (atteinte en 2036), puis hausse vers 100 % **conditionnée au
  déficit** : un pas de 5 points chaque année qui suit une année où le déficit du prudent, avant clause, calculé
  sans la hausse, est sous 3 % ; pause sinon. Dans le prudent : 55 % en 2047, pause pendant le pic des
  remboursements de 2047-2052, puis 60 % en 2054 et 100 % en 2063. En crise : 50 % jusqu'au bout.
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

## Capital du fonds : valeur ajoutée brute (correction du 29/10/2026, question d'Adrien)

Le capital du fonds était compté dans les retours économiques (canal « capital du fonds »), mais pour son seul
rendement net (3,2 % dans le prudent). Or la valeur ajoutée d'un capital comprend aussi l'usure (la part qui paie
son renouvellement fait partie du PIB), comme le canal de l'investissement des entreprises la comptait déjà.
Ajouté : usure de 4 % dans le prudent (actifs régulés à longue durée de vie), 5,5 % médian, 6,5 % optimiste.
Effet du canal sur le solde (prudent) : 6,6 Md€ en 2037, 18,4 en 2050, 42,7 en 2073 (environ le double d'avant).

Ce qui reste hors du canal : les investissements publics repris par le fonds (transports, énergie, France 2030,
investissements locaux rentables) sont une économie du budget, pas une production en plus (ils existaient déjà) ;
les retombées au-delà du rendement ne sont comptées que dans le médian et l'optimiste.

## Résultat (prudent)

| Déficit avant clause | 2029 | 2037 | 2050 | 2060 | 2073 | Publié 2037 | Dette 2073 |
|---|---|---|---|---|---|---|---|
| Avant les décisions | 5,68 | 6,03 | 4,75 | 1,96 | 0,62 | 4,10 | 132 % |
| Après les décisions | 5,36 | 5,15 | 4,59 | 1,33 | −0,52 | 3,26 | 112 % |
| Après décisions et trois canaux ajoutés | 5,35 | 5,22 | 5,18 | 2,83 | 1,77 | 3,19 | 145 % |
| **Plus hausse conditionnée et usure du capital du fonds** | **5,35** | **5,06** | **3,85** | **1,31** | **−1,71** | **3,04** | **98 %** |

Ce que pèse chaque correction sur la base actuelle (écart si on la retire, 2037 / 2050 / 2073) : prime de taux
−0,09 / −0,31 / −0,24 (dette 87 % sans elle ; la prime devient négative quand la dette repasse sous son niveau de
2029) ; participation des inactifs +0,04 / +0,07 / +0,18 ; retombées du fonds +0,01 / +0,01 / +0,04 (le prudent
n'en compte pas ; seul le médian, cible de la clause).

## Leviers encore ouverts (base actuelle, rechiffrés)

| Variante | 2037 | 2050 | 2073 | Publié 2037 | Dette 2073 | Naissances |
|---|---|---|---|---|---|---|
| **Programme actuel** | 5,06 | 3,85 | −1,71 | 3,04 | 98 % | −4,6 % |
| Famille : 2e enfant à 25 % du RUI | +0,19 | +0,37 | +0,52 | 3,20 | 108 % | −1,9 % |
| Famille : crèches +20 points (au lieu de +10) | +0,15 | +0,31 | +0,60 | 3,19 | 108 % | −3,2 % |
| Famille : parent isolé à 50 % | +0,28 | +0,45 | +0,72 | 3,28 | 112 % | −0,8 % |
| Retraites : socle annulé à 2 000 € de rente | −0,04 | −0,05 | −0,57 | 3,00 | 91 % | |
| Retraites : accès au socle à 68 ans | 0,00 | 0,00 | −0,47 | 3,04 | 90 % | |
| Retraites : âge légal de l'ancien système à 66 ans | −0,46 | −0,25 | −0,82 | 2,58 | 83 % | |
| Entreprises : déduction gardée à 50 % (pas de hausse) | 0,00 | −0,08 | −0,89 | 3,04 | 85 % | |
| Emploi : sans la baisse du coût employeur | −0,17 | −0,27 | −0,89 | 2,87 | 84 % | |
| RUI à 750 € | −0,23 | −0,30 | −0,67 | 3,04 | 86 % | −5,6 % |
| Épargne obligatoire : 1 point sur 10 versé à l'État | −0,29 | −0,40 | −0,83 | 2,75 | 82 % | |
| Sans la prime de taux liée à la dette | −0,09 | −0,31 | −0,24 | 2,99 | 87 % | |
| Sans la participation des inactifs | +0,04 | +0,07 | +0,18 | 3,07 | 101 % | |
| Sans les retombées du capital du fonds | +0,01 | +0,01 | +0,04 | 3,04 | 98 % | |
| Paquet : âge légal 66 ans + 1 point d'épargne à l'État | −0,74 | −0,58 | −1,47 | 2,31 | 70 % | |
| Paquet + 2e enfant à 25 % | −0,55 | −0,30 | −1,19 | 2,49 | 78 % | −1,9 % |
