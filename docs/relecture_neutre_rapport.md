# Relecture neutre du chiffrage des programmes 2027 (7 novembre 2026)

Relecteur indépendant, dépôt en lecture seule (aucun fichier du dépôt modifié, aucun test complet lancé). Base :
`sorties/comparaison_mesures.csv` du 7/11 16:44, scénario prudent, et calculs refaits dans `/tmp/relec/` avec les
fonctions du moteur (`bib.baisse_age_legal_detail`, `bib.report_age_legal_detail`). Convention : un montant
positif améliore le solde (Md€ de 2026). Les règles de l'auteur sont prises comme données : aucune économie
annoncée reprise, quatre scénarios, sens des scénarios, multiplicateur miroir pour une relance.

Le même défaut touche souvent la gauche et la droite. Quand c'est le cas, je le signale, avec l'effet de la
correction pour chaque camp.

---

## 1. Retraites : le retour à 62 ans est compté environ deux fois trop cher, surtout de 2028 à 2031 (Tondelier, Glucksmann, Mélenchon)

**Fichiers** : `moteur/bibliotheque.py::baisse_age_legal_detail`, `parametres/commun/economie.yaml:
ancien_systeme.part_retraites_age` (profil à 64 ans), `tondelier|glucksmann|melenchon_retraites.profil_62_ans`,
`melenchon_retraites.profil_60_ans`.

**Ce que fait le modèle** (prudent, pensions en plus) :

| | 2029 | 2030 | 2032 | 2035 | 2040 |
|---|---|---|---|---|---|
| 62 ans (Tondelier, Glucksmann) | 31,6 | 31,4 | 31,2 | 32,0 | 29,3 |
| retraités en plus (millions) | 1,27 | 1,26 | 1,25 | 1,29 | 1,18 |
| 62 puis 60 ans (Mélenchon) | 38,2 | 44,6 | 58,3 | 58,6 | 54,3 |

Soit environ 1 point de PIB dès 2029, un an après l'entrée en vigueur. Trois causes :

1. **Saut de stock en 2028.** Le scénario de référence applique le profil à 64 ans à toutes les générations, y
   compris celles nées en 1961-1966. Or la loi réelle leur donne 62 ans 3 mois à 63 ans 3 mois. La LFSS 2026 a
   suspendu la réforme : 62 ans 9 mois pour 1964, 63 ans pour 1965, 63 ans 3 mois pour 1966, 63 ans 6 mois pour
   1967, 63 ans 9 mois pour 1968, 64 ans à partir de 1969. Au passage à 62 ans en 2028, le modèle fait donc
   partir d'un coup toutes les personnes de 62 à 69 ans qui « attendaient 64 ans » (1,27 million). En réalité,
   seules les générations 1966 et suivantes sont concernées, et pour un retard de 1,25 à 2 ans.
2. **Profil à 64 ans trop tardif après 64 ans.** Ce profil est le profil de 2023 décalé de deux ans « au-delà de
   60 ans ». Il retarde donc aussi les départs de 65 à 69 ans : il suppose que l'âge du taux plein automatique
   passe de 67 à 69 ans, ce que la réforme de 2023 n'a pas fait. Écart entre les deux profils après 64 ans :
   ≈ 0,46 année de pension par génération, sur ≈ 1,46 au total.
3. **Calage trop large.** Le coefficient `k` (dépenses totales / pensions reconstituées) applique aux retraités
   en plus des dépenses qu'ils ne déclenchent pas (réversion, minimum vieillesse), soit ≈ +15 %.

Le modèle se contredit d'ailleurs lui-même : `seniors.part_concernee = 0,4` est calé sur l'étude d'impact de 2023,
qui compte ≈ 470 000 personnes concernées pour deux ans d'âge légal, contre 1,25 million de retraités en plus dans
le calcul des pensions.

**Chiffrages publics** :
- Étude d'impact 2023 (reprise par l'IFRAP) : relèvement de l'âge à 64 ans = 13,6 Md€ de 2020 en 2030, soit
  ≈ 16 Md€ de 2026. Réforme entière : 17,7 Md€ bruts et 13,7 Md€ nets en 2030.
