# C1 — Hypothèses sans source, classées par poids (13/11/2026)

Méthode (`outils/c1_inventaire.py`) : chaque paramètre au statut HYPOTHESE sans champ `source` est augmenté de
10 % (sous-champ par sous-champ), et on lit l'écart de déficit en 2037 et 2050 (points de PIB, scénario prudent, sans
règle de trajectoire). Les paramètres communs sont testés sur le statu quo, ceux d'un programme sur ce programme.
Les années (`debut`, `plein`, valeurs entières entre 1990 et 2100) sont écartées : +10 % n'a pas de sens pour elles.
Résultats bruts : `sorties/c1_<commun|ecologie_de_droite|tondelier|melenchon>.json`.

Règle de la roadmap : un paramètre qui pèse se source ; s'il n'y a pas de source, il devient une décision écrite
(statut DECISION, à valider par Adrien). Une valeur choisie à l'intérieur d'une fourchette publiée garde le statut
HYPOTHESE avec un champ `source: "Encadrement : …"`, comme le reste du dépôt.

## Paramètres communs (77 variantes, 71 sans effet mesurable)

| Paramètre | Valeur | +10 % : déficit 2037 / 2050 | Suite donnée |
|---|---|---|---|
| `macro.tendance` | 0,4 / 0,7 / 1 / 1 % | −0,11 / −0,69 | Encadré : COR, rapport de juin 2026 (0,4 / 0,7 / 1,0 %) |
| `macro.annees_taux_long_terme` | 6 ans | −0,04 / −0,14 | Encadré : durée de vie moyenne de la dette négociable 8 ans et 184 jours fin 2025 (AFT) ; 6 ans reste prudent |
| `budget_etat.inflation_2026_2030` | 7,4 % | −0,02 / −0,08 | Encadré : 1,8 % en 2027 au PLF 2027 ; 1,018⁴ = 1,074 |
| `ministeres.elasticite_eleves_etudiants` | 0,5 | −0,01 / −0,06 | **Décision à écrire** (pas de source : choix prudent déjà motivé dans la note) |
| `unites.deflateur_2026` | 1,5 % | ≈ 0 | Encadré : déflateur du PIB 2026 prévu à 1,5 % (prévisions de septembre 2026) |
| `budget_etat.cas_pensions_2026` | 50,4 Md€ | ≈ 0 | Sans enjeu |

Hors ces six, aucun paramètre commun sans source ne déplace le déficit de plus de 0,001 point.

## Écologie de droite (293 variantes, 127 paramètres ; 18 pèsent plus de 0,03 point)

Sourcés ou encadrés aujourd'hui :

| Paramètre | Valeur | Source ajoutée |
|---|---|---|
| `carbone_importe.part_hors_ue` | 75 % | L'UE27 émet près d'un quart des émissions importées (SDES-Insee) |
| `tva.agriculture` (émissions) | 77,5 Mt | 76 à 78 Mt CO2e en 2024 (Citepa, Secten 2026) |
| `tva_sante_long_terme.hausse_prix_tabac` (prix avant) | 12,54 € | 12,47 € au 1er juin 2026, prix moyen pondéré (DNF) |
| `rui_complements.micro_en_complement` | 40 % | 40 % des micro-entrepreneurs de 2018 en activité de complément (Insee Première 2118) ; 29 % cumulent avec un salaire |
| `is_investissement.categories` (parts) | 28 / 32 / 40 % | FBCF des SNF : part de la construction stable, propriété intellectuelle de 20 à 34 % (Banque de France) |
| `budget_etat.apprentissage` | 8 Md€ | Encadrement seulement : 20,5 Md€ de dépense publique totale en 2026 (OFCE), 2,0 Md€ d'aides aux employeurs en 2027 (PLF) — le périmètre des 8 Md€ est à préciser |

À rapprocher d'une source (écart constaté) :

- `collectivites.besoin_financement_2024` = 5,6 + 9,7 = 15,3 Md€. La Cour des comptes donne 11,4 Md€ pour les
  collectivités hors syndicats ; l'Insee 17,8 Md€ pour l'ensemble des administrations publiques locales (comptes de
  2026). +10 % vaut +0,07 point en 2037 : passer à 11,4 Md€ baisserait le déficit d'environ 0,18 point, passer à
  17,8 Md€ le monterait d'environ 0,12 point. Le bon périmètre est celui du déficit au sens de Maastricht.

Constructions du modèle ou choix du programme, sans source possible — **à écrire en décisions** :

| Paramètre | Valeur | +10 % : 2037 / 2050 | Nature |
|---|---|---|---|
| `independants.correction_couples` | 0,894 | −0,15 / −0,32 | Forfait d'imposition commune des couples d'indépendants |
| `epargne.taux_emploi_carriere` | 0,75 | +0,01 / +0,26 | Épargne obligatoire : part de la carrière en emploi |
| `quotient.conjugal` | 7 M de couples, 25 % à un revenu… | +0,09 / +0,19 | Données d'entrée du calcul des gains de l'imposition commune |
| `inactifs.rui_moyen_chomeurs` | 1 RUI | +0,08 / +0,17 | Choix du programme |
| `carbone_importe.intensite_kg_par_euro`, `part_importee` | 0,543 ; 64 % | −0,04 / −0,12 | Assiette de l'accise carbone aux frontières |
| `inactifs.revenu_annulant_rui` | 2 000 €/mois | +0,05 / +0,10 | Choix du programme |
| `quotient.part_enfants_parent_imposable` | 85 % | +0,05 / +0,10 | Donnée d'entrée |
| `logement.amortissement_loyers` | 85 % | +0,05 / +0,09 | Donnée d'entrée |
| `ia.plafond_taches_automatisables`, `macro.part_capital_nouveau` | 40 % ; 75 % | −0,02 / −0,07 | Hypothèses de comportement |
| `securite_sociale.postes_absents` | Sécurité sociale 2026 | +0,03 / +0,07 | Donnée (à rattacher au document d'origine) |
| `tva.seuils_profils` | 0 / 20 / 32 / 50 k€ | +0,03 / +0,05 | Choix du programme |

Hors champ : `transition.taux_implicite_fichier_source` (taux technique du fichier de cohortes) et quatre durées
entières que +10 % ne sait pas perturber (`is_investissement.categories/*/duree`,
`tva_sante_long_terme.annees_plein_effet`).

## Tondelier et Mélenchon

Tous leurs paramètres sans source sont des chiffrages de mesures, dont la note donne le calcul. Aucun ne déplace le
déficit de plus de 0,03 point pour 10 % : Tondelier, 3 au-dessus de 0,01 point (le plus lourd, la part de la marge
absorbée par la hausse du SMIC, +0,01 / +0,03) ; Mélenchon, 10 au-dessus de 0,01 point (le plus lourd, le grand âge,
+0,02 / +0,05). Rien à ajouter : c'est de l'estimation documentée, pas une hypothèse cachée.

## Ce qui reste

1. Décisions d'Adrien sur la liste « à écrire en décisions » (statut DECISION et une phrase de motif chacun).
2. Périmètre du besoin de financement des collectivités (Maastricht : APUL entières ou collectivités seules).
3. Périmètre des 8 Md€ d'apprentissage.
