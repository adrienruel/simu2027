# Journal des décisions et des écarts

## 28 octobre 2026 — Socle

- Structure du dépôt, fichier de paramètres unique, conversion d'unités centralisée, barème de l'impôt unique.
- Barème 0 / 17,9 / 57 / 66 % (seuils 12 500, 24 000, 32 000 € de coût employeur) : retrouve les profils types v232 (SMIC 168 €/mois, médian 1 129 €/mois).

## 28 octobre 2026 — Référence v235 et bloc comptable de la trajectoire

- **La copie du classeur dans le projet est un export texte : valeurs seulement**, sans formules ni adresses de cellules. Elle est découpée en une feuille par fichier (`reference/v235/`, outil `outils/decouper_export.py`) et les cibles de Total et Trajectoire sont extraites en CSV (`reference/cibles/`, outil `outils/extraire_cibles.py`).
- **Bloc comptable de la trajectoire reproduit à l'identique** (écart < 10⁻¹¹ Md€) : dépenses, solde, solde primaire, dette, dette/PIB, solde de Maastricht. Déficits publiés retrouvés : 4,67 / 3,81 / 2,31 %.
- Mécanisme retrouvé : dette(t) = dette(t−1) − solde − participations de l'État remises au fonds ; ces participations valent 86,9 Md€ en 2047 et 48,1 en 2048, soit 135 Md€ (« après décote »).
- Maastricht : (solde en intérêts réels − 1,8 % × dette de l'année précédente) / PIB.

## 28 octobre 2026 — Recettes : impôt des salariés et des retraités

Reproduits à moins de 0,01 Md€ (outil `outils/arbre.py` pour lire les formules de la v235) :
- **Ligne 4, impôt unique du privé** : 452,84 Md€. Passage des classes de 2024 en euros de 2026 par interpolation log entre classes voisines (`moteur/distribution.py`).
- **Ligne 6, impôt unique du public** : 140,08 Md€. Coût employeur aligné sur le privé (−13,5 % en moyenne pondérée des versants).
- **Ligne 5, impôt des retraités en croisière** : 24,10 Md€. Épargne obligatoire sur 43 ans, rente (moitié viagère, Gompertz), socle dégressif exonéré, gains à la flat tax.
- Facteur de passage des recettes de 2024 : 1,039456 (PIB en valeur 2025 × volume 2026 × déflateur 2026), et non 1,039 arrondi.

## 28 octobre 2026 — Recettes statiques complètes (Total!B17)

**Les recettes statiques du nouveau système sont reproduites : 1 167,767 Md€, écart 0,003 €.**
Lignes 2 (IS), 3 (TVA et accises), 4-6 (impôt unique), 7 (dividendes), 8 (successions), 9 (contribution),
15 (accises des entreprises et accise de transition), 16 (indépendants), 19 (revenus du capital), 20 (bailleurs).
Modules ajoutés : `tva.py` (accises calculées depuis le prix du carbone, taux effectifs par profil),
`systeme_actuel.py` (net actuel par classe : RSA, prime d'activité, APL, taxe foncière),
`recettes/entreprises.py`, `recettes/independants.py`, `recettes/autres.py`, `recettes/total.py`.

## Constats sur la v235 (pour Adrien)

- **Indépendants : pivot salaire / société périmé (≈ 0,9 Md€).** Le montage « salaire jusqu'au pivot, reste par la société » prend comme pivot Total!B91 = 45 000 €, ancien début du taux de 66 %. Depuis la v227, le 66 % commence à 32 000 €. Avec un pivot à 32 000 €, l'impôt des indépendants baisse de 0,92 Md€ : la v235 le surestime d'autant. Le pivot devrait être relié au seuil du 66 %, pas à une cellule de position fixe.
- **Entreprises déficitaires (bloc 5) : allègement périmé (0,28 Md€).** Le bénéfice des entreprises qui passent en positif est calculé avec la suppression de la TVA non déductible (U3), qui n'est plus supprimée depuis la v231. L'allègement réel est la fin des impôts de production (≈ 7 400 € pour la petite classe, contre 7 470 € de TVA) : l'ordre de grandeur tient, mais le libellé et la cellule sont faux.
- **Taxe foncière actuelle des bas salaires** : saisie à 0 pour les sept premières classes du privé (net avant aides ≤ 17 956 €), calculée pour toutes les classes d'agents publics. Règle implicite, non documentée.
- **Prime d'activité des agents** : barème simplifié (230 € au plus, Fonctionnaires B71-B73), alors que le privé utilise le barème sourcé d'avril 2026. Sans effet aujourd'hui (aucun agent sous 35 000 €).
- **Prix du carbone** : 256 € et les trois hausses (2 %, 0,9 %, 2,1 %) sont écrits dans les formules Barème TVA!B56 et E56, que l'audit v233 n'a pas sortis.
- **Facteurs d'euros multiples** : Indépendants!B40 = 1,0395 saisi à part, à côté du facteur de recettes (1,039456) et des facteurs de salaires.
- **Accise de transition, à vérifier** : elle est calée sur « ancienne TVA − nouvelle TVA » (Barème TVA!B181-B182), libellé « assiettes 2024 », puis multipliée par le facteur 2024 → 2026. Or les deux TVA des salariés y sont calculées sur les distributions de 2026. Le mélange d'années pourrait décaler le calage « recettes égales » de quelques milliards : à trancher en définissant l'année de chaque terme.
- **Profil import/marge** : le plafond B63 est libellé « € de coût employeur » mais appliqué au net actuel.
- **Paramètres de consommation** (2,05 et 0,92) rangés dans Total!N29:N30, sur les lignes « Sous-total régalien » et « Éducation nationale ».


- **RUI des agents publics** (Fonctionnaires, colonne AR) : la part de RUI s'éteint à 12 500 € de coût employeur, contre le coût d'un SMIC à temps plein dans le privé. Sans effet aujourd'hui (aucun agent sous 35 000 €), mais incohérent.
- **Contribution de transition** (Total!B126) : retirée de l'épargne des salariés du privé (colonne BB), pas de celle des agents publics (colonne BD). Sans effet tant qu'elle vaut 0 dans le budget statique ; à vérifier là où la clause l'active.
- **Taux d'épargne des agents** calculé sur le coût aligné, celui du privé sur le coût d'origine : cohérent, noté pour mémoire.


- **Feuille Résumé, libellé périmé** : « Tranche 3 (24 000 à 45 000 €) » à 57 %, alors que le barème de la feuille Total passe à 66 % dès 32 000 €. Le calcul est juste, le libellé faux. Même chose pour « 7 tranches » : les tranches 4 à 7 sont toutes à 66 %.
- **Coût du SMIC** : le paramètre de la v235 est 1 930 €/mois (Total) ; le profil type de l'état du programme utilise 1 979 €/mois. À éclaircir.

## Points à éclaircir à l'étape 1 (lecture de la v235)

- **Coût du SMIC** : 1 979 €/mois (23 750 €/an, profil type v232) contre 1 930 €/mois (juin 2026) cité dans l'audit v235. Lequel sert à quoi ?
- **Couples et enfants** : « couples imposés ensemble, demi-part par enfant plafonnée à 1 000 € » — mécanique exacte du quotient à préciser.
- **État du programme en v232** : les résultats publiés ont bougé en v233-v235 (déficits, chômage, profils). Les valeurs de référence des tests seront celles de la v235.
