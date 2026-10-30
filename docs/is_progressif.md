# Test d'un IS progressif (30 octobre 2026)

Demande d'Adrien : tester un IS progressif, avec le même objectif (tenue des comptes ; moins de chômage, donc
moins de RUI et plus d'impôts). Barème de l'IS de l'État par tranches de bénéfice (`entreprises.is_progressif`,
désactivé par défaut ; `moteur/is_bareme.py`), IS local de 5 % inchangé. Comparaison : `python -m outils.is_progressif`
(sorties/is_progressif.json).

## Comment le modèle traite un barème

- Recettes : barème appliqué au bénéfice de chaque classe (16 classes, DGFiP).
- Investissement et déduction : taux marginal de chaque taille, au bénéfice moyen de la taille (TPE 44 000 €,
  PME 570 000 €, ETI 11,6 M€, GE 300 M€).
- Transfert de bénéfices et localisation des activités : taux des grandes entreprises (activités mobiles).
- Dirigeants payés en salaire : IS exact au barème de leur société.
- Bailleurs, accises nettes d'IS : taux moyen effectif.
- Ajout fait pour ce test : le capital privé en plus ou en moins (investissement par taille) agit sur le chômage
  d'équilibre comme le capital du fonds (même élasticité, pondéré par l'intensité en emploi de la taille).

## Résultats (prudent, déficit sans règle ; chômage)

Barèmes neutres : le taux de la dernière tranche est calé pour garder l'IS de l'État du budget statique (145 Md€).

| Barème | Haut (État) | 2037 | 2050 | 2073 | Dette 2073 | Chômage 2037 / 2073 |
|---|---|---|---|---|---|---|
| **Taux unique 40 % (programme)** | 40 % | **4,68** | **4,09** | **0,04** | **106 %** | **7,34 / 7,07** |
| 15 % / 30 % jusqu'à 250 k€, neutre | 48,5 % | 5,63 | 5,36 | 3,21 | 143 % | 7,70 / 7,46 |
| 20 % / 35 % jusqu'à 5 M€, neutre | 54,7 % | 6,14 | 6,37 | 6,90 | 180 % | 7,95 / 7,72 |
| 25 % / 35 % jusqu'à 1 M€, neutre | 47,1 % | 5,40 | 4,99 | 3,09 | 139 % | 7,63 / 7,37 |
| 10 / 25 / 40 % jusqu'à 50 M€, neutre | 71,7 % | 7,81 | 10,01 | 40,31 | 460 % | 8,68 / 8,40 |
| 15 / 30 % jusqu'à 250 k€, 40 % au-delà | 40 % | 5,55 | 5,32 | 3,29 | 143 % | 7,33 / 7,11 |
| 25 % jusqu'à 100 k€, 40 % au-delà | 40 % | 5,18 | 4,70 | 2,13 | 130 % | 7,33 / 7,08 |
| 15 / 30 % jusqu'à 250 k€, 35 % au-delà | 35 % | 5,58 | 5,44 | 3,37 | 144 % | 7,11 / 6,92 |
| Taux unique 35 % | 35 % | 4,93 | 4,33 | 1,01 | 118 % | 7,12 / 6,88 |
| Taux unique 30 % | 30 % | 5,26 | 4,93 | 2,64 | 136 % | 6,90 / 6,69 |

## Ce qu'il faut en retenir

1. **Un IS progressif à recettes égales dégrade les comptes et le chômage.** Alléger les petites entreprises
   oblige à monter le haut du barème (47 à 72 % pour l'État), donc le taux des grandes entreprises, dont les
   bénéfices et les activités sont les plus mobiles : transfert de bénéfices (érosion de l'IS : −29 Md€ en 2050
   au taux unique, −41 à −82 Md€ avec un barème) et départ d'activités (emplois perdus par localisation : 64 000
   au taux unique en médian, 107 000 à 255 000 avec un barème).
2. **Alléger les PME en gardant 40 % en haut coûte cher et ne crée presque pas d'emplois** : 13 à 21 Md€ d'IS en
   moins, chômage inchangé. Dans le modèle, l'IS des petites entreprises ne joue sur l'emploi que par leur
   investissement (la déduction immédiate en a déjà retiré l'essentiel) ; aucune étude solide ne montre qu'une
   baisse d'IS des PME crée beaucoup d'emplois.
3. **Le levier sur le chômage est le taux des grandes entreprises** : un taux unique plus bas réduit le chômage
   (7,07 % en 2073 à 40 %, 6,88 % à 35 %, 6,69 % à 30 %), mais les recettes perdues l'emportent sur les emplois
   gagnés : les comptes sont moins bons qu'à 40 %.
4. **Le taux unique de 40 % reste le meilleur des barèmes testés pour les comptes.** Le problème des TPE et des
   PME (qui paient plus qu'aujourd'hui) se traite mieux par d'autres outils (fonds orienté vers elles, déduction,
   seuils) que par l'IS.

Limites : le transfert de bénéfices et la localisation suivent des élasticités moyennes (FMI ; Ljungqvist et
Smolyansky ; Giroud et Rauh) appliquées linéairement : au-delà de 50 % de taux, l'effet est incertain. Les
bailleurs (sociétés civiles immobilières) sont taxés au taux moyen effectif du barème.
