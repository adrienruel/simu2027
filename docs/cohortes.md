# Cellules de ménages et comptes d'épargne (29 octobre 2026)

`moteur/cohortes.py`, tests `tests/test_cohortes.py`. Première étape de la simulation dynamique demandée par
Adrien (« pousser la simulation au maximum ») ; la version précédente reste disponible (`cohortes.active` : non).

## Ce qui est calculé chaque année (2026-2073)

- **Salariés par âge (18-69 ans) et par tranche de salaire** : population de l'Insee × taux d'emploi par âge ×
  part des salariés (calculée : 0,92) ; 35 tranches de coût du privé et du public de 2026 ; coût multiplié par le
  profil de salaire par âge de l'Insee (2024 : de 0,59 du salaire moyen avant 25 ans à 1,20 après 55 ans).
- **Pour chaque cellule** : impôt unique, impôt local, part de RUI gardée, consommation, TVA, épargne obligatoire
  et volontaire (mêmes fonctions que le budget statique). Calage vérifié : en 2026, les cellules retrouvent l'impôt
  (595 contre 593 Md€), la TVA (97,4) et l'épargne obligatoire (69 contre 70 Md€) du budget statique.
- **Ce qui en sort** : l'impôt, la TVA et le RUI des salariés, et le flux d'épargne versé au fonds, suivent les
  cellules au lieu du seul nombre de personnes en emploi.
