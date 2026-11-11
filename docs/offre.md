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

### Travail : OpenFisca, personnes seules et couples, offre et demande

`outils/openfisca_offre.py` calcule avec OpenFisca-France (législation 2026), sur toute la grille de salaires, le
revenu disponible, l'impôt sur le revenu et le coût du travail d'une personne seule et de **neuf cas de couples**
(conjoint à 18 000, 30 000 ou 55 000 € brut × zéro, un ou deux enfants ; le salaire de la grille est celui du second
apporteur), pondérés (offre.couples_cas : tiers de salaires ; 35 % sans enfant, 25 % un, 40 % deux ou plus, Insee),
dans le système actuel et pour chaque réforme du travail des programmes :

| Réforme OpenFisca | Programmes | Prélèvements en moins (Md€, statique) | Prestations en plus (Md€) |
|---|---|---|---|
| CSG supprimée sur les revenus d'activité | Zemmour | 83,3 | −7,5 |
| CSG déductible +1 point sur les revenus d'activité | Tondelier (COT-04, 62 % du montant) | −8,4 | +1,0 |
| Tranche à 11 % de l'impôt sur le revenu ramenée à 9 % | Bertrand, Tondelier | 7,9 | 0 |
| Tranche à 60 % au-delà de 250 000 € par part | Tondelier | −0,7 | 0 |
| Allègements arrêtés à 1,6 SMIC au lieu de 3 | Tondelier (REC-37) | −26,0 | 0 |
| Cotisation vieillesse salariale +1 point au-delà du plafond | Tondelier (COT-01) | −1,2 | 0 |
| Cotisations vieillesse +0,5 point salarié et employeur | Tondelier (COT-02) | −9,9 | +0,4 |

Cellule par cellule (distributions de salaires de 2026) :
- **offre** : variation du gain à travailler (participation) et du taux de revenu net marginal (heures), personnes
  seules et couples (60 % des salariés, élasticité 1 à 1,5 fois plus forte) ; emplois venus de l'inactivité ;
- **demande** : variation du coût du travail (cotisations patronales, allègements), avec une élasticité par tranche
  (offre.demande_travail : forte près du SMIC, Kramarz et Philippon ; faible au-delà de 1,6 SMIC, Bozio et Wasmer) ;
  emplois pris sur le chômage.

Effet rapporté aux prélèvements en moins (cotisations patronales comprises), comme les montants des mesures.
Calage : la suppression de la CSG donne, par point de PIB, 0,3 % de PIB en crise, 0,5 % en prudent, 0,8 % en médian,
≈ 1,1 % en optimiste (Bassanini et Scarpetta, OCDE, 2001 : 0,3 direct, 0,6 à 0,7 avec l'investissement).

**Montants des mesures d'impôt sur le revenu** : OpenFisca surestime l'impôt sur le revenu (89 Md€ sur les salaires en
personnes seules, 71 avec les couples, contre ≈ 60 réels : décote, réductions et crédits, autres revenus). Il ne sert
qu'à répartir l'effet entre cellules ; les montants restent sourcés à part. Recalages faits :
- tranche à 11 % ramenée à 9 % (Bertrand, Tondelier) : 4,5 Md€ en prudent et en crise, 3,3 en médian et en optimiste,
  d'après la réforme de 2020 (14 → 11 %, ≈ 5 Md€ pour 3 points avec un mécanisme limitant le gain des tranches
  supérieures ; OpenFisca : 7,5 Md€) — avant : 3 Md€ partout ;
- impôt sur le revenu en plus quand la CSG disparaît (Zemmour) : 72 % du calcul en personne seule en médian (couples
  et impôt réel), 65 % en prudent — avant : 65 % en médian, 60 % en prudent.

