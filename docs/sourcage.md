# Sourçage des paramètres

Ordre de travail : les hypothèses qui pèsent le plus sur le déficit d'abord (`moteur/sensibilite.py`,
tableau de bord, « Les hypothèses qui pèsent le plus »).

Règles :
- une valeur publiée par une source officielle remplace l'hypothèse (statut SOURCE) ; l'ancienne valeur reste
  dans le champ `v235`, que les tests de reproduction utilisent (`Parametres(reference="v235")`) ;
- une hypothèse qu'une source encadre sans la fixer garde le statut HYPOTHESE avec un champ `source`
  (« encadrée ») ; si la valeur retenue n'est pas la plus prudente de la fourchette, c'est à trancher.

## Corrigés (29 octobre 2026)

| Paramètre | v235 | Nouveau | Source | Effet sur le déficit publié |
|---|---|---|---|---|
| rui_complements.enfants | 11 500 000 | 10 724 000 | Insee Première n° 2032 : 13 882 000 mineurs en famille (2023), dont 3 158 000 en famille monoparentale | ensemble des deux : +0,02 point |
| rui_complements.enfants_parent_isole | 2 500 000 | 3 158 000 | idem | (inclus ci-dessus) |
| macro.taux_reference_is | 25 % | 25 % (sourcé) | Article 219 du CGI | aucun |

## Décisions d'Adrien du 29 octobre 2026

| Paramètre | v235 | Retenu | Raison |
|---|---|---|---|
| macro.taux_long_terme | 3,3 % | **4,0 %** | Niveau du marché (OAT à 10 ans, juillet 2026), avant tout effet des réformes |
| macro.baisse_spread | 0 / 0 / 0,2 / 0,4 point | inchangé, désormais documenté | L'effet des réformes sur les taux est incertain : aucun en crise et en prudent, un quart de l'écart avec le Bund (≈ 0,8 point) dans le médian, la moitié dans l'optimiste |
| calendrier.inflation | 1,8 % | 1,8 % (décision) | Entre la Banque de France (1,6 % en 2028) et la cible de la BCE (2 %) |
| consommation.exposant et coefficient | 0,92 et 2,05 | **0,7914 et 7,184** | Recalés sur les quintiles de l'Insee (IP n° 1815) ; à recaler sur des ménages à l'étape OpenFisca |

### Résultats après ces décisions (déficit publié, clause comprise)

| | 2029 | 2032 | 2037 | Dette 2050 | Durablement sous 3 % |
|---|---|---|---|---|---|
| Crise | 4,87 % | 4,46 % | 3,92 % | 155 % | 2057 |
| **Prudent** | **4,86 %** | **4,46 %** | **3,51 %** | **139 %** | **2053** |
| Médian | 4,86 % | 4,46 % | 3,51 % | 99 % | 2039 |
| Optimiste | 4,41 % | 2,94 % | 1,27 % | 56 % | 2032 |

Prudent avant clause : 5,42 % / 5,85 % / 5,33 %. (v235 : 4,67 % / 3,81 % / 2,31 % ; avant clause 5,23 % / 5,18 % / 4,07 %.)

## Décisions d'Adrien du 29 octobre 2026 (après-midi)

| Paramètre | v235 (crise / prudent / médian / optimiste) | Retenu | Source |
|---|---|---|---|
| macro.ia_productivite (points de productivité par an, dix ans) | 0,10 / 0,185 / 0,27 / 0,475 | **0,07 / 0,07** / 0,27 / 0,475 | Acemoglu (2024) pour la crise et le prudent ; Aghion et Bunel (2024) pour le médian |
| macro.multiplicateur | 1 / 0,75 / 0,5 / 0,3 | **1,3 / 1 / 1 / 0,5** | « se caler sur les experts » : CAE (2024) 1 ; FMI (2012) 0,9 à 1,7 en crise, 0,5 avant 2008 |
| carbone.option_prix | prix monté à 300 € en 2030 puis valeur de l'action pour le climat | confirmé, hausse arrêtée en 2060 | Quinet III |

Déficit publié du prudent après ces décisions : 5,31 % / 4,70 % / 3,73 % en 2029 / 2032 / 2037 (avant clause 5,74 % / 6,15 % / 5,73 %).

