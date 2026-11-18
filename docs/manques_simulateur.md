# Ce qui manque au simulateur pour juger un programme en entier (18 novembre 2026)

Constat tiré du « Programme IA » (`docs/programme_ia.md`, branche `test/programme-ia`). Quand on optimise le
programme sur le comparateur, toutes les dépenses d'avenir sortent une à une : enseignants, crèches, accès aux
soins, justice. Elles ne font que coûter d'ici 2037. Ce fichier liste ce que le modèle ne mesure pas encore, et
pour chaque manque : ce qui existe déjà, ce qu'il faudrait ajouter, et avec quelles sources.

Les manques sont classés par **effet sur le classement** : en premier, ceux qui pénalisent aujourd'hui un type de
mesure pour tous les programmes.

## Correction d'abord : ce que le modèle compte déjà

La version 3 de `programme_ia.md` dit que le modèle « ne compte aucun effet des enseignants, des crèches ». C'est
inexact. Vérifié sur la version 2 :

| Canal existant | Ce qu'il donne pour le Programme IA | Pourquoi on ne le voit pas |
|---|---|---|
| **Éducation** (`instrument: education`, `docs/offre.md`) | Revalorisation des enseignants : −0,001 point de déficit en 2037, −0,009 en 2050, −0,06 en 2073 (prudent) | Effet par les salaires futurs des élèves : presque nul avant 2040 |
| **Naissances** (`moteur/naissances.py`) | Crèches : naissances +1,2 % ; recettes +9,5 Md€ en 2073, mais coûts (école, santé, prestations) presque aussi élevés | Gain d'abord négatif, à peine positif en 2073 |
| **Prime de risque sur la dette** (`macro.baisse_spread`) | Nulle en crise et en prudent | Un programme sérieux n'est pas récompensé en prudent |

Ces canaux existent donc. Le vrai manque est ailleurs : ce sont **les effets de court et moyen terme** (avant 2040)
et **les domaines sans aucun canal**.

---

## 1. Santé : aucun canal

**Aujourd'hui** : une dépense de santé (accès aux soins, prévention) n'est qu'un coût. La taxe sur les boissons
sucrées n'est comptée que comme une recette, sans effet sur la santé.

