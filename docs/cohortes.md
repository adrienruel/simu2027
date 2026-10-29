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

## Ce qui reste à faire

1. Indépendants dans les cellules ; profils de salaire par génération ; couples de l'enquête la plus récente.
2. Les points pris par la règle et l'épargne rendue dans les comptes eux-mêmes (aujourd'hui dans le capital
   seulement) ; le remboursement de 35 % dans les comptes.
3. **Scénario sans réforme** (système actuel projeté), puis bibliothèque de mesures pour d'autres programmes.
