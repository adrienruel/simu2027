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

## Aides sous condition de nationalité ou de durée (14/11/2026, soir)

- Nationalité dans la population (`microsimulation.nationalite`) : 6,03 millions d'étrangers (Insee 2024), ménage par
  ménage, plus souvent dans le bas de la distribution, calés pour recevoir 13 % des prestations des Caf (Cnaf, d'après
  l'iFRAP : 13,2 % obtenus) ; un quart ressortissants de l'UE, 30 % des autres arrivés depuis moins de cinq ans.
- Règles nouvelles : `condition_nationalite` (prestations retirées à un groupe de familles), `rsa_duree` (une part
  des allocataires du RSA le perd, sauf handicap, parent isolé, 60 ans ou plus).

| Programme | Mesure | OpenFisca (statique) | Moteur (prudent) | Emplois (prudent, application complète) |
|---|---|---|---|---|
| Zemmour | Prestations familiales, logement, RSA, prime réservés aux Français (hors UE exclus) | + 5,9 | + 5,1 | + 12 500 |
| Zemmour | RSA limité à trois ans | + 2,4 | + 1,5 | + 43 000 |
| Le Pen | Priorité nationale (moins de cinq ans, hors UE) | + 1,7 | + 2,0 | + 3 000 |
| Retailleau | Cinq ans de résidence | + 1,7 | + 2,0 | + 3 000 |
| Lisnard | Cinq ans de résidence | + 1,7 | + 2,2 | + 3 000 |
| Philippe | Durée du RSA limitée (lecture : trois ans) | + 2,4 | + 0,4 | + 43 000 |

Les montants du moteur gardent le risque juridique (crise à zéro ou presque) : la micro donne l'effet d'une
application complète. Les emplois entrent dans les trajectoires au prorata du montant du moteur (montant du moteur /
effet statique de la micro), pour toutes les mesures où la micro donne les emplois.

## Vieillissement statique et recettes de la micro dans le moteur (14/11/2026, nuit, décision d'Adrien)

`outils/vieillissement.py` recale les poids de 2026, pour 2029, 2032, 2037 et 2050 et pour chaque programme, sur :
la population du programme par âge (naissances et immigration comprises), l'emploi et le chômage de sa trajectoire
(prudent), les retraités du COR, le nombre de ménages ; les pensions suivent la pension moyenne du moteur rapportée
aux salaires (− 14 % en 2050 : pensions sur les prix, salaires sur la productivité). Revenus et législation de 2026 en
unités de salaire, comme le statu quo du moteur (barèmes qui suivent les salaires).

Statu quo, en unités de salaire : impôt sur le revenu − 4 % de 2029 à 2050, CSG − 2 % (moteur : prélèvements sur les
salaires − 1,6 %, sur les pensions + 1 %) ; pauvreté 15,0 % → 14,2 %.

Pauvreté (statique, mesures codées seulement) en 2032 : statu quo 14,9 % ; Philippe 13,8 ; Tondelier 14,3 ; Le Pen
14,8 ; Lisnard 15,1 ; Zemmour 15,3 ; Retailleau 15,4 ; Roussel 15,4 (seuil relatif : la médiane monte avec la CSG des
retraités) ; Mélenchon 0 (la garantie porte chaque ménage au-dessus de 60 % de la médiane). `sorties/micro_vieillissement*.csv`.

**Recettes de la micro dans le moteur** (`microsimulation.recettes_vieillies`, `moteur/micro.py`) : neuf mesures d'IR
et de CSG suivent l'indice de la population vieillie de leur programme (effet statique l'année t / en 2026) ; trois
montants de plus recalés sur OpenFisca (quotient familial de Lisnard − 4,4 ; CSG des retraités de Roussel − 23,1 ;
IR après une naissance de Philippe − 1,5, le chiffre du candidat n'est plus repris). Indices en 2050 : quotient
familial 0,80 (moins de familles), IR des jeunes 0,85, CSG des retraités 0,94 (pensions plus basses par rapport aux
salaires), tranche à 9 % 0,95-0,99. Déficit 2037 au prudent : Philippe 11,33 → 11,26, Roussel + 0,06, Lisnard
+ 0,03, autres ≤ 0,01.

## Impôt des moins de 30 ans (15/11/2026)

Constat : avec le profil de salaire en équivalent temps plein, les salariés de 18-24 ans de la population gagnaient
23 200 € imposables par an, contre un revenu salarial de 10 170 € net pour l'Insee (2023). Le rang de salaire suit
maintenant le revenu salarial annuel par âge (Insee), qui compte le temps partiel et les mois non travaillés :
19 800 €. L'écart restant tient surtout aux apprentis (environ un million, rémunération exonérée d'IR jusqu'au Smic)
et aux jobs d'étudiants (exonérés jusqu'à trois Smic mensuels), que la population ne distingue pas encore.
IR des foyers dont le déclarant a moins de 30 ans et un revenu sous quatre Smic : 4,2 Md€ (5,3 avant), contre 4,1
pour Montaigne revalorisé sans plafond ; l'estimation reste un peu haute.

