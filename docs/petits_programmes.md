# Bertrand, Zemmour, Arthaud : les trois plus petits programmes sur le noyau (6 novembre 2026)

Les trois candidats qui ont le moins de mesures sur programmes-2027.fr (33, 36 et 37), chiffrés avec la méthode du
programme Tondelier : statu quo + mesures, aucune économie ni recette annoncée reprise, chaque ligne sans source estimée
en crise / prudent / médian / optimiste, multiplicateur commun, mesures de 2027-2028 dans la dette de départ.

```
python -m moteur.noyau bertrand      # (zemmour, arthaud)
python -m pytest tests/test_petits_programmes.py
```

> **Mise à jour du 6 novembre 2026 (soir)** : demande par instrument, offre durable et emploi des seniors (effets sur
> le PIB) sont ajoutés à tous les programmes du noyau : résultats et méthode dans `docs/offre.md`. Les tableaux
> ci-dessous sont ceux d'avant ces effets.

## Ce qui est nouveau dans le code

- `moteur/bibliotheque.py` : premières briques de la bibliothèque de mesures (point 3 de la feuille de route) :
  report de l'âge légal (même calcul et même calage que les retraites du statu quo), CSG sur les salaires (OpenFisca),
  relèvement du SMIC (reprend le calcul de Tondelier, qu'il retrouve à l'euro près ; deux options ajoutées :
  allègements lus en multiples du SMIC, comme dans la loi, et emplois perdus à élasticité constante), défense au niveau
  du PLF 2027.
- `moteur/programme_simple.py` : la mécanique commune d'un programme (mesures simples au format de Tondelier, postes
  publics et éviction, multiplicateur, emploi, chômage, dette de départ). Un petit programme n'a plus qu'un fichier de
  paramètres, une fiche et une sous-classe de quelques lignes. Suppression de postes publics : l'éviction est prise au
  scénario miroir (prudent → médian), parce qu'une forte reprise par le privé n'est pas prudente quand on supprime.
- `programmes/bertrand`, `programmes/zemmour`, `programmes/arthaud` : `parametres.yaml`, `mesures.yaml` (toutes les
  mesures du site et leur traitement : chiffre, estime, non_chiffre, sans_effet), `programme.py`.

Tondelier n'est pas modifié : son SMIC et son retour à 62 ans pourront être rebranchés sur la bibliothèque.

## Arbitrages pris par Claude, à revoir

