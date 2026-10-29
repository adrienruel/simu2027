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

## Ce qui reste à faire (prochaines étapes)

1. **Le fonds comme somme des comptes** : aujourd'hui, le capital du fonds (canal macro) et les comptes (socle)
   sont deux calculs séparés ; le capital du fonds ne baisse pas quand les retraités tirent leur rente
   (décumulation non comptée, ce qui le surestime après 2046).
2. **Les retraités du nouveau système par cellule** : impôt et TVA calculés sur leur rente et leur socle (encore
   le budget de croisière ramené au nombre de retraités).
3. **Ménages** (couples, enfants) et quotient ; indépendants ; profils de salaire par génération.
4. **Scénario sans réforme** (système actuel projeté), puis bibliothèque de mesures pour d'autres programmes.
