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

## Décisions du 29 octobre 2026 (après la première version)

- **RUI à 25 % par enfant dès le 3e** (15 % pour les deux premiers ; parent isolé : 30 %, inchangé). Coût
  1,6 Md€ par an (1 696 600 enfants de rang 3 ou plus, Insee RP 2023, tous comptés au taux des couples).
- **Crèches : +10 points de couverture des moins de 3 ans** (≈ 160 000 places en 2034, selon les naissances),
  dès 2030, montée en 5 ans : ≈ 3 Md€ par an de fonctionnement (19 450 € par place, Onape, payés entièrement par
  l'État), plus la construction (42 000 € par place, une fois) ; 4,5 Md€ en 2034. Effet sur les naissances :
  +1,4 % dans le prudent (moitié de l'estimation allemande), +2,8 % en médian et optimiste, 0 en crise. Ni les
  emplois des crèches ni le retour à l'emploi des mères ne sont comptés (prudent).
- Soutien moyen par enfant : 601 € de moins que le système actuel (762 avant) ; naissances −4,6 % dans le
  prudent (−7,6 avant). Reste défavorable : le 2e enfant et les parents isolés.

## Pensions de l'ancien système, génération par génération

`moteur/ancien_systeme.py`. Générations nées en 1978 ou avant (les plus jeunes sont remboursées et relèvent du
nouveau système). Survivants : population de l'Insee ; part partie à la retraite à chaque âge (âge légal de 64
ans, profil DREES 2023 décalé, hypothèse encadrée) ; pension identique en 2029, 0,935 de la moyenne pour les
départs suivants (DREES : nouveaux retraités 1 557 €, ensemble 1 666 €), gelée en euros courants. Calée sur
428 Md€ et 19,15 millions de retraités en 2029.

| | 2029 | 2037 | 2050 | 2060 | 2073 |
|---|---|---|---|---|---|
| Dépenses, série de la v235 (Md€) | 428 | 392 | 271 | 154 | 89 |
| Dépenses par génération (Md€) | 428 | 413 | 244 | 105 | 12 |
| Retraités, v235 (millions) | 19,2 | 20,5 | 17,2 | 10,6 | 6,7 |
| Retraités par génération (millions) | 19,2 | 21,2 | 15,2 | 7,6 | 1,1 |

La série de la v235 gardait 6,7 millions de retraités de l'ancien système en 2073, alors que les générations nées
en 1978 ou avant auront 95 ans ou plus : c'était le complément entre le total du COR et les retraités du nouveau
système. Ce complément venait en fait d'un défaut du nouveau système, qui ne comptait ni les arrivées après 2029
ni la mortalité de l'Insee : **retraités touchant le socle en 2073 : 18,5 millions au lieu de 15,0 ; socle versé :
227 Md€ au lieu de 184.** Les deux corrections vont en sens contraire.

Question ouverte (paramètre `ancien_systeme.droits_geles_des_2029`) : les départs de 2029 à 2043 touchent-ils une
pension calculée normalement puis gelée (retenu, prudent), ou des droits gelés dès 2029 ? Le gel dès 2029
réduirait le déficit de 0,2 point en 2037 et de 0,7 point en 2050.

## Résultat d'ensemble (prudent)

| Déficit avant clause | 2029 | 2037 | 2050 | 2060 | 2073 | Dette 2073 |
|---|---|---|---|---|---|---|
| Population figée (v235) | 5,69 | 5,55 | 4,13 | 0,0 | −4,2 | 64 % |
| Population, première version | 5,69 | 5,50 | 4,87 | 2,9 | 3,2 | 155 % |
| **Avec 3e enfant, crèches, ancien système et socle par génération** | **5,74** | **6,25** | **4,63** | **1,9** | **0,6** | **132 %** |

Publié (après clause) : 5,34 % en 2029, 4,31 % en 2037, 4,75 % en 2050.

## Limites

- Santé : la trajectoire est déjà calée sur des projections qui comptent le vieillissement ; pas de second compte.
- Le système actuel souffrirait davantage de la même démographie (répartition) : la comparaison avec le statu
  quo reste à faire.
