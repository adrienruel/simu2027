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

- Pas de comparaison avec le statu quo (système actuel projeté avec la même démographie) : le chiffre seul
  ne dit pas si le programme fait mieux ou moins bien que de ne rien faire.
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
