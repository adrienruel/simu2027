# Sourçage des paramètres

Ordre de travail : les hypothèses qui pèsent le plus sur le déficit d'abord (`moteur/sensibilite.py`,
tableau de bord, « Les hypothèses qui pèsent le plus »).

Règles :
- une valeur publiée par une source officielle remplace l'hypothèse (statut SOURCE) ; l'ancienne valeur reste
  dans le champ `v235`, que les tests de reproduction utilisent (`Parametres(reference="v235")`) ;
- une hypothèse qu'une source encadre sans la fixer garde le statut HYPOTHESE avec un champ `source`
  (« encadrée ») ; si la valeur retenue n'est pas la plus prudente de la fourchette, c'est à trancher.

## Corrigés (29 octobre 2026)

| Paramètre | v235 | Nouveau | Source | Effet sur le déficit publié |
|---|---|---|---|---|
| rui_complements.enfants | 11 500 000 | 10 724 000 | Insee Première n° 2032 : 13 882 000 mineurs en famille (2023), dont 3 158 000 en famille monoparentale | ensemble des deux : +0,02 point |
| rui_complements.enfants_parent_isole | 2 500 000 | 3 158 000 | idem | (inclus ci-dessus) |
| macro.taux_reference_is | 25 % | 25 % (sourcé) | Article 219 du CGI | aucun |

## Décisions d'Adrien du 29 octobre 2026

| Paramètre | v235 | Retenu | Raison |
|---|---|---|---|
| macro.taux_long_terme | 3,3 % | **4,0 %** | Niveau du marché (OAT à 10 ans, juillet 2026), avant tout effet des réformes |
| macro.baisse_spread | 0 / 0 / 0,2 / 0,4 point | inchangé, désormais documenté | L'effet des réformes sur les taux est incertain : aucun en crise et en prudent, un quart de l'écart avec le Bund (≈ 0,8 point) dans le médian, la moitié dans l'optimiste |
| calendrier.inflation | 1,8 % | 1,8 % (décision) | Entre la Banque de France (1,6 % en 2028) et la cible de la BCE (2 %) |
| consommation.exposant et coefficient | 0,92 et 2,05 | **0,7914 et 7,184** | Recalés sur les quintiles de l'Insee (IP n° 1815) ; à recaler sur des ménages à l'étape OpenFisca |

### Résultats après ces décisions (déficit publié, clause comprise)

| | 2029 | 2032 | 2037 | Dette 2050 | Durablement sous 3 % |
|---|---|---|---|---|---|
| Crise | 4,87 % | 4,46 % | 3,92 % | 155 % | 2057 |
| **Prudent** | **4,86 %** | **4,46 %** | **3,51 %** | **139 %** | **2053** |
| Médian | 4,86 % | 4,46 % | 3,51 % | 99 % | 2039 |
| Optimiste | 4,41 % | 2,94 % | 1,27 % | 56 % | 2032 |

Prudent avant clause : 5,42 % / 5,85 % / 5,33 %. (v235 : 4,67 % / 3,81 % / 2,31 % ; avant clause 5,23 % / 5,18 % / 4,07 %.)

## Reste à reprendre

| Paramètre | Constat |
|---|---|
| tva.prix_carbone_2024 | 256 € est la valeur de l'action pour le climat **de 2025, en euros de 2023** (Quinet III, avis du CS ESE du 21 mai 2025), puis +3,2 % par an (300 € en 2030) ; le modèle la traite comme un prix de 2024 et ne la fait pas monter |

## Sources consultées

- Banque de France, projections macroéconomiques intermédiaires, septembre 2026.
- Insee Première n° 2032 (2025), enfants vivant en famille.
- Insee Première n° 1815 (septembre 2020), épargne et consommation par niveau de vie.
- Insee, bilan démographique 2025 (population au 1er janvier 2026 : 69,1 millions).
- France Stratégie, avis du CS ESE du 21 mai 2025 sur la valeur de l'action pour le climat.
- ABC Bourse, 29 juillet 2026 : OAT à 10 ans au-dessus de 4 %.
- CAE, Focus n° 124 (octobre 2025) : taux apparent de la dette 2,0 % en 2025, OAT 10 ans 3,5 % à l'époque.
