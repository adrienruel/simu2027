# Backtests sur des réformes passées (phase C5 de la roadmap)

13 novembre 2026. Script : `python -m outils.backtests` (réformes rejouées sur le statu quo, canal commun).
Critère de la roadmap : retrouver le signe et l'ordre de grandeur des évaluations ex post.

| Réforme | Rejouée comme | Évaluation publiée | Moteur (crise / prudent / médian / optimiste) | Verdict |
|---|---|---|---|---|
| CICE (2013) | Coût du travail −18 Md€ (coût de 2016), instrument « coût du travail » | ≈ 100 000 emplois créés ou sauvegardés sur 2013-2016 (micro-économétrie) ; 160 000 (macro-sectoriel, 2013-2017) ; 240 000 pour CICE et pacte de responsabilité (Banque de France) | à 3 ans : 39 000 / 59 000 / 89 000 / 144 000 ; à 10 ans : 83 000 / 118 000 / 177 000 / 272 000 | Signe et ordre de grandeur retrouvés ; le médian à 3 ans (89 000) est proche de l'évaluation micro, le prudent en dessous. |
| Âge légal + 2 ans (réforme de 2023) | Calage existant : retour de 64 à 62 ans (cas exact de l'étude d'impact) ; contrôle : report de 64 à 66 ans, un trimestre par génération | Étude d'impact : un peu plus de 300 000 seniors en emploi en plus en 2030, PIB +1,1 point | 62 ↔ 64 : ≈ 470 000 personnes concernées, ≈ 255 000 emplois au prudent à plein effet (calage de `seniors.part_concernee`) ; 64 → 66 : 158 000 / 175 000 / 193 000 / 224 000 emplois à plein effet, PIB +0,36 % au prudent à 7 ans | Cohérent mais **pas indépendant** : le nombre de personnes concernées est calé sur l'étude d'impact ; la part en emploi (la moitié au prudent, Insee et IPP) est plus prudente que celle de l'étude, d'où ≈ 255 000 au lieu de 300 000 et un effet sur le PIB plus faible. |

## Restent (C5)

- 35 heures (1998-2002, ≈ 350 000 emplois selon la Dares, avec les allègements) : à rejouer avec la mécanique commune
  des 32 heures (`programme_simple.trente_deux_heures`).
- Prélèvement forfaitaire unique (2018) : effets sur les dividendes déclarés et le coût budgétaire (France Stratégie,
  comité d'évaluation des réformes de la fiscalité du capital) ; à rejouer par l'instrument « fiscalité du capital des
  ménages ».

## Sources

- France Stratégie, évaluation du CICE (septembre 2020) : https://www.vie-publique.fr/sites/default/files/rapport/pdf/276212.pdf
- Banque de France, bulletin n° 231 (2020), CICE et pacte de responsabilité : https://www.banque-france.fr/system/files/2023-01/bdf231-6_politiques-economiques.pdf
- Rexecode, Repères n° 5 (avril 2023), d'après l'étude d'impact de la réforme de 2023 : https://www.rexecode.fr/media/documents/document-de-travail/reperes/reperes-5-impact-de-la-reforme-des-retraites-sur-le-deficit-avril-2023
