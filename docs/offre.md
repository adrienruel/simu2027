# Canal d'offre commun (6 novembre 2026)

Pourquoi : le multiplicateur commun ne compte que la demande, dont l'effet s'efface en quelques années. Une baisse
d'impôt sur le travail ou les entreprises change aussi durablement l'offre (plus de gens qui travaillent, plus de
capital), et une hausse la réduit. Sans ce canal, on pouvait reprocher au modèle de sous-estimer la croissance des
programmes qui baissent les impôts (Zemmour) et de sous-estimer le coût de ceux qui les montent (Tondelier).

```
moteur/offre.py ; paramètres : parametres/commun/economie.yaml, groupe offre ; tests : tests/test_offre.py
```

## Méthode

- Chaque mesure fiscale ou de transfert porte un **instrument** (`instrument:` dans les paramètres d'un programme,
  `Mesure.instrument` dans le code) : travail, coût du travail, fiscalité des entreprises, du capital des ménages,
  successions, TVA et accises, transferts aux actifs.
- Effet de long terme sur le PIB = élasticité de l'instrument × prélèvement en moins (en points de PIB). Un transfert
  aux actifs en moins compte comme une baisse de prélèvement (un peu plus de travail).
- **Prudence dans les deux sens** : quand l'instrument joue pour le programme (baisse), on prend l'élasticité du
  scénario ; quand il joue contre (hausse), celle du scénario miroir (prudent ↔ médian, crise ↔ optimiste), comme
  l'éviction des postes publics supprimés.
- **Montée** : ajustement partiel de 10 % de l'écart par an (8 % en crise, 12 % en optimiste), profil de Mésange
  (11 % la première année, 40 % à cinq ans, 60 % à dix ans).
- **Comptes** : le PIB en plus rapporte la part des recettes dans le PIB du statu quo, comme le multiplicateur.
- **Emploi** : offre de travail (travail, transferts) : emplois venus de l'inactivité, le chômage ne bouge pas ;
  coût du travail, entreprises, consommation : emplois pris sur le chômage.
- **Hors du canal** : les mesures qui ont déjà leur propre effet sur l'emploi (SMIC de Tondelier et d'Arthaud,
  assurance chômage de Tondelier, postes publics) et Écologie de droite, dont le moteur a des canaux d'offre plus
  détaillés (participation des inactifs, coût du travail par tranche, localisation des bénéfices).

| Instrument | Crise | Prudent | Médian | Optimiste | Sources (encadrement) |
|---|---|---|---|---|---|
| Travail (CSG, cotisations salariales, IR des actifs) | 0,2 | 0,3 | 0,5 | 0,9 | élasticité de participation 0,1 à 0,25 (Chetty et al., 2011) ; Bassanini et Scarpetta (OCDE, 2001) : 0,3, jusqu'à 0,6-0,7 avec l'investissement |
| Coût du travail (cotisations employeurs, allègements jusqu'à 1,6 SMIC) | 0,8 | 1,0 | 1,5 | 2,1 | Mésange (DG Trésor, 2017) : +2,12 % de PIB à long terme pour 1 point de PIB |
| Entreprises (IS, impôts de production, crédits d'impôt) | 0,3 | 0,5 | 1,0 | 2,0 | Arnold (OCDE, 2008) : l'IS est l'impôt le plus nuisible ; Trésor-Éco n° 290 (2021, CIR) |
| Capital des ménages (dividendes, ISF, Zucman, TTF) | 0 | 0,1 | 0,3 | 0,6 | France Stratégie, évaluation du PFU et de l'IFI : pas d'effet décelable sur l'investissement |
| Successions | 0 | 0 | 0,1 | 0,3 | CAE (2021) ; effet Carnegie (héritiers qui travaillent moins) |
| TVA et accises | 0,05 | 0,1 | 0,2 | 0,3 | Arnold (2008) : parmi les impôts les moins nuisibles |
| Transferts aux actifs (RSA, prime d'activité, APL, allocations familiales) | 0,05 | 0,1 | 0,2 | 0,4 | évaluations du RSA (2011) : effets faibles sur la reprise d'emploi |

En % de PIB à long terme pour 1 point de PIB de prélèvement (ou de transfert aux actifs) en moins.

Choix pris par Claude : les allègements supprimés au-dessus de 1,6 SMIC (Tondelier, REC-37) passent par l'élasticité
du travail, pas par celle de Mésange (baisse uniforme) : le rapport Bozio-Wasmer (2024) trouve peu d'effet sur l'emploi
à ces salaires.

## Résultats (2037 sauf mention)

Solde primaire contre le statu quo (points de PIB), avant et après le canal ; PIB contre le statu quo ; PIB en plus
qu'il faudrait encore pour rejoindre le solde du statu quo (au taux de prélèvement du statu quo).

| Programme | Scénario | Solde primaire, sans → avec | PIB 2037 | PIB 2050 | PIB en plus nécessaire | Déficit : programme / statu quo |
|---|---|---|---|---|---|---|
| Zemmour (avec Knafo) | crise | −3,3 → −3,1 | +0,4 % | +0,6 % | +5,9 % | 17,3 / 12,3 |
| | prudent | −2,8 → −2,4 | +1,0 % | +1,3 % | +4,7 % | 13,5 / 9,7 |
| | médian | −2,0 → −1,4 | +2,2 % | +2,7 % | +2,7 % | 10,6 / 8,5 |
| | optimiste | −1,1 → +0,1 | +4,4 % | +5,2 % | −0,2 % | 8,1 / 8,2 |
| Tondelier | crise | −3,3 → −3,9 | −1,7 % | −2,3 % | +7,5 % | 18,3 / 12,3 |
| | prudent | −2,4 → −2,9 | −1,3 % | −1,6 % | +5,5 % | 13,8 / 9,7 |
| | médian | −1,3 → −1,6 | −0,9 % | −1,1 % | +3,1 % | 10,7 / 8,5 |
| | optimiste | −0,3 → −0,5 | −0,7 % | −0,8 % | +1,0 % | 8,8 / 8,2 |
| Bertrand | prudent | +0,2 → +0,2 | +0,0 % | +0,1 % | −0,3 % | 9,5 / 9,7 |
| Arthaud (partiel) | prudent | −1,8 → −1,8 | −2,2 % | −2,3 % | +3,5 % | 12,7 / 9,7 |

Le PIB de Tondelier et d'Arthaud baisse surtout par les emplois perdus du SMIC, déjà comptés avant ce canal.

Lecture : avec le canal, la suppression de la CSG sur le travail rapporte durablement, en prudent, environ 1 % de PIB
(≈ 0,5 point de PIB de recettes) ; il faudrait encore 4,7 % de PIB pour que le programme Zemmour ne creuse pas le
solde par rapport au statu quo. Il ne s'autofinance que dans le scénario optimiste, qui prend la borne haute des
élasticités (0,9 pour le travail, Bassanini et Scarpetta avec l'investissement). Tondelier perd environ 0,5 point de
solde primaire : ses hausses de prélèvements sur le travail, les entreprises et le capital pèsent sur l'offre.

## Limites

1. Élasticités agrégées par instrument, pas de microsimulation : le taux marginal de chaque ménage (OpenFisca) n'est
   pas encore utilisé ; c'est l'étape suivante pour l'offre de travail.
2. Le report de l'âge de la retraite n'a toujours pas d'effet sur l'emploi des seniors (taux d'emploi par âge figés) :
   limite commune, qui sous-estime le gain des programmes qui reculent l'âge et le coût de ceux qui l'avancent.
3. Pas d'effet des dépenses publiques sur l'offre (investissement public, éducation) au-delà du multiplicateur.