## Population d'entreprises (premier jet, 15/11/2026, demande d'Adrien)

`outils/population_entreprises.py` : 17 400 entreprises synthétiques pondérées, 6 secteurs (industrie, construction,
commerce, transports, services marchands, santé et enseignement marchands) × 3 tailles (microentreprises, PME,
GE et ETI réunies), champ marchand non agricole et non financier.

- Totaux exacts par cellule : nombre d'entreprises, EQTP, valeur ajoutée, frais de personnel, EBE, investissement
  (Insee, Ésane 2023 : tableaux par secteur et par taille, `parametres/donnees/entreprises_secteurs_tailles.csv`).
  Santé et enseignement : reste du total de l'ensemble ; l'EBE des services (absent du tableau de l'Insee) est le
  reste de l'EBE, partagé entre services marchands et santé au prorata de la VA moins les frais de personnel.
- Dans chaque cellule, l'emploi suit une loi log-normale (σ : 1,0 pour les MIC, 0,8 pour les PME, 1,3 pour les GE et
  ETI : DÉCISION, à remplacer par la dispersion d'Ésane si elle est publiée) ; VA, frais de personnel et
  investissement suivent l'emploi avec un bruit, puis sont recalés. Impôts de production nets des subventions :
  VA − frais de personnel − EBE, répartis au prorata de la VA.
- IS : part des MIC à l'IS = TPE à l'IS de la DGFiP (2,49 millions) / MIC d'Ésane, la même dans chaque secteur
  (DÉCISION) ; PME, ETI et GE toutes à l'IS. Résultat fiscal tiré par rang (EBE plus un bruit de rentabilité) sur
  la distribution des bénéfices de la DGFiP en 16 classes (exacte par construction) ; le rang des MIC et des PME est
  décalé pour que les bénéfices par taille rejoignent la DGFiP.
- Contrôle (bénéfices / IS brut, Md€, modèle contre DGFiP 2024) : MIC 69,3 / 13,2 contre 65,9 / 14,0 ; PME 78,9 /
  19,2 contre 78,5 / 19,2 ; GE et ETI 131,4 / 32,8 contre 139,5 / 35,8. Total de l'IS : 65,2 contre 69,0 (− 5,5 %).
  Les MIC ne descendent pas plus bas : il y a plus de MIC à l'IS (2,49 millions) que d'entreprises bénéficiaires
  (1,72 million), elles occupent forcément une partie des rangs bénéficiaires. Les tailles de la DGFiP (par unité
  légale) et de l'Insee (par entreprise au sens économique) ne coïncident pas : 221 000 PME contre 172 500.
- Pertes : ordre de grandeur seulement (perte moyenne des classes connues de la DGFiP) ; les déficits reportables ne
  sont pas encore modélisés.

Suite : impôts de production par impôt (CVAE, CFE, C3S, taxe foncière) entreprise par entreprise ; barèmes d'IS des
programmes (taux, seuil du taux réduit, IS progressif) appliqués à chaque entreprise ; crédit d'impôt recherche ;
réactions (investissement par taille, déjà dans `moteur/entreprises_cellules.py`, emploi, prix) ; puis passage des
choix des entreprises aux revenus des ménages (salaires, dividendes), comme dans l'architecture voulue.

## Impôts des entreprises sur la population d'entreprises (phase G, premier lot, 15/11/2026)

`outils/entreprises_mesures.py` et `programmes/micro_entreprises.yaml`. Chaque entreprise a un chiffre d'affaires
(total Ésane de sa cellule) et un capital (immobilisations corporelles par EQTP de sa taille, Insee, réparties selon
l'investissement). Impôts calculés entreprise par entreprise : IS (taux réduit de 15 % jusqu'à 42 500 € si le CA est
sous 10 M€), C3S (0,16 % du CA au-delà de 19 M€), CVAE (barème légal par CA), CFE et taxe foncière (au prorata du
capital). Chaque impôt est ramené à son total national (IS 70,3 ; C3S 4,8 ; CFE 8,2 et taxe foncière 17,3 hors part du
secteur financier ; CVAE 8 Md€ au taux de 0,75 %). La part des sociétés éligibles au taux réduit (condition de
détention du capital, non modélisée) est calée sur la base de 27,0 Md€ taxée à 15 % en 2022 (Insee, DGFiP) : 61 %.

Résultats (Md€, statique ; « brut » : sans le retour d'IS ; moteur au prudent) :

| Mesure | Micro net | Micro brut | Moteur |
|---|---|---|---|
| LIS-FIS-03 : IS à 20 % | − 13,2 | − 13,2 | − 10,0 (part locale levée en partie) |
| REC-33 : taux réduit à 10 % | − 1,45 | − 1,45 | − 1,0 → − 1,45 (recalé) |
| REC-35 : CVAE à 0,75 % | + 6,2 | + 8,0 | + 7,0 |
| RN-FIS-04 : CFE et C3S supprimées | − 9,1 | − 12,1 | − 13,0 |
| RET-FIS-01 : C3S et CFE industrielle | − 5,3 | − 7,1 | − 6,0 |
| LIS-FIS-01, PHI-FIS-01 : C3S, CFE et taxe foncière | − 20,8 | − 27,6 | − 24 ; − 30 (avec d'autres impôts) |

Constat : les impôts de production et les cotisations patronales sont des charges déductibles, et le moteur ne comptait
l'IS qui revient quand elles changent que pour les hausses du SMIC (25 % de la part prise sur les marges, la moitié).
Règle commune (`entreprises.retour_is_charges`) : retour = taux effectif de la micro (0,25 de la variation du bénéfice)
× part prise sur les marges (0,5, la valeur déjà utilisée pour le SMIC), soit 10 % de la variation (taux effectif
0,20 depuis le calage des pertes sur la DGFiP 2025, voir plus bas). Elle s'applique aux
mesures marquées `deductible_is` (`true`, ou la part de la mesure qui porte sur des charges des entreprises, 0,5 quand
une mesure mêle cotisations salariales et patronales ou des particuliers employeurs) : impôts de production (Attal,
Lisnard, Philippe, Le Pen, Retailleau, Mélenchon, Tondelier), cotisations et exonérations (Attal, Le Pen, Lisnard,
Retailleau, Philippe, Tondelier : fin des allègements au-delà de 1,6 SMIC), part employeur de la capitalisation de
Retailleau, et au SMIC, dont le taux d'IS vient maintenant du même paramètre. Écologie de droite, qui refond tout le
système, garde son calcul propre. À long terme, une partie des cotisations passe dans les salaires : non modélisé.

## Crédit d'impôt recherche (15/11/2026)

MESR-DGRI, CIR en 2023 (provisoire) : 7,85 Md€ ; CIR-recherche des grandes entreprises 2 979 M€ (41 %), ETI 2 099,
PME 2 241. REC-36 (Tondelier, CIR réservé aux PME et ETI, moitié rendue en subventions) : 2,0 → 1,5 Md€ au prudent (le
moteur prenait 60 % pour les GE). GLU-FIS-04 (plafond de 100 M€ par groupe) : la tranche à 5 % au-delà de 100 M€ ne
vaut qu'environ 0,8 Md€ ; la fourchette de 1,5 à 2,5 Md€ (Sénat) suppose une consolidation au niveau du groupe entier,
non vérifiable avec les données publiées : à trancher. LFI-REC-15 (suppression) : 7,0 au prudent, cohérent.

## Calage sur l'IS de 2025 (DGFiP Statistiques n° 51, fichier fourni par Adrien, 15/11/2026)

`parametres/sources/dgfip_stat_51_is_2025.xlsx`. En 2025 : 2,83 millions d'entreprises à l'IS, dont 1 788 000
bénéficiaires et 1 046 000 déficitaires ; 111,3 Md€ de déficits de l'année ; bénéfice imposable à 15 % 30,6 Md€, à 25 %
256,8 ; IS brut 70,5 Md€ (TPE 14,5, PME 18,9, ETI 16,8, GE 20,2) ; CIR utilisé 7,7 Md€.

- Pertes : la population mettait environ 5 000 € de perte par entreprise déficitaire (seules les petites classes de
  pertes étaient connues) ; la perte moyenne réelle est d'environ 106 000 €. Les pertes sont maintenant
  proportionnelles à la VA (puissance 0,8, bruit log-normal), ramenées à 111,3 Md€. Une entreprise déficitaire franchit
  plus rarement le zéro quand ses charges baissent : le taux effectif du retour d'IS passe de 0,25 à 0,20.
- Nombre de TPE à l'IS (2,60 millions), nombre de bénéficiaires, base du taux réduit (30,6 Md€ au seuil de 42 500 €,
  part éligible 64 %) et niveau de l'IS (70,5 Md€) pris sur 2025. REC-33 : − 1,5 Md€.
- Toujours non modélisés : le stock de déficits reportables en avant et le plafond d'imputation (1 M€ + 50 % du bénéfice
  au-delà) ; la publication ne les donne pas.

## Impôts sur les salaires et employeurs sans IS (15/11/2026)

La taxe sur les salaires et le versement mobilité sont payés en partie par des employeurs qui ne paient pas l'IS
(associations, cliniques non lucratives, professions libérales) ; la population d'entreprises ne les couvre pas (elle
exclut la finance et les associations). Part des employeurs à l'IS, dans `entreprises.retour_is_charges` et les mesures
`deductible_is` (DÉCISION, sourcée) :
- cotisations patronales et SMIC : 0,9 (associations : 9,0 % de l'emploi privé en 2022, Urssaf) ; 0,45 pour les mesures
  qui mêlent cotisations salariales et patronales ou des particuliers employeurs ;
- versement mobilité 0,9, taxe sur les salaires 0,5 (produit venant largement des banques et assurances ; environ la
  moitié après retrait des employeurs publics, d'après les impôts de production par secteur de la DGFiP) : lignes
  « masse salariale » de Lisnard et de Philippe 0,67 = (15 × 0,5 + 11 × 0,9) / 26 ;
- impôts de production assis sur le capital et le chiffre d'affaires : taux de la micro, qui compte déjà les
  entreprises individuelles à l'IR (les associations sont exonérées de CFE en général).

## Déciles : mesures fiscales et SMIC ajoutés (15/11/2026, remarque d'Adrien)

Constat : pour Mélenchon, le décile le plus aisé gagnait (+ 70 € par an), parce que seules ses trois hausses de
prestations étaient codées, aucune de ses hausses d'impôt. Plus généralement, les déciles ne voyaient pas le SMIC, la
CSG de Zemmour, de Glucksmann et le « droit au brut » d'Attal. Ajouts dans `programmes/micro_mesures.yaml` :
- opérations « population » (`Base.population`) : `individualiser` (impôt individuel) et `smic_net_2027` /
  `smic_brut_2026` (salaires relevés comme dans `bibliotheque.smic`, privé et public) ; garantie de niveau de vie
  étendue aux ménages d'étudiants (`champ: etudiants`) ;
- Mélenchon : barème à 14 tranches (lecture du moteur), impôt individualisé (+ 5,97 Md€, moteur + 6,0), garantie
  d'autonomie des jeunes (− 11,0, moteur − 10,0), SMIC ; Roussel : barème à neuf tranches, SMIC ; Arthaud, Tondelier,
  Glucksmann : SMIC ; Zemmour : CSG d'activité supprimée ; Glucksmann : CSG − 15 Md€ ; Attal : « droit au brut » codé
  comme une baisse de la part déductible de la CSG d'activité (même assiette, même déductibilité).
- Le solde des mesures exclut maintenant la hausse du coût des agents publics (dépense, pas recette).

Erreur trouvée : la baisse de la première tranche de 11 à 9 % était chiffrée − 4,5 (Mélenchon) et − 3,5 (Roussel)
alors que le même barème vaut − 9,3 Md€ (recalé le 14/11 pour Bertrand et Tondelier, pas pour eux) : recalés.

Toujours hors des déciles : retraites (âge, pensions), assurance chômage, patrimoine et successions, services publics.
La colonne « Mesures prises en compte » du comparateur le dit programme par programme.

## Retraites dans la micro, et recours à l'Aspa (15/11/2026)

- Opération `population: {pensions: ...}` : pensions au-delà d'un seuil mensuel brut multipliées par un facteur (gel,
  sous-indexation), avec une perte qui s'éteint après la dernière année (≈ 18 ans, comme le moteur) ; ou
  `indexation_salaires` (pensions revalorisées comme le salaire moyen depuis 2029, ancienneté moyenne de 12 ans). Le
  vieillissement donne l'année à la base (`Base.annee`).
- Codé : Aspa au seuil de pauvreté (Mélenchon, 1 337 € ; Tondelier, ≈ 1 290 €) ou à 1 400 € (Roussel) ; pensions
  indexées sur les salaires (Roussel) ; pensions de plus de 2 000 € gelées de 2028 à 2032 (Lisnard) ou sous-indexées de
  0,5 point (Tondelier).
- Erreur trouvée : OpenFisca versait 14,7 Md€ d'Aspa à 2,2 millions de familles de la population, contre 754 460
  allocataires fin 2024 et 4,1 Md€ de dépense en 2023 (DREES) : la population n'a pas les revenus du patrimoine (qui
  comptent dans les ressources de l'Aspa), et le recours était complet alors qu'une personne seule éligible sur deux ne
  la demande pas. Recours tiré comme pour le RSA, calé sur le nombre d'allocataires (`microsimulation.recours_aspa`) :
  4,6 Md€ en 2026 ; la pauvreté de départ reste à 15,4 %.
- Non codés : âge de départ (son effet est dans la population de chaque programme, donc dans la pauvreté comparée au
  statu quo, mais pas dans les déciles, qui comparent la même population avec et sans les mesures) ; pensions des
  carrières complètes au SMIC (Mélenchon) et minimum contributif (Tondelier), faute de carrières dans la population.


## Capitalisation obligatoire (16/11/2026)

Formule `capitalisation` (`outils/openfisca_mesures.Base.capitalisation`) : la part salariale d'une capitalisation
obligatoire (taux × brut, plafonné, × (1 − part employeur)) est retirée du revenu disponible des salariés et agents
publics en emploi les plus jeunes, jusqu'au nombre d'entrants couverts depuis le début du dispositif
(entrants_par_an × taux_emploi × années), comme le moteur (`bibliotheque.capitalisation_obligatoire`). Versée à un
fonds hors des administrations publiques, elle n'est pas une recette : elle est retirée du budget de la mesure
(`fonds`). Nulle en 2026, elle apparaît dans la population vieillie. La part employeur n'est pas reportée sur les
salaires (incidence à long terme des cotisations : décision ouverte). Programmes : Retailleau (RET-RET-02), et par la
lecture commune Bertrand (BER-RET-02), Zemmour (ZEM-RET-01), Le Pen (RN-RET-03).

## Phase L (roadmap du comparateur 4.2, 18/11/2026)

**Déciles publiés selon la couverture.** `outils/couverture_micro.py` mesure, pour chaque programme, la part de son
budget « ménages » que couvrent les mesures codées dans OpenFisca (`programmes/micro_mesures.yaml`).

- **Budget « ménages »** : impôts et cotisations des ménages (instruments travail, capital des ménages, successions,
  consommation, transferts aux actifs) et transferts aux ménages (blocs retraites, chômage, famille, logement,
  pauvreté, AAH). Chaque mesure compte en valeur absolue, au prudent, en 2032.
- **Seuil** : `publication.seuil_couverture_deciles` (DÉCISION, 80 %).
- **En dessous du seuil** : les déciles du programme sortent de `comparaison_redistribution_deciles.csv`. La
  pauvreté et le Gini restent publiés, avec la couverture (`couverture_menages_pct`, `deciles_publies`).
- **Résultat** (`sorties/comparaison_couverture_micro.csv`) : seuls Attal (84 %) et Zemmour (80 %) passent. Les
  autres sont entre 11 % (Lisnard) et 67 % (Arthaud).
- **Ce qui manque le plus** :
  - l'âge de départ, qui n'est pas un barème : Le Pen, Glucksmann, Mélenchon, Roussel et Tondelier ;
  - les cotisations rendues aux actifs : Lisnard et Retailleau ;
  - la TVA et les accises, faute de consommation dans la population : Le Pen et Roussel ;
  - les successions : Zemmour et Glucksmann ;
  - les réformes de l'assurance chômage.

**Population : plus-values et apprentis** (`outils/population_synthetique.py`). Les deux ajouts sont tirés avec une
graine séparée.

- **Plus-values mobilières** : 15 Md€ (France Stratégie, 2022, revenus de 2020), réparties comme les dividendes
  mais plus dispersées. Elles sont déclarées en case 3VG (`f3vg`).
- **Apprentis** : 1 017 500 au 31/12/2025 (Dares).
  - Ils sont tirés parmi les salariés du privé de 16 à 29 ans, avec une propension par âge (hypothèse) et une
    marge de calage nouvelle.
  - Ils sont payés à la grille légale (Code du travail, art. D6222-26) et marqués `apprenti` pour OpenFisca, si
    la variable existe dans la version installée (à vérifier).
- **Vérifié sans OpenFisca** (SMIC fixé à 1 823,03 €, sans le second calage) : 1,018 million d'apprentis pondérés,
  âge moyen 20,3 ans, salaire moyen 12 600 € par an ; plus-values 15,0 Md€.
- **À régénérer avec OpenFisca** : la population (`python -m outils.population_synthetique`), puis la micro de
  chaque programme. La population du dépôt est antérieure, et ses deux colonnes nouvelles valent zéro à la lecture.

**Toujours absents** : les intérêts imposables (livrets fiscalisés, comptes à terme) et l'assurance-vie, faute de
source sur leur montant. Le patrimoine (ISF, taxe Zucman, IFI) l'est aussi, car la population ne porte pas de
patrimoine.

**ERFS** : l'accès est à demander à l'Insee par le CASD (Centre d'accès sécurisé aux données), au nom d'Adrien.
Il faut un projet, un habilitant et une convention. Quand l'accès sera ouvert, l'ERFS remplacera la population
synthétique.

## Roadmap 3.3, premier pas : âge de départ dans la population (21/11/2026)

- Opération `population: {age_depart: {age_actuel, age_cible}}` (`outils/openfisca_mesures.age_depart`).
- **Principe :** le profil de départ par âge de la population de 2026 est décalé de l'écart entre l'âge du
  programme et celui du statu quo à terme (64 ans).
- **Âge abaissé :** à chaque âge, une part des personnes qui ne sont pas encore retraitées part. Leur pension brute
  vaut 0,64 × leur revenu d'activité (`microsimulation.taux_remplacement_brut`) : c'est le taux de remplacement net
  médian de 75 % de la Drees pour les carrières complètes, passé en brut. Sans revenu d'activité, elles reçoivent la
  pension médiane des 62-66 ans.
- **Âge relevé :** une part des retraités reprend un emploi, s'inscrit au chômage (allocation de 57 % du salaire)
  ou devient inactive, selon `seniors.devenir`.
- **Emplois :** les personnes qui changent de statut sont comptées par le canal des seniors du moteur, pas par le
  gain à travailler.
- **Codé pour sept programmes**, même règle pour tous : GLU-RET-01, RN-RET-01 et RET-01 (62 ans), LFI-RET-01 et
  PCF-RET-01 (60 ans), BER-RET-01 et PHI-RET-01 (65 ans).
- **Ordres de grandeur**, population de 2026 :

| Âge cible | Retraités | Pensions brutes | Effet statique d'OpenFisca | Moteur, pensions en 2032 |
|---|---|---|---|---|
| 62 ans | +0,67 million | +18,4 Md€ | −27,1 Md€ | 23,5 Md€ |
| 60 ans | +1,7 million | +45 Md€ | −55,7 Md€ | 48,1 Md€ |
| 65 ans | −0,35 million | −8 Md€ | +8,4 Md€ | — |

  L'effet statique d'OpenFisca compte aussi les prélèvements perdus sur les revenus d'activité, ce que le moteur
  compte par le canal des seniors.
- **Couverture du budget « ménages »** (seuil de publication des déciles : 80 %) :
  - Bertrand 65 → 90 %
  - Roussel 31 → 76 %
  - Philippe 38 → 64 %
  - Glucksmann 29 → 63 %
  - Mélenchon 39 → 63 %
  - Le Pen 15 → 55 %
  - Tondelier 35 → 51 %
- **Minimum de pension des carrières complètes** (`population: {pension_minimum: {mensuel_brut}}`) :
  - La population n'a pas la durée de carrière : une pension brute au-dessus de 1 000 € par mois
    (`microsimulation.plancher_carriere_complete`, minimum contributif majoré et complémentaire) est lue comme une
    carrière complète.
  - Ces pensions sont portées au minimum. Pour LFI-RET-03, SMIC net de 1 700 €, soit ≈ 1 870 € brut : 4,3 millions
    de retraités, ≈ +20 Md€ bruts. Cela retrouve l'encadrement du moteur (4,3 millions, ≈ 350 € par mois, 22 Md€
    au prudent).
  - Effet statique d'OpenFisca : −17,3 Md€, après la CSG et l'impôt sur le revenu repris.
  - Couverture de Mélenchon : 63 → 74 %.
- **Non représentés :** durée d'assurance, carrières longues, décote.

## Roadmap 3.4 et 3.5 : assurance chômage et prélèvements rendus aux actifs (22/11/2026)

- **Assurance chômage** (`population: {assurance_chomage: {programme, mesure, age_max?, seuil_mensuel?}}`) :
  - La population n'a ni la durée d'indemnisation ni l'ancienneté. Le montant vient donc du moteur, à plein effet,
    et se répartit au prorata de l'allocation des chômeurs concernés.
  - Codé pour huit mesures, même règle pour tous : ATT-EMP-01, BER-ECO-01, GLU-EMP-02, LFI-PRE-05, PHI-EMP-02
    (moins de 50 ans), RET-EMP-03, LIS-EMP-04, PRE-15. Exemple : Philippe, effet statique +2,3 Md€.
  - L'emploi passe par le canal de l'assurance chômage du programme. La micro n'en compte pas, et l'élasticité
    agrégée des transferts n'en compte plus non plus (`moteur/offre.effets`) : elle comptait ces mesures une seconde
    fois, pour quelques milliers d'emplois (Attal, Philippe, Retailleau, Lisnard, Glucksmann, Mélenchon). Écarts de
    solde primaire 2037 : moins de 0,02 point.
- **Cotisations salariales rendues** (variable OpenFisca `cotisations_salariales`, facteur) :
  - LIS-ECO-02 : −93,6 Md€ bruts ; effet statique −71,7 Md€, contre −72,0 au moteur.
  - RET-ECO-06 : −13,3 Md€ bruts ; effet statique −10,4 Md€.
  - Facteurs tirés des cotisations salariales de la population (≈ 106,6 Md€).
- **CSG d'activité** de 9,2 à 6,6 % (LIS-ECO-07) : effet statique −20,0 Md€.
- **Une seule voie** : une mesure dont une ligne passe par les prélèvements du travail (cellules) garde cette voie.
  Ses lignes de prestations (prime d'activité en moins…) ne repassent pas par la micro.
- **Couverture du budget « ménages »** (en %) :

| Programme | Couverture |
|---|---|
| Bertrand | 100 |
| Lisnard | 94 |
| Attal | 87 |
| Retailleau | 83 |
| Zemmour | 80 |
| Mélenchon | 78 |
| Philippe | 77 |
| Roussel | 76 |
| Glucksmann | 72 |
| Arthaud | 67 |
| Le Pen | 55 |
| Tondelier | 55 |

  Six programmes atteignent le seuil de 80 %, contre deux avant la roadmap 3.3. Ce qui reste tient surtout à la
  consommation : TVA et carburants (3.1, données de l'enquête Budget de famille en attente).

## Roadmap 3.1 : consommation par ménage (22/11/2026)

- **Données :** Insee, enquête Budget de famille 2017. Dépense annuelle moyenne par ménage, par poste de
  consommation et décile de niveau de vie (TF106, `parametres/donnees/bdf2017_tf106.csv`). Le tableau TF107 (même
  dépense par quintile, propriétaires et locataires) est archivé, mais pas encore utilisé.
- **Opération :** `formule: {nom: consommation, postes: [codes], programme, mesure}`
  (`outils/openfisca_mesures.gain_consommation`).
  - La population n'a pas la consommation. Le montant de la mesure vient du moteur, à plein effet, et se répartit
    entre ménages selon la dépense de leur décile pour ces postes.
  - La baisse de prix est entièrement répercutée, sans changement des quantités consommées.
- **Codé, même règle pour tous :**

| Mesure | Postes | Codes |
|---|---|---|
| RN-FIS-01, RN-ENE-03 | carburants et énergie du logement | 0722, 045 |
| RN-FIS-02, PCF-FIS-06 | alimentation | 011 |
| PCF-FIS-07, ZEM-FIS-01b, ART-ENE-02 | carburants | 0722 |
| GLU-ENE-03 | électricité | 0451 |

- **Ajout du 22/11 au chantier 3.3 :** LIS-RET-02 (âge de 65 ans), oubliée le 21/11.
- **Couverture du budget « ménages »** (en %) :

| Programme | Couverture |
|---|---|
| Bertrand | 100 |
| Lisnard | 98 |
| Roussel | 90 |
| Attal | 87 |
| Le Pen | 87 |
| Zemmour | 87 |
| Retailleau | 83 |
| Mélenchon | 78 |
| Philippe | 77 |
| Glucksmann | 77 |
| Arthaud | 74 |
| Tondelier | 55 |

  Huit programmes atteignent le seuil de 80 % (critère de la phase 3 : dix). Ce qui reste :
  - patrimoine (3.2) : taxe Zucman, ISF, successions ;
  - Tondelier : exonérations au-delà de 1,6 SMIC, cotisations vieillesse ;
  - congés parentaux.


## Roadmap 3.2 : patrimoine par ménage (22/11/2026)

- **Données :** Insee, enquête Histoire de vie et Patrimoine 2020-2021 (tableaux fournis par Adrien, archivés dans
  `parametres/sources/insee_hvp2021/`). Patrimoine brut moyen par ménage et parts de ses composantes (immobilier,
  financier, professionnel, résiduel, endettement), par tranche de revenu disponible du ménage : dixièmes D1 à D9,
  puis 90-95e et 95-99e centiles, puis 1 % du haut (`hvp_mtpatbrut_composante_fr.xlsx`, feuille REVDISP ;
  `parametres/donnees/hvp2021_patrimoine_revdisp.csv`). Exemples : 104 400 € en D1, 2,83 M€ pour le 1 % du haut.
- **Opération :** `formule: {nom: patrimoine, composante, tranches?, programme, mesure}`
  (`outils/openfisca_mesures.gain_patrimoine`).
  - La population n'a pas le patrimoine. Le montant de la mesure vient du moteur, à plein effet, et se répartit
    entre ménages selon le patrimoine moyen de leur tranche (net, ou immobilier pour l'IFI).
  - `tranches` limite le champ aux tranches visées : impôts réservés aux plus gros patrimoines.
- **Limites, à lire avec les déciles :**
  - les tranches sont de revenu disponible du ménage, pas de niveau de vie par unité de consommation ;
  - le premier dixième a plus de patrimoine que le deuxième (indépendants à faible revenu, patrimoine
    professionnel) ;
  - l'enquête n'atteint pas les très grandes fortunes : la taxe Zucman (au-delà de 100 M€) est entièrement mise
    sur le 1 % du haut, ce qui dit qui paie dans la population, pas la concentration réelle ;
  - successions : patrimoine du ménage lui-même, comme approximation de celui des héritiers.
- **Codé, même règle pour tous (DÉCISION, à valider par Adrien) :**

| Mesure | Composante | Tranches |
|---|---|---|
| GLU-FIS-01 (plus gros héritages) | net | 95-99e, 1 % |
| ZEM-FIS-02, RET-FIS-02 (droits de succession) | net | toutes |
| LIS-FIS-04 (transmissions, taux marginal) | net | 90-95e, 95-99e, 1 % |
| LFI-REC-05, PCF-FIS-01 (ISF) | net | 90-95e, 95-99e, 1 % |
| LIS-FIS-02 (IFI) | immobilier | 95-99e, 1 % |
| LFI-REC-06, PCF-FIS-02, REC-01 (impôt plancher) | net | 1 % |

  ZEM-FIS-02 est calculée par la bibliothèque (pas de montant fixe) : `montant_md` −20,6 Md€ de 2026 (22,8 Md€
  courants en 2032 au prudent), à reprendre si le moteur change.
- **Pensions calées sur le moteur (3.3) :** l'opération `population.pensions` accepte `programme` et `mesure` à la
  place de `facteur`. ART-RET-01 (sous-indexation du budget 2027 annulée) : pensions au-delà de 1 550 € brut par
  mois (85 % du SMIC brut de 2026, DÉCISION) relevées du montant du moteur, pour toujours.
- **Couverture du budget « ménages »** (en %) :

| Programme | Couverture |
|---|---|
| Arthaud | 100 |
| Bertrand | 100 |
| Lisnard | 100 |
| Zemmour | 100 |
| Roussel | 97 |
| Attal | 87 |
| Le Pen | 87 |
| Retailleau | 86 |
| Glucksmann | 83 |
| Mélenchon | 82 |
| Philippe | 77 |
| Tondelier | 59 |

  Dix programmes atteignent le seuil de 80 % : critère de la phase 3 rempli. Ce qui reste : Tondelier
  (exonérations au-delà de 1,6 SMIC, cotisations vieillesse), Philippe (heures au-delà de 35 h), congés parentaux.

## Roadmap 4.1 : champ et secteurs de la population d'entreprises (22/11/2026)

- **Erreur corrigée :** la population suit le champ d'Ésane (marchand non agricole et non financier), mais recevait
  les nombres, pertes et bénéfices de toutes les entreprises à l'IS de la DGFiP, finance comprise. Son IS valait
  67,7 Md€, contre 57,0 dans le champ (70,5 au total, dont finance 12,7 et agriculture 0,7).
- **Correction** (`microsimulation.entreprises_champ_esane`, DGFiP Statistiques n° 51, tableau 1) : nombres et pertes
  à 90,0 % (entreprises du champ), bénéfices à 77,2 % (résultat fiscal du champ).
- **IS par secteur** (`microsimulation.entreprises_is_secteurs_2025`) : les bénéfices de chaque groupe de secteurs sont
  calés sur son IS brut de 2025. Les tailles gardent la part des bénéfices de la DGFiP.

| Groupe | IS de la population avant (Md€) | Après | DGFiP 2025 |
|---|---|---|---|
| Industrie | 18,5 | 14,7 | 14,7 |
| Construction | 5,4 | 5,4 | 5,4 |
| Commerce et transports | 16,8 | 17,7 | 17,7 |
| Services (dont santé et enseignement marchands) | 26,8 | 19,2 | 19,2 |
| **Total** | **67,7** | **57,0** | **57,0** |

- **Effet sur les chiffrages :** l'IS des mesures reste ramené au total national (70,47 Md€, finance supposée réagir
  comme les autres, inchangé). Ce qui change : la répartition entre secteurs et tailles et le retour d'IS des impôts de
  production (LIS-FIS-01 et PHI-FIS-01 : −22,1 → −21,1 Md€ ; RN-FIS-04 : −9,7 → −9,2 ; RET-FIS-01 : −5,6 → −5,3 ;
  REC-35 : +6,3 → +6,0). `parametres/donnees/population_entreprises_2023.csv` régénérée ; `sorties/micro_entreprises.csv`
  à régénérer.

## Roadmap 4.2 : répercussion sur les prix des impôts des entreprises (22/11/2026)

- **Avant :** ce que les mesures laissent ou prennent aux entreprises allait pour moitié aux salaires (Fuest, Peichl et
  Siegloch, 2018) et pour moitié aux actionnaires ; rien aux prix, faute de source.
- **Maintenant :** 31 % aux prix (`entreprises.incidence_menages.prix`), d'après Baker, Sun et Yannelis (NBER WP 27058 :
  31 % de l'impôt sur les sociétés des États américains retombe sur les consommateurs ; plus de 40 % dans leur
  révision de 2023, d'où la borne basse). Il reste 19 % aux actionnaires.
- **Répartition par décile :** les prix au prorata de la consommation du décile (Budget de famille 2017, TF106), et non
  plus du revenu initial.
- **Effet sur le solde :** seulement par le retour des prélèvements sur les dividendes, qui baisse (la part des prix
  n'a pas de retour au budget). Écarts 2037 au prudent : au plus 0,02 point (Lisnard −0,02).
- **À valider par Adrien :** la somme vient de deux études et de deux pays. Avec Baker et al. seuls : salaires 38 %,
  prix 31 %, actionnaires 31 %.

## Roadmap 3.6 : niveaux de vie, diagnostic (22/11/2026, pas de recalage)

- **Écart :** médiane de la population 24 450 € par UC (2026) ; Insee 26 740 € en 2024 (ERFS, Insee Première
  n° 2117), soit ≈ 27 300 € de 2026 sans croissance réelle : −10 %. Moyenne : ≈ 28 000 € contre ≈ 31 600 €.
- **Ce qui n'explique pas l'écart :** les masses de revenus sont proches des comptes à 5 % près (salaires bruts
  1 021 Md€, pensions 393, revenus d'indépendants 86, chômage 21,5). Les parts dans le niveau de vie autour de la
  médiane ressemblent à celles de l'ERFS 2021 (Revenus et patrimoine des ménages 2024, fiche 1.4).
- **Ce qui l'explique en partie :** les revenus du patrimoine. Ils font 3 à 3,7 % du niveau de vie autour de la
  médiane dans l'ERFS (8,8 % en moyenne, revenus des livrets et de l'assurance-vie imputés depuis l'enquête
  Patrimoine), contre ≈ 1 % dans la population. Une imputation à partir de l'enquête Histoire de vie et Patrimoine
  (3.2) en rattraperait 2 à 3 points.
- **Reste à comprendre** (≈ 7 points) : champ (l'ERFS exclut les ménages dont la personne de référence est étudiante,
  la métropole seule), échelle d'UC, prélèvements. Il faut la composition du revenu disponible par décile de l'ERFS
  2024 (Insee Résultats « Revenu, niveau de vie et pauvreté en 2024 », tableaux en xlsx, que l'environnement ne peut pas
  télécharger).
