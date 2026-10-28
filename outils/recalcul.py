"""Recalcule la v235 dans LibreOffice, avec des cellules modifiées, et lit des cellules.

Sert à vérifier le moteur sur des jeux de paramètres que la v235 n'a pas figés
(scénario de crise, variantes). Le classeur de référence n'est jamais modifié.

    python -m outils.recalcul "Effets macro!B20=1" --lire "Scénario de crise!B5" "Effets macro!B8"
    python -m outils.recalcul --crise --lire "Effets macro!B341"

Nécessite LibreOffice (soffice) et son module Python « uno ».
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CLASSEUR = RACINE / "reference" / "Chiffrage_programme_complet_v235.xlsx"
FEUILLE_CRISE = "Scénario de crise"


def _connecter(port: int):
    import uno
    local = uno.getComponentContext()
    resolveur = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
    for _ in range(60):
        try:
            return resolveur.resolve(f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext")
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("LibreOffice ne répond pas")


def _formule_api(f: str) -> str:
    """Excel « 'Feuille'!$B$3 » → grammaire de l'API LibreOffice « $'Feuille'.$B$3 »."""
    f = re.sub(r"'([^']+)'!", lambda m: "$'" + m.group(1) + "'.", f)
    return re.sub(r"(?<![\w.'$])([A-Za-zÀ-ÿ_][\wÀ-ÿ]*)!", r"$\1.", f)


def _ref(ref: str):
    feuille, cellule = ref.rsplit("!", 1)
    return feuille.strip("'"), cellule


class Classeur:
    """Une session LibreOffice sur une copie de la v235."""

    def __init__(self, chemin: Path = CLASSEUR, port: int = 2002):
        self.tmp = Path(tempfile.mkdtemp())
        self.copie = self.tmp / chemin.name
        shutil.copy(chemin, self.copie)
        self.proc = subprocess.Popen(
            ["soffice", "--headless", "--norestore", "--nologo", f"-env:UserInstallation=file://{self.tmp}/profil",
             f"--accept=socket,host=localhost,port={port};urp;"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import uno
        from com.sun.star.beans import PropertyValue
        ctx = _connecter(port)
        bureau = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        pv = PropertyValue()
        pv.Name, pv.Value = "Hidden", True
        self.doc = bureau.loadComponentFromURL(uno.systemPathToFileUrl(str(self.copie)), "_blank", 0, (pv,))

    def cellule(self, ref: str):
        feuille, cellule = _ref(ref)
        return self.doc.Sheets.getByName(feuille).getCellRangeByName(cellule)

    def ecrire(self, ref: str, valeur) -> None:
        c = self.cellule(ref)
        if isinstance(valeur, str) and valeur.startswith("="):
            c.setFormula(_formule_api(valeur))
        elif isinstance(valeur, str):
            try:  # la feuille Scénario de crise stocke certains nombres en texte (« 126,663 »)
                c.setValue(float(valeur.replace(",", "")))
            except ValueError:
                c.setString(valeur)
        else:
            c.setValue(float(valeur))

    def recalculer(self, passes: int = 3) -> None:
        for _ in range(passes):
            self.doc.calculateAll()

    def lire(self, ref: str):
        c = self.cellule(ref)
        return c.getString() if c.getType().value == "TEXT" else c.getValue()

    def plage(self, feuille: str, plage: str) -> list[list]:
        return [list(r) for r in self.doc.Sheets.getByName(feuille).getCellRangeByName(plage).getDataArray()]

    def fermer(self) -> None:
        try:
            self.doc.close(True)
        except Exception:
            pass
        self.proc.terminate()
        self.proc.wait(timeout=30)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.fermer()


def parametres_crise(classeur: Classeur) -> dict[str, object]:
    """Les cellules et valeurs de la feuille Scénario de crise (lignes 13 et suivantes)."""
    out = {}
    for ligne in range(13, 80):
        ref = classeur.lire(f"{FEUILLE_CRISE}!A{ligne}")
        if not isinstance(ref, str) or "!" not in ref:
            continue
        c = classeur.cellule(f"{FEUILLE_CRISE}!B{ligne}")
        out[ref] = c.getValue() if c.getType().value == "VALUE" else c.getString()
    return out


def appliquer_crise(classeur: Classeur, b8_formule: bool = True) -> dict[str, object]:
    """Applique les paramètres de crise. Par défaut, Effets macro!B8 garde sa formule de crise
    (=RUI!B34, jeu de crise recalculé) plutôt que la valeur collée, ce que la v235 a fait."""
    p = parametres_crise(classeur)
    if b8_formule:
        p["Effets macro!B8"] = "=RUI!B34"
    for ref, v in p.items():
        classeur.ecrire(ref, v)
    return p


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("modifs", nargs="*", help="Feuille!Cellule=valeur")
    a.add_argument("--crise", action="store_true")
    a.add_argument("--lire", nargs="*", default=[])
    args = a.parse_args()
    with Classeur() as c:
        if args.crise:
            appliquer_crise(c)
        for m in args.modifs:
            ref, v = m.split("=", 1)
            try:
                v = float(v)
            except ValueError:
                pass
            c.ecrire(ref, v)
        c.recalculer()
        for ref in args.lire:
            print(ref, c.lire(ref))


if __name__ == "__main__":
    main()
