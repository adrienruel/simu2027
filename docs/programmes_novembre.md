# Glucksmann, Attal, Philippe, Retailleau, Lisnard : chiffrage sur le noyau (7 novembre 2026)

```
programmes/<nom>/ (parametres.yaml, mesures.yaml, programme.py) ; tests/test_<nom>.py
python -m moteur.noyau <nom>
```

Aucun de ces candidats n'a publié de programme présidentiel complet au 6/11/2026. Chaque fiche (`mesures.yaml`) reprend toutes les mesures recensées par programmes-2027.fr, avec leur source et leur traitement :
- un paramètre ;
- un calcul ;
- ou la raison de ne pas la chiffrer : réglementation, institutions, niveau européen, hors solde, ou proposition du seul parti.

Le nombre de mesures recensées est le suivant :

| Candidat | Mesures |
|---|---|
| Glucksmann | 112 |
| Attal | 106 |
| Philippe | 87 |
| Retailleau | 93 |
| Lisnard | 91 |

## Règles appliquées

- **Économies et recettes annoncées : jamais reprises.** Seules les mesures nommées sont estimées, en quatre scénarios. Les annonces écartées sont les suivantes :
  - Attal : 150 Md€ ;
  - Philippe : 50 Md€ d'aides aux entreprises, estimés à 20 Md€ en prudent sans reprendre l'annonce ;
  - Retailleau : 197 Md€ ;
  - Lisnard : 80 puis 200 Md€ ;
  - Glucksmann : les 15 Md€ attendus des héritages.
- **Montants des mesures donnés par le candidat : ce sont des paramètres** (statut DECISION ou SOURCE) :
  - Philippe : 50 Md€ d'impôts de production en moins ;
  - Lisnard : 40 Md€ d'impôts de production et 120 Md€ rendus aux actifs ;
  - Retailleau : restitution de 30 Md€ et défense à 100 Md€ ;
  - Glucksmann : 15 Md€ de CSG.
