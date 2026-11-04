"""Découpe du fichier de paramètres unique en trois fichiers (4 novembre 2026), utilisé une seule fois.

    python -m outils.decouper_parametres

- parametres/commun/options.yaml : options du modèle (unités, interrupteurs de modules, corrections) ;
- parametres/commun/economie.yaml : hypothèses et données communes à tous les programmes ;
- programmes/ecologie_de_droite/parametres.yaml : mesures du programme et hypothèses propres à ses mesures.

Le texte est découpé tel quel (commentaires et notes gardés). Règle de classement : voir PORTEE ci-dessous et
docs/architecture.md. Première passe : les hypothèses propres aux mesures du programme restent du côté du
programme ; elles iront dans la bibliothèque de mesures quand la mesure y sera codée de façon générique.
"""
from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "parametres" / "parametres.yaml"

# Groupes entièrement propres au programme « Écologie de droite ».
GROUPES_PROGRAMME = {
    "impot_unique", "rui", "rui_complements", "epargne", "retraites", "capital", "impot_local",
    "impot_local_entreprises", "fonds", "fonds_reprises", "clause", "objectifs", "transition", "penibilite",
    "revalorisation", "quotient", "economies_missions", "budget_statique", "famille", "carrieres", "ascenseur",
    "education", "environnement", "ia", "tva", "tva_sante_long_terme", "carbone_importe", "logement",
    "logement_dynamique", "etudiants_rui", "securite_sociale", "crise", "collectivites", "alignement",
}

# Décisions qui sont des choix de modélisation (communs), pas des mesures.
OPTIONS = {
    "unites.annee_modele", "unites.annee_bascule", "systeme_actuel.source", "entreprises.localisation_taux_effectif",
    "macro.depart_commun", "macro.seniors_lies_aux_reportes", "macro.permis_rapide_separe",
    "macro.corrections_relecture", "macro.impots_par_revenu", "chomage.dynamique", "emploi.gain_par_canal",
    "emploi.retenues_calculees", "is_investissement.assiette_locale", "demographie.active",
    "ancien_systeme.par_generation", "cohortes.active", "carrieres.active", "entreprises_cellules.active",
    "inflation.active", "ministeres.par_public", "sante_trajectoire.derive_prise_en_compte",
}

# Décisions qui sont des hypothèses économiques communes (choix entre sources), pas des mesures.
DECISIONS_COMMUNES = {
    "calendrier.inflation", "demographie.scenario_fecondite", "sante_trajectoire.pente_phase_1",
    "macro.annees_effet_ajustement",
}

# Hypothèses ou sources rangées dans un groupe commun, mais qui décrivent l'effet d'une mesure du programme.
HYPOTHESES_PROGRAMME = {
    "emploi.reformes_directes", "emploi.bas_salaires_rui_prorata", "emploi.prime_jeunes",
    "emploi.subventions_supprimees", "emploi.commerces", "emploi.accords_branche", "emploi.aide_personne",
    "emploi.assistantes_maternelles", "emploi.creches", "emploi.gain_par_emploi",
    "macro.seniors_part_emploi_reportes", "macro.seniors_court", "macro.montee_seniors_court", "macro.seniors_long",
    "macro.annee_seniors_long", "macro.montee_seniors_long", "macro.logements_initial", "macro.duree_initiale",
    "macro.logements_croisiere", "macro.part_additionnelle_logement", "macro.permis_rapide_cout",
    "macro.permis_rapide", "macro.cumul_emploi_socle", "macro.annee_cumul", "macro.montee_cumul",
    "macro.niveau_eleves", "macro.premiere_annee_ecole", "macro.annees_ecole", "macro.part_reinvestie",
    "macro.effort_2029", "macro.baisse_spread", "macro.annees_baisse_spread", "macro.fraude_tva",
    "macro.montee_fraude", "macro.extinction_aides_construction", "macro.aides_construction",
    "macro.part_capital_nouveau", "macro.usure_capital_fonds", "macro.externalites_capital_fonds",
    "macro.productivite", "macro.annees_productivite", "macro.premiere_annee_productivite", "macro.adoption_ia",
    "macro.reduction_cout_capital_autres", "macro.montee_erosion_is", "macro.etranger", "macro.cible_dette",
    "hauts_revenus.regle_nordique", "hauts_revenus.part_par_societe", "hauts_revenus.montee",
    "entreprises_cellules.repartition_fonds", "entreprises_cellules.plafond_part_capital",
    "entreprises_cellules.cout_financement_marche", "is_investissement.categories",
    "is_investissement.part_investissement_concernee", "collectivites_detail.meme_doctrine",
    "collectivites_detail.part_agents_gestion", "collectivites_detail.charges_fixes", "sante.mesures_a_terme",
    "sante_trajectoire.montee_mesures", "sante_trajectoire.hopitaux_administratifs",
    "sante_trajectoire.forfait_generalistes", "sante_trajectoire.options", "budget_etat.part_eleves_retour_public",
    "budget_etat.apprentissage", "inactifs.revenu_annulant_rui", "inactifs.rui_moyen_chomeurs",
    "inactifs.part_chomeurs_deja_comptee", "independants.salaire_pivot", "independants.seuil_retention",
    "independants.correction_couples", "calendrier.mesures_2028", "carbone.part_accise_prix_final",
}


