# Évaluation indépendante du moteur simu2027 (branche `roadmap`, commit e796068, 27/11/2026)

Méthode : lecture du code (`moteur/`, `programmes/`, `outils/export_comparaison.py`) et contre-calculs avec `moteur.noyau.simuler` (scripts dans `/home/claude/audit/scripts/`, lancés avec `python3 -I`). Sauf mention contraire, les chiffres sont ceux du scénario **prudent en 2037**. Les valeurs recalculées sont identiques aux sorties publiées (Roussel : dette aux taux du statu quo 295,19 dans les deux cas). Suite rapide : 341 tests réussis en 90 s (hors OpenFisca, Monte Carlo et tests lents).
[V] = vérifié par un calcul ou dans le code ; [S] = supposition.

## Résumé : les 5 problèmes les plus importants

1. **Bug critique, Roussel** : les nationalisations (≈ 250 Md€, une seule fois selon `docs/roussel.md`) sont comptées **chaque année** (`moteur: fixe`, sans `fin`), soit 2 250 Md€ de dette en trop en 2037. Correction : écart de dette aux taux du statu quo +140,9 → +72,4 points, déficit 33,5 → 25,6 %. Roussel et Mélenchon échangent leur rang.
2. **La lecture principale n'est pas « sans pari sur les taux »** : la prime de dette et l'écart de taux propres au programme agissent sur le PIB par `bouclage_prime_demande`, donc sur le solde primaire. Cela pèse jusqu'à 0,93 point de PIB sur l'écart de solde primaire (Roussel) et jusqu'à 7,6 points sur la dette aux taux du statu quo.
3. **La « dette aux taux du statu quo » garde l'effacement de la dette par l'inflation propre au programme**, alors que le taux nominal ne suit que l'inflation de la zone euro. Cela retire de la dette 29 points (Mélenchon), 23 (Roussel), 10 (Arthaud), 8 (Tondelier) et 6 (Glucksmann). La dette indexée sur l'inflation (OATi) n'est pas modélisée.
4. **Les taux du statu quo contiennent eux-mêmes une prime de dette**, c'est-à-dire une réaction des marchés : +0,37 point en 2037 et +2,1 points en 2050. Ses effets sur les écarts de dette : 0,1 à 1,2 point en 2037, mais +28 points pour Mélenchon et +47 pour Roussel en 2050.
5. **Traçabilité et contrôles** : 61 mesures sans source pèsent 77 Md€ (Mélenchon 32 mesures pour 53 Md€ ; Tondelier 19 mesures pour 14 Md€ sans source ni note) ; « 42 annuités » de Le Pen non modélisé ; le contrôle micro/macro laisse de côté les plus grosses mesures ; aucun test n'aurait vu le bug n° 1.

---

## Critique

### C1. Roussel : nationalisations comptées chaque année au lieu d'une fois [V]

- **Problème.** `programmes/roussel/parametres.yaml:165` code `nationalisations` avec `poste: participations, moteur: "fixe", debut: 2028, plein: 2029` et **sans `fin`**. `ProgrammeSimple.profil` (`moteur/programme_simple.py:217`) donne donc −250 Md€ chaque année de 2029 à 2073. La note (valeurs de marché : BNP 85 + AXA 80 + SG 30 + Engie 35 + autoroutes 40-50 ≈ 275 Md€) et `docs/roussel.md:45` (« ≈ 250 Md€ en prudent ») décrivent pourtant une opération faite **une fois**. Mélenchon, codé dans le même format, a bien `fin: 2031` (`programmes/melenchon/parametres.yaml:957`), soit 90 Md€ au total.
- **Preuve.** `scripts/decomp_dette.py` donne pour Roussel des participations cumulées de −2 250 Md€ en 2037, plus que le déficit primaire cumulé (−2 105 Md€). `scripts/roussel_fix.py` refait le calcul avec un achat unique en 2029 (`debut = fin = 2029`) :

| Roussel | publié | achat unique |
|---|---|---|
| Écart de solde primaire 2037, prudent | −9,82 | −9,52 |
| Dette aux taux du statu quo 2037, prudent | 295,2 % | 226,7 % |
| Dette au sens de Maastricht 2037, prudent | 332,6 % | 247,4 % |
| Déficit 2037, prudent | 33,49 % | 25,58 % |
| Dette aux taux du statu quo 2037, médian | 239,5 % | 189,5 % |

