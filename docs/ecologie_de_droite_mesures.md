# « Écologie de droite » mesure par mesure contre le statu quo (4 novembre 2026)

`programmes/ecologie_de_droite/programme.py`, noyau `moteur/noyau.py`. `python -m moteur.noyau` imprime le bilan.
Première passe du recodage du programme sur le noyau (feu vert d'Adrien : on cherche la vérité, pas à retrouver les
résultats actuels).

## Ce qui est fait

- **Recettes, instrument par instrument** : chaque impôt du programme contre les impôts actuels qu'il remplace (statu
  quo impôt par impôt), avec la même évolution que le moteur du programme. Contrôle : rien de non réparti (écart nul).
- **Dépenses, ligne par ligne** : chaque ligne du registre du programme dans son poste ; les blocs du statu quo que ce
  poste remplace sont retirés.
- **Périmètre** : collectivités (ressources propres et dépenses) et ventes et tarifs de l'État, des opérateurs et des
  hôpitaux (79,7 Md€ en 2025, Insee), que le statu quo compte en brut, remis des deux côtés (sans effet sur le solde).
- **Effets macroéconomiques** : une mesure par canal, règle de trajectoire comprise.
- Les résultats du programme sont inchangés (reproduits à 1e-13 près) : cette passe rend le chiffrage lisible, elle ne
  le recalcule pas encore mesure par mesure.

## Bilan (prudent, Md€ de 2026, + = améliore le solde par rapport au statu quo)

