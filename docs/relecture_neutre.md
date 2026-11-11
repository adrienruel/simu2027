# Relecture neutre du réalisme : corrections appliquées (11 novembre 2026)

Un agent indépendant, en lecture seule sur le dépôt, a relu tous les programmes le 7/11/2026. Son rapport complet, avec les sources, est dans docs/relecture_neutre_rapport.md. Ce qui a été appliqué :

| Point | Correction | Fichiers | Effet (prudent) |
|---|---|---|---|
| 1, 8 | **Âge légal réel de chaque génération au statu quo** : loi de 2023 et suspension de la LFSS 2026, soit 62 ans 9 mois pour 1964 et 63 ans 9 mois pour 1968. Avant, le modèle appliquait 64 ans à toutes les générations : au retour à 62 ans, 1,3 million de personnes partaient d'un coup. | parametres/commun/economie.yaml (age_legal_generation, part_retraites_62), moteur/ancien_systeme.profil_generation, moteur/statu_quo.retraites, moteur/bibliotheque | Retour à 62 ans : 15 Md€ en 2029 et ≈ 23 à 25 Md€ à plein effet, contre 31 dès 2029 auparavant |
| 1, 2 | **Taux plein automatique à 67 ans inchangé** : un report de l'âge ne décale plus les départs à partir de 67 ans, et le profil à 64 ans rejoint celui à 62 ans à 67 ans. **Calage sur la masse de droit direct** (88 %) : la réversion et le minimum vieillesse ne bougent pas avec l'âge. | idem (age_taux_plein, part_droit_direct) | 65 ans : ≈ 9 à 10 Md€ à plein effet, contre 13,5 (Cour des comptes : 9,2) |
| — | **Statu quo recalé sur le COR** : l'érosion relative passe de 0,46 à 0,36 % pour garder 15,3 % du PIB en 2070. 2030 donne 14,06 % (COR 14,1 %), 2045 13,86 % (COR 14,2 %). | parametres/commun/statu_quo.yaml, tests/test_statu_quo.py | La part des retraites est un peu plus basse entre 2032 et 2050 |
| — | Tondelier rebranché sur la bibliothèque, avec le même calcul du retour à 62 ans que Glucksmann et Mélenchon | programmes/tondelier/programme.py | — |
| 2 | **Retailleau relu** : ce n'est pas un report à 65 ans. La mesure combine un âge minimal de 63 ans avec décote et un taux plein automatique ramené de 67 à 65 ans. Son solde net est estimé à 0 / +1 / +2,5 / +4 Md€ à plein effet. | programmes/retailleau | ≈ −7 Md€ en 2040 |
| 3 | **Philippe, aides aux entreprises** : estimation propre (12 / 20 / 28 / 35 Md€) au lieu de 50 à 100 % des 50 Md€ annoncés | programmes/philippe | ≈ −15 Md€ |
| 4 | **Postes non remplacés, règle commune** (précédent de la RGPP) : 120 000 / 200 000 / 300 000 / 400 000, plafonnés à l'annonce | Zemmour, Retailleau, Lisnard | −2 à −5 Md€ |
| 5 | **Emplois payés au SMIC** : 39 % de prélèvements récupérés au lieu de 57 % (`fp_taux`) | Mélenchon (conscription, garantie d'emploi, emploi jeune), Tondelier (AESH) | Mélenchon ≈ −6 Md€ |
| 6 | **Attal, « droit au brut »** : 58 / 52 / 46 / 40, car le prudent ne peut pas être sous le calcul de la fiche | programmes/attal | ≈ −4,5 Md€ |
| 7 | **Impôts de production assis sur les salaires** : la part payée par les administrations (hôpitaux, versement mobilité des employeurs publics) est retirée | Philippe, Lisnard | +2 à +3 Md€ |
| 9 | **Enseignants** : coût employeur ≈ 2,2 fois le net (CAS Pensions compris), cohérent avec les 57 % de prélèvements récupérés | Attal, Retailleau, Philippe, Lisnard | −0,6 à −1 Md€ |
| 10 | **Économies nommées encore à 0** : estimées | Tondelier (moratoire sur les prisons, niches climat, bonus-malus), Mélenchon (Nouvelle-Calédonie), Bertrand (conseiller territorial), Lisnard (INSP) | +0,1 à +1,5 Md€ |

Ce qui n'a pas été appliqué :
- Les objectifs d'ensemble chiffrés par les candidats sans mesures (150, 197, 200 Md€, déficit à 2 %) restent écartés. Les estimer compterait deux fois les mesures déjà chiffrées.
- Les mesures tirées des seules conventions de Renaissance ne sont pas chiffrées.
- Philippe gardait son propre rythme de non-remplacement (175 000 postes en prudent) : aligné le 11/11/2026 sur la règle commune, plafonnée aux 250 000 annoncés (120 000 / 200 000 / 250 000 / 250 000).
- `seniors.part_concernee` : la proposition du rapport (0,9 à 1) n'est pas retenue, car les pensions restent calculées sur le profil par génération (≈ 1,1 million de non-retraités pour deux ans d'âge). Recalé le 11/11/2026 de 0,4 à 0,42 pour retrouver les ≈ 470 000 personnes concernées de l'étude d'impact de 2023.

Appliqué ensuite (11/11/2026, phase 1 de la roadmap) : enseignants de Glucksmann (35 Md€ bruts × 1,9) et prélèvements récupérés sur les embauches d'Arthaud (`fp_taux` 0,47 à 0,50) ; voir docs/journal.md.
