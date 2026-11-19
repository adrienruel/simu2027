# Backtests sur des réformes passées (phase C5 de la roadmap)

13 novembre 2026. Script : `python -m outils.backtests` (réformes rejouées sur le statu quo, canal commun).
Critère de la roadmap : retrouver le signe et l'ordre de grandeur des évaluations ex post.

| Réforme | Rejouée comme | Évaluation publiée | Moteur (crise / prudent / médian / optimiste) | Verdict |
|---|---|---|---|---|
| CICE (2013) | Coût du travail −18 Md€ (coût de 2016), instrument « coût du travail » | ≈ 100 000 emplois créés ou sauvegardés sur 2013-2016 (micro-économétrie) ; 160 000 (macro-sectoriel, 2013-2017) ; 240 000 pour CICE et pacte de responsabilité (Banque de France) | à 3 ans : 39 000 / 59 000 / 89 000 / 144 000 ; à 10 ans : 83 000 / 118 000 / 177 000 / 272 000 | Signe et ordre de grandeur retrouvés ; le médian à 3 ans (89 000) est proche de l'évaluation micro, le prudent en dessous. |
| Âge légal + 2 ans (réforme de 2023) | Calage existant : retour de 64 à 62 ans (cas exact de l'étude d'impact) ; contrôle : report de 64 à 66 ans, un trimestre par génération | Étude d'impact : un peu plus de 300 000 seniors en emploi en plus en 2030, PIB +1,1 point | 62 ↔ 64 : ≈ 470 000 personnes concernées, ≈ 255 000 emplois au prudent à plein effet (calage de `seniors.part_concernee`) ; 64 → 66 : 158 000 / 175 000 / 193 000 / 224 000 emplois à plein effet, PIB +0,36 % au prudent à 7 ans | Cohérent mais **pas indépendant** : le nombre de personnes concernées est calé sur l'étude d'impact ; la part en emploi (la moitié au prudent, Insee et IPP) est plus prudente que celle de l'étude, d'où ≈ 255 000 au lieu de 300 000 et un effet sur le PIB plus faible. |
| 35 heures (lois Aubry, 1998-2002) | Mécanique commune des 32 heures, paramètres de Roussel : 39 → 35 heures sans perte de salaire pour 60 % des salariés du privé, plus ≈ 10 Md€ d'allègements propres aux 35 heures (16 Md€ à maturité, dont 6 pour la ristourne Juppé préexistante), en euros de 2026 par le PIB nominal (× 1,95), instrument « coût du travail » ; pas de modération salariale | ≈ 350 000 emplois de 1996 à 2002 (Dares, Insee), soit ≈ 2,2 % de l'emploi salarié privé ; fourchette de 200 000 à 350 000 au début de la réforme | à 6 ans, en part de l'emploi privé : −0,7 % / +1,0 % / +2,0 % / +3,2 % (−139 000 / +194 000 / +409 000 / +650 000 emplois de 2026) ; dont allègements : 66 000 / 97 000 / 146 000 / 231 000 | Signe et ordre de grandeur retrouvés au médian (2,0 % contre 2,2 %) ; le prudent en donne la moitié, la crise un effet négatif. **Partiellement indépendant** : la part des heures rendues par des embauches (≈ 35 % au médian) avait été choisie pour les 32 heures d'après ce précédent. La modération salariale des accords de 1998-2002, absente ici, irait dans le sens de l'évaluation. |
| PFU (2018) | Fiscalité du capital des ménages −1,9 Md€ de 2026 (≈ 1,5 Md€ de 2018), instrument « fiscalité du capital des ménages » | Aucun effet identifié sur l'investissement (France Stratégie, comité d'évaluation, 3e rapport et rapport final de 2023) ; dividendes versés aux ménages +60 % en 2018 ; coût budgétaire fortement réduit par ces dividendes | PIB à 5 ans : 0,00 % / +0,003 % / +0,009 % / +0,02 % ; aucun emploi | Retrouvé : effet sur l'activité négligeable. La réponse des dividendes (qui réduit le coût) n'est pas dans le canal commun ; elle passe par les réactions des contribuables, mesure par mesure. |
| Baisse de l'IS de 33,3 à 25 % (2018-2022), **hors calage** (phase 3.3) | Capital des entreprises −12,7 Md€ de 2026 (≈ 11 Md€ de coût ex ante, FIPECO 2017 et Institut Montaigne 2022, × 1,15 pour le PIB nominal de 2022 à 2026), montée en cinq ans | Aucun effet agrégé sur l'investissement isolé à ce jour (France Stratégie, rapport final du comité d'évaluation, octobre 2023) ; création d'entreprises +1 point par point de taux en moins (IPP n° 47, 2023, PFU et IS ensemble) ; taux implicite de l'IS de 20,7 % à 17,5 % de l'excédent net d'exploitation de 2016 à 2022, la base ayant crû plus vite (Insee, document de travail n° 2025-18) | PIB à 10 ans : +0,03 % / +0,04 % / +0,05 % / +0,05 % (0,9 à 1,9 Md€) ; ≈ 3 000 à 5 000 emplois | Compatible avec l'absence d'effet agrégé mesuré : effet faible, coût presque entier. **Test faible** : l'évaluation ex post ne chiffre pas l'effet sur le PIB. Le moteur ne fait pas croître la base de l'IS après une baisse de taux ; l'Insee montre que la base a crû plus vite que l'excédent, ce qui a réduit le coût effectif. |
| Assurance chômage 2019-2021, **hors calage** (phase 3.3) : contrôle des lectures « chômage structurel en moins » d'Attal, Philippe, Retailleau et Lisnard | Ordre de grandeur tiré des effets mesurés : salaire journalier de référence (1,1 million d'allocataires, −10 jours sans emploi), dégressivité (70 000 par an, −1,5 mois), affiliation (475 000 personnes, +3 points de retour à 2 mois) | Dares, rapport final du comité d'évaluation (avril 2025) : effets micro, pas d'effet chiffré sur le niveau d'emploi (p. 9) ; économies ex ante ≈ 2,3 Md€ par an, 7 % des allocations ; Banque de France : réformes de 2021 et 2023 ≈ 0,6 point de chômage structurel | Réforme 2019-2021 : ≈ 41 000 chômeurs en moins, soit 0,13 point. Lectures des programmes au prudent : Lisnard 0,10 ; Attal et Philippe 0,20 ; Retailleau 0,30 (médian 0,15 à 0,40) | Même ordre de grandeur. Au prudent, Attal, Philippe et Retailleau supposent 1,5 à 2,3 fois l'effet de la réforme de 2019-2021 : c'est défendable si leur réforme est plus large (durée ramenée à 12 mois chez Philippe, cumul de mesures chez Retailleau), à confirmer en chiffrant l'ampleur de chaque réforme (à faire). |

