# Effets économiques communs : demande et offre, instrument par instrument (6 novembre 2026)

Pour tous les programmes chiffrés sur le noyau (Bertrand, Zemmour, Arthaud, Tondelier). Écologie de droite garde son
moteur, qui a déjà ses propres canaux (participation des inactifs, coût du travail par tranche, cohortes d'entreprises,
localisation des bénéfices).

```
moteur/offre.py ; paramètres : parametres/commun/economie.yaml, groupes offre, demande et seniors ;
tests : tests/test_offre.py
```

## Pourquoi

- **Avant** : un seul multiplicateur (1 en prudent) sur le coût net des mesures, quel qu'il soit, et aucun effet
  durable. Une baisse de CSG relançait autant qu'une dépense publique, puis l'effet s'effaçait.
- **Cohortes d'entreprises** : elles calculent bien l'investissement par taille et la localisation, mais seulement
  dans le moteur d'Écologie de droite. Le statu quo et les autres programmes n'y passaient pas : ils n'avaient pas
  d'effet de croissance du tout. Le canal des entreprises utilise désormais la même élasticité de l'investissement
  (macro.elasticite_invest) : un seul paramètre pour les deux moteurs.

## Demande : un multiplicateur par instrument

Chaque mesure entre dans l'impulsion budgétaire avec un poids relatif à la dépense publique (demande.poids), d'après
les comparaisons de modèles de la zone euro (Kilponen et al., BNB WP 278, 2015 : consommation publique 0,5 à 0,98 la
première année ; impôt sur le travail 0,04 à 0,51 ; impôt sur le capital 0,02 à 0,65 ; consommation 0,14 à 0,72 ;
Coenen et al., AEJ Macro, 2012, pour les transferts).

| Dépense | Transferts ciblés | Pensions | Travail | Coût du travail | TVA, accises | Entreprises | Capital des ménages | Successions | Autres recettes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0,8 | 0,6 | 0,4 | 0,4 | 0,55 | 0,3 | 0,2 | 0,1 | 1 |

« Autres recettes » : prélèvements sans instrument (sur les rémunérations publiques, les pensions, le SMIC), qui
suivent la dépense dont ils sont la contrepartie.

## Offre : effet durable, instrument par instrument

- **Travail, par cellule de salaire** (OpenFisca 2026, distributions de salaires du privé et du public) : la mesure
  est répartie entre cellules selon son incidence (proportionnelle aux prélèvements ; à l'impôt sur le revenu ; aux
  bas salaires ; aux hauts revenus ; aux salaires de 1,6 à 3,5 SMIC pour les allègements ; au-dessus du plafond de la
  Sécurité sociale) ; chaque cellule réagit à son revenu net en plus avec l'élasticité de participation de sa tranche
  (plus forte en bas : Immervoll et al., 2007 ; Bargain, Orsini et Peichl, 2014) et celle des heures. Effet sur le PIB
  : travail en plus pondéré par le coût × part du travail (0,65 à capital inchangé en prudent, 1 en optimiste quand le
  capital suit). Pour 1 point de PIB : +0,3 % de PIB en prudent (0,34 sur les bas salaires, 0,25 sur les hauts
  revenus), +0,65 % en médian, +1,5 % en optimiste.
- **Entreprises** : élasticité de l'investissement au coût du capital des cohortes (Mésange, OFCE), coût du capital
  (1 − τz)/(1 − τ), part du capital 0,35 : ≈ +0,45 % de PIB pour 1 point de PIB d'IS en moins.
- **Coût du travail** (Mésange), **capital des ménages**, **successions**, **TVA**, **transferts aux actifs** :
  élasticités de long terme sourcées dans economie.yaml.
