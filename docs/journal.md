# Journal des décisions et des écarts

## 28 octobre 2026 — Socle

- Structure du dépôt, fichier de paramètres unique, conversion d'unités centralisée, barème de l'impôt unique.
- Barème 0 / 17,9 / 57 / 66 % (seuils 12 500, 24 000, 32 000 € de coût employeur) : retrouve les profils types v232 (SMIC 168 €/mois, médian 1 129 €/mois).

## 28 octobre 2026 — Référence v235 et bloc comptable de la trajectoire

- **La copie du classeur dans le projet est un export texte : valeurs seulement**, sans formules ni adresses de cellules. Elle est découpée en une feuille par fichier (`reference/v235/`, outil `outils/decouper_export.py`) et les cibles de Total et Trajectoire sont extraites en CSV (`reference/cibles/`, outil `outils/extraire_cibles.py`).
- **Bloc comptable de la trajectoire reproduit à l'identique** (écart < 10⁻¹¹ Md€) : dépenses, solde, solde primaire, dette, dette/PIB, solde de Maastricht. Déficits publiés retrouvés : 4,67 / 3,81 / 2,31 %.
- Mécanisme retrouvé : dette(t) = dette(t−1) − solde − participations de l'État remises au fonds ; ces participations valent 86,9 Md€ en 2047 et 48,1 en 2048, soit 135 Md€ (« après décote »).
- Maastricht : (solde en intérêts réels − 1,8 % × dette de l'année précédente) / PIB.

## Constats sur la v235 (pour Adrien)

- **Feuille Résumé, libellé périmé** : « Tranche 3 (24 000 à 45 000 €) » à 57 %, alors que le barème de la feuille Total passe à 66 % dès 32 000 €. Le calcul est juste, le libellé faux. Même chose pour « 7 tranches » : les tranches 4 à 7 sont toutes à 66 %.
- **Coût du SMIC** : le paramètre de la v235 est 1 930 €/mois (Total) ; le profil type de l'état du programme utilise 1 979 €/mois. À éclaircir.

## Points à éclaircir à l'étape 1 (lecture de la v235)

- **Coût du SMIC** : 1 979 €/mois (23 750 €/an, profil type v232) contre 1 930 €/mois (juin 2026) cité dans l'audit v235. Lequel sert à quoi ?
- **Couples et enfants** : « couples imposés ensemble, demi-part par enfant plafonnée à 1 000 € » — mécanique exacte du quotient à préciser.
- **État du programme en v232** : les résultats publiés ont bougé en v233-v235 (déficits, chômage, profils). Les valeurs de référence des tests seront celles de la v235.
