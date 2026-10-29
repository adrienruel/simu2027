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
4. **La transition des retraites** : ancien système (générations nées en 1978 ou avant), socle des générations
   de 22 à 50 ans en 2029 (population de l'Insee, arrivées comprises), remboursement de 35 % au départ
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
