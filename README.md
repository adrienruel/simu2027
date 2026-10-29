# Moteur de simulation — « Écologie de droite »

Refonte du classeur `Chiffrage_programme_complet_v235.xlsx` en moteur Python vérifiable.
Cahier des charges : `Refonte_outil_de_simulation.md` (projet).

## Lancer

```
pip install pyyaml pytest openpyxl
python -m pytest
python -m moteur.simulation   # déficits des quatre scénarios, avant et après la clause
python -m outils.cibles_crise  # (LibreOffice) recalcule la crise de la v235 en pleine précision
python -m outils.tableau_de_bord  # sorties/tableau_de_bord.html (avec l'attribution par mesure, ~20 s)
```

## Organisation

| Dossier | Contenu |
|---|---|
| `parametres/parametres.yaml` | Fichier de paramètres unique : valeur (par scénario si besoin), unité, année des euros, statut, source |
| `moteur/parametres.py` | Chargement et validation (source obligatoire si SOURCE, année obligatoire pour un montant, scénarios complets) |
| `moteur/unites.py` | Seul endroit où l'on convertit en euros de 2026 ; une double conversion lève une erreur |
| `moteur/impot_unique.py` | Barème de l'impôt unique (personne seule) |
| `moteur/trajectoire.py` | Bloc comptable de la trajectoire 2029-2073 (solde, dette, Maastricht) |
| `reference/v235/` | Export de la v235, une feuille par fichier (valeurs seules) |
| `reference/cibles/` | Valeurs cibles de Total et Trajectoire, que le moteur doit reproduire |
| `outils/` | Extraction de la référence ; `recalcul.py` recalcule la v235 dans LibreOffice avec des cellules modifiées |
| `tests/` | Tests automatiques |
| `parametres/registre_lois.yaml` | Registre des mesures séparables et façon de les neutraliser (attribution) |
| `docs/sourcage.md` | Paramètres sourcés, corrigés, et décisions sur les hypothèses |
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
3. Microsimulation OpenFisca
4. Bloc emploi unifié et incertitude
5. Sorties (Excel généré, site, manifeste)
