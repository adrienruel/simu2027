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

## Résultats (1 000 tirages, ρ = 0,5 ; variantes ρ = 0 et ρ = 1 sur 200 tirages)

Déficit en % du PIB, centiles 10 – 50 – 90 des tirages (règle de trajectoire comprise), et probabilité que le
déficit du programme soit sous celui du statu quo dans le même tirage (entre parenthèses : ρ = 0 / ρ = 1).

| Programme | Déficit 2037 | Déficit 2050 | Mieux que le statu quo en 2037 |
|---|---|---|---|
| Écologie de droite | 1,8 – 2,5 – 3,7 | -0,2 – 1,7 – 3,6 | 100 % (100 % / 100 %) |
| Bertrand (Nous France) | 6,8 – 7,7 – 8,8 | 9,5 – 12,1 – 17,1 | 100 % (100 % / 98 %) |
| Retailleau (Les Républicains) | 6,6 – 8,1 – 9,7 | 9,0 – 12,9 – 19,9 | 70 % (98 % / 62 %) |
| Statu quo | 7,9 – 8,4 – 9,2 | 11,5 – 13,5 – 18,1 | — (— / —) |
| Philippe (Horizons) | 6,9 – 8,5 – 10,2 | 9,7 – 14,1 – 22,1 | 49 % (34 % / 48 %) |
| Attal (Renaissance) | 7,2 – 8,9 – 10,7 | 9,8 – 14,5 – 22,2 | 30 % (6 % / 40 %) |
| Tondelier (Les Écologistes) | 8,7 – 10,4 – 12,4 | 13,6 – 18,8 – 27,8 | 1 % (0 % / 5 %) |
| Zemmour (Reconquête) | 8,6 – 10,6 – 12,9 | 12,7 – 19,4 – 30,1 | 3 % (0 % / 10 %) |
| Lisnard (Nouvelle Énergie) | 8,9 – 11,1 – 13,4 | 13,0 – 20,3 – 31,5 | 2 % (0 % / 8 %) |
| Le Pen (Rassemblement national) — partiel | 9,8 – 11,1 – 12,7 | 15,4 – 20,4 – 28,8 | 0 % (0 % / 0 %) |
| Glucksmann (Place publique) | 10,7 – 11,9 – 13,6 | 17,1 – 22,1 – 30,1 | 0 % (0 % / 0 %) |
| Arthaud (Lutte ouvrière) — partiel | 11,6 – 13,7 – 16,4 | 19,7 – 27,5 – 38,2 | 0 % (0 % / 0 %) |
| Mélenchon (La France insoumise) | 18,9 – 22,2 – 26,6 | 39,1 – 50,1 – 62,7 | 0 % (0 % / 0 %) |
| Roussel (Parti communiste français) | 19,2 – 23,1 – 27,8 | 47,3 – 61,1 – 74,7 | 0 % (0 % / 0 %) |

Lecture :
- les écarts entre programmes sont plus grands que l'incertitude pour la plupart d'entre eux : Écologie de droite
  et Bertrand font mieux que le statu quo dans presque tous les tirages ; Arthaud, Glucksmann, Le Pen, Mélenchon et
  Roussel dans aucun ; Tondelier, Lisnard et Zemmour presque jamais ;
- Retailleau, Philippe et Attal sont proches du statu quo : leur classement dépend des hypothèses (Retailleau mieux
  dans 70 % des tirages, Philippe dans la moitié, Attal dans un tiers) ;
- l'intervalle s'élargit fortement avec le temps (la dette et la prime de taux amplifient les écarts) ;
- la corrélation pèse : à ρ = 0 les intervalles sont deux à trois fois plus étroits et les probabilités plus
  tranchées (Retailleau 98 %, Attal 6 %) ; à ρ = 1 ils redonnent à peu près l'écart entre l'optimiste et le prudent.

## Sensibilité (D3) : ce qui fait le déficit de 2037

Corrélation de rang entre la part propre du tirage de chaque hypothèse et le déficit de 2037 (signe négatif : la valeur
favorable baisse le déficit) ; le « climat commun » est la part commune des tirages. Les dix premières de chaque
programme sont dans `sorties/incertitude.json` et dans la table du comparateur (cinq premières).

- Statu quo : `macro.ia_productivite` (-0,50), `macro.tendance` (-0,22), `macro.prime_dette` (-0,18), `inflation.long_terme` (+0,09), `offre.recherche/rendement` (+0,08) ; climat commun -0,80
- Écologie de droite : `offre.elasticite_cout_travail` (-0,26), `macro.baisse_spread` (-0,13), `macro.ia_productivite` (-0,13), `offre.recherche/rendement` (+0,09), `macro.semi_elasticite_transfert` (-0,09) ; climat commun -0,92
- Tondelier (Les Écologistes) : `macro.ia_productivite` (-0,23), `macro.prime_dette` (-0,12), `macro.tendance` (-0,11), `offre.recherche/rendement` (+0,10), `tondelier_mesures.superprofits/montant` (+0,10) ; climat commun -0,96
- Mélenchon (La France insoumise) : `macro.prime_dette` (-0,19), `macro.ia_productivite` (-0,15), `offre.recherche/rendement` (+0,09), `melenchon_mesures.gratuite_ecole/montant` (-0,08), `melenchon_mesures.nationalisations/montant` (+0,08) ; climat commun -0,97
- Retailleau (Les Républicains) : `macro.ia_productivite` (-0,26), `macro.prime_dette` (-0,13), `macro.tendance` (-0,12), `offre.recherche/rendement` (+0,10), `retailleau_ecologie.dpe/effet_mt` (+0,07) ; climat commun -0,95

Au-delà du climat commun, qui domine partout (−0,8 à −0,97 : productivité, multiplicateurs et comportements ensemble),
les hypothèses qui comptent le plus sont l'apport de l'IA à la productivité, la tendance de productivité et la prime de
risque sur la dette pour tous ; l'élasticité de l'emploi au coût du travail pour Écologie de droite.

À vérifier : le rendement de la recherche publique (`offre.recherche/rendement`) va partout dans le mauvais sens
(+0,08 à +0,10), y compris pour le statu quo, qui n'a pas de mesure de recherche. C'est probablement le hasard : l'écart
type d'une corrélation sur 1 000 tirages est ≈ 0,03, et ce sont les mêmes tirages pour tous les programmes (un seul
écart de 2,5 écarts types, répété). À confirmer avec une autre graine. Les corrélations sous 0,1 sont à lire avec cette
réserve.

## Limites

- Les bornes sont celles des scénarios : la loi ne dit rien de plus que les sources qui les fondent (phase C).
- La valeur de ρ est une hypothèse ; les variantes ρ = 0 et ρ = 1 sont publiées à côté.
- Les effets en sens inverse (scénario miroir) restent à leur valeur prudente dans chaque tirage.
- Calcul : ≈ 6 s par tirage pour les quatorze trajectoires sur deux processus (1 000 tirages ≈ 1 h 40) ;
  les tirages sont écrits au fil de l'eau (`sorties/incertitude_tirages_*.jsonl`) et le calcul reprend après une
  interruption.