## Calculé par le moteur au lieu d'être saisi (29 octobre 2026)

| Paramètre | v235 | Maintenant | Effet |
|---|---|---|---|
| Gains du quotient conjugal | 8 510 € (couple à un revenu), 580 € (deux revenus) : résultats figés d'une simulation avec un ancien barème | Calculés avec le barème en vigueur sur la distribution des coûts employeur (privé et public aligné), corrélation des revenus 0,4 : **9 900 €** et **500 €** | coût du quotient conjugal 20,9 Md€ au lieu de 18,9 ; déficit +0,07 point |

| Assiette de l'impôt local | 1 169 Md€ saisis, décrits comme « salaires, traitements, pensions » | Calculée sur ceux qui paient l'impôt local (décision du 29/10) : coût employeur des salariés et des agents, salaire des indépendants, au-delà de 12 500 € : **1 174 Md€** ; les indépendants paient désormais l'impôt local sur leur salaire (3,0 Md€) | taux moyen 7,17 % au lieu de 7,20 % ; déficit inchangé à 0,01 point près |

| Imposition commune des couples de retraités | 0,894 fixe (correction de l'impôt des anciennes pensions), plus un forfait de 1 Md€ « couples de retraités » dans le quotient conjugal : les mêmes couples comptés deux fois | Calculée année par année sur la distribution DREES des pensions : 60 % des retraités en couple, corrélation 0,2 (valeurs prudentes, sans source) ; la part du forfait qui porte sur l'ancien système est rendue | correction 0,92 en 2029, 0,82 vers 2050 ; recette +2,4 Md€ en 2029, −0,6 Md€ en 2050 ; déficit 2029 −0,06 point |

| independants.passage_2023_2026 | 1,0395 saisi | **1,0706** : +2,7 % en 2024 pour les non-salariés classiques (Insee Première n° 2114), puis comme les salaires (+2,0 % et +2,2 %) | déficit −0,04 point |

| carbone.fin_hausse | Prix porté à 300 € (de 2023) en 2030 puis +3,2 % par an jusqu'en 2073 (1 221 € de 2026) | Hausse arrêtée en 2060, comme la valeur de l'action pour le climat (811 € de 2026) ; la montée du prix est confirmée par Adrien | effet après 2060 seulement |

| TVA payée aujourd'hui par les retraités | 41 Md€ saisis | **34,0 Md€** calculés : 16,3 millions de retraités résidant en France, pension nette moyenne 1 692 € fin 2023 (DREES) revalorisée de 5,3 %, distribution DREES, impôt sur le revenu moyen 6 % (hypothèse), fonction de consommation actuelle | déficit +0,15 point environ |

## Sources ajoutées (sans changement de valeur)

| Paramètre | Source |
|---|---|
| tva.prix_carbone_2024 (256 €) | Valeur de l'action pour le climat **2025**, en euros de **2023** (Quinet III) ; les trois hausses qui la passent en euros de 2026 sont l'inflation 2024 (2,0 %), 2025 (0,9 %, Insee) et la prévision 2026 (2,1 %). La valeur est juste ; seul le nom du paramètre trompe. |
| budget_etat.contribution_ue_courants (30,9 Md€) | PLF 2027 (28,4 Md€ en LFI 2026) |
| successions.base_nouveau_systeme (16,6 Md€) | Droits de succession 2023 (Fipeco) ; montant de 2023 compté en euros de 2024 |
| rui_complements.aah (14,6 Md€) | PLF 2026 |
| inactifs.chomeurs_bit (2,7 millions) | Insee, Informations rapides n° 192, 2e trimestre 2026 |
| alignement.versants (parts) | Insee, rémunération des salariés des administrations publiques 2025 : État 45 %, local 29 %, sécurité sociale 26 % ; le modèle retient 48 / 29 / 23 (hôpitaux seuls dans la sécurité sociale) |
| alignement.versants (charges 52 %) | Cotisations CNRACL 2026 : 60,7 % du traitement indiciaire ; 52 % du brut primes comprises est plausible, à recalculer avec OpenFisca |

## Contrôle global

Avec la TVA des retraités recalculée, le modèle reconstitue une TVA actuelle d'environ 202 Md€, contre 206 Md€ perçus en 2024 (Fipeco) : l'écart (−2 %) va dans le sens prudent, puisque les recettes du nouveau système sont calées sur cette TVA actuelle.

## Reste à reprendre

| Paramètre | Constat |
|---|---|

## Sources consultées

- Banque de France, projections macroéconomiques intermédiaires, septembre 2026.
- Insee Première n° 2032 (2025), enfants vivant en famille.
- Insee Première n° 1815 (septembre 2020), épargne et consommation par niveau de vie.
- Insee, bilan démographique 2025 (population au 1er janvier 2026 : 69,1 millions).
- France Stratégie, avis du CS ESE du 21 mai 2025 sur la valeur de l'action pour le climat.
- ABC Bourse, 29 juillet 2026 : OAT à 10 ans au-dessus de 4 %.
- CAE, Focus n° 124 (octobre 2025) : taux apparent de la dette 2,0 % en 2025, OAT 10 ans 3,5 % à l'époque.

## Paramètres ajoutés le 29 octobre 2026 (fin d'après-midi)

| Paramètre | Statut | Valeur (prudent) | Source ou raison |
|---|---|---|---|
| demographie.scenario_fecondite | DÉCISION | central (crise : fécondité basse ; optimiste : haute) | Insee, projections 2026 |
| demographie.taux_emploi_age | SOURCE | 2025, figés | Insee, Dares, COR (50-54 ans calculé) |
| demographie.natalite_semi_elasticite | HYPOTHÈSE encadrée | 1 % de naissances pour 100 € par an | Espagne (González et Trommlerová), Israël (Cohen, Dehejia, Romanov) |
| demographie.creches_effet | HYPOTHÈSE encadrée | +1,4 % pour +10 points | Bauernschuster, Hener et Rainer (2016), moitié |
| famille.creches_nouvelles | DÉCISION | +10 points de couverture dès 2030 | Adrien |
| famille.cout_place_fonctionnement / investissement | SOURCE / HYPOTHÈSE encadrée | 19 450 € / 42 000 € | Onape 2025 ; IGAS-IGF 2017 |
| rui_complements.part_enfant_rang3 / enfants_rang3 | DÉCISION / SOURCE | 25 % / 1 696 600 | Adrien ; Insee RP 2023 |
| rui_complements.part_enfant_rang2 / enfants_rang2 | DÉCISION / SOURCE | 15 % (variante 25 %) / 4 303 600 | Insee RP 2023 |
| ancien_systeme.part_retraites_age | HYPOTHÈSE encadrée | profil de 2023 décalé à 64 ans | DREES, fiche 16 |
| ancien_systeme.pension_nouveaux_relative | SOURCE | 0,935 | DREES, fiches 5 et 7 |
| ancien_systeme.droits_geles_des_2029 | DÉCISION | non (calculée au départ, puis gelée) | Adrien |
| ancien_systeme.age_legal | DÉCISION | 64 → 65 ans, deux trimestres par génération | programme |
| is_investissement.part_admise / hausse_part_admise | DÉCISION | 50 %, puis +5 points par année suivant un déficit < 3 % | Adrien |
| retraites.socle_plein | DÉCISION | 1 200 € (v235 : 1 300) | Adrien |
| emploi.baisse_cout_travail | DÉCISION | 2,5 % (v235 : 5 %) | Adrien |
| emploi.participation_inactifs | HYPOTHÈSE encadrée | élasticité 0,1 sur 1,93 million | Chetty et al. ; Bargain et al. ; Insee |
| macro.prime_dette / maturite_moyenne_dette | HYPOTHÈSE encadrée / SOURCE | 3 points de base par point de dette ; 8,5 ans | CBO 2019, Laubach 2009 ; AFT |
| macro.usure_capital_fonds | HYPOTHÈSE encadrée | 4 % | Banque de France ; durées des actifs régulés |
| macro.externalites_capital_fonds | HYPOTHÈSE encadrée | 0 (médian 1 %, optimiste 2 %) | Bom et Ligthart (2014) |

Décompte des paramètres : 404, dont 109 sourcés, 89 décisions, 31 hypothèses encadrées, 175 hypothèses sans source.
