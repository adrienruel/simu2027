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

## 29 octobre 2026 — Début du sourçage

- `moteur/sensibilite.py` classe les hypothèses par poids sur le déficit (+10 % sur chacune) : la fonction de consommation, l'alignement public-privé par versant, le taux long de la dette, le quotient conjugal figé et la correction des couples arrivent en tête.
- Chaque paramètre corrigé garde sa valeur de la v235 (champ `v235`) ; les tests de reproduction la lisent (`Parametres(reference="v235")`), le calcul publié prend la valeur corrigée.
- Premiers corrigés et points à trancher : `docs/sourcage.md`. Le déficit publié passe à 4,69 % / 3,84 % / 2,33 % (enfants : chiffres de l'Insee).

## 29 octobre 2026 — Décisions d'Adrien sur le taux long, l'inflation et la consommation

- Taux long de la dette au niveau du marché (4,0 %) ; l'effet des réformes sur les taux reste porté par l'écart avec le Bund, différent selon le scénario. Inflation gardée à 1,8 %. Fonction de consommation recalée sur l'Insee. Détail et résultats : `docs/sourcage.md`.
- Déficit publié du prudent : 4,86 % / 4,46 % / 3,51 % en 2029 / 2032 / 2037 (v235 : 4,67 / 3,81 / 2,31) ; durablement sous 3 % en 2053 ; dette 139 % du PIB en 2050.

## 29 octobre 2026 — Quotient conjugal calculé, sensibilité champ par champ

- Les gains du quotient conjugal sont calculés par le moteur avec le barème en vigueur (9 900 € pour un couple à un revenu, 500 € à deux revenus) au lieu des résultats figés d'une ancienne simulation (8 510 € et 580 €) : +2,0 Md€ de coût, +0,07 point de déficit.
- La sensibilité perturbe désormais chaque champ d'une valeur structurée séparément (398 variantes, `python -m moteur.sensibilite`, résultat dans `sorties/sensibilite.json`, lu par le tableau de bord). L'ancienne méthode augmentait d'un bloc toutes les parts de l'alignement public-privé, ce qui n'avait pas de sens.
- Sources ajoutées : chômeurs BIT (Insee, 2e trimestre 2026), parts et charges des versants de la fonction publique (Insee 2025, cotisations CNRACL 2026).
- Déficit publié du prudent : 4,93 % / 4,53 % / 3,59 %.

## 29 octobre 2026 — Couples de retraités

- L'imposition commune des couples de retraités de l'ancien système est calculée par le moteur, année par année, au lieu du coefficient fixe de 0,894. Le gain des couples grandit avec le temps (0,92 en 2029, 0,82 vers 2050), parce que les pensions gelées baissent en euros constants et passent dans la tranche à 0 %. Hypothèses prises prudentes faute de source : 60 % en couple, corrélation 0,2.
- Déficit publié du prudent : 4,87 % / 4,49 % / 3,58 %.

## 29 octobre 2026 — Indépendants, carbone, contribution européenne

- Passage des revenus 2023 des indépendants en euros de 2026 sourcé (Insee Première n° 2114, puis évolution des salaires) : 1,0706 au lieu de 1,0395.
- Prix du carbone : 256 € est bien la valeur de l'action pour le climat de 2025 en euros de 2023, et les trois hausses qui la convertissent sont l'inflation 2024, 2025 et 2026 (Insee). Seul le nom du paramètre trompe. Le module carbone fait déjà monter le prix (300 € de 2023 en 2030, puis +3,2 % par an) ; Adrien confirme la hausse. Corrigé : la hausse s'arrête en 2060 comme la valeur de l'action pour le climat, au lieu de continuer jusqu'en 2073.
- Contribution à l'UE : 30,9 Md€ confirmés par le PLF 2027.
- Déficit publié du prudent : 4,83 % / 4,45 % / 3,53 %.

## 29 octobre 2026 — TVA des retraités, successions, AAH

- TVA payée aujourd'hui par les retraités calculée par le moteur à partir des données DREES : 34,0 Md€ au lieu de 41 Md€ saisis. La TVA actuelle reconstituée passe à 202 Md€ (206 Md€ perçus en 2024).
- Sources : droits de succession 2023 (16,6 Md€, Fipeco), AAH 2026 (14,6 Md€, PLF).
- Déficit publié du prudent : 4,97 % / 4,60 % / 3,70 %.

## 29 octobre 2026 — Incertitude sur les hypothèses de comportement

- `moteur/incertitude.py` : 300 tirages, chaque hypothèse ventilée par scénario tirée entre sa valeur de crise et sa valeur optimiste, indépendamment des autres, emplois créés par les réformes compris ; prudent sans clause. Résultat dans `sorties/incertitude.json`, affiché par le tableau de bord.
- Déficit 2037 sans clause : 80 % des tirages entre 3,8 % et 4,9 % (médiane 4,4 %) ; le prudent (6,0 %) est plus défavorable que tous les tirages ; la crise donne 7,1 %. Le prudent cumule les hypothèses défavorables : il n'est pas un scénario central.
- Ce qui pèse le plus sur 2037 : emplois créés par les réformes, productivité de l'IA, baisse de l'écart de taux, élasticités des revenus déclarés, érosion de l'IS. Ce sont les hypothèses de comportement à étayer en priorité.

## 29 octobre 2026 — Sources des hypothèses macro

- Les notes de la v235 sur les hypothèses macro (feuille Effets macro, colonnes E à H) sont reportées dans le fichier de paramètres (`note_v235`), et 13 hypothèses reçoivent leur encadrement par la littérature (Okun, CAE, FMI, OCDE, Acemoglu, Aghion et Bunel, Mésange, Saez et al., Auckland, Insee).

## 29 octobre 2026 — Décisions sur l'IA et le multiplicateur

- IA : 0,07 point de productivité par an en crise et en prudent (Acemoglu, 2024). Multiplicateur calé sur les experts : 1,3 / 1 / 1 / 0,5 (FMI en crise, CAE, FMI avant 2008).
- Le multiplicateur de 1 dans le médian relève le déficit de 2029 du médian, sur lequel la clause aligne le prudent : 5,31 % en 2029 au lieu de 4,97 %.
- Déficit publié du prudent : 5,31 % / 4,70 % / 3,73 %.

## 29 octobre 2026 — Étape 3 : OpenFisca-France

- OpenFisca-France 176.1 installé. `outils/openfisca_actuel.py` calcule le système actuel (législation 2026) sur une grille de salaires : salariés du privé et fonctionnaires de chaque versant (primes à 24,6 % du brut, DGAFP), personne seule locataire en zone 2. Les tables sont dans `parametres/donnees/openfisca_*_2026.csv` ; le moteur les lit sans avoir besoin d'OpenFisca.
- Le système actuel du moteur (nets, RSA, prime d'activité, aides au logement) vient désormais d'OpenFisca (`systeme_actuel.source`), sauf la taxe foncière, qu'OpenFisca ne calcule pas. Écarts avec la v235 : nets du privé à ±5 % ; agents publics : la v235 surestimait le net d'environ 5 % sur les classes les plus nombreuses et le sous-estimait au-dessus de 110 000 € de coût. Effet sur le déficit : +0,01 point.
- Ménages types (`parametres/menages_types.yaml`, `outils/openfisca_menages.py`, `moteur/menages_types.py`) : huit ménages, système actuel par OpenFisca (prestations familiales comprises), nouveau système par le moteur.

## 29 octobre 2026 — Le nouveau système codé dans OpenFisca

- `outils/openfisca_reforme.py` : réforme OpenFisca-France (impôt unique du foyer avec imposition commune et quotient familial plafonné, impôt local des actifs, RUI au prorata et RUI du conjoint sans revenu, compléments par enfant, épargne obligatoire, revenu disponible). Ses valeurs viennent du fichier de paramètres du moteur.
- Les deux écritures (réforme OpenFisca et `moteur/menages_types.py`) donnent le même revenu disponible à moins d'un centime sur les dix ménages types ; un test le vérifie, et un second recalcule la table avec OpenFisca quand il est installé.
- Ménages de retraités de l'ancien système ajoutés : retraité seul à 1 700 € bruts −3,9 % de consommation possible (il perd l'aide au logement), couple de retraités +0,5 %.

## 29 octobre 2026 — Futurs retraités, règle du RUI du conjoint

- Règle du RUI du conjoint sans revenu confirmée par Adrien (il s'éteint quand le revenu net du couple atteint deux RUI par personne).
- Futurs retraités du nouveau système (croisière, carrière entière) : SMIC 1 300 € nets par mois (socle seul), médian 1 530 € (rente 480 + socle 1 050), cadre à 100 000 € 1 762 € (rente 963 + socle 799). Taux de remplacement du revenu d'actif du nouveau système : 76 %, 75 %, 57 %.
- Pas de ménage d'indépendant : OpenFisca couvre mal les cotisations des non-salariés au réel ; à reprendre avec un cas micro-entrepreneur.

## 29 octobre 2026 — Étape 4 : bloc emploi unifié

- `moteur/emploi_canaux.py` et `docs/bloc_emploi.md` : chaque mesure dans un canal (offre, appariement, coût du travail, localisation, population active, perdus), rendements décroissants répartis au prorata, règles écrites contre le double compte. La somme des emplois par mesure redonne exactement le total de la feuille Emploi.
- Chaque emploi rapporte selon le salaire de son canal, avec les taux du nouveau système (`emploi.gain_par_canal`). Gain d'un emploi au SMIC : 11 556 € (v235 : 15 161 € pour 1,3 SMIC, TVA de l'ancien système) ; emploi perdu par localisation : 31 512 €.
- Déficit publié du prudent : 5,33 % / 4,74 % / 3,81 %.

## 29 octobre 2026 — IS à 45 % : taux légal, taux effectif, coût du capital

- Remarque d'Adrien : avec la déduction immédiate de l'investissement, l'IS à 45 % dissuade moins. `moteur/taux_effectifs.py` calcule le taux effectif moyen (Devereux et Griffith, projet type de l'OCDE) : 32,8 % aujourd'hui (IS à 25 % et impôts de production sur le capital), 41,3 % dans le prudent, 39,0 % dans l'optimiste.
- La localisation des activités et la réaction réelle de l'assiette suivent désormais ce taux effectif ; le transfert de bénéfices suit toujours le taux légal (la déduction n'y change rien). Emplois perdus par localisation (prudent) : 101 000 au lieu de 178 000.
- Déficit publié du prudent : 5,28 % / 4,59 % / 3,64 %.