| Mesure | 2029 | 2037 | 2050 | 2073 |
|---|---|---|---|---|
| **Budget** | | | | |
| Remplacé par « Retraites : socle, transition et ancien système » : retraites (statu quo) | +428,0 | +465,0 | +492,8 | +565,8 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Autres dépenses : point de départ (2029) | -363,1 | -363,1 | -363,1 | -363,1 |
| Santé : trajectoire et mesures — Santé : trajectoire des dépenses | -313,8 | -336,8 | -394,7 | -523,5 |
| Remplacé par « Santé : trajectoire et mesures » : sante (statu quo) | +301,5 | +328,5 | +385,4 | +510,7 |
| Remplacé par « Autres dépenses du programme (ministères, collectivités, mesures) » : collectivites (statu quo) | +230,3 | +245,9 | +266,8 | +296,5 |
| Remplacé par « Autres dépenses du programme (ministères, collectivités, mesures) » : etat_missions (statu quo) | +210,4 | +220,0 | +234,8 | +254,8 |
| Retraites : socle, transition et ancien système — Retraites : socle, point de départ (2029) | -220,0 | -220,0 | -220,0 | -220,0 |
| Recettes non fiscales actuelles (versées au fonds ; part locale remise par le périmètre) | -191,4 | -203,7 | -219,0 | -229,1 |
| Retraites : socle, transition et ancien système — Transition des retraites : coût net | -206,9 | -191,6 | -160,5 | -25,6 |
| Remplacé par « Investissement : subventions restées à l'État, renouvelables » : investissement (statu quo) | +133,6 | +142,3 | +152,9 | +160,0 |
| Revenu universel et AAH — RUI et AAH : point de départ (2029) | -130,1 | -130,1 | -130,1 | -130,1 |
| Remplacé par « Autres dépenses du programme (ministères, collectivités, mesures) » : autres (statu quo) | +106,4 | +113,7 | +123,3 | +137,1 |
| Remplacé par « Autres dépenses du programme (ministères, collectivités, mesures) » : defense_ue (statu quo) | +87,5 | +93,2 | +100,2 | +104,8 |
| TVA écologique et santé, accises (remplace TVA et accises actuelles) | -81,7 | -89,4 | -94,0 | -94,3 |
| Impôt unique sur les salaires du privé (remplace cotisations, CSG, IR des salariés) | -66,3 | -73,3 | -78,6 | -91,5 |
| Impôt unique sur les rémunérations publiques (remplace cotisations, CSG, IR des agents) | -68,0 | -73,2 | -78,5 | -84,8 |
| Remplacé par « Revenu universel et AAH » : chomage (statu quo) | +46,6 | +49,5 | +51,6 | +53,7 |
| Retraites : socle, transition et ancien système — Ancien système : âge de départ porté de 64 à 67 ans, quatre trimestres par génération à partir de 2029 (67 ans pour la génération née en 1967) | +8,6 | +38,2 | -6,3 | -0,6 |
| IS à 45 %, fin des impôts de production, accises carbone des entreprises | +33,7 | +35,9 | +38,3 | +35,8 |
| Impôt unique des retraités du nouveau système (remplace CSG, CASA, IR des pensions) | -32,5 | -35,0 | -35,7 | -43,2 |
| Fin des droits de mutation, des taxes locales et affectées (remplacés par l'impôt local) | -32,2 | -34,3 | -36,9 | -38,6 |
| Remplacé par « Revenu universel et AAH » : famille (statu quo) | +34,7 | +32,8 | +33,8 | +32,8 |
| Anciennes pensions : prélèvement net | +54,6 | +31,7 | -5,5 | +7,7 |
| Contribution d'épargne retraite et recettes non fiscales gardées au budget | +29,0 | +30,7 | +33,0 | +33,8 |
| Remplacé par « Revenu universel et AAH » : pauvrete (statu quo) | +24,0 | +25,5 | +27,0 | +28,1 |
| Remplacé par « Revenu universel et AAH » : aah_invalidite (statu quo) | +23,5 | +25,0 | +26,5 | +28,0 |
| Retraites : socle, transition et ancien système — Contribution de solidarité des retraités de l'ancien système (5 à 10 %) | +24,4 | +22,2 | +12,3 | +0,5 |
| Retraites : socle, transition et ancien système — Entre l'âge légal et 67 ans : RUI ou socle selon les annuités | -3,9 | -18,9 | -14,3 | -14,2 |
| Remplacé par « Revenu universel et AAH » : logement (statu quo) | +16,7 | +17,8 | +19,4 | +21,5 |
| Revenu universel et AAH — RUI étudiant sous condition de ressources | +21,2 | +15,5 | +15,5 | +15,5 |
| IS : déduction de l'investissement | -5,5 | -14,7 | -8,4 | -12,4 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Réformes de l'emploi : coût | -12,7 | -13,4 | -14,7 | -17,2 |
| Successions (transmissions d'entreprises exonérées) | -5,7 | -8,7 | -11,8 | -12,4 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Collectivités : besoin de financement divisé par deux d'ici 2032 (emprunt limité aux investissements rentables, le reste par le fonds ou l'impôt local) | +4,0 | +8,4 | +9,2 | +10,8 |
| Flat tax sur les dividendes, revenus du capital, bailleurs ; fin de l'IFI | -6,8 | -7,5 | -8,1 | -9,2 |
| Indépendants en société : impôt unique ou IS (remplace cotisations, CSG, IR) | -5,9 | -6,5 | -7,0 | -8,1 |
| Investissement : subventions restées à l'État, renouvelables — Soutien aux renouvelables (contrats en cours) | -10,7 | -6,2 | -0,0 | -0,0 |
| Investissement : subventions restées à l'État, renouvelables — Subventions d'investissement restées à l'État | -6,2 | -6,2 | -6,2 | -6,2 |
| Autres dépenses du programme (ministères, collectivités, mesures) — IA dans l'administration : économie | +0,9 | +4,8 | +7,0 | +8,2 |
| Ascenseur social : recettes | +2,4 | +4,6 | +6,0 | +7,2 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Armées : évolution (croissance, public servi, PIB ou prix) | -0,0 | -4,3 | -10,1 | -12,2 |
| Revenu universel et AAH — RUI : démographie (adultes, enfants) | -0,0 | +3,5 | +8,8 | +24,6 |
| Retraites : socle, transition et ancien système — Pensions sous le minimum vieillesse : revalorisation | -0,4 | -3,2 | -5,2 | -0,7 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Crèches : places créées (fonctionnement et construction) | -0,0 | -3,2 | -3,1 | -2,3 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Éducation : évolution (croissance, public servi, PIB ou prix) | -0,0 | -3,0 | -6,1 | -10,8 |
| Successions : supplément | +0,9 | +2,8 | +5,5 | +5,8 |
| Autres dépenses du programme (ministères, collectivités, mesures) — France 2030 : pas de nouveau plan après 2030 (subventions) | -0,0 | +2,3 | +2,5 | +2,9 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Contribution UE : évolution (croissance, public servi, PIB ou prix) | -0,0 | -1,8 | -4,2 | -5,0 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Gestion des caisses de sécurité sociale : −30 % au total avec l'IA (maladie, accidents du travail, retraite et famille) | +0,4 | +1,7 | +1,9 | +2,2 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Éducation : effectifs ajustés un pour un à la baisse du nombre d'élèves (au lieu d'un départ sur deux) | +0,2 | +1,6 | +1,8 | +2,1 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Autres : évolution (croissance, public servi, PIB ou prix) | -0,0 | -1,6 | -3,8 | -6,4 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Quotient familial et conjugal, RUI du conjoint : enfants et couples | -0,0 | +1,6 | +2,5 | +5,0 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Intérieur : évolution (croissance, public servi, PIB ou prix) | -0,0 | -1,6 | -3,8 | -6,7 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Achats et fonctionnement courant de l'État hors défense : −10 % | +0,5 | +1,6 | +1,7 | +2,0 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Quotient familial et conjugal : croissance tendancielle | -0,0 | -1,6 | -4,3 | -9,7 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Recherche : évolution (croissance, public servi, PIB ou prix) | -0,0 | -1,6 | -2,2 | -4,5 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Finances publiques : moins d'impôts à gérer (IR, CSG, cotisations, IFI, droits de mutation, TICPE fusionnés ou supprimés), −15 % sur la mission Gestion des finances publiques | +0,3 | +1,5 | +1,7 | +2,0 |
| Revenu universel et AAH — RUI et AAH : revalorisation (règle d'indexation) | -0,0 | +1,4 | +1,4 | +1,4 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Effectifs de l'État hors défense, sécurité, justice et enseignement : −10 % d'ici 2032 (sans baisse à l'hôpital) | +0,3 | +1,1 | +1,2 | +1,4 |
| Retraites : socle, transition et ancien système — Ancien système : barème des hautes pensions doublé (10 % au-delà de 3 000 €, 10 % de plus au-delà de 5 000 €) | +1,1 | +1,0 | +0,7 | +0,0 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Universités : droits d'inscription relevés pour les étudiants non boursiers (≈ 1 000 € en licence, 1 500 € en master) | +0,3 | +0,9 | +1,0 | +1,2 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Finances : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,8 | -1,9 | -3,2 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Administration territoriale : fin des départements en 2034, préfectures regroupées à l'échelon régional, −15 % | -0,0 | +0,7 | +0,8 | +0,9 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Aide médicale de l'État remplacée par une aide médicale d'urgence | +0,2 | +0,5 | +0,6 | +0,7 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Cabinets de conseil de l'État divisés par deux | +0,2 | +0,5 | +0,6 | +0,7 |
| Retraites : socle, transition et ancien système — Ancien système : pensions de réversion alignées sur les règles du régime général pour les nouvelles liquidations | +0,1 | +0,5 | +0,3 | +0,0 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Culture : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,5 | -1,2 | -2,1 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Écologie : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,4 | -1,0 | -1,2 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Temps de travail à 1 607 h dans la fonction publique d'État | +0,1 | +0,4 | +0,5 | +0,5 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Affaires étrangères : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,4 | -1,0 | -1,1 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Services de l'État qui doublonnent les compétences confiées aux régions (agriculture, forêts, biodiversité, formation) | -0,0 | +0,4 | +0,4 | +0,5 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ascenseur social : dépenses | -0,1 | -0,4 | -0,4 | -0,5 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Agriculture : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,2 | -0,6 | -0,7 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Administration : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,2 | -0,6 | -1,0 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Sports : évolution (croissance, public servi, PIB ou prix) | -0,0 | -0,1 | -0,2 | -0,3 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Ministères — Justice : évolution (croissance, public servi, PIB ou prix) | -0,0 | +0,1 | -1,0 | -1,8 |
| Autres dépenses du programme (ministères, collectivités, mesures) — Quotient familial et conjugal : démographie (population) | -0,0 | -0,0 | +0,4 | +2,9 |
| Retraites : socle, transition et ancien système — Socle : revalorisation (règle d'indexation) | -0,0 | -0,0 | +0,4 | +2,4 |
| **Périmètre** | | | | |
| Périmètre : ressources propres des collectivités (impôt local unique, IS local, autres) | +214,3 | +228,9 | +248,3 | +276,0 |
| Périmètre : dépenses des collectivités financées par ces ressources | -214,3 | -228,9 | -248,3 | -276,0 |
| Périmètre : ventes et tarifs de l'État, des opérateurs et des hôpitaux | +81,1 | +86,3 | +92,8 | +97,1 |
| Périmètre : dépenses financées par ces ventes et tarifs | -81,1 | -86,3 | -92,8 | -97,1 |
| **Effets macroéconomiques** | | | | |
| Effet macro : clause | +56,5 | +34,8 | +54,0 | +55,5 |
| Effet macro : erosion_is | -8,3 | -26,4 | -28,6 | -32,6 |
| Effet macro : reactions_impot | -7,8 | -24,8 | -27,2 | -31,9 |
| Effet macro : carbone | +7,9 | +18,9 | +27,1 | +19,1 |
| Effet macro : emploi | +0,3 | +7,4 | +7,1 | +7,5 |
| Effet macro : ajustement_budgetaire | -29,4 | +7,3 | -5,8 | -4,6 |
| Effet macro : productivite | +0,0 | +5,2 | +7,0 | +7,1 |
| Effet macro : épargne rendue et socle supplémentaire (règle) | +0,0 | -3,8 | -14,7 | -37,6 |
| Effet macro : logement | -0,5 | +2,7 | +3,9 | +5,2 |
| Effet macro : fraude_tva | +0,6 | +2,2 | +2,2 | +2,2 |
| Effet macro : ia | +0,2 | +2,1 | +2,5 | +2,6 |
| Effet macro : sante | -1,9 | -1,4 | -0,6 | -0,7 |
| Effet macro : salaires_dirigeants | -0,4 | -0,9 | -1,0 | -1,2 |
| Effet macro : capital_du_fonds | +0,0 | +0,8 | +5,0 | +13,3 |
| Effet macro : investissement_entreprises | -0,0 | -0,4 | -0,3 | +0,4 |
| Effet macro : emplois_fonds | +0,0 | +0,1 | +0,9 | +1,5 |
| Effet macro : permis_rapide | -0,1 | +0,1 | +0,1 | +0,1 |
| Effet macro : fin_aides_construction | -2,0 | +0,0 | +0,0 | +0,0 |
| **Flux de dette** | | | | |


Les lignes « Remplacé par … (statu quo) » sont les dépenses actuelles que le poste du programme remplace ; les lignes
« Poste — ligne » sont les dépenses du programme. Leur différence par poste :

| Écart de départ, hors effets macro (Md€) | 2029 | 2037 | 2050 |
|---|---|---|---|
| Recettes | −80 | −125 | −160 |
| Retraites (socle, transition, ancien système) | +31 | +93 | +100 |
| Santé | −12 | −8 | −9 |
| Revenu universel et AAH (contre chômage, famille, logement, RSA et prime d'activité, AAH) | +37 | +41 | +54 |
| Investissement et autres dépenses (ministères, collectivités, fonds) | +88 | +118 | +141 |
| **Total (points de PIB)** | **+2,1** | **+3,7** | **+3,6** |

## Constats

1. **TVA et accises : −82 Md€ en 2029** contre le statu quo (TVA écologique et santé, accises des ménages), et −55 Md€
   en ajoutant les accises carbone des entreprises (dans la ligne « IS à 45 % … »). C'est la baisse décidée le 18
   octobre 2026 (accises des entreprises, TVA non déductible ramenée au taux légal, baisse pour les ménages) ; la v235
   l'estimait à ≈ −64 Md€. À présenter comme une mesure, pas comme un calage « à recettes égales ».
2. **Impôt unique : −66 Md€ sur les salariés du privé, −68 Md€ sur les agents publics** en 2029 contre les cotisations,
   la CSG et l'impôt sur le revenu actuels (alignement du coût des agents compris).
3. **Recettes non fiscales : −191 Md€**, dont 81 de ventes et tarifs remis par le périmètre et la part locale remise
   par le périmètre des collectivités ; reste la part de l'État versée au fonds (revenus de la propriété et transferts).
4. **Santé : −12 Md€**, surtout une différence de classement (pensions d'invalidité et gestion de l'assurance maladie
   dans la santé du programme, ailleurs dans le statu quo), pas une mesure.
5. **Revenu universel** : 130 Md€ de RUI et AAH en 2029, contre 145 Md€ de prestations actuelles remplacées ; le RUI
   étudiant sous condition rapporte 21 Md€.

## Deuxième passe (4 novembre 2026) : impôt unique et TVA des salariés recalculés sur le noyau

- Recalcul sur les cellules du statu quo (`statu_quo.agreger_cellules` : même population, mêmes âges et salaires,
  barème du programme appliqué à chaque cellule), au niveau des distributions de 2026. **Pas d'erreur trouvée** : sans
  son effet sur les naissances, le moteur du programme est retrouvé à 0,3 Md€ près en 2073 ; le déficit change de
  moins de 0,1 point.
- **Effet du programme sur les naissances** isolé en mesure à part (il était dans chaque ligne) : sur l'impôt unique
  et la TVA des salariés, −0,4 Md€ en 2050, −4,9 en 2060, −16,2 en 2073 (moins d'enfants nés à partir de 2030, donc
  moins d'actifs ensuite).
- **Point de méthode trouvé : l'IA.** Mettre l'IA dans les salaires (comme le statu quo) ferait monter les recettes
  du programme sans faire monter ses dépenses, que son moteur fait suivre la tendance sans l'IA : un avantage d'un
  seul côté (jusqu'à −0,9 point de déficit en 2073). Le recalcul garde donc l'IA hors des salaires ; le moteur du
  programme la compte dans son canal macro (10 % du PIB en plus passe au solde). À unifier quand les dépenses du
  programme seront recalculées sur le noyau : l'IA dans les salaires des deux côtés.
- `programme(recalcul_noyau=False)` garde le pont exact (test de reproduction).

## Troisième passe (4 novembre 2026) : retraites et revenu universel

**Retraites** (prudent, Md€, − = économie par rapport au statu quo) :

| Mesure | 2029 | 2037 | 2050 | 2073 |
|---|---|---|---|---|
| Gel des pensions de l'ancien système (nés en 1979 ou avant) | 0 | −52 | −87 | −13 |
| Nés à partir de 1980 : socle à 67 ans et remboursement de 35 % au lieu des pensions actuelles | 0 | 0 | −24 | −307 |
| Âge de départ porté à 67 ans (ancien système) | −9 | −38 | +6 | +1 |
| Contribution de solidarité des retraités (5 à 10 %) | −24 | −22 | −12 | −1 |
| Entre l'âge légal et 67 ans : RUI ou socle | +4 | +19 | +14 | +14 |
| Pensions sous le minimum vieillesse revalorisées | 0 | +3 | +5 | +1 |
| Hautes pensions (baisse et doublement du barème), réversion | −2 | −2 | −2 | 0 |

Contrôle : l'ancien système du programme, sans le gel, retrouve les pensions du statu quo des mêmes générations (463
contre 465 Md€ en 2037, 28 contre 29 en 2073) : deux calculs indépendants qui concordent, pas d'erreur trouvée.

**Revenu universel** :

| Mesure | 2029 | 2037 | 2050 | 2073 |
|---|---|---|---|---|
| RUI et AAH (revalorisés sur les salaires) contre les prestations remplacées | −15 | −16 | −16 | −16 |
| RUI revalorisé sur les prix plutôt que sur les salaires (baisse relative assumée) | 0 | −9 | −22 | −41 |
| RUI étudiant sous condition de ressources | −21 | −16 | −16 | −16 |
| Effet du programme sur les naissances (compléments des enfants) | 0 | 0 | −1 | −3 |

Le RUI et l'AAH coûtent 130 Md€ en 2029, contre 146 Md€ de prestations remplacées (assurance chômage 47, famille 35,
RSA et prime d'activité 24, AAH et invalidité 24, logement 17).

## Reste à faire (passes suivantes)

- Recalculer chaque mesure sur le noyau au lieu de la lire dans le moteur du programme (recettes de chaque instrument à
  partir des cellules communes, dépenses à partir des blocs du statu quo), en commençant par les plus grosses : impôt
  unique, TVA, retraites, revenu universel.
- Isoler la mesure « revenu universel revalorisé sur les prix » (décision du 4/11/2026).
- Effets macroéconomiques par instrument (coût du travail, taux marginal, taux effectif de l'IS) au lieu des canaux
  propres au programme.
