# Journal des décisions et des écarts

## 28 octobre 2026 — Socle

- Structure du dépôt, fichier de paramètres unique, conversion d'unités centralisée, barème de l'impôt unique.
- Barème 0 / 17,9 / 57 / 66 % (seuils 12 500, 24 000, 32 000 € de coût employeur) : retrouve les profils types v232 (SMIC 168 €/mois, médian 1 129 €/mois).

## 28 octobre 2026 — Référence v235 et bloc comptable de la trajectoire

- **La copie du classeur dans le projet est un export texte : valeurs seulement**, sans formules ni adresses de cellules. Elle est découpée en une feuille par fichier (`reference/v235/`, outil `outils/decouper_export.py`) et les cibles de Total et Trajectoire sont extraites en CSV (`reference/cibles/`, outil `outils/extraire_cibles.py`).
- **Bloc comptable de la trajectoire reproduit à l'identique** (écart < 10⁻¹¹ Md€) : dépenses, solde, solde primaire, dette, dette/PIB, solde de Maastricht. Déficits publiés retrouvés : 4,67 / 3,81 / 2,31 %.
- Mécanisme retrouvé : dette(t) = dette(t−1) − solde − participations de l'État remises au fonds ; ces participations valent 86,9 Md€ en 2047 et 48,1 en 2048, soit 135 Md€ (« après décote »).
- Maastricht : (solde en intérêts réels − 1,8 % × dette de l'année précédente) / PIB.

## 28 octobre 2026 — Recettes : impôt des salariés et des retraités

Reproduits à moins de 0,01 Md€ (outil `outils/arbre.py` pour lire les formules de la v235) :
- **Ligne 4, impôt unique du privé** : 452,84 Md€. Passage des classes de 2024 en euros de 2026 par interpolation log entre classes voisines (`moteur/distribution.py`).
- **Ligne 6, impôt unique du public** : 140,08 Md€. Coût employeur aligné sur le privé (−13,5 % en moyenne pondérée des versants).
- **Ligne 5, impôt des retraités en croisière** : 24,10 Md€. Épargne obligatoire sur 43 ans, rente (moitié viagère, Gompertz), socle dégressif exonéré, gains à la flat tax.
- Facteur de passage des recettes de 2024 : 1,039456 (PIB en valeur 2025 × volume 2026 × déflateur 2026), et non 1,039 arrondi.

## 28 octobre 2026 — Recettes statiques complètes (Total!B17)

**Les recettes statiques du nouveau système sont reproduites : 1 167,767 Md€, écart 0,003 €.**
Lignes 2 (IS), 3 (TVA et accises), 4-6 (impôt unique), 7 (dividendes), 8 (successions), 9 (contribution),
15 (accises des entreprises et accise de transition), 16 (indépendants), 19 (revenus du capital), 20 (bailleurs).
Modules ajoutés : `tva.py` (accises calculées depuis le prix du carbone, taux effectifs par profil),
`systeme_actuel.py` (net actuel par classe : RSA, prime d'activité, APL, taxe foncière),
`recettes/entreprises.py`, `recettes/independants.py`, `recettes/autres.py`, `recettes/total.py`.

## 28 octobre 2026 — Dépenses statiques, transition des retraites, IA

- **Dépenses statiques (Total!B44) : 1 217,58 Md€ retrouvés.** Budget de l'État mission par mission (salaires alignés, CAS Pensions réparti), santé (ONDAM, invalidité, autonomie, alignement hospitalier, Sécurité sociale), RUI de toutes les populations et AAH, collectivités.
- **Coût de la transition des retraites, 2029-2073, reproduit année par année** (`moteur/retraites_transition.py`) : socle par génération (5 quintiles, épargne capitalisée), survie de Gompertz, remboursement de 35 % au départ en retraite payé d'abord en participations (135 Md€ en 2047-2048), économie sur les hautes pensions (Pareto), pénibilité. Moyenne 132,91 Md€.
- **IA dans l'administration** reproduite (masse de gestion ministère par ministère, non-remplacement, plafond 40 %).
- Encore provisoires à cette date : économies sur les missions conservées (Total!B121) et quotient familial (Total!B122). *Portés depuis (voir plus bas).*

## 29 octobre 2026 — Effets macro et clause de trajectoire

- **Feuille Effets macro reproduite pour les trois scénarios, 2029-2073** (`moteur/macro.py`) : emploi, seniors, ajustement budgétaire, capital du fonds (avec la part placée à l'étranger qui dépend de la dette), logement, érosion de l'IS, fraude à la TVA, productivité, tendance, école, IA et adoption, réactions à l'impôt, investissement des entreprises, carbone, éviction de l'épargne, taux d'intérêt, dette, déficit de Maastricht. Écart maximal : 10⁻¹¹ Md€.
- **Clause de trajectoire reproduite** : prudent avant clause 5,23 / 5,18 / 4,07 %, mesures (étalement définitif, contribution jusqu'à 5 points, baisse du RUI jusqu'au RSA), prudent publié 4,67 / 3,81 / 2,31 %.
- Les trois scénarios sont calculés ensemble à chaque appel (fin de la limite I5 de l'audit pour la trajectoire macro).
- Entrées encore provisoires à cette date, *toutes portées depuis* : emplois et gain par emploi (Emploi), réactions à l'impôt (Hauts revenus), écarts de santé, carbone dynamique, logement, IS investissement, dette de départ et transferts aux collectivités (Calendrier), solde primaire hors effets macro (Trajectoire, lignes 18 à 22 et 43).
- Mise en garde de méthode : en lisant des formules tronquées à l'affichage, j'ai cru un moment que le médian et l'optimiste omettaient le carbone ; la formule complète les inclut. Les constats du journal ont été revérifiés sur formules complètes.

## 29 octobre 2026 — Chaîne complète : budget statique → trajectoire → effets macro → déficit

- Lignes 17 à 22 et 43 de la Trajectoire reproduites (`moteur/trajectoire_annuelle.py`) ; le solde primaire hors effets macro est désormais calculé, plus lu dans la v235.
- `python -m moteur.simulation` donne les déficits des trois scénarios et le prudent avant clause, identiques à la v235.
- Entrées encore provisoires pour la trajectoire (`reference/entrees_provisoires_trajectoire.json`) : santé année par année, anciennes pensions, successions, ascenseur social, économies, coût des réformes de l'emploi, RUI des étudiants.

## 29 octobre 2026 — Feuilles annexes et emploi

- Portés et testés contre la v235 : calendrier 2027-2028 (dette fin 2028), successions, ascenseur social, registre des mesures d'économies (`moteur/mesures.py`, premier embryon du registre des lois), objectifs (TVA de 2028, gel, RUI des étudiants), santé année par année avec pentes recalculées depuis les repères de l'Assurance maladie et du Trésor, garde-fou, volet santé de la TVA, feuille Emploi entière (14 réformes, rendements décroissants, marge intensive, localisation, gain par emploi, coût des réformes, taux de chômage par année).
- Le chargeur de paramètres refuse désormais les clés en double (YAML gardait la dernière sans prévenir : c'est arrivé une fois pendant le portage).
- Chômage 2037 retrouvé : 7,26 % (prudent), 6,13 % (médian).

## 29 octobre 2026 — Plus aucune valeur lue dans la v235 ; anciennes pensions

- Le moteur ne lit plus aucune valeur calculée de la v235 : les fichiers d'entrées provisoires sont supprimés, et un test vérifie qu'aucun module n'y fait référence. Portés en dernier : hauts revenus, collectivités (point fixe de l'impôt local calculé par itération), environnement, économies des missions, quotient conjugal, anciennes pensions.

## 29 octobre 2026 — Scénario de crise calculé

- La crise est maintenant le quatrième scénario calculé (`Parametres.en_crise()`, `simuler()["crise"]`), comme le fait la v235 : les valeurs de crise remplacent la colonne prudente (macro, santé, carbone, hauts revenus, emploi), la décote des participations passe à 20 %, l'effort ressenti en 2029 est saisi à 1,2 point, puis la clause de trajectoire s'applique.
- Outil `outils/recalcul.py` : recalcule la v235 dans LibreOffice avec des cellules modifiées. Vérifié d'abord sur la v235 telle quelle : **aucune cellule numérique** ne diffère des valeurs d'Excel. Il permet de vérifier le moteur sur n'importe quelle variante de paramètres.
- Cible en pleine précision `reference/cibles/crise.csv` (`outils/cibles_crise.py`) : le moteur la reproduit à 1e-9 (déficit, dette, chômage) et la feuille figée à six décimales.
- Résultats publiés (crise, clause comprise) : **4,68 % / 3,81 % / 2,64 %** en 2029 / 2032 / 2037 ; **avant clause : 5,45 % / 5,89 % / 4,91 %**.

## 29 octobre 2026 — Tableau de bord

- `moteur/restitution.py` met une simulation en forme (JSON) ; `python -m outils.tableau_de_bord` écrit `sorties/tableau_de_bord.html`, page autonome : synthèse du prudent publié avant et après la clause, déficit, dette et chômage des quatre scénarios, décomposition par canal de l'effet sur le solde et comptes d'une année au choix, part des paramètres sourcés.
- Le module macro garde désormais la décomposition par canal (emploi, ajustement, fonds, logement, érosion de l'IS, réactions à l'impôt, IA, santé, carbone, clause…) ; un test vérifie que la somme des canaux redonne l'effet total.

## 29 octobre 2026 — Registre des lignes du budget (architecture année par année, première étape)

- La trajectoire hors effets de l'économie est désormais construite comme une liste de lignes datées (`trajectoire_annuelle.Lignes`) : socle du budget statique, croissance tendancielle, dépenses à trajectoire propre (santé, transition des retraites, renouvelables), et mesures datées (une ligne par mesure du registre des économies, TVA de 2028, successions, RUI étudiant, IA, réformes de l'emploi…). Les postes de la feuille Trajectoire sont la somme de ces lignes : résultats inchangés.
- Un test vérifie que lignes + effets de l'économie − charge de la dette redonnent le solde public, pour le prudent et la crise.
- Tableau de bord : graphique du solde public (déficit sous zéro) au lieu d'un « déficit » qui devenait négatif en cas d'excédent ; période 2029-2050 par défaut ; tableau « le budget ligne par ligne » pour l'année et le scénario choisis.
- Étape suivante : faire porter aux mesures leurs propres dates et paramètres (aujourd'hui une partie vit encore dans des modules), puis attribuer aux mesures leur part des effets de l'économie.

## 29 octobre 2026 — Registre des lois et attribution par mesure

- `parametres/registre_lois.yaml` : 31 mesures séparables (réformes de l'emploi, emploi des seniors, fraude à la TVA, logement, IA, santé…), chacune avec la façon de la neutraliser ; les 17 mesures du registre des économies s'y ajoutent automatiquement. La bascule (impôt unique, TVA, RUI, retraites, fonds) n'y est pas : elle forme un seul système.
- `Parametres.avec()` crée une variante (valeur simple ou champ d'une valeur structurée) sans toucher aux paramètres de base ; `clause.active` permet de calculer sans la clause.
- `moteur/attribution.py` : contribution de chaque mesure = solde avec tout − solde sans la mesure, prudent sans clause, décomposée en ligne budgétaire, effets sur l'activité et intérêts. Ensemble des mesures séparables en 2037 : +33,0 Md€, −1,12 point de déficit, −1,04 point de chômage ; la somme mesure par mesure (+31,4 Md€) en diffère de 1,7 Md€ (interactions).
- Tableau de bord : section « Ce que rapporte chaque mesure » (2029, 2032, 2037, 2050, filtre par domaine).

## Constats sur la v235 (pour Adrien)

- **La réforme des entreprises détruit des emplois dans le prudent.** Avec l'IS à 45 %, le jeu de crise de la feuille Emploi compte 178 000 emplois perdus par délocalisation, et aucun gagné par la fin des impôts de production ; le médian en compte 181 000 gagnés. Le prudent prenant le milieu des deux, l'effet net est à peu près nul, et même légèrement négatif après rendements décroissants (+0,09 point de chômage en 2037 du fait de cette réforme).
- **Les mesures les plus coûteuses du programme hors bascule** sont, en 2037 : la baisse de 5 % du coût employeur jusqu'à 1,3 SMIC (−8,2 Md€, net de ses emplois), les crèches (−5,7 Md€), l'aide à l'autonomie et à la garde d'enfants (−4,4 Md€). Les plus rentables : la division par deux du besoin de financement des collectivités (+9,4 Md€), l'âge légal de l'ancien système (+7,2 Md€), l'IA dans l'administration (+6,2 Md€).
- **Fin des contrats aidés et de l'insertion** : elle ajoute 0,36 point de chômage et coûte 2,0 Md€ par l'activité perdue ; l'économie budgétaire correspondante est dans le budget statique de la bascule, pas dans cette ligne.

- **Le prudent repasse au-dessus de 3 % après la clause.** Il passe sous 3 % en 2036, puis remonte à 3,42 % en 2038, dès que la contribution de transition s'arrête (dernière année : 2037), et reste au-dessus de 3 % jusqu'en 2041 ; nouveau passage à 3,55 % en 2047-2048. Il n'est durablement sous 3 % qu'à partir de 2049. À partir de 2040, l'étalement de la déduction coûte au lieu de rapporter (jusqu'à −15 Md€ par an). L'indicateur « première année sous 3 % » de la v235 ne montre pas cette remontée ; le tableau de bord affiche l'année à partir de laquelle le déficit reste sous 3 %.
- **Excédents de long terme sans rétroaction.** En fin de période, tous les scénarios dégagent de gros excédents (prudent : 7,7 % du PIB en 2073, optimiste : plus de 15 %), et la dette devient négative dans le médian et l'optimiste. Le modèle n'a aucune règle qui rende ces excédents (baisse d'impôt, dépenses) : les chiffres d'après 2050 décrivent une marge de manœuvre, pas une trajectoire plausible.

- **Scénario de crise : le point fixe de l'impôt local n'est pas recalculé.** Les feuilles de salariés lisent un taux recopié à la main (Collectivités!B91 = 7,2036 %), resté à la valeur du prudent ; en crise, le taux qui équilibre les collectivités est 7,2800 %. Les feuilles Emploi et Hauts revenus lisent, elles, le taux recalculé (B32). Le moteur publie la crise avec le point fixe recalculé ; l'écart de déficit est inférieur à 0,01 point. Le test de reproduction garde l'ancienne copie (`en_crise(comme_v235=True)`).
- **Scénario de crise : la liste des paramètres ne dit pas ce qui a servi.** Elle affiche Effets macro!B8 = 126 663 emplois (le milieu prudent, valeur collée), alors que les valeurs figées ont été produites avec B8 = RUI!B34 recalculé en crise (126 391). Avec 126 663, le PIB s'écarte de la feuille figée ; avec 126 391, il la reproduit. Effets macro!B273 est stocké en texte.
- **En crise, le médian bouge aussi.** Comme la clause aligne le prudent sur le déficit du médian, et que le médian lit la colonne prudente (part du PIB qui revient au budget, IS, santé du budget statique, gain par emploi), le déficit publié de la crise en 2029 (4,68 %) n'est pas celui du médian de base (4,67 %). La crise ne mesure donc pas « le prudent sous des hypothèses dures » mais « le médian recalculé sous des hypothèses dures, plus ce que la clause ne compense pas ».
- **La clause efface la crise jusqu'en 2032** : jusque-là, le déficit publié de la crise est celui du médian (4,68 %, 3,81 %), parce que la contribution de transition (jusqu'à 5 points) absorbe tout l'écart. C'est l'affichage « avant clause » (5,45 %, 5,89 %, 4,91 %) qui montre la crise. Les deux doivent toujours figurer ensemble.
- **Taux marginal combiné de 73,2 %** au-delà de 32 000 € : 66 % d'impôt unique plus 7,2 % d'impôt local. Le « plafond de 66 % » affiché n'en est pas un pour le contribuable.
- **Hauts revenus** : la réaction des agents publics à hauts revenus est calculée sur leur coût non aligné ; le canal « passage par une société » leur est neutralisé par un facteur 0 écrit dans la formule.
- **Collectivités** : constantes écrites dans les formules (par exemple la part 59,9 / (59,9 + 19,5) entre communes et régions).
- **Quotient conjugal** : les gains sont des résultats de simulation figés, calculés avec un ancien barème ; ils ne suivent pas le barème actuel.
- **Anciennes pensions** : avec la réversion, les pensions par décile ne sont plus rangées par ordre croissant ; à vérifier dans la source.
- **IS « protection contre la chaleur »** : la perte d'IS est comptée chaque année jusqu'en 2073, sans extinction ; à confirmer que c'est voulu.

- **Gain budgétaire par emploi (Emploi!B245)** : la TVA sur la consommation en plus est calculée au taux moyen de l'ancien système (13 %, Total!B140), pas aux taux effectifs du nouveau (≈ 17-18 %), et appliquée au montant toutes taxes comprises. Le gain par emploi est un peu sous-estimé.
- **Prudent de l'emploi** : il prend le milieu de la crise et du médian pour les emplois créés (Effets macro!B8), mais la valeur de crise pour les emplois perdus (fin des subventions, fin de la prime) : asymétrie volontairement prudente, à écrire noir sur blanc.
- **Impôt local dans la feuille Emploi** : lu dans Collectivités!B32 (0,07203594340), alors que les feuilles de salariés lisent la copie B91 (0,07203594282) ; le point fixe n'est pas tout à fait atteint.
- **Libellés périmés** : « RUI de 850 € » (Emploi ligne 10) ; « part remboursée 60 % » des prépas (Ascenseur social ligne 62) contre 55 % dans le calcul ; « Moyenne 2026-2070 » pour des moyennes 2029-2073.
- **Constantes dans les formules** : 52 Md€ d'impôts de production sur les salaires (Emploi!B217 « =52 »), dépense par élève ingénieur 13 000 × 0,6, prix du tabac 14,7 / 12,54 (Santé!B69).
- **Décès après 2070** : gardés constants (la formule de prolongation n'a plus de second point) ; sans effet notable.


- **Revalorisation des pensions sous le minimum vieillesse** (Objectifs!B16) : exposant compté depuis 2028, alors que tout le reste part de 2029 ; une année de croissance en plus dès 2029.


- **Coût du capital (Effets macro!B273:D273)** : trois constantes sans libellé retranchées dans les formules (0,047 / 0,055 / 0,121 selon le scénario).
- **« Prudent avant clause »** : c'est le déficit d'une seule année sans les mesures, avec la dette et les intérêts de la trajectoire après clause, pas une trajectoire entière sans clause. L'écart s'accumule : la vraie trajectoire sans clause est un peu plus haute que ces chiffres.


- **Constantes encore écrites dans des formules** (en plus de celles déjà signalées) : AAH 14,6 Md€ (RUI!B17), aide sociale à l'autonomie 20,2 Md€ (Santé!B103), heures d'APA 4,29/25,18 (Santé!B105), gestion de la Sécurité sociale 14,63 Md€ et 48 632 agents de France Travail (Sécurité sociale!B15, C22), contribution à l'UE 30,9/1,018, crédits du programme 155 (2,0594 Md€, Budget État!B133).
- **Gestion de l'assurance maladie** : sa part conservée (Sécurité sociale!C13) est calculée à partir du gain d'IA de France Travail. La baisse de 30 % annoncée pour la gestion de la Sécurité sociale passe donc par un ratio propre à France Travail.
- **Économies de santé du budget statique** : prises dans la colonne prudente (Santé!B38 via Trajectoire!B12), quel que soit le scénario retenu.
- **Libellés « 2026-2070 »** des moyennes (IA administration!E59, Coût transition ligne 51) : elles portent sur 2029-2073.


- **Indépendants : pivot salaire / société périmé (≈ 0,9 Md€).** Le montage « salaire jusqu'au pivot, reste par la société » prend comme pivot Total!B91 = 45 000 €, ancien début du taux de 66 %. Depuis la v227, le 66 % commence à 32 000 €. Avec un pivot à 32 000 €, l'impôt des indépendants baisse de 0,92 Md€ : la v235 le surestime d'autant. Le pivot devrait être relié au seuil du 66 %, pas à une cellule de position fixe.
- **Entreprises déficitaires (bloc 5) : allègement périmé (0,28 Md€).** Le bénéfice des entreprises qui passent en positif est calculé avec la suppression de la TVA non déductible (U3), qui n'est plus supprimée depuis la v231. L'allègement réel est la fin des impôts de production (≈ 7 400 € pour la petite classe, contre 7 470 € de TVA) : l'ordre de grandeur tient, mais le libellé et la cellule sont faux.
- **Taxe foncière actuelle des bas salaires** : saisie à 0 pour les sept premières classes du privé (net avant aides ≤ 17 956 €), calculée pour toutes les classes d'agents publics. Règle implicite, non documentée.
- **Prime d'activité des agents** : barème simplifié (230 € au plus, Fonctionnaires B71-B73), alors que le privé utilise le barème sourcé d'avril 2026. Sans effet aujourd'hui (aucun agent sous 35 000 €).
- **Prix du carbone** : 256 € et les trois hausses (2 %, 0,9 %, 2,1 %) sont écrits dans les formules Barème TVA!B56 et E56, que l'audit v233 n'a pas sortis.
- **Facteurs d'euros multiples** : Indépendants!B40 = 1,0395 saisi à part, à côté du facteur de recettes (1,039456) et des facteurs de salaires.
- **Accise de transition, à vérifier** : elle est calée sur « ancienne TVA − nouvelle TVA » (Barème TVA!B181-B182), libellé « assiettes 2024 », puis multipliée par le facteur 2024 → 2026. Or les deux TVA des salariés y sont calculées sur les distributions de 2026. Le mélange d'années pourrait décaler le calage « recettes égales » de quelques milliards : à trancher en définissant l'année de chaque terme.
- **Profil import/marge** : le plafond B63 est libellé « € de coût employeur » mais appliqué au net actuel.
- **Paramètres de consommation** (2,05 et 0,92) rangés dans Total!N29:N30, sur les lignes « Sous-total régalien » et « Éducation nationale ».


- **RUI des agents publics** (Fonctionnaires, colonne AR) : la part de RUI s'éteint à 12 500 € de coût employeur, contre le coût d'un SMIC à temps plein dans le privé. Sans effet aujourd'hui (aucun agent sous 35 000 €), mais incohérent.
- **Contribution de transition** (Total!B126) : retirée de l'épargne des salariés du privé (colonne BB), pas de celle des agents publics (colonne BD). Sans effet tant qu'elle vaut 0 dans le budget statique ; à vérifier là où la clause l'active.
- **Taux d'épargne des agents** calculé sur le coût aligné, celui du privé sur le coût d'origine : cohérent, noté pour mémoire.


- **Feuille Résumé, libellé périmé** : « Tranche 3 (24 000 à 45 000 €) » à 57 %, alors que le barème de la feuille Total passe à 66 % dès 32 000 €. Le calcul est juste, le libellé faux. Même chose pour « 7 tranches » : les tranches 4 à 7 sont toutes à 66 %.
- **Coût du SMIC** : le paramètre de la v235 est 1 930 €/mois (Total) ; le profil type de l'état du programme utilise 1 979 €/mois. À éclaircir.

## Points à éclaircir à l'étape 1 (lecture de la v235)

- **Coût du SMIC** : 1 979 €/mois (23 750 €/an, profil type v232) contre 1 930 €/mois (juin 2026) cité dans l'audit v235. Lequel sert à quoi ?
- **Couples et enfants** : « couples imposés ensemble, demi-part par enfant plafonnée à 1 000 € » — mécanique exacte du quotient à préciser.
- **État du programme en v232** : les résultats publiés ont bougé en v233-v235 (déficits, chômage, profils). Les valeurs de référence des tests seront celles de la v235.
