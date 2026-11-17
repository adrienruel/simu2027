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
comprise.

**Effets en sens inverse (phase 3.2, 16/11/2026).** Le moteur lit le scénario miroir quand un effet change de sens
(une relance prend les valeurs du prudent dans le médian : multiplicateur, transmission des taux, éviction, offre,
seniors, capital public, solde migratoire, réformes de structure). Ces paramètres (`incertitude.MIROIR_CLES`) ont
désormais leur colonne prudente tirée au point miroir z_m = −z − 1,2816 : au médian (z = 0) elle vaut le prudent, au
10e centile le médian, au 90e centile elle va vers la crise, comme dans les scénarios publiés. Avant, elle restait
au prudent publié : les effets en sens inverse n'étaient pas tirés. Les autres lectures de la colonne prudente
(tendance d'avant 2029, inflation de 2027-2028) ne bougent pas.

**Multiplicateur de référence.** Les profils d'emploi de Mésange étaient rapportés au multiplicateur médian, lu
dans la colonne tirée : l'emploi de conjoncture ne suivait pas le multiplicateur tiré, et un tirage à la borne
basse (multiplicateur nul) divisait par zéro (2 tirages sur 600 écartés à ρ = 0, 5 à ρ = 1, pour tous les
programmes). La référence est désormais fixe (`bouclage.multiplicateur_reference`, 1, le médian publié) : aucun
tirage n'est écarté, et le nombre de tirages écartés est publié (`tirages_ecartes` dans
`comparaison_incertitude.csv`).

**Fonds de capitalisation.** Pour les cinq programmes qui en ont un (Bertrand, Le Pen, Philippe, Retailleau,
Zemmour), chaque tirage calcule aussi la variante « fonds dans les administrations publiques » : fourchettes dans
`sorties/comparaison_incertitude_fonds.csv`, à côté de la publiée.

**Contrôle (en test depuis le 16/11/2026, `tests/test_incertitude.py`).** Avec ρ = 1 et tous les z au 10e centile,
le tirage retrouve le scénario prudent à quelques dixièmes près. Écart au statu quo en 2037, tirage moins publié :
statu quo −0,04 point ; programmes de −0,04 (Bertrand) à −0,73 (Arthaud), Mélenchon −0,61, Tondelier −0,10. Avant le
tirage des miroirs : jusqu'à −1,36 (Arthaud), Mélenchon −1,27, Tondelier −0,63. Le reste vient de règles propres au
scénario prudent (moyennes de jeux, lectures de colonnes hors miroir) : le prudent publié reste un peu plus prudent
que le 10e centile de la loi. Le test exige moins de 0,1 point pour le statu quo et moins de 0,8 pour chaque
programme.

## Résultats (600 tirages communs, fourchette entre les deux bornes de la corrélation)

Recalculés le 17/11/2026 (phase 3.2 : effets miroirs tirés, multiplicateur de référence fixe, aucun tirage écarté), avec la macro bouclée (phase E), la micro des ménages et des entreprises (phases F et H).

Décision d'Adrien (14/11/2026) : la corrélation entre hypothèses n'a pas de source ; on publie la fourchette entre
ρ = 0 (hypothèses indépendantes) et ρ = 1 (toutes ensemble), sans valeur centrale. Déficit en % du PIB, règle de
trajectoire comprise ; « 8 sur 10 » : centiles 10 et 90 ; dernière colonne : part des tirages où le déficit du programme
est sous celui du statu quo dans le même tirage (ρ = 0 – ρ = 1).