- **Effet sur le classement.** La dette de Roussel passe sous celle de Mélenchon (232,7) : Roussel n'est plus dernier. L'écart de solde primaire bouge aussi de 0,3 point, par la prime de dette (voir C2). Le Monte Carlo publié contient le même défaut.
- **Correction.** `debut: 2029, plein: 2029, fin: 2029` : la dette de départ ne compte pas les participations de 2027-2028 (`programme_simple.py:752`), donc l'achat doit tomber en 2029. Ajouter un test qui refuse une mesure `participations` sans `fin` et qui plafonne le cumul des participations (par exemple à 15 % du PIB). Effort : 15 min, plus une régénération.

### C2. L'écart de solde primaire et la dette aux taux du statu quo contiennent la réaction des marchés [V]

- **Problème.** `noyau.trajectoire` (`moteur/noyau.py:288-315`) fait passer l'écart de taux de marché au statu quo (prime de dette, `taux_supplementaire`, baisse de l'écart de taux en médian et optimiste) par le PIB (`dy_r`). Ce PIB change les recettes (`dy_r × rec_sq / y_sq`), le chômage, les dépenses de chômage et l'emploi publié. L'écart de solde primaire (`export_comparaison.py`, commenté « la mesure robuste ») et `decomposition.aux_taux_statu_quo` reprennent ce solde primaire et ce PIB. Ils contiennent donc l'effet des taux du programme, ce que la règle de l'auteur exclut.
- **Preuve.** `scripts/tous.py` avec `{"macro.bouclage_prime_demande": false}`, prudent 2037 :

| Programme | Écart de solde primaire, publié | sans réaction des taux | Dette aux taux du statu quo, publié | sans réaction des taux |
|---|---|---|---|---|
| Roussel | −9,82 | −8,89 | 295,2 | 287,6 |
| Mélenchon | −12,31 | −11,61 | 232,7 | 227,6 |
| Arthaud | −4,71 | −4,42 | 190,4 | 188,2 |
| Le Pen | −2,61 | −2,46 | 177,0 | 176,0 |
| Glucksmann | −2,98 | −2,85 | 172,5 | 171,5 |
| Tondelier | −3,25 | −3,12 | 170,5 | 169,6 |
| Lisnard | −2,68 | −2,56 | 176,8 | 176,0 |
| Zemmour | −2,36 | −2,23 | 179,2 | 178,2 |

  La pénalité croît avec le déficit. La lecture principale amplifie donc les écarts : le programme le plus déficitaire paie deux fois, par sa prime en intérêts et par sa prime en PIB. Dans la variante, l'ordre ne change pas en 2037, mais l'écart Le Pen – Lisnard passe de 0,07 à 0,10 point.
- **Correction.** Calculer la lecture principale (écart de solde primaire, dette et déficit aux taux du statu quo, emploi, chômage) sur une trajectoire où l'écart de marché du programme est forcé à celui du statu quo : `dm = 0` dans la rétroaction, et pas de `taux_supplementaire` ni de baisse de l'écart de taux. La trajectoire complète reste la variante « avec la réaction des marchés ». Cela demande un second appel à `trajectoire` par scénario, avec une option du noyau. Effort : ½ journée, plus une régénération.

## Important

### I1. La dette aux taux du statu quo garde l'effacement par l'inflation du programme [V]

- **Problème.** `aux_taux_statu_quo` (`moteur/decomposition.py:65`) applique le taux nominal du statu quo mais l'**inflation du programme** : `dette × (1 + i_sq − π_prog)`. Dans le noyau, le taux de marché ne suit que la part de la France dans l'inflation de la zone (`bouclage.py:24-29`, poids `w`). L'auteur l'assume : « une inflation française plus haute allège la dette réelle ». Mais garder ce canal tout en supprimant la réaction des taux revient à supposer que les marchés ne réagissent pas à une inflation propre à la France, ce qui est aussi un pari sur les taux. Par ailleurs, la part de dette indexée sur l'inflation (OAT€i, ≈ 10 à 12 % de la dette négociable [S]) n'est pas modélisée : aucune occurrence dans `moteur/` ni dans les paramètres.
- **Preuve.** `scripts/infl_tax2.py` recalcule la dette aux taux du statu quo avec l'inflation du statu quo. Écart de dette 2037 au statu quo :

