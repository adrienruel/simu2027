# Banc d'essai du noyau : chocs standard contre modèles publiés (21/11/2026)

`outils/banc_essai.py` → `sorties/banc_essai.csv`. Question d'Adrien : « le modèle est hyper rigide, chaque
changement ne rapporte rien ». Rien n'est réglé ici : on rejoue dans le noyau des chocs dont la réponse est publiée
pour d'autres modèles. Scénario médian (le prudent est proche), choc permanent à partir de t = 2031.

Sources :
- OFCE, document de travail 2026-9 (Mésange et ThreeME) : https://www.ofce.fr/wp/2026/9/OFCEWP2026-9.pdf ;
- DG Trésor pour le COR (mars 2026), âge d'ouverture des droits de 64 à 65 ans ;
- Fipeco (2024), recul de deux ans : +0,9 point, dont 0,5 pour les retraites et 0,4 pour les autres
  administrations ;
- COR, rapport annuel 2026, partie 2, chapitre 5 : productivité de 1 % au lieu de 0,7 %.

## 1. Dépense publique +1 point de PIB : conforme à Mésange

| Solde primaire (pt de PIB) | t | t+1 | t+4 | t+9 | LT |
|---|---|---|---|---|---|
| simu2027 | −0,50 | −0,41 | −0,58 | −0,76 | −0,83 |
| Mésange | −0,53 | −0,34 | −0,53 | −0,68 | −0,85 |
| ThreeME | −0,72 | −0,57 | −0,49 | −0,53 | −0,71 |

Le PIB suit aussi : +0,84 % à t contre +0,76 %, +0,70 % à t+4 contre +0,88 %. C'est attendu, puisque le bouclage
est calé sur Mésange : ce n'est donc pas une validation.

## 2. TVA −1 point de PIB : l'activité rend moins au budget que dans Mésange

| Solde primaire (pt de PIB) | t | t+1 | t+4 | t+9 | LT |
|---|---|---|---|---|---|
| simu2027 | −1,02 | −0,61 | −0,56 | −0,63 | −0,57 |
| Mésange | −0,80 | −0,37 | −0,37 | −0,44 | −0,47 |
| ThreeME | −0,89 | −0,68 | −0,40 | −0,33 | −0,29 |

Le PIB est proche de Mésange (+0,75 % à t+4 contre +0,81 %), mais le budget récupère environ 0,2 point de moins.
Une baisse d'impôt coûte donc plus cher que dans Mésange, et une hausse d'impôt rapporte plus.

## 3. Productivité +1 % : plus favorable que Mésange à 10 ans, moins à long terme

| Solde primaire (pt de PIB) | t | t+4 | t+9 | t+29 | LT |
|---|---|---|---|---|---|
| simu2027 | +0,11 | +0,11 | +0,11 | +0,05 | +0,03 |
| Mésange | −0,04 | 0,00 | +0,05 | +0,14 | +0,18 |
| ThreeME | −0,01 | −0,14 | −0,05 | +0,06 | +0,07 |

Où part un euro de PIB en plus (2031) : recettes +0,49 ; dépenses +0,40, dont santé 0,10, collectivités 0,08,
missions 0,07, investissement 0,04, défense 0,03, autres 0,03. En 2073, s'y ajoutent les pensions (+0,13), qui
rattrapent les salaires. Toutes ces dépenses suivent le PIB ou les salaires **dès l'année même**. C'est la
convention du statu quo, et c'est ce qui ramène le gain au solde vers zéro à long terme.

Pensions seules (variante haute du COR, +0,3 point de productivité par an) : dépenses de retraite −1,1 point de PIB
en 2070, contre −0,8 point pour le COR. Sur ce poste, le modèle est **plus** favorable à la productivité que le COR.

Artefact trouvé : les dépenses sont indexées en rapport à 2029 (indice 1). Un gain de productivité dès 2029
échappe donc à toute indexation, avec un dividende de 40 % au lieu de 9 %. Les chocs du banc partent de 2031. Les
mesures des programmes partent presque toutes après 2029, mais c'est à vérifier.

## 4. Âge d'ouverture des droits de 64 à 65 ans : 60 % de l'effet de la DG Trésor

| Solde public (pt de PIB) | 5 ans | 20 ans |
|---|---|---|
| simu2027, toute l'économie gardée | +0,26 | +0,29 |
| simu2027, part gardée de Bertrand (0,65) | +0,17 | +0,19 |
| DG Trésor (COR, mars 2026) | +0,4 | +0,5 |

Décomposition, médian, à 20 ans :

| | simu2027 | Fipeco, pour un an de recul |
|---|---|---|
| Pensions en moins | +0,26 | ≈ +0,25 |
| Reste du budget | **≈ 0** : recettes +0,06, autres dépenses −0,04 | ≈ +0,2 |
| Emploi | +112 000 | |
| PIB | +0,26 % | |

