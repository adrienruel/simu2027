# Recoupements du statu quo avec les projections publiées (phase C3 de la roadmap)

13 novembre 2026, commit de référence : celui de ce fichier. Statu quo : scénario prudent (`sorties/comparaison_trajectoire.csv`).
Tolérance de la roadmap : 0,5 point de PIB pour les flux ; au-delà, l'écart est expliqué.

| Grandeur | Référence publiée | Valeur publiée | Statu quo (prudent) | Écart | Lecture |
|---|---|---|---|---|---|
| Dépenses de retraite (% du PIB) | COR, rapport annuel de juin 2026, scénario de référence | 14,1 % (2025) ; 14,2 % (2045) ; 15,3 % (2070) | 14,1 % (2029) ; 14,3 % (2040 et 2050) ; 15,3 % (2070) | ≤ 0,1 point | Conforme. Le statu quo suit le COR (même démographie de l'Insee, pensions indexées sur les prix). |
| Retraites (convention européenne, invalidité comprise) | Ageing Report 2024, fiche France (Trésor, décembre 2023), tableau 7 | 14,4 % (2022) ; 14,3 % (2030) ; 13,7 % (2050) ; 13,6 % (2070) | 14,1 % (2029) ; 14,3 % (2050) ; 15,3 % (2070) | +0,6 point en 2050, +1,7 en 2070 | Expliqué : l'Ageing Report 2024 suppose une fécondité de 1,8 ; le COR de juin 2026 retient 1,45 (Insee, avril 2026), comme le statu quo ; l'écart est celui de la fécondité, pas de la méthode. |
| Déficit public à politique inchangée (% du PIB) | FMI, consultation de l'article IV, 22 mai 2025 | « autour de 6 % à moyen terme » sans mesures additionnelles | 5,9 % (2029) ; 6,3 % (2030) | ≤ 0,3 point | Conforme. Le statu quo dérive ensuite (7,2 % en 2032, 8,8 % en 2035) : la charge d'intérêts monte avec la dette. |
| Dette publique (% du PIB) | FMI (scénario sans mesures, repris par la presse, avril 2026) ; IGF, « Trajectoire des finances publiques » (2025) | 124,1 % (2029, FMI) ; « plus de 130 % en 2030 » (IGF) | 128,8 % (2029) ; 132,1 % (2030) | +4,7 points contre le FMI ; dans la fourchette de l'IGF | Écart au FMI expliqué : le FMI part de la dette de 2024 (113,2 %) et de prévisions de déficit de 2025 ; le statu quo part de la loi de finances 2026 et du PLF 2027 (dette de 118,5 % fin 2026 selon la Cour des comptes, juin 2026). La pente 2026-2030 (≈ +3,5 points par an) est celle de l'IGF. |

| Charge de la dette (toutes administrations) | Cour des comptes, situation et perspectives des finances publiques, juin 2026 | « pourrait atteindre 100 milliards d'euros en 2029, soit 3 % du PIB » | 101,8 Md€ de 2026, 3,35 % du PIB (2029) | +0,35 point | Conforme (sous 0,5 point). Taux apparent de 2,7 % en 2029. |
| Chômage (BIT) | Banque de France, projections intermédiaires de septembre 2026 | 8,3 % (2026 et 2027) ; 8,0 % (2028) | 8,3 % (2029, dès l'économie de 2026 placée en 2029) ; 8,1 % en 2050 | +0,3 point en 2029 | Conforme. Le statu quo garde le chômage de 2026 (pas de reflux de 2028). |
| Santé et autonomie (ONDAM et aide sociale à l'autonomie, % du PIB) | OCDE, Panorama de la santé 2025 (moyenne des pays, scénario de référence) ; Ageing Report 2024 (dépendance, France) | santé publique : +1,5 point entre 2024 et 2045 (moyenne OCDE) ; dépendance : 1,9 % (2022) → 2,6 % (2070) | 9,9 % (2029) ; 10,3 % (2040) ; 11,1 % (2050) ; 13,6 % (2070) | ≈ +0,8 point en 16 ans jusqu'en 2045, sous la moyenne de l'OCDE ; +3,7 points à 2070 | Partiel. Jusqu'en 2045, la pente de l'assurance maladie est plus basse que la moyenne de l'OCDE ; après, la pente PROMEDE est plus forte que la seule dépendance de l'Ageing Report. Le chiffre de santé de la fiche France de l'Ageing Report n'a pas été trouvé : à recouper sur la fiche elle-même. |

## Roadmap 1.3 : dérive 2029-2036 contre la Commission européenne (21/11/2026)

Référence : Commission européenne, *Debt Sustainability Monitor 2025* (Institutional Paper 332, février 2026), fiche
France, scénario sans changement de politique. Statu quo médian, après les corrections et arbitrages du 21/11/2026
(prestations par prestation, défense en euros) et le nouveau taux apparent au rythme du refinancement
(`macro.taux_apparent_refinancement`).

| Année | Dette, Commission | Dette, modèle | Intérêts (% du PIB), Commission | Intérêts, modèle avant → après | Taux apparent, Commission | Taux apparent, modèle avant → après |
|---|---|---|---|---|---|---|
| 2029 | 124,2 | 128,5 | 3,3 | 3,35 → 3,35 | 2,8 % | 2,69 → 2,69 % |
| 2030 | 126,5 | 130,4 | 3,5 | 3,68 → 3,65 | 2,9 % | 2,91 → 2,88 % |
| 2032 | 131,7 | 134,2 | 4,1 | 4,42 → 4,22 | 3,3 % | 3,39 → 3,24 % |
| 2035 | 140,8 | 140,0 | 5,0 | 5,67 → 4,97 | 3,7 % | 4,13 → 3,65 % |
| 2036 | 144,0 | 142,0 | 5,3 | 5,82 → 5,19 | 3,9 % | 4,17 → 3,76 % |

- **Intérêts et taux apparent** : conformes depuis la correction, à 0,1 point de PIB près. Avant, le taux apparent
  rejoignait le taux long (4 %) en ligne droite en 6 ans, plus vite que le refinancement réel de la dette : +0,7 point
  de PIB d'intérêts en 2035. Désormais, chaque année, la dette échue (1/8,5, AFT) et la dette nouvelle se financent au
  taux du moment.
- **Dette** : +4 points en 2029-2030, expliqués par la convention « économie de 2026 placée en 2029 » (décision G1
  ouverte) : la Commission fait croître le PIB de 2026 à 2029, le modèle non. Écart refermé en 2035, parce que le
  solde primaire du modèle s'améliore davantage.
- **Solde primaire** : la Commission le garde à −2,1 / −2,2 % du PIB de 2026 à 2036 (structurel, coûts du
  vieillissement compris). Le modèle passe de −2,5 % (2029) à −1,7 % (2035) au médian. Écart d'environ 0,5 point en
  2035, à la limite de la tolérance. Il vient notamment des arbitrages du 21/11 (prestations revalorisées en partie
  sur les prix, défense en euros après 2030) : la Commission garde les dépenses hors vieillissement en part constante
  du PIB. Prudent : −2,1 % en 2035, en ligne.
- **Prudent** : intérêts 5,3 % du PIB en 2035 (+0,3 point sur la Commission), par la prime de dette plus forte.

## Reste à recouper (C3)

- Santé : fiche France de l'Ageing Report 2024 (dépenses de santé publiques en 2022 et 2070), DREES ; la pente
  PROMEDE de long terme est à confronter à ce chiffre.

## Sources

- COR, rapport annuel de juin 2026, partie 2, chapitre 4 : https://www.cor-retraites.fr/sites/default/files/2026-06/RA_Part2_Chap4.pdf
- Ageing Report 2024, fiche France : https://economy-finance.ec.europa.eu/document/download/e412927a-ea31-406d-bb6c-c925914123e9_en ; hypothèses comparées COR et Ageing Report (DG Trésor, novembre 2024) : https://www.cor-retraites.fr/sites/default/files/2024-11/Doc_03_Ageing_report.pdf ; COR juin 2026, synthèse (fécondité 1,45) : https://www.cor-retraites.fr/sites/default/files/2026-06/Synth%C3%A8se_RA_2026.pdf
- FMI, déclaration de fin de mission, article IV 2025 : https://www.imf.org/en/news/articles/2025/05/22/cs-france-2025
- France Épargne, reprise des projections du FMI (avril 2026) : https://www.france-epargne.fr/news/le-fmi-alerte-sur-la-montee-des-risques-budgetaires-en-france
- IGF, Trajectoire des finances publiques (2025), sommaire cité par le moteur de recherche (page redirigée, non lue en entier).
- Cour des comptes, situation et perspectives des finances publiques, juin 2026 (dette 2026) : https://www.vie-publique.fr/rapport/303867-la-situation-et-les-perspectives-des-finances-publiques-2026
- Commission européenne, Debt Sustainability Monitor 2025 (février 2026), fiche France : https://economy-finance.ec.europa.eu (Institutional Paper 332 ; copie consultée : https://www.ot.gr/wp-content/uploads/2026/02/ , fiche 10)
- Charge de la dette 2029 selon la Cour (Banque des territoires, 25/06/2026) : https://www.banquedesterritoires.fr/finances-publiques-tous-les-signaux-sont-au-rouge-en-2026-alerte-la-cour-des-comptes
- Banque de France, projections intermédiaires de septembre 2026 : https://www.banque-france.fr/fr/publications-et-statistiques/publications/projections-macroeconomiques-intermediaires-septembre-2026 ; chômage 2026-2027 (Reuters, 15/09/2026) : https://www.easybourse.com/international/news/1537735/la-banque-france-revoit-son-tour-sa-prevision-croissance-2026.html
- OCDE, Panorama de la santé 2025, projections : https://www.oecd.org/fr/publications/panorama-de-la-sante-2025_2f564c6c-fr/full-report/health-spending-projections_d3702f1a.html
- Dépendance, Ageing Report 2024 (profil France, Eurocarers) : https://eurocarers.org/country-profiles/france/
