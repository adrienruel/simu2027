# Levier : taux de l'IS et déduction immédiate de l'investissement (29 octobre 2026)

`python -m outils.levier_is` (résultats dans `sorties/levier_is.json`) ; tests de cohérence dans
`tests/test_levier_is.py`. Prudent, déficit sans clause de trajectoire (pour voir l'effet propre du levier).

| IS total | Déduction | Taux effectif | Coût de la déduction 2037 | Érosion de l'IS 2037 | Emplois perdus (localisation) | Déficit 2029 | 2037 | 2050 | Dette 2050 |
|---|---|---|---|---|---|---|---|---|---|
| **45 %** | **100 %** | 41,3 % | 34,5 Md€ | −26,1 Md€ | 101 000 | 5,69 % | 5,97 % | 4,64 % | 156 % |
| 45 % | 50 % | 43,5 % | 13,0 | −27,2 | 132 000 | 5,51 % | 5,28 % | 4,18 % | 148 % |
| 45 % | 0 % | 45,8 % | −8,4 | −28,2 | 164 000 | 5,32 % | 4,59 % | 3,72 % | 139 % |
| 40 % | 100 % | 36,7 % | 30,1 | −16,1 | 44 000 | 6,14 % | 6,10 % | 4,96 % | 160 % |
| 35 % | 100 % | 32,1 % | 25,8 | −8,0 | (+5 000) | 6,62 % | 6,31 % | 5,41 % | 165 % |
| 30 % | 100 % | 27,5 % | 21,5 | −1,9 | (+25 000) | 7,12 % | 6,65 % | 6,03 % | 173 % |
| 25 % | 100 % | 22,9 % | 17,2 | +2,3 | (+44 000) | 7,65 % | 7,07 % | 6,78 % | 182 % |

(Ligne en gras : le programme. Coût de la déduction négatif : sans déduction, il reste la fin de la
déduction des intérêts, qui rapporte.)

## Lecture

- **Baisser le taux dégrade les comptes.** Chaque 5 points d'IS en moins coûte ≈ 19 Md€ de recettes
  statiques ; la baisse du transfert de bénéfices et le retour d'activités n'en rendent qu'une partie.
  De 45 % à 35 % : +0,3 point de déficit en 2037, +0,8 point en 2050.
- **La déduction immédiate coûte cher pendant vingt ans.** À 45 %, la supprimer réduirait le déficit de
  1,4 point en 2037 et de 0,9 point en 2050, au prix de 63 000 emplois perdus de plus par localisation et
  d'un investissement plus faible. C'est surtout un décalage dans le temps (on déduit tout de suite au lieu
  d'amortir) : le coût baisse à mesure que les amortissements de l'ancien régime s'éteignent.
- **Le résultat dépend de la réaction de l'investissement.** Le modèle prend l'élasticité au coût du
  capital des modèles français (0,24 à 0,37 : OFCE, Mésange). Les études des déductions accélérées
  trouvent des réactions bien plus fortes : +10 à +17 % d'investissement aux États-Unis (Zwick et Mahon,
  2017), +12 à +14 % pour le suramortissement numérique des PME françaises (DGE, 2026). Avec une élasticité
  de 1,6, la déduction coûte encore ≈ 1 point de déficit en 2037, mais devient plus avantageuse que son
  absence à partir de 2050 environ (4,28 % contre 4,40 %).

## Ce qui est solide et ce qui ne l'est pas

Solide (tests) : les recettes montent avec le taux ; la déduction baisse le taux effectif et coûte ; la
localisation et l'érosion suivent le bon sens ; l'investissement monte avec la déduction.
Fragile : les élasticités (transfert de bénéfices, localisation, investissement) sont estimées sur de petites
variations de taux ; un écart de 20 points de taux légal sort de leur domaine. La réaction de
l'investissement à la déduction est probablement sous-estimée (prudent contre la déduction).

## Défauts corrigés grâce à ces tests

- La fin de la déduction des intérêts divisait par la part déduite : impossible de simuler « pas de
  déduction ». Elle suit maintenant la seule montée en charge.
- Le taux effectif ignorait la part de chaque investissement déduite immédiatement (`part_admise`).
