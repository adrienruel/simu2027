# Microsimulation : population synthétique et OpenFisca (phase F)

Décision d'Adrien du 14/11/2026 : faute d'accès à une enquête (ERFS, EFL), la base micro est une **population
synthétique** de ménages tirée et calée sur des tableaux publics. Elle pourra être remplacée par une vraie enquête
sans changer le reste de la chaîne. Paramètres : `parametres/commun/microsimulation.yaml`.

```
python -m outils.population_synthetique   # → parametres/donnees/population_synthetique_2026.csv (≈ 3 s)
python -m outils.openfisca_population     # totaux OpenFisca 2026 contre les comptes (≈ 30 s)
```

## Construction (F1)

1. **Ménages** : 20 000 unités de tirage (graine 2027). Type de ménage (Insee, recensement 2021), âges tirés dans la
   population de l'Insee 2026 hors ménages ordinaires (Ehpad, foyers), enfants par famille, écart d'âge des conjoints.
2. **Statuts** : emploi par âge (`demographie.taux_emploi_age`), corrigé selon la configuration familiale (Insee,
   enquête Emploi 2024 : − 3,4 points sans enfant, − 5,2 en famille monoparentale, + 5,3 en couple avec enfants) ;
   chômage par âge, plus fréquent sans conjoint ; retraite par âge ; études ; salariés du privé, agents publics,
   indépendants.