Le PIB en plus ne revient au budget qu'à environ 25 %, contre 53 % pour la DG Trésor (taux de prélèvements
obligatoires).

## Constats
1. **Ce n'est pas la dépense ni le multiplicateur :** ils sont conformes à Mésange.
2. **Le retour de l'activité au budget est faible.** Quand une mesure crée des emplois ou de l'activité, le budget
   en récupère environ 25 à 35 %, contre environ 50 % dans Mésange et dans le modèle comptable de la DG Trésor.
   C'est l'écart principal (âge, TVA). À vérifier : si le dividende de productivité, pensé pour des salaires plus
   hauts, s'applique aussi aux emplois en plus (qui ne relèvent pas les salaires par tête), et ce que vaut
   `emploi.valeur_emploi` contre le taux de prélèvements de 53 %.
3. **L'emploi des seniors est bas :** environ 110 000 emplois pour un an d'âge, avec 58 % des seniors maintenus
   qui deviennent inactifs (`seniors.part_concernee` = 42 %, déjà au chantier 2.3 de la roadmap).
4. **L'indexation immédiate de toutes les dépenses sur le PIB** efface à long terme le gain de la productivité.
   C'est une convention à revoir bloc par bloc (missions et défense votées en euros, ONDAM, chantier 1.2).
5. **Les pensions ne sont pas trop rigides :** elles répondent plus que celles du COR à la productivité.

## Diagnostic du retour de l'activité (21/11/2026, suite)

Décomposition au médian : PIB en plus, recettes en plus et blocs qui bougent (Md€).

| Choc, année | PIB | Emplois | PIB par emploi | Recettes en plus, hors choc direct | Blocs |
|---|---|---|---|---|---|
| Dépense +1 pt, 2035 | +23,3 | +49 000 | — | +12,0, soit 51 % du PIB | chômage −0,3 |
| TVA −1 pt, 2035 | +24,9 | +121 000 | — | +12,5, soit 50 % du PIB | chômage −0,8 |
| Âge 65 ans, 2039 | +7,5 | +108 000 | 69 000 € | +1,2, soit 16 % du PIB, net des prélèvements sur les pensions en moins | pensions −10,1 ; chômage +0,9 ; AAH et invalidité +0,4 |

1. **Quand l'activité vient de la demande** (dépense, TVA), les recettes rendent environ 50 % du PIB en plus :
   c'est le taux de prélèvements, comme chez la DG Trésor. Pas de rigidité là.
   - Pour la TVA, l'écart restant avec Mésange (0,2 point) vient probablement de l'effet prix. Dans Mésange, la
     baisse de TVA fait baisser les prix, donc les dépenses indexées sur les prix ; dans le modèle, les comptes sont
     en euros constants. Non vérifié dans le code.
2. **Quand l'activité vient d'emplois en plus, le budget ne reçoit pas les prélèvements sur le PIB que ces
   emplois créent : il reçoit une valeur fixe par emploi.**
   - Canaux communs : `programme_commun.emploi_valeur_emploi`, 20 000 € (un emploi au SMIC, prélèvements, TVA et
     chômage évité), avec une valeur ajoutée de 35 000 € par emploi.
   - Seniors : `seniors.valeur_emploi`, 27 000 €. Or le canal des seniors ajoute environ 69 000 € de PIB par
     emploi : le budget n'en reçoit que 39 %, contre 50 à 53 % de prélèvements. C'est une incohérence interne
     (environ 1,8 Md€, 0,05 point, pour un an d'âge).
   - Tous les emplois créés sont implicitement des emplois au SMIC (35 000 € de PIB) : une mesure qui crée ou
     prolonge des emplois moyens (âge de départ, qualifications, immigration de travail) est sous-évaluée en PIB
     comme en recettes. C'est le chantier 2.2 de la roadmap (valeur d'un emploi selon son salaire), qui devient
     prioritaire.
   - Les seniors maintenus en activité qui ne trouvent pas d'emploi coûtent en chômage et en AAH (+1,3 Md€) : c'est
     un vrai effet, qui dépend de la part de 42 % (chantier 2.3).
3. **Quand l'activité vient de la productivité,** environ 40 % du PIB en plus part tout de suite en dépenses
   indexées (section 3) : le retour tombe à environ 9 %, puis vers 0. C'est le chantier 1.2 (indexation des blocs).

### Correction proposée (noyau, à faire après la fusion de `phase-q`)
- **Un seul prix par emploi, cohérent avec son PIB :** chaque canal déclare le salaire des emplois qu'il crée
  (0,8 à 3 SMIC). Le PIB en plus et les recettes en plus (prélèvements calculés par OpenFisca, TVA, IS sur la
  valeur ajoutée) viennent du même niveau de salaire. Un emploi senior prolongé est un emploi à son salaire, pas un
  emploi au SMIC.
