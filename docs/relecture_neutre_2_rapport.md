# Seconde relecture neutre du chiffrage (12 novembre 2026)

Relecteur indépendant, dépôt en lecture seule : branche `arbitrages-equite`, commit 312d919. Aucun fichier du dépôt
n'est modifié, hors ce rapport. Périmètre : tout le projet (noyau, statu quo, canaux communs, treize programmes,
comparateur), et pas seulement les changements de la branche. Les règles d'Adrien sont prises comme données ; je
vérifie leur application.

Méthode : lecture du code commun et des paramètres, recalcul de tous les programmes (`noyau.simuler`), audit
automatique des 1 343 paramètres, expériences en mémoire (fonctions remplacées sans toucher au dépôt),
lecture du texte du comparateur. Convention : un montant positif améliore le solde (Md€ de 2026). Sauf mention, les
chiffres sont ceux de 2037 au scénario prudent.

## Vue d'ensemble

| N° | Constat | Gravité | Qui est touché |
|---|---|---|---|
| 1 | Un gain de PIB venu de la productivité rapporte 52 % au solde, alors que le statu quo lui-même n'en garde que 12 % | Haute | Tous, dans les deux sens |
| 2 | Barème de productivité : grille appliquée de façon inégale, hors du champ de l'indicateur de l'OCDE | Haute | Tous |
| 3 | Écologie de droite : le déficit de 3 % repose sur un emprunt aux ménages compté en recette | Haute | Écologie de droite |
| 4 | 32 heures : une embauche rapporte 83 000 € au solde, un emploi perdu en coûte 21 000 | Haute | Roussel, Arthaud, Mélenchon |
| 5 | Écologie de droite : hypothèses sans source, fraude à la TVA, logement, mesures « méthode » | Moyenne | Écologie de droite |
| 6 | Baisse de l'écart de taux : gagnée par des trajectoires qui divergent | Moyenne | Attal, Bertrand, Lisnard, Philippe, Retailleau, Tondelier, Zemmour |
| 7 | PIB publié : un poste public ne produit rien après cinq ans | Moyenne | Gauche (PIB trop bas), droite (trop haut) |
| 8 | Zemmour sans émissions ; baisse de l'immigration sans effet sur l'emploi | Moyenne | Zemmour, Le Pen, Philippe, Retailleau |
| 9 | Fiscalité des entreprises : ordre des scénarios rompu | Moyenne | Tous ceux qui touchent à l'IS et aux impôts de production |
| 10 | Comparateur : sept chiffres ou formulations à corriger | Moyenne | Écologie de droite, Philippe, Zemmour, Tondelier, Arthaud |
| 11 à 16 | Enveloppe d'économies, canaux IA et école, licenciements, sources manquantes, documentation, statu quo | Faible | — |

Les quatre premiers points déplacent le déficit de 2037 de 0,2 à 1,7 point de PIB selon le programme. Aucun ne
change le sens du classement d'ensemble ; le point 1 fait passer Philippe au-dessus du statu quo.

---

## 1. Un gain de productivité rapporte 52 % au solde ; le statu quo du modèle n'en garde que 12 %

Réponse à la question du brief : des deux conventions, c'est celle d'Écologie de droite (dividende de croissance)
qui est cohérente avec le modèle, pour les gains de productivité. Celle des programmes simples les surestime
d'un facteur quatre, dans les deux sens.

**Ce que fait le modèle.** Un PIB en plus dû à un canal déclaré ou au canal d'offre rapporte « la part des recettes
dans le PIB du statu quo », soit 52 % (`moteur/canaux_declares.py:65-72`, `moteur/offre.py:375-377`). Les dépenses
restent celles du statu quo : `noyau.trajectoire` lit `sq.blocs(p, s)` sans tenir compte du PIB du programme
(`moteur/noyau.py:185`).

**Pourquoi c'est incohérent.** Dans le statu quo, presque toute la dépense suit les salaires ou le PIB
(`moteur/statu_quo.py:399-416`) : santé, prestations (décision du 4/11), collectivités, missions de l'État, « autres »,
investissement, défense. Seules les pensions suivent les prix, avec quinze ans de retard sur les salaires. Un
programme qui relève la productivité relève donc aussi, selon les règles mêmes du modèle, les dépenses indexées.
Le calcul ne le fait pas : il garde 52 % du gain.

**Preuve** (expérience 4, `exp4.py`). J'ai relevé de 1 % en dix ans la productivité du statu quo et mesuré ce qui
reste au solde primaire, en part du PIB gagné :

