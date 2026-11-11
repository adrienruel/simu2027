# Glucksmann (Place publique) : chiffrage sur le noyau (7 novembre 2026)

```
programmes/glucksmann/ (parametres.yaml, mesures.yaml, programme.py) ; tests/test_glucksmann.py
python -m moteur.noyau glucksmann
```

## Sources

Pas de programme présidentiel publié au 6/11/2026. Les sources sont les suivantes :
- « Notre vision pour la France. Acte I » (Place publique, 23 juin 2025), présenté comme une vision ;
- les débats de LCP (23/09 et 05/10/2026) ;
- Public Sénat (24/08/2026) ;
- L'Info Durable (12/10/2026).

Les 112 mesures recensées par programmes-2027.fr sont toutes dans la fiche, avec leur traitement :
- un paramètre de chiffrage ;
- ou la raison de ne pas les chiffrer (réglementation, institutions, niveau européen).

Seul le plan contre les violences sexistes et sexuelles est chiffré par le candidat (1 Md€). Les ≈ 15 Md€ attendus des très gros héritages ne sont pas repris : la recette est estimée à part, à 4 Md€ en prudent.

## Mesures calculées

| Mesure | Calcul | Prudent 2032 |
|---|---|---|
| SMIC à 1 600 € net en deux ans | bibliotheque.smic, mêmes paramètres que Mélenchon | ≈ −7 Md€ net, 171 000 emplois perdus |
| CSG sur les salaires −15 Md€ | fraction de la suppression OpenFisca de Zemmour, impôt sur le revenu et prestations en sens inverse | ≈ −13 Md€ net, +32 000 emplois (offre) |
| Retour à 62 ans en 2028 | baisse_age_legal_detail, même profil que Tondelier (âge légal réel des générations depuis la relecture neutre) | ≈ −23 Md€, −264 000 emplois de seniors |
| Assurance chômage abrogée | 6 Md€ (bloc chômage) et +0,6 point de chômage (Banque de France) | −190 000 emplois |
| Territoires zéro chômeur généralisés | 60 000 emplois aidés, éviction de 15 % | +51 000 emplois nets |
| Service civique obligatoire de dix mois | 8 Md€ ; une génération de 800 000 jeunes, 20 % pris sur l'emploi | −133 000 emplois, sans chômeurs en plus |

**Nouveau dans le moteur** : `ProgrammeSimple` accepte `self.actifs_en_plus[(id(p), s)]`. Ce sont des personnes qu'une mesure retire de la population active. Leurs emplois perdus ne font donc pas de chômeurs (cas du service civique).

## Résultats (2037 ; solde primaire contre le statu quo, points de PIB)

| Scénario | Solde 2029 | Solde 2037 | PIB | Chômage : programme / statu quo | Emplois (milliers) | dont seniors | PIB encore nécessaire | Déficit : programme / statu quo |
|---|---|---|---|---|---|---|---|---|
| crise | −2,5 | −4,0 | −1,5 % | 11,3 / 10,3 | −862 | −324 | +7,5 % | 19,2 / 12,3 |
| prudent | −1,7 | −3,3 | −1,1 % | 9,0 / 8,3 | −692 | −278 | +6,3 % | 14,7 / 9,7 |
| médian | −1,4 | −2,6 | −0,8 % | 8,7 / 8,3 | −512 | −253 | +5,1 % | 12,3 / 8,5 |
| optimiste | −0,8 | −2,0 | −0,4 % | 8,3 / 8,3 | −335 | −228 | +3,9 % | 10,9 / 8,2 |

Lecture : les recettes nouvelles (≈ 12 Md€ en prudent) sont plus qu'absorbées par la baisse de CSG et celle de la taxe sur l'électricité. Les dépenses tiennent surtout aux postes suivants :
- retraite à 62 ans ;
- État : école, service civique, aide au développement, point d'indice ;
- prestations : assurance chômage, chèque énergie, garde d'enfants.

## Limites

1. Émissions chiffrées le 11/11/2026 (`glucksmann_ecologie`) : MaPrimeRénov', écoles, Ticket climat, transport rural, niches des transports, fonds chaleur, agriculture. La sortie du gaz et du pétrole reste sans effet compté : moyens non précisés.
2. Le niveau européen est hors du solde national, en particulier le remboursement de l'emprunt de 500 Md€ (après 2035).
3. Retraite à 62 ans : recalée le 11/11/2026 (relecture neutre) sur l'âge légal réel de chaque génération, soit 15 Md€ en 2029 et ≈ 23 à 25 Md€ à plein effet ; chiffrages publics : 10 à 20 Md€.
4. Il n'y a pas de document de programme : à refaire quand le programme présidentiel sortira.


Résultats après la relecture neutre du 11/11/2026 : voir docs/programmes_novembre.md.