## C5 fini

Les quatre réformes de la roadmap sont rejouées ; le moteur retrouve le signe et l'ordre de grandeur, au médian pour
le CICE et les 35 heures, avec un prudent en dessous des évaluations. Deux backtests (âge légal, 35 heures) ne sont
que partiellement indépendants, une partie de leurs paramètres ayant été calée sur ces réformes.

## Phase 3.3 (16/11/2026)

Deux backtests hors calage s'ajoutent (`is_33_25`, `assurance_chomage_2019` dans `outils/backtests.py`). Aucun
paramètre n'a été calé sur ces réformes. Le premier est faible, faute d'évaluation ex post agrégée ; le second
confronte des lectures propres aux programmes à un ordre de grandeur tiré d'effets micro. Chiffrage tiers des
programmes 2027 : l'Institut Montaigne l'annonce pour le premier trimestre 2027 (communiqué du 06/10/2026) ;
l'outil de comparaison mesure par mesure est prêt (`outils/ecarts_tiers.py`, saisie dans
`parametres/sources/chiffrages_tiers.csv`).

## Sources

- Dares, rapport final du comité d'évaluation de la réforme de l'assurance chômage 2019-2021 (avril 2025) : https://www.vie-publique.fr/files/rapport/pdf/298088.pdf
- Insee, document de travail n° 2025-18, la réforme du taux statutaire de l'IS : https://www.insee.fr/fr/statistiques/8635773
- France Stratégie, comité d'évaluation des réformes de la fiscalité du capital, rapport final (octobre 2023) : https://www.strategie.gouv.fr/sites/strategie.gouv.fr/files/atoms/files/fs-2023-rapport-isf-quatrieme_rapport_complet_17octobre.pdf
- IPP, rapport n° 47 (octobre 2023) : https://www.ipp.eu/wp-content/uploads/2023/10/Rapport_IPP_47_ISFcrea-synthese.pdf
- FIPECO, la baisse du taux de l'IS (01/09/2017, coût 11 Md€) : https://fipeco.fr/pdf/0.37671300%201504257113.pdf
- Institut Montaigne, chiffrage des programmes 2027 annoncé (06/10/2026) : https://institutmontaigne.org/communiques-de-presse/presidentielle-2027-linstitut-montaigne-devoile-les-reperes-de-montaigne-25-recommandations-pour-la

