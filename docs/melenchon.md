# Programme Mélenchon (La France insoumise) sur le noyau (6 novembre 2026)

`programmes/melenchon/` : `mesures.yaml` (fiche de 215 mesures à portée budgétaire ou économique, citations vérifiées
page par page), `parametres.yaml` (chiffrage de chaque mesure : montant par scénario, assiette, montée, source),
`programme.py`. `python -m moteur.noyau melenchon` imprime le bilan ; `python -m outils.export_comparaison` l'ajoute au
comparateur ; `python -m pytest tests/test_melenchon.py`.

Source : « L'Avenir en commun. Le programme de la Nouvelle France », 5e édition (La Dispute, novembre 2026, 224 p.),
lu en entier. Le site communautaire laec.fr n'a pas servi : il bloque la lecture automatique et reprend l'édition de
2021. **Le livre ne chiffre rien** : ni coût, ni recette, ni solde. Les seuls montants sont des paramètres de mesure
(SMIC à 1 700 € net, seuil de pauvreté de 1 337 €, point d'indice +10 %, APL +10 %, 3 Md€ pour les violences sexistes
et sexuelles, 1 Md€ contre le racisme, 0,7 % du RNB pour l'aide au développement, 1 % du PIB pour la culture, 200 000
logements publics et 700 000 isolations par an, 10 000 places d'Ehpad par an, 500 000 places en crèche, héritage
maximal de 12 M€). Les « plans thématiques » annoncés ne sont pas encore parus : à relire quand ils sortiront.

## Méthode

- **Mesures simples** (comme les petits programmes, `moteur/programme_simple.py`) : montant à l'économie de 2029 en
  Md€ de 2026, montée linéaire, puis l'assiette (PIB, pensions, impôt ou bloc du statu quo). Une rémunération publique
  rend 57 % en prélèvements ; les postes publics créés ont l'éviction commune.
