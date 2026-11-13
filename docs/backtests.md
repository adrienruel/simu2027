# Backtests sur des réformes passées (phase C5 de la roadmap)

13 novembre 2026. Script : `python -m outils.backtests` (réformes rejouées sur le statu quo, canal commun).
Critère de la roadmap : retrouver le signe et l'ordre de grandeur des évaluations ex post.

| Réforme | Rejouée comme | Évaluation publiée | Moteur (crise / prudent / médian / optimiste) | Verdict |
|---|---|---|---|---|
| CICE (2013) | Coût du travail −18 Md€ (coût de 2016), instrument « coût du travail » | ≈ 100 000 emplois créés ou sauvegardés sur 2013-2016 (micro-économétrie) ; 160 000 (macro-sectoriel, 2013-2017) ; 240 000 pour CICE et pacte de responsabilité (Banque de France) | à 3 ans : 39 000 / 59 000 / 89 000 / 144 000 ; à 10 ans : 83 000 / 118 000 / 177 000 / 272 000 | Signe et ordre de grandeur retrouvés ; le médian à 3 ans (89 000) est proche de l'évaluation micro, le prudent en dessous. |
| Âge légal + 2 ans (réforme de 2023) | Calage existant : retour de 64 à 62 ans (cas exact de l'étude d'impact) ; contrôle : report de 64 à 66 ans, un trimestre par génération | Étude d'impact : un peu plus de 300 000 seniors en emploi en plus en 2030, PIB +1,1 point | 62 ↔ 64 : ≈ 470 000 personnes concernées, ≈ 255 000 emplois au prudent à plein effet (calage de `seniors.part_concernee`) ; 64 → 66 : 158 000 / 175 000 / 193 000 / 224 000 emplois à plein effet, PIB +0,36 % au prudent à 7 ans | Cohérent mais **pas indépendant** : le nombre de personnes concernées est calé sur l'étude d'impact ; la part en emploi (la moitié au prudent, Insee et IPP) est plus prudente que celle de l'étude, d'où ≈ 255 000 au lieu de 300 000 et un effet sur le PIB plus faible. |
| 35 heures (lois Aubry, 1998-2002) | Mécanique commune des 32 heures, paramètres de Roussel : 39 → 35 heures sans perte de salaire pour 60 % des salariés du privé, plus ≈ 10 Md€ d'allègements propres aux 35 heures (16 Md€ à maturité, dont 6 pour la ristourne Juppé préexistante), en euros de 2026 par le PIB nominal (× 1,95), instrument « coût du travail » ; pas de modération salariale | ≈ 350 000 emplois de 1996 à 2002 (Dares, Insee), soit ≈ 2,2 % de l'emploi salarié privé ; fourchette de 200 000 à 350 000 au début de la réforme | à 6 ans, en part de l'emploi privé : −0,7 % / +1,0 % / +2,0 % / +3,2 % (−139 000 / +194 000 / +409 000 / +650 000 emplois de 2026) ; dont allègements : 66 000 / 97 000 / 146 000 / 231 000 | Signe et ordre de grandeur retrouvés au médian (2,0 % contre 2,2 %) ; le prudent en donne la moitié, la crise un effet négatif. **Partiellement indépendant** : la part des heures rendues par des embauches (≈ 35 % au médian) avait été choisie pour les 32 heures d'après ce précédent. La modération salariale des accords de 1998-2002, absente ici, irait dans le sens de l'évaluation. |
| PFU (2018) | Fiscalité du capital des ménages −1,9 Md€ de 2026 (≈ 1,5 Md€ de 2018), instrument « fiscalité du capital des ménages » | Aucun effet identifié sur l'investissement (France Stratégie, comité d'évaluation, 3e rapport et rapport final de 2023) ; dividendes versés aux ménages +60 % en 2018 ; coût budgétaire fortement réduit par ces dividendes | PIB à 5 ans : 0,00 % / +0,003 % / +0,009 % / +0,02 % ; aucun emploi | Retrouvé : effet sur l'activité négligeable. La réponse des dividendes (qui réduit le coût) n'est pas dans le canal commun ; elle passe par les réactions des contribuables, mesure par mesure. |

## C5 fini

Les quatre réformes de la roadmap sont rejouées ; le moteur retrouve le signe et l'ordre de grandeur, au médian pour
le CICE et les 35 heures, avec un prudent en dessous des évaluations. Deux backtests (âge légal, 35 heures) ne sont
que partiellement indépendants, une partie de leurs paramètres ayant été calée sur ces réformes.

## Sources

- Insee, Économie et statistique n° 376-377 (2004), bilan des 35 heures (≈ 350 000 emplois de 1998 à 2002) : https://www.insee.fr/fr/statistiques/fichier/1376464/es376377b.pdf
- Assemblée nationale, réponse à la question n° 26390 (allègements : 16 Md€ à maturité, dont 6 pour la ristourne Juppé) : https://questions.assemblee-nationale.fr/dyn/12/questions/QANR5L12QE26390.pdf
- France Stratégie, comité d'évaluation des réformes de la fiscalité du capital, 3e rapport : https://www.vie-publique.fr/rapport/281944-comite-devaluation-des-reformes-de-la-fiscalite-du-capital-3e-rapport

- France Stratégie, évaluation du CICE (septembre 2020) : https://www.vie-publique.fr/sites/default/files/rapport/pdf/276212.pdf
- Banque de France, bulletin n° 231 (2020), CICE et pacte de responsabilité : https://www.banque-france.fr/system/files/2023-01/bdf231-6_politiques-economiques.pdf
- Rexecode, Repères n° 5 (avril 2023), d'après l'étude d'impact de la réforme de 2023 : https://www.rexecode.fr/media/documents/document-de-travail/reperes/reperes-5-impact-de-la-reforme-des-retraites-sur-le-deficit-avril-2023
