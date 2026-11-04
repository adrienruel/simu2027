# Simulation des programmes — présidentielle 2027

Premier programme chiffré : « Écologie de droite ».

Refonte du classeur `Chiffrage_programme_complet_v235.xlsx` en moteur Python vérifiable.
Cahier des charges : `Refonte_outil_de_simulation.md` (projet).

## Lancer sous Windows

Double-cliquer sur `lancer.bat`. La première fois, il crée un environnement Python local (`.venv`) et installe les
bibliothèques (Python 3.10 ou plus requis : https://www.python.org/downloads/, cocher « Add python.exe to PATH »).
Menu : résumé rapide, tableau de bord (recalculé puis ouvert dans le navigateur), tout recalculer, tests.

## Lancer (ligne de commande)

```
pip install pyyaml pytest openpyxl
pip install openfisca-france   # seulement pour régénérer les tables du système actuel
python -m pytest
python -m moteur.simulation   # déficits des quatre scénarios, avant et après la clause
python -m outils.cibles_crise  # (LibreOffice) recalcule la crise de la v235 en pleine précision
python -m outils.openfisca_actuel   # tables OpenFisca du système actuel (privé, public)
python -m outils.openfisca_menages  # ménages types, système actuel
python -m moteur.menages_types      # ménages types : actuel contre nouveau
python -m moteur.sensibilite        # sorties/sensibilite.json
python -m moteur.incertitude        # sorties/incertitude.json
python -m outils.tableau_de_bord  # sorties/tableau_de_bord.html (avec l'attribution par mesure)
python -m outils.population_insee <dossier>  # projections de l'Insee (xlsx) → parametres/donnees/population_insee_2026_*.csv
python -m outils.valeur_enfant      # soutien par enfant, système actuel (OpenFisca)
python -m outils.participation      # gain à travailler d'un inactif, système actuel (OpenFisca)
python -m outils.levier_is          # grille taux de l'IS × déduction de l'investissement
python -m outils.leviers            # variantes et paquets chiffrés (sorties/leviers.json, ~20 min)
```

Relecture indépendante : `docs/relecture.md`.

## Organisation

| Dossier | Contenu |
|---|---|
| `parametres/commun/` | Hypothèses communes à tous les programmes (`economie.yaml`) et options du modèle (`options.yaml`) : valeur (par scénario si besoin), unité, année des euros, statut, source |
| `programmes/<programme>/` | Un dossier par programme : ses paramètres (qui ne peuvent pas redéfinir une hypothèse commune), son registre des mesures, ses économies datées. Architecture : `docs/architecture.md` |
| `moteur/parametres.py` | Chargement et validation (source obligatoire si SOURCE, année obligatoire pour un montant, scénarios complets) |
| `moteur/unites.py` | Seul endroit où l'on convertit en euros de 2026 ; une double conversion lève une erreur |
| `moteur/impot_unique.py` | Barème de l'impôt unique (personne seule) |
| `moteur/trajectoire.py` | Bloc comptable de la trajectoire 2029-2073 (solde, dette, Maastricht) |
| `reference/v235/` | Export de la v235, une feuille par fichier (valeurs seules) |
| `reference/cibles/` | Valeurs cibles de Total et Trajectoire, que le moteur doit reproduire |
| `outils/` | Extraction de la référence ; `recalcul.py` recalcule la v235 dans LibreOffice avec des cellules modifiées |
| `tests/` | Tests automatiques |
| `moteur/demographie.py` | Population année par année (Insee 2026), emploi par âge, effet du programme sur la natalité, crèches |
| `moteur/ancien_systeme.py` | Pensions de l'ancien système génération par génération, âge légal à 65 ans |
| `moteur/taux_effectifs.py` | Taux effectif moyen d'imposition (Devereux et Griffith) pour la localisation |
| `moteur/emploi_canaux.py` | Bloc emploi unifié : canaux, rendements décroissants, gain par emploi |
| `docs/sourcage.md` | Paramètres sourcés, corrigés, et décisions sur les hypothèses |
| `docs/demographie.md`, `docs/leviers.md`, `docs/levier_is.md`, `docs/bloc_emploi.md` | Notes de méthode et résultats |
| `docs/journal.md` | Journal des décisions et des écarts avec la v235 |

## Règles

- Une hypothèse sans source est prise prudente ; le prudent est publié.
- Prudent toujours affiché avant et après la clause de trajectoire.
- Aucune indexation sur l'inflation (RUI, socle, SMIC suivent la croissance).
- Euros constants de 2026 ; économie de 2026 placée en 2029 ; une seule conversion.
- Chaque changement de résultat est commité avec sa raison.

## Étapes

1. **Moteur budgétaire identique à la v235** (Total et trajectoire, 4 scénarios, à 0,01 Md€) — *fait : crise, prudent, médian, optimiste reproduits ; aucune valeur lue dans la v235*
2. Paramètres complets (1 278 du registre) et tests de la partie 6
3. Microsimulation OpenFisca — *fait : système actuel, ménages types, réforme codée dans OpenFisca (concordance au centime)*
4. Bloc emploi unifié et incertitude — *fait ; population annuelle, ancien système par génération, prime de taux, participation des inactifs*
5. Sorties (Excel généré, site, manifeste)
