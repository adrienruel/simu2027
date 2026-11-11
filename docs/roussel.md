# Programme de Fabien Roussel (Parti communiste français) : chiffrage (11 novembre 2026)

Code : `programmes/roussel/` ; fiche : `mesures.yaml` (45 mesures et leur traitement) ; tests : `tests/test_roussel.py`.

## Sources

Pas de programme présidentiel 2027 publié (candidature validée le 6 septembre 2026). Sources : université d'été du
PCF (22/08/2026), Fête de l'Humanité (2025 et 12/09/2026), « Pacte pour l'avenir de la France » (2025), pages
thématiques de pcf.fr, recensées par programme-candidat.fr, quivoter2027.com, swipetonvote.fr et france-vote.fr ;
votons-2027.fr cite encore le programme de 2022. Plusieurs mesures datent de 2025 (CSG des retraites, ASPA à
1 400 €, indexation des pensions sur les salaires) : **à confirmer** à la publication du programme.

## Méthode

Mêmes règles que les autres programmes : aucune recette annoncée reprise (60 Md€ de contribution des banques et
assurances, 211 Md€ d'aides « réorientées ») ; les mesures communes avec L'Avenir en commun (ISF, taxe Zucman,
« 100 % Sécu », logement public, garantie d'emploi, SMIC à 1 700 €, retraite à 60 ans) reprennent les estimations
et le calendrier de Mélenchon, pour que les deux programmes soient jugés de la même façon.

**32 heures sans perte de salaire** (nouveau dans le modèle) : −8,6 % d'heures par salarié au même salaire.
- Privé : coût horaire +9,4 %, réduit des gains de productivité (20 à 40 % de la baisse d'heures) ; une partie des
  heures est rendue par des embauches de partage du travail (25 à 40 %, ≈ 35 % lors des 35 heures, Dares 2005) ; le
  reste est de la production en moins (part marchande du PIB ≈ 75 %). Emplois perdus par le coût horaire :
  élasticité −0,1 à −0,5. Pas d'allègements de cotisations (le programme n'en prévoit pas, à la différence des
  35 heures).
- Fonction publique : embauches pour garder le service (40 à 70 % des heures perdues), avec l'éviction commune.
- Le noyau accepte désormais un PIB en plus ou en moins hors emploi (`ProgrammeSimple.pib_en_plus`).

## Résultats

| Prudent | 2029 | 2032 | 2037 |
|---|---|---|---|
| Déficit (% du PIB) ; statu quo 5,9 / – / 9,5 | 9,7 | 16,8 | 29,6 |
| Solde primaire contre le statu quo (points) | −3,7 | −7,5 | −9,1 |
| PIB contre le statu quo | +0,4 % | −2,7 % | −4,5 % |
| Chômage (%) ; statu quo 8,3 en 2037 | 7,7 | 7,5 | 8,3 |

Médian 2037 : déficit 22,3 %, PIB −2,7 % ; optimiste : 17,5 %, −1,1 %. Emploi en 2037 (prudent) : −670 000, surtout des
seniors partis à la retraite (−520 000) ; 32 heures : −380 000 par le coût, +520 000 embauches de partage,
+400 000 embauches publiques moins autant d'emplois privés évincés.

Postes principaux en 2037 (prudent, Md€) : retraite à 60 ans −48, 32 heures (production perdue) −43, pensions
indexées sur les salaires −32 (et la montée continue), « 100 % Sécu » −31, CSG des retraites −24, rail −16, SMIC −13
net des recettes sur les hausses, carburant à 1,50 € −13 ; recettes : taxe Zucman +5, revenus des entreprises
nationalisées +8,5, ISF +2,7. Les nationalisations (≈ 250 Md€ en prudent) passent par la dette, pas par le déficit.

Émissions (2037) : mesures −0,8 Mt en prudent (rail, transports gratuits, véhicules, moins le carburant bloqué),
−4,1 en médian ; effet de l'activité −5,8 Mt en prudent (PIB plus bas).

## Limites

1. Programme non publié : sources de seconde main, mesures de 2025 gardées.
2. 32 heures : aucun précédent de cette ampleur sans allègements ; résultats très sensibles aux gains de productivité
   et aux embauches (paramètres `roussel_temps_travail.trente_deux_heures`).
3. Sortie du marché européen de l'électricité (prix −30 à −50 %) et fonds de 500 Md€ par les banques nationalisées :
   hors solde, seule la baisse des dividendes est comptée.
