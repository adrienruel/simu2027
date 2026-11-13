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

## 29 octobre 2026 — Règle de trajectoire dans tous les scénarios

DÉCISION d'Adrien : même point de départ pour tous les scénarios. Le médian et l'optimiste passaient au-dessus du
prudent en déficit publié (4,27 % et 3,65 % en 2029 contre 3,00 %), seul le prudent ayant la règle. La règle
s'applique désormais aussi au médian et à l'optimiste (`clause.scenarios`), qui sont publiés avec et sans règle :
tous partent de 3,00 % en 2029. Le médian sort de la contribution et de la baisse du RUI en 2033, l'optimiste dès
2030 ; le prudent en 2051 ; la crise jamais. L'étalement de la déduction, une fois déclenché, reste acquis (règle
inchangée), d'où un déficit publié sous le déficit sans règle quelques années après la sortie ; l'épargne prise est
rendue à 67 ans dans chaque scénario.

Correction faite en passant : quand le déficit sans règle était sous 3 % mais que l'étalement coûtait cette
année-là, la règle prélevait quand même ce coût sur l'épargne (prudent, 2044-2051 : jusqu'à 7 Md€ par an pris sans
nécessité ; aussi quelques dizaines de millions en fin de période). Elle ne prend plus que ce qui dépasse la marge
sous la cible. Effet : prudent 2073 −1,79 → −1,77 % (moins d'épargne prise, donc moins à rendre et plus de capital).

| Déficit sans règle / publié | 2029 | 2032 | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|---|---|
| Crise | 4,81 / 3,00 | 5,62 / 3,69 | 4,95 / 3,25 | 4,29 / 3,22 | 5,05 / 3,93 | 152 % |
| Prudent | 4,68 / 3,00 | 5,06 / 3,14 | 4,28 / 3,00 | 3,66 / 3,00 | −1,77 / −1,77 | 85 % |
| Médian | 4,27 / 3,00 | 3,50 / 3,00 | 2,35 / 2,14 | −0,78 / −0,73 | −8,81 / −8,81 | −64 % |
| Optimiste | 3,65 / 3,00 | 2,14 / 1,89 | 0,54 / 0,34 | −3,02 / −2,98 | −10,75 / −10,75 | −122 % |

## 30 octobre 2026 — Chômage jusqu'en 2073

Demande d'Adrien : le chômage n'était calculé que jusqu'en 2040 (population active figée en 2026, comme la v235).
Paramètre `chomage.dynamique` (v235 : non). Chaque année :
- **sans le programme** (`demographie.chomage_tendanciel`) : population de l'Insee × taux d'emploi par âge de 2025,
  chômeurs par âge au taux de 2025 de leur âge (Insee : 19,8 % avant 25 ans, 6,9 % de 25 à 49, 5,0 % après 50),
  calés sur 8,3 % en 2026. Taux tendanciel : 8,3 % en 2037, 8,1 % en 2050, 8,0 % en 2073 (moins de jeunes) ;
- **réformes** : chômeurs repris par les réformes, proportionnels à l'écart entre le taux tendanciel et le
  chômage incompressible de 3,5 % (rendements décroissants : −6 % d'emplois des réformes en 2073, effet aussi
  sur le budget) ; effet récessif de l'ajustement de 2029 et des baisses du RUI de la règle ;
- **seniors** : 7 chômeurs en plus pour 17 emplois de seniors gardés (réforme de 2010, Insee 2017), au niveau de la
  source dans tous les scénarios : 70 000 en 2037, 195 000 à partir de 2050 avec le socle à 67 ans ;
- **population active** : grossie des emplois venus de l'inactivité (seniors, cumul, inactifs, jeunes entrés plus
  tôt), qui ne réduisent pas le nombre de chômeurs.

| Chômage (%) | 2029 | 2032 | 2037 | 2040 | 2050 | 2060 | 2073 |
|---|---|---|---|---|---|---|---|
| Crise | 9,40 | 9,16 | 8,33 | 8,29 | 8,39 | 8,32 | 8,28 |
| Prudent | 9,19 | 8,45 | 7,33 | 7,35 | 7,59 | 7,64 | 7,61 |
| Médian | 8,78 | 7,34 | 6,42 | 6,41 | 6,61 | 6,66 | 6,63 |
| Optimiste | 8,03 | 5,77 | 5,05 | 5,06 | 5,35 | 5,41 | 5,40 |

Lecture : après 2040, le chômage remonte d'environ 0,3 point, parce que le report du socle à 67 ans met des seniors
au chômage (la source de 2010 en compte 7 pour 17 emplois gardés) ; la baisse due aux réformes tient, un peu
réduite par la démographie. Effet sur les comptes : négligeable (déficit sans règle 2073 prudent −1,77 → −1,76 %).

## 30 octobre 2026 — Entreprises par taille (première étape)