- **Test du banc à ajouter :** pour tout canal d'emplois, les recettes en plus rapportées au PIB en plus restent
  entre 40 et 55 %.
- **Effet attendu :** l'âge de départ passe d'environ +0,29 à environ +0,35 ou +0,40 point à 20 ans. Les mesures
  qui créent des emplois qualifiés y gagnent, celles qui créent des emplois au SMIC ne changent presque pas.

## Correction 1 : les dépenses ne suivent plus la croissance d'un programme (21/11/2026)

Demande d'Adrien : « ne pas augmenter les budgets sur la croissance, mais sur quelque chose de plus cohérent ».

La croissance d'un programme ne fait monter les dépenses que par le dividende de productivité
(`statu_quo.dividende_programme`). Les blocs du statu quo ne répondent pas à la demande. La nouvelle règle est dans
`statu_quo._depenses_en_plus`, avec les paramètres `indexation_programme` :
- **Réponse entière** pour les blocs dont le coût suit un salaire par une règle de droit :
  - pensions (loi et carrières) ;
  - chômage (allocation proportionnelle au salaire perdu) ;
  - prestations, selon `statu_quo.indexation_prestations`. Elles sont sur les salaires d'après la décision
    d'Adrien de novembre 2026 ; sur les prix, elles ne bougeraient pas.
- **Part salariale seulement** pour la santé (0,6), les missions (0,4), les collectivités (0,3) et les autres (0,3) :
  - elle suit à 100 / 100 / 75 / 50 % (crise / prudent / médian / optimiste) ;
  - en moyenne mobile sur 3 / 5 / 7 / 10 ans.
- **Aucune réponse** pour l'investissement et la défense, programmés en euros, puis en cible de PIB du statu quo.
- Le statu quo lui-même garde son indexation actuelle : c'est le chantier 1.2, qui reste à sourcer bloc par bloc.

Choix par défaut du 21/11/2026, révisables : prestations gardées sur les salaires, défense en cible de PIB du statu
quo, passage des salaires publics selon le scénario.

### Effet
Dividende d'un euro de PIB dû à la productivité, statu quo, médian :

| | 2030 | 2038 | 2050 | 2073 |
|---|---|---|---|---|
| Avant | 0,25 | 0,12 | 0,11 | 0,01 |
| Après | 0,46 | 0,39 | 0,36 | 0,28 |

Banc, productivité +1 % due à un programme (solde primaire, points de PIB), rapporté au point de PIB en plus :

| | t+9 | Long terme |
|---|---|---|
| simu2027, après | +0,36 | +0,26 |
| Mésange | +0,05 / 0,61 = +0,08 | +0,18 / 0,89 = +0,20 |
| ThreeME | — | +0,07 / 0,76 = +0,09 |

À long terme, le modèle est maintenant en ligne avec Mésange. À moyen terme, il est plus favorable : dans Mésange,
le PIB et l'emploi mettent du temps à suivre la productivité (le chômage monte d'abord), alors que dans le modèle,
la productivité passe tout de suite au PIB.

Programmes, écart de solde primaire au statu quo, prudent (points de PIB) :

| | 2037 avant → après | 2050 avant → après |
|---|---|---|
| Lisnard | −2,83 → −2,76 | −3,73 → −3,65 |
| Retailleau | −0,43 → −0,40 | −0,82 → −0,78 |
| Philippe | −1,02 → −1,01 | −1,70 → −1,69 |
| Zemmour, Bertrand | inchangés | inchangés |
| Attal | −1,10 → −1,17 | −1,32 → −1,44 |
| Le Pen | −2,26 → −2,33 | −2,78 → −2,88 |
| Glucksmann | −2,60 → −2,71 | −2,92 → −3,07 |
| Tondelier | −2,60 → −2,84 | −3,47 → −3,81 |
| Arthaud | −4,05 → −4,62 | −4,59 → −5,47 |
| Roussel | −8,86 → −9,20 | −8,68 → −9,18 |
| Mélenchon | −11,40 → −11,66 | −12,09 → −12,47 |

La règle est symétrique. Un programme qui fait baisser la production (moins d'heures, plus d'impôts sur le capital)
ne voit plus ses dépenses baisser avec elle : il perd davantage. Un programme qui la fait monter garde davantage de
son gain. Les écarts entre programmes s'élargissent, surtout vers le bas, parce que les canaux d'offre de la plupart
des programmes sont petits ou négatifs.

## Correction 2 : la valeur d'un emploi suit le barème du programme (21/11/2026)

Demande d'Adrien : moduler la valeur d'un emploi selon le coût de l'assurance chômage du programme et selon son
manque à gagner en impôt.

