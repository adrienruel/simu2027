"""Chargement et validation du fichier de paramètres unique."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CHEMIN_DEFAUT = Path(__file__).resolve().parent.parent / "parametres" / "parametres.yaml"
STATUTS = {"SOURCE", "HYPOTHESE", "DECISION"}
UNITES_MONTANT = {"eur_an", "eur_mois", "md_eur"}


class ErreurParametre(ValueError):
    pass


@dataclass(frozen=True)
class Parametre:
    cle: str
    valeur: Any
    unite: str
    statut: str
    annee_euros: int | None = None
    source: str | None = None
    note: str | None = None

    def pour(self, scenario: str) -> Any:
        """Valeur du paramètre dans un scénario (identique partout si non ventilée)."""
        if isinstance(self.valeur, dict):
            if scenario not in self.valeur:
                raise ErreurParametre(f"{self.cle} : pas de valeur pour le scénario {scenario}")
            return self.valeur[scenario]
        return self.valeur


class Parametres:
    def __init__(self, chemin: Path | str = CHEMIN_DEFAUT):
        brut = yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
        self.scenarios: list[str] = brut.pop("scenarios")
        self._p: dict[str, Parametre] = {}
        for groupe, contenu in brut.items():
            for nom, champs in contenu.items():
                cle = f"{groupe}.{nom}"
                self._p[cle] = self._valider(cle, champs)

    def _valider(self, cle: str, c: dict) -> Parametre:
        for champ in ("valeur", "unite", "statut"):
            if champ not in c:
                raise ErreurParametre(f"{cle} : champ « {champ} » manquant")
        if c["statut"] not in STATUTS:
            raise ErreurParametre(f"{cle} : statut inconnu {c['statut']}")
        if c["statut"] == "SOURCE" and not c.get("source"):
            raise ErreurParametre(f"{cle} : statut SOURCE sans source")
        if c["unite"] in UNITES_MONTANT and "annee_euros" not in c:
            raise ErreurParametre(f"{cle} : montant sans année des euros")
        if isinstance(c["valeur"], dict) and set(c["valeur"]) != set(self.scenarios):
            raise ErreurParametre(f"{cle} : scénarios incomplets {sorted(c['valeur'])}")
        return Parametre(
            cle=cle, valeur=c["valeur"], unite=c["unite"], statut=c["statut"],
            annee_euros=c.get("annee_euros"), source=c.get("source"), note=c.get("note"),
        )

    def __getitem__(self, cle: str) -> Parametre:
        return self._p[cle]

    def val(self, cle: str, scenario: str = "prudent") -> Any:
        return self._p[cle].pour(scenario)

    def __iter__(self):
        return iter(self._p.values())
