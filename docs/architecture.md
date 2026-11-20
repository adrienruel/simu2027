# Architecture : un noyau commun, un dossier par programme

Réécrit le 20/11/2026, après la suppression d'« Écologie de droite » (programme de test d'Adrien, à refaire un jour
sur le noyau commun comme un programme ordinaire, sans code ni paramètre propre). L'historique des étapes est dans
`docs/journal.md`.

## Règles

1. **Un programme ne redéfinit jamais une hypothèse commune.** Le chargeur des paramètres refuse une clé présente
   dans deux fichiers (`moteur/parametres.py`, test `tests/test_programmes.py`). Un paramètre commun à plusieurs
   programmes vit dans `programme_commun` (`parametres/commun/economie.yaml`), pas recopié.
2. **Une mécanique nouvelle va dans le noyau** et sert à tous les programmes ; un programme ne contient que ses
   mesures et la lecture de son texte (`mesures.yaml`).
3. **Chaque changement du noyau recalcule tous les programmes** (export, micro, incertitude) ; l'effet se lit contre
   le point de référence (`python -m outils.ecarts_reference`).
4. Le résultat d'un programme se lit comme un **écart au statu quo** (écart de solde primaire en tête).

## Paramètres

| Fichier | Contenu |
|---|---|
| `parametres/commun/economie.yaml` | Données et hypothèses communes : économie, démographie, système actuel, comportements, entreprises, `programme_commun`, `lectures_communes` |
| `parametres/commun/options.yaml` | Options du modèle : unités, modules activés, corrections de méthode |
| `parametres/commun/statu_quo.yaml` | Scénario sans réforme : point de départ (PLF 2027), blocs de dépense, retraites |
| `parametres/commun/ecologie.yaml` | Émissions et empreinte carbone |
| `parametres/commun/microsimulation.yaml` | Population synthétique et OpenFisca |
| `programmes/<nom>/parametres.yaml` | Mesures du programme (montant par scénario, poste, instrument…) |

`Parametres()` charge les hypothèses communes seules ; `Parametres(programme=<nom>)` y ajoute un programme.

## Code

| Bloc | Modules |
|---|---|
| Noyau et statu quo | `noyau`, `statu_quo`, `decomposition`, `parametres`, `unites`, `distribution`, `calendrier` |
| Mécanique d'un programme | `programme_simple`, `bibliotheque` (SMIC, âge de départ, CSG, capitalisation…), `annonces` |
| Canaux communs | `offre`, `bouclage`, `capital`, `naissances`, `migrations`, `canaux_declares`, `reformes_structurelles`, `fraude`, `emploi_canaux` (plancher du chômage), `incidence_entreprises` |
| Démographie et retraites | `demographie`, `ancien_systeme` (profils de départ par génération) |
| Système actuel | `systeme_actuel`, `recettes/` (effectifs de salariés, inactifs), `depenses/ministeres` (règles des missions) |
| Écologie | `ecologie/emissions` |
| Micro, incertitude, variantes | `micro`, `incertitude`, `fonds_apu`, `sensibilite`, `menages_types` |

Outils (`outils/`) : population synthétique, OpenFisca (ménages, entreprises, vieillissement), exports du
comparateur, audits, variantes, traçabilité des sorties (`trace.py`).

## Suppression d'Écologie de droite (20/11/2026)

Supprimés : `programmes/ecologie_de_droite/` (paramètres, mesures, budget, effets, modules propres), ses sorties,
ses tests (marqueur `edd`), le classeur v235 et ses outils (`reference/v235`, recalcul, extraction des cibles), ses
leviers et son tableau de bord, et le code du noyau qui ne servait qu'à lui :
- modules : `collectivites`, `emploi`, `epargne`, `impot_unique`, `is_bareme`, `tva`, `recettes/entreprises`,
  `recettes/retraites_croisiere`, et les 26 modules sortis de `moteur/` le même jour ;
- fonctions jamais exécutées par la suite de tests ni par aucun outil publié (mesure de couverture du 20/11/2026),
  dans les modules mêlés (`ancien_systeme`, `demographie`, `emploi_canaux`, `menages_types`, `offre`, `tva_menages`,
  `impot_salaires`, `ministeres`, `systeme_actuel`, `sensibilite`, `calendrier`, `bouclage`, `emissions`, `statu_quo`).

Critère : les sorties publiées se recalculent à l'identique (`tests/test_independance.py`).
