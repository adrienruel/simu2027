# Population année par année (29 octobre 2026)

`moteur/demographie.py`, données `parametres/donnees/population_insee_2026_*.csv` (convertisseur
`outils/population_insee.py`), soutien par enfant `outils/valeur_enfant.py`.

## Ce que fait le module

- **Population par âge** de 2026 à 2070 : projections de l'Insee de juin 2026 (Insee Première n° 2108).
  Fécondité basse (1,20) en crise, centrale (1,45) en prudent et médian, haute (1,70) en optimiste ; solde
  migratoire +150 000 par an. 2071-2073 prolongés par la tendance de 2065-2070.
- **Emploi** = population par âge × taux d'emploi par âge de 2025 (Insee, Dares, COR), figés : la démographie
  seule. Les recettes, le PIB de référence et l'épargne versée au fonds suivent cet emploi.
- **RUI** : part des adultes selon les 18-64 ans, compléments selon les enfants. **Autres dépenses** : selon la
  population totale.
- **Écart entre scénarios** : la trajectoire suit la démographie du prudent ; les autres scénarios ajoutent un
  canal « démographie » (écart au prudent).

## Effet du programme sur la natalité

Soutien par enfant (revenu disponible avec un enfant de plus), législation 2026 par OpenFisca contre nouveau
système : le nouveau système verse le même montant pour chaque enfant (15 % du RUI et la demi-part plafonnée).
Mieux pour le premier enfant des couples qui travaillent, nettement moins bien pour le troisième.
Moyenne pondérée (rang 1 : 44 %, Insee ; rangs 2 et 3 : 35 et 21 %, hypothèse ; parent isolé 20 % des
ménages, hypothèse) : **762 € de moins par enfant et par an.**

Semi-élasticité (naissances pour 100 € par an de soutien) : crise 2 %, prudent et médian 1 %, optimiste
0,5 % (Espagne : +3 % de naissances pour 2 500 € à la naissance ; Israël : −7,5 % pour ≈ 400 € par an de
moins ; une grande part est un effet de calendrier). **Naissances : −7,6 % dans le prudent** (−3,8 % à −15,2 %),
pour les générations nées à partir de 2030. Crèches : aucun effet (la mesure finance les places existantes).

## Résultats

Déficit avant clause, en % du PIB (publié entre parenthèses quand il diffère), et dette en 2073 :

| Prudent | 2029 | 2037 | 2050 | 2060 | 2073 | Dette 2073 |
|---|---|---|---|---|---|---|
| Sans démographie (avant) | 5,69 (5,28) | 5,55 (3,64) | 4,13 (4,24) | −0,01 | −4,24 | 64 % |
| Avec démographie, natalité neutre | 5,69 (5,28) | 5,58 (3,67) | 5,03 (5,15) | 2,79 | 2,21 | 147 % |
| **Avec démographie et effet sur la natalité** | 5,69 (5,28) | 5,50 (3,60) | 4,87 (4,99) | 2,87 | 3,16 | **155 %** |

Personnes en emploi (prudent) : 29,9 millions en 2029, 25,1 millions en 2073 (−16 %). La population en âge de
travailler baisse avec une fécondité de 1,45 : c'est la projection de l'Insee, pas un effet du programme.
L'effet du programme sur la natalité allège le budget jusque vers 2060 (moins d'enfants à soutenir), puis
l'alourdit (moins d'actifs).

## Limites

- Santé : la trajectoire est déjà calée sur des projections qui comptent le vieillissement ; pas de second compte.
- Pensions de l'ancien système : série de la v235. Recoupée : retraités du COR +17,6 % de 2029 à 2060, 63 ans
  ou plus de l'Insee +22 % (l'âge de départ qui monte explique l'écart) ; pas recalculée génération par génération.
- Le système actuel souffrirait davantage de la même démographie (répartition) : la comparaison avec le statu
  quo reste à faire.
