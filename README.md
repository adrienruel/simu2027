# Moteur de simulation — « Écologie de droite »

Refonte du classeur `Chiffrage_programme_complet_v235.xlsx` en moteur Python vérifiable.
Cahier des charges : `Refonte_outil_de_simulation.md` (projet).

## Lancer

```
pip install pyyaml pytest
python -m pytest
```

## Organisation

| Dossier | Contenu |
|---|---|
| `parametres/parametres.yaml` | Fichier de paramètres unique : valeur (par scénario si besoin), unité, année des euros, statut, source |
| `moteur/parametres.py` | Chargement et validation (source obligatoire si SOURCE, année obligatoire pour un montant, scénarios complets) |
| `moteur/unites.py` | Seul endroit où l'on convertit en euros de 2026 ; une double conversion lève une erreur |
| `moteur/impot_unique.py` | Barème de l'impôt unique (personne seule) |
| `tests/` | Tests automatiques |
| `docs/journal.md` | Journal des décisions et des écarts avec la v235 |

## Règles

- Une hypothèse sans source est prise prudente ; le prudent est publié.
- Prudent toujours affiché avant et après la clause de trajectoire.
- Aucune indexation sur l'inflation (RUI, socle, SMIC suivent la croissance).
- Euros constants de 2026 ; économie de 2026 placée en 2029 ; une seule conversion.
- Chaque changement de résultat est commité avec sa raison.

## Étapes

1. **Moteur budgétaire identique à la v235** (Total et trajectoire, 4 scénarios, à 0,01 Md€) — *en cours : socle posé*
2. Paramètres complets (1 278 du registre) et tests de la partie 6
3. Microsimulation OpenFisca
4. Bloc emploi unifié et incertitude
5. Sorties (Excel généré, site, manifeste)
