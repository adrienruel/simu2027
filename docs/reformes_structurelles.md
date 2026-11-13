# Réformes de structure : barème commun restreint au champ de l'OCDE (12 novembre 2026)

Source : Égert et Gal (2017), OCDE, document de travail n° 1354. Paramètres : `macro.reformes_structurelles`
(commun), `<nom>_canaux.reformes_structurelles` (chaque programme), `macro.reformes_programme` (Écologie de droite).
Code : `moteur/reformes_structurelles.py`.

DÉCISION d'Adrien du 12/11/2026, après la seconde relecture neutre (docs/relecture_neutre_2_rapport.md, point 2) :
ne compter que ce que mesurent les deux indicateurs de l'article, avec la même grille pour tous.

## Champ

- **Marchés de produits** (indicateur ETCR) : électricité, gaz, télécommunications, poste, rail, aérien, fret routier.
  Ce qui compte : entrée sur le marché, propriété publique, structure du marché, prix réglementés.
- **Protection de l'emploi** (EPL des contrats réguliers) : règles du licenciement.
- **Hors champ, pour tous** : normes générales et simplification, commande publique, banques et assurances,
  autoroutes, aéroports, audiovisuel, santé, logement, commerce de détail et prix de détail (carburant), commerce
  extérieur, subventions et taxes (comptées ailleurs).

## Grille

- 1 : un secteur entier du champ (nationalisation, sortie du marché, refonte), contrat unique, interdiction des
  licenciements ;
- 0,5 : mesure ciblée dans un secteur du champ (une grande entreprise, prix réglementés, entrée interdite ou facilitée
  sur un segment, refonte du code du travail) ;
- positif : libéralise ; négatif : réglemente ou nationalise ; plafond ±2 par domaine.

## Compteurs

| Programme | Marchés de produits | Avant | Protection de l'emploi | Avant | Mesures retenues |
|---|---|---|---|---|---|
| Arthaud | −2 | −2 | −1 | −2 | électricité et transports hors du marché (1 + 1) ; interdiction des licenciements (1) |
| Roussel | −1,5 | −2 | 0 | 0 | Engie dans un pôle public, transports nationalisés, sortie du marché européen de l'électricité |
| Mélenchon | −1 | −2 | −0,5 | −0,5 | Engie renationalisé, tarifs réglementés de l'énergie ; licenciements boursiers interdits |
| Tondelier | −1 | −1 | 0 | 0 | tarif progressif de l'électricité, vols courts interdits |
| Glucksmann | −0,5 | −0,5 | 0 | 0 | facture d'électricité indexée sur le coût de production |
| Le Pen | −0,5 | −0,25 | 0 | 0 | moratoire sur l'éolien terrestre et démontage des parcs |
| Attal | −0,5 | 1 | 0,5 | 0,5 | électricité à ≈ 75 €/MWh par la régulation ; code du travail réécrit |
| Bertrand | 0 | 0 | 0 | 0 | — |
| Philippe | 0 | 1,25 | 0 | 0 | — |
| Zemmour | 0 | 0,75 | 0 | 0 | — |
| Retailleau | 0 | 0,5 | 0,5 | 0,75 | code du travail refondé (les seuils sociaux ne comptent plus) |
| Lisnard | 0 | 1,75 | 1 | 1 | contrat de travail unique |
| Écologie de droite | 0,5 | 1 | 0,5 | 0,5 | permis rapide pour la production d'énergie ; contrat de travail assoupli |

## Lectures confirmées par Adrien (12/11/2026, soir, roadmap B1)

- Arthaud : l'interdiction des licenciements vaut 1, comme dans la grille (−2 auparavant, hors grille).
- Attal : « électricité à 75 €/MWh » lu comme un prix réglementé (−0,5), comme la facture de Glucksmann et les tarifs
  de Mélenchon.
- Tondelier : le tarif progressif de l'électricité et l'interdiction des vols courts comptent ; la sortie du
  nucléaire, choix de technique, ne compte pas.
- Le Pen et Écologie de droite : l'entrée sur la production d'électricité compte dans les deux sens (moratoire
  éolien −0,5, permis rapide +0,5).
- La décote de la protection de l'emploi (trois quarts de l'effet) reste ; elle ne vient pas de l'article.

## Ce que rapporte le gain

Le PIB en plus rapporte au solde le dividende de productivité du statu quo (`statu_quo.dividende_productivite`) :
≈ 25 % la première année, 12 % après dix ans, presque rien à très long terme, parce que les dépenses indexées sur les
salaires montent avec la productivité. Même règle pour l'IA, l'école et la part productivité du canal d'offre.

## Vérification sur le texte (phase C2, 13/11/2026)

Texte lu : version de travail présentée à l'atelier « structural reforms » (Égert et Gal, ECO/WKP(2016)78,
https://www.structural-reforms.eu/workshops/session2/Egert-Gal-structural-reforms.pdf), mêmes résultats que le
document de travail n° 1354 de l'OCDE (2017), dont le PDF n'est pas lisible depuis cet environnement.

- Tableau 4 (effet total sur le PIB par habitant) : réglementation des marchés de produits (ETCR, réforme typique
  −0,31 point) +0,72 % à 5 ans, +1,02 % à 10 ans, +2,09 % à long terme ; protection de l'emploi des contrats
  réguliers (EPL, réforme typique −0,30 point) +0,22 %, +0,57 %, +1,83 %. **Les six valeurs du barème sont exactes.**
- Tableau 3 (5 ans, par composante) : ETCR = productivité globale des facteurs 0,53 %, capital 0,07 %, emploi 0,10 ;
  pour l'EPL, l'extraction du tableau ne permet pas de lire sûrement les colonnes (0,24 % et 0,07). L'EPL n'est pas
  parmi les déterminants de la productivité globale (tableau 1) : son effet passe par le capital et l'emploi.
- **Décote de l'EPL** (`part_hors_emploi_epl` = 0,75) : toujours sans source. D'après le tableau 3, l'effet de l'EPL
  à 5 ans passerait surtout par le capital, donc hors emploi : la part hors emploi serait proche de 1, et 0,75 est
  plus prudent que le texte. À confirmer sur le PDF de l'OCDE (tableaux 3, A6.3 et A6.4) ; en attendant, la valeur
  reste une décision.