3. **Revenus** : tirés dans les distributions déjà utilisées par le moteur (classes de coût du travail du privé et du
   public, indépendants par décile, déciles de pensions de la Drees ramenés à 1 980 € bruts par mois), rangés selon
   un score latent qui suit le profil de salaire par âge et corrèle les conjoints (rangs : 0,35 pour les salaires,
   0,2 pour les pensions). Un bas salaire annuel est en partie travaillé sur quelques mois (Smic d'OpenFisca).
   Chômeurs : 72 % indemnisés, 1 310 € bruts par mois en moyenne (Unédic). AAH : 1,35 million d'adultes.
   Dividendes (53 Md€) et loyers perçus (30 Md€) répartis par une loi de Pareto selon le rang de revenu.
4. **Logement** : propriétaires plus fréquents avec l'âge et le revenu, parc social dans le bas de la distribution ;
   loyers au m² (RPLS pour le social, hypothèse pour le privé) ; zones des aides au logement.
   Étudiants : deux sur trois vivent hors de chez leurs parents (OVE 2023), en ménage d'une personne rattaché au
   foyer fiscal des parents et de même poids.
5. **Calage** (ratissage borné, poids entre 0,2 et 5 fois le poids de départ) sur 50 marges, toutes atteintes à
   1,3 % près : population par âge (21 tranches), ménages par type (4), familles par nombre d'enfants mineurs (4),
   familles d'au moins deux enfants de moins de 20 ans (Cnaf), agents publics, indépendants, chômeurs, retraités,
   salariés du privé par classe de coût du travail (8), statuts d'occupation (4).

Masses obtenues : salaires bruts 1 039 Md€, coût du travail 1 446, revenus d'indépendants 115, allocations chômage 30,
pensions 396.

## Calcul par OpenFisca et calage sur les comptes (F1, deuxième partie)

`outils/openfisca_population.py` construit foyers fiscaux (déclaration commune des mariés et pacsés, 75 % des
couples), familles au sens des prestations et ménages, calcule la législation 2026 (revenus des deux années
précédentes pris égaux à ceux de l'année) et pondère. Recours : RSA 65 % des familles éligibles, prime d'activité
50 % (Drees, 2026), tirés avec une probabilité qui croît avec le montant ; ASF : 0,98 million de familles (OpenFisca
la suppose due à tout parent isolé).

| Agrégat 2026 (Md€) | OpenFisca | Comptes | Écart | Source des comptes |
|---|---|---|---|---|
| Impôt sur le revenu net | 105,2 | 104,0 | + 1 % | PLF 2026, voies et moyens |
| Prestations d'entretien (AF, CF, ASF, ARS, Paje de base et naissance) | 23,2 | 25,2 | − 8 % | Cnaf 2024, revalorisé |
| Aides au logement | 14,8 | 16,7 | − 11 % | SDES, compte du logement |
| RSA (allocations) | 10,6 | 12,4 | − 15 % | Cnaf, RSA Conjoncture T4 2025 |
| Prime d'activité | 11,9 | 10,5 | + 13 % | Sénat, PLF 2025 |
| AAH | 15,7 | 14,6 | + 7 % | PLF 2026 |

**Second calage sur les bénéficiaires (14/11/2026, soir, décision d'Adrien).** OpenFisca calcule d'abord qui est
éligible ; les poids sont ensuite recalés, en plus des marges démographiques, sur les effectifs publiés : RSA par
configuration familiale et avec la prime d'activité (Drees), prime d'activité, aides au logement (Drees, décembre
2025), complément familial (Cnaf), adultes handicapés. Toutes les marges sont atteintes (la plus éloignée, les couples
sans enfant au RSA, à 16 % d'un petit effectif). Recours : probabilité proportionnelle au montant à la puissance 0,2,
qui reproduit l'écart de la Drees entre non-recours au RSA en nombre et en montant.

Les **effectifs** sont donc justes ; les écarts restants sont des **montants moyens** : RSA 480 € par foyer et par mois
contre 567 € à la Cnaf, aides au logement 218 € contre ≈ 245 €, prime d'activité 208 € contre ≈ 184 €. Le calage par
les poids ne peut pas corriger un montant moyen : il faut que les revenus et les loyers des bénéficiaires soient plus
justes (trop de revenus partiels au RSA, loyers du privé et zones à sourcer, revenus des travailleurs modestes lissés
sur l'année).

Correction trouvée en route : la cible RSA de 13,5 Md€ (statu_quo.rsa) compte aussi les dépenses d'insertion des
départements ; les allocations seules font ≈ 12,4 Md€ (Cnaf). Le bloc du statu quo n'est pas changé (l'insertion est
une vraie dépense), mais sa note est à corriger.

Pistes, par ordre d'intérêt :

1. **Caler aussi sur les effectifs de bénéficiaires** publiés par la Cnaf et la Drees (RSA par configuration
   familiale, aides au logement, AAH, complément familial), en faisant tourner OpenFisca dans la boucle de calage :
   c'est la pratique des modèles de microsimulation publics. L'écart en montant reste alors un contrôle.
2. **Définir le périmètre** de chaque comparaison (outre-mer, foyers et établissements) avec des montants sourcés.
3. Accès à l'ERFS (Insee, via le CASD) : remplace la population synthétique.

Hypothèses à sourcer en priorité : loyer au m² du privé, zones des aides au logement, part de l'AAH en emploi,
emploi et chômage des personnes seules (Insee, France portrait social 2012 : chômage des hommes sans conjoint
13 % contre 5 % en couple).

## Suite de la phase F

- F2 : coder les mesures fiscales et sociales des programmes dans OpenFisca (réformes de `outils/openfisca_reforme.py`).
- F3 : sorties redistributives (déciles de niveau de vie, pauvreté, Gini, gagnants et perdants, cas types).
- F4 : boucle micro-macro (recettes d'OpenFisca à la place des élasticités agrégées, écarts de plus de 10 % expliqués).

## F2 : mesures des programmes dans OpenFisca (premier lot, 14/11/2026, soir)

`programmes/micro_mesures.yaml` décrit chaque mesure codée par des opérations (paramètre d'OpenFisca changé, tranche
ajoutée, prestation revalorisée, règle nouvelle) ; `outils/openfisca_mesures.py` calcule la population avant et après
(un processus par programme : `python -m outils.openfisca_mesures <programme>`), avec les mêmes tirages de recours.
Effet **statique** sur le solde (Md€ de 2026, + = l'améliore) contre le chiffrage du moteur au prudent :

| Programme | Mesure | OpenFisca | Moteur | Lecture de l'écart |
|---|---|---|---|---|
| Bertrand, Tondelier | Tranche à 11 % ramenée à 9 % | − 9,3 | − 4,5 | Le moteur transpose la réforme de 2020 (3 points, 5,4 Md€) qui neutralisait le gain des tranches supérieures ; ici tous les contribuables au-delà de 11 600 € par part gagnent : **le moteur sous-estime probablement** |
| Bertrand | PFU + 2 points | + 0,8 | + 0,7 | Proche |
| Tondelier | Tranche à 60 % | + 1,0 | + 1,2 | Proche (moteur : élasticité du revenu comprise) |
| Tondelier | Fin de l'abattement de 10 % des retraités | + 5,8 | + 4,0 | Encadrement du moteur (4 à 4,5) à revoir à la hausse |
| Tondelier | CSG + 1 point | + 7,4 | + 13,6 | OpenFisca : revenus d'activité seuls ; le moteur compte tous les revenus |
| Tondelier | Capital : CSG et PFU + 3 points | + 1,3 | + 3,5 | La population n'a ni intérêts, ni plus-values, ni assurance-vie |
| Tondelier | APL + 10 % | − 1,7 | − 1,7 | Égal |
| Tondelier | AF dès le premier enfant | − 3,5 | − 2,8 | |
| Tondelier | AAH + 250 € | − 4,1 | − 4,4 | Proche |
| Tondelier | Garantie d'autonomie (RSA + 20 %, dès 18 ans) | − 5,8 | − 6,6 | Proche |
| Lisnard | Quotient familial déplafonné | − 4,4 | − 3,5 | Moteur dans l'encadrement (3 à 4) ; OpenFisca un peu au-dessus |
| Roussel | CSG sur les retraites supprimée | − 23,1 | − 22,0 | Proche |
| Roussel | APL + 5 % | − 0,9 | − 0,8 | Proche |
| Roussel | RSA dès 18 ans | − 1,5 | − 2,0 | |
| Mélenchon | APL + 10 % | − 1,7 | − 1,7 | Égal |
| Mélenchon | AAH à 1 700 € | − 10,8 | − 11,5 | Proche |
| Mélenchon | Garantie d'autonomie au seuil de pauvreté | − 37,2 | − 28,0 | Ménages d'étudiants exclus (champ de l'Insee, les jeunes ont leur propre mesure) ; la distribution relative est juste (voir plus bas), les niveaux de vie sont ≈ 12 % trop bas, d'où plus de ménages sous un seuil fixé en euros |
| Le Pen | IR nul avant 30 ans (jusqu'à 4 SMIC) | − 6,5 | − 3,7 | Montaigne : 3,7 à 4,1 ; jeunes trop imposés dans la population ? à vérifier |
| Le Pen | ASF doublée | − 4,2 | − 1,3 | Le moteur prend l'ASF à 1,6 Md€, la Cnaf donne 3,1 Md€ en 2024 : **le moteur sous-estime** ; la population la surestime (4,2 Md€ d'ASF, montant moyen trop haut) ; le bon ordre de grandeur est ≈ − 3,1 |
| Philippe | IR allégé trois ans après une naissance | − 1,5 | − 3,0 | Le candidat annonce 3 Md€ ; ici 1,5 |
| Arthaud | Revalorisation de 1,2 % (AF, prime d'activité, APL) | − 0,7 | − 0,6 | Proche |

Correction d'OpenFisca : `revenus_non_salarie_nets` (version 177) additionnait les revenus de micro-entreprise de toute
la population et les donnait à chaque personne (`sum()` de Python sur un tableau) ; le revenu disponible en était
faux, pas l'impôt ni les prestations. Corrigé localement (`openfisca_population.systeme`), à signaler au projet.

Non codé dans ce lot : conditions de nationalité ou de résidence (Zemmour, Le Pen, Retailleau, Lisnard : la population
n'a pas l'information), patrimoine (ISF, taxe Zucman, IFI), barèmes non publiés (Mélenchon, Roussel), individualisation
de l'impôt, crédit d'impôt par enfant sans montant, allocation unique de Philippe, revenu d'incitation de Retailleau.

## F3 : niveau de vie par décile (premier lot)

`sorties/micro_deciles.csv` : variation du niveau de vie de chaque décile (personnes, niveau de vie initial), mesures
codées du programme ensemble, effet statique. Exemples : Mélenchon + 87 % pour le 1er décile (garantie, surestimée),
Tondelier + 10,8 % pour le 1er décile et − 1,0 % pour le 10e, Roussel + 1,3 à + 2,5 % partout (CSG des retraités),
Bertrand jusqu'à + 1 % aux 7e et 8e déciles. Un programme n'a que ses mesures codées : ce ne sont pas encore des
bilans complets.

| Lisnard | Aides plafonnées à SMIC − 500 € sans activité | + 2,6 | + 2,0 | |
| Retailleau | Revenu d'incitation (300 € ; 550 € avec activité) | + 4,2 | + 3,0 | Lecture retenue : à la place du RSA et de la prime pour les familles éligibles au RSA ; la lecture littérale coûte 14 Md€ |
| Retailleau | Aides plafonnées à 70 % du SMIC net | + 3,5 | + 1,0 | |

## Distribution des niveaux de vie : la population contre l'Insee

| 2026 (population) contre 2023 (Insee) | Population | Insee |
|---|---|---|
| Taux de pauvreté (60 % de la médiane) | 15,4 % | 15,4 % |
| Intensité de la pauvreté | 20,2 % | 19,2 % |
| Rapport D9 / D1 | 3,53 | 3,5 |
| Médiane (€ par an) | 24 240 (€ de 2026) | 25 760 (€ de 2023) |

La forme de la distribution est la bonne ; le niveau est ≈ 12 % trop bas (médiane de l'Insee ≈ 27 700 € en euros de
2026) : il manque surtout des revenus du patrimoine (intérêts, assurance-vie, plus-values). Pas de recalage du bas
de distribution, donc : il est juste en relatif.

## Emploi : gain à travailler calculé par OpenFisca (14/11/2026, soir, demande d'Adrien)

Moins d'aides pour qui ne travaille pas = plus de gain à travailler = plus d'emploi et de recettes. Pour chaque
personne en emploi de 18 à 64 ans, OpenFisca calcule le revenu disponible de son ménage si elle ne travaillait pas
(deux simulations : personnes de référence, puis autres adultes), avant et après la réforme. La variation relative du
gain à travailler × l'élasticité de participation de sa tranche de salaire (offre.travail_participation, 0,12 / 0,06 /
0,03 au prudent ; scénario miroir quand le gain baisse) donne les emplois en plus ; chaque emploi rapporte son coût
du travail moins le gain du ménage (prélèvements payés et aides évitées). Effet de long terme, sans montée. Bruit
de l'ordre de ± 10 000 emplois (mesures sans effet attendu).

| Programme (mesures codées) | Emplois (milliers) | Effet sur le solde (Md€) | Moteur, canal « transferts aux actifs » (2037) |
|---|---|---|---|
| Retailleau (revenu d'incitation, plafond des aides) | + 251 | + 3,0 | + 6 |
| Lisnard (plafond des aides sans activité, quotient familial) | + 89 | + 1,3 | + 3 |
| Bertrand (tranche à 9 %, PFU) | + 30 | + 0,6 | |
| Le Pen (IR des jeunes, ASF) | + 22 | + 0,5 | |
| Roussel (RSA dès 18 ans surtout) | − 59 | − 1,7 | |
| Tondelier (garantie d'autonomie surtout : − 210) | − 240 | − 5,6 | − 13 |
| Mélenchon (garantie au seuil de pauvreté : − 1 081) | − 1 053 | − 26,1 | − 84 |

Le canal agrégé du moteur (élasticité de 0,1 au prudent sur les montants) donne des effets 10 à 40 fois plus petits.
La micro mesure le changement de gain à travailler là où il se produit : un plafond d'aides ou un RSA plus bas
augmente beaucoup le gain de ceux qui en dépendent ; une garantie de revenu au seuil de pauvreté le supprime
(taux marginal de 100 % sous le seuil). À discuter avant d'entrer dans les trajectoires (F4) : les évaluations
françaises du RSA trouvent des effets plutôt faibles (Dares, 2011), les élasticités de participation au gain
(Immervoll et al., 2007 ; Bargain et al., 2014) des effets nets.

## F4 (premier pas) : l'emploi de la micro dans les trajectoires (14/11/2026, soir, décision d'Adrien)

- Trois niveaux pour l'effet du gain à travailler quand il change par les aides (`offre.participation_transferts`) :
  bas (crise, prudent : un tiers des élasticités de participation, évaluations françaises du RSA), central (médian :
  deux tiers, Bargain et Doorley 2011), haut (optimiste : les élasticités entières, Immervoll et al. 2007). Une baisse
  d'emploi prend le scénario miroir.
- `outils/openfisca_mesures.py` écrit les emplois et leur valeur pour le solde, par mesure et par scénario
  (`parametres/donnees/micro_emploi_2026.csv`). Le moteur (`offre.effets`, option `offre.micro_emploi`) les prend pour
  les transferts codés, à la place de l'élasticité agrégée : montée au profil de la mesure, emplois venus de
  l'inactivité, prélèvements et aides évitées calculés par la micro, PIB à 35 000 € par emploi.
- Montants recalés sur la micro : tranche à 9 % (Bertrand, Tondelier : − 9,3), ASF doublée (Le Pen : 3,2 au prudent),
  fin de l'abattement des retraités (Tondelier : + 5,5 / 5,8), revenu d'incitation (Retailleau : 4,2, lecture retenue),
  plafond des aides (Retailleau : 3,5 ; Lisnard : 2,6). Crise : 75 % des économies.

Emplois par le gain à travailler au prudent (milliers) : Retailleau + 95, Lisnard + 23, Mélenchon − 724 (garantie),
Tondelier − 146 (garantie d'autonomie), Roussel − 40 (RSA dès 18 ans).

Effet sur le déficit 2037 au prudent : Mélenchon + 0,57 point, Tondelier + 0,23, Bertrand + 0,17 (IR), Le Pen + 0,10
(ASF), Retailleau − 0,17, Lisnard − 0,03.
