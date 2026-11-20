# simu2027 — comparateur des programmes de la présidentielle 2027

Un moteur Python chiffre, sur un noyau commun, les programmes des candidats contre un statu quo (PLF 2027 provisoire,
puis aucune mesure nouvelle). Mêmes règles pour tous les programmes : on ne reprend que leurs mesures, jamais les
économies ou les recettes qu'ils annoncent ; le modèle les estime lui-même en crise, prudent, médian et optimiste.

Programmes publiés : `programmes/publies.yaml` (statu quo, Arthaud, Attal, Bertrand, Glucksmann, Le Pen, Lisnard,
Mélenchon, Philippe, Retailleau, Roussel, Tondelier, Zemmour).

## Lancer (ligne de commande)

```
pip install -r requirements.txt
pip install -r requirements-micro.txt  # OpenFisca-France : microsimulation et ses tests
python -m pytest -q -p no:cacheprovider           # suite complète (~11 min avec OpenFisca)
python -m moteur.noyau <programme>                # un programme contre le statu quo
python -m outils.export_comparaison               # sorties/comparaison_*.csv (~1 min)
python -m moteur.incertitude 600                  # Monte Carlo (~1 h 45), sorties/incertitude_rho0.json et _rho1.json
python outils/export_incertitude.py               # sorties/comparaison_incertitude.csv (et _fonds.csv)
python -m outils.variantes_dette                  # décomposition du déficit et variantes de la dette (~40 s)
python -m outils.sources_poids                    # paramètres sourcés classés par poids (~5 min)
python -m outils.backtests                        # backtests sur des réformes passées
python -m outils.variante_fonds_apu               # variante « fonds dans les APU » (~20 min)
python -m outils.openfisca_mesures <programme>    # micro des ménages, un programme par processus
python -m outils.vieillissement <programme>       # micro vieillie (2029, 2032, 2037, 2050)
python -m moteur.statu_quo --ecart                # scénario sans réforme (sorties/statu_quo.json)
python -m outils.couverture_micro                 # part du budget « ménages » codée dans la micro (seuil des déciles)
python -m outils.export_incidence                 # incidence des mesures sur les entreprises, par décile
python -m outils.page_comparateur                 # page publique autonome (sorties/comparateur.html)
python -m outils.export_demographie               # naissances, décès, migrations, âges du comparateur (~10 s)
python -m outils.export_menages_types             # ménages types du comparateur, avec OpenFisca (~8 min)
python -m outils.veille_programmes                # veille des sites de campagne (veille/rapport.md, poste avec accès web)
```

## Organisation

| Dossier | Contenu |
|---|---|
| `parametres/commun/` | Hypothèses communes à tous les programmes (économie, options, statu quo, écologie, microsimulation) : valeur par scénario si besoin, unité, année des euros, statut, source |
| `programmes/<programme>/` | Un dossier par programme : `parametres.yaml` (qui ne peut pas redéfinir une hypothèse commune), `mesures.yaml`, `programme.py`. Architecture : `docs/architecture.md` |
| `programmes/publies.yaml` | Liste des programmes publiés dans le comparateur |
| `comparateur/` | Code de la page du comparateur en ligne (onglets, scripts par vue), copie de l'artifact ; mise à jour : `docs/comparateur.md` |
| `moteur/parametres.py` | Chargement et validation. `Parametres()` charge les seules hypothèses communes ; `Parametres(programme=<nom>)` y ajoute celles d'un programme |
| `moteur/noyau.py` | Comptabilité commune : un programme = statu quo + mesures + canaux communs |
| `moteur/statu_quo.py` | Scénario sans réforme, référence commune |
| `moteur/programme_simple.py`, `moteur/bibliotheque.py` | Mécanique d'un programme ; mesures communes (SMIC, âge de départ, CSG, capitalisation…) |
| `moteur/offre.py`, `bouclage.py`, `capital.py`, `naissances.py`, `migrations.py` | Canaux communs : offre, macro bouclée, capital, démographie |
| `moteur/fonds_apu.py`, `moteur/incertitude.py` | Variante commune des fonds de capitalisation ; Monte Carlo commun |
| `moteur/incidence_entreprises.py` | Des entreprises aux revenus des ménages : salaires, prix, actionnaires (phase L, `docs/entreprises.md`) |
| `moteur/decomposition.py` | Décomposition du déficit : primaire, taux, prime de dette, dette en plus, croissance (`docs/dette.md`) |
| `outils/` | Population synthétique, OpenFisca, vieillissement, exports |
| `tests/` | Tests automatiques |
| `docs/journal.md` | Journal des décisions, du plus ancien au plus récent |

## Règles

- Mêmes règles pour tous les programmes : un canal commun, jamais une règle propre à un programme.
- Une économie annoncée n'est jamais reprise ; une économie nommée sans chiffre est estimée, jamais mise à 0.
- Une hypothèse sans source est prise prudente.
- Euros constants de 2026 ; économie de 2026 placée en 2029 ; une seule conversion.
- Chaque changement de résultat est commité avec sa raison.

Roadmap : `Roadmap_simulation_globale_2026-11-20.md` (projet). Point de référence des écarts : étiquette
`ref-2026-11-20`, `python -m outils.ecarts_reference`.