## 29 octobre 2026 — Ménages : couples et enfants

- `cohortes.menages` : couples d'âge actif par année (Insee, forme par âge ; calage 2026 sur le quotient), part des couples à un revenu (emploi des conjoints indépendant, prudent). Quotient familial, conjugal et RUI du conjoint suivent enfants et couples.
- Prudent : publié 3,00 % en 2029, 2037 et 2050 ; avant clause −1,7 % en 2073 ; dette 85 %. Crise : 4,0 % en 2073, dette 152 %.

## 29 octobre 2026 — Fonds = somme des comptes ; fiscalité des nouveaux retraités par profil

- `cohortes.comptes` : comptes de toutes les générations, rente viagère pour moitié à 67 ans, l'autre moitié placée ; le capital nouveau du fonds suit les versements, les rendements gardés et les rentes versées (décumulation), au lieu de « 62,5 % des rendements réinvestis ».
- `cohortes.fiscalite_retraites_nouveaux` : impôt et TVA des nouveaux retraités sur la rente et le socle de chaque profil ; très proche de l'ancienne approximation.
- Prudent : publié 3,00 % en 2029, 2037 et 2050 ; avant clause −1,3 % en 2073 ; dette 90 %. Crise : 4,2 % en 2073, dette 154 %.

## 29 octobre 2026 — Cellules de salariés et comptes d'épargne par génération

