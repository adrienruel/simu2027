"""Le nouveau système codé comme une réforme d'OpenFisca-France.

La réforme ajoute, à partir du coût employeur calculé par OpenFisca (le même qu'aujourd'hui : la bascule
garde le coût du travail et change ce que le salarié en garde) :
- impot_unique (foyer fiscal) : barème sur le coût employeur, couples imposés ensemble, demi-part par enfant
  plafonnée ;
- impot_local_actif (individu) : au-delà de l'abattement, au taux moyen du point fixe du moteur ;
- rui_actif (individu) : RUI au prorata du coût employeur ;
- rui_famille (famille) : RUI des adultes sans revenu (règle du conjoint), compléments par enfant ;
- epargne_obligatoire (individu) ;
- revenu_disponible_nouveau (ménage).

Toutes les valeurs viennent du fichier de paramètres du moteur (une seule source). Le test
tests/test_openfisca_reforme.py vérifie que la réforme et le moteur donnent le même résultat sur les ménages
types : deux écritures indépendantes des mêmes règles.
"""
from __future__ import annotations

import numpy as np


def construire(tbs, p, scenario: str = "prudent"):
    from openfisca_core.model_api import ADD, MONTH, YEAR, Reform, Variable, max_
    from openfisca_france.entities import Famille, FoyerFiscal, Individu, Menage

    from moteur.collectivites import taux_impot_local
    from moteur.epargne import taux_epargne
    from moteur.impot_unique import bareme

    seuils, taux = bareme(p, scenario)
    bornes = np.array([0.0, *seuils])
    taux_ = np.array(taux)
    rui = p.val("rui.montant") * 12
    smic = p.val("epargne.cout_smic_mensuel") * 12
    abattement = p.val("impot_local.abattement")
    t_local = taux_impot_local(p, salaries=True)
    plafond = p.val("quotient.plafond_demi_part")
    parts_enfant = p.val("quotient.parts_par_enfant")
    part_enfant = p.val("rui_complements.part_enfant")
    part_enfant_isole = p.val("rui_complements.part_enfant_parent_isole")
    part_rang3 = max(part_enfant, p.val("rui_complements.part_enfant_rang3"))

    def bareme_vect(x):
        x = np.asarray(x, dtype=float)
        hauts = np.append(bornes[1:], np.inf)
        tranches = np.clip(x[:, None] - bornes[None, :], 0, hauts - bornes)
        return (tranches * taux_).sum(axis=1)

    def taux_epargne_vect(c):
        return np.array([taux_epargne(x, p) for x in np.asarray(c, dtype=float)])

    class cout_employeur_annuel(Variable):
        value_type = float
        entity = Individu
        definition_period = YEAR
        label = "Coût employeur annuel (base de l'impôt unique)"

        def formula(individu, period):
            return individu("cout_du_travail", period, options=[ADD])

    class base_impot_unique(Variable):
        value_type = float
        entity = Individu
        definition_period = YEAR
        label = "Base de l'impôt unique : coût employeur, plus la pension brute des retraités de l'ancien système"

        def formula(individu, period):
            return individu("cout_employeur_annuel", period) + individu("retraite_brute", period, options=[ADD])

    class rui_actif(Variable):
        value_type = float
        entity = Individu
        definition_period = YEAR
        label = "RUI gardé par un actif, au prorata de son coût employeur"

        def formula(individu, period):
            c = individu("cout_employeur_annuel", period)
            return (c > 0) * max_(0, 1 - c / smic) * rui

    class impot_unique(Variable):
        value_type = float
        entity = FoyerFiscal
        definition_period = YEAR
        label = "Impôt unique du foyer (coût employeur, imposition commune, quotient familial plafonné)"

        def formula(foyer, period):
            r = foyer.sum(foyer.members("base_impot_unique", period), role=FoyerFiscal.DECLARANT)
            p0 = foyer.nb_persons(FoyerFiscal.DECLARANT).astype(float)
            n = foyer.nb_persons(FoyerFiscal.PERSONNE_A_CHARGE).astype(float)
            parts = p0 + parts_enfant * n
            sans = p0 * bareme_vect(r / p0)
            avec = parts * bareme_vect(r / parts)
            return np.where(n > 0, np.maximum(avec, sans - plafond * n * parts_enfant / 0.5), sans)

    class impot_local_actif(Variable):
        value_type = float
        entity = Individu
        definition_period = YEAR
        label = "Impôt local sur le revenu d'activité (taux moyen)"

        def formula(individu, period):
            return max_(0, individu("cout_employeur_annuel", period) - abattement) * t_local

    class epargne_obligatoire(Variable):
        value_type = float
        entity = Individu
        definition_period = YEAR
        label = "Épargne obligatoire versée sur le compte (sur le net après impôt individuel)"

        def formula(individu, period):
            c = individu("cout_employeur_annuel", period)
            net = c - bareme_vect(c) + individu("rui_actif", period)
            return (c > 0) * taux_epargne_vect(c) * net

    class rui_famille(Variable):
        value_type = float
        entity = Famille
        definition_period = YEAR
        label = "RUI des adultes sans revenu et compléments par enfant"

        def formula(famille, period):
            b = famille.members("base_impot_unique", period)
            parents = famille.nb_persons(Famille.PARENT)
            enfants = famille.nb_persons(Famille.ENFANT).astype(float)
            inactifs = famille.sum(b <= 0, role=Famille.PARENT)
            foyer_imp = famille.demandeur.foyer_fiscal("impot_unique", period)
            net = (famille.sum(b, role=Famille.PARENT) - foyer_imp
                   - famille.sum(famille.members("impot_local_actif", period), role=Famille.PARENT)
                   + famille.sum(famille.members("rui_actif", period), role=Famille.PARENT))
            # seul et sans revenu : RUI plein ; en couple : RUI du conjoint sans revenu réduit selon le revenu du couple
            seul = (parents == 1) * (inactifs >= 1) * rui
            couple = (parents == 2) * (inactifs == 1) * rui * max_(0, 1 - (net / 2) / (2 * rui))
            couple_deux = (parents == 2) * (inactifs == 2) * 2 * rui
            parts = np.where(parents == 1, enfants * part_enfant_isole,
                             np.minimum(enfants, 2) * part_enfant + np.maximum(enfants - 2, 0) * part_rang3)
            return seul + couple + couple_deux + parts * rui

    class revenu_disponible_nouveau(Variable):
        value_type = float
        entity = Menage
        definition_period = YEAR
        label = "Revenu disponible dans le nouveau système (épargne obligatoire déduite)"

        def formula(menage, period):
            c = menage.sum(menage.members("base_impot_unique", period))
            local = menage.sum(menage.members("impot_local_actif", period))
            rui_a = menage.sum(menage.members("rui_actif", period))
            ep = menage.sum(menage.members("epargne_obligatoire", period))
            imp = menage.sum(menage.members.foyer_fiscal("impot_unique", period), role=Menage.PERSONNE_DE_REFERENCE)
            fam = menage.sum(menage.members.famille("rui_famille", period), role=Menage.PERSONNE_DE_REFERENCE)
            return c - imp - local + rui_a + fam - ep

    class ReformeNouveauSysteme(Reform):
        name = "Nouveau système (impôt unique, RUI, impôt local, épargne obligatoire)"

        def apply(self):
            for v in (cout_employeur_annuel, base_impot_unique, rui_actif, impot_unique, impot_local_actif, epargne_obligatoire,
                      rui_famille, revenu_disponible_nouveau):
                self.add_variable(v)

    _ = MONTH
    return ReformeNouveauSysteme(tbs)
