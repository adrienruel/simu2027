# Formation supérieure : diplômés en plus par cohorte (phase Q, 20/11/2026)

`moteur/qualifications.py`, paramètres `formation_superieure` (`parametres/commun/economie.yaml`), canal déclaré
`formation_superieure` (`moteur/canaux_declares.py`), coût dans `ProgrammeSimple.mesures_formation`, tests
`tests/test_formation.py`, profils `outils/profils_formation.py`.

Demande d'Adrien (20/11/2026) : intégrer la mesure de Philippe « 100 000 ingénieurs formés par an » (PHI-NUM-03),
ses conséquences, et le cas où l'offre d'ingénieurs dépasse la demande ; faire évoluer les cohortes de travailleurs
pour suivre les profils. Point de départ retenu par Adrien : ≈ 47 000 diplômés par an (IESF : 47 400 en 2024 ;
Philippe écrit « contre 40 000 »).

## Avant
Une dépense forfaitaire de 0,8 à 1,5 Md€ selon le scénario, dont 57 % revenaient en prélèvements, sans aucun effet
sur le PIB ni sur l'emploi.

## Canal commun
Un programme déclare `{filiere, objectif, debut, plein}` dans `<nom>_canaux.formation_superieure`. Tout le reste
est commun. Seule filière codée : `ingenieurs`.

| Étape | Calcul | Paramètres |
|---|---|---|
| Flux | (objectif − 47 400) × part atteinte × montée des places de `debut` à `plein`, décalée de la durée des études | `part_objectif_atteinte` 0,4 / 0,5 / 0,7 / 0,9 ; `delai_diplome` 5 / 4 / 3 / 3 ans |
| Coût | places en plus × coût net d'une année (école − cursus remplacé) × part publique ; prélèvements sur les rémunérations comme une mesure « fp » ; multiplicateur | `cout_net_annee_etudiant` 8 000 / 6 500 / 5 000 / 4 000 € ; `part_publique` 0,9 / 0,8 / 0,7 / 0,6 |
| Entrée retardée | une part des étudiants en plus aurait travaillé : PIB en moins (profil des 18-24 ans) | `part_etudiants_sinon_en_emploi` 0,3 / 0,2 / 0,15 / 0,1 |
| Besoin | postes non pourvus en plus chaque année jusqu'en 2035, puis une part ; une part du besoin non utilisé se reporte | `besoin_annuel` 14 000 / 21 000 / 28 000 / 40 000 (Institut Montaigne : 28 000 en réindustrialisation modérée) ; `besoin_report` 0,25 / 0,5 / 0,75 / 1 ; `besoin_apres` 0,25 / 0,5 / 0,75 / 1 |
| Excédent | au-delà du besoin, une part part à l'étranger, le reste est déclassé et garde une part de l'écart ; à l'optimiste seulement, une part crée sa propre demande | `part_etranger_excedent` 0,4 / 0,3 / 0,25 / 0,2 ; `prime_declasses` 0,15 / 0,25 / 0,4 / 0,5 ; `besoin_suit_offre` 0 / 0 / 0 / 0,25 |
| Cohortes | chaque cohorte vieillit : survie de l'Insee, emploi des ingénieurs (93 % de 30 à 49 ans, profil de la population aux autres âges), 11 % à l'étranger (CGE 2025) | `taux_emploi`, `part_etranger`, `age_diplome` |
| Productivité | en emploi × écart de salaire observé (17 %, IESF) × part causale × salaire relatif du cursus remplacé (1,3) × profil de salaire par âge × PIB par emploi ; au solde par le dividende de productivité du statu quo | `ecart_salaire_observe`, `part_causale` 0,25 / 0,4 / 0,6 / 0,8, `salaire_relatif_contrefactuel` |

Valeurs dans l'ordre crise / prudent / médian / optimiste.

Le statut d'une cohorte (absorbée ou en excédent) est fixé à sa sortie d'école : les déclassés ne rattrapent pas.
Ce n'est pas compté :
- la baisse de l'écart de salaire des ingénieurs déjà en poste quand l'offre monte (modèle de Katz et Murphy). C'est
  un transfert entre salariés et employeurs, sans effet de premier ordre sur le PIB ; il jouerait un peu sur les
  recettes, par la progressivité ;
- les effets d'entraînement sur l'innovation ;
- les techniciens : Montaigne en compte 29 000 de plus par an à former, mais la mesure n'en parle pas.

## Profils des travailleurs
`qualifications.stock_statu_quo` : ingénieurs en activité par âge, calés sur l'IESF (1 000 400 fin 2024). La
répartition par âge vient des flux passés (14 000 en 1985, 38 000 en 2015, 47 400 en 2024), puis le flux du statu
quo reste constant. `outils/profils_formation.py` écrit `sorties/profils_formation.csv` (par année) et
`sorties/profils_formation_ages.csv` (par âge en 2029, 2037, 2050 et 2073).

| Prudent | 2037 | 2050 | 2073 |
|---|---|---|---|
| Ingénieurs en activité, statu quo | 1 175 000 | 1 379 000 | 1 482 000 |
| Part dans l'emploi, statu quo | 3,9 % | 4,7 % | 5,6 % |
| Philippe : en plus sur des postes d'ingénieur | 52 000 | 168 000 | 353 000 |
| Philippe : en plus déclassés | 7 000 | 139 000 | 372 000 |
| Philippe : partis à l'étranger (cumul) | 17 000 | 93 000 | 229 000 |
| Part dans l'emploi, Philippe | 4,1 % | 5,7 % | 8,3 % |

Au prudent, le besoin est saturé vers 2040. Au-delà, plus de la moitié des diplômés en plus sont déclassés ou partis.

## Effets sur Philippe (prudent)
| | 2037 | 2050 |
|---|---|---|
| Coût net (Md€) | 0,58 | 0,64 |
| Prélèvements sur les rémunérations | +0,33 | +0,36 |
| PIB : productivité / entrée retardée (Md€) | +0,5 / −1,4 | +2,7 / −1,5 |
| Écart de solde primaire au statu quo (point de PIB) | −1,015 → −1,013 | −1,696 → −1,687 |

L'effet sur le classement est négligeable : quelques centièmes de point, au plus 0,09 en 2073 à l'optimiste.
Avant 2045, le PIB baisse au prudent, parce que les étudiants en plus retardent leur entrée dans l'emploi. Les
autres programmes ne changent pas (vérifié sur `comparaison_trajectoire.csv`).

## À valider par Adrien
- Besoin au médian : scénario modéré de Montaigne (28 000 par an) ; demande qui suit l'offre réservée à l'optimiste.
- Lecture du calendrier de Philippe : places de 2028 à 2032, diplômés en plus ensuite.
- Hypothèses à sourcer en priorité : part causale, entrée retardée, part publique (part des écoles privées dans les
  diplômes, CDEFI), départs des diplômés en excédent.
