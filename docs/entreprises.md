# Entreprises par taille (30 octobre 2026)

`moteur/entreprises_cellules.py`, données `parametres/donnees/entreprises_tailles.csv`, paramètres
`entreprises_cellules.*`, tests `tests/test_entreprises_cellules.py`. Demande d'Adrien : le comportement des
entreprises, comme les cellules de ménages. Première étape : quatre tailles (TPE, PME, ETI, GE).

## Données

| Taille | Entreprises à l'IS | Bénéfices | IS brut | Salariés (ETP) | Valeur ajoutée | Investissement / VA | Impôts de production / VA |
|---|---|---|---|---|---|---|---|
| TPE | 2 489 000 | 65,9 Md€ | 14,0 Md€ | 2,41 M | 186 Md€ | 26,3 % | 1,0 % (hypothèse) |
| PME | 221 000 | 78,5 | 19,2 | 3,99 M | 277 | 15,2 % | 1,9 % |
| ETI | 9 000 | 64,5 | 16,2 | 3,46 M | 307 | 19,8 % | 2,9 % |
| GE | 400 | 75,0 | 19,6 | 3,98 M | 409 | 23,7 % | 3,4 % |

Sources : DGFiP, L'impôt sur le bénéfice 2024 des entreprises (Statistiques n° 39, 2025), tableau 2 ; Insee, Les
entreprises en France, catégories d'entreprises, Ésane 2021 (secteurs principalement marchands, catégories
MIC/PME/ETI/GE) ; DGFiP, Les impôts de production en 2023 (Statistiques n° 35, 2025) : poids des impôts d'origine
fiscale dans la valeur ajoutée (« très faible » pour les microentreprises).

## Ce que le module change

1. **Impôts de production des entreprises déficitaires.** Le budget statique ajoutait les 75 Md€ d'impôts de
   production supprimés (hors secteur non marchand) au bénéfice imposable des seules entreprises bénéficiaires.
   Une part est payée par des entreprises déficitaires (20 % dans le prudent, hypothèse : 36 % des entreprises à
   l'IS sont déficitaires, surtout petites) ; sa suppression réduit leurs pertes et n'est imposée que plus tard,
   quand les déficits reportés sont imputés (31 % : 35 Md€ imputés pour 112 Md€ de déficits par an, DGFiP).
   Base de l'IS nouveau : −13,8 % des impôts de production ajoutés ; IS de l'État −4,2 Md€ par an.
2. **Qui paie.** Bilan statique, avant la déduction immédiate de l'investissement et avant les réactions :

| Md€ de 2026 | IS actuel | Impôts de production | Total actuel | IS nouveau (45 %) | Écart |
|---|---|---|---|---|---|
| TPE | 14,6 | 4,7 | 19,2 | 33,2 | +14,0 (+73 %) |
| PME | 20,0 | 13,2 | 33,2 | 42,5 | +9,3 (+28 %) |
| ETI | 16,8 | 22,4 | 39,2 | 39,4 | +0,2 (0 %) |
| GE | 20,4 | 35,0 | 55,4 | 49,3 | −6,1 (−11 %) |

   Le programme déplace l'impôt des grandes entreprises vers les petites : les TPE passent du taux réduit de 15 %
   à 45 % et payaient peu d'impôts de production.
3. **Investissement par taille.** Chaque taille a son taux marginal actuel (TPE 19 %, mélange du taux réduit et du
   taux normal ; autres 25 %), sa part d'impôts de production sur le capital (relative à la moyenne) et sa
   réaction : les petites entreprises réagissent 95 % plus que les grandes (Zwick et Mahon, AER 2017 ; PME et ETI
   interpolées), l'élasticité moyenne restant celle du module macro. Effet : le canal reste petit (la déduction
   compense le taux), un peu plus défavorable (−0,3 Md€ en 2037 dans le prudent, contre −0,2).

## Effet sur les résultats

| Sans règle / publié | 2029 | 2037 | 2050 | 2073 | Dette 2073 |
|---|---|---|---|---|---|
| Prudent avant | 4,76 / 3,00 | 4,34 / 3,00 | 3,83 / 3,00 | −0,84 / −0,84 | 95 % |
| Prudent après | 4,90 / 3,01 | 4,59 / 3,00 | 4,08 / 3,03 | −0,16 / −0,16 | 104 % |
| Crise après | 4,97 / 3,09 | 5,18 / 3,48 | 4,56 / 3,49 | 5,80 / 4,67 | 157 % |

En 2029, la règle est au maximum dans le prudent (5 points d'épargne pris, RUI baissé de 148 € par mois jusqu'au
plancher) et ne suffit plus tout à fait (3,01 %).

## Ce qui manque (étapes suivantes)

- **Réaction des TPE** : avec un IS à 45 %, des dirigeants de petites sociétés passeront à l'impôt sur le revenu
  ou se verseront un salaire (arbitrage avec le barème de l'impôt unique) : base des TPE à risque, non comptée.
- **Secteurs** (industrie, commerce, construction, services) : impôts de production très inégaux (industrie
  16 %, commerce et transports 18 %).
- **Démographie des entreprises** : créations, défaillances, passage de PME à ETI.
- **Incidence** : part des impôts répercutée sur les salaires et les prix (Fuest, Peichl et Siegloch, 2018 :
  environ la moitié de l'impôt local sur les entreprises retombe sur les salaires).
- **Localisation et transfert de bénéfices** par taille (aujourd'hui en agrégat, part des grandes entreprises).
