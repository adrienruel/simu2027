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
multiplicateurs ont tendance à être bons ou mauvais ensemble), ε propre à l'hypothèse. Faute de source, on publie la fourchette entre ρ = 0
(indépendance, qui rend presque impossibles les cas où tout va bien ou tout va mal) et ρ = 1 (tout ensemble, qui
redonne les scénarios) : `incertitude.correlation`, décision du 14/11/2026.

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

## Résultats (600 tirages communs, fourchette entre les deux bornes de la corrélation)

Décision d'Adrien (14/11/2026) : la corrélation entre hypothèses n'a pas de source ; on publie la fourchette entre
ρ = 0 (hypothèses indépendantes) et ρ = 1 (toutes ensemble), sans valeur centrale. Déficit en % du PIB, règle de
trajectoire comprise ; « 8 sur 10 » : centiles 10 et 90 ; dernière colonne : part des tirages où le déficit du programme
est sous celui du statu quo dans le même tirage (ρ = 0 – ρ = 1).

| Programme | Médiane 2037 | 2037, 8 sur 10 (indépendantes) | 2037, 8 sur 10 (ensemble) | 2050, de la borne basse à la borne haute | Mieux que le statu quo en 2037 |
|---|---|---|---|---|---|
| Écologie de droite | 2,6 | 2,2 – 3,1 | 1,4 – 4,0 | 0,5 – 4,1 | 100 % – 100 % |
| Bertrand (Nous France) | 7,6 | 7,3 – 8,3 | 6,7 – 9,1 | 10,9 – 19,2 | 100 % – 98 % |
| Retailleau (Les Républicains) | 8,1 | 7,6 – 8,8 | 6,2 – 10,2 | 11,5 – 22,9 | 96 % – 62 % |
| Statu quo | 8,3 | 8,0 – 9,1 | 7,9 – 9,4 | 12,3 – 19,6 | — |
| Philippe (Horizons) | 8,4 | 7,9 – 9,2 | 6,5 – 10,9 | 12,6 – 25,4 | 39 % – 48 % |
| Attal (Renaissance) | 8,9 | 8,3 – 9,7 | 6,7 – 11,2 | 12,7 – 25,6 | 5 % – 36 % |
| Tondelier (Les Écologistes) | 10,3 | 9,9 – 11,3 | 8,3 – 13,2 | 16,9 – 30,7 | 0 % – 4 % |
| Zemmour (Reconquête) | 10,6 | 10,1 – 11,5 | 7,9 – 13,6 | 17,3 – 33,5 | 0 % – 9 % |
| Le Pen (Rassemblement national) — partiel | 11,0 | 10,5 – 11,8 | 9,5 – 13,2 | 18,2 – 31,5 | 0 % – 0 % |
| Lisnard (Nouvelle Énergie) | 11,1 | 10,5 – 12,0 | 8,2 – 14,4 | 18,2 – 35,6 | 0 % – 6 % |
| Glucksmann (Place publique) | 11,9 | 11,4 – 12,8 | 10,3 – 14,0 | 19,9 – 32,4 | 0 % – 0 % |
| Arthaud (Lutte ouvrière) — partiel | 13,4 | 12,9 – 14,9 | 11,0 – 17,4 | 24,1 – 41,6 | 0 % – 0 % |
| Mélenchon (La France insoumise) | 22,0 | 21,5 – 23,8 | 18,0 – 28,3 | 46,9 – 67,1 | 0 % – 0 % |
| Roussel (Parti communiste français) | 22,7 | 21,7 – 25,2 | 18,2 – 29,6 | 55,6 – 80,0 | 0 % – 0 % |

Lecture :
- Écologie de droite et Bertrand font mieux que le statu quo dans presque tous les tirages, aux deux bornes ;
  Arthaud, Glucksmann, Le Pen, Mélenchon et Roussel dans aucun ; Tondelier, Lisnard et Zemmour presque jamais ;
- Retailleau, Philippe et Attal sont à portée du statu quo : leur classement dépend de la corrélation (Retailleau de
  96 % à 62 % des tirages, Philippe de 39 à 48 %, Attal de 5 à 36 %) ;