| Programme | avec l'inflation du programme (publié) | avec l'inflation du statu quo |
|---|---|---|
| Mélenchon | 78,4 | 107,5 |
| Roussel | 140,9 | 163,7 |
| Arthaud | 36,1 | 46,1 |
| Tondelier | 16,2 | 24,2 |
| Glucksmann | 18,2 | 23,9 |
| Le Pen | 22,6 | 25,0 |

  Mélenchon a 3,6 % d'inflation en 2029 et 4,2 % en 2032, contre 1,65 et 1,8 % au statu quo. L'effacement cumulé atteint 887 Md€ de 2029 à 2037.
- **Effet.** La dette des programmes inflationnistes est sous-estimée de 6 à 29 points dans la lecture n° 2. Le classement ne change pas en 2037, mais les écarts entre la gauche et la droite sont réduits d'autant.
- **Correction.** Pour la lecture aux taux du statu quo, retenir le **taux réel** du statu quo (`i_sq − π_sq`). Publier l'effacement par l'inflation comme une composante de `decomposition.ecart`. Ajouter un paramètre sourcé (AFT) pour la part de dette indexée. Effort : 2 h, plus l'indexation (½ journée).

### I2. Les taux du statu quo contiennent une prime de dette [V]

- **Problème.** `prime_marche` s'applique aussi au statu quo (`noyau.py:358`) : 3 pb par point de dette au-dessus de 2029 en prudent (`macro.prime_dette`), avec un plafond de +4 points. Le taux du statu quo (`scripts/taux_sq.py`) se compose ainsi : base 3,64 + prime 0,37 = 4,00 % en 2037 ; base 3,96 + prime 2,10 = 6,06 % en 2050. La lecture « aux taux du statu quo » applique donc à la dette en plus des programmes une réaction des marchés **à la dette du statu quo**.
- **Preuve.** Sans la prime du statu quo, sa dette 2050 passe de 242,0 à 208,5 %. Écart de dette 2050 aux taux du statu quo : Mélenchon 278,5 → 250,2 ; Roussel 439,3 → 392,1 ; Lisnard 98,9 → 88,1 ; Attal 37,4 → 33,4. En 2037, l'effet reste de 0,1 à 1,2 point.
- **Correction.** Lecture n° 2 aux taux hors prime (`taux_base + taux_fisher + taux_bce`, composantes déjà publiées). Garder la prime dans la variante de Maastricht. Effort : 1 h.

### I3. Le Pen : « 42 annuités » non modélisées, même coût que les programmes à 43 ans [V pour le code, S pour l'ampleur]

- **Problème.** `programmes/le_pen/programme.py:31` appelle `baisse_age_legal_detail` avec le seul profil « 62 ans ». Le coût est **identique** à celui de Tondelier (« durée Touraine de 43 ans gardée ») et de Glucksmann : −15,6 / −23,5 / −25,5 Md€ en 2029, 2032 et 2037, et −22,8 Md€ identiques dans `sorties/micro_mesures.csv`. La note de `le_pen/parametres.yaml:20` se contredit : « 42 annuités […] réforme Touraine gardée ». Or Touraine porte la durée à 43 ans pour les générations de 1973 et après.
- **Effet [S].** Un an de durée de moins pour les générations nées après 1965 représente de l'ordre de 0,1 à 0,2 point de PIB à terme (ordre de grandeur des chiffrages de la réforme Touraine). Le Pen (−2,61) et Lisnard (−2,68) ne sont séparés que de 0,07 point en 2037 : leur ordre peut s'inverser.
- **Correction.** Un paramètre commun « durée d'assurance » dans `baisse_age_legal_detail` (décalage du profil de départ par génération), appliqué à Le Pen et à tout programme qui touche la durée. Effort : 1 journée.

### I4. Mesures sans source, au mépris de la règle « une source ou une décision écrite » [V]

- **Problème.** `Parametres._valider` (`moteur/parametres.py:137`) n'exige une source qu'au statut SOURCE. Une HYPOTHÈSE de plusieurs milliards peut donc n'avoir ni source ni note.
- **Preuve.** Mesures chiffrées sans `source` :

| Programme | Mesures sans source | Montant (prudent) | dont ni source ni note | Montant |
|---|---|---|---|---|
| Mélenchon | 32 | 53,2 Md€ | 5 | 5,9 Md€ |
| Tondelier | 27 | 21,9 Md€ | 19 | 14,3 Md€ |
| Zemmour | 2 | 1,6 Md€ | – | – |
| Bertrand | 2 | 0,7 Md€ | – | – |

  Exemples : `tondelier_mesures.services_publics_divers` 2,1 Md€, `melenchon_mesures.services_publics` 2,5 Md€ sans note. Par ailleurs, 10 paramètres communs au statut SOURCE ne renvoient qu'à une cellule de classeur ou à la v235 : `macro.taux_apparent_2029` (« Effets macro!B211 », alors que c'est la valeur de départ de tout le calcul des intérêts), `statu_quo.apul_depenses_2026`, `sante.ondam_2026`, `budget_etat.lpm_2030_courants`… Enfin, 121 paramètres SOURCE sur 154 n'ont pas d'URL.
