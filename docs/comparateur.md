# Le comparateur en ligne

Page : https://claude.ai/artifact/LYqmGYBCyXpD7VpwM1mCy7 (slug `9e4fbe29-b427-46b2-a5d6-a3aae6214ba2`, privée).
Refaite le 19/11/2026 en huit onglets. Le dossier `comparateur/` est la copie de son code ; la page en ligne
reste la référence (une modification faite à la main dans la page doit être recopiée ici).

## Onglets

| Onglet | Contenu | Jeux de données |
|---|---|---|
| Vue d'ensemble | Chiffres clés du programme choisi (vert ou rouge contre le statu quo, rang sur l'écart de solde primaire), résumé avec ce qui joue pour et contre, écart par poste, liste des mesures prises en compte | traj, ecologie, redistribution, ecarts, mesures |
| Comparer | Deux programmes côte à côte (18 indicateurs, colonne B − A, statu quo), six courbes superposées, écart par poste | traj, demographie, redistribution, ecologie, ecarts |
| Économie | Synthèse de tous les programmes, croissance (écart de PIB, croissance annuelle), déficit, dette, solde primaire, dépenses et recettes, décomposition du déficit | traj, decomposition |
| Emploi | Chômage, emploi, taux d'emploi et d'activité, emploi mesure par mesure | traj, emploi_canaux |
| Population | Naissances, décès, soldes naturel et migratoire, fécondité, vieillissement, âge médian, population par âge, pauvreté 2029-2050, déciles au fil des années | demographie, pyramide, redistribution, redistribution_deciles, couverture_micro |
| Ménages types | Revenu disponible de onze ménages types, actuel et avec chaque programme, mesure par mesure | menages_types, menages_mesures, couverture_micro |
| Écologie | Émissions, empreinte, budgets carbone, effet des mesures, secteurs, mesures | ecologie, ecologie_mesures |
| Fiabilité et méthode | Annonces contre chiffrage, variantes de la dette, incertitude, lectures qui pèsent le plus, méthode | annonces, dette_variantes, incertitude, lectures |

Règle de publication de la micro : déciles et totaux des ménages types seulement pour les programmes dont au moins
80 % du budget « ménages » est codé (`outils/couverture_micro.py`) ; sinon la page montre la part codée et, pour les
ménages types, l'effet des seules mesures codées, une par une.

## Fichiers

- `index.html` : tous les textes, dont les résumés des candidats (`<div class="resume-prog" data-prog="<libellé>">`,
  chiffres du scénario prudent en 2037, à mettre à jour à la main quand les résultats changent).
- `commun.js` (filtres, onglets, courbes, barres), puis un script par onglet : `ensemble.js`, `comparer.js`,
  `economie.js`, `emploi.js`, `population.js`, `menages.js`, `ecologie.js`, `fiabilite.js`.
- Dans l'artifact, ces fichiers sont les documents `files/<nom>` (champ `text`), et chaque jeu de données un document
  `datasets/<id>`. Chaque écriture doit rester sous 64 Ko : `index.html` (≈ 125 Ko) se modifie par remplacements.

## Mettre à jour les données

1. `python -m outils.export_comparaison`, `python -m outils.export_demographie`,
   `python -m outils.export_menages_types` (OpenFisca, ≈ 8 minutes), et les exports de l'incertitude, de la dette,
   des lectures et de la couverture si le modèle a changé.
2. Envoyer les CSV comme fichiers de l'artifact (`upload_asset`).
3. Dans `datasets`, `update` de `source.url`, `updated` et `edit` (avec `ifVersion`) : traj, ecarts, mesures,
   annonces, emploi_canaux, ecologie, ecologie_mesures, redistribution, redistribution_deciles, incertitude,
   decomposition, dette_variantes, demographie, pyramide, couverture_micro, lectures, menages_types, menages_mesures.
4. Revoir les chiffres cités dans les résumés.

## Ménages types (`outils/export_menages_types.py`)

Les ménages de `parametres/menages_types.yaml`, plus un jeune salarié au SMIC de 24 ans, passent par les mêmes
réformes OpenFisca et les mêmes règles ajoutées après OpenFisca que la population synthétique
(`outils/openfisca_mesures.py`). Différences : recours complet aux aides, nationalité française, personne ne perd le
RSA par la durée, seul le jeune salarié cotise à une capitalisation obligatoire, pensions et capitalisation à l'effet
de 2032, locataires du parc privé en zone 2. Non compté : emploi, prix, services publics, assurance chômage,
patrimoine et successions, mesures non codées.

## Démographie (`outils/export_demographie.py`)

Relit la population que le moteur calcule pour chaque programme (`moteur/migrations.population_programme`) et en tire
les flux : décès et solde migratoire de l'Insee pour le statu quo, naissances par l'équation de la population ;
écarts d'un programme par l'écart de population à 0 an, la variation migratoire déclarée et le reste pour les décès.
Les écarts commencent en 2030 (les entrées de 2028 et 2029 arrivent au 1er janvier 2030) : flux publiés à partir de
2030. La fécondité est l'indicateur du scénario de l'Insee plus l'effet du canal commun des naissances.