def portee(cle: str, statut: str) -> str:
    groupe = cle.split(".")[0]
    if cle in OPTIONS:
        return "options"
    if cle in DECISIONS_COMMUNES:
        return "economie"
    if groupe in GROUPES_PROGRAMME or cle in HYPOTHESES_PROGRAMME or statut == "DECISION":
        return "programme"
    return "economie"


ENTETES = {
    "options": "# Options du modèle, communes à tous les programmes : unités, modules activés, corrections de méthode.\n"
               "# Un programme ne peut pas les redéfinir (moteur/parametres.py).\n",
    "economie": "# Hypothèses et données communes à tous les programmes (économie, démographie, système actuel,\n"
                "# comportements). Un programme ne peut pas les redéfinir (moteur/parametres.py).\n"
                "#\n# Chaque paramètre porte : valeur (nombre ou dictionnaire par scénario), unite, annee_euros\n"
                "# (montants), statut (SOURCE, HYPOTHESE, DECISION), source (obligatoire si SOURCE), note.\n"
                "# Règle : une valeur sans source est prise prudente. Le scénario prudent est publié.\n",
    "programme": "# Programme « Écologie de droite » : mesures et hypothèses propres à ses mesures.\n"
                 "# Les hypothèses communes sont dans parametres/commun/ ; ce fichier ne peut pas les redéfinir.\n",
}


def decouper(texte: str) -> dict[str, str]:
    lignes = texte.splitlines(keepends=True)
    sorties = {k: [ENTETES[k], "\n"] for k in ENTETES}
    i = 0
    # En-tête et scénarios : la liste des scénarios va dans economie.yaml.
    while not re.match(r"^scenarios:", lignes[i]):
        i += 1
    sorties["economie"].append(lignes[i] + "\n")
    i += 1
    commentaire_groupe: list[str] = []
    groupe = None
    blocs: list[tuple[str, str, list[str], list[str]]] = []  # (groupe, cle, commentaire_groupe, lignes)
    attente: list[str] = []
    courant = None
    while i < len(lignes):
        l = lignes[i]
        if re.match(r"^[a-z_0-9]+:\s*$", l):
            groupe = l.split(":")[0]
            commentaire_groupe = [x for x in attente]
            attente = []
            courant = None
        elif re.match(r"^  [a-z_0-9]+:", l):
            nom = l.strip().split(":")[0]
            courant = [*attente, l]
            attente = []
            blocs.append((groupe, nom, commentaire_groupe, courant))
        elif l.startswith("#") or l.startswith("  #") or not l.strip():
            attente.append(l)
        else:
            if courant is None:
                raise ValueError(f"Ligne hors paramètre {i + 1} : {l!r}")
            if any(x.strip() for x in attente):
                raise ValueError(f"Commentaire au milieu d'un paramètre, ligne {i + 1}")
            courant.extend(attente)
            attente = []
            courant.append(l)
        i += 1
    # Statuts lus dans le texte de chaque bloc.
    groupe_ouvert = {k: None for k in sorties}
    for groupe, nom, com, bloc in blocs:
        m = re.search(r"\bstatut:\s*(\w+)", "".join(bloc))
        if not m:
            raise ValueError(f"{groupe}.{nom} : statut introuvable")
        dest = portee(f"{groupe}.{nom}", m.group(1))
        if groupe_ouvert[dest] != groupe:
            sorties[dest].extend(["\n", *[c for c in com if c.strip()], f"{groupe}:\n"])
            groupe_ouvert[dest] = groupe
        while bloc and not bloc[-1].strip():
            bloc = bloc[:-1]
        sorties[dest].extend(bloc)
    return {k: "".join(v) for k, v in sorties.items()}


def main():
    res = decouper(SOURCE.read_text(encoding="utf-8"))
    (RACINE / "parametres" / "commun").mkdir(exist_ok=True)
    (RACINE / "programmes" / "ecologie_de_droite").mkdir(parents=True, exist_ok=True)
    (RACINE / "parametres" / "commun" / "options.yaml").write_text(res["options"], encoding="utf-8")
    (RACINE / "parametres" / "commun" / "economie.yaml").write_text(res["economie"], encoding="utf-8")
    (RACINE / "programmes" / "ecologie_de_droite" / "parametres.yaml").write_text(res["programme"], encoding="utf-8")


if __name__ == "__main__":
    main()