- **Comptes d'épargne par génération et par tranche** (générations de 22 à 49 ans en 2029) : chaque année d'emploi
  verse son épargne obligatoire, capitalisée au rendement du fonds ; à 67 ans, rente et socle de chaque tranche.
  Une part de chaque génération (taux d'emploi moyen de 25 à 64 ans, 78 %) fait carrière ; l'autre n'a pas de
  capital et touche le socle plein (au lieu d'un taux d'emploi de carrière moyen appliqué à tous, qui
  sous-estimait le socle de ceux qui n'ont pas travaillé).

## Effet de composition (hypothèse)

Des actifs plus âgés gagnent plus en moyenne. La croissance de la productivité retenue (0,7 %, COR) est une
moyenne par actif qui contient déjà une partie de cet effet : dans le prudent et la crise, il est retiré (le
salaire moyen suit la tendance seule ; restent la progressivité de l'impôt et le socle par cellule) ; il est
gardé dans le médian et l'optimiste (`cohortes.effet_composition_salaires`).

## Effet sur les résultats (prudent)

| | 2037 avant clause | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|
| Sans cellules | 4,38 % | 3,86 % | −1,23 % | 92 % |
| Avec cellules | 4,40 % | 3,80 % | −1,43 % | 89 % |

Correction faite en passant : l'emploi du module de population comptait les 15-17 ans au taux des 15-24 ans
(34,5 %) ; il commence désormais à 18 ans, comme les cellules.

## Le fonds comme somme des comptes (deuxième étape)

`cohortes.comptes` : comptes de toutes les générations qui travaillent après 2029 (y compris celles de l'ancien
système, qui épargnent aussi). Avant 67 ans, versements des salariés (cellules) capitalisés au rendement du fonds ;
à 67 ans, la moitié du capital part en rente viagère (prix de la rente : mortalité de Gompertz), l'autre reste
placée et verse ses rendements ; au décès, elle passe aux héritiers et reste placée. Encours : 605 Md€ en 2037,
1 780 en 2050, 3 780 en 2073 ; rentes versées : 16 Md€ en 2050, 87 en 2073.

Capital nouveau du fonds (canal macro) : apport net de l'année (versements − investissements publics repris, après
éviction et part placée à l'étranger) + rendements gardés moins rentes versées, au prorata de la part des comptes
placée en capital nouveau. Remplace l'ancienne règle « 62,5 % des rendements réinvestis », qui ne voyait pas la
décumulation. Capital nouveau : 414 Md€ en 2050, 1 466 en 2073.

## Impôt et TVA des nouveaux retraités par profil (troisième étape)

`cohortes.fiscalite_retraites_nouveaux` : rente et socle de chaque profil (tranches de ceux qui ont fait carrière,
et ceux sans capital), mêmes règles que le budget de croisière. Résultat très proche de l'ancienne approximation
(croisière au prorata du nombre de retraités) : 24,0 contre 25,8 Md€ d'impôt et 43,7 contre 44,0 Md€ de TVA en 2073.

## Ménages : couples et enfants (quatrième étape)

`cohortes.menages` : couples d'âge actif (20 à 66 ans) chaque année, à partir de la population de l'Insee et de la
part des personnes en couple par âge (recensement de 2006, forme seulement ; niveau calé sur les 7 millions de
couples du quotient conjugal en 2026). Part des couples à un seul revenu : emploi des conjoints supposé
indépendant (prudent : plus de couples à un revenu), calée sur 25 % en 2026. Le quotient conjugal suit les couples
pondérés par leur gain (9 900 € à un revenu, 500 € à deux), le quotient familial suit les enfants, l'économie sur le
RUI du conjoint suit les personnes sans emploi en couple (au lieu de la population totale) : −2 Md€ de dépenses
en 2050, −5 Md€ en 2073 (moins d'enfants et de couples d'âge actif).

## Réformes du supérieur : carrières (cinquième étape)

`moteur/carrieres.py`, paramètres `carrieres.*`. Réformes : sélection à l'université, apprentissage et alternance,
RUI étudiant sous condition, prépas et écoles facturées. Leurs coûts et économies sont déjà au budget ; le module
ajoute leurs effets sur les carrières.

| Effet | Ce qui est retenu | Crise | Prudent | Médian | Optimiste |
|---|---|---|---|---|---|
| Entrée plus tôt dans l'emploi | 48 000 années d'études en moins par an (3 % de 1,6 million, déjà au budget), de 19 à 23 ans ; part en emploi (Céreq, Génération 2017 : 63 % des bacheliers généraux, 38 % des non-diplômés, trois ans après la sortie) | 38 % | 50 % | 63 % | 63 % |
| Meilleur emploi des jeunes | Déjà dans le bloc emploi (« sélection et apprentissage », « alternance », en points de chômage) : rien n'est ajouté | — | — | — | — |
| Moins de décrochage | Points d'une génération qui obtiennent une licence au lieu de sortir sans diplôme ; aucune estimation causale (SIES 2023 : la hausse du passage en L2 après la loi ORE tient surtout à la crise sanitaire) | 0 | 0 | 1 | 3 |
| Salaires plus élevés | Moitié de l'écart licence − bac général du Céreq (+14,7 %), pour les générations nées à partir de 2011, dès 22 ans ; l'emploi lié au diplôme n'est pas ajouté (canal « sélection » du bloc emploi) | 0 | 0 | +0,07 % par génération | +0,22 % |

Les jeunes entrés plus tôt s'ajoutent aux cellules de salariés (impôt, TVA, épargne au salaire de leur âge) et à
l'indice d'emploi du PIB, pondérés par leur salaire relatif (0,59 du salaire moyen). Les indices sont rapportés à
2029 sans ces effets, pour que l'effet présent dès 2029 ne soit pas effacé. Pas d'effet compté : apprentissage sur
les salaires (pas d'estimation causale ; Cart et Léné, 2014, ne trouvent pas d'écart de salaire à l'embauche) ;
prépas facturées (moins d'inscrits possible, effet inconnu).

Effet, prudent : 24 000 emplois en plus à partir de 2031 ; déficit avant règle −0,01 point en 2029, −0,03 en 2037
et 2050, −0,08 en 2073 ; dette de 2073 −1 point.

## Ce qui reste à faire

1. Indépendants dans les cellules ; profils de salaire par génération ; couples de l'enquête la plus récente.
2. Les points pris par la règle et l'épargne rendue dans les comptes eux-mêmes (aujourd'hui dans le capital
   seulement) ; le remboursement de 35 % dans les comptes.
3. **Scénario sans réforme** (système actuel projeté), puis bibliothèque de mesures pour d'autres programmes.
