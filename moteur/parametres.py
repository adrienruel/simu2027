"""Chargement et validation du fichier de paramètres unique."""
from __future__ import annotations

import copy
import dataclasses
import itertools
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHIERS_COMMUNS = (RACINE / "parametres" / "commun" / "economie.yaml", RACINE / "parametres" / "commun" / "options.yaml",
                    RACINE / "parametres" / "commun" / "statu_quo.yaml",
                    RACINE / "parametres" / "commun" / "ecologie.yaml",
                    RACINE / "parametres" / "commun" / "microsimulation.yaml")


def dossier_programme(programme: str) -> Path:
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


class _ChargeurStrict(getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
    """Refuse les clés en double : YAML garderait silencieusement la dernière. Analyseur en C (libyaml) quand PyYAML
    l'a, 12 fois plus rapide ; sinon le même en Python (roadmap du moteur 25/11/2026, R1.1)."""


def _sans_doublon(loader, node, deep=False):
    vues = set()
    for k, _ in node.value:
        cle = loader.construct_object(k, deep=deep)
        if cle in vues:
            raise ErreurParametre(f"Clé en double dans le fichier de paramètres : {cle} (ligne {k.start_mark.line + 1})")
        vues.add(cle)
    return loader.construct_mapping(node, deep)


_ChargeurStrict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _sans_doublon)

# Fichiers déjà analysés (R1.2) : chemin → (texte, YAML brut en pickle). Chaque Parametres() reçoit une copie neuve
# (pickle.loads, ≈ 0,6 ms) au lieu d'une nouvelle analyse (≈ 120 ms en Python). La clé est le texte lu : un fichier
# modifié, même dans la même seconde et à la même taille, est analysé à nouveau.
_LUS: dict[Path, tuple[str, bytes]] = {}


def _lire_yaml(f: Path) -> dict:
    texte = f.read_text(encoding="utf-8")
    deja = _LUS.get(f)
    if deja is not None and deja[0] == texte:
        return pickle.loads(deja[1])
    brut = yaml.load(texte, Loader=_ChargeurStrict) or {}
    _LUS[f] = (texte, pickle.dumps(brut, protocol=pickle.HIGHEST_PROTOCOL))
    return brut


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
    # source vérifiable (phase 3.4, 16/11/2026) : adresse du document et page, tableau ou cellule où lire la valeur
    url: str | None = None
    page: str | None = None

    def pour(self, scenario: str) -> Any:
        """Valeur du paramètre dans un scénario (identique partout si non ventilée)."""
        if self.par_scenario:
            if scenario not in self.valeur:
                raise ErreurParametre(f"{self.cle} : pas de valeur pour le scénario {scenario}")
            return self.valeur[scenario]
        return self.valeur


# Jeton propre à chaque instance (R1.4, 25/11/2026). Les programmes rangent des résultats sous (p.jeton, scénario).
# Avant : sous l'adresse de l'objet, avec toutes les instances gardées en vie pour que Python ne la réattribue pas à
# une autre instance, qui aurait lu des résultats périmés (relecture du 11/11/2026). Un jeton ne revient jamais : les
# instances peuvent être libérées.
_JETONS = itertools.count(1)


class Parametres:
    def __init__(self, chemin: Path | str | None = None, programme: str | None = None):
        """Hypothèses communes (parametres/commun/) + paramètres d'un programme (programmes/<programme>/).

        Un programme ne peut pas redéfinir une hypothèse commune : une clé présente dans deux fichiers lève une
        erreur. chemin : un fichier unique à la place (fichier de test)."""
        self.programme = None if chemin else programme
        if chemin:
            fichiers = [Path(chemin)]
        elif programme in (None, "statu_quo", "vide"):
            self.programme = None
            fichiers = list(FICHIERS_COMMUNS)
        else:
            fichiers = [*FICHIERS_COMMUNS, dossier_programme(programme) / "parametres.yaml"]
        self.scenarios: list[str] = []
        self._p: dict[str, Parametre] = {}
        self.origine: dict[str, Path] = {}
        for f in fichiers:
            brut = _lire_yaml(Path(f).resolve())
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
        self.jeton = next(_JETONS)

    def _valider(self, cle: str, c: dict) -> Parametre:
        for champ in ("valeur", "unite", "statut"):
            if champ not in c:
                raise ErreurParametre(f"{cle} : champ « {champ} » manquant")
        if c["statut"] not in STATUTS:
            raise ErreurParametre(f"{cle} : statut inconnu {c['statut']}")
        if c["statut"] == "SOURCE" and not c.get("source"):
            raise ErreurParametre(f"{cle} : statut SOURCE sans source")
        if c.get("url") is not None and not str(c["url"]).startswith(("https://", "http://")):
            raise ErreurParametre(f"{cle} : url sans http(s) : {c['url']}")
        if c.get("url") and c["statut"] != "SOURCE":
            raise ErreurParametre(f"{cle} : url sur un paramètre au statut {c['statut']} (réservée au statut SOURCE)")
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
            par_scenario=par_scenario,
            url=c.get("url"), page=(str(c["page"]) if c.get("page") is not None else None),
        )

    # Colonne lue quand un module demande le prudent : « crise » pour le calcul du scénario de crise.
    colonne_prudent: str = "prudent"
    mesures_desactivees: frozenset = frozenset()

    def __getitem__(self, cle: str) -> Parametre:
        return self._p[cle]

    # Accès sans passer par _p (R2.3, 25/11/2026)
    def __contains__(self, cle: str) -> bool:
        return cle in self._p

    def cles(self):
        return self._p.keys()

    def items(self):
        return self._p.items()

    def remplacer(self, cle: str, par: Parametre) -> None:
        """Remplace un paramètre sur place : réservé aux copies neuves (avec(), en_crise()) ; les résultats déjà
        mis en cache sur cette instance sont oubliés."""
        if cle not in self._p:
            raise ErreurParametre(f"Paramètre inconnu : {cle}")
        self._p[cle] = par
        self.__dict__.pop("_cache", None)

    def ajouter(self, cle: str, par: Parametre) -> None:
        """Ajoute un paramètre absent (copies neuves et tests seulement, comme remplacer)."""
        if cle in self._p:
            raise ErreurParametre(f"{cle} existe déjà : remplacer()")
        self._p[cle] = par
        self.__dict__.pop("_cache", None)

    def retirer(self, cle: str) -> None:
        """Retire un paramètre (copies neuves seulement, comme remplacer)."""
        del self._p[cle]
        self.__dict__.pop("_cache", None)

    def val(self, cle: str, scenario: str = "prudent") -> Any:
        if scenario == "depart":  # colonne prudente, même dans le calcul de crise (point de départ commun)
            scenario = "prudent"
        elif scenario == "prudent":
            scenario = self.colonne_prudent
        return self._p[cle].pour(scenario)

    def en_crise(self) -> "Parametres":
        """Copie pour le calcul de crise : la colonne prudente lit les valeurs de crise, sans toucher au fichier de
        paramètres (la colonne « depart » reste le prudent)."""
        c = copy.copy(self)
        c.__dict__.pop("_cache", None)
        c.colonne_prudent = "crise"
        c._p = dict(self._p)  # copie : une écriture dans c._p ne touche plus l'original (R2.3)
        c.jeton = next(_JETONS)
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
        c.jeton = next(_JETONS)
        return c
