# Reprise : phases L, M et N (18 et 19/11/2026)

Ce fichier dit ce qui a été fait, où, et ce qui reste, pour reprendre le travail sans relire la conversation. Le
détail chiffré est dans `docs/journal.md` (entrées du 18/11/2026).

## Branches

| Branche | Phase de la roadmap | Contenu | Dans `main` |
|---|---|---|---|
| `phase-l` | 4 | Dépenses de chômage du programme, couverture de la micro, incidence des entreprises | oui |
| `phase-m` | 5 (et 7.1, 7.3) | Décisions d'Adrien : générosité des allocations, prime d'activité, retour de l'incidence | oui |
| `phase-n` | 8 et 9 | Backtest de l'assurance chômage, sources, veille des programmes, page publique | oui |
| `reprise-phases-l-n` | — | Ce fichier | non |

## Ce qui a changé dans le modèle

### Phase L — roadmap 4

- **4.1 Dépenses sensibles au chômage** (`docs/depenses_chomage.md`).
  - Les blocs chômage et pauvreté suivent les chômeurs du programme : `moteur/noyau.py`, contexte `chomeurs_depenses`.
  - L'allocation évitée sort de la valeur d'un emploi des canaux.
  - Paramètres : `emploi.depenses_chomage_programme`, `emploi.part_allocation_assurance_chomage`.
- **4.2 Micro** : déciles publiés seulement si la micro couvre 80 % du budget « ménages ».
  - Code : `outils/couverture_micro.py`. Paramètre : `publication.seuil_couverture_deciles`.
  - Plus-values et apprentis ajoutés à `outils/population_synthetique.py`.
- **4.3 Incidence des entreprises** : `moteur/incidence_entreprises.py`, `outils/export_incidence.py`.

### Phase M — roadmap 5

- **5.3** : l'horizon des courbes reste 2060.
- **5.4** : le coût d'un chômeur dépend de la générosité du programme.
  - Paramètre `emploi.generosite_programme`.
  - Fonction `generosite` dans `moteur/programme_simple.py`.
  - Mesures marquées `volume: true` exclues.
- **5.5** : prime d'activité des emplois en plus, ≈ 2 140 €.
  - Paramètre `emploi.prime_activite_emplois`, fonction `noyau.ppa_par_emploi`.
- **5.6** : prélèvements des ménages sur les revenus de l'incidence, sans double compte avec l'offre.
  - Paramètres `entreprises.incidence_retour_budget` et `entreprises.retour_dividendes`.
  - Avec 7.3, la part des salaires monte à la vitesse de l'offre.
- **5.7** : les 91,2 Md€ de charge d'intérêts 2027 sont ceux des APU (État seul : 72,9 Md€). Note corrigée, valeur
  inchangée.

### Phase N — roadmap 8 et 9

- **8.3** : `outils/backtests.ampleur_assurance_chomage`. La lecture de Lisnard est 1,7 fois l'effet que justifie sa
  réforme.
- **8.1** : huit paramètres sourcés avec adresse. Il en reste 158 dans `parametres/sources/sans_url.txt`.
- **9.2** : `outils/veille_programmes.py` et `programmes/veille.yaml`.
- **9.3** : `outils/page_comparateur.py`, qui écrit `sorties/comparateur.html`.

## Ce qui reste

| Point | Pourquoi ce n'est pas fait | Qui |
|---|---|---|
| 5.1 Lectures des réformes de structure | Arbitrage (jusqu'à 0,66 point en 2037) | Adrien |
| 5.2 Lectures du solde migratoire | Arbitrage | Adrien |
| 5.8 Emploi spécifique jeune (Mélenchon) | Arbitrage | Adrien |
| 6 Micro relancée | Demande OpenFisca, absent de l'environnement de Claude | Poste d'Adrien |
| 7.2 Incidence en niveau de vie | Demande OpenFisca | Poste d'Adrien |
| 7.4 Coût du travail à long terme, 7.5 Secteurs et prix | Décisions de modèle | Adrien, puis Claude |
| 8.2 Chiffrage de l'Institut Montaigne | Attendu au T1 2027 | — |
| 8.4 Relecture neutre n° 3 | À confier à un agent qui n'a pas vu le code | Claude, sur demande |
| 9.1 Programmes « partiels » | Recherche sur les programmes d'Arthaud et de Le Pen | Claude |
| Sources : parts du retour des dividendes | Deux hypothèses à 0,5 sans source | Claude |

## À lancer sur le poste d'Adrien

```
python -m outils.population_synthetique      # population avec apprentis et plus-values (OpenFisca)
python -m outils.openfisca_mesures <programme>   # micro d'un programme, un par processus
python -m outils.vieillissement <programme>      # puis sa micro vieillie (2029, 2032, 2037, 2050)
python -m outils.veille_programmes           # veille des sites de campagne (accès web)
```

À vérifier au premier lancement : que les variables `apprenti` et `f3vg` existent dans la version d'OpenFisca
installée. Le code les ignore si elles manquent.

## Points d'attention

- **Monte Carlo** : il faut supprimer `sorties/incertitude_tirages_*.jsonl` avant de relancer après un changement
  de paramètres. Sinon la reprise garde les anciens tirages.
- **Empreinte des paramètres** : toute modification d'un fichier de paramètres, même une note, rend les sorties
  « anciennes » pour `tests/test_sorties.py`. Il faut alors tout régénérer, Monte Carlo compris (≈ 2 h sur 2 cœurs).
- **Page publique** : elle est publiée à part sur claude.ai, privée tant qu'elle n'est pas partagée. Pour la mettre à
  jour, régénérer avec `python -m outils.page_comparateur`.