- **Effet.** Ces montants pèsent 1,7 point de PIB pour Mélenchon et 0,7 point pour Tondelier, sans trace vérifiable.
- **Correction.** Rendre obligatoires, dans le validateur, `source` ou `note` pour toute HYPOTHÈSE qui a un `montant` au-dessus de 0,5 Md€. Ajouter un test. Effort : 2 h, plus la rédaction des sources (1 journée).

### I5. Le contrôle micro/macro laisse de côté les plus grosses mesures [V]

- **Problème.** Dans `sorties/micro_mesures.csv`, les mesures calculées ont `moteur_md = 0` et un écart vide : rien n'est comparé. Les plus grosses mesures ne sont donc pas contrôlées : SMIC d'Arthaud (OpenFisca 95,7 Md€), LIS-ECO-02 (−71,4), ZEM-FIS-01 (−51,5), âge de 60 ans de Mélenchon et Roussel (−49,7), droit au brut d'Attal (−36,0). Là où la comparaison existe, les écarts dépassent 25 % sur plusieurs mesures : REC-37 −50 %, COT-04 −44 %, LFI-RET-03 −25 %, LFI-PRE-02 +37 %, LIS-SOC-01 +47 %. Certains écarts sont expliqués (incidence, assiette partielle), mais aucun seuil n'est testé.
- **Correction.** Écrire le montant du moteur des mesures calculées dans `micro_mesures.csv` (il est disponible dans `bilan_mesures`). Ajouter un test qui borne l'écart (par exemple 30 %), sauf exception documentée. Effort : ½ journée.

### I6. Aucun test de propriété sur les flux de dette hors solde ni sur les fins de mesures ponctuelles [V]

- **Constat.** C1 passe la suite verte : 341 tests, dont `test_roussel.py:44`, qui ne vérifie que l'ordre des scénarios. Un balayage des mesures « fixes » ou « pib » sans `fin` dont le libellé désigne un montant ponctuel ou sur une durée (`scripts/scan.py`) trouve aussi le plan **France 2040 d'Attal** : « 200 Md€ […] en dix ans », codé 7 Md€ par an indexés sur le PIB, sans `fin`. Cela fait ≈ 7 à 8 Md€ par an en trop après 2037, soit 0,2 point de PIB en 2050.
- **Correction.** Ajouter des tests : `participations` sans `fin` refusées ; cumul des participations plafonné ; chiffre de la note (« ≈ X Md€ en tout ») comparé à la somme de la série, avec un champ `total` facultatif contrôlé. Corriger Attal (`fin: 2037`). Effort : ½ journée.

## Mineur