- à ρ = 0 les intervalles sont deux à trois fois plus étroits ; à ρ = 1 ils redonnent à peu près l'écart entre
  l'optimiste et le prudent ; l'intervalle s'élargit fortement avec le temps (dette et prime de taux).

## Sensibilité (D3) : ce qui fait le déficit de 2037

Lue dans les tirages indépendants (ρ = 0), où chaque hypothèse bouge seule : corrélation de rang entre le tirage de
l'hypothèse et le déficit de 2037 (signe moins : une valeur favorable baisse le déficit), gardée au-delà de 3 écarts
types du hasard (0,12 pour 600 tirages). L'anomalie du rendement de la recherche vue sur le premier calcul (ρ = 0,5)
disparaît : c'était le hasard.

- Statu quo : `macro.ia_productivite` (−0,81); `macro.tendance` (−0,42); `macro.prime_dette` (−0,18); `inflation.long_terme` (+0,13)
- Écologie de droite : `offre.elasticite_cout_travail` (−0,70); `macro.baisse_spread` (−0,36); `macro.ia_productivite` (−0,27); `macro.semi_elasticite_transfert` (−0,21); `offre.travail_part_pib` (+0,21); `hauts_revenus.elasticite_revenu` (−0,20); `logement_offre.bareme/logements` (−0,19); `seniors.devenir` (−0,17); `macro.tendance` (+0,16)
- Retailleau (Les Républicains) : `macro.ia_productivite` (−0,75); `macro.tendance` (−0,37); `macro.prime_dette` (−0,15); `logement_offre.bareme/logements` (−0,14); `enveloppe_economies.domaines/etat/capacite` (−0,14); `retailleau_mesures.ria/montant` (−0,13)
- Tondelier (Les Écologistes) : `macro.ia_productivite` (−0,67); `macro.tendance` (−0,39); `tondelier_mesures.successions/montant` (−0,27); `tondelier_mesures.zucman/montant` (−0,26); `emploi_public.eviction_privee` (−0,19); `tondelier_smic.elasticite_emploi` (−0,16); `macro.prime_dette` (−0,16); `fraude.bareme/rendement_marginal` (−0,15); `tondelier_mesures.tva_verte/montant` (−0,13); `tondelier_mesures.is_minimal/montant` (−0,13)
- Mélenchon (La France insoumise) : `macro.ia_productivite` (−0,54); `macro.prime_dette` (−0,52); `macro.tendance` (−0,30); `melenchon_mesures.garantie_autonomie/montant` (−0,20); `melenchon_mesures.zucman/montant` (−0,18); `emploi_public.eviction_privee` (−0,16); `melenchon_mesures.garantie_jeunes/montant` (−0,15); `melenchon_ecologie.agriculture/effet_mt` (+0,14)
- Roussel (Parti communiste français) : `roussel_mesures.nationalisations/montant` (−0,58); `macro.prime_dette` (−0,55); `macro.ia_productivite` (−0,27); `roussel_temps_travail.trente_deux_heures/gain_productivite` (−0,26); `roussel_temps_travail.trente_deux_heures/part_embauches` (−0,19); `roussel_mesures.zucman/montant` (−0,18); `emploi_public.eviction_privee` (−0,18); `roussel_mesures.carburants/montant` (−0,17)

Partout, l'apport de l'IA à la productivité et la tendance de productivité dominent ; la prime de risque sur la dette
pèse le plus pour les programmes à fort déficit (Mélenchon, Roussel) ; l'élasticité de l'emploi au coût du travail pour
Écologie de droite.

## Limites

- Les bornes sont celles des scénarios : la loi ne dit rien de plus que les sources qui les fondent (phase C).
- La corrélation entre hypothèses n'a pas de source : on publie ses deux bornes, pas de valeur centrale.
- Les effets en sens inverse (scénario miroir) restent à leur valeur prudente dans chaque tirage.
- Calcul : ≈ 6 s par tirage pour les quatorze trajectoires sur deux processus (1 000 tirages ≈ 1 h 40) ;
  les tirages sont écrits au fil de l'eau (`sorties/incertitude_tirages_*.jsonl`) et le calcul reprend après une
  interruption.
