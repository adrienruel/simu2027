# Nouveau nucléaire : canal commun (27/11/2026)

Demande d'Adrien : « pour ceux qui ne disent rien, il faut intégrer les nouveaux EPR qui vont être livrés, avec la
conséquence sur le prix de l'électricité et la décarbonation ». Code : `moteur/nucleaire.py` ; paramètres : groupe
`nucleaire` de `parametres/commun/ecologie.yaml` (sources et hypothèses) ; branchement : `statu_quo.blocs`
(bloc `etat_missions`) et canal déclaré `nucleaire` (`moteur/canaux_declares.py`).

## Statu quo : les six EPR2 décidés
- Calendrier (EDF, décembre 2025) : Penly en 2038, puis un réacteur tous les 12 à 18 mois. Optimiste 2038 / 12 mois ;
  médian 2039 / 15 ; prudent 2040 / 18 ; crise 2041 / 18. 1,67 GW, 80 % de facteur de charge : 11,7 TWh par réacteur.
- Coût : 72,8 Md€ de 2020 pour six, 13,9 Md€ de 2026 par réacteur (+10 % au prudent, +20 % en crise).
- Prêt du fonds d'épargne (60 % du coût, CPN du 12/03/2026, PLF 2027) : hors des administrations publiques, il
  n'entre pas dans la dette ; l'État paie la bonification (taux de la ressource, 3 %, pendant le chantier ; une part
  après la mise en service : 50 % au prudent et au médian).
- Contrat pour différence (100 € de 2024 par MWh, 40 ans) : l'État paie l'écart avec le prix de marché (70 € au
  prudent, 80 au médian, 90 en optimiste, 60 en crise ; hypothèse), reçoit l'excédent au-dessus.
- Coût pour l'État, prudent : 0,9 Md€ en 2035, 1,6 en 2040, 3,0 en 2050. Déficit du statu quo en 2037 : +0,04 point.

## Programmes
Un programme déclare son parc (`<nom>_canaux.nucleaire`) ; sans déclaration, il a celui du statu quo.

| Programme | Déclaration | Budget en 2050 (prudent, Md€) | Prix de l'électricité en 2060 |
|---|---|---|---|
| Attal, Philippe, Zemmour | 14 EPR2 | +2,2 | −10 % |
| Retailleau | 14 EPR2, parc prolongé | +2,2 | −13 % |
| Roussel | 20 EPR2, parc prolongé (SMR non comptés) | +3,2 | −13 % |
| Le Pen | 10 EPR2 (milieu de « 6 à 14 », à valider) | +1,3 | −5 % |
| Mélenchon | aucun EPR2, fermetures à 60 ans | −3,0 | +9 % |
| Tondelier | sortie accélérée | −3,0 | +18 % |
| Autres (Glucksmann, Lisnard, Bertrand, Arthaud) | statu quo | 0 | 0 |

- Prix : coût complet annualisé du système électrique de RTE en 2060 (Futurs énergétiques 2050 : M0 80, M1 77,
  M23 71, N1 66, N2 61, N03 59 Md€ par an), interpolé sur le nombre d'EPR2 (statu quo : 68), rapporté au statu quo,
  monté de 2035 à 2060.
- Décarbonation : électrification des transports et des bâtiments par le prix de l'électricité
  (`ecologie.elasticite_croisee_electricite` : 0 au prudent, 0,1 au médian, 0,2 en optimiste) ; médian 2050 : −0,6 Mt
  pour 14 EPR2, +1,0 Mt pour la sortie accélérée. Le gaz de secours d'une sortie reste compté à part
  (`<nom>_ecologie.sortie_nucleaire`, Tondelier et Mélenchon).

## Limites
- Le prix de l'électricité ne passe que par les émissions : pas de canal des prix dans le moteur (pouvoir d'achat,
  compétitivité). Une sortie économise au budget le soutien aux EPR2, mais l'électricité y est plus chère, payée par
  les ménages et les entreprises : à lire ensemble.
- Coûts de RTE de 2021, avant la hausse de 40 % du devis des EPR2 ; l'actualisation est en cours (2026).
- Non comptés : dividendes et dépréciations d'EDF, démantèlement anticipé, SMR, importations et exportations
  d'électricité.