- **M1. Point de départ (décision D3 en attente) [V].** La dette de fin 2028 vaut 125,1 % du PIB de 2026 (`statu_quo.dette_fin_2028`), contre ≈ 122,5 % avec la croissance de la Banque de France (0,9 % puis 1,2 %). Les intérêts de 2029 font 3,35 % du PIB (contre 2,9 % au PLF 2027 pour 2027) et le déficit de 2029 atteint 5,9 %, alors que le point de départ est de 5,0 %. L'effet sur les écarts est faible, mais les niveaux publiés sont plus pessimistes (statu quo : 154 % de dette en 2037). À trancher avant publication.
- **M2. Garantie d'autonomie de Mélenchon (LFI-PRE-01, 28 Md€) [V].** La note dit « suit les salaires (seuil de pauvreté) », mais le code utilise `moteur: bloc:pauvrete`, qui reste à plat (indice 0,999 en 2037, 0,942 en 2050, contre 1,063 et 1,165 pour les salaires). La mesure est sous-estimée de 1,8 Md€ en 2037 et de 6,2 Md€ en 2050, plus LFI-PRE-02. Correction : `moteur: salaire` ou un indice du seuil de pauvreté.
- **M3. Année blanche d'Attal [V].** Les économies sur les pensions et les prestations sont multipliées par `idx["pib"]` (`programmes/attal/programme.py`), alors que ces montants sont revalorisés sur les prix en euros constants. Elles sont surestimées d'environ 8 % en 2037, soit moins de 0,5 Md€.
- **M4. Enveloppe d'économies non détaillées [V].** Les économies nommées ne sont jamais confrontées à la capacité historique, alors que les économies non détaillées y sont plafonnées. Lisnard nomme 47,9 Md€ pour une capacité de 12 (prestations : 13,9 contre 3) ; Retailleau 34,3 contre 12 ; Le Pen 15,7 contre 10,5. Leur enveloppe vaut donc 0 (`scripts/env.py`). C'est conforme à la règle, mais un programme qui détaille ses économies obtient plus de crédit que les précédents historiques ne le justifient. Proposition : publier un indicateur « économies nommées / capacité » par domaine.
- **M5. `_autres()` calculé comme un résidu [V].** Dans `decomposition.py:31`, `_autres` vaut `interets_reels − (i − π) × dette`. Si l'on modifie l'inflation d'un compte, l'écart passe en silence dans « autres intérêts » : mon premier test de sensibilité donnait un faux résultat (78,4 → 77,6 au lieu de 107,5). Correction : publier `interets_menages` comme un champ à part et ne plus le déduire par résidu.
- **M6. Deux codes pour le SMIC [V].** Tondelier a sa propre fonction `smic` (`programmes/tondelier/programme.py:123`, justifiée par ses allègements « nominalisés »), alors que les quatre autres programmes passent par `bib.smic`. Les deux codes risquent de diverger. Correction : `bib.smic(..., allegements_suivent_smic=False)` couvre déjà ce cas.
- **M7. Paramètres de comportement propres à chaque programme [V].** La baisse du chômage d'une réforme de l'assurance chômage (`*_chomage.baisse_taux`) vaut 0,1 à 0,3 point en prudent, fixée programme par programme (Lisnard 0,1 ; Attal et Philippe 0,2 ; Retailleau 0,3). Le sens inverse a une valeur commune (`programme_commun.chomage_hausse_taux`, 0,6). Un barème commun (point par mois de durée ou par point de taux de remplacement) rendrait le traitement symétrique.

## Ce qui pèse le plus sur le classement

- **Bas du classement.** C1 inverse Roussel et Mélenchon sur la dette ; I1 rapproche Mélenchon de Roussel (107,5 contre 163,7 avec l'inflation du statu quo).
- **Groupe Zemmour / Le Pen / Lisnard** (−2,36 / −2,61 / −2,68). L'ordre se joue à moins de 0,3 point et dépend de trois choses :
  - la démographie, qui coûte net 0,39 point à Lisnard, 0,24 à Zemmour et 0,17 à Le Pen en 2037 (1,2 point de recettes en moins pour Lisnard, compensé en partie) : `demographie.titres_vers_solde.realisation` et `emploi_relatif` décident de l'ordre ;
  - les 42 annuités de Le Pen (I3) ;
  - la réaction des taux (C2).
- **Glucksmann / Tondelier** (−2,98 / −3,25). Le canal des réformes de structure (`reformes_structurelles.pmr`, notes de −0,5 et −1, jugées programme par programme : 0,21 et 0,42 point de PIB) pèse autant que leur écart.
- **Haut du classement.** Bertrand, Retailleau et Philippe sont robustes à tout ce qui précède : moins de 0,05 point.

## Ce qui est solide

- L'architecture est appliquée par le code : un programme vide redonne le statu quo, les clés en double sont refusées, la bibliothèque est commune (Mélenchon et Roussel ont des lignes de retraite, de santé et de SMIC identiques au centime). Les sorties publiées se recalculent à l'identique.
- La logique du miroir est appliquée partout : éviction (1,0 contre 0,5), seniors, migrations, réformes de structure.
- Les ordres de grandeur du statu quo sont bons en 2029 : recettes 51,8 % du PIB, dépenses primaires 54,4 %, retraites 14,1 % (COR 14,1 %), chômage 8,3 % (Insee : 8,1 % au premier trimestre 2026).
- Le contre-calcul OpenFisca de REC-37 (suppression des allègements au-delà de 1,6 SMIC) donne 17,5 Md€ en statique, contre 16,5 Md€ dans le moteur.
- Les migrations sont traitées complètement (recettes, dépenses par bloc, naissances) et symétriquement. Le noyau est rapide (≈ 0,5 s par programme et par scénario).