**Correction trouvée en passant** : supprimer la CSG fait baisser la prime d'activité, le RSA et les aides au logement
(≈ 7,5 Md€ d'économie que le chiffrage de Zemmour ne comptait pas) ; la hausse de CSG de Tondelier les fait monter
(≈ 1 Md€).

### Entreprises et autres instruments

- Entreprises : élasticité de l'investissement au coût du capital des cohortes, coût du capital (1 − τz)/(1 − τ),
  part du capital 0,35 : ≈ +0,45 % de PIB pour 1 point de PIB d'IS en moins.
- Investissement public (dépense au poste investissement) : +0,2 % de PIB à long terme pour 1 point de PIB en prudent,
  0,33 en médian (Mésange), 0,5 en optimiste (Bom et Ligthart, 2014) ; emplois à moitié, pris sur le chômage.
- Coût du travail (autres mesures, Mésange), capital des ménages, successions, TVA, transferts aux actifs : élasticités
  sourcées dans economie.yaml.
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
| Zemmour (avec Knafo) | crise | −3,0 | −2,7 | +0,8 % | 11,2 / 10,3 | −16 | +109 | +5,1 % | 17,3 / 12,3 |
| | prudent | −2,8 | −1,9 | +1,6 % | 9,0 / 8,3 | +158 | +121 | +3,7 % | 13,0 / 9,7 |
| | médian | −2,4 | −0,8 | +3,0 % | 8,3 / 8,3 | +466 | +133 | +1,6 % | 9,9 / 8,5 |
| | optimiste | −1,8 | +0,8 | +5,4 % | 7,1 / 8,3 | +1 030 | +155 | −1,5 % | 7,2 / 8,2 |
| Tondelier | crise | −0,9 | −4,1 | −2,4 % | 13,5 / 10,3 | −1 448 | −324 | +7,9 % | 18,6 / 12,3 |
| | prudent | −0,8 | −3,1 | −1,9 % | 10,5 / 8,3 | −1 064 | −278 | +5,9 % | 14,1 / 9,7 |
| | médian | +0,0 | −1,7 | −1,4 % | 9,3 / 8,3 | −654 | −253 | +3,3 % | 10,8 / 8,5 |
| | optimiste | +0,4 | −0,5 | −1,0 % | 8,3 / 8,3 | −314 | −228 | +1,0 % | 8,9 / 8,2 |
| Bertrand | prudent | −0,1 | +0,2 | +0,3 % | 8,5 / 8,3 | +71 | +79 | aucun | 9,4 / 9,7 |
| | optimiste | +0,1 | +0,6 | +0,7 % | 8,3 / 8,3 | +200 | +132 | aucun | 7,4 / 8,2 |
| Arthaud (partiel) | prudent | −0,9 | −1,8 | −2,2 % | 13,4 / 8,3 | −1 623 | 0 | +3,4 % | 12,7 / 9,7 |

Lecture :
- Zemmour : la suppression de la CSG, calculée par OpenFisca, rapporte durablement environ 1 % de PIB en prudent ;
  avec les seniors et la prime d'activité en moins, il lui faudrait encore 3,7 % de PIB pour ne pas creuser le solde
  par rapport au statu quo ; il ne s'autofinance que dans l'optimiste.
- Tondelier : le retour à 62 ans coûte ≈ 280 000 emplois de seniors en prudent ; avec le SMIC, la fin des
  allègements au-dessus de 1,6 SMIC et les hausses de prélèvements, le PIB est 1,9 % sous le statu quo.

## Limites restantes

1. Les mesures du travail encore en incidence simple pèsent peu (Tondelier : épargne salariale, plafonnement des
   niches) ; toutes les grosses passent par OpenFisca.
2. Couples : neuf cas types pondérés, pas encore l'échantillon des ménages réels (enquête Revenus fiscaux et sociaux,
   accès sécurisé) ; familles monoparentales absentes.
3. OpenFisca surestime l'impôt sur le revenu (décote, réductions, autres revenus absents) : il répartit les effets,
   les montants restent calés sur des chiffrages publics.
4. Éducation et recherche : canal ajouté le 11/11/2026 (section suivante), aux preuves plus fragiles que les autres.

## Éducation et recherche : effets de très long terme (11/11/2026, phase 2)

Deux instruments en plus, `education` et `recherche` (`moteur/offre.education`, `moteur/offre.recherche`), sans
emploi direct, avec le poids de la dépense dans la demande. Une baisse prend le scénario miroir.

- **Éducation** : une génération gagne 0,25 / 0,5 / 1 / 2 % de salaire (crise à optimiste) pour 10 % de dépense par
  élève en plus sur sa scolarité (6 à 18 ans), en moyenne sur ses années d'école ; effet sur le PIB = 60 % (part du
  travail) × gain moyen des actifs de 20 à 64 ans. Dépense de référence : 155 Md€ (État et collectivités, DEPP).
  Sources : Jackson et Mackevicius (2024), Jackson, Johnson et Persico (2016), Chetty, Friedman et Rockoff (2014).
- **Recherche publique** : stock de connaissances amorti de 15 % par an, rendement de 5 / 10 / 25 / 50 % par an après
  quatre ans. Sources : Hall, Mairesse et Mohnen (2010), Fieldhouse et Mertens (2023, 140 à 210 %), Griliches (1979).
- Mesures concernées : salaires et postes d'enseignants, classes, AESH, universités, recherche (Glucksmann, Attal,
  Philippe, Retailleau, Lisnard, Mélenchon, Tondelier, Arthaud). Hors champ : bâtiments, cantine, bourses,
  périscolaire, logement étudiant, hausses générales du point d'indice.

Ordres de grandeur (prudent) : Glucksmann +0,04 % de PIB en 2050 et +0,12 % en 2073 ; Mélenchon, éducation +0,10 et
+0,28 %, recherche +0,18 et +0,20 %. L'effet de l'éducation est presque nul avant 2040 : les générations concernées
entrent à peine sur le marché du travail.