| | 2030 | 2037 | 2050 | 2073 |
|---|---|---|---|---|
| Recettes en plus | 49 % | 49 % | 50 % | 54 % |
| Dépenses en plus | 24 % | 37 % | 39 % | 54 % |
| **Reste au solde** | **25 %** | **12,5 %** | **10 %** | **≈ 0 %** |

Le résultat est le même dans les quatre scénarios. Écologie de droite applique son propre dividende (≈ 8 %,
`programmes/ecologie_de_droite/effets.py:44-69`, lignes 266, 276 et 280) : il est proche du bon ordre de grandeur.

**Ce qui est concerné.** Les gains de type productivité : réformes de structure, IA, école, et dans le canal
d'offre la fiscalité des entreprises, l'éducation, la recherche et l'investissement public (le salaire monte avec
la productivité). Ne sont pas concernés : les gains d'emploi et d'heures (travail, coût du travail, seniors), où le
salaire par tête ne bouge pas, et le multiplicateur, où la dépense est fixe à court terme.

**Effet de la correction** (déficit, % du PIB ; A : canaux déclarés seuls ; B : A plus les instruments d'offre de
type productivité) :

| Programme | 2037 prudent | A | B | 2037 médian | B |
|---|---|---|---|---|---|
| Arthaud | 19,92 | 18,26 | 18,25 | 14,05 | 13,29 |
| Mélenchon | 31,52 | 30,24 | 30,26 | 23,05 | 22,57 |
| Roussel | 31,99 | 30,84 | 30,85 | 23,40 | 22,87 |
| Tondelier | 14,51 | 13,97 | 13,92 | 10,60 | 10,27 |
| Glucksmann | 14,62 | 14,37 | 14,36 | 11,85 | 11,83 |
| Le Pen | 13,23 | 13,10 | 13,20 | 10,73 | 10,80 |
| Bertrand | 9,20 | 9,20 | 9,20 | 7,33 | 7,32 |
| Zemmour | 12,96 | 13,17 | 13,17 | 9,63 | 10,14 |
| Retailleau | 9,94 | 10,16 | 10,20 | 7,14 | 7,72 |
| Attal | 10,76 | 11,08 | 11,11 | 7,81 | 8,65 |
| Philippe | 9,34 | 9,67 | **9,75** | 6,26 | 7,03 |
| Lisnard | 12,95 | 13,51 | 13,64 | 9,16 | 10,39 |

Statu quo : 9,50 (prudent) et 8,37 (médian). Philippe passe au-dessus du statu quo au prudent. En solde primaire :
Arthaud +37 Md€, Mélenchon +28, Roussel +26, Tondelier +14 ; Lisnard −18, Philippe −11, Attal −9, Retailleau −7.