- **Mesures calculées** :
  - SMIC à 1 700 € net dès juillet 2027 (`bibliotheque.smic`, allègements qui suivent le SMIC comme dans la loi) ;
  - point d'indice +10 % dès juillet 2027 (55 % du coût des agents), réparti entre les versants ;
  - retraite : 62 ans pour les départs de 2028, puis six mois de moins par an jusqu'à 60 ans en 2032, nouvelle brique
    `bibliotheque.baisse_age_legal_detail` (calendrier de profils de départ, même calcul et même calage que le statu
    quo ; elle retrouve à l'euro près le retour à 62 ans de Tondelier) ; prélèvements sur les pensions ; emploi des
    seniors (`offre.seniors`) ;
  - chômage plus élevé quand les réformes de l'assurance chômage sont annulées (Banque de France, comme Tondelier) ;
  - sixième semaine de congés payés et 4 février férié : coût horaire du privé +2,7 %, emplois perdus ;
  - garantie d'emploi et emploi spécifique jeune : emplois créés avec leur propre éviction (15 % et 40 % en prudent),
    pas celle des postes publics (100 %).
- **Nationalisations** (Engie, ArcelorMittal France, ArianeGroup, autoroutes, aéroports, FDJ, Ehpad privés lucratifs,
  GE Vernova) : ≈ 90 Md€ de dette hors solde de 2029 à 2031 (poste participations), et leurs revenus.
- **Règle** : aucune recette ni économie annoncée (il n'y en a pas) ; les lignes déclaratives (niches, fraude) sont
  estimées en quatre scénarios ; défense : loi de programmation du statu quo.

## Arbitrages pris par Claude (le livre ne règle pas), à revoir

| Point | Lecture retenue | Autre lecture |
|---|---|---|
| Garantie d'autonomie (« le revenu mensuel de chaque personne atteindra le seuil de pauvreté ») | niveau de vie du ménage porté au seuil (définition de l'Insee) : 28 Md€ en prudent, plus 10 pour les jeunes détachés du foyer fiscal | seuil appliqué à chaque personne (« individualisation des droits ») : plusieurs fois plus cher |
| Retraite à 60 ans | 62 ans en 2028, 60 ans en 2032 ; 65 % d'une génération partie à 60 ans (pas de décote) | 60 ans dès 2028 |
| 40 annuités et décote supprimée | +3 % des pensions des nouveaux retraités en prudent (12,8 Md€ à terme) | de +1 à +4 % selon la durée des carrières |
| Pensions des carrières complètes « au niveau du SMIC revalorisé » | SMIC de 1 700 € net, 22 Md€ en prudent | SMIC actuel : environ moitié moins |
| AAH « à hauteur du SMIC » | SMIC de 1 700 € net, 11,5 Md€ | SMIC actuel : ≈ 6 Md€ |
| Arrêts maladie à 100 % | la Sécurité sociale complète là où l'employeur ne le fait pas : 6,5 Md€ | elle paie tout le salaire : ≈ 17 Md€ |
| 14 tranches d'impôt sur le revenu | hausse au-delà de 100 000 € par part (+2), baisse en bas (−4,5) | barème de 2022 de L'Avenir en commun |
| Crédit d'impôt par enfant | à la place du quotient familial, presque à budget constant | en plus du quotient familial (≈ 10 Md€) |
| Successions (héritage maximal de 12 M€, exonération sous 150 000 €) | −1 Md€ en prudent (l'exonération coûte plus que le plafond ne rapporte), +4 en optimiste | — |
| Classes « mieux que 19 élèves » | 19 en primaire et en éducation prioritaire, −2 élèves ailleurs | 19 partout : plusieurs Md€ de plus |
| Culture à 1 % du PIB | base de 0,7 % (État, audiovisuel, collectivités) : +9 Md€ | base du seul ministère : ≈ 25 Md€ |
| Recherche | CIR supprimé (+7 Md€) rendu en dotations (+7,6) plus 1,5 | — |
| Taxe d'habitation rétablie | recette des communes (6 Md€) dépensée par elles : effet net nul | recette gardée au solde |
| Conscription de neuf mois au SMIC | classe d'âge entière (800 000), 23 Md€ brut, 57 % rendus en prélèvements | — |
| Recrutements à l'hôpital (aucun chiffre) | 100 000 en cinq ans, comme en 2022 | — |
| Plan d'investissement, adaptation (aucun chiffre) | adaptation 6 Md€ par an en 2032 ; industrie 3,5 | — |
| Dette détenue par la BCE annulée, circuit du Trésor | hors scénario (accord de l'Union nécessaire) | variante à construire |
| Défense (« rejeter les 5 % ») | loi de programmation du statu quo | — |

## Résultats (6 novembre 2026)

*Chiffres du 6 novembre, avant le multiplicateur en miroir du 7 novembre (voir Sensibilités) : déficit 2037 désormais 28,4 % en prudent, 37,6 en crise, 22,0 en médian, 17,8 en optimiste.*

Effet des mesures sur le solde, contre le statu quo (prudent, Md€ de 2026 ; − = dégrade) :

| Prudent | 2029 | 2032 | 2037 | 2050 |
|---|---|---|---|---|
| Recettes (impôts nouveaux, prélèvements sur les hausses de salaire et les pensions) | +67,9 | +108,7 | +112,7 | +121,8 |
| Retraites (60 ans, 40 annuités, minimum au SMIC, ASPA, fonctionnaires) | −58,2 | −89,5 | −93,0 | −109,2 |
| Prestations (garantie d'autonomie, AAH, chômage, congé d'accueil, APL) | −63,1 | −71,1 | −75,8 | −80,0 |
| Santé et grand âge (100 % Sécu, arrêts maladie, hôpital, Ehpad) | −52,1 | −76,6 | −80,8 | −93,6 |
| État (point d'indice, éducation, recherche, conscription, justice, police) | −37,4 | −74,0 | −77,0 | −83,0 |
| Investissement (rénovation, logement public, adaptation, ferroviaire) | −20,0 | −35,5 | −35,3 | −36,6 |
| Collectivités, culture, emplois aidés, autres dépenses | −53,5 | −78,9 | −82,1 | −88,3 |
| Défense et aide au développement | −5,4 | −11,0 | −11,4 | −12,3 |
| Effets économiques (multiplicateur, offre, emplois, seniors) | +78,0 | +26,6 | −33,5 | −41,0 |
| **Total** | **−143,8** | **−301,3** | **−376,4** | **−422,2** |
| en points de PIB | −4,7 | −9,7 | −11,6 | −12,2 |

Les recettes comprennent ≈ 60 Md€ de prélèvements qui reviennent sur les hausses de rémunérations publiques et de
pensions ; les impôts nouveaux eux-mêmes font ≈ 45 Md€ en prudent (≈ 1,5 point de PIB) (quotient conjugal, CIR, nouvel impôt des
éco-régions, taxe d'habitation, Zucman, ISF…). Dépenses nouvelles brutes en 2032 : ≈ 440 Md€ (≈ 14 % du PIB ;
Institut Montaigne, 2022 : 332 Md€ pour le programme de 2022).

| Scénario | Solde primaire 2037 (points de PIB, contre le statu quo) | Déficit 2032 / 2037 (programme / statu quo) | Dette 2037 | Chômage 2037 |
|---|---|---|---|---|
| Crise | −14,4 | 19,5 / 8,6 % ; 35,0 / 12,3 % | 317 / 186 % | 12,4 / 10,3 % |
| Prudent | −11,9 | 17,8 / 7,3 % ; 28,1 / 9,7 % | 273 / 164 % | 9,0 / 8,3 % |
| Médian | −9,5 | 15,7 / 7,0 % ; 22,1 / 8,5 % | 237 / 154 % | 7,6 / 8,3 % |
| Optimiste | −7,4 | 14,8 / 6,8 % ; 18,9 / 8,2 % | 218 / 149 % | 6,5 / 8,3 % |

Mesures de 2027-2028 (SMIC, point d'indice, APL, montée de la retraite) : 69 Md€ de dette en plus à fin 2028.
Emploi en 2032 (prudent) : SMIC −355 000, seniors −530 000 (départs à 60 ans), sixième semaine −160 000, assurance
chômage −190 000 (chômeurs), garantie d'emploi et emploi jeune +390 000 (−100 000 d'éviction), conjoncture +490 000
(l'impulsion budgétaire, qui s'efface ensuite). Le chômage baisse d'abord (7,5 % en 2032 contre 8,4 %), puis remonte
au-dessus du statu quo.

Lecture : l'écart vient d'abord de la taille du programme (≈ 14 points de PIB de dépenses nouvelles pour ≈ 1,5 point
d'impôts nouveaux), pas des hypothèses de comportement ; même l'optimiste creuse le déficit de plus de 10 points en
2037. Le déficit s'écarte ensuite plus que le solde primaire : les intérêts de la dette en plus s'accumulent (prime de
risque bornée du modèle). Comme pour les autres, il faut lire l'écart au statu quo, qui diverge lui-même.

## Limites connues

1. **Garantie d'autonomie** : chiffrée sur l'écart de pauvreté de l'Insee, pas par microsimulation ; premier poste à
   passer dans OpenFisca (avec les jeunes détachés, l'AAH et le minimum de pension au SMIC).
2. **Retraite à 60 ans** : les départs plus tôt ont des pensions plus faibles (carrières plus courtes) : le calcul de
   l'âge ne le compte pas, la ligne des 40 annuités en retire une partie (+3 % au lieu de +5 %).
3. **Prix** : SMIC à +16 %, blocage des prix, tarifs de l'énergie au coût, indexation des salaires : pas de canal des
   prix ; les effets sur l'inflation et les taux ne sont pas comptés.
4. **Non chiffré** : sortie du nucléaire à 60 ans et arrêt de l'EPR2 (EDF hors administrations, à faire dans le module
   écologie comme pour Tondelier), annulation de la dette détenue par la BCE, circuit du Trésor, désobéissance
   européenne, protectionnisme (droits de douane, réaction des partenaires), quotas de contrats précaires, interdiction
   des licenciements boursiers, indépendance de la Kanaky-Nouvelle-Calédonie, plafond de 5 logements transmissibles,
   32 heures dans le privé par la négociation.
5. **Empreinte** : le réemploi, la relocalisation et les droits de douane écologiques réduisent surtout les émissions
   importées : non comptés.

## Écologie : émissions évitées (7 novembre 2026)

Groupe `melenchon_ecologie` (treize mesures, même méthode et mêmes sources que Tondelier, `docs/ecologie.md`) :
isolation de 700 000 logements par an, chauffages au fioul et au gaz remplacés, ferroviaire, transports publics,
leasing social, vélo, lignes aériennes intérieures supprimées quand le train fait moins de quatre heures, fin des
subventions aux énergies fossiles, bifurcation agroécologique, chaleur renouvelable, réemploi, bâtiments scolaires ;
en sens inverse, le gaz de secours si les renouvelables ne suivent pas la fermeture des réacteurs à 60 ans.

| Émissions territoriales (Mt CO2e) | 2032 | 2037 | 2050 |
|---|---|---|---|
| Statu quo (prudent) | 315,5 | 287,7 | 221,4 |
| Mélenchon, prudent : effet des mesures | −5,7 | −8,6 | −8,2 |
| Mélenchon, médian : effet des mesures | −10,9 | −17,0 | −17,1 |
| Tondelier, prudent / médian (rappel) | −7,5 / −13,7 | −8,3 / −17,6 | −5,2 / −16,4 |

Les deux programmes sont du même ordre : Mélenchon gagne plus tard (agriculture et rail plus dotés, sortie du
nucléaire plus lente), Tondelier plus tôt (rénovations complètes, sortie du fioul datée). Aucun n'approche l'objectif
de −65 % en 2033 (≈ 190 Mt) avec les mesures chiffrables : il manque des mesures datées sur les voitures, les
chaudières au gaz et le cheptel.

## Sensibilités (7 novembre 2026)

Effet sur le solde primaire de 2037, contre le statu quo (points de PIB) :

| Variante | Prudent | Autres |
|---|---|---|
| Référence | −11,9 | crise −14,4 ; médian −9,5 ; optimiste −7,4 |
| Lectures les moins chères (culture +6, AAH et pensions au SMIC actuel, arrêts maladie 4,5) | −11,2 | médian −8,9 ; optimiste −6,9 |
| Garantie d'autonomie par personne (coût doublé, hypothèse) | −12,9 | |
| Culture sur la base du seul ministère (+25 Md€) | −12,5 | |
| Arrêts maladie entièrement payés par la Sécurité sociale | −12,3 | |
| Éviction des postes publics à 0,5 au lieu de 1 | −11,8 | chômage 2037 : 8,3 % au lieu de 9,0 |
| Effet de la demande sur 8 ans au lieu de 4,5 | −11,4 | chômage 2032 : 6,3 % au lieu de 7,5 |
| Multiplicateur en miroir pour une relance (appliqué depuis, voir ci-dessous) | −12,0 | crise −14,5 ; optimiste −7,3 |

Les lectures ambiguës et les hypothèses communes bougent le solde de 2037 d'un point au plus sur douze : le résultat
tient à la taille du programme. Elles comptent davantage pour le chômage (de 6,3 à 9 % selon la persistance de la
relance et l'éviction).

**Multiplicateur en miroir pour une relance** (incohérence trouvée, corrigée le 07/11/2026 avec l'accord d'Adrien,
pour tous les programmes : `programme_simple.multiplicateur`, repris par Tondelier) : le multiplicateur et sa durée
ne passaient pas au scénario miroir quand l'impulsion est une relance, alors que l'éviction et le canal d'offre le
font. L'optimiste gardait 0,5 (valeur choisie pour qu'un ajustement budgétaire coûte peu) et donnait donc moins de
relance à un programme qui dépense ou baisse les impôts. Désormais, chaque impulsion annuelle prend son scénario si
c'est un resserrement, le scénario miroir si c'est une relance. Écologie de droite (moteur propre, ajustement) ne
change pas.

| Déficit (% du PIB), avant → après | 2029 | 2032 | 2037 |
|---|---|---|---|
| Mélenchon, crise | 9,7 → 13,4 | 19,5 → 24,3 | 35,0 → 37,6 |
| Mélenchon, prudent | 10,2 → 10,3 | 17,8 → 18,4 | 28,1 → 28,4 |
| Mélenchon, optimiste | 9,4 → 7,1 | 14,8 → 12,1 | 18,9 → 17,8 |
| Tondelier, crise / optimiste (2032) | | 11,6 → 12,9 / 7,2 → 6,5 | |
| Arthaud, crise / optimiste (2032) | | 10,8 → 11,4 / 8,1 → 7,9 | |
| Zemmour, crise / optimiste (2032) | | 12,2 → 12,5 / 6,9 → 6,8 | |

Prudent et médian bougent peu (même multiplicateur de 1 ; seule la durée change, et seulement les années où
l'impulsion change de sens). Bertrand : inchangé en prudent et médian. Chômage de Mélenchon en optimiste : 5,4 % en
2032 au lieu de 6,4 %.

**Piste écartée** : un effet durable des crèches sur l'emploi des mères. L'Insee (P. Pora, Insee Analyses n° 55,
2020) ne trouve pas d'effet significatif d'une place en plus sur l'emploi salarié des mères (−1,7 point, intervalle
de −8,7 à +5,3) : rien à ajouter au modèle.