- Baisse : élasticité du scénario ; hausse : scénario miroir (prudent ↔ médian, crise ↔ optimiste). Montée de
  Mésange (≈ 10 % de l'écart par an).

## Emploi des seniors quand l'âge de la retraite change

Les personnes pas encore retraitées en plus (calcul génération par génération, même profil que les pensions) se
répartissent, d'après la réforme de 2010, entre emploi, chômage et inactivité (seniors.devenir) :

| | Emploi | Chômage | Inactivité | Source |
|---|---|---|---|---|
| Crise | 45 % | 30 % | 25 % | Rabaté et Rochut (JPEF, 2020) : 21 points d'emploi pour 48 de retraités en moins |
| Prudent | 50 % | 25 % | 25 % | IPP, rapport n° 61 (2025) : la moitié en emploi, un quart au chômage indemnisé |
| Médian | 55 % | 25 % | 20 % | |
| Optimiste | 64 % | 28 % | 8 % | Koubi et Dubois (Insee), Trésor-Éco n° 302 (2022) |

Chaque emploi rapporte des prélèvements (27 000 €) et de la valeur ajoutée (75 000 €) ; chaque chômeur coûte une
allocation (16 000 €), chaque inactif des prestations (9 000 €, invalidité et minima). Un âge abaissé (Tondelier)
prend le scénario miroir. Un an de plus (65 ans) : ≈ 575 000 personnes pas encore retraitées à terme, dont la moitié en
emploi en prudent.

## Résultats (2037, sauf 2029)

Solde primaire contre le statu quo (points de PIB) ; PIB contre le statu quo ; emplois en plus (milliers), dont
seniors ; PIB qu'il faudrait encore en plus pour rejoindre le solde primaire du statu quo.

| Programme | Scénario | Solde 2029 | Solde 2037 | PIB | Chômage : programme / statu quo | Emplois | dont seniors | PIB encore nécessaire | Déficit : programme / statu quo |
|---|---|---|---|---|---|---|---|---|---|
| Zemmour (avec Knafo) | crise | −3,2 | −3,1 | +0,8 % | 11,5 / 10,3 | +99 | +272 | +6,0 % | 18,1 / 12,3 |
| | prudent | −3,1 | −2,3 | +1,6 % | 9,2 / 8,3 | +257 | +302 | +4,5 % | 13,7 / 9,7 |
| | médian | −2,7 | −1,0 | +3,4 % | 8,5 / 8,3 | +614 | +333 | +2,0 % | 10,2 / 8,5 |
| | optimiste | −1,9 | +1,1 | +7,0 % | 7,4 / 8,3 | +1 267 | +387 | −2,2 % | 6,7 / 8,2 |
| Tondelier | crise | −1,3 | −4,6 | −4,0 % | 12,9 / 10,3 | −1 936 | −810 | +8,8 % | 19,8 / 12,3 |
| | prudent | −0,9 | −3,3 | −3,0 % | 9,9 / 8,3 | −1 472 | −696 | +6,4 % | 14,6 / 9,7 |
| | médian | −0,1 | −1,9 | −2,3 % | 8,7 / 8,3 | −1 023 | −633 | +3,6 % | 11,1 / 8,5 |
| | optimiste | +0,3 | −0,7 | −2,0 % | 7,7 / 8,3 | −666 | −569 | +1,3 % | 9,1 / 8,2 |
| Bertrand | prudent | −0,0 | +0,3 | +0,5 % | 8,6 / 8,3 | +183 | +197 | aucun | 9,3 / 9,7 |
| | optimiste | +0,1 | +0,7 | +1,2 % | 8,5 / 8,3 | +400 | +329 | aucun | 7,2 / 8,2 |
| Arthaud (partiel) | prudent | −0,9 | −1,8 | −2,2 % | 13,4 / 8,3 | −1 623 | 0 | +3,4 % | 12,7 / 9,7 |

Lecture :
- **Demande** : la baisse de la CSG relance beaucoup moins qu'avant les premières années (poids 0,4 au lieu de 1) :
  Zemmour perd l'essentiel de sa relance de 2029 (−3,1 points de solde au lieu de −2,1). Tondelier, qui dépense
  plus qu'il ne baisse d'impôts, change peu en 2029 (−0,9 au lieu de −0,8).
- **Offre** : Zemmour gagne +1,6 % de PIB en prudent en 2037 (travail, seniors), +7 % en optimiste ; Tondelier perd
  3 % (SMIC, retour à 62 ans, hausses de prélèvements).
- **Seniors** : 65 ans rapporte environ 300 000 emplois et 7 à 11 Md€ nets par an (prélèvements moins allocations) ;
  62 ans en coûte environ 700 000 et 11 Md€.
- Le programme de Zemmour ne s'autofinance que dans l'optimiste ; en prudent, il faudrait encore 4,5 % de PIB.

## Limites

1. L'offre de travail passe par les cellules de salaire avec un revenu net calculé par OpenFisca, mais pour une
   personne seule ; les couples (où la participation des femmes réagit le plus) ne sont pas encore représentés.
2. L'incidence d'une mesure entre cellules est une forme simple (proportionnelle, impôt sur le revenu, bas, hauts
   revenus…) ; une vraie microsimulation de chaque réforme dans OpenFisca reste à faire.
3. Seniors : le nombre de personnes pas encore retraitées vient du profil de départ par âge du modèle (≈ 575 000
   pour un an de plus) ; à recouper avec les évaluations de la réforme de 2023 (DREES, COR) avant publication.
4. Pas d'effet des dépenses publiques sur l'offre (éducation, investissement public) au-delà du multiplicateur.