**Correction proposée.** Calculer une fois, dans le noyau, le dividende de productivité du statu quo (année par année,
comme dans l'expérience) et l'appliquer à tout PIB en plus de type productivité, pour tous les programmes, Écologie de
droite comprise. Garder la part des recettes pour les gains d'emploi et le multiplicateur. Une variante plus propre :
passer la productivité du programme au noyau, qui recalcule les blocs indexés.

## 2. Barème de productivité : une grille appliquée de façon inégale, au-delà de ce que mesure l'OCDE

**Enjeu.** Un cran de 0,5 vaut 4,3 Md€ pour qui libéralise et 8,6 Md€ pour qui réglemente (scénario miroir), avec la
convention actuelle. Le classement d'une seule mesure pèse donc plus que la plupart des mesures chiffrées.

**a. La grille n'est pas appliquée de la même façon à tous.** Relevé dans les fiches `mesures.yaml` et les notes des
paramètres `<nom>_canaux.reformes_structurelles` :

| Mesure | Comptée chez | Non comptée chez | Écart si même règle |
|---|---|---|---|
| Préférence dans la commande publique (−0,5) | Glucksmann, Tondelier | Le Pen (« priorité nationale dans les marchés publics », `le_pen/mesures.yaml:136`) | Le Pen −8,6 Md€ |
| Prix réglementés ou bloqués (−0,5) | Mélenchon (énergie), Roussel (carburant) | Tondelier (« prix encadrés », ligne 1134), Glucksmann (prix planchers, ligne 162), Attal (prix planchers, interdiction de vendre à perte, lignes 139 et 147) | −8,6 Md€ chacun |
| Fin des surtranspositions (+0,5) | Zemmour, Lisnard | Bertrand (`bertrand/mesures.yaml:38`), Philippe et Retailleau (non comptée à part) | Bertrand +4,3 Md€ |
| Logement | Attal (+0,5 : « construction simplifiée et statut du bailleur privé ») | Écologie de droite, Retailleau, Mélenchon (exclu : « absent du cadre de l'OCDE ») | Attal −4,3 Md€ |
| Contrats de travail | Mélenchon (licenciements boursiers, −0,5) | Mélenchon (quota de contrats précaires, LFI-EMP-08) | — |
| Normes nouvelles | — (aucune) | Tondelier, Glucksmann (interdictions de produits, de vols courts) alors que les moratoires de la droite valent +0,5 | à trancher |

Avec la même règle pour tous, Attal passerait de +10,4 à environ +1,8 Md€, Le Pen de −4,3 à −12,8, Tondelier de
−17,1 à −25,7, Glucksmann de −8,6 à −17,1, Bertrand de 0 à +4,3. La grille est donc sensible au relevé des mesures
plus qu'aux programmes.

**b. L'indicateur de l'OCDE ne couvre pas la plupart des mesures notées.** L'effet retenu est celui de l'indicateur
ETCR : la réglementation de l'électricité, du gaz, des transports et des communications. Une « réforme typique » est
la moyenne des variations sur deux ans observées dans l'OCDE (−0,31 point). Entrent dans ce champ : Engie, les tarifs
de l'énergie, la sortie du marché de l'électricité, le rail. N'y entrent pas : les banques et AXA (comptées 1 chez
Roussel), les moratoires sur les normes, le « silence vaut accord », la commande publique, l'audiovisuel, la
pharmacie. Pour ces mesures, le barème n'a pas de source : c'est une analogie. La réforme typique est mesurée sur
des libéralisations ; l'effet d'une hausse de la réglementation est supposé symétrique.

**c. Protection de l'emploi : les trois quarts n'ont pas de source.** Dans les présentations de l'auteur, la
protection de l'emploi agit par l'intensité en capital, et non par le taux d'emploi (je n'ai pas pu relire le tableau
de l'article). La décote d'un quart « pour la part d'emploi » (`part_hors_emploi_epl`) ne viendrait donc pas de
l'article. Il n'y a pas de double compte avec les canaux d'emploi d'Arthaud (embauches en moins, réquisitions) ; à
l'inverse, rien ne justifie la décote. Effet : faible (Arthaud −4,8 Md€, Lisnard +1,2).

**d. Deux peines pour une mesure.** Le carburant bloqué de Roussel coûte 12,8 Md€ au budget, puis 8,6 Md€ par le
barème. Les nationalisations coûtent leur prix (dette), des dividendes réduits de moitié au prudent, puis le barème.
Une subvention de prix n'est pas une barrière à l'entrée : son coût économique est déjà dans le canal « TVA et
accises ».

**e. Plafond.** Mélenchon et Roussel additionnent 3 crans, Arthaud davantage ; le plafond de 2 leur épargne au moins
17 Md€ chacun. Il n'a pas d'autre justification que le domaine d'estimation de l'article.

**Correction proposée**, par ordre de préférence :
1. Restreindre le barème à ce que mesurent les deux indicateurs (réseaux d'énergie, de transport et de
   communication ; règles du licenciement), avec un tableau unique, mesure par mesure et candidat par candidat,
   validé par Adrien. Sortir le reste.
2. À défaut, garder le barème en variante publiée à part, hors du déficit affiché.
3. Dans tous les cas : corriger les six incohérences du tableau, retirer la décote d'un quart ou la sourcer, appliquer
   le point 1 (dividende de productivité), et écrire dans le comparateur « barème du modèle, d'après une étude de
   l'OCDE » : l'OCDE n'a noté aucun programme.

## 3. Écologie de droite : le déficit de 3 % repose sur un emprunt aux ménages compté en recette

Le brief demande la même sévérité pour ce programme. Trois constats.

**a. La contribution prise par la règle est un emprunt.** Elle est rendue à 67 ans avec le rendement du fonds
(`clause.restitution`). Le noyau la compte en recette et publie les créances à part (expérience 6, prudent) :

| | 2029 | 2032 | 2037 | 2050 | 2073 |
|---|---|---|---|---|---|
| Déficit publié | 3,00 | 3,38 | 3,00 | 3,17 | 3,00 |
| Contribution d'épargne prise (Md€) | 35,0 | 35,7 | 37,0 | 39,9 | 27,6 |
| En points de PIB | 1,17 | 1,15 | 1,12 | 1,14 | 0,74 |
| Baisse du revenu universel (Md€) | 19,0 | 20,1 | 3,2 | 19,3 | 0 |
| Déficit sans la règle | 4,83 | 5,32 | 5,23 | 6,08 | 10,64 |
| Dette publiée (% du PIB) | 129 | 128 | 124 | 124 | 132 |
| Dette et créances des ménages | 130 | 133 | 134 | 142 | 149 |

La contribution est à son plafond (5 points d'épargne sur 10) chaque année de 2029 à 2037 au moins. En 2029, le
revenu universel baisse de 132 € par mois. Si la contribution est classée en emprunt, ce que ferait sans doute un
comptable national pour un prélèvement remboursable, le déficit de 2037 est de 4,1 % et non de 3,0 %.

**b. Le classement du fonds.** Avec les investissements du fonds comptés en dépense publique
(`sorties/variante_fonds_apu.json`), le déficit prudent est de 5,4 % en 2029, 6,1 % en 2037 et 10,1 % en 2050. Le
comparateur le dit sans chiffre (« sensiblement plus élevé »), alors que les faiblesses des autres sont chiffrées.

**c. Le comparateur classe ce programme après règle, les autres sans.** Le tableau de synthèse trie sur le déficit
publié : 3,0 %. La fourchette honnête pour 2037 va de 3,0 % (publié) à 4,1 % (contribution en emprunt), 5,2 % (sans
règle) et 6,1 % (fonds dans les administrations).

**Correction proposée.** Afficher pour ce programme le déficit sans règle en premier, ou compter la contribution
remboursable comme un financement ; afficher « dette et créances » à côté de la dette ; chiffrer la variante du
fonds dans le résumé. Régénérer `variante_fonds_apu.json`, qui date d'avant les dernières corrections (dette de 2037 :
122,6 % contre 123,9 % publié).

## 4. 32 heures : une embauche rapporte 83 000 € au solde, un emploi perdu en coûte 21 000

**Fichier** : `moteur/programme_simple.py:196-232` (`trente_deux_heures`) et lignes 385-396.

**Constat.** Les embauches de partage du travail sont comptées deux fois en recettes :
- la production qu'elles préservent n'est pas retirée du PIB (`1 − gp − ge`, ligne 220), donc pas taxée en moins, à
  52 % ;
- la ligne « prélèvements des embauches » leur ajoute `valeur_emploi` (20 000 €, lignes 229-231), qui contient déjà
  prélèvements et TVA.

Les emplois perdus par le coût horaire, eux, ne coûtent que `valeur_emploi`. Recalcul sur les sorties :

| 2037, prudent | Embauches | Recette par embauche | Emplois perdus | Perte par emploi |
|---|---|---|---|---|
| Roussel | 523 000 | 11,1 + 32,4 Md€ = 83 000 € | 384 000 | 8,2 Md€ = 21 000 € |
| Arthaud | 555 000 | 11,8 + 34,4 Md€ = 83 000 € | 409 000 | 8,7 Md€ = 21 000 € |
| Mélenchon | 64 000 | 1,4 + 4,0 Md€ = 83 000 € | 47 000 | 1,0 Md€ = 21 000 € |

La valeur de 20 000 € est celle d'un emploi au SMIC ; les 32 heures généralisées touchent tous les salaires.

**Second défaut.** Ces embauches entrent aussi dans le PIB par `hors_conj × valeur_ajoutee_emploi` (lignes 385-396),
alors que leur production est déjà dans le PIB par la ligne 220 : ≈ 20 Md€ de PIB comptés deux fois pour Roussel et
Arthaud (0,6 point).

**Correction proposée.** Garder la production préservée, et ne laisser dans la ligne des embauches que l'allocation
chômage évitée. Évaluer les emplois perdus au salaire moyen du privé, pas au SMIC. Retirer ces embauches de
`hors_conj`.

**Effet** : de −7 Md€ (double compte seul) à −23 Md€ (emplois perdus valorisés comme les embauches) pour Roussel,
−8 à −25 pour Arthaud, −1 à −3 pour Mélenchon. Soit jusqu'à +0,7 point de déficit.

**Vérifié.** Les 350 000 emplois des 35 heures viennent bien de la Dares (Gubian et al., *Économie et Statistique*,
2005). Ce chiffre est net, avec aides et modération salariale : s'en servir pour les embauches brutes, puis retirer
à part l'effet du coût horaire, est cohérent. Les effectifs de Mélenchon (1,3 à 3 millions) et la durée d'Arthaud
(31,8 heures) restent des lectures, comme le dit le brief ; je n'ai pas relu Sumer en ligne.

---

## 5. Écologie de droite : sources, fraude à la TVA, logement, mesures « méthode »

- **Sources.** 135 des 161 hypothèses du programme n'ont pas de champ `source`, et 78 n'ont ni source ni note. Les
  autres programmes en ont 1 à 4 sans source, sauf Mélenchon (34) et Tondelier (31). Parmi les 78 : les paramètres du
  carbone importé (`carbone_importe.*`), `macro.part_capital_nouveau`,
  `is_investissement.part_investissement_concernee`.
- **Fraude à la TVA** (`macro.fraude_tva`, `parametres.yaml:466`) : 2,25 Md€ au prudent, sans source ni note. Les
  autres programmes reçoivent 0,5 à 0,6 Md€ pour la lutte contre la fraude (Tondelier, Mélenchon, Roussel). La règle
  « chaque économie saisie est sourcée » n'est pas tenue ici.
- **Logement.** Le programme compte 2,7 Md€ de recettes et 9 000 emplois pour le droit à construire, par un canal
  propre. Les mesures de logement des autres (Retailleau, Attal, Lisnard, Mélenchon) n'ont ni canal ni barème.
- **Mesures « méthode ».** Au médian, elles ajoutent 33,6 Md€ au solde de 2037 (santé 14,0 ; IA 7,5 ; tendance 6,5 ;
  économies du registre 5,6). Le journal du 12/11 mesure l'écart avec un registre par scénario : +4 Md€ au médian,
  +26 Md€ à l'optimiste en 2037, en faveur du programme. Arbitrage « plus tard » : le biais reste dans les chiffres
  publiés.

**Correction proposée.** Sourcer ou ramener au barème commun la fraude à la TVA ; ouvrir un canal logement commun ou
retirer celui du programme ; bâtir le registre par scénario avant toute publication de l'optimiste ; lancer sur ce
programme la même revue des sources que sur les autres.

## 6. Baisse de l'écart de taux : gagnée par des trajectoires qui divergent

**Fichier** : `moteur/noyau.py:302-316`. Une année compte dès que le déficit est sous celui du statu quo, et ne se
perd jamais. Or le déficit du statu quo explose (9,5 % en 2037, 20,6 % en 2050 au prudent).

**Preuve** (`sorties/comparaison_trajectoire.csv`) :

| Programme, scénario | Année | Déficit | Dette | Baisse du taux |
|---|---|---|---|---|
| Bertrand, médian | 2037 | 7,3 % | 148 % | 20 points de base |
| Lisnard, médian | 2073 | 53,2 % | 680 % | 20 |
| Attal, médian | 2073 | 44,0 % | 565 % | 20 |
| Tondelier, optimiste | 2073 | 33,8 % | 459 % | 40 |

Une dette de 459 % du PIB garde une prime de crédibilité. De plus, la prime de dette baisse déjà quand la dette est
sous celle du statu quo (`prime_marche`, symétrique) : le même écart est récompensé deux fois, dans la limite de
80 points de base.

**Correction proposée.** Un critère absolu : déficit sous un seuil (3 %, ou le solde qui stabilise la dette), ou
dette en baisse. Une année acquise se perd si le critère n'est plus rempli. Effet : nul au prudent (barème nul),
quelques dixièmes de point de PIB d'intérêts au médian et à l'optimiste après 2040.

## 7. PIB publié : un poste public ne produit rien après cinq ans

**Fichier** : `moteur/programme_simple.py:382-396`. Les postes publics sont exclus de la valeur ajoutée (« déjà dans
le PIB par leur dépense et le multiplicateur »), mais le multiplicateur s'efface en quatre à cinq ans. Les emplois privés
évincés, eux, sont retirés du PIB pour toujours.

**Effet.** En comptabilité nationale, un poste public produit son coût. En 2037, le PIB de Roussel est sous-estimé
d'environ 35 Md€ (642 000 postes, 1,1 point), celui de Mélenchon et de Tondelier de 0,6 à 0,7 point ; celui de
Lisnard, Philippe et Retailleau est surestimé d'environ 11 Md€ (0,3 point). Les écarts de PIB cités dans le
comparateur (−6,6 % pour Roussel, +3,1 % pour Lisnard) en sont faussés, et le déficit en points de PIB de 0,1 à
0,35 point.

**Correction proposée.** Ajouter au PIB le coût des postes créés, et le retirer pour les postes supprimés, une fois
le multiplicateur éteint.

## 8. Deux effets comptés pour les uns et pas pour les autres

- **Émissions de Zemmour : zéro.** Le programme n'a pas de groupe `zemmour_ecologie`. Il baisse pourtant d'un tiers
  l'accise sur les carburants (ZEM-FIS-01b), supprime l'Anah, l'Ademe et le soutien aux renouvelables. Les mesures
  voisines sont comptées ailleurs : Le Pen +8,1 Mt (TVA sur l'énergie), Arthaud +3,7 (carburant à prix coûtant),
  Retailleau +2,2 (fin de MaPrimeRénov'). Le comparateur dit que ces effets « ne sont pas encore modélisés » ; en
  attendant, Zemmour affiche les émissions du statu quo.
- **Immigration.** Les régularisations rapportent 0,4 Md€ à Mélenchon et 0,2 à Glucksmann. La baisse de
  l'immigration (Zemmour, Le Pen, Philippe « divisée par deux », Retailleau) ne compte que des économies ; son effet
  sur la population active est écrit « non modélisé ». Ordre de grandeur pour un solde migratoire nul (mon estimation, non simulée) : 200 000 à
  250 000 emplois de moins en 2037, soit ≈ 0,8 % de PIB, et une part des retraites dans le PIB plus haute de
  0,1 point, davantage ensuite.

**Correction proposée.** Chiffrer les émissions de Zemmour avec les règles déjà écrites pour Le Pen et Retailleau.
Pour l'immigration : une variante démographique commune (projections de l'Insee à solde migratoire bas), ou retirer
les recettes des régularisations tant que l'autre sens n'est pas compté.

## 9. Fiscalité des entreprises : l'ordre des scénarios est rompu

**Fichiers** : `parametres/commun/economie.yaml:302-304` (`macro.elasticite_invest` : 0,37 / 0,335 / 0,30 / 0,37),
`moteur/offre.py:281-291`.

**Constat.** Ce paramètre a été réglé pour Écologie de droite, qui relève l'IS : la crise y prend la valeur haute.
Le canal d'offre commun le réutilise dans les deux sens. Effet de long terme d'un point de PIB d'IS en moins :
crise 0,505 % de PIB, prudent 0,457, médian 0,410, optimiste 0,505. Pour une baisse d'impôt, la crise est aussi
favorable que l'optimiste, et le prudent plus favorable que le médian. Pour une hausse (scénario miroir), le prudent
perd moins que le médian.

**Preuve** (expérience 3). Lisnard, fiscalité des entreprises, 2037 : +0,26 % de PIB au prudent, +0,20 % au médian.
Philippe, canal d'offre entier : 12,9 Md€ de PIB au prudent, 12,0 au médian.

**Correction proposée.** Pour le canal commun, une série croissante (0,24 de l'OFCE en crise, 0,30, 0,335, 0,37) ; le
scénario miroir fait le reste. Effet : 1 à 2 Md€ par programme.

## 10. Comparateur : chiffres et ton

J'ai comparé une soixantaine de chiffres des résumés « En bref » aux sorties. Les fichiers
`sorties/comparaison_*.csv` sont identiques au recalcul (écart nul sur le déficit et le chômage, tous programmes,
scénarios et années). À corriger :

| Programme | Texte | Sorties |
|---|---|---|
| Écologie de droite | « environ 19 Mt […] contre 8 à 9 pour La France insoumise et les Écologistes » (2050) | Mélenchon 8,5 ; Tondelier 5,3 |
| Écologie de droite | « le déficit est tenu à 3 % du PIB dès 2029 » | 3,5 en 2030, 3,4 en 2032, 3,2 en 2050 |
| Écologie de droite | rien sur les créances des ménages | dette et créances : 134 % en 2037, 142 % en 2050 (dette : 124 %) |
| Philippe | « solde primaire 0,2 point au-dessus du statu quo » | 0,12 point |
| Zemmour | « plus de 80 [Md€ d'économies] dans le médian » | 77,9 |
| Tondelier, Glucksmann, Le Pen | « environ 260 000 seniors » | 277 000 en 2037 (Roussel est cité à sa valeur de 2037) |
| Arthaud | « plus d'un million d'emplois perdus » | 1,63 million |

**Ton.**
- Tondelier est présentée comme « un programme de hausse des dépenses sociales et publiques » ; l'écologie, son
  thème, vient en dernière phrase. Zemmour est présenté comme « un programme de fortes baisses d'impôts » ;
  l'immigration vient en fin de paragraphe. Les autres sont décrits par leur projet (« social-démocrate et
  européen », « libéral, contre la bureaucratie »). Même défaut que celui relevé le 7/11 pour Mélenchon.
- « Barème commun des réformes de structure de l'OCDE » revient dans dix résumés, en faveur de la droite et contre la
  gauche. La formule prête à l'OCDE une notation qui est celle du modèle (point 2).
- Tondelier, Mélenchon, Zemmour et Bertrand n'ont pas leur déficit de 2037 dans le texte ; les autres l'ont.

---

## Points de moindre gravité

**11. Enveloppe d'économies non détaillées.**
- Le plafond `annonce` mêle les unités : Attal 150 et Bertrand 100 sont des cumuls sur cinq ans, comparés à des
  économies annuelles (`programme_simple.py:158`). Le plafond ne mord jamais ; sans effet aujourd'hui.
- La capacité par domaine borne les économies non nommées, pas les nommées. Zemmour nomme ≈ 19 Md€ sur les missions
  de l'État hors postes (25 avec), pour une capacité de 6 Md€ (État et opérateurs, prudent) tirée des précédents. Soit la
  capacité est trop basse, soit ces lignes sont trop hautes : à trancher par Adrien.
- Les capacités elles-mêmes (15 Md€ au prudent, cinq domaines) sont dans l'ordre des précédents cités.

**12. Canaux IA et école.** Même valeur pour un plan de 200 Md€ (Attal) et pour un objectif sans montant (Zemmour).
Négligeable au prudent (0,5 Md€). À l'optimiste, 42,7 Md€ par programme en 2050 selon le journal ; avec le point 1,
quatre fois moins.

**13. Arthaud, interdiction des licenciements.** Le coût (15,1 Md€) est le produit de quatre hypothèses sans source :
250 000 emplois, 60 % maintenus, 25 % de sorties par an, 25 000 € par emploi. Le stock vaut le flux divisé par le
taux de sortie : à 10 % de sorties, 37 Md€. La mesure écrite vise tous les licenciements ; le calcul ne couvre que
les défaillances. Ordre de grandeur acceptable, à présenter comme tel.

**14. Sources et ordre des scénarios dans les paramètres.** L'audit des 517 mesures simples ne trouve aucune
inversion, sauf `melenchon_mesures.superprofits` (1 Md€ en crise, 0 ailleurs, voulu ; Tondelier compte la même taxe
0,5 à 1,5 Md€ dans tous les scénarios) et `melenchon_mesures.depenses_communes_th`, miroir de la taxe d'habitation
rétablie (neutre). Recettes ou économies sans champ `source` : Tondelier (fraude, IS minimal,
niches, aérien, malus au poids, fiscalité de santé, superprofits, médicaments, économies diverses), Mélenchon (niches,
IS progressif, épargne à l'étranger, taxes sur le sport), Bertrand (audiovisuel). 45 mesures de Tondelier et 28 de
Mélenchon ont le même montant dans les quatre scénarios.

**15. Documentation et rangement.**
- `README.md` cite `moteur/trajectoire.py` et `outils.cibles_crise`, supprimés ou sans objet depuis le 12/11.
- `docs/statu_quo.md` indexe les prestations sur les prix ; le code les indexe sur les salaires.
- `macro.baisse_spread` et `macro.annees_baisse_spread`, lus par la règle commune du noyau, sont dans le fichier
  d'Écologie de droite. Ce sont les deux seuls paramètres de ce fichier lus quand on simule un autre programme
  (expérience 2).

**16. Statu quo, pour mémoire.** Le solde primaire du statu quo est stable (−2,6 % en 2029, −2,7 % en 2037). Toute
la dérive vient des intérêts : 3,4 % du PIB en 2029, 6,8 % en 2037, 17 % en 2050. Les déficits publiés mêlent donc
l'effet des mesures et celui de la dette. L'écart de solde primaire, déjà dans les sorties, est la mesure la plus
robuste : je suggère de le mettre en premier dans le comparateur.
`ancien_systeme.pension_nouveaux_relative` = 1,0 : la source citée donne 0,935 ; le calage sur le COR tient à quatre
points de contrôle (2030, 2045, productivité à 0,4 % et 1,0 %), mais la sensibilité à la productivité est plus faible
que celle du COR (2,1 points de PIB par point de productivité contre 2,7). Acceptable, à valider.

---

## Points vérifiés et jugés corrects

- **Sorties à jour** : les CSV du dépôt reproduisent le code du commit, à 0,001 près.
- **Ordre des scénarios sur les résultats** : déficit crise ≥ prudent ≥ médian ≥ optimiste pour chaque programme et
  chaque année, sans exception. PIB relatif au statu quo : deux inversions sans portée (Le Pen 2029-2030, Bertrand
  2029).
- **Émissions** : 53 paramètres, tous sourcés, tous dans le bon ordre (le prudent est le moins favorable au climat).
- **Mêmes calculs pour les mêmes mesures** : retour à 62 ans 25,45 Md€ (Tondelier, Glucksmann, Le Pen) ; 60 ans
  47,87 (Mélenchon, Roussel) ; 65 ans 10,60 (Philippe, Lisnard, Zemmour) ; aide au développement 9,3 en 2032 (trois
  programmes) ; postes non remplacés sur la règle commune ; abrogation des réformes de l'assurance chômage
  190 000 chômeurs (quatre programmes) ; SMIC par la même fonction.
- **Aucune économie annoncée reprise** : les annonces ne servent que de plafond à l'enveloppe.
- **Isolation des programmes** : simuler un autre programme ne lit aucun paramètre d'Écologie de droite, sauf les
  deux du point 15.
- **Source du barème** : taille des réformes typiques (−0,31 et −0,30) et effet à cinq ans de l'ETCR (≈ 0,7 %)
  retrouvés dans des présentations de l'OCDE et du Trésor. Les effets à dix ans et à long terme ne sont pas
  vérifiés : le document n'était pas accessible depuis cette session.
- **Tests** : `test_canaux_declares.py`, `test_noyau.py`, `test_programmes.py` : 25 tests passent (9 min 29 s).

## Ce que je n'ai pas fait

- La suite complète des tests (un fichier prend 40 minutes).
- La relecture ligne à ligne de `programmes/tondelier/programme.py`, de `programmes/ecologie_de_droite/budget.py` et
  des modules propres à Écologie de droite (cohortes, épargne, impôt unique, entreprises).
- La vérification en ligne des sources, sauf deux (OCDE, 35 heures).
- La comparaison des fichiers de données de l'artefact avec le commit : seul le texte est lu.
- `moteur/ecologie/emissions.py` : lu en partie ; les tonnes de la phase 2 ne sont vérifiées que sur l'ordre des
  scénarios et la présence d'une source.
- Les points de la première relecture, déjà appliqués.

## Expériences (hors dépôt, à joindre si utile)

| Script | Objet |
|---|---|
| `audit_params.py` | Ordre des scénarios, sources, statuts des paramètres |
| `run_all.py` | Recalcul des quatorze trajectoires, comparaison aux CSV |
| `exp2.py` | Paramètres d'Écologie de droite lus par un autre programme |
| `exp3.py` | Canal d'offre par instrument et par scénario |
| `exp4.py` | Dividende de productivité du statu quo, variantes A et B |
| `exp6.py` | Leviers de la règle de trajectoire d'Écologie de droite, année par année |

## Sources

- [OCDE, Égert et Gal, document de travail n° 1354](https://www.oecd.org/content/dam/oecd/en/publications/reports/2017/02/the-quantification-of-structural-reforms-in-oecd-countries_b5d58c7d/2d887027-en.pdf)
- [Trésor, présentation de B. Égert : réforme typique de l'ETCR (−0,31), effets à cinq ans par canal](https://www.tresor.economie.gouv.fr/Articles/4780e961-e91f-431a-833b-0b9d67b029f2/files/b07ce64f-02b5-433c-8b4e-deb4a3ac039b)
- [OCDE, B. Égert, « The Role of PMR » (2023) : ETCR, canaux de la productivité, du capital et de l'emploi](https://www.oecd.org/content/dam/oecd/en/events/2023/3/Session%201_Egert_FINAL.pdf)
- [Insee, Gubian, Jugnot, Lerais et Passeron, « Les effets de la RTT sur l'emploi », Économie et Statistique n° 376-377, 2005](https://www.insee.fr/fr/statistiques/1376464)
