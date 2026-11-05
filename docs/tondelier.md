# Programme Tondelier (Les Écologistes) sur le noyau (5 novembre 2026)

`programmes/tondelier/` : `mesures.yaml` (fiche des 116 mesures à portée budgétaire, citations vérifiées page par page),
`parametres.yaml` (chiffrage de chaque mesure : montant par scénario, assiette, montée, source), `programme.py`.
`python -m moteur.noyau tondelier` imprime le bilan ; `python -m outils.export_comparaison` l'ajoute au comparateur.

Sources : programme « Pour une prospérité écologique » (juillet 2026, 208 p., 557 mesures) et dossier de presse
« Budget 2027 : la grande transmission doit financer la grande transition » (26 août 2026, 8 p.).

## Méthode

- **Mesures simples** : montant à l'économie de 2029 (Md€ de 2026), montée linéaire, puis l'assiette (PIB, pensions,
  successions, TVA, IS, un bloc du statu quo). Une dépense de rémunération publique rend 57 % en prélèvements
  (OpenFisca, statu_quo.prelevements_activite).
- **Mesures calculées** :
  - rémunérations publiques (+9,5 % du coût des agents, par catégorie, réparties entre versants ; pensions des
    fonctionnaires relevées pour les départs suivants) ;
  - retour à 62 ans (pensions de toutes les générations, profil de départ à 62 ans pour les départs à partir de
    2028, même calcul et même calage que le statu quo) ;
  - SMIC à 2 000 € brut (table OpenFisca de 2026 lue au salaire relevé, allègements nominalisés ; prélèvements, prime
    d'activité, TVA, IS, emplois perdus avec une élasticité au coût du travail) ;
  - génération sans tabac (population de l'Insee).
- **Effets macroéconomiques** : multiplicateur commun (1 en prudent) sur l'impulsion budgétaire nette des mesures,
  dissipé comme l'ajustement budgétaire du modèle ; emplois perdus du SMIC (PIB et chômage).
- **2027-2028** : SMIC dès 2027, le reste à la loi de finances 2028 ; ces années passent dans la dette de fin 2028.
- **Règle** : aucune recette ni économie annoncée n'est reprise (successions : 15 Md€ annoncés, 4 retenus en prudent) ;
  les économies déclaratives (fraude, médicaments, privé sous contrat, rétention) sont estimées en trois scénarios.

## Arbitrages

Réglés par le dossier de presse :

| Point | Lecture retenue | Source |
|---|---|---|
| Taxe Zucman | impôt plancher différentiel : 2 % du patrimoine, tous impôts confondus | dossier, p. 5 |
| ISF | seuil d'entrée à 1,3 M€, barème modulé selon l'empreinte carbone | dossier, p. 5 |
| TVA écologique | 20 % sur les biens à fort impact (aérien), 5,5 % sur la transition (train, bio, réparation) | dossier, p. 4 |
| Successions | +10 % au-delà de 4 M€, +10 % au-delà de 13 M€ ; Dutreil à 50 % au-delà de 50 M€ ; fin de la réduction pour donation avant 70 ans et du démembrement ; plus-values latentes au barème actuel avec report | dossier, p. 6 |
| Défense | loi de programmation militaire du statu quo (le dossier s'en félicite) | dossier, p. 4 |
| Paquet 2027 | 10 Md€ : ferroviaire 1, RER 0,5, vélo 0,5, leasing 1, outre-mer 0,4, biodiversité 1, MaPrimeRénov' 1,4, Fonds vert 1,9, écoles 2, sécurité civile 0,26 | dossier, p. 7-8 |

Pris par Claude (Adrien : « sinon fais-les toi-même »), à revoir :

| Point | Lecture retenue | Autre lecture |
|---|---|---|
| SMIC × allègements | allègements « nominalisés et désindexés » (p. 67) : barème de 2026 gardé, coût au SMIC +14,4 % (brut +7,7 %) | allègements qui suivent le SMIC : coût +7,7 %, environ moitié moins d'emplois perdus |
| CSG et flat tax | +3 points de CSG sur le capital et +3 points de PFU s'ajoutent ; CSG +1 point sur tous les revenus | PFU +3 seulement |
| Retraites | 62 ans en 2028 pour tous les départs, durée Touraine gardée | entrée progressive |
| Allocations familiales | chaque enfant reçoit la moitié du montant de deux enfants | à budget constant (baisse pour les familles nombreuses) |
| Impôt sur le revenu | tranche à 11 % ramenée à 9 % (« baisser les tranches basses ») | non chiffré |
| UE à 2 % du PIB | hors scénario central (dépend des 26 autres États) | variante |
| Aide au développement | 0,7 % du revenu national en 2032 | — |
| Violences sexistes et sexuelles | 3 Md€ par an | 3 Md€ sur le quinquennat |
| Soins à 100 % | ticket modérateur des soins de ville | « grande Sécu » (≈ 20 Md€) |
| Hautes pensions | au-dessus de 2 000 €, inflation − 0,5 point pendant cinq ans | — |
| Hôpital | +0,5 point de masse salariale par an de 2028 à 2032 | — |
| TSN | seuils actuels (le seuil de 5 Md€ du texte serait une hausse) | — |

## Résultats (5 novembre 2026)

Effet des mesures sur le solde primaire, contre le statu quo (Md€ de 2026 ; − = dégrade) :

| Prudent | 2029 | 2032 | 2037 | 2050 |
|---|---|---|---|---|
| Recettes (impôts nouveaux, prélèvements sur les hausses de salaire) | +94,6 | +119,2 | +123,8 | +131,4 |
| Retraites (62 ans, minimum vieillesse, pénibilité, pensions des fonctionnaires) | −32,5 | −33,8 | −36,7 | −41,1 |
| État et défense (rémunérations, éducation, justice, aide au développement, VSS) | −19,6 | −40,0 | −41,8 | −45,2 |
| Santé (soins à 100 %, franchises, hôpital, Ehpad) | −16,5 | −29,4 | −30,9 | −35,4 |
| Prestations (garantie d'autonomie, AAH, famille, congés, chômage, APL) | −25,6 | −26,1 | −26,6 | −27,8 |
| Investissement (adaptation, rénovation, ferroviaire) | −10,1 | −18,0 | −18,1 | −19,5 |
| Collectivités et autres dépenses | −18,7 | −26,9 | −27,1 | −29,7 |
| Effets économiques (multiplicateur, emplois perdus du SMIC) | +10,1 | +6,4 | −9,9 | −10,5 |
| **Total** | **−18,5** | **−48,6** | **−67,4** | **−77,8** |
| en points de PIB | −0,6 | −1,6 | −2,1 | −2,2 |

| Scénario | Solde primaire 2037 (points de PIB) | Emplois perdus (SMIC) | Déficit 2037 : programme / statu quo |
|---|---|---|---|
| Crise | −2,7 | 668 000 | 12,9 / 9,2 % |
| Prudent | −2,1 | 534 000 | 12,6 / 9,6 % |
| Médian | −1,1 | 401 000 | 10,0 / 8,5 % |
| Optimiste | −0,2 | 267 000 | 8,4 / 8,2 % |

Le déficit s'écarte plus que le solde primaire : les intérêts de la dette en plus s'accumulent. Le statu quo
lui-même diverge (docs/statu_quo.md) : il faut lire l'écart, pas le niveau.

## Limites connues

1. **Emploi des seniors** : le statu quo garde les taux d'emploi par âge de 2025 alors que ses pensions supposent
   64 ans ; le retour à 62 ans ne perd donc aucun emploi dans le modèle. À corriger dans le noyau (emploi par âge selon
   l'âge légal), ce qui alourdira le coût de RET-01.
2. **Assurance chômage** : les durées plus longues ne font pas monter le chômage (prudent : le compter).
3. **Prix** : TVA écologique, SMIC, fiscalité de l'énergie : pas d'effet sur l'inflation.
4. **Non chiffré** : sortie du nucléaire (EDF hors administrations), commerce (accords non ratifiés, préférence
   européenne), budget européen à 2 % du PIB, fonds souverain « livret industrie », renationalisation des
   autoroutes, régularisations, économies de santé de la prévention.
5. Les assiettes des nouveaux impôts (successions, Zucman, ISF, TVA écologique) sont des hypothèses encadrées, pas des
   microsimulations : ce sont les premières lignes à passer dans OpenFisca.