- **Assurance chômage : déjà fait** (roadmap 5.4, phase L). L'allocation évitée est sortie de la valeur d'un emploi
  et passe par le bloc chômage, au coût d'un chômeur du programme (`programme_simple.generosite`). Coût d'un chômeur
  par rapport au statu quo, en 2037, au prudent :

  | Programme | Bloc chômage | Bloc pauvreté |
  |---|---|---|
  | Mélenchon | 1,13 | 2,52 |
  | Tondelier | 1,16 | 1,21 |
  | Attal | 0,94 | 0,78 |
  | Philippe | 0,94 | 0,92 |
  | Retailleau | 0,90 | 0,56 |

- **Manque à gagner en impôt : nouveau** (`moteur/emploi_valeur.py`, `emploi.prelevements_programme`).
  - Les prélèvements et la TVA d'un emploi type sont calculés au barème du programme : 1,3 SMIC pour les canaux,
    coût moyen pour les seniors.
  - Chaque mesure de recettes sur le travail touche l'emploi selon son incidence, avec la règle du canal d'offre
    (`offre.base_incidence`) ; les mesures sur la consommation jouent au prorata de la TVA et des accises.
  - Facteur en 2037, au prudent, pour un emploi à 1,3 SMIC : Lisnard 0,87 ; Zemmour 0,89 ; Roussel 0,95 ;
    Attal 0,95 ; Philippe 0,99 ; Mélenchon 1,00 (ses hausses portent sur les hauts revenus) ; Tondelier 1,04.
- **Effet :** au plus 0,03 point d'écart de solde primaire (Roussel −9,20 → −9,17, Lisnard −2,76 → −2,77). Les
  emplois qui pèsent le plus (SMIC, 32 heures, emplois aidés, canal d'offre) ont déjà leur propre calcul budgétaire
  au barème de la mesure ; la modulation ne touche que les canaux génériques et les seniors. C'est un gain de
  cohérence, pas un levier.

Reste ouvert : les impôts sur la part non salariale de la valeur ajoutée (IS, impôts de production) ne sont pas dans
la valeur d'un emploi. Pour un senior, le budget reçoit 37 % du PIB qu'il crée, contre 45 à 53 % de prélèvements.

## Correction 3 : impôts sur la marge d'un emploi (21/11/2026)

`emploi_valeur.excedent`, paramètre `emploi.taux_impots_excedent` = 0,22. C'est l'IS (69,5 Md€) plus les impôts de
production hors facteur travail (40,7 Md€), rapportés à l'EBE des sociétés non financières (497,5 Md€).
- Il s'applique à la part non salariale de la valeur ajoutée d'un emploi en plus :
  - environ 6 000 € pour un emploi des canaux (35 000 € de valeur ajoutée, 29 000 € de coût), soit environ 1 300 €
    d'impôts par an ;
  - environ 21 400 € pour un senior (75 000 € de valeur ajoutée, 53 600 € de coût), soit environ 4 700 € par an.
- Le programme le module par ses mesures sur les entreprises (instrument capital_entreprises), au prorata de l'IS
  et des impôts de production du statu quo.
- Choix prudent : la fiscalité des dividendes distribués n'est pas comptée.

Âge 64 → 65 ans (médian) : +0,27 point à 5 ans et +0,31 à 20 ans (avant : +0,26 et +0,29 ; DG Trésor : +0,4 et
+0,5). Le PIB en plus revient au budget à environ 45 % pour un senior. Le reste de l'écart avec la DG Trésor vient
surtout du nombre d'emplois : 110 000 par an d'âge, avec 58 % des seniors maintenus qui deviennent inactifs
(chantier 2.3).

Programmes, écart de solde primaire au statu quo, prudent, 2037 :
- Mélenchon −11,66 → −11,79 et Roussel −9,17 → −9,29 : ils détruisent des emplois dans les canaux génériques, et
  chaque emploi perdu coûte l'IS de sa marge, plus élevé chez eux, puisqu'ils relèvent l'IS ;
- Glucksmann −2,70 → −2,76 ; Le Pen −2,33 → −2,37 ;
- Philippe −1,01 → −0,99 ; Lisnard −2,77 → −2,76 ;
- les autres à 0,01 point près.

### Bilan des trois corrections (prudent, 2037)

| | Départ | Après les trois corrections |
|---|---|---|
| Bertrand | +0,03 | +0,04 |
| Retailleau | −0,43 | −0,40 |
| Philippe | −1,02 | −0,99 |
| Attal | −1,10 | −1,17 |
| Le Pen | −2,26 | −2,37 |
| Zemmour | −2,40 | −2,40 |
| Glucksmann | −2,60 | −2,76 |
| Tondelier | −2,60 | −2,84 |
| Lisnard | −2,83 | −2,76 |
| Arthaud | −4,05 | −4,65 |
| Roussel | −8,86 | −9,29 |
| Mélenchon | −11,40 | −11,79 |
