# Bloc emploi unifié (étape 4)

Code : `moteur/emploi_canaux.py` (emplois par mesure et par canal, gain par emploi selon le canal) ;
branché sur la macro par `emploi.gain_par_canal` (la v235 se reproduit avec la valeur `false`).

## Les canaux

| Canal | Ce qui se passe | Mesures |
|---|---|---|
| Offre | Le chômeur ou l'inactif reprend un emploi parce que travailler rapporte plus ou qu'il est mieux formé | allocation chômage remplacée par le RUI, sélection et apprentissage, alternance, RUI au prorata des bas salaires (marge intensive comprise) |
| Appariement | L'offre et la demande se rencontrent mieux | France Travail recentré sur le conseil, accompagnement par l'IA, droit à construire |
| Coût du travail | L'employeur embauche parce que le travail coûte moins ou est moins risqué | baisse ciblée du coût jusqu'à 1,3 SMIC, impôts de production assis sur les salaires (réforme des entreprises), SMIC revalorisé sur la croissance, prime d'embauche jeune, accords d'entreprise, contrat assoupli, horaires des commerces |
| Localisation | Des activités rentables partent (ou viennent) selon l'imposition des bénéfices | réforme des entreprises (IS à 45 %) |
| Population active | Des emplois s'ajoutent sans venir du chômage | emploi des seniors (âge de départ), cumul emploi-socle |
| Perdus | Emplois subventionnés qui disparaissent | insertion par l'activité, territoires zéro chômeur, contrats aidés, fin de la prime jeune |
| Demande (conjoncture) | L'ajustement budgétaire réduit l'activité les premières années | multiplicateur et loi d'Okun (module macro) |

## Règles contre le double compte

1. **Un emploi n'est compté qu'une fois.** Toutes les réformes qui réduisent le chômage passent par une
   seule courbe de rendements décroissants : la baisse totale ne peut pas dépasser l'écart au chômage
   incompressible. Chaque mesure reçoit une part de la baisse proportionnelle à son effet propre.
2. **La population active est à part.** Les emplois des seniors et du cumul ne viennent pas du chômage :
   ils sont hors de la courbe et ne baissent pas le taux de chômage.
3. **Deux canaux, deux assiettes.** La réforme des entreprises joue sur le coût du travail (assiette : les
   impôts assis sur les salaires) et sur la localisation (assiette : le taux effectif sur les bénéfices).
4. **Chaque emploi rapporte selon son salaire.** Gagné par l'offre, l'appariement ou le coût du travail : au
   SMIC, faute de source sur le salaire des emplois créés (prudent : ils rapportent moins). Perdu par
   localisation : au coût moyen du privé (les activités mobiles sont rentables). Seniors : salaire médian.
5. **Le gain par emploi est celui du nouveau système** : impôt unique, impôt local, RUI économisé pour
   la part des embauchés qui le touchaient, TVA aux taux du nouveau système sur la consommation en plus.

## Effet (prudent)

Gain par emploi au SMIC : 11 556 € par an (la v235 comptait 15 161 € pour un emploi à 1,3 SMIC, avec la TVA
de l'ancien système) ; emploi perdu par localisation : 31 512 € ; emploi d'un senior : 23 822 €.
Déficit publié du prudent : 5,33 % / 4,74 % / 3,81 % en 2029 / 2032 / 2037 (avant : 5,33 / 4,71 / 3,73) ; puis 5,28 % / 4,59 % / 3,64 % avec les taux effectifs pour la localisation.

## Recouvrements et manques encore ouverts

- **Localisation, érosion réelle de l'IS et investissement : corrigé le 29 octobre.** La hausse de l'IS à
  45 % joue sur trois décisions, chacune selon le taux qui la gouverne (`moteur/taux_effectifs.py`) :
  - le **transfert de bénéfices** (montages comptables) suit le **taux légal** : 45 % contre 25 %, la déduction
    de l'investissement n'y change rien ; c'est l'essentiel de l'érosion de l'IS (≈ 14 % de l'assiette des
    grandes entreprises dans le prudent, ≈ −21 Md€ par an) ;
  - la **localisation** des activités rentables et la **réaction réelle** de l'assiette suivent le **taux
    effectif moyen** (Devereux et Griffith), qui tient compte de la déduction immédiate et de la fin des
    impôts de production : 32,8 % aujourd'hui, 41,3 % dans le prudent (60 % de l'investissement déduit
    immédiatement), 39,0 % dans l'optimiste. Hausse de 8,5 points au lieu de 14 avec le taux légal ;
  - l'**investissement** à la marge suit le coût du capital : la déduction immédiate le fait baisser,
    l'investissement monte (+0,6 Md€ sur le solde en 2037, +2,4 Md€ en 2050).
  Emplois perdus par localisation dans le prudent : 101 000 au lieu de 178 000. Les trois effets sont
  cohérents avec la théorie : la déduction exonère le rendement normal (l'investissement monte), mais la rente
  reste taxée à 45 % (les activités les plus rentables restent plus mobiles), et les bénéfices comptables
  suivent le taux légal.
- **Valeur ajoutée par emploi** : l'effet d'un emploi sur le PIB compte toute la valeur ajoutée (part du
  capital comprise), alors que le capital a son propre canal. Effet sur le ratio de déficit très faible.
- **Canal manquant : le RUI des inactifs.** Un revenu garanti sans condition d'activité peut réduire la
  participation (second apporteur de revenu, jeunes). Rien ne le chiffre aujourd'hui.
- **Réactions à l'impôt des classes moyennes et des hauts revenus** : elles passent par le module des
  hauts revenus (élasticité du revenu imposable), pas par le bloc emploi. C'est le canal « offre » à la
  marge intensive pour les revenus moyens et élevés ; il n'est pas compté deux fois.


## Canal ajouté le 29 octobre 2026 : participation des inactifs

Des personnes du halo du chômage (1,93 million en 2025, Insee) prennent un emploi parce que travailler rapporte
davantage dans le nouveau système : au mi-temps au SMIC, une personne seule garde 59 % de ce qu'elle gagne en
plus, contre 36 % aujourd'hui (OpenFisca, RSA, prime d'activité et aides au logement compris) ; au temps plein,
47 % contre 42 %. Emplois = élasticité de participation × variation moyenne du log de la part gardée × base :
élasticité 0 en crise, 0,1 dans le prudent, 0,2 médian, 0,3 optimiste (Chetty et al., 2013 ; Bargain, Orsini et
Peichl, 2014). Prudent : ≈ 59 000 emplois à terme (suivent la population de 18 à 64 ans). Ils s'ajoutent à
l'emploi sans réduire le taux de chômage (ces personnes n'y sont pas comptées), au coût de 0,75 SMIC. Distinct
du canal « bas salaires », qui porte sur les chômeurs.
