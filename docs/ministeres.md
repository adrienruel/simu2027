# Dépenses des ministères année par année (4 novembre 2026)

Demande d'Adrien : les dépenses des ministères augmentent avec le temps ; indexation laissée au choix le plus
cohérent. `moteur/depenses/ministeres.py`, paramètres `ministeres.*`, tests `tests/test_ministeres.py`.

## Règles

Chaque mission de l'État (et les autres dépenses courantes : collectivités, Sécurité sociale hors santé, concours
aux outre-mer) part de son coût de 2029 dans le nouveau système, puis suit :

| Règle | Missions | Pourquoi |
|---|---|---|
| Croissance × population | sécurité, justice, administration, finances publiques, culture, sport, outre-mer, AME, collectivités, Sécurité sociale hors santé | salaires publics alignés sur ceux du privé (loi de Baumol) ; besoin proportionnel aux habitants |
| Croissance × élèves (3-17 ans, après 2035) | enseignement scolaire | la baisse des élèves d'ici 2035 est déjà dans les mesures (enseignants ajustés) ; après, moyens −0,5 % pour −1 % d'élèves (prudent) |
| Croissance × jeunes de 18-24 ans (moitié) et PIB (moitié) | recherche et enseignement supérieur | universités : étudiants ; recherche : part de la richesse |
| Croissance × enfants | aide sociale à l'enfance | |
| Croissance × personnes en emploi | travail et emploi | |
| PIB | défense, contribution à l'Union européenne, aide au développement, économie, écologie, agriculture | part constante de la richesse produite (programmation militaire, budget européen en part du revenu national) |
| Prix seulement (règle d'indexation) | engagements financiers, monde combattant | montants qui ne suivent pas la croissance |

Avant : tout suivait la croissance et la population totale. Les mesures sur les pensions de l'ancien système (âge de
départ à 67 ans, hautes pensions, réversion) passent du poste « autres » au poste « retraites », et le libellé de la
mesure d'âge est corrigé (64 → 67 ans, quatre trimestres par génération).

## Par ministère (prudent, Md€ de 2026)

| Ministère | 2029 | 2037 | 2050 | 2073 |
|---|---|---|---|---|
| Éducation | 75,9 | 77,5 | 76,5 | 72,9 |
| Armées | 73,6 | 78,0 | 83,7 | 85,8 |
| Contribution à l'UE | 30,4 | 32,1 | 34,5 | 35,4 |
| Recherche et enseignement supérieur | 29,0 | 30,4 | 29,4 | 30,8 |
| Intérieur | 26,7 | 28,3 | 30,5 | 33,4 |
| Justice (avec l'aide sociale à l'enfance) | 24,0 | 23,9 | 25,0 | 25,8 |
| Finances | 15,7 | 16,5 | 17,6 | 18,9 |
| Autres (outre-mer, collectivités, Sécurité sociale hors santé…) | 29,0 | 30,6 | 32,9 | 35,5 |

(Chiffres avant l'élasticité de 0,5 sur les élèves et les étudiants : Éducation et Recherche un peu plus hautes
après 2035.)

## Effet

| Sans règle / publié | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|
| Prudent avant | 4,12 / 3,00 | 5,05 / 3,55 | 5,17 / 3,68 | 137 % |
| Prudent après | 4,04 / 3,00 | 4,91 / 3,40 | 4,53 / 3,04 | 135 % |
| Crise après | 4,97 / 3,07 | 5,80 / 4,27 | 15,29 / 13,77 | 245 % |

Les ministères augmentent (poste « autres » : 368 Md€ en 2029, 406 en 2073 dans le prudent), mais moins
qu'avec l'ancienne règle (433) : moins d'élèves et d'étudiants, et un PIB qui croît moins vite que la tendance quand
le nombre de personnes en emploi baisse.
