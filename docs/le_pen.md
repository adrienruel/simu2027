# Programme de Marine Le Pen (Rassemblement national) : chiffrage partiel (11 novembre 2026, phase 3)

Code : `programmes/le_pen/` ; fiche des mesures : `mesures.yaml` (49 mesures et leur traitement) ; tests :
`tests/test_le_pen.py`.

## Sources

Le contre-budget et la « trajectoire financière du quinquennat » du 6 octobre 2026 ne sont pas publiés en ligne. Le
chiffrage repose sur les comptes rendus (Public Sénat, Acteurs publics, AFP, LCP), les mesures recensées par
votons-2027.fr d'après rassemblementnational.fr, candidats-presidentielle-2027.fr (illustratif), swipetonvote.fr,
FranceBudget, et les chiffrages de l'Institut Montaigne (2022, 2024). programmes-2027.fr n'était pas accessible
depuis l'outil. **À refaire** quand le document du contre-budget ou le programme complet sera publié.

## Méthode

Mêmes règles que les autres programmes : aucune économie annoncée reprise (140 Md€ nets en 2032 ; immigration 15 puis
29 Md€, État 20,7, Union européenne 9, collectivités 8,2 puis 18, agences 3,4 puis 10, retraites 15 à 20) ; chaque
économie nommée est estimée ; le reste passe par l'enveloppe déduite du programme domaine par domaine (État,
opérateurs et collectivités : cibles principales ; santé protégée ; prestations citées). En prudent, les économies
nommées dépassent déjà la capacité des domaines : l'enveloppe ajoute zéro.

- **Retraite** : 62 ans, 42 annuités, 60 ans pour les carrières commencées avant 20 ans, soit la loi d'avant 2023 :
  même calcul que Glucksmann (`bib.baisse_age_legal_detail`), emploi des seniors au scénario miroir.
- **Obstacles juridiques documentés** : contribution à l'Union européenne (zéro en prudent) ; « priorité nationale »
  sur les prestations (zéro en crise, 2 à 6 Md€ sinon).
- **Neutres contre le statu quo** : minimum vieillesse à 1 000 € (déjà 1 034 €), réindexation des pensions (déjà la
  règle), défense à 55 Md€ en 2027 (loi de programmation), assurance chômage de 2024 (jamais appliquée).
- **À vérifier** : recherche publique (+9 Md€) et « 100 % Rénov' » (+3,8 Md€), connus seulement par FranceBudget.

## Résultats (prudent)

| | 2029 | 2032 | 2037 |
|---|---|---|---|
| Déficit (% du PIB), statu quo 5,9 / – / 9,5 | 7,5 | 9,7 | 13,0 |
| Effet des mesures sur les émissions (Mt) | | | +8,1 |

Postes principaux en 2032 (Md€, + = améliore le solde) : retraite à 62 ans −23,4 (−20,6 net des prélèvements, plus
l'emploi des seniors), TVA sur l'énergie −13,3, CFE et C3S −13,3, recherche −9,2, exonération des hausses de salaire
−5,1 (jusqu'en 2033), postes non remplacés +11,2 bruts (+4,8 nets des prélèvements), priorité nationale +2,0.

Émissions : TVA à 5,5 % sur l'énergie (+5 Mt en prudent), moratoire et démontage de l'éolien terrestre (+4 Mt),
composante carbone de 2017 (+0,6), « 100 % Rénov' » (−1,3 en 2050).

## Limites

1. Le document du contre-budget n'est pas public : plusieurs montants (recherche, rénovation, postes) sont connus de
   seconde main.
2. Les effets sur l'emploi et les recettes d'une immigration plus faible ne sont pas comptés.
3. L'arrivée des réacteurs neufs (après 2037) n'est pas reliée aux émissions : l'effet du moratoire éolien est gardé
   constant.