- `moteur/cohortes.py`, `docs/cohortes.md` : salariés par âge et tranche de salaire chaque année (profil de l'Insee), impôt, TVA, RUI, épargne par cellule ; comptes par génération et socle par cellule (part sans carrière au socle plein). Calage 2026 sur le budget statique vérifié.
- Effet de composition des salaires retiré dans le prudent et la crise (double compte avec la tendance de productivité).
- Correction : l'emploi commence à 18 ans (les 15-17 ans comptaient au taux des 15-24 ans).
- Prudent : publié 3,00 % en 2029, 2037 et 2050 ; avant clause −1,4 % en 2073 ; dette 89 % en 2073. Crise : 4,2 % en 2073, dette 154 %.
- Limite connue : le capital du fonds ne baisse pas quand les retraités tirent leur rente (à traiter ensuite).

## 29 octobre 2026 — Contribution progressive ; vérification de la TVA

- Décision d'Adrien : contribution des anciens retraités progressive de 5 à 10 % (barème proposé : 5 % au-dessus du minimum vieillesse de 1 043,59 €, 10 % à partir de 3 000 € bruts) ; taux moyen 7,6 %, 33 Md€ en 2029, 16 en 2050.
- Vérification de la TVA (question d'Adrien) : la baisse du RUI par la règle ne comptait pas la TVA perdue sur la consommation qu'il finance (corrigé : gain divisé par 1 + taux des ménages modestes) ; taux de TVA actuel ramené de 13 % à 12,5 % (reconstitue les 206 Md€ de 2024 ; prudent). Constat : 29 Md€ des recettes viennent d'une « accise de transition » qui cale le nouveau système sur les recettes de consommation actuelles, sans instrument défini.
- Prudent publié : 3,00 % en 2029 et 2037, 3,18 % en 2050, excédent en 2073 ; dette 105 % en 2073. Crise : 6,3 % en 2073, dette 171 %.

## 29 octobre 2026 — Contribution des anciens retraités ; épargne rendue

- Décision d'Adrien : « tout le monde contribue, mais surtout les retraités actuels ». Contribution de solidarité de 5 % (taux proposé, à confirmer) sur les pensions de l'ancien système au-dessus du minimum vieillesse, nette d'une fuite de 25 % (impôt et TVA perdus).
- Chiffrage demandé : l'épargne prise par la règle est rendue à chaque génération, avec le rendement du fonds, à son départ à 67 ans ; le capital rendu rejoint le fonds. Version « pas avant 2055 » écartée (316 Md€ d'un coup en 2055). Droits encore dus en 2073 : ≈ 450 Md€.
- Prudent publié : 3,00 % en 2029, 3,04 % en 2037, 3,24 % en 2050 ; excédent léger en 2073 ; dette 107 %. Crise : 7,2 % en 2073, dette 182 %.

## 29 octobre 2026 — Règle automatique à 3 % ; socle à 67 ans

- Décisions d'Adrien : socle seulement à 67 ans (RUI entre l'âge légal et 67 ans, rente de son épargne possible en plus) ; règle automatique permanente visant 3 % de déficit au lieu de la clause temporaire calée sur le médian (`clause.cible`, `clause.derniere_annee` = 2073, `clause.ordre`).
- Refusés par Adrien : capitalisation plus progressive (perte de capacité d'investissement), remboursement réduit (injuste pour la génération qui paie les deux systèmes).
- Ajouté : socle en plus des générations dont l'épargne est prise par la règle (moins de capital à 67 ans) ; capacité de la règle proportionnelle aux actifs.
- Constat : sans la clause, le prudent est à 12,8 % de déficit et 270 % de dette en 2073 ; la clause de la v235 reposait déjà sur 5 points d'épargne pris de 2031 à 2037.
- Prudent publié avec la règle : 3,43 % (2029), 3,52 % (2037), 3,24 % (2050), excédent en 2073, dette 104 % ; la règle prend 5 points d'épargne presque chaque année jusqu'en 2050 et baisse le RUI de 141 € en 2030. Crise : 6 % en 2073, dette 182 %.

## 29 octobre 2026 — Attente entre l'âge légal et 67 ans ; recette carbone ; génération 1979

- Décision d'Adrien : entre l'âge légal et 67 ans, socle si annuités complètes (90 %), RUI sinon ; pour le nouveau système et les reportés de l'ancien.
- Recette carbone statique calculée par le moteur : 54,9 Md€ (v235 : 57,7 saisis).
- Erreur corrigée : la génération 1979 (50 ans en 2029) manquait (ni ancien système, ni cohortes du nouveau).
- Prudent : publié 4,03 % en 2037, 5,91 % en 2050 ; avant clause 4,18 % en 2073 ; dette 180 % en 2073 (131 % sans la prime de taux).

## 29 octobre 2026 — Relecture indépendante : corrections

- Erreurs vérifiées par la relecture et corrigées (`macro.corrections_relecture`, détail dans `docs/relecture.md`) : usure non taxée ; contribution de la clause retirée du fonds ; baisse du RUI bornée par le plancher sur le RUI réel ; effet récessif de cette baisse ; recettes des retraités et carbone statique hors indice de l'emploi ; pertes d'emplois hors rendements décroissants ; emplois proportionnels à la population de 18 à 64 ans.
- Prudent publié : 3,63 % en 2037 (3,04 avant), 4,97 % en 2038, 4,46 % en 2050 ; avant clause 0,09 % en 2073 ; dette 124 % en 2073 (98 avant).
- Tableau de bord : 2038 et 2050 affichés à côté de 2037 (fin des mesures temporaires de la clause).

## 29 octobre 2026 — Hausse de la déduction conditionnée ; usure du capital du fonds

- Décision d'Adrien : la hausse de la déduction vers 100 % avance d'un pas (5 points) chaque année qui suit un déficit du prudent, avant clause, sous 3 % (calculé sans la hausse). Prudent : 55 % en 2047, 100 % en 2063 ; crise : 50 %.
- Correction (question d'Adrien sur les retours du fonds) : la valeur ajoutée du capital du fonds compte l'usure (4 % dans le prudent) en plus du rendement net, comme l'investissement des entreprises.
- Prudent avant clause : 5,06 % en 2037, 3,85 % en 2050, −1,7 % en 2073 ; publié 3,04 % en 2037 ; dette 98 % en 2073.

## 29 octobre 2026 — Décisions (déduction, socle, coût employeur) et trois canaux ajoutés

- Décisions d'Adrien : déduction de l'investissement à 50 % puis vers 100 % (2040-2049, calendrier proposé) ; socle 1 200 € ; baisse du coût employeur 2,5 %. Le taux effectif (localisation, érosion de l'IS) suit la part déduite de chaque année.
- Canaux ajoutés : prime de taux liée à la dette (CBO, Laubach ; maturité 8,5 ans) ; participation des inactifs du halo du chômage (OpenFisca contre moteur, `outils/participation.py`) ; retombées du capital du fonds (médian et optimiste seulement).
- Prudent avant clause : 5,22 % en 2037, 5,18 % en 2050, 1,77 % en 2073 ; publié 3,19 % en 2037 ; dette 145 % en 2073. La prime de taux pèse 2,4 points en 2073.
- Test d'attribution : tolérance d'interaction relative (les intérêts dépendent désormais de la dette).

## 29 octobre 2026 — Pistes pour améliorer les comptes

- `outils/leviers.py`, `docs/leviers.md` : 15 variantes et paquets chiffrés. Paramètre ajouté : part du RUI pour le 2e enfant (15 %, variante à 25 %).
- Défaut corrigé : la contribution de transition (part de l'épargne obligatoire versée à l'État) n'était pas comptée en recette hors clause.

## 29 octobre 2026 — Âge légal à 65 ans par génération ; chiffrage du parent isolé à 50 %

- Âge légal à 65 ans (mesure du programme) : économie calculée génération par génération (12,5 Md€ vers 2033-2035 au lieu de 7 forfaitaires). Décision : départs de 2029-2043 calculés au départ puis gelés. Prudent avant clause : 6,03 % en 2037 ; publié 4,10 %.
- Chiffrage (non retenu) : RUI à 50 % par enfant pour le parent isolé : 6,1 Md€ par an, naissances −0,8 % au lieu de −4,6 %, +0,2 à +0,35 point de déficit jusqu'en 2060, autofinancé en flux en 2073, dette 2073 +5 points.

## 29 octobre 2026 — 3e enfant, crèches, ancien système par génération

- Décisions d'Adrien : RUI à 25 % par enfant dès le 3e ; +10 points de couverture en crèche (places créées). Réforme OpenFisca mise à jour, test de concordance pour 3 enfants.
- `moteur/ancien_systeme.py` : pensions de l'ancien système génération par génération (nés en 1978 ou avant), mortalité de l'Insee, gel en euros courants. La série de la v235 gardait 6,7 millions d'anciens retraités en 2073 (95 ans ou plus) : 1,1 million par génération.
- Socle du nouveau système : survivants pris dans la population de l'Insee (arrivées après 2029 et mortalité comprises) au lieu de la population de 2026 × Gompertz : 18,5 millions de bénéficiaires en 2073 au lieu de 15,0 ; 227 Md€ au lieu de 184.
- Prudent avant clause : 6,25 % en 2037, 4,63 % en 2050, 0,6 % en 2073 ; dette 132 % en 2073. Question ouverte : droits des départs de 2029-2043 gelés dès 2029 ou au départ.

## 29 octobre 2026 — Population année par année

- `moteur/demographie.py`, `docs/demographie.md` : projections de l'Insee de juin 2026 (fécondité basse en crise, centrale en prudent et médian, haute en optimiste) ; emploi par âge à taux de 2025 figés ; recettes, PIB, épargne versée au fonds, RUI et autres dépenses suivent la population. La v235 figeait la population de 2026.
- Effet du programme sur la natalité : le nouveau système verse 762 € de moins par enfant et par an en moyenne (moins pour le 3e enfant) ; naissances −7,6 % dans le prudent.
- Résultat : le prudent n'est plus à l'équilibre en 2060 (déficit 2,9 % avant clause) ; dette 155 % en 2073 au lieu de 64 %. Le recul de l'emploi (−16 % de 2029 à 2073) vient de la fécondité de 1,45 projetée par l'Insee.

## 29 octobre 2026 — Levier IS : taux et déduction

- `outils/levier_is.py`, `docs/levier_is.md`, `tests/test_levier_is.py` : grille taux légal × part déduite. Baisser le taux dégrade les comptes (45 → 35 % : +0,3 point de déficit en 2037 sans clause). La déduction immédiate coûte 34,5 Md€ en 2037 ; la supprimer réduirait le déficit de 1,4 point en 2037, au prix de 63 000 emplois perdus de plus et de moins d'investissement.
- Deux défauts trouvés par ces tests et corrigés : division par la part déduite (fin de la déduction des intérêts) ; taux effectif qui ignorait la part déduite.

## Constats sur la v235 (pour Adrien)

- **Le vrai coût de l'IS à 45 % est le transfert de bénéfices.** Il suit le taux légal (45 % contre 25 % aujourd'hui, et contre 15 à 25 % dans la plupart des pays voisins) : ≈ 14 % de l'assiette des grandes entreprises part vers l'étranger dans le prudent, soit ≈ 21 Md€ par an. La déduction de l'investissement ne le réduit pas. C'est le premier canal par lequel l'IS à 45 % coûte au budget.

- **Ménages types : le programme fait des perdants nets.** À consommation hors taxes comparable (TVA et accises de chaque système comprises, épargne obligatoire mise à part) : personne seule au SMIC −1,6 %, au salaire médian −4,3 %, cadre à 100 000 € −22,6 %, parent isolé au SMIC −10,3 %, couple de deux médians −3,7 % ; gagnants : couple de deux SMIC avec deux enfants +6,0 %, couple à un salaire médian avec deux enfants +11,1 % (quotient conjugal). L'épargne obligatoire (2 400 € par an au salaire médian) reste au ménage, mais elle n'est pas disponible. Le parent isolé perd l'allocation de soutien familial, la prime d'activité et l'aide au logement, que le complément de RUI (30 % par enfant) ne compense pas.

- **Les notes décrivent l'ancien prudent.** Depuis la v186 (décision du 17 octobre), l'ancien prudent est devenu la crise et le nouveau prudent est souvent le milieu entre crise et médian. Les notes de la v235 n'ont pas suivi : « prudent : la moitié » (seniors : 85 000, c'est la crise ; le prudent vaut 127 500), « prudent : 25 000 logements » (c'est la crise ; prudent 37 500), « prudent : 0,37 » (élasticité de l'investissement ; prudent 0,335), « prudent : multiplicateur de 1 » (c'est la crise ; prudent 0,75).
- **IA : même la crise est au-dessus de la source la plus prudente.** Acemoglu (2024) estime le gain de productivité de l'IA à 0,07 point par an ; la crise en compte 0,10 et le prudent 0,185 (milieu de la crise et du médian). L'effet de l'IA de la tendance mondiale est compté en plus de la croissance du COR (0,7 %), ce qui se défend puisque le COR ne le compte pas à part, mais ce n'est pas un effet du programme.

- **Couples de retraités comptés deux fois.** La v235 réduit l'impôt des anciennes pensions de 10,6 % pour l'imposition commune (≈ 6 Md€) et ajoute en plus un forfait de 1 Md€ « couples de retraités » dans le coût du quotient conjugal. Le moteur ne compte plus qu'une fois les retraités de l'ancien système.

- **Assiette de l'impôt local : libellé faux, valeur juste.** La v235 décrit ses 1 169 Md€ comme « salaires, traitements et pensions », mais le montant correspond aux seuls revenus d'activité (le moteur les recalcule à 1 174 Md€). Décision d'Adrien du 29/10 : l'impôt local est payé par les entreprises sur leurs bénéfices et par les actifs sur leur salaire, pas par les retraités ; le barème relève de chaque collectivité (le modèle prend un taux moyen). L'assiette est maintenant calculée, et les indépendants paient l'impôt local sur la part de leur revenu prise en salaire (3,0 Md€), ce que la v235 omettait.

- **Le taux long de la dette (3,3 %) est sous le marché.** L'OAT à 10 ans a dépassé 4 % en juillet 2026. À 4 %, le déficit de 2037 passe de 2,31 % à 3,29 % et la dette de 2050 de 117 % à 134 % du PIB. C'est, de loin, l'hypothèse non sourcée qui pèse le plus parmi celles qu'on peut vérifier sur le marché.

- **La réforme des entreprises détruit des emplois dans le prudent.** Avec l'IS à 45 %, le jeu de crise de la feuille Emploi compte 293 000 emplois perdus par délocalisation et 125 000 gagnés par la fin des impôts de production sur les salaires, soit 168 000 perdus au net, après rendements décroissants (correction du 29/10 : le chiffre net de 178 000, avant rendements décroissants, avait été présenté comme un effet de localisation seul) ; le médian en compte 181 000 gagnés au net. Le prudent prenant le milieu des deux, l'effet net est à peu près nul, et même légèrement négatif après rendements décroissants (+0,09 point de chômage en 2037 du fait de cette réforme).
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


## 29 octobre 2026 — Réformes du supérieur dans les carrières

Demande d'Adrien : les quatre réformes du supérieur et leurs quatre effets (entrée plus tôt, emploi des jeunes,
salaires, décrochage), sourcés, le bas des estimations en prudent. `moteur/carrieres.py` ; détail dans
docs/cohortes.md. Retenu en prudent : l'entrée plus tôt seulement (24 000 emplois). L'emploi des jeunes est déjà dans
le bloc emploi ; décrochage et salaires sont nuls en prudent faute d'estimation causale (positifs en médian et
optimiste). Effet modeste : −0,03 point de déficit avant règle en 2037, −0,08 en 2073.