- Institut Montaigne : abrogation = 14,1 Md€ en 2030.
- M. Zemmour (Sciences Po) : ≈ 20 Md€ en 2032 pour l'abrogation entière, mesures sociales gardées.
- Cour des comptes (P. Moscovici, mars 2025) : ≈ 10 Md€ de déficit en plus (10,4 Md€ en 2035).
- COR (repris par Fipeco) : la réforme de 2023 baisse les dépenses de retraite d'environ 0,2 point de PIB en 2030.
- Institut Montaigne 2022 (méthode DREES) : passer de 62 à 60 ans = 0,43 point de PIB. Le paquet entier de
  Mélenchon 2022 (60 ans, 40 annuités, taux plein à 65 ans, sur une base de 62 ans) = 1,2 point.

**Correction proposée** :
- Calculer l'écart génération par génération sur le calendrier légal réel : retard = âge légal de la loi (LFSS 2026)
  − 62. Garder 67 ans comme âge du taux plein dans le profil à 64 ans : redresser les parts à 65-67 ans vers le
  profil de 2023.
- Caler l'effet à plein sur ≈ 0,45 à 0,5 million de retraités en plus pour deux ans d'âge (étude d'impact),
  puis recaler `seniors.part_concernee` (≈ 0,9 à 1) pour ne pas réduire deux fois l'effet sur l'emploi des seniors.
- À défaut, montants cibles des pensions en plus (Md€ de 2026) :

| Mesure | Année | crise | prudent | médian | optimiste |
|---|---|---|---|---|---|
| 62 ans | 2029 | 9 | 8 | 7 | 6 |
| 62 ans | 2032 et après | 20 | 18 | 16 | 13 |
| Mélenchon (62 ans puis 60 ans, profil à 60 ans comprenant les 40 annuités) | 2029 | 13 | 12 | 11 | 10 |
| Mélenchon | 2032 et après | 55 | 52 | 48 | 45 |

**Effet sur le solde (prudent)** :
- Tondelier et Glucksmann : ≈ **+20 Md€ en 2029** et ≈ **+13 Md€ en 2032** (+0,4 point de PIB). Le calcul pour
  2032 : pensions +13,2, prélèvements sur pensions −1,6, canal seniors +2,0. Le multiplicateur de 2029 baisse un
  peu aussi.
- Mélenchon : ≈ **+26 Md€ en 2029**, +20 en 2030, ≈ +7 en 2032 (LFI-RET-02 gardé à part).

## 2. Retraites : le report à 65 ans est surestimé d'environ un tiers ; Retailleau est mal lu (Bertrand, Zemmour, Philippe, Retailleau, Lisnard)

**Fichiers** : `bib.report_age_legal_detail`, `<prog>_retraites`, `retailleau_retraites.part_economie_gardee`.

**Ce que fait le modèle** : un an d'âge en plus donne 0,57 million de non-retraités et 13,5 Md€ d'économie à plein
effet (0,41 point de PIB, en 2040). En 2032 : 7,4 Md€ pour Philippe et Zemmour, 4,8 pour Bertrand et Retailleau.
Le profil est celui du point 1 : décaler de 64 à 65 ans revient aussi à reporter de 67 à 68 ans l'âge du taux
plein automatique. Le gain est donc gonflé de la même façon.

**Référence** : Cour des comptes (février 2025). Un an de plus (65 ans, à partir de la génération 1972) améliore
le solde de 8,4 Md€ en 2045 (≈ 9,2 Md€ de 2026). Revenir à 63 ans coûte 4,3 Md€.

**Correction proposée** : même recalage qu'au point 1, soit ≈ 0,68 × l'économie actuelle.
- À plein effet : crise 7,5 / prudent 8,5 / médian 9,5 / optimiste 10,5 Md€.
- En 2032 : prudent ≈ 5,0 pour Philippe et Zemmour, ≈ 3,3 pour Bertrand et Retailleau.
- Le report doit aussi être défini par rapport au calendrier réel de la LFSS 2026, dans le statu quo comme dans la
  mesure : la génération 1966 a 63 ans 3 mois, pas 64.

**Retailleau, en plus** : sa mesure (LCP, 23/09/2026) ne relève pas l'âge à 65 ans. Elle combine :
- un âge minimal abaissé à 63 ans, avec une décote de 7 % par an, proche de la neutralité ;
- un taux plein automatique **abaissé de 67 à 65 ans** ;
- une décote à 64 ans pour les assurés qui ont leur durée, d'où des départs plus tardifs et une économie.

L'abaissement de 67 à 65 ans a un coût qui n'est pas compté. Environ 7 % d'une génération part à 67 ans pour
avoir le taux plein (DREES, fiche 16) : 0,07 × 0,8 million × 2 ans × ≈ 14 000 € ≈ 1,6 Md€, plus ≈ 0,5 Md€ de
décote annulée à 65-66 ans, soit ≈ 2 Md€ à plein effet. Proposition : solde de la mesure à plein effet de
crise 0 / prudent +1 / médian +2,5 / optimiste +4 Md€, contre ≈ +9 aujourd'hui.

**Effet sur le solde (prudent)** :
- Philippe, Zemmour, Lisnard : ≈ −2 Md€ en 2032, ≈ −4 Md€ en 2040 (net des prélèvements et du canal seniors).
- Bertrand : ≈ −1,3 en 2032, −2,8 en 2040.
- Retailleau : ≈ −3,5 en 2032, ≈ −7 en 2040.

## 3. Philippe : les « aides aux entreprises supprimées » sont estimées à partir du chiffre annoncé (+35,8 Md€ en 2032)

**Fichier** : `philippe_mesures.aides_entreprises_travail` (14 / 17 / 20) et `aides_entreprises_capital` (21 / 25,5
/ 30), prudent = 70 % des 50 Md€ annoncés.

**Problème** : la règle écarte le chiffre du candidat, mais ici les scénarios sont des pourcentages de ce chiffre.
Les aides ne sont pas nommées, et 70 % en prudent est la plus forte réalisation retenue parmi tous les candidats.
À comparer : Lisnard, subventions compensant les charges supprimées, +4,1 Md€.

**Précédents** :
- La LFSS 2025 visait 4 Md€ d'allègements en moins et en a retenu ≈ 1,6.
- Le rapport Bozio-Wasmer (2024) propose de redéployer quelques milliards d'allègements, pas de les supprimer.
- Commission d'enquête du Sénat (rapport n° 808, 2025) : 211 Md€ d'aides en 2023, dont la plupart sont des
  allègements de cotisations et des dépenses fiscales. Les supprimer revient à relever les prélèvements des
  entreprises mêmes que la baisse des impôts de production veut soulager.

**Correction proposée** : estimation indépendante de l'annonce, sur les leviers identifiables (crédit d'impôt
recherche des grands groupes, taux réduits, subventions sectorielles, allègements au-delà de 2 SMIC). Total en
Md€ : crise 12 / prudent 20 / médian 28 / optimiste 35, réparti 40 / 60 comme aujourd'hui.

