# Incertitude chiffrée (phase D de la roadmap)

14 novembre 2026. Module : `moteur/incertitude.py` ; table du comparateur : `outils/export_incertitude.py` →
`sorties/comparaison_incertitude.csv`.

## Méthode

**Loi de chaque hypothèse (D1).** Toute hypothèse dont la valeur change d'un scénario à l'autre (paramètre ventilé
par scénario, ou sous-champ structuré dont les clés sont des scénarios : montants des mesures, jeux d'emploi…) reçoit
une loi dont le **prudent est le 10e centile, le médian la médiane et l'optimiste le 90e centile**. Entre ces points,
la valeur suit une loi normale de pente différente de chaque côté ; au-delà, la pente continue, bornée par la valeur de
crise (ou, sans crise plus défavorable, un pas de plus que le prudent) et par un pas de plus que l'optimiste. Les
années sont exclues. Sans prudent écrit (jeux d'emploi), le prudent est le milieu de la crise et du médian, comme dans
le moteur. Les sources des valeurs centrales et des bornes sont celles des scénarios (phase C).

**Corrélation.** z = √ρ Z + √(1 − ρ) ε : Z est commun au tirage (le « climat » : productivité, comportements,
multiplicateurs ont tendance à être bons ou mauvais ensemble), ε propre à l'hypothèse. ρ = 0,5 par défaut
(`incertitude.correlation`, hypothèse) ; ρ = 1 redonne les scénarios, ρ = 0 suppose l'indépendance, qui rend presque
impossibles les cas où tout va bien ou tout va mal.

**Tirages communs (D2).** Le z d'une hypothèse ne dépend que de la graine, du numéro du tirage et de son nom : une
hypothèse commune est tirée au même point pour tous les programmes, et les écarts entre programmes se lisent tirage
par tirage. Chaque tirage remplace la colonne médiane et se calcule dans le scénario médian, règle de trajectoire
comprise. La colonne prudente reste celle du scénario prudent : le moteur la lit pour les effets en sens inverse
(scénario miroir), comme dans le scénario médian publié ; ces effets ne sont donc pas tirés.

**Contrôle.** Avec ρ = 1 et tous les z au 10e centile, le tirage retrouve le scénario prudent à quelques dixièmes
près : statu quo 2037 9,47 contre 9,50 % ; Écologie de droite 4,00 contre 4,15 ; Retailleau 10,31 contre 10,46 ;
Tondelier 13,36 contre 13,98 ; Mélenchon 28,66 contre 29,63. L'écart vient des règles propres au scénario prudent
(effets en sens inverse lus dans le médian, moyennes de jeux) : le prudent publié est un peu plus prudent que le
10e centile de la loi.

## Résultats

Voir la section suivante, écrite à partir de `sorties/incertitude.json`.