`moteur/entreprises_cellules.py` (détail dans docs/entreprises.md) : impôts de production des entreprises
déficitaires retirés de la base de l'IS nouveau (−4,2 Md€), bilan des impôts par taille (TPE +14 Md€, GE −6 Md€),
investissement par taille. Prudent 2073 sans règle −0,84 → −0,16 % ; dette 95 → 104 %.
Suite (demande d'Adrien) : dirigeants de petites sociétés qui se versent un salaire au lieu du bénéfice : 2,4 Md€
passés en salaire, 0,9 Md€ de recettes perdues par an dans le prudent. Prudent 2073 sans règle −0,16 → −0,02 %.
Suite (remarque d'Adrien) : bilan par taille avec la déduction de l'investissement et les intérêts non déduits ;
correction : la déduction jouait sur l'IS de l'État seul, pas sur l'IS local de même assiette (+12,5 % de coût).
Prudent 2073 sans règle −0,02 → +0,18 %.
Suite (décision d'Adrien) : le fonds investit d'abord dans les entreprises les moins capitalistiques (PME, TPE, puis
ETI et GE, 25 % au plus du capital de chaque taille) pour réduire le plus le chômage ; nouveau canal : le chômage
d'équilibre baisse avec le capital (élasticité 0,23 en prudent). Prudent : 104 000 emplois en 2073, chômage 7,08 %.

## 30 octobre 2026 — Impôts recalculés selon la nature des revenus

Question d'Adrien : pourquoi les recettes partent d'un budget statique. Réponse : le barème est appliqué une fois
aux distributions de 2026, puis les recettes suivent la croissance, la population et les cellules de salariés
(impôt et TVA recalculés chaque année par âge et niveau de salaire). DÉCISION d'Adrien : les barèmes suivent la
croissance. Avec des barèmes qui suivent les revenus, recalculer chaque année l'impôt de revenus qui suivent la
croissance donne le même résultat (l'impôt est proportionnel quand revenus et seuils grandissent ensemble) : ce
qui change, ce sont les revenus que le programme crée ou détruit. Ils étaient imposés à la part moyenne des
recettes dans le PIB (38 %). Désormais (`macro.impots_par_revenu`) : salaires à 53 % du coût employeur (impôt
unique, impôt local, TVA des cellules de l'année), bénéfices à 45 % (IS), valeur ajoutée mêlée à 50 % (63 % de
salaires, 37 % de bénéfices). Effet : la récession de l'ajustement de 2029 coûte plus (−29 Md€ au lieu de −23) ;
le capital du fonds rapporte plus (17 Md€ en 2073 au lieu de 14). Prudent sans règle : 2029 4,93 → 5,16 % ;
2037 4,68 → 4,72 ; 2073 inchangé (0,04). En 2029, la règle au maximum ne ramène plus le prudent qu'à 3,26 %
(crise 3,31 %).

## 30 octobre 2026 — Inflation, indexation, départ à 67 ans

DÉCISIONS d'Adrien : indexation de la RUI, de l'AAH, du socle et des seuils de la contribution des retraités au
minimum de l'inflation et de la croissance nominale ; départ à 67 ans (quatre trimestres par génération) ; inflation
modélisée. Détail : docs/inflation_indexation.md. Prudent 2073 sans règle −0,14 → +5,17 % ; dette 105 → 137 %.

## 4 novembre 2026 — Dépenses des ministères par règle

Demande d'Adrien du 30/10 : chaque mission suit sa règle (croissance et public servi, PIB, ou prix). Détail :
docs/ministeres.md. Mesures de l'ancien système classées en « retraites ». Prudent 2073 sans règle 5,17 → 4,53 %.

## 4 novembre 2026 — Scénario sans réforme (statu quo projeté)

Première étape de la feuille de route multi-programmes (demande d'Adrien). `moteur/statu_quo.py`, paramètres communs
`parametres/commun/statu_quo.yaml`, détail dans docs/statu_quo.md. Système actuel à législation constante (PLF 2027),
mêmes hypothèses communes que les programmes, aucun paramètre de programme (test avec un programme vide). Retraites de
toutes les générations, érosion relative calée sur le COR 2070 (0,46 % par an) ; contrôles hors calage : 2045 et
variantes de productivité du COR à 0,2 point près. Résultat (prudent) : déficit 5,6 % en 2029, 8,6 % en 2037, dette
au-dessus de 200 % vers 2045 (trajectoire divergente : déficit primaire de 2 % et taux au-dessus de la croissance).
Écart du programme (solde primaire sans sa règle) : +0,6 point en 2029, +2,8 en 2037, +2,1 en 2050 ; à confirmer par
le test « programme vide = statu quo » (étape 2). Aucun résultat du programme n'est changé.

DÉCISIONS d'Adrien (4 novembre 2026) : le statu quo garde le PLF 2027 comme point de départ provisoire (pas encore
voté ; à actualiser avec la loi votée) ; la trajectoire des dépenses de santé est gardée telle quelle.

## 4 novembre 2026 — Noyau commun : un programme = statu quo + mesures

`moteur/noyau.py` (demande d'Adrien, étape 2 de la feuille de route) : la comptabilité 2029-2073 de tous les
programmes passe par le même calcul (blocs du statu quo + mesures du programme, puis intérêts, dette, déficit). Le
statu quo est le programme vide. « Écologie de droite » est rebranché (`programmes/ecologie_de_droite/programme.py`) :
son budget devient des mesures poste par poste contre le statu quo, ses effets macro une mesure par canal, son
contexte (PIB, inflation, baisse de l'écart de taux, chômage, dette de 2028) passe au noyau ; résultats identiques à
1e-13 près. Constat : périmètres différents (collectivités en net dans le programme, en brut dans le statu quo) ; à
aligner avant de découper le programme en mesures une à une. Aucun résultat changé.

## 4 novembre 2026 — Recettes du statu quo impôt par impôt ; périmètres alignés

Question d'Adrien : le statu quo refait-il toute la fiscalité actuelle ? Non (un agrégat) : désormais, recettes impôt
par impôt (niveau du PLF 2027, répartition de la colonne « Ancien » de la v235, à 0,27 % de l'Insee), chacune avec son
assiette (masse salariale, pensions, PIB, décès). Périmètres alignés (accord d'Adrien) : les collectivités sont
remises au budget du programme (230 Md€ de dépenses, ressources propres égales moins le besoin de financement déjà
compté). Écart de départ du programme, hors effets macro, prudent 2029 : recettes −163 Md€, retraites +31, santé −12,
revenu universel contre prestations +68, investissement et autres dépenses +138 ; total +2,0 points de PIB. Aucun
résultat du programme changé ; statu quo inchangé à 0,1 point près (recettes sur les pensions).

DÉCISIONS d'Adrien (4 novembre 2026) : le fonds reste hors des administrations publiques ; priorité au chiffrage complet
du statu quo avant de refaire le programme (feuille de route dans docs/statu_quo.md). Premier contrôle : les
prélèvements sur les salaires calculés par OpenFisca recoupent la répartition des recettes (privé −0,6 %, public −2,8 %).

## 4 novembre 2026 — Statu quo : prélèvements sur les pensions par OpenFisca

`outils/openfisca_retraites.py` (table OpenFisca-France 176.1.10, législation 2026, personnes seules et couples) et
`statu_quo.prelevements_retraites` : 51,2 Md€ en 2029, comme la répartition des recettes (−0,1 %). Option
`statu_quo.baremes_retraites` (prix par défaut, législation constante ; salaires : −0,7 point de PIB de recettes en
2073), à trancher par Adrien.

## 4 novembre 2026 — Statu quo : TVA par source de revenu ; barèmes des retraités sur les prix

DÉCISION d'Adrien : `statu_quo.baremes_retraites` = prix (loi actuelle). `statu_quo.tva` : TVA des salariés et agents
(revenus OpenFisca), des retraités (pension nette OpenFisca, chaque année), des inactifs et étudiants, et non
déductible ; le calcul explique 91 % de la TVA de départ (calage 1,10). TVA 7,21 % du PIB en 2029, 7,34 % en 2073.

## 4 novembre 2026 — Statu quo : IS, impôts de production, CVAE en extinction

IS (70,3) et impôts de production (75,3, Md€ de 2024) séparés. Législation en vigueur : CVAE de 0,28 % (2027) à 0,09 %
(2029), supprimée en 2030 (≈ 3 Md€). Contribution exceptionnelle des grandes entreprises : versée en 2026, sans effet
après. Statu quo prudent 2029 : 5,6 % de déficit (inchangé à 0,1 point près).

## 4 novembre 2026 — Statu quo : prestations sourcées

Famille (34,7 Md€, REPSS 2023), aides au logement (16,7, compte du logement 2025), RSA (13,5, DREES et Sénat) et prime
d'activité (10,5, Sénat) remplacent les parts encadrées de la DREES (le reste de ces risques, action sociale et
crèches, passe dans « autres », qui suit les salaires). Prime d'activité à législation constante : barème OpenFisca
fixe face aux salaires qui montent (−52 % par personne en emploi en 2073). Statu quo prudent : 8,8 % en 2037.

## 4 novembre 2026 — Statu quo : dépenses de l'État, des collectivités et reste

Le bloc « autres » (377 Md€ en reste) est découpé : missions de l'État 2026 hors CAS Pensions et hors ce que d'autres
blocs comptent déjà (prime d'activité, AAH, aides au logement, régimes de retraite, transferts aux collectivités, part
de l'investissement), chacune selon la règle de moteur/depenses/ministeres.py (210 Md€) ; défense hors pensions et
contribution à l'UE, au PIB (88) ; collectivités hors RSA, autonomie et investissement (230) ; reste 106 Md€. Prudent :
8,9 % en 2037.

## 4 novembre 2026 — Statu quo : validation

Contrôles contre le COR (retraites, calage et hors calage), la Commission européenne (retraites 2070 : 13,6 % avec une
démographie plus ancienne, contre 15,3 %), le HCFP (dette fin 2028 125 %, intérêts 2029 102 Md€), la Cour des comptes
(déficit primaire et dette qui monte) ; tests ajoutés. Tableau de bord du statu quo publié.

DÉCISION d'Adrien (4 novembre 2026) : les prestations du statu quo (famille, logement, RSA, prime d'activité, AAH)
suivent les salaires, pas les prix. Prudent : solde primaire −5,1 % du PIB en 2060 (−4,3 sur les prix), déficit 19,4 %
en 2050 (18,1). Point de neutralité avec le programme (revenu universel sur les prix) signalé dans docs/statu_quo.md.

DÉCISION d'Adrien (4 novembre 2026) : la différence d'indexation est gardée et assumée. Le statu quo garde le niveau
relatif des prestations (salaires) ; le programme revalorise le revenu universel sur les prix, ce qui le fait baisser
par rapport aux salaires dans le temps : c'est un objectif du programme, à présenter comme une mesure à part entière.

## 4 novembre 2026 — Statu quo : cellules de salariés (même méthode que le programme)

Question d'Adrien : le statu quo suit-il la méthode des cohortes ? Retraités : oui (génération par génération) ;
salariés : non jusqu'ici (nombre × salaire moyen). `statu_quo.cellules_salaries` : cellules par âge et tranche de
salaire comme moteur/cohortes.py, prélèvements et TVA par OpenFisca. Effet faible (prudent 2050 : 19,4 %, inchangé à
0,1 point ; optimiste +0,2 point), mais méthode identique des deux côtés.

## 4 novembre 2026 — Écologie de droite mesure par mesure (première passe)

Recettes instrument par instrument contre les impôts actuels, dépenses ligne par ligne, périmètre complété (ventes et
tarifs de l'État, des opérateurs et des hôpitaux), effets macro par canal. Résultats inchangés (lisibilité). Constats :
docs/ecologie_de_droite_mesures.md (TVA et accises −82 Md€, impôt unique −66 et −68, santé : classement).

## 4 novembre 2026 — Deuxième passe : salariés recalculés sur le noyau

Impôt unique (privé, public) et TVA des salariés recalculés sur les cellules communes : moteur du programme retrouvé
(pas d'erreur), effet sur les naissances isolé (−16 Md€ en 2073), point de méthode sur l'IA (à unifier avec les
dépenses). Déficit inchangé à 0,1 point près.

## 4 novembre 2026 — Troisième passe : retraites et revenu universel mesure par mesure

Retraites : gel de l'ancien système (−87 Md€ en 2050), fermeture aux nés à partir de 1980 (−307 Md€ en 2073), âge à
67 ans, contribution de solidarité, attente 65-67 ans ; contrôle : ancien système sans gel = statu quo des mêmes
générations (pas d'erreur). Revenu universel : −15 Md€ contre les prestations remplacées, revalorisation sur les prix
isolée (−41 Md€ en 2073, décision d'Adrien), RUI étudiant, naissances. Statu quo des pensions par génération
(`depenses_generations_recentes`). Déficit inchangé.

## 4 novembre 2026 — Quatrième passe : santé et autres dépenses mesure par mesure

- `mesures_sante` : santé du programme contre santé + invalidité du statu quo (même périmètre) ; les deux pentes
  concordent à 2 Md€ près ; gestion de l'assurance maladie en classement ; vraies mesures −8 Md€ (2029) à −19 (2073).
- `mesures_autres` : missions ministère par ministère (alignement du coût des agents à part, investissement de l'État
  comparé dans les ministères), défense et UE, collectivités (besoin laissé au budget), investissement (local, État,
  fonds), reste. `decomposition_collectivites` : 230 contre 304 Md€ en 2029, poste par poste.
- Corrections : invalidité comptée deux fois dans l'écart du RUI (9 Md€) ; défense du statu quo au niveau de la loi de
  programmation actualisée (76,3 Md€ en 2030, `statu_quo.defense_trajectoire`, DÉCISION « loi actuelle ») : déficit
  du statu quo 6,1 % en 2029 (au lieu de 5,6).
- Point ouvert : le fonds finance ~63 Md€ par an d'investissement hors budget ; s'il est classé administration
  publique, ~2 points de PIB reviennent au déficit de Maastricht.

## 4 novembre 2026 — Comparateur des programmes

- `outils/export_comparaison.py` : trajectoires, écarts au statu quo par grand poste (dont intérêts et effet du PIB
  sur les ratios, pour que la somme retrouve l'écart de déficit) et mesures, pour tous les programmes de
  `noyau.programmes_disponibles()` (statu quo + chaque dossier `programmes/<nom>/`). Un nouveau programme n'a qu'à
  définir `libelle`.
- Tableau de bord « Comparateur des programmes » (claude.ai) sur ces trois fichiers : relancer l'export et remplacer
  les fichiers à chaque nouveau chiffrage.

## 5 novembre 2026 — Relecture indépendante n° 3 (corrections)

Relecture par un agent sans historique du projet (constats complets : `docs/relecture.md`, section du 5 novembre).
Corrigé :
- **Prime de taux liée à la dette bornée et commune** (C1, I4). Sans borne, le statu quo atteignait 79 % de taux
  apparent et 14 000 % de dette/PIB en 2073 (prudent), et les programmes qui se désendettent obtenaient des taux réels
  négatifs. Désormais : prime bornée dans [−0,8 ; +4] points (`macro.prime_dette_bornes`) ; référence = dette/PIB du
  statu quo en 2029, commune à tous ; ratio = dette/PIB publiée de l'année précédente, calculé par le noyau seul (le
  contexte `pib_prime` fourni par le programme est supprimé) ; une dette négative compte pour zéro ; la baisse totale
  (prime + `baisse_spread` du programme) ne dépasse pas l'écart OAT − Bund. Même définition dans `macro.py` : le pont
  noyau = moteur du programme reste exact (test_noyau).
- **Défense comptée deux fois de 2026 à 2027** (I1) : le bloc part du PLF 2027 (63,4 Md€ hors pensions,
  `statu_quo.defense_2027_courants`) et non de 2026 ; la hausse vers la loi de programmation part de ce niveau
  (8,8 Md€ au lieu de 13,9). Le statu quo perd environ 5 Md€ de dépense fictive, que le programme comptait comme une
  économie en retirant « autres ».
- **TVA des transferts du statu quo** revalorisée comme les prestations (salaires) au lieu des prix.
- Textes périmés (README, `ancien_systeme.py`, en-tête de `statu_quo.py`, notes du RUI) alignés sur les décisions
  (67 ans ; minimum de l'inflation et de la croissance nominale ; prestations du statu quo sur les salaires) ; test des
  prestations « sur les prix » qui passait pour une mauvaise raison ; code mort retiré.

Effet (déficit, % du PIB, prudent) : statu quo 2037 9,90 → 9,65, 2050 21,67 → 20,75 ; programme 2050 3,42 → 3,49,
2073 3,11 → 3,24 (la clause absorbe l'essentiel jusqu'en 2037).

Non corrigé, à trancher : `macro.part_pib_tendanciel_au_solde` (10 % du PIB en plus au solde, sans source : C2),
santé indexée sur le salaire par tête (I2), scénario de crise du statu quo meilleur que le prudent jusqu'en 2045 (I3),
architecture « mesures seules » pour les autres programmes (C3).

## 5 novembre 2026 — Décisions d'Adrien sur la relecture (points 1 à 4)

- **Santé (point 2) : surplus financé par les produits nocifs.** Le surplus de dépenses de santé au-delà d'une part
  constante du PIB est couvert, avec un an de décalage, par une accise supplémentaire sur le tabac, l'alcool et les
  produits sucrés et ultra-transformés (`moteur/sante.accise_produits_nocifs`, `sante_produits_nocifs.*`). La hausse
  de prix réduit le volume taxé (fuite hors réseau comprise) et la consommation ; la baisse de consommation réduit les
  soins avec délai. Plafonds de hausse de prix : tabac +100 %, alcool +50 %, sucrés +30 %. Prudent 2073 : surplus
  102 Md€, recette 47 Md€, soins évités 5 Md€, **50 Md€ non couverts** (les plafonds sont atteints vers 2058) ;
  médian : 12 Md€ non couverts. Remplace le garde-fou de la v235.
- **Crise (point 3).** Productivité 0,4 % (bas des variantes du COR), chômage +2 points durables en trois ans
  (`chomage.hausse_crise`), taux de marché +0,5 point (`macro.ecart_taux_scenario`), pour le statu quo et les
  programmes. Test : déficit du statu quo rangé crise ≥ prudent ≥ médian ≥ optimiste chaque année.
- **Économies saisies (point 4).** Règle commune (`moteur/mesures.py`) : une économie saisie en montant n'est retenue
  qu'avec au moins deux sources indépendantes (colonne `sources`), jamais le programme ou une déclaration de candidat ;
  sinon elle compte pour zéro et est listée comme écartée. Taux de réalisation par scénario (crise 50 %, prudent 60 %,
  médian 80 %, optimiste 95 %). Aucune des 16 économies saisies du programme n'a encore ses sources : **22,5 Md€ à
  plein effet écartés** jusqu'au sourçage. Restent hors de la règle pour l'instant : les coupes de missions
  (`economies_missions.coupes`) et la décomposition des collectivités.
- **Dividende de croissance (point 1).** La part d'un euro de PIB en plus qui passe au solde n'est plus 10 % sans
  source : elle est mesurée sur le programme lui-même (`moteur/macro.dividende_croissance`), en recalculant tous ses
  postes avec une productivité relevée de 0,3 point. Résultat : 2 % en 2030, 8 % en 2037, 7 % en 2050, 14 % en 2073
  (le revenu universel revalorisé sur les prix fait monter le dividende avec le temps). Linéarisation autour du
  prudent : la refonte complète (chaque poste recalculé aux salaires et au PIB de chaque scénario) reste à faire.

Déficit du programme (prudent) : 2037 3,01 → 3,18 % ; 2050 3,49 → 3,46 % ; 2073 3,24 → 3,08 %. Médian 2050 : 0,21 →
0,88 % ; optimiste 2050 : −1,75 → −0,81 %. Crise 2050 : 4,39 → 8,95 %.

## 5 novembre 2026 — Économies sourcées ou estimées, antidépresseurs

- **Les 16 économies saisies du programme** sont passées en « estimation » (`mesures_economies.csv`, colonnes
  `sources`, `methode`, `estimation_<scénario>`) : aucune n'avait deux sources indépendantes qui chiffrent la mesure
  telle qu'écrite ; chacune a maintenant ses sources pour les bases et une estimation propre par scénario (décision
  d'Adrien : « s'il n'y a pas de source, estimation prudente / médiane / optimiste »). Total à plein effet : crise
  9,7 Md€, prudent 12,3, médian 17,6, optimiste 22,5, contre 22,5 saisis. Écarts les plus nets : cabinets de conseil
  (0,05 Md€ en prudent contre 0,5 saisis : l'État y dépense environ 0,1 Md€ par an), aide médicale d'État (0 en
  prudent, d'après le rapport Évin-Stefanini), collectivités (5 au lieu de 8), effets sur les caisses de sécurité
  sociale et les achats. Les estimations portent déjà leur taux de réalisation.
- Les estimations du médian et de l'optimiste passent au solde par l'écart au prudent (`mesures.ecart_scenario`,
  canal « tendance_et_ecole » du moteur du programme).
- **Antidépresseurs** (décision d'Adrien) : reste à charge hors dépression modérée à sévère et prescription recentrée
  sur les recommandations de la HAS (2017). Estimation : crise −0,05 Md€, prudent 0, médian 0,1, optimiste 0,2. Le
  médicament coûte peu, les complémentaires reprennent une partie du reste à charge, et la baisse de l'usage dans la
  dépression légère suppose plus de psychothérapie ; un sous-traitement des dépressions modérées coûterait en arrêts de
  travail. Base de remboursement à sourcer (Medic'AM, classe N06A). Ligne au poste santé.
- Comparateur des programmes (claude.ai) mis à jour avec l'export du jour.

Déficit du programme (prudent) : 2037 3,01 % ; 2050 3,08 % ; 2073 2,67 %. Médian 2050 0,31 % ; crise 2050 7,65 %.

Corrigé en relançant les tests : le dividende de croissance est mesuré sans l'accise sur les produits nocifs (plafonnée,
donc non linéaire), qui rendait les effets des mesures non additifs (écart de 26 Md€ en 2050, 5,5 après) ; le choc de
chômage et de taux de la crise démarre après le point de départ commun de 2029.

## 5 novembre 2026 — Émissions et empreinte carbone (branche `ecologie-emissions`)

- Décision d'Adrien : la baisse des émissions suit l'activité, le progrès technique et la part importée
  (`moteur/ecologie/emissions.py`, `docs/ecologie.md`), au lieu du taux fixe de −1,9 % par an.
- **Erreur trouvée** : la recette carbone ne faisait répondre l'assiette au prix qu'à partir du prix de 2029 ; le saut
  depuis le prix du statu quo n'érodait jamais l'assiette. Recette et émissions partagent désormais la même équation
  (option `ecologie_options.emissions_activite`). Déficit publié du prudent : 2037 3,01 → 3,39 % ; 2050 3,08 → 3,72 %.
- Comparateur : `sorties/comparaison_ecologie.csv`.
- Décisions d'Adrien du 05/11/2026 (après-midi) : correction de la recette carbone validée et fusionnée dans `main` ;
  hypothèse de gaz en secours pendant la sortie du nucléaire de Tondelier validée ; les quatre mesures de Tondelier
  estimées à zéro faute de source (ferroviaire, agriculture, voitures de fonction, renouvelables) sont sourcées.
- 05/11/2026 (soir) : réponse au prix du carbone corrigée (hausse du prix de l'énergie triplée par erreur, voir
  docs/ecologie.md). Écologie de droite, prudent : prix du carbone −24 Mt en 2037 (au lieu d'environ −49), mesures
  −26 Mt en 2037 et −30 Mt en 2050 ; déficit publié 3,01 % en 2037 (3,39 avec l'erreur, 3,01 avant le couplage) et
  3,23 % en 2050 (3,72 avec l'erreur, 3,08 avant).

## 6 novembre 2026 (soir) — Programme Mélenchon (L'Avenir en commun, 5e édition)

- Livre de 224 pages transmis par Adrien et lu en entier ; fiche de 215 mesures, citations vérifiées page par page
  (`programmes/melenchon/mesures.yaml`, 0 erreur) ; chiffrage dans `parametres.yaml`, méthode et arbitrages dans
  `docs/melenchon.md`. Le livre ne chiffre rien : chaque montant est estimé par le modèle.
- Nouvelle brique `bibliotheque.baisse_age_legal_detail` : baisse de l'âge légal selon un calendrier de profils de
  départ (retrouve à l'euro près le retour à 62 ans de Tondelier, test).
- Résultat (prudent) : −4,7 points de PIB de solde en 2029, −9,7 en 2032, −11,6 en 2037 ; déficit 2037 28,1 % contre
  9,7 % au statu quo (optimiste : 18,9 contre 8,2).

## 7 novembre 2026 — Mélenchon : émissions et sensibilités

- Remarque d'Adrien : le résumé du comparateur était partisan et oubliait l'écologie. Résumé réécrit ; treize mesures
  écologiques chiffrées en tonnes (`melenchon_ecologie`) : −8,6 Mt en 2037 dans le prudent, −17 dans le médian, du
  même ordre que Tondelier.
- Sensibilités (`docs/melenchon.md`) : lectures ambiguës et hypothèses communes bougent le solde de 2037 d'un point
  au plus sur douze. Incohérence trouvée, à valider : le multiplicateur ne passe pas au scénario miroir pour une
  relance (l'éviction et l'offre le font). Piste des crèches écartée (Insee Analyses n° 55, 2020).
- Décision d'Adrien du 07/11/2026 : multiplicateur en miroir pour une relance, pour tous les programmes
  (`programme_simple.multiplicateur`, Tondelier compris) ; test `test_multiplicateur_en_miroir_pour_une_relance`.
  Effets surtout en crise et en optimiste (tableau dans `docs/melenchon.md`).

## 11 novembre 2026 — Phase 1 de la roadmap : fiabiliser

- **Régression complète** : 380 tests passent ; le seul échec (`test_chomeurs_seniors_ajoutes`, moteur d'Écologie
  de droite) est antérieur à ces corrections et corrigé dans le commit deec27a (chômeurs seniors stables après la
  montée en charge, avec l'âge légal réel des générations).
- **Contrôle COR 2045 : cause trouvée.** `ancien_systeme.pension_nouveaux_relative` = 0,935 (nouveaux retraités
  rapportés à la moyenne de tous les retraités, DREES) appliqué contre un stock de pensions uniforme : la pension
  moyenne baissait mécaniquement de 6,5 % pendant le remplacement du stock (2029-2050). Avec 1,0 (noria quasi nulle
  depuis 2017, DREES) et l'érosion recalée sur 2070 (0,36 → 0,595 %) : 2030 14,09 %, 2045 14,24 %, variantes de
  productivité inchangées, sans calage sur 2045. Tolérance du test ramenée de 0,4 à 0,15 point.
- **Seniors** : `seniors.part_concernee` 0,4 → 0,42, recalé sur le nouveau calcul (retour de 64 à 62 ans :
  ≈ 1,11 million de non-retraités à plein effet ; 0,42 en garde ≈ 470 000, comme l'étude d'impact de 2023). La
  proposition de la relecture (0,9 à 1) supposait des pensions recalées sur 0,47 million de retraités : non retenue.
- **Points du rapport appliqués** : postes de Philippe sur la règle commune (120 000 / 200 000 / 250 000 / 250 000,
  plafonnés aux 250 000 annoncés) ; enseignants de Glucksmann sur la même assiette que Philippe (35 Md€ bruts,
  coefficient 1,9 : 4,6 à 6,7 Md€ au lieu de 3,5 à 5) ; embauches d'Arthaud avec un `fp_taux` par versant (0,47
  hôpitaux et transports, CNRACL ; 0,50 éducation) au lieu de 0,57.

## 11 novembre 2026 — Phase 2 de la roadmap : combler les trous de chiffrage

- **Émissions des cinq derniers programmes** (Glucksmann, Attal, Philippe, Retailleau, Lisnard) : groupes
  `<nom>_ecologie`, lus par `ProgrammeSimple.mesures_ecologie` (Mélenchon y passe aussi, résultats inchangés).
  Tableau dans docs/ecologie.md.
- **Tonnes à zéro sourcées** : bâtiments publics de Tondelier et de Mélenchon, règle commune de 0,05 t par an pour
  1 000 € de rénovation.
- **Retailleau, capitalisation obligatoire** (RET-RET-02) : 1 % du brut des entrants depuis 2028, moitié salarié,
  moitié employeur, plafond de 40 € par mois ; fonds hors des administrations publiques ; au budget, la part des
  employeurs publics (0,2 Md€ en 2037) ; emplois perdus par le canal d'offre (≈ 5 600 en 2037, 20 000 en 2050).
- **Attal et Lisnard, caisses de retraite** : la lecture à droits inchangés, caisses compensées par l'État, est
  vérifiée et écrite ; la compensation est interne aux administrations publiques.
- **Tondelier, taxe sur les bouteilles en plastique** (REC-46), absente des paramètres : estimée à 0,1 / 0,15 /
  0,25 / 0,35 Md€ ; recette sans dépense affectée, donc sans coût à financer.
- **Éducation et recherche** : canal d'offre de long terme (docs/offre.md), instruments `education` et `recherche`
  sur les mesures concernées de huit programmes.

## 11 novembre 2026 — Phase 3 : candidats manquants, Rassemblement national

- Liste des candidats absents du comparateur : docs/candidats_manquants.md (votons-2027.fr ; programmes-2027.fr
  inaccessible depuis l'outil).
- **Le Pen (RN), chiffrage partiel** : `programmes/le_pen/`, docs/le_pen.md. Contre-budget du 6/10/2026 non publié :
  sources de seconde main. Aucune économie annoncée reprise ; obstacles juridiques documentés (Union européenne,
  priorité nationale). Prudent 2037 : déficit 13,0 % (statu quo 9,5 %), émissions +8 Mt.
- Comparateur : données de l'artifact non modifiables par l'outil tant qu'il est public ; fichiers téléversés.
- **Roussel (PCF)** : `programmes/roussel/`, docs/roussel.md. Programme 2027 non publié : discours de 2025-2026.
  Nouveau dans le noyau : PIB hors emploi (`pib_en_plus`) pour les heures perdues des 32 heures. Prudent 2037 :
  déficit 29,6 % (statu quo 9,5 %), solde primaire −9,1 points, PIB −4,5 %.

## 12 novembre 2026 — « Écologie de droite » sur le noyau commun, plus aucun moteur propre

DÉCISION d'Adrien : « change mon programme pour qu'il tourne sur le même moteur, je ne veux aucun moteur ». Trois
choix : effets propres recodés en mesures ; clause de trajectoire en règle générique du noyau (publiée avec et sans
règle) ; ancien moteur supprimé tout de suite, avec ses tests de reproduction de la v235.

**Ce qui change dans le code**
- Supprimés : `moteur/macro.py`, `moteur/trajectoire_annuelle.py`, `moteur/simulation.py`, `tests/test_macro_v235.py`,
  `tests/test_crise_v235.py`, `tests/test_trajectoire_annuelle_v235.py`. `python -m moteur.noyau` remplace
  `python -m moteur.simulation` (README, lanceur, docs/relecture.md).
- Noyau : deux mécanismes génériques. **Dynamiques** (objets à état par scénario : `debut(t, etat)` renvoie PIB,
  recettes, blocs, participations, emploi, chômage ; `fin(t, etat)` met à jour l'état). **Règle de trajectoire**
  (`Regle`, `Levier` : cible de déficit, leviers ordonnés avec capacité et rendement, mesures automatiques ; levier
  utilisé = min(reste à couvrir / rendement, capacité)). Publiés chaque année : `deficit_sans_regle`, `regle`,
  `dynamiques`.
- Programme : `budget.py` (registre du budget, ex-`trajectoire_annuelle`), `effets.py` (canaux recodés en mesures,
  fonds d'épargne obligatoire comme dynamique, clause comme règle), `programme.py` (assemble). Le multiplicateur,
  l'offre (seniors), les taux, le chômage (formule commune) et la conjoncture (Okun) viennent du pipeline commun.
- Boucle de l'IS d'investissement (`annees_sous_seuil`) : calculée sur un passage du noyau de la variante sans hausse.
- Outils et modules portés sur le noyau : `is_investissement`, `entreprises_cellules`, `attribution`, `restitution`,
  `sensibilite`, `incertitude`, `statu_quo`, `outils/leviers`, `levier_is`, `is_progressif`.

**Vérifié avant suppression** (scénario de crise, comparaison avec l'ancien moteur) : le fonds et la règle redonnent
exactement le capital (6,0 / 53,6 / 211,0 / 743,8 Md€ en 2030 / 2037 / 2050 / 2073), la contribution (35,1 / 36,2 /
37,3 / 32,1), la baisse du RUI (19,1 / 19,1 / 18,2 / 14,4) et le PIB d'épargne du fonds. Les canaux érosion de l'IS,
réactions, fraude TVA, logement, productivité, IA, carbone, TVA santé, permis, dirigeants et aides à la construction
s'écartent de moins de 0,1 Md€.

**Déficits (% du PIB), avant (pont sur l'ancien moteur) → après**

| Scénario | 2029 | 2037 | 2050 | 2073 |
|---|---|---|---|---|
| prudent | 2,92 → 3,32 | 2,75 → 3,00 | 2,83 → 3,29 | 2,02 → 3,00 |
| crise | 2,93 → 3,86 | 4,37 → 5,26 | 7,10 → 10,41 | 40,3 → 57,3 |
| médian | 2,76 → 3,00 | 1,84 → 1,96 | 0,39 → 0,26 | −6,99 → −6,63 |
| optimiste | 2,77 → 3,00 | 0,35 → 0,29 | −1,14 → −1,70 | −10,98 → −10,95 |

**Pourquoi les résultats bougent** (chaque écart vient d'un choix de méthode commun, pas d'un paramètre changé)
1. **Multiplicateur sur l'impulsion des mesures** (commun à tous les programmes) à la place du canal « ajustement
   budgétaire » de l'ancien moteur, qui l'appliquait au solde. En 2029 au prudent : −78,8 Md€ de PIB contre −29,5. C'est
   la cause probable de l'écart de 2029 (à vérifier par attribution) : la règle atteint ses plafonds (5 points
   d'épargne, RUI au plancher) et le déficit reste à 3,3 %, alors que le pont donnait 2,9 %.
2. **Seniors** : l'offre commune (`offre.seniors`, avec reports) remplace le canal de court terme de l'ancien moteur.
3. **Démographie et tendance** : ne sont plus des effets sur le PIB. Le registre du budget est bâti sur la tendance et la
   population prudentes ; l'écart avec chaque scénario reste donc codé en mesures « méthode » (ia, tendance,
   démographie, économies du registre, santé). Dette technique : bâtir le registre par scénario.
4. **Rétroaction dette → prime → intérêts** : le noyau l'applique à tout l'écart, pas seulement au statu quo ; elle compose
   les écarts de la crise (déficit de 2050 : 10,4 contre 7,1 dans le pont). Écarts à décomposer au prudent et au médian.
5. **Effet récessif de la baisse du RUI** (année + 1) : multiplicateur lu selon le sens de la baisse, sans contrainte de
   capacité sur l'effet de la clause.
6. **Option `macro.depart_commun`** : supprimée avec l'ancien moteur (paramètre conservé, désactivé). La convergence
   des scénarios vers un point de départ commun n'existe plus ; chaque scénario part de son statu quo.
7. **Tests de reproduction de la v235 supprimés** (décision d'Adrien) ; `reference="v235"` ne sert plus qu'à lire les
   paramètres de l'époque.

**À faire** : retirer les mesures « méthode » (registre par scénario) ; l'indexation `(1+tend0)^n` est conservée ;
le canal d'emploi du fonds n'est pas dans `emplois_canaux`.

## 12 novembre 2026 (suite) — Relecture indépendante : vrai scénario sans règle, créances de la règle, performance

Une relecture par un agent indépendant (11/11/2026) a relevé, entre autres, deux défauts de publication de la règle de
trajectoire et une lenteur. DÉCISION d'Adrien : corriger ses points 1 et 5 ; les points 2 à 4 (impulsion du
multiplicateur, équité des canaux entre programmes, registre par scénario) attendent ses arbitrages.

**1. Vrai scénario sans règle.** Le « déficit sans règle » publié était celui de l'année avant les leviers, avec la dette
et le PIB déjà modifiés par la règle des années précédentes : ce n'était pas un scénario sans règle. Désormais :
- `deficit_avant_regle` : l'ancien chiffre (année par année, avant les leviers ; sert à la règle elle-même et au
  seuil de la hausse conditionnelle de la déduction de l'IS, convention de l'ancien moteur inchangée) ;
- `sans_regle` (déficit, dette, PIB, chômage…) et `deficit_sans_regle` : le scénario complet recalculé sans la règle,
  par `noyau.simuler`. Pour Écologie de droite, tout est recalculé avec `clause.active = False`
  (`entrees_sans_regle`) : la clause pèse aussi hors de ses leviers, par la hausse conditionnelle de la déduction de
  l'IS, qui suit le déficit avant clause. Testé : identique à un passage avec la clause désactivée.

**2. Créances de la règle.** La contribution prise par la règle est rendue aux ménages à 67 ans avec le rendement du
fonds : c'est un emprunt, hors dette de Maastricht. Une dynamique peut maintenant déclarer une `quasi_dette()` ; le
noyau publie `quasi_dette` (Md€) et `dette_et_quasi_dette_pib`. L'export du comparateur et la restitution ont les
colonnes `deficit_sans_regle`, `dette_pib_sans_regle`, `dette_et_quasi_dette_pib`.

| Prudent | Publié | Sans règle (nouveau) | Ancien « sans règle » | Dette publiée | Dette sans règle | Créances | Dette + créances |
|---|---|---|---|---|---|---|---|
| 2037 | 3,00 | 5,12 | 4,32 | 123 % | 140 % | 332 Md€ | 133 % |
| 2050 | 3,29 | 5,69 | 4,80 | 124 % | 153 % | 625 Md€ | 141 % |
| 2073 | 3,00 | 8,45 | 3,47 | 132 % | 209 % | 561 Md€ | 147 % |

Crise 2073 : 57,3 publié, 85,8 sans règle, créances 1 135 Md€. Au médian et à l'optimiste, le scénario sans règle finit
un peu mieux que le publié (médian 2073 : −8,4 contre −6,6) : sans la clause, le déficit reste plus longtemps au-dessus
du seuil de la hausse conditionnelle de la déduction de l'IS (moins de déduction, plus d'IS), et il n'y a pas de
créances à rendre. Le seuil de cette hausse lit toujours le déficit avant clause année par année : à confirmer.

**3. Performance et nettoyage (point 5).**
- `tva.taux_effectifs` (relisait le CSV des produits à chaque appel, ~227 000 fois par passage) et
  `inflation.facteur_prix` (~750 000 appels) gardés dans le cache des paramètres : le prudent d'Écologie de droite
  passe de 49 s à 25 s ; les quatre scénarios, avec en plus le scénario sans règle, en ~50 s (contre ~116 s).
  Résultats publiés inchangés.
- Caches indexés par `id(p)` (programme_simple et plusieurs programmes) : les instances de `Parametres` restent en vie
  jusqu'à la fin du processus (`parametres._VIVANTES`), donc un id ne peut plus être réattribué à une autre instance.
- Supprimés : `moteur/trajectoire.py` (second bloc comptable, utilisé seulement par son test de reproduction v235) et
  `tests/test_trajectoire_v235.py` ; imports morts d'effets.py ; références à `moteur/macro.py` dans les textes.
- Tests rendus non conditionnels (règle générique du noyau ; règle d'Écologie de droite en 2037) ; nouveau test du
  scénario sans règle.

**Restent ouverts** (relecture, points 2 à 4) : impulsion du multiplicateur d'Écologie de droite (natures
« classement », écarts de méthode de 2029, recettes carbone et énergie hors multiplicateur, poids du RUI) ; canaux
propres au programme absents des autres (fraude TVA, productivité, IA, école, écart de taux) ; comparateur qui montre
ce programme après règle et les autres sans ; mesures « méthode » ; variante « fonds dans les APU » ; inflation
d'Écologie de droite encore tirée de `macro.effort_2029` et non de l'impulsion calculée.

## 12 novembre 2026 (suite) — Relecture indépendante, points 2 et 4 : impulsion du multiplicateur, fonds dans les APU

DÉCISION d'Adrien : traiter les points 2 et 4 de la relecture.

**Point 2 — ce qui alimente le multiplicateur d'Écologie de droite.** Quatre corrections :
1. les reclassements (nature « classement » : gestion de l'assurance maladie comptée en santé, aide sociale à
   l'enfance, +22,3 Md€) entrent dans l'impulsion : leur contrepartie y était déjà, donc 22 Md€ de resserrement étaient
   comptés en trop ;
2. le revenu universel est pondéré comme les transferts qu'il remplace (poids 0,8 au lieu de 1) ;
3. la recette carbone du scénario (prélèvement sur la consommation, poids 0,55) et l'IS sur les taxes d'énergie
   supprimées (poids 0,3) entrent dans l'impulsion : ces recettes échappaient au multiplicateur ;
4. pas de retrait forfaitaire d'« écarts de méthode » en 2029 : une fois ces corrections faites, l'impulsion calculée
   de 2029 (−57,9 Md€ au prudent, −55,2 au médian) retrouve l'effort que le programme déclare (macro.effort_2029 −
   assouplissement + prélèvement sur les anciennes pensions : −54,4 et −51,3 Md€). L'écart restant (3 à 4 Md€) est la
   borne de ce que les écarts de méthode pèsent dans l'impulsion. Test : écart inférieur à 15 %.

Effet (déficit publié, % du PIB) : prudent 2029 3,32 → 3,00 (la règle n'est plus au maximum) ; crise 2029 3,86 → 3,35,
2073 57,3 → 55,4 ; médian et optimiste presque inchangés. Vrai scénario sans règle, prudent : 4,83 / 5,07 / 5,56 / 7,63
(2029 / 2037 / 2050 / 2073).

**Point 4a — variante « fonds dans les administrations publiques ».** `EcologieDeDroite.variante_fonds_apu` et
`python -m outils.variante_fonds_apu` (sorties/variante_fonds_apu.json) : les investissements financés par le fonds
(missions transports, énergie, France 2030 ; opérateurs, hôpitaux, sécurité sociale ; investissements locaux repris :
73 Md€ en 2029) comptés en dépense publique. Même économie, seul le classement change ; convention haute (l'épargne
obligatoire n'est pas comptée en recette publique). Déficit prudent : 5,4 % en 2029, 6,1 % en 2037, 10,1 % en 2050
(dette 190 % du PIB contre 123 %) ; médian : 5,0 / 3,4 / 3,7 %. La règle de trajectoire ne suffit plus au prudent.

**Point 4b — registre du budget par scénario : mesuré, pas encore adopté.** Essai : registre recalculé avec la colonne
du scénario à la place de la colonne prudente (comme le calcul de crise), comparé aux mesures « méthode » :

| Écart de solde primaire avec le registre prudent (Md€) | 2037 | 2050 | 2073 |
|---|---|---|---|
| médian : registre par scénario | 15,2 | 25,8 | 141,7 |
| médian : mesures « méthode » actuelles | 19,6 | 33,9 | 118,6 |
| optimiste : registre par scénario | −0,5 | 28,5 | 211,9 |
| optimiste : mesures « méthode » actuelles | 25,3 | 29,5 | 202,9 |

Même ordre de grandeur, mais des écarts de 5 à 25 Md€ selon l'année. L'essai n'est pas adopté tel quel : plusieurs
modules rendent des valeurs indexées par nom de scénario (emploi : le prudent est la moyenne des jeux crise et médian ;
réactions des hauts revenus, inactifs, choc de chômage) et ne suivent pas la colonne ; l'IA n'est pas dans le registre.
Reste à faire : une copie de paramètres par scénario (`en_scenario`), l'audit de ces modules, puis le retrait des
mesures « méthode ».

**Correction au passage.** `moteur/attribution.py` : la décomposition lisait la charge de la dette nominale alors que
le solde du noyau porte les intérêts réels (écart de 0,003 Md€, test `test_decomposition` en échec depuis la migration).

## 12 novembre 2026 (suite) — Canaux déclarés, ouverts à tous les programmes

Critique : Écologie de droite était seul à compter des effets propres hors du tronc commun (fraude à la TVA,
productivité, adoption de l'IA, niveau des élèves, baisse de l'écart de taux) et une règle de trajectoire.
DÉCISION d'Adrien (trois options proposées : version « règles communes » du programme dans le comparateur, suppression
de ces canaux, ouverture à tous) : **ouvrir à tous**.

- `moteur/canaux_declares.py` : tout programme peut déclarer ces cinq canaux et une règle de trajectoire dans le
  groupe `<nom>_canaux` de son parametres.yaml, avec les formules d'Écologie de droite. Canal absent : zéro. Nom de
  canal inconnu : erreur. Chaque valeur porte statut et source, comme tout paramètre.
- Le PIB en plus rapporte la part des recettes dans le PIB du statu quo (règle du canal d'offre commun) ; Écologie de
  droite garde son dividende de croissance calculé sur son propre budget (écart de convention à garder en tête).
- Règle de trajectoire déclarée : cible, dernière année, scénarios, leviers (capacité en part du PIB, sur les recettes
  ou sur un bloc de dépenses) ; c'est la règle du noyau. `ProgrammeSimple.entrees` et `Tondelier.entrees` la passent au
  noyau, qui publie alors le programme avec et sans règle, comme Écologie de droite.
- Ces effets sont publiés sous le nom « Canal déclaré : … » (nature « effet_macro »), hors multiplicateur.
- Aucun programme ne déclare de canal à ce jour : les résultats des autres candidats sont inchangés (testé). Chiffrer
  ces canaux pour chacun reste à faire, programme par programme, avec ses sources.
- Tests : `tests/test_canaux_declares.py` (sans canal rien ne change, canal inconnu refusé, chaque canal, règle
  déclarée avec scénario sans règle égal au programme sans la règle).

## 12 novembre 2026 (suite) — Canaux déclarés pour les autres programmes : barème commun (IA, école)

DÉCISION d'Adrien : ajouter les canaux pour tous les programmes. Règle appliquée, mécanique pour rester neutre : un
programme reçoit un canal dès qu'une de ses mesures porte sur le même objet, **à la valeur d'Écologie de droite**,
quelle que soit l'ampleur de la mesure (statut HYPOTHÈSE, mesure citée dans la note du paramètre).

| Canal | Valeur (crise / prudent / médian / optimiste) | Programmes |
|---|---|---|
| Adoption de l'IA | 0 / 5 % / 10 % / 43 % du gain de l'IA | Attal, Glucksmann, Lisnard, Philippe, Retailleau, Zemmour |
| École (niveau des élèves) | 0 / 0 / 0 / 0,1 écart-type, à partir de 2045 | Arthaud, Attal, Glucksmann, Le Pen, Lisnard, Mélenchon, Philippe, Retailleau, Roussel, Tondelier |

Recettes en plus en 2050 : 0,6 Md€ au prudent, 5,3 au médian, 42,7 à l'optimiste (IA et école) ; école seule : 1,0 Md€
à l'optimiste en 2050, 25,5 en 2073. Rien dans le scénario de crise.

**Non déclarés, et pourquoi** :
- fraude : Le Pen, Mélenchon, Roussel, Tondelier et Zemmour ont déjà leur mesure de lutte contre la fraude, à
  l'estimation commune ; ajouter le canal la compterait deux fois. Les autres programmes n'ont pas de mesure ;
- productivité : celle d'Écologie de droite repose sur l'ensemble de ses réformes (OCDE 2014) ; dire quels autres
  programmes y ont droit est un jugement programme par programme — à décider par Adrien ;
- baisse de l'écart de taux : annoncer une règle d'or (Attal, Bertrand, Le Pen, Philippe, Retailleau) ne suffit pas à
  la justifier quand le déficit simulé du programme reste au-dessus du statu quo ; il faut un critère sur le résultat,
  à décider ;
- règle de trajectoire : ces mêmes programmes annoncent une cible, mais pas les leviers (quel impôt, quelle dépense) ;
  les inventer reviendrait à saisir une économie annoncée, ce que la règle commune interdit.

Limite du barème : il ne distingue pas un plan de 200 Md€ d'une mesure non chiffrée. À affiner mesure par mesure.

## 12 novembre 2026 (suite) — Arbitrages d'Adrien sur l'équité entre programmes

Réponses d'Adrien aux huit questions ouvertes :
1. **Productivité** (arbitrage laissé à Claude) : aucun autre programme pour l'instant. Elle reste propre à Écologie de
   droite et signalée comme telle : dire quels programmes ont un ensemble de réformes structurelles qui la justifie
   est un jugement politique, sans critère mécanique. Le canal reste ouvert (`<nom>_canaux.productivite`).
2. **Baisse de l'écart de taux : sur le résultat, pour tous**, Écologie de droite comprise. Ce n'est plus un canal
   déclaré ni un élément du contexte d'Écologie de droite : `noyau.baisse_ecart_taux`. Chaque année où le déficit du
   programme est sous celui du statu quo compte pour une année de crédibilité ; la baisse (macro.baisse_spread :
   0 en crise et au prudent, 20 points de base au médian, 40 à l'optimiste) est entière au bout de 8 années acquises.
   Deux passages par scénario (le premier donne les années acquises). Une année acquise ne se perd pas (limite).
   Résultat : Écologie de droite inchangé (son déficit est sous le statu quo chaque année). Au médian, 2073 :
   Bertrand, Philippe, Retailleau 20 pb, Tondelier 5 pb ; à l'optimiste : Attal, Bertrand, Lisnard, Philippe,
   Retailleau, Tondelier, Zemmour 40 pb. Aucune baisse : Arthaud, Glucksmann, Le Pen, Mélenchon, Roussel.
3. **Règle de trajectoire** : pas de règle pour un programme tant qu'il ne nomme pas ses leviers.
4. **Liste des programmes par canal** (IA, école) : Adrien donnera ses corrections.
5. **Seuil de la hausse de la déduction de l'IS** : inchangé (déficit de l'année avant les leviers de la règle).
6. **Registre par scénario** : plus tard.
7. **Statu quo après 2050** : laissé en l'état.
8. **Sorties du comparateur** : régénérées.

## 12 novembre 2026 (suite) — Gains de productivité : barème commun des réformes de structure

Demande d'Adrien : la productivité propre à Écologie de droite (arbitrage 1) le dérange ; évaluer les gains de
productivité « de la manière la plus juste », pour tous.

- Source unique : Égert et Gal (2017), OCDE, document de travail n° 1354 (cadre de quantification des réformes) :
  effet d'une réforme typique observée sur le PIB par habitant. Marchés de produits (ETCR −0,31) : +0,72 % à 5 ans,
  +1,02 % à 10 ans, +2,09 % à long terme. Protection de l'emploi (EPL −0,30) : +0,22 %, +0,57 %, +1,83 % (trois
  quarts retenus : part hors emploi). Les autres domaines du cadre passent déjà ailleurs (canal d'offre commun,
  mesures d'emploi, IS, retraites, SMIC, recherche, éducation). Ouverture commerciale (compétence européenne) et
  logement (absent du cadre) : non comptés.
- `moteur/reformes_structurelles.py` et `macro.reformes_structurelles` (paramètres communs) ; canal déclaré
  `reformes_structurelles` ({pmr, epl, debut}) ; grille 1 / 0,5 / 0,25, signe négatif pour réglementer ou nationaliser,
  plafond ±2. Scénarios : crise 0, prudent moitié de l'effet à 10 ans, médian effet à 10 ans puis moitié du chemin vers
  le long terme (atteint à 25 ans), optimiste complet ; scénario miroir pour une réglementation.
- Écologie de droite : `macro.productivite` remplacé par `macro.reformes_programme` (pmr 1, epl 0,5, début 2029), lu
  aussi par le budget et par la règle d'indexation « croissance sans inflation ». Copie de crise prise en compte.
- Compteurs (pmr / epl) : Lisnard 1,75 / 1 ; Philippe 1,25 / 0 ; Attal 1 / 0,5 ; Écologie de droite 1 / 0,5 ;
  Zemmour 0,75 / 0 ; Retailleau 0,5 / 0,75 ; Bertrand 0 ; Le Pen −0,25 / 0 ; Glucksmann −0,5 / 0 ; Tondelier −1 / 0 ;
  Mélenchon −2 / −0,5 ; Roussel −2 / 0 ; Arthaud −2 / −2. Mesures citées dans la note de chaque paramètre.
- Point 4 (liste des canaux) : remarque d'Adrien vérifiée, Zemmour parle de l'école (ZEM-EDU-01, 02, 04) : canal école
  ajouté. Tous les programmes qui ont le canal IA ont maintenant le canal école.
- Test : `tests/test_canaux_declares.py::test_reformes_structurelles_bareme`.

## 12 novembre 2026 (suite) — Seconde relecture neutre : trois corrections

Rapport : docs/relecture_neutre_2_rapport.md. DÉCISIONS d'Adrien : appliquer la même règle à tous les programmes pour
les gains de productivité (point 1) ; restreindre le barème des réformes de structure au champ de l'OCDE (point 2) ;
pour Écologie de droite, publier le déficit au sens de Maastricht, la contribution de la règle étant un emprunt aux
ménages, règle inchangée (point 3). Les autres points du rapport attendent ses arbitrages.

**1. Dividende de productivité commun** (`statu_quo.dividende_productivite`). Un PIB en plus dû à la productivité
rapportait la part des recettes dans le PIB (52 %), alors que dans le statu quo les dépenses indexées sur les salaires
montent avec lui. Calcul : productivité du statu quo relevée de 1 % en dix ans, écart de solde primaire rapporté à
l'écart de PIB : ≈ 25 % en 2030, 12,5 % en 2037, 10 % en 2050, presque rien en 2073 (même chose dans les quatre
scénarios). Appliqué à tous : canaux déclarés (réformes de structure, IA, école), part hors emploi des instruments de
productivité du canal d'offre (capital des entreprises et des ménages, successions, investissement public, éducation,
recherche), et Écologie de droite (réformes, école, adoption de l'IA). Le dividende propre au budget d'Écologie de
droite (`q_div`) ne sert plus qu'aux écarts de méthode (tendance, IA du statu quo). Inchangés : les gains d'emploi et
d'heures, le multiplicateur. Limite : un seul profil de gain pour tous.

**2. Barème restreint au champ de l'OCDE** (docs/reformes_structurelles.md). Marchés de produits : électricité, gaz,
télécommunications, poste, rail, aérien, fret routier ; protection de l'emploi : licenciement des contrats réguliers.
Normes, simplification, commande publique, banques, autoroutes, aéroports, audiovisuel, santé, logement, commerce :
hors champ pour tous. Compteurs (pmr / epl) : Arthaud −2 / −1 ; Roussel −1,5 / 0 ; Mélenchon −1 / −0,5 ; Tondelier
−1 / 0 ; Glucksmann, Le Pen −0,5 / 0 ; Attal −0,5 / 0,5 ; Bertrand, Philippe, Zemmour 0 / 0 ; Retailleau 0 / 0,5 ;
Lisnard 0 / 1 ; Écologie de droite 0,5 / 0,5. Lectures à confirmer par Adrien : listées dans la note.

**3. Écologie de droite : contribution de la règle en emprunt** (`clause.contribution_en_emprunt`). La contribution
n'entre plus dans les recettes : le déficit publié la compte et la dette de Maastricht comprend ce que l'État doit aux
ménages ; le remboursement à 67 ans est hors solde ; `dette_et_quasi_dette_pib` ne compte plus les créances deux fois
(`quasi_dette_dans_dette`). La règle ne change pas (mêmes leviers, mêmes montants) : elle vise 3 % comme si la
contribution était une recette. Les intérêts de cet emprunt sont ceux de la dette du noyau (taux de marché et prime de
dette), un peu au-dessus du rendement du fonds rendu aux ménages.

**Déficit 2037 (% du PIB), avant → après**

| Programme | Prudent | Médian | Prudent 2050 |
|---|---|---|---|
| Statu quo | 9,50 | 8,37 | 20,57 |
| Écologie de droite | 3,00 → 4,27 | 2,10 → 2,23 | 3,17 → 5,29 |
| Bertrand | 9,20 → 9,20 | 7,33 → 7,32 | 19,69 → 19,68 |
| Philippe | 9,34 → 9,93 | 6,26 → 7,44 | 19,73 → 21,61 |
| Retailleau | 9,94 → 10,29 | 7,14 → 7,92 | 21,73 → 22,79 |
| Attal | 10,76 → 11,45 | 7,81 → 9,01 | 24,05 → 26,16 |
| Le Pen | 13,23 → 13,28 | 10,73 → 10,82 | 30,94 → 31,15 |
| Zemmour | 12,96 → 13,31 | 9,63 → 10,37 | 30,10 → 31,06 |
| Lisnard | 12,95 → 13,93 | 9,16 → 10,90 | 29,52 → 32,23 |
| Tondelier | 14,51 → 13,91 | 10,60 → 10,26 | 35,60 → 33,69 |
| Glucksmann | 14,62 → 14,35 | 11,85 → 11,83 | 34,78 → 33,94 |
| Arthaud | 19,92 → 18,06 | 14,05 → 13,21 | 50,66 → 44,53 |
| Mélenchon | 31,52 → 29,63 | 23,05 → 22,30 | 76,87 → 71,37 |
| Roussel | 31,99 → 30,51 | 23,40 → 22,72 | 88,02 → 83,60 |

Écologie de droite, prudent : 4,17 % en 2029, 4,65 % en 2032, 4,27 % en 2037, 5,29 % en 2050, 5,74 % en 2073 ; dette
130 % en 2029, 135 % en 2037, 147 % en 2050, 178 % en 2073 (sans règle : 5,25 % et 141 % en 2037). L'ordre des
scénarios est respecté pour tous les programmes, chaque année.

**À faire** : les résumés « En bref » du comparateur citent encore les anciens chiffres (barème « de l'OCDE », 3 % pour
Écologie de droite, écarts de PIB) : à réécrire avec les nouvelles sorties.

## 12 novembre 2026 (suite) — Philippe : programme mis à jour sur son site

Lecture des 15 pages thématiques du site (mise à jour du 12/11/2026) : 32 mesures ajoutées à programmes/philippe/
mesures.yaml (123), 7 nouveaux paramètres et 5 paramètres précisés dans parametres.yaml. Détail, effet et points
ouverts : docs/programmes_novembre.md, section « Philippe : programme mis à jour le 12 novembre 2026 ».
Décisions d'Adrien du soir : capitalisation collective chiffrée en dépense (compensation annoncée non reprise), lecture
CSG des heures sup confirmée, allocation familiale unique chiffrée sans coût constant (même section).
Philippe, jours de carence : recalés sur la revue de dépenses IGF-Igas (juillet 2024, 289 M€ pour toute la fonction publique, 112 M€ pour l'État), répartis entre État, collectivités et hôpitaux, plus les arrêts évités dans le privé ; l'ancien paramètre (0,5 Md€ sur l'État seul) était trop haut.

## 12 novembre 2026 (suite) — Annonces des candidats contre le chiffrage retenu

Demande d'Adrien : rendre visible que la règle (on ne reprend jamais les montants annoncés) mesure ce qui est démontré,
pas ce qui est impossible. programmes/annonces.yaml liste les annonces (économies d'ensemble ou recettes de mesures
précises), lu seulement par outils/export_comparaison.py : sorties/comparaison_annonces.csv met en regard, en 2032 et
par scénario, l'annonce et ce que retient le modèle (économies nommées plus enveloppe, ou somme des lignes de la mesure),
l'écart en points de PIB et le déficit si l'annonce était tenue (statique). Aucun résultat du modèle ne change.
Comparateur : phrase de méthode dans l'en-tête et tableau « Ce qu'annoncent les candidats, ce que retient le modèle ».
Remarque d'Adrien : la colonne « déficit si l'annonce était tenue » était statique, sans les effets d'une dépense en
moins sur l'activité (TVA…). Remplacée par une variante complète (moteur/annonces.py, `variante_annonces = True`,
calculée seulement par l'export) : l'écart entre l'annonce et le retenu est ajouté comme des mesures ordinaires
(postes de l'enveloppe pour les économies d'ensemble, profil et instrument de la mesure pour les recettes), qui passent
par le multiplicateur, l'offre et les intérêts. Prudent, 2032 : environ trois quarts de l'écart brut améliorent
vraiment le déficit pour les économies ; un peu plus que l'écart pour les recettes sur le patrimoine (multiplicateur
faible, intérêts en moins). Les autres sorties sont inchangées.

## 12 novembre 2026 (soir) — Phase A de la roadmap : cohérence comptable

Branche `phase-a` : `main` + `arbitrages-equite` (seconde relecture neutre, fusionnée ici), puis les chantiers A1 à A6
et A8 de la roadmap « vers le meilleur moteur possible ». Décisions d'Adrien du 12/11 au soir : A2 (valeur de l'emploi
modulée selon la mesure, emplois des 32 heures au voisinage du SMIC, « le moteur doit simuler des cohortes »), A3
(postes publics au coût des facteurs), A5 (dette en baisse), A6 (rendement du fonds).

- **A1, productivité au noyau** (`statu_quo.dividende_programme`). Le dividende d'un gain de productivité n'est plus
  la moyenne d'un profil type : le noyau relève la productivité du statu quo du profil du programme (réformes, IA,
  école réunies), recalcule recettes et dépenses indexées, et rend (Δ recettes − Δ dépenses) / Δ PIB année par année.
  Canaux déclarés, part productivité du canal d'offre, Écologie de droite. Sur le profil type, on retrouve exactement
  l'ancien dividende (test).
- **A2, 32 heures** (`ProgrammeSimple.trente_deux_heures`). Les embauches de partage du travail ne rapportent plus que
  l'allocation de chômage évitée (`emploi.allocation_chomeur_evitee`, 9 000 €) : leur production est celle des heures
  rendues, déjà gardée dans le PIB avec ses recettes ; elles n'ajoutent plus de valeur ajoutée au PIB (canal « ** »).
  Les emplois perdus par le coût horaire valent la cellule OpenFisca de leur niveau de salaire
  (`ProgrammeSimple.valeur_emploi_cellule` : prélèvements, TVA, allocation), paramètre `cout_emplois_perdus` de la
  mesure, par défaut 1,3 SMIC (`emploi.cout_emploi_cree_smic`, emplois au voisinage du SMIC) : 20 650 €, la valeur
  d'un emploi des autres canaux (20 000 €). Le SMIC exact (16 200 €) aurait rendu les emplois perdus moins coûteux
  que partout ailleurs dans le modèle. Cohortes : la valeur d'un emploi suit désormais le salaire par emploi
  (`idx["salaire"]`) et non le PIB, qui comptait une seconde fois l'évolution du nombre d'emplois (tous les canaux
  d'emploi des programmes simples, emplois perdus du SMIC d'Arthaud, Glucksmann, Mélenchon, Roussel et Tondelier).
- **A3, postes publics dans le PIB** (`programme_simple.production_non_marchande`). La dépense des postes créés (ou
  supprimés) entre au PIB à son coût au rythme où le multiplicateur s'éteint (même durée, scénario miroir pour une
  hausse) : à long terme le PIB garde le coût des postes, comme en comptabilité nationale. Postes des mesures
  (`postes`), 32 heures dans la fonction publique, et Tondelier (qui ne retirait pas non plus du PIB les emplois privés
  évincés : corrigé avec la même valeur ajoutée que ses emplois perdus).
- **A4, `macro.elasticite_invest`** : 0,24 / 0,30 / 0,335 / 0,37 (crise → optimiste), ordonnée pour une baisse
  d'impôt ; une hausse prend le scénario miroir, dans le canal d'offre comme dans les cohortes d'entreprises
  d'Écologie de droite (tranche par tranche).
- **A5, baisse de l'écart de taux** (`noyau.baisse_ecart_taux`) : une année compte quand le ratio de dette baisse, une
  année où il remonte en fait perdre une. Effet : au médian, Bertrand, Philippe, Retailleau et Tondelier perdent la
  baisse qu'ils gagnaient sous le statu quo qui diverge ; Écologie de droite la garde.
- **A6, emprunt aux ménages** : le noyau compte en intérêts l'écart entre le rendement servi sur les créances
  (`epargne.rendement_fonds`, 1,76 % réel) et le taux réel de la dette de marché, sur le stock de début d'année
  (`interets_menages`). Le rendement servi est sous le taux réel de l'OAT (≈ 2,2 %) : la correction allège la charge
  d'Écologie de droite (−1,7 Md€ en 2037 au prudent).
- **A8, unités de l'enveloppe** : l'annonce est convertie en points de PIB de 2029 en un seul endroit
  (`unites.annonce_en_points_pib`), euros de 2027 ramenés en 2026, forme « niveau » ou « cumul » (Attal, Bertrand :
  `forme_annonce: cumul`). Plafond seulement : aucun chiffre ne change.
- **Pas fait : A7** (registre par scénario d'Écologie de droite, plus aucune ligne « méthode » dans le bilan). Chantier
  à part : il faut recalculer le budget du programme dans chaque scénario au lieu du prudent corrigé.

Déficit 2037 (prudent, avant → après la phase A, sorties de `arbitrages-equite` puis de `phase-a`) : Roussel 30,51 →
30,78 ; Arthaud 18,05 → 18,45 ; Mélenchon 29,63 → 29,55 (PIB relevé par les postes) ; Tondelier 13,91 → 13,97 ;
Philippe 10,87 (après sa mise à jour du 12/11) ; Écologie de droite 4,27 → 4,21 ; les autres à moins de 0,1 point.
Médian : Bertrand 7,32 → 7,67, Philippe 8,33, Retailleau 7,92 → 8,16 (baisse de l'écart de taux perdue).

Tests : `tests/test_coherence_phase_a.py` (un test par chantier) ; test de l'écart de taux adapté au critère absolu.

## 12 novembre 2026 (nuit) — Phase B de la roadmap : B1, B2, B3 (et B8)

Décisions d'Adrien (12/11, 22 h 17) : B1 et B2 validés.

- **B1, barème des réformes de structure** : les quatre lectures (Arthaud EPL, Attal électricité, Tondelier, Le Pen et
  Écologie de droite) passent en DÉCISION ; tableau des compteurs dans `docs/reformes_structurelles.md`. Aucun
  chiffre ne change.
- **B8, licenciements d'Arthaud** : déjà réglé par B1 (interdiction des licenciements = 1 cran de protection de
  l'emploi, comme la grille).
- **B2, variante migratoire commune** (`moteur/migrations.py`, canal déclaré `solde_migratoire`). Un programme déclare
  des premiers titres de séjour en moins par an ; variation du solde = titres × part au solde (0,8 / 0,7 / 0,6 / 0,5)
  × réalisation (1 / 0,8 / 0,6 / 0,4), du prudent au plus fort. L'écart de population par âge (profil des immigrés,
  Insee Première n° 1849) passe dans le statu quo (`statu_quo.population`, `_choc_population`), qui recalcule emploi
  (taux d'emploi relatif des immigrés 0,87, Insee 2024), PIB, recettes par cellules et dépenses qui suivent la
  population ; la santé, qui ne dépend pas de la population dans le statu quo, suit ici un profil de dépense par âge
  (`demographie.sante_relative_age`, ordres de grandeur DREES, à remplacer par la table). Ces personnes sortent de la
  population active : elles ne font pas de chômeurs. Sens du résultat : 100 000 entrées nettes de moins par an coûtent
  ≈ 5,8 Md€ au solde en 2037 et 25 Md€ en 2050 au prudent (moins d'actifs ; les dépenses ne baissent qu'en partie,
  les pensions de ces personnes seraient venues après 2060). D'où l'ordre des scénarios (le prudent prend la baisse la
  plus forte).
  Lectures (titres en moins par an, sur 384 230 premiers titres en 2025, DGEF) : Zemmour 266 260 (tout sauf les
  étudiants), Lisnard 336 200 (titres divisés par huit), Philippe 192 100 (divisée par deux), Le Pen 137 400 (familial
  et moitié de l'humanitaire), Retailleau 128 100 (un tiers), Attal 52 300 (un quart du familial et de l'étudiant),
  Bertrand 38 400 (un dixième : niveau des quotas inconnu). À valider par Adrien. Les régularisations (gauche) ne
  changent pas la population : inchangées.
  Limites : enfants des personnes en plus ou en moins non comptés ; salaires au niveau moyen de leur âge (seul
  l'emploi est corrigé, ce qui grossit l'effet) ; défense et investissement suivent le PIB comme dans le statu quo.
- **B3, émissions de Zemmour** (`zemmour_ecologie`), mêmes règles que Le Pen, Arthaud et Retailleau : accise sur les
  carburants (6 Mt à plein effet au prudent), Anah, renouvelables, Ademe (estimation à sourcer) : +7,4 Mt en 2037 au
  prudent.

Déficit 2037 au prudent (après la phase A → après B) : Lisnard 14,00 → 14,77 ; Zemmour 13,36 → 13,96 ; Philippe
10,87 → 11,26 ; Le Pen 13,38 → 13,69 ; Retailleau 10,33 → 10,59 ; Attal 11,50 → 11,61 ; Bertrand 9,21 → 9,28 ; les
autres inchangés. Comparateur : l'écart d'emploi de ces programmes compte des personnes absentes, pas des chômeurs.

Restent dans la phase B : B4 (canal logement commun), B5 (fraude), B6 (IA et école proportionnelles à la mesure), B7
(grille commune des plafonds d'économies).

## 12 novembre 2026 (nuit, suite) — Limites de B2 levées ; B4, B5, B6

Demande d'Adrien (22 h 53) : régler les limites de B2, puis les chantiers sans décision.

- **B2, limites levées** (`moteur/migrations.py`, `statu_quo`) :
  - naissances des personnes en plus ou en moins : ICF du scénario × 1,26 (ICF des femmes nées à l'étranger 2,3
    contre 1,83, Insee Références 2023, fiche 1.8), calendrier par âge de la mère ;
  - salaire relatif 0,91 (salaire médian à temps complet des immigrés de 25 à 49 ans inférieur de 9 %, Insee
    Références 2023, fiche 4.4) : PIB (emploi en équivalent productif) et prélèvements (cellules au coût réduit) ;
  - santé par âge recalée sur la DREES (1 420 € entre 21 et 30 ans, 8 529 € au-delà de 80 ans, pour 2 903 € en
    moyenne) ; statut SOURCE ;
  - la défense ne suit plus la population ;
  - **défaut corrigé** : le statu quo rapporte emploi, PIB et recettes à 2029 ; un écart présent dès 2029 entrait
    dans la base et effaçait l'effet de 2028-2029. Les écarts commencent désormais en 2030.
  Effet de 100 000 entrées nettes de moins par an (prudent) : −5,4 Md€ en 2037, −18,7 Md€ en 2050 (−5,8 et −25
  avant : les enfants en moins coûtent aussi moins).
- **B5, fraude** (`moteur/fraude.py`, canal `fraude`, `fraude.bareme`) : agents de contrôle en plus × 1,1 M€ recouvré
  par agent (11,4 Md€ pour 10 377 ETPT en 2024) × rendement marginal 0,15 / 0,25 / 0,4 / 0,6, plafond 40 % des
  montants de 2024 ; coût des agents ajouté sauf s'il est déjà compté ; renforcement sans chiffre = 2 000 agents
  (rapport Feld, 2026). Tondelier 1 000 agents (programme, p. 63), Mélenchon 5 000, Roussel 8 000 (40 % des 20 000
  postes), Le Pen et Écologie de droite sans chiffre. Écologie de droite : 2,25 Md€ sans source → ≈ 0,5 Md€ net au
  prudent ; sa « facturation électronique » est déjà dans la loi, donc dans le statu quo.
- **B6, IA et école** : l'adoption de l'IA est proportionnelle au budget engagé (`adoption_ia.budget` : barème entier
  pour 1 Md€ par an en plus, 0,25 Md€ pour une mesure sans montant) : Attal 1, Glucksmann 0,5, Philippe 0,4, Zemmour,
  Lisnard, Retailleau et Écologie de droite 0,25. Canal « école » retiré des dix programmes dont les mesures sont
  budgétaires : elles passent déjà par le canal d'offre de l'éducation, proportionnel à la dépense par élève (double
  compte). Gardé pour Écologie de droite et Zemmour (réformes d'organisation sans budget).
- **B4, logement** (canal `logement`, `logement_offre.bareme`, mêmes logements que la croisière d'Écologie de
  droite) : intensité × 25 000 / 37 500 / 50 000 / 100 000 logements par an, PIB des chantiers et recettes. Lectures :
  Retailleau +1, Lisnard +0,5, Attal +0,5, Philippe +0,25, Glucksmann −0,25, Mélenchon −0,5, Roussel −0,5. À valider.
- **Pas fait** :
  - A7 (registre par scénario d'Écologie de droite) : le budget du programme est figé au prudent à une vingtaine
    d'endroits ; chantier à part ;
  - B7 (plafonds communs des économies nommées) : demande un arbitrage (relecture n° 2, point 11 : capacité
    trop basse ou lignes trop hautes).

Déficit 2037 au prudent (avant → après) : Retailleau 10,59 → 10,46 ; Attal 11,61 → 11,54 ; Glucksmann 14,39 →
14,44 ; Mélenchon 29,55 → 29,63 ; Écologie de droite 4,21 → 4,29 ; les autres à moins de 0,05 point.

## 13/11/2026 — Phase A7 (registre d'Écologie de droite par scénario), santé sur le statu quo, B7

- **A7, registre par scénario** (`macro.registre_par_scenario`, DÉCISION) : le budget d'Écologie de droite était figé
  au prudent ; il se calcule désormais dans chaque scénario avec `Parametres.en_scenario` (copie dont la colonne
  prudente lit le médian ou l'optimiste, comme `en_crise` pour la crise). Les lignes de méthode « tendance »,
  « démographie » et « économies du registre » disparaissent. L'effet de l'IA du statu quo est recalculé dans le
  budget du programme (registre avec la tendance + l'IA du scénario), au lieu d'une ligne de méthode.
- **Santé sur le statu quo** (`sante_trajectoire.base_statu_quo`, DÉCISION d'Adrien du 13/11/2026 : « le modèle du
  statu quo augmente les dépenses selon les forecasts, et les programmes diminuent cette augmentation en fonction des
  mesures ») : la santé du programme part de la santé + l'invalidité du statu quo (dérive 2027-2029, scénarios de
  l'assurance maladie puis PROMEDE, sur les salaires) ; ses mesures (gestion, autonomie, agents hospitaliers,
  économies à terme, IA des hôpitaux, forfait des généralistes, produits nocifs, antidépresseurs) suivent la même
  croissance. La ligne de méthode « même périmètre sur la pente du programme » est nulle par construction et
  disparaît (elle valait −1,4 / −7,0 / −12,8 Md€ en 2037 au prudent / médian / optimiste).
- **B7, plafonds communs des économies nommées** : DÉCISION d'Adrien du 13/11/2026 : ne rien plafonner. Les
  économies nommées des programmes restent à leur chiffrage (relecture n° 2, point 11, clos).

Écologie de droite, déficit (avant → après, avec la règle) : 2037 crise 6,94 → 6,99, prudent 4,29 → 4,34, médian
2,38 → 3,13, optimiste 0,78 → 1,67 ; 2050 médian 0,06 → 3,29, optimiste −1,89 → 0,82. L'écart entre scénarios
venait en partie des lignes de méthode : le budget figé au prudent comptait au médian et à l'optimiste une santé et
des économies qui n'étaient pas celles du programme. Les autres programmes ne changent pas.

## 13/11/2026 (après-midi) — Écologie de droite sans rien de propre hors ses mesures

DÉCISION d'Adrien du 13/11/2026 : « virer tout ce qui est spécifique au projet de base, à part les mesures ».
Réponses : tout passe sur les canaux communs, OpenFisca compris ; fonds et règle gardés comme des mesures.

- **Échelle** : la croissance par tête des canaux du programme suit les salaires du statu quo du scénario (tendance,
  IA, scénario), plus la tendance du prudent ; le dividende de croissance du budget n'est plus calculé (il ne
  servait qu'aux lignes de méthode).
- **Santé** : l'accise sur les produits nocifs finance le surplus de la santé du statu quo au-delà d'une part constante
  du PIB du statu quo ; la TVA santé compte les soins évités dans tous les scénarios (la pente commune ne compte pas
  la prévention du programme).
- **Canaux communs** (`moteur/canaux_declares.py`, appelé avec les lectures du programme) : réformes de structure,
  adoption de l'IA, fraude, école, logement (intensité 1, `macro.logement_canal`). La phase initiale négative du
  logement (fin des aides à la pierre) passe par la dépense en moins et le multiplicateur.
- **Réactions des contribuables** : chiffrées avec les mesures (nature « budget », dans l'impulsion), comme les
  autres programmes, dont les montants sont nets des réactions (Tondelier, tranche à 60 % : 3,5 Md€ en statique,
  1,2 retenus ; Lisnard, IS à 20 % : −12 et −10). Un canal commun en plus les aurait comptées deux fois. Sans les
  heures des classes moyennes ni la part réelle des hauts revenus, que compte le canal d'offre commun.
- **Permis rapide** : retiré (double emploi avec le canal logement, intensité 1 = réforme d'ensemble du foncier).
- **Emploi** (`emploi.canal_offre_commun`) : l'impôt unique et le revenu universel passent par le canal d'offre
  commun, cellule par cellule, comme réforme d'ensemble (`offre.travail_reforme`, `offre.reforme_travail`) ; table
  du programme au format d'OpenFisca (`outils/table_offre_ecologie_de_droite.py`, depuis `menages_types.nouveau`,
  épargne obligatoire hors revenu disponible comme les cotisations retraite aujourd'hui). L'assurance chômage
  remplacée (bloc chômage moins le revenu universel des chômeurs) et le SMIC revalorisé de la seule croissance
  passent par les instruments communs (transferts aux actifs, coût du travail). Les seniors du socle à 67 ans passent
  par `offre.seniors`. Retirés du bloc emploi propre : allocation chômage, bas salaires, coût du travail des
  entreprises, baisse ciblée du coût du travail, SMIC, inactifs, seniors à long terme. Le canal commun trouve que le
  système du programme réduit les heures : le taux marginal sur le coût employeur passe d'environ 60 % à 73 % entre
  1,3 et 4 SMIC (impôt unique à 66 % au-delà de 32 000 € de coût, impôt local 7,2 %), et à 67 % sous le SMIC (sortie
  du revenu universel).
- **Fonds** : externalités du capital ramenées à zéro (le capital du fonds rapporte comme celui des entreprises).

Restent propres au programme, à trancher : le canal de l'énergie des entreprises (IS des taxes d'énergie supprimées,
emploi industriel), les emplois perdus par la localisation des bénéfices (IS), le cumul emploi-socle, l'éviction de
l'épargne volontaire, et les réformes du marché du travail sans équivalent fiscal (France Travail, apprentissage,
alternance, contrat, accords de branche, commerces, prime jeunes, entrée plus tôt des jeunes).

## 13/11/2026 (fin d'après-midi) — Phase G (performance), phase C3 (recoupements du statu quo)

- **Caches** : tables d'OpenFisca, tables d'offre, fichiers de l'ancien système et de la transition lus une fois par
  processus ; barème de l'impôt unique en cache par jeu de paramètres (1,2 million d'appels) ; probabilités des paires
  de déciles (copule) en cache. Résultats identiques au centième de milliardième.
- **Registre relevé de l'IA** : il reprend les années sous le seuil de la hausse de la déduction de l'IS du registre
  de base. Sa simulation imbriquée comptait l'IA deux fois (tendance relevée et registre de l'IA recalculé dedans).
- **Hausse conditionnelle de la déduction de l'IS au fil de la trajectoire** (`is_investissement.hausse_au_fil`,
  DÉCISION d'Adrien du 13/11/2026) : dynamique du noyau (`HausseDeduction`, `HausseDeductionProgramme`) ; chaque année,
  la part déduite monte d'un pas par année passée sous 3 % de déficit avant règle ; l'IS en moins, l'investissement des
  entreprises (cohortes) et l'érosion de l'IS (taux effectif) suivent. Plus de simulation imbriquée.
  **Constat** : l'ancienne règle décidait sur le déficit du prudent (« déficit du prudent, avant clause ») et, en
  pratique, la hausse ne se déclenchait jamais (le prudent ne passe pas sous 3 %) ; depuis le registre par scénario,
  la simulation imbriquée mêlait même le statu quo du prudent et la colonne du scénario. Désormais chaque scénario
  décide sur son propre déficit : la hausse se déclenche dès 2032 en optimiste (part de 0,5 à 1 en 2041, 22 Md€ d'IS
  en moins en 2037) et plus tard en médian. Optimiste 2037 : 1,67 → 2,33 % ; médian 2050 : 3,70 → 4,05 %.
- **Temps** : Écologie de droite, quatre scénarios avec et sans règle, 170 s → 27 s. Un scénario : 61 s → 9 s environ.
  Une piste plus générale (cache entre copies de paramètres, avec les paramètres lus) a été essayée et abandonnée :
  exacte mais plus lente, faute de savoir ce qu'ont lu les résultats déjà en cache.
- **C3** : `docs/recoupements.md` : retraites conformes au COR de juin 2026 (≤ 0,1 point), déficit conforme au FMI
  (≈ 6 % à moyen terme), dette 4,7 points au-dessus du FMI (point de départ plus récent), dans la fourchette de l'IGF.
- **Correction (même jour)** : en passant l'emploi d'Écologie de droite au canal commun, l'effet du coût du travail
  (baisse ciblée jusqu'à 1,3 SMIC, impôts de production assis sur les salaires supprimés, 52 Md€ de 2024) avait été
  retiré du bloc emploi sans être remis ailleurs. Il passe désormais par l'instrument commun « coût du travail »
  (comme le SMIC relatif), neutralisable mesure par mesure (attribution) ; la table d'offre garde le coût employeur
  actuel. Effet : ≈ 370 000 emplois au prudent en 2037 (le bloc propre en comptait ≈ 300 000). Déficit 2037 au prudent
  4,78 → 4,14 % ; médian 3,79 → 2,57 ; optimiste 2,33 → 0,83.
- Attribution : la fraude se neutralise par le barème commun (`macro.fraude_controle/agents`), le logement par
  l'intensité du canal commun ; le permis rapide sort du registre ; libellés numérotés tolérés.
- **Tests** : la suite complète passe, `test_attribution` compris, en 11 min 24 s (objectif de la phase G : 15 min).

## 13/11/2026 (soir) — Phase C : C3 fini, C2, C5 commencé, C4 en attente

- **C3** (`docs/recoupements.md`) : retraites (COR 2026 ; Ageing Report 2024, écart expliqué par la fécondité),
  déficit (FMI), dette (FMI, IGF), charge de la dette (Cour des comptes : ≈ 100 Md€ et 3 % du PIB en 2029 ; moteur
  3,35 %), chômage (Banque de France : 8,0 % en 2028 ; moteur 8,3 %), santé (sous la moyenne de l'OCDE jusqu'en 2045,
  au-dessus de l'Ageing Report à long terme ; chiffre santé de la fiche France non trouvé).
- **C2** (`docs/reformes_structurelles.md`) : les six valeurs du barème des réformes de structure sont celles du
  tableau 4 d'Égert et Gal ; la décote de l'EPL (0,75) reste sans source, le texte suggérant plutôt une part hors
  emploi proche de 1.
- **C5** (`docs/backtests.md`, `outils/backtests.py`) : CICE retrouvé (89 000 emplois à 3 ans au médian, 100 000
  dans l'évaluation micro) ; âge légal cohérent mais calé ; restent les 35 heures et le PFU.
- **C4** : aucun chiffrage d'ensemble publié pour 2027 (l'Institut Montaigne l'annonce pour le premier trimestre
  2027 ; l'IFRAP publie un comparateur des propositions, sans chiffrage) : en attente.

## 13/11/2026 (nuit) — Phase C1 : hypothèses sans source classées par poids

- `outils/c1_inventaire.py` : +10 % sur chaque hypothèse sans source, écart de déficit 2037 et 2050 au prudent ;
  les programmes qui lisent leurs paramètres à part (Tondelier, programmes simples) sont perturbés par leur `pt` ;
  les années sont écartées. Résultats dans `docs/sources_c1.md`.
- Communs : quatre paramètres pèsent (productivité, durée de la dette, inflation 2026-2030, élasticité des moyens de
  l'enseignement) ; les trois premiers et le déflateur 2026 sont encadrés (COR, AFT, PLF 2027), le quatrième devient
  une décision à écrire.
- Écologie de droite : six paramètres encadrés (Citepa, SDES, DNF, Insee, Banque de France, OFCE) ; le besoin de
  financement des collectivités (15,3 Md€) est entre la Cour des comptes (11,4) et l'Insee (17,8) : périmètre à
  trancher ; une douzaine de constructions du modèle à écrire en décisions.
- Tondelier, Mélenchon : chiffrages de mesures documentés, aucun au-dessus de 0,03 point pour 10 %.
- Aucune valeur changée : les résultats sont inchangés.

## 13/11/2026 (soir) — C1 : décisions d'Adrien appliquées

- Quatorze hypothèses sans source passent en DECISION, motif en tête de note (liste dans `docs/sources_c1.md`).
- Besoin de financement des collectivités : toutes les administrations publiques locales (17,8 Md€ en 2024, Insee),
  au prorata des deux blocs du classeur ; apprentissage : 8 Md€ encadrés par le budget de l'alternance de France
  compétences (8,2 Md€ en 2026).
- Écologie de droite, déficit 2037 au prudent : 4,14 → 4,15 % avec la règle, 5,01 → 5,13 % sans ; 2050 : 4,58 → 4,72 %.
- **Anomalie trouvée** : `tests/test_chomage.py::test_chomage_calcule_chaque_annee` échoue, et échouait déjà au
  commit d547442. En optimiste, le chômage d'Écologie de droite passe sous le plancher incompressible (3,5 %) de 2044
  à la fin (2,6 % en 2047) : les emplois du coût du travail passés le 13/11 par le canal d'offre commun n'ont plus de
  rendements décroissants vers le plancher, que l'ancien bloc propre appliquait. À corriger.

## 13/11/2026 (soir) — Plancher du chômage commun

- `moteur/emploi_canaux.plancher_chomage` : à moins d'un point au-dessus du chômage incompressible (3,5 %), les
  emplois en plus d'un programme ont des rendements décroissants, u* = plancher + marge × exp((u − plancher − marge)
  / marge) : même valeur et même pente au raccord, jamais sous le plancher. Les emplois manquants sont retirés des
  canaux positifs au prorata (sauf démographie), de l'emploi et du PIB ; les recettes des effets d'offre suivent.
  Appliqué aux programmes simples et à Écologie de droite (contexte, puis emplois du fonds dans la dynamique).
  Nouveau paramètre `emploi.marge_plancher` (1 point, hypothèse).
- Seul Écologie de droite est touché : chômage optimiste de 2050 2,9 → 3,6 %, déficit optimiste 2050 +0,1 point
  environ (le reste de l'écart au précédent export vient des collectivités, C1). Aucun autre programme ne bouge de plus
  de 0,005 point de déficit.
- `test_chomage_calcule_chaque_annee` repasse ; `test_hypotheses_communes_sans_mesure_du_programme` admet l'élasticité
  des moyens de l'enseignement (décision de modèle de C1). Suite complète : 366 tests, 10 min 16 s.
