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