| Programme | Médiane 2037 | 2037, 8 sur 10 (indépendantes) | 2037, 8 sur 10 (ensemble) | 2050, de la borne basse à la borne haute | Mieux que le statu quo en 2037 |
|---|---|---|---|---|---|
| Bertrand (Nous France) | 8,1 | 7,6 – 8,6 | 6,9 – 9,4 | 9,4 – 19,8 | 100 % – 93 % |
| Retailleau (Les Républicains) | 8,1 | 7,5 – 8,8 | 6,2 – 9,9 | 8,0 – 22,2 | 99 % – 66 % |
| Statu quo | 8,5 | 8,0 – 9,1 | 7,9 – 9,4 | 11,3 – 19,6 | — |
| Philippe (Horizons) | 8,6 | 8,0 – 9,3 | 6,3 – 10,9 | 8,4 – 25,8 | 36 % – 47 % |
| Attal (Renaissance) | 8,9 | 8,2 – 9,6 | 6,7 – 10,9 | 8,8 – 24,8 | 7 % – 36 % |
| Tondelier (Les Écologistes) | 10,0 | 9,4 – 10,9 | 7,2 – 13,0 | 10,5 – 30,7 | 0 % – 20 % |
| Zemmour (Reconquête) | 10,6 | 10,0 – 11,3 | 8,1 – 13,0 | 11,6 – 32,3 | 0 % – 7 % |
| Le Pen (Rassemblement national) — partiel | 10,9 | 10,3 – 11,5 | 9,1 – 13,0 | 13,9 – 31,3 | 0 % – 0 % |
| Lisnard (Nouvelle Énergie) | 10,9 | 10,2 – 11,6 | 8,3 – 13,5 | 11,9 – 34,1 | 0 % – 5 % |
| Glucksmann (Place publique) | 11,3 | 10,6 – 12,0 | 9,7 – 13,1 | 15,0 – 30,4 | 0 % – 0 % |
| Arthaud (Lutte ouvrière) — partiel | 12,7 | 11,8 – 13,7 | 10,3 – 15,8 | 16,5 – 38,2 | 0 % – 0 % |
| Mélenchon (La France insoumise) | 20,8 | 19,7 – 22,1 | 15,7 – 27,0 | 29,5 – 64,5 | 0 % – 0 % |
| Roussel (Parti communiste français) | 21,8 | 20,4 – 24,0 | 16,5 – 29,2 | 39,6 – 78,1 | 0 % – 0 % |

Lecture :
- Bertrand et Retailleau font mieux que le statu quo dans la plupart des tirages, aux deux bornes (Retailleau de 99 %
  à 66 % des tirages) ; Arthaud, Glucksmann, Le Pen, Mélenchon et Roussel jamais ;
- Philippe et Attal sont à portée du statu quo : leur classement dépend de la corrélation (Philippe de 36 à 47 %, Attal
  de 7 à 36 %) ; Tondelier passe de 0 à 20 %, Zemmour de 0 à 7 %, Lisnard de 0 à 5 % ;
- par rapport au calcul du 16/11 (miroirs non tirés), les médianes bougent de 0,1 point au plus et les fourchettes
  « ensemble » s'élargissent un peu (Tondelier 7,8 – 12,6 → 7,2 – 13,0) : les effets en sens inverse sont désormais
  incertains eux aussi ;
- fonds dans les administrations publiques (`comparaison_incertitude_fonds.csv`) : Philippe fait mieux que le statu quo
  dans 75 % à 55 % des tirages (36 % à 47 % publié) ; pour les quatre autres programmes à fonds, moins de 0,2 point
  d'écart ;
- à ρ = 0 les intervalles sont deux à trois fois plus étroits ; l'intervalle s'élargit fortement avec le temps (dette
  et prime de taux).

## Sensibilité (D3) : ce qui fait le déficit de 2037

Lue dans les tirages indépendants (ρ = 0), où chaque hypothèse bouge seule : corrélation de rang entre le tirage de
l'hypothèse et le déficit de 2037 (signe moins : une valeur favorable baisse le déficit), gardée au-delà de 3 écarts
types du hasard (0,12 pour 600 tirages). L'anomalie du rendement de la recherche vue sur le premier calcul (ρ = 0,5)
disparaît : c'était le hasard.