| Point | Lecture retenue | Autre lecture |
|---|---|---|
| Âge légal (Bertrand, Zemmour : « reporter », sans âge) | 65 ans, un trimestre par génération dès 1966 (65 ans pour 1969) | 66 ou 67 ans ; indexation sur l'espérance de vie |
| Départ anticipé avec décote (Bertrand) | 60 à 85 % de l'économie gardée (prudent 65 %) | décote actuarielle neutre : tout gardé |
| Capitalisation obligatoire (Bertrand, Zemmour) | cotisation en plus vers des fonds privés : sans effet sur le solde | prise sur les cotisations actuelles : coût de transition de plusieurs dizaines de Md€ par an |
| Baisse de l'IR des premières tranches (Bertrand) | tranche à 11 % ramenée à 9 % (−3 Md€), comme Tondelier | — |
| Flat tax relevée (Bertrand) | +2 points | — |
| Fonctionnaires en moins (Bertrand) | 25 000 à 80 000 postes de l'État (prudent 40 000) en cinq ans | — |
| Plan Knafo (Zemmour) : non-remplacement | 300 000 à 700 000 postes (prudent 400 000), moitié État, 40 % collectivités, 10 % administratifs hospitaliers | 800 000 comme annoncé |
| Plan Knafo : budget européen | dépend de l'unanimité : 0 à 4 Md€ | 14 Md€ annoncés |
| Plan Knafo : IA dans les administrations | zéro en prudent (moyen du non-remplacement, double compte) | 5 Md€ (rapport IGF-IGAS) |
| Suppression de postes publics (tous) | reprise par le privé au scénario miroir ; créations et suppressions comptées chacune avec son taux | — |
| Préférence nationale (Zemmour) | ressortissants européens exclus (droit de l'Union) ; risque constitutionnel dans le prudent | toutes les nationalités étrangères |
| Renouvelables (Zemmour) | seuls les nouveaux contrats disparaissent, économie qui monte jusqu'en 2035 | contrats signés rompus (contentieux) |
| SMIC à 2 200 € net (Arthaud) | allègements qui suivent le SMIC (loi actuelle) | allègements nominalisés (lecture de Tondelier) : coût au SMIC +88 % au lieu de +50 % |
| Embauches (Arthaud : « des centaines de milliers ») | 300 000 postes en cinq ans | — |
| Budget 2027 (Arthaud refuse la sous-indexation des pensions, les gels de prestations, les déremboursements) | le statu quo suppose le PLF 2027 voté : l'annuler coûte ses économies | statu quo sans ces mesures : coût nul |

## Résultats (prudent, Md€ de 2026, + = améliore le solde, contre le statu quo)

**Bertrand** : un programme proche du statu quo. Les 20 Md€ d'économies par an annoncés ne sont pas saisis ; les
lignes identifiées (âge légal, assurance chômage, fonctionnaires) rapportent un peu plus que ce que coûtent la baisse de
l'impôt sur le revenu et les dépenses nouvelles.

| Groupe | 2029 | 2032 | 2037 | 2050 |
|---|---|---|---|---|
| Retraites (65 ans, départs anticipés avec décote) | +0,0 | +4,8 | +9,2 | +9,1 |
| Recettes (IR, flat tax, prélèvements des postes supprimés et des pensions) | −2,8 | −4,2 | −4,9 | −5,1 |
| Assurance chômage | +1,5 | +1,5 | +1,6 | +1,7 |
| Effets économiques (multiplicateur, éviction) | +0,9 | −1,3 | −0,3 | +0,4 |
| État (fonctionnaires, culture, bourses, justice, carburant) | −0,7 | −0,2 | −0,2 | −0,2 |
| **Total** | **−1,1** | **+0,7** | **+5,5** | **+5,8** |
| en points de PIB | −0,04 | +0,02 | +0,17 | +0,17 |

**Zemmour, avec le plan de Sarah Knafo** (6 novembre 2026, fin d'après-midi) : la suppression de la CSG sur les
revenus du travail (≈ 107 Md€, dont ≈ 101 sur les salaires par OpenFisca, moins ≈ 11 d'impôt sur le revenu en plus),
celle des droits de succession (≈ 21 Md€) et la baisse d'un tiers de l'accise sur les carburants (≈ 12 Md€) ne sont
compensées qu'en partie. Le plan Knafo (budget2027.fr, 24 mesures, « 140 Md€ par an au minimum », une seule source de
chiffrage citée) est repris mesure par mesure (ZEM-KNA-01 à 24), chacune estimée en quatre scénarios. Le plus gros
poste est le non-remplacement de 800 000 départs : 400 000 postes réalisés en prudent (300 000 à 700 000), dont 57 % de
la masse revient en prélèvements perdus, et des emplois en moins le temps que le privé en reprenne une partie.

Économies brutes identifiées en 2037 (toutes les lignes positives, retraites comprises) : 62 Md€ en crise, 79 en
prudent, 104 en médian, 130 en optimiste ; les seules lignes nouvelles du plan Knafo : 15, 22, 33 et 46 Md€.

| Groupe | 2029 | 2032 | 2037 | 2050 |
|---|---|---|---|---|
| Recettes (CSG, successions, carburants ; prélèvements des postes non remplacés) | −133,3 | −144,9 | −153,2 | −167,2 |
| État et défense (non-remplacement, APD, Anah, Ademe, France Travail, audiovisuel, UE…) | +19,5 | +28,5 | +30,3 | +32,5 |
| Retraites (65 ans) | +0,0 | +7,4 | +14,2 | +14,0 |
| Collectivités (non-remplacement) | +3,5 | +9,0 | +9,4 | +10,2 |
| Prestations (préférence nationale, RSA limité à trois ans) | +5,2 | +6,0 | +6,2 | +6,5 |
| Effets économiques (multiplicateur de la baisse d'impôt, emplois privés libérés) | +42,0 | +2,7 | +3,9 | +4,1 |
| Investissement (IA) | −1,1 | −1,1 | −1,2 | −1,3 |
| Santé (40 000 soignants, moins les administratifs non remplacés et les ARS) | −0,2 | −0,4 | −0,4 | −0,5 |
| **Total** | **−63,9** | **−92,1** | **−90,3** | **−101,1** |
| en points de PIB | −2,1 | −3,0 | −2,8 | −2,9 |

Avant le plan Knafo : −3,6 points de PIB en 2037.

**Arthaud (partiel)** : le SMIC à 2 200 € net (+50 % de brut) domine : hausse de coût pour l'État employeur,
allègements étendus jusqu'à 3 nouveaux SMIC, et surtout 1,6 million d'emplois perdus en prudent (0,6 à 2,1 million
selon le scénario), ordre de grandeur seulement (élasticités estimées pour de petites hausses). La défense ramenée au
niveau du PLF 2027 rapporte ≈ 9 Md€.

| Groupe | 2029 | 2032 | 2037 | 2050 |
|---|---|---|---|---|
| Effets économiques (emplois perdus du SMIC, éviction par les postes publics, multiplicateur) | −15,6 | −30,6 | −37,5 | −40,8 |
| Santé (embauches, SMIC à l'hôpital, déremboursements refusés) | −11,9 | −17,4 | −18,2 | −20,6 |
| Prestations (prime d'activité en moins avec le SMIC ; budget 2027 annulé) | +12,9 | +13,2 | +13,8 | +14,8 |
| Recettes (prélèvements et TVA du SMIC, confiscation) | +6,8 | +12,8 | +13,4 | +14,9 |
| Collectivités (SMIC des agents, transports, pompiers) | −9,4 | −11,1 | −11,5 | −12,4 |
| État et défense (éducation, SMIC des agents, défense au PLF 2027) | −6,1 | −9,8 | −10,1 | −10,8 |
| Retraites (pas de sous-indexation en 2027) | −5,5 | −5,7 | −6,0 | −6,3 |
| **Total** | **−28,8** | **−48,5** | **−56,2** | **−61,3** |
| en points de PIB | −1,0 | −1,6 | −1,8 | −1,8 |

### Par scénario, en 2037

| Programme | Scénario | Solde primaire (pts de PIB) | Chômage : programme / statu quo | Emplois (milliers) | Déficit : programme / statu quo | Dette (% du PIB) |
|---|---|---|---|---|---|---|
| Bertrand | crise | +0,1 | 10,4 / 10,3 | −27 | 12,2 / 12,3 | 187 / 186 |
| | prudent | +0,2 | 8,4 / 8,3 | −25 | 9,5 / 9,7 | 164 / 164 |
| | médian | +0,3 | 8,3 / 8,3 | −4 | 8,1 / 8,5 | 152 / 154 |
| | optimiste | +0,5 | 8,2 / 8,3 | +38 | 7,6 / 8,2 | 146 / 149 |
| Zemmour (avec Knafo) | crise | −3,3 | 11,1 / 10,3 | −241 | 17,7 / 12,3 | 220 / 186 |
| | prudent | −2,8 | 8,9 / 8,3 | −195 | 14,1 / 9,7 | 194 / 164 |
| | médian | −2,0 | 8,2 / 8,3 | +27 | 11,5 / 8,5 | 175 / 154 |
| | optimiste | −1,1 | 7,1 / 8,3 | +384 | 9,8 / 8,2 | 162 / 149 |
| Arthaud (partiel) | crise | −2,1 | 17,0 / 10,3 | −2 109 | 16,2 / 12,3 | 212 / 186 |
| | prudent | −1,8 | 13,4 / 8,3 | −1 621 | 12,7 / 9,7 | 185 / 164 |
| | médian | −1,4 | 11,8 / 8,3 | −1 106 | 10,7 / 8,5 | 169 / 154 |
| | optimiste | −1,1 | 10,4 / 8,3 | −643 | 9,9 / 8,2 | 162 / 149 |

Pour comparer : Tondelier, au même code, −2,4 points de PIB de solde primaire en 2037 (prudent).

## Limites connues

1. **Plan Knafo** : moins de France Travail, d'Anah et d'Ademe, de soutien aux renouvelables : aucun effet compté sur le chômage ni sur les émissions dans cette passe. Qualité des services avec 400 000 agents de moins : non modélisée.
2. **Immigration (Zemmour, Arthaud)** : arrêt de l'immigration légale et « remigration » d'un côté, régularisations
   et liberté d'installation de l'autre changent la population active ; le modèle ne le fait pas encore. À construire :
   une variante démographique sur le solde migratoire (l'Insee publie des projections à solde migratoire haut et bas),
   commune à tous les programmes.
3. **Report de l'âge** : comme pour le retour à 62 ans de Tondelier, les taux d'emploi par âge sont figés, donc
   reporter l'âge n'ajoute pas d'emplois de seniors ni de recettes : l'économie est prudente.
4. **Prix** : pas de canal des prix (accise, protectionnisme, carburant à prix coûtant, SMIC).
5. **Arthaud** : chiffrage partiel par construction (expropriation, interdiction des licenciements, réduction du temps
   de travail sans perte de salaire, planification : hors modèle). Le SMIC sort du domaine de validité des
   élasticités.
6. **Sources** : les fiches reprennent la liste de programmes-2027.fr ; les sources primaires (tracts, entretiens)
   n'ont pas été relues une à une. Les montants du budget 2027 (pensions, prestations, déremboursements) viennent de la
   presse (MoneyVox, octobre 2026) : à remplacer par l'étude d'impact du PLFSS.
7. **Pas de programme publié** pour Bertrand (déclaration attendue fin 2026) : à refaire quand il sortira.
