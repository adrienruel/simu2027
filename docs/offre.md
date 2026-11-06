# Effets économiques communs : demande, offre et seniors (6 novembre 2026)

Pour tous les programmes chiffrés sur le noyau (Bertrand, Zemmour, Arthaud, Tondelier). Écologie de droite garde son
moteur, qui a déjà ses propres canaux (participation des inactifs, coût du travail par tranche, cohortes d'entreprises,
localisation des bénéfices).

```
moteur/offre.py ; outils/openfisca_offre.py (tables OpenFisca) ; paramètres : parametres/commun/economie.yaml,
groupes offre, demande et seniors ; tests : tests/test_offre.py
```

## Pourquoi

- **Avant** : un seul multiplicateur (1 en prudent) sur le coût net des mesures, quel qu'il soit, et aucun effet
  durable. Une baisse de CSG relançait autant qu'une dépense publique, puis l'effet s'effaçait.
- **Cohortes d'entreprises** : elles calculent l'investissement par taille et la localisation, mais seulement dans le
  moteur d'Écologie de droite. Le statu quo et les autres programmes n'avaient pas d'effet de croissance du tout. Le
  canal des entreprises utilise désormais la même élasticité de l'investissement (macro.elasticite_invest).

## Demande : un multiplicateur par instrument

Chaque mesure entre dans l'impulsion budgétaire avec un poids relatif à la dépense publique (demande.poids), d'après
les comparaisons de modèles de la zone euro (Kilponen et al., BNB WP 278, 2015 ; Coenen et al., AEJ Macro, 2012).

| Dépense | Transferts ciblés | Pensions | Travail | Coût du travail | TVA, accises | Entreprises | Capital des ménages | Successions | Autres recettes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0,8 | 0,6 | 0,4 | 0,4 | 0,55 | 0,3 | 0,2 | 0,1 | 1 |

## Offre : effet durable, instrument par instrument

### Travail : OpenFisca, personnes seules et couples

`outils/openfisca_offre.py` calcule avec OpenFisca-France (législation 2026), sur toute la grille de salaires, le
revenu disponible d'une personne seule et d'un ménage en couple (marié, un enfant, conjoint à 30 000 € brut ; le salaire
de la grille est celui du second apporteur), dans le système actuel et pour chaque réforme du travail des programmes :

| Réforme OpenFisca | Programmes | Impôts en moins (Md€, statique) | Prestations en plus (Md€) |
|---|---|---|---|
| CSG supprimée sur les revenus d'activité | Zemmour | 83,3 | −7,5 |
| CSG déductible +1 point sur les revenus d'activité | Tondelier (COT-04) | −8,4 | +1,0 |
| Tranche à 11 % de l'impôt sur le revenu ramenée à 9 % | Bertrand, Tondelier | 7,9 | 0 |
| Tranche à 60 % au-delà de 250 000 € par part | Tondelier | −0,7 | 0 |

