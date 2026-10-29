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

## À trancher

| Paramètre | Retenu | Ce que disent les sources | Effet si on prend la valeur prudente |
|---|---|---|---|
| macro.taux_long_terme (taux nominal de long terme de la dette) | 3,3 % | OAT à 10 ans à 4,01 % le 24 juillet 2026, plus haut depuis 2008 ; Bund 3,22 % | à 4,0 % : déficit 2037 3,29 % au lieu de 2,31 % ; dette 2050 134 % au lieu de 117 % |
| calendrier.inflation | 1,8 % | Banque de France (sept. 2026) : 1,9 % en 2027, 1,6 % en 2028 ; cible BCE 2 % | à 1,6 % : déficit 2037 +0,13 point, 2050 +0,4 point |
| consommation.exposant et coefficient (2,05 × revenu^0,92) | v235 | Insee Première n° 1815 : taux d'épargne de 2,7 % (1er quintile) à 28,4 % (5e) en 2017 ; la fonction du modèle donne 3 % à 17 % | recalée sur l'Insee (0,79 et 7,18) : déficit +0,17 à +0,19 point |
| tva.prix_carbone_2024 | 256 € (traité comme un prix de 2024) | Quinet III, avis du CS ESE du 21 mai 2025 : 256 € **de 2023** pour **2025**, puis +3,2 % par an (300 € en 2030) | la valeur est la bonne, l'année et la trajectoire non ; à reprendre avec le module carbone |

Les trois premières ensemble : déficit publié 4,88 % / 4,53 % / 3,66 % en 2029 / 2032 / 2037,
dette 148 % du PIB en 2050, déficit durablement sous 3 % en 2054 seulement.

## Sources consultées

- Banque de France, projections macroéconomiques intermédiaires, septembre 2026.
- Insee Première n° 2032 (2025), enfants vivant en famille.
- Insee Première n° 1815 (septembre 2020), épargne et consommation par niveau de vie.
- Insee, bilan démographique 2025 (population au 1er janvier 2026 : 69,1 millions).
- France Stratégie, avis du CS ESE du 21 mai 2025 sur la valeur de l'action pour le climat.
- ABC Bourse, 29 juillet 2026 : OAT à 10 ans au-dessus de 4 %.
- CAE, Focus n° 124 (octobre 2025) : taux apparent de la dette 2,0 % en 2025, OAT 10 ans 3,5 % à l'époque.
