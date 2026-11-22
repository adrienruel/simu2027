# Préparer le chiffrage programme par programme (roadmap 7.1 à 7.3, 22/11/2026)

## 7.1 Bibliothèque commune

Une même mesure a le même coût dans deux programmes : test `tests/test_bibliotheque_commune.py` (retraite à 60 ans de
LFI et du PCF, soins remboursés à 100 %, impôt sur le revenu des premières tranches de Bertrand et de Tondelier). Les
mesures annoncées sans taux passent par `lectures_communes`, et les types de mesures par les canaux communs
(`moteur/programme_simple.py`) ; aucune fonction propre à un programme n'est restée dans `moteur/`.

## 7.2 Fiche de chaque mesure

`python -m outils.priorites_mesures` écrit `sorties/fiches_mesures.csv` (1 116 mesures). Pour chacune :
- le texte cité (intitulé, source, traitement de `mesures.yaml`) ;
- la lecture retenue (paramètre, instrument, statut et source du chiffrage) ;
- l'effet sur le solde en 2037 dans les quatre scénarios, en points de PIB, calculé par le noyau (toutes les lignes de
  la mesure ; achats d'actifs exclus : ils font la dette, pas le solde) ;
- si elle est codée dans la micro ;
- quatre fragilités : chiffrage sans source (HYPOTHESE ou DECISION), lecture d'une mesure floue, mesure sur les
  ménages non codée dans la micro, même montant dans les quatre scénarios.

Pas encore dedans : le chiffrage tiers (Institut Montaigne, premier trimestre 2027) et le lien de chaque citation (les
`mesures.yaml` donnent la source en texte).

## 7.3 Ordre de travail

Priorité = |effet au prudent| × (1 + fragilités) (`sorties/priorites_mesures.csv`). Les 15 premières :

| Rang | Programme | Mesure | Effet 2037 (pt de PIB) | Fragilités |
|---|---|---|---|---|
| 1 | Philippe | PHI-FIS-01 | -1,41 | sans source, lecture |
| 2 | Lisnard | LIS-FIS-01 | -1,13 | sans source, lecture |
| 3 | Zemmour | ZEM-FIS-01 | -2,85 | – |
| 4 | Lisnard | LIS-ECO-02 | -2,29 | – |
| 5 | Philippe | PHI-FIS-01b | +0,63 | sans source, lecture |
| 6 | Mélenchon | LFI-SAN-01 | -0,93 | sans source |
| 7 | Roussel | PCF-SAN-01 | -0,93 | sans source |
| 8 | Arthaud | ART-EMP-02 | -1,82 | – |
| 9 | Roussel | PCF-RET-03 | -0,87 | sans source |
| 10 | Roussel | PCF-EMP-01 | -1,72 | – |
| 11 | Mélenchon | LFI-PRE-01 | -0,85 | sans source |
| 12 | Tondelier | REC-37 | +0,49 | sans source, non codée |
| 13 | Mélenchon | LFI-RET-03 | -0,72 | sans source |
| 14 | Arthaud | ART-ECO-01 | -1,34 | – |
| 15 | Attal | ATT-ECO-01 | -1,30 | – |

Par programme (`sorties/priorites_programmes.csv`, somme des priorités) :

| Rang | Programme | Priorité | Mesures fragiles |
|---|---|---|---|
| 1 | Mélenchon | 28,6 | 115 / 218 |
| 2 | Tondelier | 18,3 | 82 / 122 |
| 3 | Roussel | 14,6 | 27 / 44 |
| 4 | Philippe | 10,5 | 48 / 123 |
| 5 | Lisnard | 10,1 | 30 / 94 |
| 6 | Zemmour | 7,2 | 28 / 63 |
| 7 | Glucksmann | 6,2 | 56 / 118 |
| 8 | Arthaud | 5,8 | 6 / 37 |
| 9 | Le Pen | 5,2 | 28 / 49 |
| 10 | Retailleau | 4,7 | 34 / 98 |
| 11 | Attal | 3,6 | 29 / 106 |
| 12 | Bertrand | 1,9 | 12 / 33 |

**Ordre proposé :** Mélenchon, Tondelier, Roussel, puis Philippe et Lisnard (les impôts de production, lus et sans
source, sont en tête des mesures). L'a priori de la roadmap (Lisnard, Le Pen, Retailleau, Glucksmann d'abord) ne tient
pas : la couverture de la micro est maintenant haute partout, et ce sont les gros programmes de gauche qui portent le
plus de montants fragiles.
