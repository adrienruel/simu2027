# Barème commun de l'assurance chômage (27/11/2026)

Demande d'Adrien : la baisse (ou la hausse) du chômage d'une réforme de l'assurance chômage dépend du type de réforme,
et chaque type a sa source. Avant, chaque programme fixait sa propre valeur (0,1 à 0,3 point au prudent), et les
abrogations prenaient une valeur commune de 0,6 point.

Fonction : `moteur/bibliotheque.effet_assurance_chomage`. Paramètres : `assurance_chomage.*`
(`parametres/commun/economie.yaml`). Déclaration de chaque programme : `<nom>_chomage.reforme` (statut DECISION).

| Type de réforme | Effet sur le chômage structurel | Source |
|---|---|---|
| Durée maximale d'indemnisation | −0,4 point pour −25 %, linéaire, au prorata des allocataires concernés | Banque de France, Bulletin n° 264/1 (2026), p. 6 et 11-12 : réforme de 2023, élasticité de Le Barbanchon (2016) ≈ 0,25 |
| Salaire journalier de référence (réforme de 2021) | −0,2 point | même Bulletin, p. 6 |
| Dégressivité | −0,015 point pour 0,4 Md€ d'économie, au prorata de l'économie | Comité d'évaluation 2019-2021 (Dares, 2025), p. 1, 13, 17 : 40 000 personnes, −1,5 mois hors emploi |
| Condition d'affiliation | zéro | même comité, p. 23-24 : effet à deux mois, plus visible deux à trois ans après |
| Contrôles, refus d'offres, ruptures conventionnelles, indemnisation dès le premier jour, régimes particuliers | zéro | aucune évaluation chiffrée |
| Abrogation d'une réforme | l'effet de la réforme, de signe inverse | — |

Scénarios (`assurance_chomage.facteurs`, DECISION) : une baisse du chômage vaut l'effet de la Banque de France au
médian et à l'optimiste, ses deux tiers durables au prudent (Bulletin, p. 12), un tiers en crise ; une hausse prend
le scénario miroir (entière en crise et au prudent, deux tiers au médian, un tiers à l'optimiste).

Lectures (prudent, point de chômage) :

| Programme | Déclaration | Effet |
|---|---|---|
| Attal | durée de 18 à 15 mois ; affiliation (zéro) | −0,18 |
| Philippe | durée de 18 à 12 mois pour les moins de 50 ans (83 % des ouvertures de droit, Unédic 2025) | −0,30 |
| Retailleau | durée de 18 à 15 mois ; dégressivité au-dessus de 3 000 € (1 Md€) ; ruptures conventionnelles et refus (zéro) | −0,20 |
| Lisnard | dégressivité élargie (1 Md€) | −0,025 |
| Glucksmann, Mélenchon, Roussel, Tondelier | réformes de 2021 et 2023 abrogées | +0,6 |
| Bertrand | économies non détaillées : pas d'effet (réforme non décrite) | 0 |
