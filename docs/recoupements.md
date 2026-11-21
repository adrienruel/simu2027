# Recoupements du statu quo avec les projections publiées (phase C3 de la roadmap)

13 novembre 2026, commit de référence : celui de ce fichier. Statu quo : scénario prudent (`sorties/comparaison_trajectoire.csv`).
Tolérance de la roadmap : 0,5 point de PIB pour les flux ; au-delà, l'écart est expliqué.

| Grandeur | Référence publiée | Valeur publiée | Statu quo (prudent) | Écart | Lecture |
|---|---|---|---|---|---|
| Dépenses de retraite (% du PIB) | COR, rapport annuel de juin 2026, scénario de référence | 14,1 % (2025) ; 14,2 % (2045) ; 15,3 % (2070) | 14,1 % (2029) ; 14,3 % (2040 et 2050) ; 15,3 % (2070) | ≤ 0,1 point | Conforme. Le statu quo suit le COR (même démographie de l'Insee, pensions indexées sur les prix). |
| Retraites (convention européenne, invalidité comprise) | Ageing Report 2024, fiche France (Trésor, décembre 2023), tableau 7 | 14,4 % (2022) ; 14,3 % (2030) ; 13,7 % (2050) ; 13,6 % (2070) | 14,1 % (2029) ; 14,3 % (2050) ; 15,3 % (2070) | +0,6 point en 2050, +1,7 en 2070 | Expliqué : l'Ageing Report 2024 suppose une fécondité de 1,8 ; le COR de juin 2026 retient 1,45 (Insee, avril 2026), comme le statu quo ; l'écart est celui de la fécondité, pas de la méthode. |
| Déficit public à politique inchangée (% du PIB) | FMI, consultation de l'article IV, 22 mai 2025 | « autour de 6 % à moyen terme » sans mesures additionnelles | 5,9 % (2029) ; 6,3 % (2030) | ≤ 0,3 point | Conforme. Le statu quo dérive ensuite (7,2 % en 2032, 8,8 % en 2035) : la charge d'intérêts monte avec la dette. |
| Dette publique (% du PIB) | FMI (scénario sans mesures, repris par la presse, avril 2026) ; IGF, « Trajectoire des finances publiques » (2025) | 124,1 % (2029, FMI) ; « plus de 130 % en 2030 » (IGF) | 128,8 % (2029) ; 132,1 % (2030) | +4,7 points contre le FMI ; dans la fourchette de l'IGF | Écart au FMI expliqué : le FMI part de la dette de 2024 (113,2 %) et de prévisions de déficit de 2025 ; le statu quo part de la loi de finances 2026 et du PLF 2027 (dette de 118,5 % fin 2026 selon la Cour des comptes, juin 2026). La pente 2026-2030 (≈ +3,5 points par an) est celle de l'IGF. |

| Charge de la dette (toutes administrations) | Cour des comptes, situation et perspectives des finances publiques, juin 2026 | « pourrait atteindre 100 milliards d'euros en 2029, soit 3 % du PIB » | 101,8 Md€ de 2026, 3,35 % du PIB (2029) | +0,35 point | Conforme (sous 0,5 point). Taux apparent de 2,7 % en 2029. |
| Chômage (BIT) | Banque de France, projections intermédiaires de septembre 2026 | 8,3 % (2026 et 2027) ; 8,0 % (2028) | 8,3 % (2029, dès l'économie de 2026 placée en 2029) ; 8,1 % en 2050 | +0,3 point en 2029 | Conforme. Le statu quo garde le chômage de 2026 (pas de reflux de 2028). |
| Santé et autonomie (ONDAM et aide sociale à l'autonomie, % du PIB) | OCDE, Panorama de la santé 2025 (moyenne des pays, scénario de référence) ; Ageing Report 2024 (dépendance, France) | santé publique : +1,5 point entre 2024 et 2045 (moyenne OCDE) ; dépendance : 1,9 % (2022) → 2,6 % (2070) | 9,9 % (2029) ; 10,3 % (2040) ; 11,1 % (2050) ; 13,6 % (2070) | ≈ +0,8 point en 16 ans jusqu'en 2045, sous la moyenne de l'OCDE ; +3,7 points à 2070 | Partiel. Jusqu'en 2045, la pente de l'assurance maladie est plus basse que la moyenne de l'OCDE ; après, la pente PROMEDE est plus forte que la seule dépendance de l'Ageing Report. Le chiffre de santé de la fiche France de l'Ageing Report n'a pas été trouvé : à recouper sur la fiche elle-même. |

## Roadmap 1.3 : dérive 2029-2036 contre la Commission européenne (21/11/2026)

Référence : Commission européenne, *Debt Sustainability Monitor 2025* (Institutional Paper 332, février 2026), fiche
France, scénario sans changement de politique. Statu quo médian, après les corrections et arbitrages du 21/11/2026
(prestations par prestation, défense en euros) et le nouveau taux apparent au rythme du refinancement
(`macro.taux_apparent_refinancement`).

| Année | Dette, Commission | Dette, modèle | Intérêts (% du PIB), Commission | Intérêts, modèle avant → après | Taux apparent, Commission | Taux apparent, modèle avant → après |
|---|---|---|---|---|---|---|
| 2029 | 124,2 | 128,5 | 3,3 | 3,35 → 3,35 | 2,8 % | 2,69 → 2,69 % |
| 2030 | 126,5 | 130,4 | 3,5 | 3,68 → 3,65 | 2,9 % | 2,91 → 2,88 % |
| 2032 | 131,7 | 134,2 | 4,1 | 4,42 → 4,22 | 3,3 % | 3,39 → 3,24 % |
| 2035 | 140,8 | 140,0 | 5,0 | 5,67 → 4,97 | 3,7 % | 4,13 → 3,65 % |
| 2036 | 144,0 | 142,0 | 5,3 | 5,82 → 5,19 | 3,9 % | 4,17 → 3,76 % |

- **Intérêts et taux apparent** : conformes depuis la correction, à 0,1 point de PIB près. Avant, le taux apparent
  rejoignait le taux long (4 %) en ligne droite en 6 ans, plus vite que le refinancement réel de la dette : +0,7 point
  de PIB d'intérêts en 2035. Désormais, chaque année, la dette échue (1/8,5, AFT) et la dette nouvelle se financent au
  taux du moment.
- **Dette** : +4 points en 2029-2030, expliqués par la convention « économie de 2026 placée en 2029 » (décision G1
  ouverte) : la Commission fait croître le PIB de 2026 à 2029, le modèle non. Écart refermé en 2035, parce que le
  solde primaire du modèle s'améliore davantage.
- **Solde primaire** : la Commission le garde à −2,1 / −2,2 % du PIB de 2026 à 2036 (structurel, coûts du
  vieillissement compris). Le modèle passe de −2,5 % (2029) à −1,7 % (2035) au médian. Écart d'environ 0,5 point en
  2035, à la limite de la tolérance. Il vient notamment des arbitrages du 21/11 (prestations revalorisées en partie
  sur les prix, défense en euros après 2030) : la Commission garde les dépenses hors vieillissement en part constante
  du PIB. Prudent : −2,1 % en 2035, en ligne.
- **Prudent** : intérêts 5,3 % du PIB en 2035 (+0,3 point sur la Commission), par la prime de dette plus forte.

## Roadmap 1.1 et 1.2 : recettes et dépenses du statu quo (21/11/2026, en cours)

**1.1, dérive de l'impôt sur le revenu** (`statu_quo.baremes_salaires`, `statu_quo.derive_ir_salaires`) :
- **Barème :** il est revalorisé sur les prix, comme le font les lois de finances, et comme les pensions depuis la
  décision du 04/11. Avant, l'impôt des salariés suivait la masse salariale, comme si le barème suivait les
  salaires.
- **Calcul :** l'impôt sur le revenu des salariés monte comme le salaire réel puissance 1,73 (OCDE, Price, Dang et
  Botev, 2015, France). Contrôle : OpenFisca donne 2,0 sur la distribution des salaires du privé, pour une personne
  seule.
- **Assiette :** l'impôt sur le revenu fait 14 % des prélèvements sur les salaires du privé. Cotisations et CSG ne
  dérivent pas.
- **Effet sur les recettes** du statu quo (points de PIB) :

| Scénario | 2037 | 2050 | 2073 |
|---|---|---|---|
| Prudent | +0,13 | +0,34 | +0,75 |
| Médian | +0,23 | +0,55 | +1,19 |

- **Déficit du statu quo, prudent :** 8,12 → 7,95 % en 2037, 16,97 → 16,06 % en 2050.
- **Dividende de productivité** d'un programme : +0,02 environ, car un salaire réel plus haut paie aussi plus
  d'impôt.
- Le choix entre « prix » et « salaires » est la décision G3 d'Adrien. Le réglage « salaires » rend l'ancienne
  convention.

**1.1, répartition impôt par impôt** :
- La répartition doit passer de la colonne « Ancien » de la v235 aux comptes de l'Insee de 2025 (tableaux 3.216 et
  3.217 de « Dépenses et recettes des administrations publiques en 2025 », mai 2026).
- **Bloqué :** les fichiers ne sont pas accessibles depuis l'environnement de travail. Repères 2025 vus en ligne :
  TVA 208,8 Md€, impôt sur le revenu avant crédits d'impôt 103,6, IS avant crédits d'impôt 69,5.
- **Élasticités par impôt :** l'OCDE (2015) donne, pour la France, l'IS à 2,40 sur l'excédent d'exploitation et les
  impôts indirects à 0,91 sur la consommation. Ce sont des élasticités au cycle. À long terme, un impôt
  proportionnel suit son assiette, ce que fait déjà le moteur. Seul l'impôt sur le revenu, progressif, s'en écarte
  de façon durable.

**1.2, blocs de dépense** : chaque bloc a une source (aucun bloc n'est au statut HYPOTHÈSE sans source). Indexation
contre le droit actuel :

| Bloc | Départ (Md€ 2026) | Indexation du statu quo | Droit actuel |
|---|---|---|---|
| Retraites | 428,0 | pensions par génération (COR) | revalorisation sur les prix, salaires portés au compte |
| Santé | 297,4 | âge, coûts relatifs (Ageing Report) | ONDAM voté chaque année |
| Chômage | 46,6 | chômeurs × salaires | allocation sur le salaire de référence |
| Famille | 34,7 | enfants × prix | BMAF sur les prix (L551-1 CSS) |
| Logement | 16,7 | population × prix | paramètres revalorisés sur l'IRL, proche des prix |
| Pauvreté (RSA, prime d'activité) | 24,0 | bénéficiaires × prix, 30 % de la hausse des salaires | prix (L161-25 CSS), coups de pouce réguliers |
| AAH, invalidité | 23,5 | adultes × prix, 80 % (AAH) | prix, revalorisations exceptionnelles de l'AAH |
| Investissement | 133,5 | PIB | — |
| Missions de l'État | 210,4 | règle par mission (élèves, effectifs, salaires publics) | lois de finances |
| Défense et UE | 92,6 | LPM jusqu'en 2030, puis euros ; UE sur le PIB | LPM 2024-2030 actualisée ; ressource RNB |
| Collectivités | 230,3 | salaires × population | — |
| Autres (résidu) | 101,2 | salaires × population | — |

La « défense 2026 » de la v235 (57,1 Md€), qui n'était plus lue, est retirée.

## Roadmap 2.1 : une seule voie d'emploi par mesure (21/11/2026)

Trois mesures tests, emplois de long terme par Md€ de mesure (personnes ; + : emplois en plus). Micro : gain à
travailler de chaque personne en emploi (OpenFisca, population synthétique) × élasticité de participation de sa
tranche × `offre.participation_transferts`. Agrégé : élasticité par point de PIB du canal de l'instrument.

| Mesure test | Voie | Prudent | Médian | Repère |
|---|---|---|---|---|
| Prime d'activité +10 % (1,63 Md€) | micro, miroir personne par personne (avant) | −3 000 | +7 500 | IPP pour France Stratégie (2023), réforme de 2019 : effet non identifiable (placebo de 2018 de même ampleur) ; Cour des comptes (avril 2026) : pas d'effet mis en évidence |
| | micro, miroir sur le sens net (après) | +1 300 | +3 300 | |
| | agrégé, `elasticite_transferts_actifs` (hausse : miroir) | −1 900 | −1 000 | |
| RSA +10 % (1,46 Md€) | micro (après ; baisse nette : miroir) | −27 700 | −10 900 | |
| | agrégé | −1 900 | −1 000 | |
| Aides au logement +10 % (1,68 Md€) | micro (après ; baisse nette : miroir) | −4 800 | −1 900 | |
| | agrégé | −1 900 | −1 000 | |
| Baisse de cotisations au SMIC | cellules, `offre.demande_travail` (zone `smic`) | +21 600 | +29 000 | Trésor-Éco n° 97 (2012) : 20 000 à 40 000 € bruts par emploi pour les allègements de 1993-1997, soit 25 000 à 50 000 emplois par Md€ |
| | agrégé, `elasticite_cout_travail` (Mésange, baisse uniforme) | +9 600 | +14 400 | |
| | cellules, zone `milieu` (1,6 à 3,5 SMIC) | +2 500 | +3 800 | Bozio-Wasmer (2024) : effets faibles au-delà de 1,6 SMIC |
| Recul de l'âge de 64 à 65 ans | canal des seniors (`offre.seniors`) | — | ≈ +210 000 (un an d'âge) | Rexecode (2023), réforme de 2023 (deux ans) : +300 000 emplois en 2030 ; Insee (2023) : +600 000 à +800 000 actifs |
| | micro | non codé (chantier 3.3) | | |

Constats :
- **Prime d'activité** : les deux voies ont le même ordre de grandeur (moins de 4 000 emplois par Md€), mais pas le
  même signe. Logement : même signe, à un facteur 2,5 près. La voie agrégée traite toute aide comme une aide aux inactifs ; la micro voit qu'une aide liée à
  l'activité augmente le gain à travailler de la plupart des bénéficiaires (6,3 millions de gagnants, 5,2 millions
  de perdants, surtout des conjoints dont le contrefactuel change). Le résultat de la micro, petit et positif, est
  compatible avec les évaluations.
- **Défaut corrigé dans la micro** : le scénario miroir était choisi personne par personne. Les perdants prenaient
  l'élasticité du miroir, plus forte au prudent : +10 % et −10 % de prime d'activité perdaient tous deux environ
  5 000 emplois au prudent. Le miroir est désormais choisi sur le sens net de la mesure
  (`outils.openfisca_mesures.emplois_par_scenario`).
- **RSA** : la micro donne dix à quinze fois l'agrégé. Elle compte toutes les personnes en emploi dont le ménage toucherait
  le RSA si elles cessaient de travailler (7,8 millions) ; l'élasticité agrégée de 0,1 ne distingue pas une aide aux
  inactifs d'une aide aux actifs. Une seule voie est gardée, la micro, et l'écart est documenté (critère de la
  roadmap : « une seule voie est utilisée et documentée »).
- **Cotisations au SMIC** : l'élasticité uniforme de Mésange sous-estime d'un facteur 2,2 l'effet d'une baisse
  ciblée au SMIC, et surestime d'un facteur 4 une baisse entre 1,6 et 3,5 SMIC. Une mesure de coût du travail peut
  maintenant déclarer sa zone de salaires (`incidence: smic | milieu | prive`). Elle passe alors par la demande de
  travail cellule par cellule (élasticités par tranche, déjà utilisées pour les réformes calculées par OpenFisca),
  et non plus par Mésange. Sans zone, Mésange reste la voie (impôts de production sur la masse salariale, baisses
  larges). Zones déclarées : Philippe PHI-FIS-01b (allègements au-delà de 2 SMIC : `milieu`, −67 000 → −18 000
  emplois en 2037 au prudent, +2,9 Md€ de solde) ; Lisnard LIS-EMP-05 (embauches au SMIC : `smic`, +3 700 → +8 400
  emplois, −0,07 Md€ de solde, car ces emplois rapportent moins).
- **Âge de départ** : une seule voie (canal des seniors), dans le facteur 2 de Rexecode. La micro ne voit pas les
  pensions de carrière (chantier 3.3) ; ses lignes « retraites » ne sont pas lues par le moteur.
- **SMIC relevé** (Arthaud, Mélenchon, Roussel) : la micro comptait le gain à travailler des salariés dont le
  salaire est relevé (+49 700 emplois pour Mélenchon et Roussel au prudent). Au SMIC, l'emploi est fixé par la
  demande, déjà comptée par le canal du coût horaire (`bibliotheque.smic`) ; ces réponses positives sont désormais
  mises à zéro.

**Règle contre le double compte** (testée par `tests/test_une_voie_emploi.py`) :
1. Une mesure n'a qu'une voie d'emploi. Le moteur choisit dans cet ordre :
   - transfert codé dans OpenFisca (`programmes/micro_mesures.yaml`) : la micro, quel que soit l'instrument
     déclaré ;
   - mesure sur le coût du travail avec zone : la demande par cellule ;
   - mesure sur les prélèvements du travail : les cellules (offre et demande) ;
   - autre instrument déclaré : son élasticité agrégée ;
   - âge de départ : le canal des seniors ;
   - SMIC et temps de travail : le canal du coût horaire.
2. Les emplois d'un canal ne repassent pas par la valeur générique d'un emploi (`programme_simple`, canaux « Offre »
   et « Seniors » exclus).
3. Au SMIC, l'offre ne crée pas d'emploi : seule la demande compte.

**Reste ouvert** (hors 2.1) :
- Des transferts sans instrument ni code OpenFisca n'ont aucun effet d'emploi : année blanche des prestations
  (ATT-FIS-03), économies non détaillées sur les prestations (Bertrand, Philippe), aides aux étrangers (PHI-IMM-05).
  Les classer relève des fiches de programmes (chantier 7).
- L'assurance chômage passe encore par l'élasticité agrégée des transferts (chantier 3.4).
- `parametres/donnees/micro_emploi_2026.csv` recalculé avec les deux corrections (21/11, un programme par
  processus ; sorties de la micro non régénérées). Plus gros changements, emplois en application complète :

| Mesure | Prudent, avant → après | Médian, avant → après | Cause |
|---|---|---|---|
| Arthaud ART-ECO-01 (SMIC à 2 200 € net) | +194 700 → +7 000 | +506 500 → +17 800 | SMIC |
| Mélenchon LFI-SAL-01, Roussel PCF-SAL-01 (SMIC) | +49 700 → +1 500 | +137 900 → +3 900 | SMIC |
| Tondelier PRE-01 (SMIC) | +29 700 → +1 000 | +85 600 → +2 500 | SMIC |
| Glucksmann GLU-ECO-01 (SMIC) | +27 100 → +1 000 | +78 000 → +2 600 | SMIC |
| Mélenchon LFI-REC-02 | +7 500 → +14 300 | +43 100 → +36 300 | miroir |
| Roussel PCF-PRE-01 | −46 700 → −37 600 | −5 800 → −14 800 | miroir |
| Retailleau RET-EMP-01 | +66 100 → +71 900 | +188 400 → +182 500 | miroir |

  Les emplois du SMIC qui restent viennent des aides qui changent pour les autres membres du ménage.

## Reste à recouper (C3)

- Santé : fiche France de l'Ageing Report 2024 (dépenses de santé publiques en 2022 et 2070), DREES ; la pente
  PROMEDE de long terme est à confronter à ce chiffre.

## Sources

- COR, rapport annuel de juin 2026, partie 2, chapitre 4 : https://www.cor-retraites.fr/sites/default/files/2026-06/RA_Part2_Chap4.pdf
- Ageing Report 2024, fiche France : https://economy-finance.ec.europa.eu/document/download/e412927a-ea31-406d-bb6c-c925914123e9_en ; hypothèses comparées COR et Ageing Report (DG Trésor, novembre 2024) : https://www.cor-retraites.fr/sites/default/files/2024-11/Doc_03_Ageing_report.pdf ; COR juin 2026, synthèse (fécondité 1,45) : https://www.cor-retraites.fr/sites/default/files/2026-06/Synth%C3%A8se_RA_2026.pdf
- FMI, déclaration de fin de mission, article IV 2025 : https://www.imf.org/en/news/articles/2025/05/22/cs-france-2025
- France Épargne, reprise des projections du FMI (avril 2026) : https://www.france-epargne.fr/news/le-fmi-alerte-sur-la-montee-des-risques-budgetaires-en-france
- IGF, Trajectoire des finances publiques (2025), sommaire cité par le moteur de recherche (page redirigée, non lue en entier).
- Cour des comptes, situation et perspectives des finances publiques, juin 2026 (dette 2026) : https://www.vie-publique.fr/rapport/303867-la-situation-et-les-perspectives-des-finances-publiques-2026
- Commission européenne, Debt Sustainability Monitor 2025 (février 2026), fiche France : https://economy-finance.ec.europa.eu (Institutional Paper 332 ; copie consultée : https://www.ot.gr/wp-content/uploads/2026/02/ , fiche 10)
- Charge de la dette 2029 selon la Cour (Banque des territoires, 25/06/2026) : https://www.banquedesterritoires.fr/finances-publiques-tous-les-signaux-sont-au-rouge-en-2026-alerte-la-cour-des-comptes
- Banque de France, projections intermédiaires de septembre 2026 : https://www.banque-france.fr/fr/publications-et-statistiques/publications/projections-macroeconomiques-intermediaires-septembre-2026 ; chômage 2026-2027 (Reuters, 15/09/2026) : https://www.easybourse.com/international/news/1537735/la-banque-france-revoit-son-tour-sa-prevision-croissance-2026.html
- OCDE, Panorama de la santé 2025, projections : https://www.oecd.org/fr/publications/panorama-de-la-sante-2025_2f564c6c-fr/full-report/health-spending-projections_d3702f1a.html
- Dépendance, Ageing Report 2024 (profil France, Eurocarers) : https://eurocarers.org/country-profiles/france/