- Statu quo : `macro.ia_productivite` (−0,81); `macro.tendance` (−0,42); `macro.prime_dette` (−0,18); `inflation.long_terme` (+0,13)
- Écologie de droite : `offre.elasticite_cout_travail` (−0,68); `macro.ia_productivite` (−0,40); `macro.baisse_spread` (−0,33); `offre.travail_part_pib` (+0,22); `macro.multiplicateur` (−0,21); `seniors.devenir` (−0,19); `logement_offre.bareme/logements` (−0,18); `macro.semi_elasticite_transfert` (−0,17); `hauts_revenus.elasticite_revenu` (−0,14)
- Retailleau (Les Républicains) : `macro.ia_productivite` (−0,76); `macro.tendance` (−0,37); `logement_offre.bareme/logements` (−0,14); `macro.prime_dette` (−0,14); `inflation.long_terme` (+0,13); `hauts_revenus.regle_nordique` (−0,12)
- Philippe (Horizons) : `macro.ia_productivite` (−0,69); `macro.tendance` (−0,38); `philippe_mesures.aides_entreprises_capital/montant` (−0,24); `enveloppe_economies.domaines/prestations/capacite` (−0,23); `macro.prime_dette` (−0,16); `philippe_mesures.capitalisation_collective/montant` (−0,15); `philippe_mesures.retraites_contribution/montant` (−0,14)
- Tondelier (Les Écologistes) : `macro.ia_productivite` (−0,68); `macro.tendance` (−0,39); `tondelier_mesures.successions/montant` (−0,25); `tondelier_mesures.zucman/montant` (−0,25); `emploi_public.eviction_privee` (−0,19); `fraude.bareme/rendement_marginal` (−0,15); `tondelier_mesures.is_minimal/montant` (−0,14)
- Mélenchon (La France insoumise) : `macro.ia_productivite` (−0,53); `capacite.effet_au_dela` (−0,46); `macro.prime_dette` (−0,32); `macro.tendance` (−0,30); `melenchon_mesures.zucman/montant` (−0,19); `melenchon_mesures.garantie_autonomie/montant` (−0,18); `emploi_public.eviction_privee` (−0,15); `bouclage.prime_demande` (−0,15); `capacite.seuil_pib` (−0,14); `melenchon_mesures.ir_hauts_revenus/montant` (−0,13)
- Roussel (Parti communiste français) : `roussel_mesures.nationalisations/montant` (−0,62); `macro.prime_dette` (−0,48); `macro.ia_productivite` (−0,26); `roussel_temps_travail.trente_deux_heures/gain_productivite` (−0,24); `capacite.effet_au_dela` (−0,19); `roussel_temps_travail.trente_deux_heures/part_embauches` (−0,19); `emploi_public.eviction_privee` (−0,16); `roussel_mesures.carburants/montant` (−0,15); `roussel_mesures.zucman/montant` (−0,15)

Partout, l'apport de l'IA à la productivité et la tendance de productivité dominent ; la prime de risque sur la dette
pèse le plus pour les programmes à fort déficit (Mélenchon, Roussel) ; l'élasticité de l'emploi au coût du travail pour
Écologie de droite. Calcul du 16/11/2026 : ≈ 4,7 s par tirage, ≈ 47 min par borne.

## Limites

- Les bornes sont celles des scénarios : la loi ne dit rien de plus que les sources qui les fondent (phase C).
- La corrélation entre hypothèses n'a pas de source : on publie ses deux bornes, pas de valeur centrale.
- Les effets en sens inverse (scénario miroir) restent à leur valeur prudente dans chaque tirage.
- Calcul : ≈ 6 s par tirage pour les quatorze trajectoires sur deux processus (1 000 tirages ≈ 1 h 40) ;
  les tirages sont écrits au fil de l'eau (`sorties/incertitude_tirages_*.jsonl`) et le calcul reprend après une
  interruption.