**Effet** : ≈ **−15,8 Md€** en 2032 en prudent. L'effet d'offre négatif lié à la hausse du coût du travail baisse
un peu.

## 4. Non-remplacement des fonctionnaires : réalisation prudente trop haute par rapport au précédent de la RGPP (Zemmour, Lisnard, Retailleau)

**Fichiers** : `zemmour_mesures.non_remplacement_*` (prudent 400 000 postes), `lisnard_mesures` LIS-TER-07
(70 % de 400 000), `retailleau_mesures.postes_*`.

**Problème** : la source citée par Zemmour donne ≈ 150 000 postes de l'État en cinq ans pour la RGPP (Cour des
comptes, 2012). L'État ne décide ni des effectifs des collectivités ni de ceux des hôpitaux. 400 000 postes en
prudent, c'est 2,7 fois le seul précédent.

**Correction proposée** (postes réellement non remplacés à l'horizon 2032, même règle pour les trois candidats) :
crise 120 000 / prudent 200 000 / médian 300 000 / optimiste 400 000, plafonnés à l'annonce.
Philippe (un départ sur trois, ≈ 180 000) est cohérent avec ces valeurs.

**Effet en prudent, 2032** :
- Zemmour : ≈ −5 Md€ (−11 Md€ bruts, +6,3 de prélèvements, éviction libérée moindre).
- Lisnard : ≈ −2,5 Md€.
- Retailleau : ≈ −3 Md€.

## 5. Postes payés au SMIC : 57 % de prélèvements récupérés, c'est trop (Mélenchon surtout)

**Fichier** : `programme_simple.part_prelevements_fp` (57 %, taux moyen des agents publics) appliqué par `fp: true`
à LFI-EDU-10 (conscription au SMIC, 23 Md€), LFI-EMP-01 (garantie d'emploi, 8,6), LFI-EMP-02 (emploi jeune, 4,8)
et aux embauches de bas niveau (Arthaud ART-SP-01, Tondelier FP-04 pour les AESH).

**Problème** : pour un contractuel public au SMIC, il n'y a ni cotisation au CAS Pensions à 74 % ni impôt sur le
revenu. Les cotisations employeur et salarié, la CSG et la CRDS font ≈ 38-40 % du coût, avant même la prime
d'activité versée.

**Correction proposée** : paramètre `fp_taux` par mesure, ≈ 0,39 pour les emplois au SMIC, 0,57 sinon.

**Effet** :
- Mélenchon : ≈ **−6,5 Md€** en 2032 (prélèvements surcomptés sur 36,4 Md€).
- Arthaud et Tondelier (AESH) : ≈ −1 à −2 Md€.

## 6. Attal, « droit au brut » : le prudent est sous le calcul de la fiche

**Fichier** : `attal_droit_au_brut.baisse` = 50 / 46 / 42 / 40.

**Problème** : la fiche calcule elle-même ≈ 52 Md€ (≈ 215 € par mois pour ≈ 20 millions de salariés), et le
modèle répartit ensuite le montant entre privé et public. S'il s'agit d'un coût, le prudent doit être au moins
égal au calcul. Si les agents publics sont compris, le coût dépasse plutôt 60 Md€.

**Correction proposée** : crise 58 / prudent 52 / médian 46 / optimiste 40. Le montant de 40 cité par la presse
reste l'optimiste.

**Effet** : ≈ −4,5 Md€ net en 2032 (−6 bruts, impôt sur le revenu et prestations rendus).

## 7. Impôts de production assis sur les salaires : une partie est payée par les administrations elles-mêmes (Philippe, Lisnard)

**Fichiers** : `philippe_mesures.impots_production_travail` (taxe sur les salaires et versement mobilité, −20 Md€)
et la ligne équivalente de Lisnard (−16,4 Md€).

**Problème** : les hôpitaux publics paient la taxe sur les salaires. Les employeurs publics de onze salariés et plus
paient le versement mobilité. Ces montants circulent entre administrations : les supprimer ne coûte rien au solde
consolidé. Ordre de grandeur, **à vérifier** dans le rapport Voies et moyens et les comptes des hôpitaux :
≈ 3 à 5 Md€ sur 26.

**Correction proposée** : retirer la part publique du montant de la mesure, ou la compter en économie
« participations ».

**Effet** : **en faveur des deux candidats**, ≈ +2 à +4 Md€ chacun.

## 8. Statu quo : la suspension de la réforme (LFSS 2026) n'est pas modélisée (tous les programmes)

**Fichier** : `parametres/commun/economie.yaml: part_retraites_age` (profil à 64 ans pour toutes les générations).

**Problème** : les générations 1964 à 1968 partent 3 mois plus tôt que dans le modèle. Le gouvernement chiffre la
suspension à 0,1 Md€ en 2026 et 1,4 Md€ en 2027 (CMS Francis Lefebvre, d'après l'exposé de la lettre
rectificative). L'effet reste de l'ordre de 1 à 3 Md€ jusqu'en 2032, puis s'éteint.

**Effet** : petit en niveau et commun à tous. Mais c'est la cause du saut de stock du point 1, et il change la
référence des mesures d'âge du point 2. À corriger en même temps.

## 9. Enseignants : coût calculé « × 1,6 le net », incohérent avec les 57 % de prélèvements récupérés (Attal, Retailleau ; Philippe, Lisnard, Glucksmann dans une moindre mesure)

**Fichiers** : `attal_mesures.enseignants`, `retailleau_mesures.enseignants` (« coût employeur ≈ 1,6 fois le net »).

**Problème** : avec un retour de 57 %, le coût net du modèle vaut 0,43 × 1,6 = 0,69 fois le net versé. Or l'État
paie au moins le net. Pour un fonctionnaire de l'État, cotisation au CAS Pensions comprise, le coût employeur
vaut ≈ 2,2 à 2,3 fois le net.

**Correction proposée** :
- Attal : 7,0 / 6,5 / 6,0 / 5,5 Md€ bruts.
- Retailleau : 5,2 / 4,8 / 4,4 / 4,0 Md€ bruts.
- Philippe et Lisnard : appliquer le coefficient ≈ 1,9 au brut, au lieu de 1,4.

**Effet** : −0,6 à −0,9 Md€ net par candidat (Philippe ≈ −1).

## 10. Économies nommées encore à 0 ou « non chiffrées » (règle précisée par l'auteur : estimer, sans reprendre le chiffre du candidat)

Pour cette liste, j'ai relu toutes les fiches `programmes/*/mesures.yaml` et cherché les mesures sans ligne dans les
`parametres.yaml`. Les lignes déjà ajoutées par le coordinateur (Philippe : santé, niches ; Glucksmann : cabinets
de conseil) ne sont pas reprises ici.

| Programme | Mesure | Constat | Estimation proposée (Md€ / an, crise / prudent / médian / optimiste) | Base |
|---|---|---|---|---|
| Mélenchon | LFI-INS-01 Indépendance de la Nouvelle-Calédonie (2028) | non chiffré | 0 / 0,3 / 0,7 / 1,0 à partir de 2029 | La fiche cite ≈ 1,5 Md€ de dépenses de l'État sur place ; « plan de réparation » et coopération après l'indépendance déduits |
| Tondelier | ECO-05 Moratoire sur les nouvelles places de prison | absent des paramètres | 0,1 / 0,2 / 0,4 / 0,6 | Programme « 15 000 places » du statu quo, ≈ 0,5 à 0,7 Md€ d'investissement par an |
| Tondelier | ECO-03 Niches défavorables au climat, voitures de fonction, barèmes kilométriques | absent (sauf si compris dans REC-42 : à vérifier) | 0,1 / 0,3 / 0,6 / 1,0 | Frais réels et barème kilométrique ≈ 2 Md€ de dépense fiscale ; avantage en nature des voitures de fonction |
| Tondelier | REC-46 Taxe sur les bouteilles en plastique, TIRUERT, redevances de dépollution | absent | 0,1 / 0,2 / 0,4 / 0,6 | Contribution plastique de l'UE payée par le budget ≈ 1,5 Md€ (assiette de référence) |
| Tondelier | COT-06 Bonus-malus renforcé sur les contrats courts | absent | 0 / 0,1 / 0,2 / 0,4 | Bonus-malus actuel quasi neutre en recette (Unédic) |
| Tondelier | REC-38 Conditionnement des aides aux entreprises | prudent 0, documenté | à garder | — |
| Attal | ATT-IMM-05 Fin des prestations à l'expiration du titre (proposition du parti) | non chiffré | 0 / 0,05 / 0,1 / 0,2 | Faible : prestations versées après l'expiration du titre ; 3 000 places de rétention à compter en coût (≈ −0,2) |
| Mélenchon | LFI-EMP-08 Quota de contrats précaires | non chiffré | 0 / 0 / 0,2 / 0,5 (assurance chômage) | Effet emploi de signe incertain, documenté ; prudent 0 |
| Bertrand | BER-INS-02 Conseiller territorial | non chiffré | ≈ 0,05 | Indemnités d'élus |
| Lisnard | LIS-TER-06 INSP supprimé | non chiffré | ≈ 0,03 à 0,05 | Budget de l'INSP, recrutement direct à compter en coût |

**Objectifs sans mesures** (Attal 150 Md€, Lisnard −80 puis −200 Md€, Philippe « 50 % social », Retailleau
197 Md€) : je propose de les **laisser à 0** au-delà des mesures nommées. Ce ne sont pas des économies nommées, et
les estimer compterait deux fois les mesures déjà chiffrées. La décision et ses raisons sont à écrire dans les
fiches.

**Effet total** : faible, ≈ +1 à +2 Md€ pour Tondelier, +0,3 pour Mélenchon, le reste négligeable.

## 11. Autres points, moins lourds

- **Consolidation de l'effet multiplicateur 2029** (Mélenchon +50,9, Tondelier +30,3, Glucksmann +25,7 Md€) : il
  est en partie nourri par le saut de pensions du point 1. Ce n'est pas une erreur du multiplicateur, mais il
  baissera de quelques Md€ en 2029-2030 quand le point 1 sera corrigé.
- **Retailleau** : l'âge minimal de 63 ans avec une décote de 7 % est proche de la neutralité ; on peut le laisser
  hors chiffrage (voir point 2).
- **CVAE** : Tondelier REC-35 rapporte 7,2 Md€ (taux 0,75 %), Mélenchon LFI-REC-16 6,1 Md€ (impôt nouveau,
  arbitré « un peu dessous »). Les deux partent de la même base de 8 Md€ (Fipeco) : l'écart est documenté.

---

## Points vérifiés et jugés corrects

- **Défense** : la loi de programmation actualisée (76,3 Md€ hors pensions en 2030) est dans le statu quo. Les
  écarts sont bien calculés contre elle : Retailleau, 100 Md€ en 2032 (≈ 89 Md€ de 2026 contre ≈ 73) ; Arthaud,
  retour au PLF 2027 (`bib.defense_sans_lpm`). Pas de double compte.
- **CVAE** : suppression en 2030 au statu quo (LF 2025, art. 62). Attal ne compte que l'avance sur 2028-2029.
  Tondelier et Mélenchon comptent un rétablissement en recette en plus. Cohérent.
- **Aide publique au développement à 0,7 % du RNB** : 9,3 Md€ pour Tondelier, Glucksmann et Mélenchon, identique.
  Ordre de grandeur juste (APD ≈ 0,4 % du RNB après les baisses 2025-2026).
- **Point d'indice** : rattrapage du gel de 2027 ≈ 2,8-2,9 Md€ chez Tondelier, Glucksmann et Mélenchon, identique.
  +10 % du point pour Mélenchon ≈ 5,6 % du coût des agents (traitement indiciaire ≈ 55 %) : correct.
  Tondelier FP-02 (+9,5 % des rémunérations) est une autre mesure, documentée.
- **SMIC** : même mécanique et mêmes élasticités (−0,8 en prudent) pour Arthaud, Tondelier, Glucksmann et
  Mélenchon. L'écart sur les allègements est documenté : nominalisés chez Tondelier comme le dit son programme,
  en multiples du SMIC, comme la loi, chez les autres.
- **Assurance chômage** : chiffrages voisins d'un programme à l'autre (abrogation : −6,2 à −7,8 Md€ et
  ≈ 3,9 Md€ de chômeurs en plus ; resserrement : +1,5 à +4,6). Les économies annoncées ne sont pas reprises.
- **CSG sur les salaires (Zemmour)** : 101 Md€ (OpenFisca) plus 6,5 Md€ pour les indépendants. Cohérent avec la
  CSG sur les revenus d'activité (≈ 105-110 Md€). La part déductible (6,8 points) revient bien dans l'impôt sur
  le revenu.
- **Lisnard, 120 Md€** : 2,6 points de CSG (≈ 29 Md€) plus ≈ 91 Md€ de cotisations salariales. Le montant
  respecte l'annonce, qui est une mesure et non une économie.
- **Successions (Zemmour)** : ≈ 21 Md€ en 2029, en ligne avec le rendement des droits de mutation à titre
  gratuit.
- **Multiplicateur et loi d'Okun** : les emplois dus à la conjoncture ne reçoivent pas de « valeur d'emploi » en
  plus des recettes du PIB. Pas de double compte. Le miroir pour une relance et la contrainte de capacité sont
  appliqués à tous.
- **Canal d'offre** : symétrique (élasticité miroir en cas de hausse). Les mesures déjà comptées par un effet propre
  (SMIC, postes publics) n'ont pas d'instrument. Pas de double compte.
- **Postes publics** : 55 000 € par poste et 57 % de retour. Cohérent pour des postes au salaire moyen ; à
  corriger seulement pour les emplois au SMIC (point 5). L'éviction est asymétrique (création 1,0, suppression
  0,5 en prudent) mais du même côté de la prudence dans les deux sens : conforme à la règle.
- **Année blanche d'Attal** : effet de niveau permanent. Correct.
- **Sens des scénarios** : je n'ai trouvé aucune inversion dans les lignes de plus de 2 Md€, sauf le niveau du
  prudent d'Attal (point 6).
- **Aucune économie annoncée reprise telle quelle**, sauf Philippe, où le chiffre annoncé sert de base aux
  scénarios (point 3).

## Sources

- [IFRAP, « Mise en garde à ceux qui veulent revenir sur la réforme des retraites »](https://www.ifrap.org/retraite/mise-en-garde-ceux-qui-veulent-revenir-sur-la-reforme-des-retraites) : étude d'impact 2023, 17,7 / 13,7 Md€ en 2030 ; âge à 64 ans 13,6 Md€ de 2020
- [Moneyvox, « Abroger la réforme : 14 à 20 milliards »](https://www.moneyvox.fr/retraite/actualites/98707/abroger-la-reforme-des-retraites-et-le-depart-a-64-ans-combien-ca-coute) : Institut Montaigne 14,1 Md€ (2030), M. Zemmour ≈ 20 Md€ (2032)
- [Public Sénat, Moscovici : « 10 milliards de plus »](https://www.publicsenat.fr/actualites/emploi/retraites-si-vous-abrogez-la-reforme-de-2023-cest-10-milliards-deuros-de-plus-quil-faut-trouver-souligne-pierre-moscovici)
- [Public Sénat, rapport de la Cour des comptes de février 2025](https://www.publicsenat.fr/actualites/societe/retraites-un-deficit-qui-pourrait-atteindre-environ-30-milliards-deuros-dici-2045-selon-le-rapport-de-la-cour-des-comptes) : 65 ans +8,4 Md€ en 2045 ; 63 ans −4,3 Md€
- [Fipeco, note sur les retraites 2023](https://fipeco.fr/pdf/Retraites%202023.pdf) : COR, −0,2 point de PIB de dépenses en 2030
- [Institut Montaigne, Mélenchon 2022, retraite à 60 ans](https://www.institutmontaigne.org/presidentielle-2022/jean-luc-melenchon/retablir-la-retraite-a-60-ans-apres-40-ans-annees-de-cotisation/) : 60 à 62 ans = 0,43 point de PIB (DREES) ; âge et durée 1,2 point
- [CMS Francis Lefebvre, lettre rectificative du PLFSS 2026](https://cms.law/fr/fra/a-la-une/plfss-pour-2026-une-lettre-rectificative-pour-suspendre-la-reforme-des-retraites) : calendrier par génération, coût 0,1 et 1,4 Md€
- [Quelles Aides, suspension de la réforme](https://quelles-aides.fr/mag/reformes/suspension-reforme-retraites-2026-1er-septembre-generations-1964-1968/) : calendrier de 1964 à 1969
- Pour les points 3 et 4, les références sont celles que citent déjà les fiches du dépôt (Sénat, rapport n° 808 ; Cour des comptes 2012 sur la RGPP ; rapport Bozio-Wasmer 2024) ; je ne les ai pas relues en ligne. Le point 7 est à confirmer dans le rapport Voies et moyens.
