"""Chargement et validation du fichier de paramètres unique."""
from __future__ import annotations

import copy
import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHIERS_COMMUNS = (RACINE / "parametres" / "commun" / "economie.yaml", RACINE / "parametres" / "commun" / "options.yaml",
                    RACINE / "parametres" / "commun" / "statu_quo.yaml",
                    RACINE / "parametres" / "commun" / "ecologie.yaml")
PROGRAMME_DEFAUT = "ecologie_de_droite"


def dossier_programme(programme: str = PROGRAMME_DEFAUT) -> Path:
    """Dossier d'un programme : paramètres, registre des mesures, ménages types, fiche."""
    d = RACINE / "programmes" / programme
    if not d.is_dir():
        raise FileNotFoundError(f"Programme inconnu : {programme} (pas de dossier {d})")
    return d
STATUTS = {"SOURCE", "HYPOTHESE", "DECISION"}
UNITES_MONTANT = {"eur_an", "eur_mois", "md_eur"}


class ErreurParametre(ValueError):
    pass


_ABSENT = None


class _ChargeurStrict(yaml.SafeLoader):
    """Refuse les clés en double : YAML garderait silencieusement la dernière."""


def _sans_doublon(loader, node, deep=False):
    vues = set()
    for k, _ in node.value:
        cle = loader.construct_object(k, deep=deep)
        if cle in vues:
            raise ErreurParametre(f"Clé en double dans le fichier de paramètres : {cle} (ligne {k.start_mark.line + 1})")
        vues.add(cle)
    return loader.construct_mapping(node, deep)


_ChargeurStrict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _sans_doublon)


@dataclass(frozen=True)
class Parametre:
    cle: str
    valeur: Any
    unite: str
    statut: str
    annee_euros: int | None = None
    source: str | None = None
    note: str | None = None
    par_scenario: bool = False
    v235: Any = None  # valeur de la v235 si le paramètre a été corrigé depuis (_ABSENT sinon)

    def pour(self, scenario: str) -> Any:
        """Valeur du paramètre dans un scénario (identique partout si non ventilée)."""
        if self.par_scenario:
            if scenario not in self.valeur:
                raise ErreurParametre(f"{self.cle} : pas de valeur pour le scénario {scenario}")
            return self.valeur[scenario]
        return self.valeur


# Toute instance reste en vie jusqu'à la fin du processus : plusieurs programmes mettent leurs résultats en cache
# sous id(p) ; une instance libérée laisserait Python réattribuer son id à une autre, qui lirait alors des résultats
# périmés (relecture indépendante du 11/11/2026). Le coût : quelques centaines d'instances au plus par processus.
_VIVANTES: list = []