- Insee, Économie et statistique n° 376-377 (2004), bilan des 35 heures (≈ 350 000 emplois de 1998 à 2002) : https://www.insee.fr/fr/statistiques/fichier/1376464/es376377b.pdf
- Assemblée nationale, réponse à la question n° 26390 (allègements : 16 Md€ à maturité, dont 6 pour la ristourne Juppé) : https://questions.assemblee-nationale.fr/dyn/12/questions/QANR5L12QE26390.pdf
- France Stratégie, comité d'évaluation des réformes de la fiscalité du capital, 3e rapport : https://www.vie-publique.fr/rapport/281944-comite-devaluation-des-reformes-de-la-fiscalite-du-capital-3e-rapport

- France Stratégie, évaluation du CICE (septembre 2020) : https://www.vie-publique.fr/sites/default/files/rapport/pdf/276212.pdf
- Banque de France, bulletin n° 231 (2020), CICE et pacte de responsabilité : https://www.banque-france.fr/system/files/2023-01/bdf231-6_politiques-economiques.pdf
- Rexecode, Repères n° 5 (avril 2023), d'après l'étude d'impact de la réforme de 2023 : https://www.rexecode.fr/media/documents/document-de-travail/reperes/reperes-5-impact-de-la-reforme-des-retraites-sur-le-deficit-avril-2023

## Ampleur des réformes de l'assurance chômage (roadmap 8.3, 18/11/2026)

`outils/backtests.ampleur_assurance_chomage` rapporte chaque réforme à celle de 2019-2021. L'ampleur, ce sont les
économies de législation du bloc chômage au prudent en 2032, divisées par 2,3 Md€. La lecture relative, c'est la
baisse du chômage déclarée, divisée par 0,13 point. Un rapport proche de 1 veut dire que la lecture est
proportionnée à la réforme.

| Programme | Économies (Md€) | Ampleur | Lecture relative | Rapport |
|---|---|---|---|---|
| Retailleau | 4,61 | 2,01 | 2,30 | 1,15 |
| Philippe | 3,08 | 1,34 | 1,53 | 1,15 |
| Attal | 2,87 | 1,25 | 1,53 | 1,23 |
| Lisnard | 1,03 | 0,45 | 0,77 | 1,72 |

Les lectures d'Attal, Philippe et Retailleau sont proportionnées à l'ampleur de leurs réformes, à 15-25 % près.
L'écart signalé en phase 3.3 (1,5 à 2,3 fois l'effet de 2019-2021) s'explique donc par des réformes plus larges.

Lisnard suppose 1,7 fois l'effet que justifie l'ampleur de sa réforme (dégressivité seule, 1,0 Md€). L'écart est
petit en absolu (0,1 point, ≈ 30 000 chômeurs), mais c'est la lecture à revoir en premier : la ramener à ≈ 0,07 point
la mettrait au rapport des trois autres.

Limite : les 2,3 Md€ sont en euros de 2019-2021, les économies des programmes en euros de 2026 et à l'économie de
2032. La comparaison est un ordre de grandeur.