**Ce qui manque :**
- effet de l'accès aux soins sur l'**emploi** : arrêts maladie, invalidité, sorties précoces du travail ;
- effet de la **prévention** sur les dépenses futures (obésité, diabète, maladies liées à l'alcool et au tabac) ;
- effet des **taxes comportementales** sur la consommation, puis sur la santé (le canal prix existe pour le carbone,
  pas pour la santé).

**Sources possibles** : évaluations de la taxe soda britannique (Soft Drinks Industry Levy, 2018) et de la taxe
française de 2012 et 2018 ; Drees et Assurance maladie (charges et produits) pour le coût des pathologies ; Dares
pour les sorties d'emploi pour raison de santé.

**Prudence** : les économies de la prévention sont souvent surestimées (on vit plus longtemps, donc on coûte
ailleurs). Un prudent proche de zéro est défendable, comme pour le canal école.

## 2. Petite enfance : l'emploi des mères manque

**Aujourd'hui** : une place de crèche passe par le canal naissances. Rien sur le **travail des parents**, alors que
c'est l'effet le plus documenté et le plus rapide.

**Ce qui manque :**
- canal **offre de travail des mères** : heures travaillées et taux d'emploi en plus par place créée, donc des
  cotisations et des impôts dès la première année ;
- effet sur le **développement de l'enfant** (langage, réussite scolaire), à brancher sur le canal école existant.

**Sources possibles** : Cnaf et Onape (taux de recours, effet sur l'activité des mères) ; Insee (activité selon
l'âge du plus jeune enfant) ; études sur les réformes de garde en Norvège et au Québec, avec des effets contrastés
selon le pays ; pour le développement, les programmes préscolaires américains (Perry, Abecedarian), à prendre avec
précaution hors de leur contexte.

**Base déjà là** : la microsimulation corrige déjà l'emploi selon la configuration familiale (Insee 2024) ; il
faudrait faire dépendre cette correction de l'offre de garde.

## 3. Éducation : seulement le très long terme

**Aujourd'hui** : le canal passe par la **dépense par élève** et le salaire futur des élèves. Il ne joue qu'à partir
de 2040. Le canal `ecole` (niveau des élèves en écart-type) est libre : chaque programme déclare son effet, sans
barème qui relie une mesure à un gain.

**Ce qui manque :**
- **barème commun** mesure → niveau des élèves (taille des classes, formation des enseignants, temps
  d'enseignement), pour que le canal `ecole` ne dépende plus d'une déclaration ;
- effets de **moyen terme** : décrochage, insertion des jeunes, emplois non pourvus ;
- **attractivité du métier** : postes non pourvus aux concours, contractuels, qualité de l'enseignement. La
  revalorisation du Programme IA visait cela, mais sans canal pour le compter.

**Sources possibles** : DEPP (évaluations nationales, effet des dédoublements de CP et de CE1) ; Jackson et
Mackevicius (2024) déjà cité ; Cour des comptes sur l'attractivité du métier ; Céreq pour l'insertion.

## 4. Justice et sécurité : aucun canal

**Aujourd'hui** : greffiers, magistrats et policiers ne sont qu'un coût. Le Programme IA les a retirés pour cette
seule raison.

**Ce qui manque :**
- **délais de justice** → vie des entreprises (contentieux commerciaux, recouvrement des créances, défaillances) ;
- **sécurité** → activité locale, coût de la délinquance pour les victimes et l'assurance.

**Sources possibles** : CEPEJ (Conseil de l'Europe) pour les délais comparés ; travaux de l'OCDE sur l'efficacité
judiciaire et l'investissement ; ministère de la Justice pour les stocks d'affaires.

**Prudence** : les preuves sont plus fragiles que pour l'éducation. Un prudent à zéro est probable ; l'intérêt est
surtout d'afficher le médian.

## 5. Faisabilité : tout est supposé voté et appliqué

**Aujourd'hui** : une mesure déclarée est appliquée à 100 % à la date prévue. La règle de dépense (30 Md€ annoncés)
passe par l'enveloppe, mais rien ne dit si elle tiendra cinq ans.

**Ce qui manque :**
- une **probabilité d'application** par mesure : besoin d'une loi, d'une révision de la Constitution, d'un accord
  européen, d'une majorité ;
- un **historique d'exécution** : comment les règles de dépense passées (lois de programmation des finances
  publiques) ont été tenues ;
- les **délais** : décrets, contentieux, montée en charge réelle (le leasing social, par exemple, s'arrête quand
  l'enveloppe est vide).

**Sources possibles** : Haut Conseil des finances publiques et Cour des comptes (écarts entre programmation et
exécution) ; historique des lois de programmation depuis 2012.

## 6. Acceptabilité et popularité : rien

**Aujourd'hui** : le comparateur mesure ce que coûte et rapporte une mesure, pas qui la soutient. La
sous-indexation des pensions et l'âge légal à 65 ans pèsent lourd dans le score, sans signal sur leur coût
politique.

**Ce qui manque** : un indicateur séparé, **hors du solde**, par mesure : soutien dans les sondages publics, groupes
touchés (le nombre de perdants et de gagnants vient de la microsimulation).

**Prudence** : à ne jamais mélanger au chiffrage. C'est une colonne d'information, pas un correctif du déficit.

## 7. Redistribution : prévue, mais pas pour toutes les mesures

**Aujourd'hui** : la microsimulation (OpenFisca, `docs/microsimulation.md`) répartit les grosses mesures par décile.
Les mesures « simples » (comme la plupart de celles du Programme IA) passent par une incidence approximative
(`haut`, proportionnelle). Dans l'environnement de cette conversation, OpenFisca n'était pas installé : aucun effet
par décile n'a été calculé pour le Programme IA.

**Ce qui manque :**
- un branchement OpenFisca pour la **sous-indexation des pensions** au-dessus d'un seuil (déciles de pensions de la
  Drees déjà présents) et pour les **successions** ;
- les **familles monoparentales**, absentes des cas types (`docs/offre.md`, limite 2).

## 8. IA et numérique : seulement le privé

**Aujourd'hui** : le canal `adoption_ia` donne un gain de productivité au privé. Le plan IA du Programme IA a été
retiré : 1,1 Md€ de coût pour +0,2 Md€ au solde en 2037 (prudent).

**Ce qui manque** : un canal **productivité des administrations** (temps d'agent économisé, délais de traitement,
fraude détectée), qui donnerait une économie de fonctionnement et pas seulement du PIB.

**Sources possibles** : retours d'expérience de la DINUM et de la DGFiP (ciblage des contrôles par les données) ;
évaluations de l'OCDE sur l'IA dans le secteur public.

## 9. Logement : l'offre, pas la mobilité

**Aujourd'hui** : le canal `logement` compte les logements construits en plus. La bascule des droits de mutation
vers la taxe foncière (mesure 10) n'a pas été chiffrée.

**Ce qui manque** : un canal **mobilité résidentielle** (droits de mutation → déménagements → emploi, la mobilité
vers les bassins d'emploi) et un effet sur les **loyers**, donc sur le pouvoir d'achat.

**Sources possibles** : travaux du CAE et de l'OCDE sur les droits de mutation ; Insee pour les mobilités.

## 10. Écologie : des secteurs encore hors champ

Déjà documenté dans `docs/ecologie.md` (limites) : puits de carbone et sols, industrie face à un prix national,
biodiversité, intensité commune à tous les secteurs. À cela s'ajoute : la population utilisée pour les émissions par
habitant est celle du statu quo, sans l'effet des naissances du programme.

---

## Priorités proposées

| Rang | Manque | Pourquoi d'abord | Difficulté |
|---|---|---|---|
| 1 | Petite enfance → emploi des mères | Effet rapide, bien documenté, touche beaucoup de programmes | Moyenne : la base familiale de la microsimulation existe |
| 2 | Santé → emploi et taxes comportementales | Aucun canal aujourd'hui ; plusieurs programmes ont des mesures de santé | Moyenne à forte |
| 3 | Barème commun pour le canal `ecole` | Le canal existe mais dépend d'une déclaration libre | Moyenne |
| 4 | Faisabilité (probabilité d'application) | Change la lecture de tous les programmes, surtout les économies non détaillées | Forte : demande des choix de méthode |
| 5 | Redistribution des mesures simples | Indispensable pour juger qui paie | Faible : OpenFisca est déjà branché |
| 6 | Productivité des administrations (IA) | Utile, mais preuves encore minces | Moyenne |
| 7 | Justice, mobilité, acceptabilité | Preuves fragiles ou indicateur hors solde | Variable |

Règle à garder pour chaque ajout : **un barème commun, appliqué à tous les programmes**, comme pour l'offre de
logements ou les réformes de structure. Sinon, le comparateur récompenserait celui qui déclare le plus gros effet.

## À corriger dans `programme_ia.md`

La phrase « il ne compte aucun effet des enseignants, des crèches ou de l'accès aux soins » doit devenir : il compte
l'effet des enseignants (après 2040) et des crèches sur les naissances, mais rien sur l'emploi des mères ni sur la
santé, et rien avant 2040 pour l'école.
