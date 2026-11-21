# Banc d'essai du noyau : chocs standard contre modèles publiés (21/11/2026)

`outils/banc_essai.py` → `sorties/banc_essai.csv`. Question d'Adrien : « le modèle est hyper rigide, chaque
changement ne rapporte rien ». Rien n'est réglé ici : on rejoue dans le noyau des chocs dont la réponse est publiée
pour d'autres modèles. Scénario médian (le prudent est proche), choc permanent à partir de t = 2031.

Sources :
- OFCE, document de travail 2026-9 (Mésange et ThreeME) : https://www.ofce.fr/wp/2026/9/OFCEWP2026-9.pdf ;
- DG Trésor pour le COR (mars 2026), âge d'ouverture des droits de 64 à 65 ans ;
- Fipeco (2024), recul de deux ans : +0,9 point, dont 0,5 pour les retraites et 0,4 pour les autres
  administrations ;
- COR, rapport annuel 2026, partie 2, chapitre 5 : productivité de 1 % au lieu de 0,7 %.

## 1. Dépense publique +1 point de PIB : conforme à Mésange

| Solde primaire (pt de PIB) | t | t+1 | t+4 | t+9 | LT |
|---|---|---|---|---|---|
| simu2027 | −0,50 | −0,41 | −0,58 | −0,76 | −0,83 |
| Mésange | −0,53 | −0,34 | −0,53 | −0,68 | −0,85 |
| ThreeME | −0,72 | −0,57 | −0,49 | −0,53 | −0,71 |

Le PIB suit aussi : +0,84 % à t contre +0,76 %, +0,70 % à t+4 contre +0,88 %. C'est attendu, puisque le bouclage
est calé sur Mésange : ce n'est donc pas une validation.

## 2. TVA −1 point de PIB : l'activité rend moins au budget que dans Mésange

| Solde primaire (pt de PIB) | t | t+1 | t+4 | t+9 | LT |
|---|---|---|---|---|---|
| simu2027 | −1,02 | −0,61 | −0,56 | −0,63 | −0,57 |
| Mésange | −0,80 | −0,37 | −0,37 | −0,44 | −0,47 |
| ThreeME | −0,89 | −0,68 | −0,40 | −0,33 | −0,29 |

Le PIB est proche de Mésange (+0,75 % à t+4 contre +0,81 %), mais le budget récupère environ 0,2 point de moins.
Une baisse d'impôt coûte donc plus cher que dans Mésange, et une hausse d'impôt rapporte plus.

## 3. Productivité +1 % : plus favorable que Mésange à 10 ans, moins à long terme

| Solde primaire (pt de PIB) | t | t+4 | t+9 | t+29 | LT |
|---|---|---|---|---|---|
| simu2027 | +0,11 | +0,11 | +0,11 | +0,05 | +0,03 |
| Mésange | −0,04 | 0,00 | +0,05 | +0,14 | +0,18 |
| ThreeME | −0,01 | −0,14 | −0,05 | +0,06 | +0,07 |

Où part un euro de PIB en plus (2031) : recettes +0,49 ; dépenses +0,40, dont santé 0,10, collectivités 0,08,
missions 0,07, investissement 0,04, défense 0,03, autres 0,03. En 2073, s'y ajoutent les pensions (+0,13), qui
rattrapent les salaires. Toutes ces dépenses suivent le PIB ou les salaires **dès l'année même**. C'est la
convention du statu quo, et c'est ce qui ramène le gain au solde vers zéro à long terme.

Pensions seules (variante haute du COR, +0,3 point de productivité par an) : dépenses de retraite −1,1 point de PIB
en 2070, contre −0,8 point pour le COR. Sur ce poste, le modèle est **plus** favorable à la productivité que le COR.

Artefact trouvé : les dépenses sont indexées en rapport à 2029 (indice 1). Un gain de productivité dès 2029
échappe donc à toute indexation, avec un dividende de 40 % au lieu de 9 %. Les chocs du banc partent de 2031. Les
mesures des programmes partent presque toutes après 2029, mais c'est à vérifier.

## 4. Âge d'ouverture des droits de 64 à 65 ans : 60 % de l'effet de la DG Trésor

| Solde public (pt de PIB) | 5 ans | 20 ans |
|---|---|---|
| simu2027, toute l'économie gardée | +0,26 | +0,29 |
| simu2027, part gardée de Bertrand (0,65) | +0,17 | +0,19 |
| DG Trésor (COR, mars 2026) | +0,4 | +0,5 |

Décomposition, médian, à 20 ans :

| | simu2027 | Fipeco, pour un an de recul |
|---|---|---|
| Pensions en moins | +0,26 | ≈ +0,25 |
| Reste du budget | **≈ 0** : recettes +0,06, autres dépenses −0,04 | ≈ +0,2 |
| Emploi | +112 000 | |
| PIB | +0,26 % | |

Le PIB en plus ne revient au budget qu'à environ 25 %, contre 53 % pour la DG Trésor (taux de prélèvements
obligatoires).

## Constats
1. **Ce n'est pas la dépense ni le multiplicateur :** ils sont conformes à Mésange.
2. **Le retour de l'activité au budget est faible.** Quand une mesure crée des emplois ou de l'activité, le budget
   en récupère environ 25 à 35 %, contre environ 50 % dans Mésange et dans le modèle comptable de la DG Trésor.
   C'est l'écart principal (âge, TVA). À vérifier : si le dividende de productivité, pensé pour des salaires plus
   hauts, s'applique aussi aux emplois en plus (qui ne relèvent pas les salaires par tête), et ce que vaut
   `emploi.valeur_emploi` contre le taux de prélèvements de 53 %.
3. **L'emploi des seniors est bas :** environ 110 000 emplois pour un an d'âge, avec 58 % des seniors maintenus
   qui deviennent inactifs (`seniors.part_concernee` = 42 %, déjà au chantier 2.3 de la roadmap).
4. **L'indexation immédiate de toutes les dépenses sur le PIB** efface à long terme le gain de la productivité.
   C'est une convention à revoir bloc par bloc (missions et défense votées en euros, ONDAM, chantier 1.2).
5. **Les pensions ne sont pas trop rigides :** elles répondent plus que celles du COR à la productivité.
