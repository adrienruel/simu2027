# Leviers pour améliorer les comptes (29 octobre 2026)

`python -m outils.leviers` (résultats dans `sorties/leviers.json`). Chaque ligne : le programme actuel avec un
seul changement. Prudent, déficit avant clause en % du PIB (écart au programme entre parenthèses), déficit
publié 2037, dette 2073, effet du programme sur les naissances. Rien n'est adopté : ce sont des pistes.

| Variante | 2037 | 2050 | 2073 | Publié 2037 | Dette 2073 | Naissances |
|---|---|---|---|---|---|---|
| **Programme actuel** | 6,03 | 4,75 | 0,62 | 4,10 | 132 % | −4,6 % |
| Famille : 2e enfant à 25 % du RUI | +0,17 | +0,24 | −0,02 | 4,26 | 136 % | −1,9 % |
| Famille : crèches +20 points (au lieu de +10) | +0,14 | +0,21 | +0,14 | 4,24 | 137 % | −3,2 % |
| Famille : parent isolé à 50 % | +0,25 | +0,35 | −0,01 | 4,34 | 137 % | −0,8 % |
| Retraites : socle à 1 200 € (au lieu de 1 300) | −0,05 | −0,13 | −0,54 | 4,06 | 125 % | |
| Retraites : socle annulé à 2 000 € de rente (au lieu de 2 500) | −0,04 | −0,11 | −0,47 | 4,06 | 126 % | |
| Retraites : accès au socle à 68 ans | 0,00 | −0,08 | −0,28 | 4,10 | 126 % | |
| Retraites : âge légal de l'ancien système à 66 ans | −0,45 | −0,12 | −0,25 | 3,68 | 126 % | |
| Entreprises : déduction de l'investissement à 50 % | −0,69 | −0,50 | −0,79 | 3,44 | 114 % | |
| Emploi : baisse du coût employeur de 2,5 % (au lieu de 5 %) | −0,15 | −0,22 | −0,45 | 3,96 | 124 % | |
| Emploi : sans la baisse du coût employeur | −0,30 | −0,45 | −0,92 | 3,81 | 116 % | |
| RUI à 750 € | −0,21 | −0,24 | −0,21 | 3,92 | 126 % | −5,6 % |
| Épargne obligatoire : 1 point sur 10 versé à l'État | −0,28 | −0,36 | −0,44 | 3,84 | 121 % | |
| **Paquet A** : déduction 50 %, coût employeur −2,5 %, âge légal 66 ans | −1,28 | −0,86 | −1,50 | 2,88 | 99 % | |
| **Paquet B** : A + socle 1 200 € + 1 point d'épargne | −1,61 | −1,36 | −2,51 | 2,58 | 80 % | |
| **Paquet B + famille** (2e enfant à 25 %, crèches +20 points) | −1,29 | −0,91 | −2,33 | 2,89 | 89 % | −0,5 % |

Les effets ne s'additionnent pas exactement (interactions, clause).

## Défaut corrigé

La part de l'épargne obligatoire versée à l'État (`epargne.contribution_transition`) baissait l'épargne et le capital
du fonds sans être comptée en recette (elle ne l'était que par la clause de trajectoire). Elle est désormais une
ligne de recettes de la trajectoire.
