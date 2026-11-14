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
| Mélenchon | Garantie d'autonomie au seuil de pauvreté | − 48,1 | − 28,0 | Le bas de la distribution est trop pauvre dans la population (1er décile : 8 600 € par an et par unité de consommation) : **la micro surestime** ; à recaler sur le taux et l'intensité de la pauvreté de l'Insee |
| Le Pen | IR nul avant 30 ans (jusqu'à 4 SMIC) | − 6,5 | − 3,7 | Montaigne : 3,7 à 4,1 ; jeunes trop imposés dans la population ? à vérifier |
| Le Pen | ASF doublée | − 4,2 | − 1,3 | Le moteur prend l'ASF à 1,6 Md€, la Cnaf donne 3,1 Md€ en 2024 : **le moteur sous-estime** ; la population la surestime un peu (4,2 / 2 = 2,1 de base… à revoir avec le montant moyen) |
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