Pour chaque cellule de salaire (distributions de 2026, privé et public) : variation du **gain à travailler** (revenu
disponible en emploi moins sans emploi : participation) et du **taux de revenu net marginal** (heures), pour une
personne seule et pour un second apporteur en couple (60 % des salariés, élasticité 1 à 1,5 fois plus forte : Bargain,
Orsini et Peichl, 2014). Élasticités de participation au gain à travailler par tranche de salaire (plus fortes en bas,
Immervoll et al., 2007), calées pour que la suppression de la CSG donne, par point de PIB, 0,26 % de PIB en crise,
0,44 % en prudent, 0,69 % en médian et 1,1 % en optimiste (Bassanini et Scarpetta, OCDE, 2001 : 0,3 effet direct,
0,6 à 0,7 avec l'investissement). L'effet est rapporté aux impôts en moins, comme les montants des mesures.

Les autres mesures du travail (cotisations, allègements, épargne salariale, niches) gardent une incidence simple
(proportionnelle aux prélèvements, entre 1,6 et 3,5 SMIC, au-dessus du plafond de la Sécurité sociale…).

**Correction trouvée en passant** : supprimer la CSG fait baisser la prime d'activité, le RSA et les aides au logement
(le salaire net monte) : ≈ 7,5 Md€ d'économie que le chiffrage de Zemmour ne comptait pas ; symétriquement, la hausse
de CSG de Tondelier les fait monter (≈ 1 Md€). Les deux sont désormais des mesures.

### Entreprises et autres instruments

- Entreprises : élasticité de l'investissement au coût du capital des cohortes, coût du capital (1 − τz)/(1 − τ),
  part du capital 0,35 : ≈ +0,45 % de PIB pour 1 point de PIB d'IS en moins.
- Coût du travail (Mésange), capital des ménages, successions, TVA, transferts aux actifs : élasticités sourcées dans
  economie.yaml.
- Baisse : élasticité du scénario ; hausse : scénario miroir (prudent ↔ médian, crise ↔ optimiste). Montée de
  Mésange (≈ 10 % de l'écart par an).

## Emploi des seniors quand l'âge de la retraite change

Les personnes pas encore retraitées en plus viennent du profil de départ par âge décalé, génération par génération,
puis :

- **Part concernée : 0,4**, calée sur l'étude d'impact de la réforme de 2023 (deux ans d'âge : +300 000 emplois,
  +84 000 allocataires du chômage, +60 000 de minima sociaux, DARES) : les carrières longues, l'invalidité,
  l'inaptitude et les départs au taux plein à 67 ans gardent leur âge. Sans ce calage, le modèle comptait deux fois
  trop de seniors.
- **Devenir** (réforme de 2010) : prudent 50 % en emploi, 25 % au chômage (IPP, 2025) ; optimiste 64 % et 28 % (Insee,
  Trésor-Éco n° 302) ; crise 45 % et 30 % (Rabaté et Rochut, 2020). Âge abaissé : scénario miroir.
- Chaque emploi : 27 000 € de prélèvements, 75 000 € de valeur ajoutée ; chaque chômeur : 16 000 € d'allocation ;
  chaque inactif : 9 000 € de prestations.

Contrôle : deux ans d'âge (retour à 62 ans) font perdre ≈ 280 000 emplois en prudent, 230 000 à 320 000 selon le
scénario, autour des 300 000 de l'étude d'impact.

## Résultats (2037, sauf 2029)

Solde primaire contre le statu quo (points de PIB) ; PIB contre le statu quo ; emplois en plus (milliers), dont
seniors ; PIB qu'il faudrait encore en plus pour rejoindre le solde primaire du statu quo.

| Programme | Scénario | Solde 2029 | Solde 2037 | PIB | Chômage : programme / statu quo | Emplois | dont seniors | PIB encore nécessaire | Déficit : programme / statu quo |
|---|---|---|---|---|---|---|---|---|---|
| Zemmour (avec Knafo) | crise | −3,0 | −2,8 | +0,7 % | 11,2 / 10,3 | −9 | +109 | +5,3 % | 17,4 / 12,3 |
| | prudent | −2,8 | −2,0 | +1,5 % | 9,0 / 8,3 | +172 | +121 | +3,9 % | 13,1 / 9,7 |
| | médian | −2,5 | −0,9 | +2,8 % | 8,3 / 8,3 | +487 | +133 | +1,8 % | 10,1 / 8,5 |
| | optimiste | −1,9 | +0,6 | +5,2 % | 7,1 / 8,3 | +1 064 | +155 | −1,2 % | 7,4 / 8,2 |
| Tondelier | crise | −0,9 | −4,0 | −2,3 % | 13,3 / 10,3 | −1 421 | −324 | +7,7 % | 18,5 / 12,3 |
| | prudent | −0,7 | −3,0 | −1,8 % | 10,3 / 8,3 | −1 042 | −278 | +5,8 % | 14,0 / 9,7 |
| | médian | +0,0 | −1,7 | −1,4 % | 9,2 / 8,3 | −646 | −253 | +3,3 % | 10,8 / 8,5 |
| | optimiste | +0,4 | −0,6 | −1,2 % | 8,2 / 8,3 | −327 | −228 | +1,2 % | 8,9 / 8,2 |
| Bertrand | prudent | −0,0 | +0,2 | +0,2 % | 8,5 / 8,3 | +67 | +79 | aucun | 9,3 / 9,7 |
| | optimiste | +0,1 | +0,6 | +0,7 % | 8,3 / 8,3 | +202 | +132 | aucun | 7,3 / 8,2 |
| Arthaud (partiel) | prudent | −0,9 | −1,8 | −2,2 % | 13,4 / 8,3 | −1 623 | 0 | +3,4 % | 12,7 / 9,7 |

Lecture :
- Zemmour : la suppression de la CSG, calculée par OpenFisca, rapporte durablement environ 1 % de PIB en prudent ;
  avec les seniors et la prime d'activité en moins, il lui faudrait encore 3,9 % de PIB pour ne pas creuser le solde
  par rapport au statu quo ; il ne s'autofinance que dans l'optimiste.
- Tondelier : le retour à 62 ans coûte ≈ 280 000 emplois de seniors en prudent ; avec le SMIC et les hausses de
  prélèvements, le PIB est 1,8 % sous le statu quo.

## Limites restantes

1. Quatre réformes du travail sont calculées par OpenFisca (les plus lourdes) ; les autres mesures du travail gardent
   une incidence simple.
2. Couples : un seul cas type de second apporteur (conjoint au salaire médian, un enfant) ; pas encore la distribution
   des ménages réels.
3. Les montants des mesures restent ceux des programmes (barème de l'impôt sur le revenu calé sur la DGFiP) ;
   OpenFisca, en personne seule, surestime l'impôt sur le revenu (tranche à 11 % ramenée à 9 % : 7,9 Md€ contre 3 Md€
   retenus) : il ne sert qu'à répartir l'effet entre cellules.
4. Pas d'effet des dépenses publiques sur l'offre (éducation, investissement public) au-delà du multiplicateur.
