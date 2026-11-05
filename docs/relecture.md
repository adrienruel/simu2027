# Dossier pour une relecture indépendante (29 octobre 2026)

Objet : vérifier que le moteur chiffre honnêtement le programme « Écologie de droite » — ni flatteur, ni
punitif. Le relecteur n'a pas participé au travail. Règle du projet : « un devoir et une volonté de vérité » ;
les hypothèses sans source sont prises prudentes ; le prudent est publié, toujours montré avant et après la
clause de trajectoire.

## Lancer

```
pip install pyyaml pytest openpyxl openfisca-france
python -m pytest                     # 193 tests, ~2 min
python -m moteur.simulation          # déficits des quatre scénarios
python -m outils.tableau_de_bord     # sorties/tableau_de_bord.html
python -m outils.leviers             # variantes (~20 min)
```

## Résultat publié (prudent)

| | 2029 | 2037 | 2050 | 2060 | 2073 |
|---|---|---|---|---|---|
| Déficit avant clause (% du PIB) | 5,35 | 5,06 | 3,85 | 1,31 | −1,71 |
| Déficit publié | 4,94 | 3,04 | 3,91 | 1,34 | −1,71 |
| Dette (% du PIB) | 130 | 129 | 137 | 133 | 98 |

Crise : dette 150 % en 2050, 235 % en 2073 (pas de retour à l'équilibre).

## Ce qu'il faut vérifier en priorité

1. **Les hypothèses qui font le résultat de long terme.** Classement : `sorties/sensibilite.json`,
   `sorties/incertitude.json`, `docs/leviers.md`. Les plus lourdes ajoutées récemment :
   - usure du capital du fonds (4 %) : la retirer porte le déficit 2073 de −1,7 % à +0,7 % et la dette de 98 %
     à 128 % ; est-il juste de compter rendement net + usure comme valeur ajoutée (`moteur/macro.py`, pib_cap) ?
   - prime de taux liée à la dette (3 points de base par point, symétrique) ;
   - effet du programme sur la natalité (−4,6 % de naissances) ;
   - rendement du capital du fonds (3,2 % net) et éviction de l'épargne volontaire (17,5 %).
2. **Les doubles comptes.** Emploi : un seul passage par la courbe de rendements décroissants
   (`docs/bloc_emploi.md`) ; seniors, cumul et inactifs hors chômage. Âge légal à 65 ans : calculé dans
   `moteur/ancien_systeme.py` et retiré du forfait de la v235 (`moteur/mesures.py`). Santé : la trajectoire compte
   déjà le vieillissement, le module de population n'y touche pas.
3. **La clause de trajectoire** (`moteur/macro.py`) ramène le prudent sur le déficit du médian : tout ce qui
   améliore le médian (retombées du fonds, par exemple) rend la clause plus exigeante et améliore le prudent
   publié. Vérifier que le publié n'en devient pas flatteur.
4. **La transition des retraites** : ancien système (générations nées en 1979 ou avant), socle des générations
   de 22 à 49 ans en 2029 (population de l'Insee, arrivées comprises), remboursement de 35 % au départ
   (pic du déficit en 2047-2052).
5. **La concordance OpenFisca** : le nouveau système est codé deux fois (moteur et réforme OpenFisca), tests au
   centime ; le système actuel vient d'OpenFisca-France 176.1.10, législation 2026.

## Limites connues (non traitées)

- Comparaison avec le statu quo : faite le 4 novembre 2026 (docs/statu_quo.md), à confirmer par le test
  « programme vide = statu quo » quand le programme sera branché sur le noyau par des mesures.
- La correspondance fécondité ↔ scénario et la participation des inactifs ne sont pas tirées dans l'incertitude
  (valeurs structurées).
- Taux d'emploi par âge figés à 2025 ; la fin de la montée à 64 ans (réforme de 2023) n'est pas comptée.
- Effets des crèches sur l'emploi des mères et emplois des crèches non comptés (prudent).
- Réaction des naissances chez les parents isolés : fragile ; incitation à déclarer une séparation non chiffrée.
- Hausse conditionnée de la déduction : calculée sur la trajectoire sans la hausse (pas de point fixe).
- 175 paramètres restent des hypothèses sans source (`docs/sourcage.md`).

## Historique

`docs/journal.md` (décisions datées et écarts à la v235), `git log`.


## Relecture du 29 octobre 2026 : résultats et corrections

Relecture faite par un agent indépendant (aucune participation au travail, dépôt en lecture seule). Erreurs
vérifiées, corrigées sous `macro.corrections_relecture` (valeur v235 : non, pour les tests de reproduction) :

1. **Usure du capital taxée comme un revenu** : l'usure du capital du fonds (et de l'investissement des entreprises)
   compte dans le PIB mais pas dans l'assiette des impôts (elle paie le renouvellement du capital).
2. **Contribution de la clause comptée deux fois** : la part de l'épargne versée à l'État par la clause ne va
   plus au fonds. Reste à faire : l'effet sur le socle des générations concernées (moins de capital, plus de socle).
3. **Baisse du RUI de la clause sous le plancher** : marge calculée sur le RUI réel de l'année (non indexé).
4. **Baisse du RUI sans effet récessif** : même multiplicateur et même dissipation que l'effort de 2029.
6. **Recettes des retraités et carbone statique** (erreur pénalisante) : elles ne suivent plus l'emploi
   (indice 1 ; la recette nette des anciennes pensions et le module carbone les règlent déjà).
7. **Emplois perdus par localisation** : retirés en entier, hors de la courbe de rendements décroissants.
8. (petit) Emplois des réformes, seniors et perdus : suivent la population de 18 à 64 ans.

Prudent après corrections : avant clause 5,39 % (2037), 4,40 % (2050), 0,09 % (2073) ; publié 3,63 % (2037),
4,97 % (2038), 4,46 % (2050) ; dette 124 % en 2073. Avant corrections : publié 3,04 % (2037), dette 98 % (2073).

**Point 5 tranché par Adrien** : entre l'âge légal (65 ans) et 67 ans, une personne sans emploi touche le socle
si elle a ses annuités (90 %, hypothèse), le RUI sinon ; appliqué au nouveau système et aux reportés de l'ancien
(`retraites.attente_age_legal_67`). Coût : 6 à 9 Md€ par an de 2030 à 2043 (reportés de l'ancien système),
≈ 15 Md€ de socle anticipé à partir de 2045 (nouveau système).

**Recette carbone recalculée** (demande d'Adrien) : 54,9 Md€ calculés par le moteur (accises carbone de la
ligne 3 et accises brutes des entreprises nettes d'IS) au lieu de 57,7 saisis.

**Erreur trouvée en corrigeant** : la génération née en 1979 (50 ans en 2029) n'était ni dans l'ancien système
(arrêté à 1978) ni dans les cohortes du nouveau (22 à 49 ans). Elle est rattachée à l'ancien système.

Prudent après tout cela : avant clause 5,78 % (2037), 5,85 % (2050), 4,18 % (2073) ; publié 4,03 % (2037),
5,38 % (2038), 5,91 % (2050) ; dette 180 % en 2073. La prime de taux liée à la dette amplifie fortement la fin de
période : sans elle, 0,26 % de déficit et 131 % de dette en 2073.

**Points discutables relevés, non changés** : la clause fait du médian le chiffre publié jusqu'en 2036, puis le
publié saute en 2038 (désormais affiché) ; rendement versé aux épargnants (2,33 %) supérieur au rendement net
d'impôt du capital ; RUI réel sous le RSA de 2026 vers 2050 (règle de non-indexation) ; recette carbone saisie
(57,7 Md€, à recalculer) ; prime de taux symétrique ; permis rapide sans coût ; seniors sur 1,25 an de report.

## Corrections avant l'audit (30 octobre 2026)

Décisions d'Adrien : l'accise de transition (calage de 29 Md€) et le barème de la contribution des retraités actuels
(5 à 10 %, seuil haut 3 000 €) sont gardés, à retirer si de meilleures économies sont trouvées.

Points de la relecture du 29/10 traités :

1. **Seniors sur 1,25 an de report** (`macro.seniors_lies_aux_reportes`) : les emplois de seniors de l'ancien
   système suivent désormais les personnes dont le départ est réellement reporté par l'âge légal à 65 ans,
   génération par génération (0,2 million en 2029, 0,68 en 2037, plus personne après 2050), × 12,75 % en emploi
   dans le prudent (17 % dans la source, Insee 2017). Avant : un forfait de 127 500 emplois, calé sur 1,25 an de
   report et gardé jusqu'en 2073, alors que l'ancien système s'éteint (double compte avec les seniors du socle à
   67 ans à partir de 2043). Chômeurs seniors : même lien (7 pour 17 emplois).
2. **Permis rapide sans coût** (`macro.permis_rapide_separe`, `macro.permis_rapide_cout`) : capital privé suivi à
   part, qui s'use à 10 % par an comme celui des entreprises (2 Md€ d'investissement en plus par an font un stock
   d'environ 20 Md€, au lieu de 90 Md€ en 2073 sans usure), coût des services instructeurs 0,1 Md€ par an
   (hypothèse sans source). Avant : ajouté au capital du fonds, ce qui gonflait aussi la part des comptes placée
   en capital nouveau.
3. **Rendement versé aux épargnants** : 1,76 % au lieu de 2,33 % (calculé : rendement net du capital du prudent,
   3,2 %, × (1 − 45 % d'impôt sur les bénéfices)). Les comptes ne peuvent pas rapporter plus que le capital qui
   les porte. Frais de gestion non comptés (à ajouter).

Point vérifié, pas d'incohérence : le RUI versé à 89 % des 65-66 ans alors que le bloc emploi compte des seniors en
emploi. Le coût est compté pour toute la tranche d'âge, et le RUI économisé par les seniors qui travaillent est
crédité dans le gain de chaque emploi (moteur/emploi_canaux.gain_au_cout) : rien n'est compté deux fois.

| Sans règle / publié | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|
| Prudent avant | 4,28 / 3,00 | 3,66 / 3,00 | −1,64 / −1,64 | 85 % |
| Prudent après | 4,34 / 3,00 | 3,83 / 3,00 | −0,84 / −0,84 | 95 % |
| Crise avant | 4,95 / 3,25 | 4,28 / 3,21 | 5,16 / 4,04 | 152 % |
| Crise après | 4,96 / 3,26 | 4,37 / 3,29 | 5,71 / 4,58 | 155 % |

Effet de chaque correction seule sur le prudent de 2073 : seniors +0,35 point, permis +0,10, rendement +0,42.

## Relecture indépendante du 5 novembre 2026

Agent sans historique du projet ; consigne : chercher les erreurs, lire les relectures précédentes seulement à la fin.
Statut de chaque constat après vérification dans le code.

| Constat | Gravité | Statut |
|---|---|---|
| C1. Prime de dette sans borne (statu quo à 14 000 % de dette/PIB ; taux réels négatifs des programmes qui se désendettent ; cumul avec `baisse_spread`) | critique | **corrigé** (bornes, référence commune, dette négative à zéro, baisse totale ≤ écart au Bund) |
| C2. Programme chiffré à la croissance du prudent ; surplus de PIB des scénarios au solde par `part_pib_tendanciel_au_solde = 0,1` sans source (+1,6 point de déficit médian en 2050 si q = 0) | critique | **ouvert** : refonte (postes du programme aux salaires et au PIB de chaque scénario) |
| C3. Architecture : économies saisies en Md€ par le programme, effets de comportement dans son dossier, pas de bloc macro commun | critique | **ouvert** : plan dans `docs/architecture.md` à écrire |
| I1. Hausse de la défense 2026-2027 comptée deux fois | important | **corrigé** |
| I2. Santé indexée sur le salaire par tête (la pente est une part du PIB) : +64 Md€ en 2073 | important | **à trancher** (décision : trajectoire de santé gardée) |
| I3. Crise du statu quo meilleure que le prudent jusqu'en 2045 ; `elasticite_invest` non monotone | important | **à trancher** (définition de la crise) |
| I4. Dénominateur de la prime choisi par le programme (`pib_prime`) | important | **corrigé** (avec C1) |
| I5. Fonds hors APU : flux non bouclés (~63 Md€ d'investissement hors budget) | important | ouvert (décision : hors APU ; compte du fonds à ajouter) |
| I6. Artefact de méthode santé médian (−14 Md€ en 2073) ; IA retirée des recettes mais pas des blocs remplacés | important | ouvert |
| I7. Économies sans taux de réalisation ni contrôle de recouvrement (IA, effectifs, Bercy) | important | ouvert (lié à C3) |
| I8. Unités contournables (`sans_unite` pour des Md€) ; 187 paramètres sur 482 sans source | important | ouvert |
| I9. Taux d'emploi par âge figés ; 15-24 ans appliqué aux 18-24 ans (~0,6 million d'emplois) | important | ouvert |
| Textes périmés (README, 65 ans, prestations « sur les prix »), test mal ciblé, TVA des transferts, code mort | mineur | **corrigé** |
| Constantes en dur (PIB 2024, 900 000 retraités à l'étranger…), clé `charge_dette` ambiguë, exception avalée dans `outils/openfisca_menages.py` | mineur | ouvert |