- **Suppressions de postes annoncées.** Règle commune depuis la relecture neutre : 120 000 (crise), 200 000 (prudent), 300 000 (médian) et 400 000 (optimiste) postes, plafonnés à l'annonce, à 55 000 € par poste, avec la même règle d'éviction que les autres programmes.
- **Attal.** Les mesures tirées seulement des conventions ou pétitions de Renaissance (2025) ne sont pas chiffrées, car ce sont des propositions du parti.
- **Économie nommée mais non chiffrée par le candidat : estimée, jamais mise à 0** (rappel d'Adrien du 07/11/2026). Ajouts : santé stabilisée et niches fiscales (Philippe), cabinets de conseil (Glucksmann), désindexation des pensions au-delà de 2 000 € (Lisnard). Les objectifs d'ensemble chiffrés par le candidat sans mesure (150, 197, 200 Md€, déficit à 2 %) restent écartés.
- **Sens des scénarios.** Dépense : crise ≥ prudent ≥ médian ≥ optimiste. Recette : l'inverse. C'est vérifié par un test pour chaque programme.

## Nouveau dans le moteur

- `bibliotheque.baisse_prelevements_salaries` : baisse de prélèvements salariaux (CSG ou cotisations) répartie entre privé et public. Elle comprend :
  - l'impôt sur le revenu en plus, puisque les prélèvements déductibles diminuent ;
  - la prime d'activité et les aides en moins ;
  - un effet d'offre calculé par OpenFisca, avec la forme de la suppression de la CSG.

  Elle sert à Attal (« droit au brut »), Retailleau (restitution aux salariés) et Lisnard (120 Md€).
- `ProgrammeSimple` : `actifs_en_plus` sert aux personnes retirées de la population active sans devenir chômeuses (service civique de Glucksmann).

## Mesures calculées

| Programme | Mesure | Calcul |
|---|---|---|
| Glucksmann | SMIC à 1 600 €, CSG −15 Md€, retraite à 62 ans, assurance chômage, TZCLD, service civique de dix mois | bib.smic, baisse de CSG, baisse_age_legal_detail, seniors |
| Attal | « Droit au brut » (≈ 52 Md€ en prudent ; 40 cités par la presse), année blanche de 2028, assurance chômage | baisse_prelevements_salaries ; pensions gelées une année, l'économie s'éteint avec les retraités de 2028 |
| Philippe | Retraite à 65 ans en moins de dix ans, indemnisation chômage ramenée à 12 mois | report_age_legal_detail (rythme de Bertrand) |
| Retailleau | Âge minimal de 63 ans avec décote et taux plein ramené à 65 ans (solde net estimé, relecture neutre), restitution de 13 Md€ aux salariés, assurance chômage | baisse_prelevements_salaries |
| Lisnard | CSG de 9,2 à 6,6 % et cotisations salariales (120 Md€, montée en quatre ans), retraite à 65 ans (décision d'Adrien du 07/11/2026), pensions au-delà de 2 000 € gelées pendant le quinquennat, dégressivité du chômage | baisse_prelevements_salaries, report_age_legal_detail |

## Limites

1. Les émissions ne sont pas encore chiffrées pour ces cinq programmes.
2. Les grandes baisses de prélèvements salariaux (Attal, Lisnard) prennent la forme d'incidence de la suppression de la CSG (proportionnelle au salaire). Le gain forfaitaire d'Attal (250 € au médian) pèse davantage sur les bas salaires.
3. La forme des aides aux entreprises supprimées (Philippe, Lisnard) n'est pas connue. La répartition entre coût du travail (40 %) et capital (60 %) est un arbitrage.
4. Les cotisations salariales supprimées (Attal, Lisnard) ne réduisent pas les droits à retraite : on suppose que l'État compense les caisses.
5. Ces programmes sont partiels : le chiffrage est à refaire à la publication des programmes complets.

## Résultats (2037, sauf 2029) — après la relecture neutre du 11/11/2026 (docs/relecture_neutre.md)

Solde primaire contre le statu quo, en points de PIB.

| Programme | Scénario | Solde 2029 | Solde 2037 | PIB | Chômage : programme / statu quo | Emplois (milliers) | dont seniors | PIB encore nécessaire | Déficit : programme / statu quo |
|---|---|---|---|---|---|---|---|---|---|
| Glucksmann | prudent | −1,3 | −3,1 | −1,1 % | 9,0 / 8,3 | −677 | −264 | +5,9 % | 13,9 / 9,3 |
|  | optimiste | −0,5 | −1,8 | −0,3 % | 8,3 / 8,3 | −322 | −216 | +3,5 % | 10,2 / 7,9 |
| Attal | prudent | −1,1 | −1,3 | +0,6 % | 8,2 / 8,3 | +148 | 0 | +2,5 % | 11,3 / 9,3 |
|  | optimiste | −0,5 | −0,1 | +1,4 % | 7,7 / 8,3 | +344 | 0 | +0,3 % | 8,1 / 7,9 |
| Philippe | prudent | −0,3 | −0,4 | +0,8 % | 8,3 / 8,3 | +151 | +100 | +0,7 % | 9,8 / 9,3 |
|  | optimiste | +0,2 | +0,9 | +1,2 % | 7,5 / 8,3 | +444 | +128 | aucun | 6,6 / 7,9 |
| Retailleau | prudent | −0,5 | −0,5 | +0,5 % | 8,3 / 8,3 | +44 | 0 | +1,0 % | 10,1 / 9,3 |
|  | optimiste | +0,1 | +1,0 | +1,5 % | 7,1 / 8,3 | +484 | 0 | aucun | 6,5 / 7,9 |
| Lisnard | prudent | −1,7 | −3,0 | +2,0 % | 8,3 / 8,3 | +369 | +100 | +5,8 % | 13,7 / 9,3 |
|  | optimiste | −0,9 | −0,3 | +4,6 % | 6,9 / 8,3 | +1060 | +128 | +0,8 % | 8,3 / 7,9 |

Lecture :
- **Philippe et Retailleau** : les baisses d'impôts sont compensées, en partie seulement, par les mesures nommées (âge de 65 ans, non-remplacement, aides aux entreprises, assurance chômage). Le solde est à moins d'un demi-point du statu quo en prudent, meilleur en médian et en optimiste.
- **Lisnard** : les 120 Md€ rendus aux actifs et les 40 Md€ d'impôts de production font le plus fort effet d'offre des programmes chiffrés (+1,8 % de PIB en prudent, +4,5 % en optimiste). Les économies nommées n'en couvrent qu'une partie.
- **Attal** : le « droit au brut » (≈ 52 Md€) n'est couvert qu'en partie par les mesures nommées.
- **Glucksmann** : voir docs/glucksmann.md.