class Parametres:
    def __init__(self, chemin: Path | str | None = None, reference: str | None = None,
                 programme: str = PROGRAMME_DEFAUT):
        """Hypothèses communes (parametres/commun/) + paramètres d'un programme (programmes/<programme>/).

        Un programme ne peut pas redéfinir une hypothèse commune : une clé présente dans deux fichiers lève une
        erreur. chemin : un fichier unique à la place (ancien format, ou fichier de test).
        reference="v235" : reprend, pour chaque paramètre corrigé depuis, la valeur de la v235 (champ v235)
        — sert aux tests de reproduction du classeur. Par défaut : valeurs actuelles (publiées)."""
        self.reference = reference
        self.programme = None if chemin else programme
        fichiers = [Path(chemin)] if chemin else [*FICHIERS_COMMUNS, dossier_programme(programme) / "parametres.yaml"]
        self.scenarios: list[str] = []
        self._p: dict[str, Parametre] = {}
        self.origine: dict[str, Path] = {}
        for f in fichiers:
            brut = yaml.load(f.read_text(encoding="utf-8"), Loader=_ChargeurStrict) or {}
            if "scenarios" in brut:
                if self.scenarios:
                    raise ErreurParametre(f"{f.name} : liste des scénarios déjà définie")
                self.scenarios = brut.pop("scenarios")
            for groupe, contenu in brut.items():
                for nom, champs in contenu.items():
                    cle = f"{groupe}.{nom}"
                    if cle in self._p:
                        raise ErreurParametre(f"{cle} défini deux fois : {self.origine[cle]} et {f}")
                    self._p[cle] = self._valider(cle, champs)
                    self.origine[cle] = f
        _VIVANTES.append(self)

    def _valider(self, cle: str, c: dict) -> Parametre:
        if getattr(self, "reference", None) == "v235" and "v235" in c:
            c = {**c, "valeur": c["v235"]}
        for champ in ("valeur", "unite", "statut"):
            if champ not in c:
                raise ErreurParametre(f"{cle} : champ « {champ} » manquant")
        if c["statut"] not in STATUTS:
            raise ErreurParametre(f"{cle} : statut inconnu {c['statut']}")
        if c["statut"] == "SOURCE" and not c.get("source"):
            raise ErreurParametre(f"{cle} : statut SOURCE sans source")
        if c["unite"] in UNITES_MONTANT and "annee_euros" not in c:
            raise ErreurParametre(f"{cle} : montant sans année des euros")
        # Ventilé par scénario si toutes les clés sont des scénarios ; un dictionnaire qui mêle
        # scénarios et autres champs est une valeur structurée, lue par le module qui l'utilise.
        par_scenario = isinstance(c["valeur"], dict) and bool(c["valeur"]) and set(c["valeur"]) <= set(self.scenarios)
        if par_scenario and set(c["valeur"]) != set(self.scenarios):
            raise ErreurParametre(f"{cle} : scénarios incomplets {sorted(c['valeur'])}")
        return Parametre(
            cle=cle, valeur=c["valeur"], unite=c["unite"], statut=c["statut"],
            annee_euros=c.get("annee_euros"), source=c.get("source"),
            note=" | ".join(x for x in (c.get("note"), ("Note de la v235 : " + c["note_v235"]) if c.get("note_v235") else None) if x) or None,
            par_scenario=par_scenario, v235=c.get("v235", _ABSENT),
        )

    # Colonne lue quand un module demande le prudent : « crise » pour le calcul du scénario de crise.
    colonne_prudent: str = "prudent"
    _surcharges: dict = {}
    taux_local_copie: float | None = None
    mesures_desactivees: frozenset = frozenset()

    def __getitem__(self, cle: str) -> Parametre:
        return self._p[cle]

    def val(self, cle: str, scenario: str = "prudent") -> Any:
        if cle in self._surcharges:
            return self._surcharges[cle]
        if scenario == "depart":  # colonne prudente, même dans le calcul de crise (point de départ commun)
            scenario = "prudent"
        elif scenario == "prudent":
            scenario = self.colonne_prudent
        return self._p[cle].pour(scenario)

    def en_crise(self, comme_v235: bool = False) -> "Parametres":
        """Copie pour le calcul de crise : la v235 recopie les valeurs de crise dans la colonne prudente,
        recalcule, puis lit le bloc prudent. On fait de même, sans toucher au fichier de paramètres.

        comme_v235 : reproduit aussi le défaut de la v235, dont les feuilles de salariés gardent le taux
        d'impôt local recopié à la main (Collectivités!B91, point fixe du prudent) au lieu de le recalculer ;
        sert au test de reproduction. Par défaut, le point fixe est recalculé avec les paramètres de crise.
        """
        c = copy.copy(self)
        c.__dict__.pop("_cache", None)
        c.__dict__.pop("_taux_local_force", None)
        c.colonne_prudent = "crise"
        c._surcharges = {"transition.decote_participations": self.val("crise.decote_participations")}
        if comme_v235:
            c.taux_local_copie = self.val("impot_local.taux_point_fixe")
        _VIVANTES.append(c)
        return c

    def en_scenario(self, scenario: str) -> "Parametres":
        """Copie dont la colonne prudente lit le scénario donné (médian ou optimiste), comme en_crise pour la crise :
        un moteur écrit pour le prudent calcule alors tout ce scénario (phase A7 de la roadmap, 13/11/2026, registre
        d'Écologie de droite par scénario). La colonne « depart » reste le prudent."""
        if scenario == "prudent":
            return self
        if scenario == "crise":
            return self.en_crise()
        c = copy.copy(self)
        c.__dict__.pop("_cache", None)
        c.__dict__.pop("_taux_local_force", None)
        c.colonne_prudent = scenario
        c._surcharges = dict(self._surcharges)
        _VIVANTES.append(c)
        return c

    def __iter__(self):
        return iter(self._p.values())

    def avec(self, modifs: dict[str, Any] | None = None, mesures_desactivees: set[str] | frozenset = frozenset()) -> "Parametres":
        """Copie avec des valeurs remplacées, pour les variantes et l'attribution par mesure.

        modifs : {"groupe.nom": valeur} ou {"groupe.nom/sous/chemin": valeur} pour une valeur structurée.
        Un paramètre par scénario reçoit la même valeur dans tous les scénarios (sauf chemin explicite).
        mesures_desactivees : libellés du registre des économies (mesures_economies.csv) à neutraliser.
        """
        c = copy.copy(self)
        c.__dict__.pop("_cache", None)
        c.__dict__.pop("_taux_local_force", None)
        c._p = dict(self._p)
        for cle_chemin, v in (modifs or {}).items():
            cle, *chemin = cle_chemin.split("/")
            if cle not in c._p:
                raise ErreurParametre(f"Paramètre inconnu : {cle}")
            par = c._p[cle]
            if not chemin:
                nouvelle = {s: v for s in self.scenarios} if par.par_scenario else v
            else:
                nouvelle = copy.deepcopy(par.valeur)
                cibles = [nouvelle[s] for s in self.scenarios] if par.par_scenario and chemin[0] not in self.scenarios else [nouvelle]
                for cible in cibles:
                    for k in chemin[:-1]:
                        cible = cible[k]
                    if chemin[-1] not in cible:
                        raise ErreurParametre(f"{cle} : pas de champ {'/'.join(chemin)}")
                    cible[chemin[-1]] = v
            c._p[cle] = dataclasses.replace(par, valeur=nouvelle)
        c.mesures_desactivees = frozenset(self.mesures_desactivees) | frozenset(mesures_desactivees)
        _VIVANTES.append(c)
        return c
