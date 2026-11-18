"""Veille des sites de campagne (roadmap du comparateur, phase 9.2, 18/11/2026).

Pour chaque programme publié, télécharge les pages de programmes/veille.yaml, en tire le texte et le compare à la
dernière lecture gardée dans veille/<programme>.json. Écrit veille/rapport.md : pour chaque page, nouvelle ou
changée, les lignes ajoutées et retirées, et la date de lecture de la fiche (mesures.yaml, programme.date_lecture),
pour savoir quelles mesures sont à chiffrer. Le rapport n'est pas une sortie du comparateur (pas de manifeste) :
c'est une liste de travail.

    python -m outils.veille_programmes            # lit les pages, écrit le rapport, garde les nouvelles lectures
    python -m outils.veille_programmes --essai    # écrit le rapport sans remplacer les lectures gardées

À lancer sur un poste qui a accès au web (l'environnement de travail de Claude n'y a pas accès depuis le shell).
Les PDF demandent pypdf ; sans lui, leur empreinte seule est comparée.
"""
from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import html
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "veille"
AGENT = "simu2027-veille/1.0 (+https://github.com/adrienruel/simu2027)"


def pages() -> dict[str, list[str]]:
    from moteur import noyau
    noms = noyau.programmes_disponibles()
    liste = yaml.safe_load((RACINE / "programmes" / "veille.yaml").read_text(encoding="utf-8"))
    return {n: liste.get(n, []) for n in noms if n != "statu_quo"}


def telecharger(url: str, delai: float = 30.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=delai) as r:  # noqa: S310 (adresses de veille.yaml)
        return r.read()


def texte(url: str, contenu: bytes) -> str:
    """Texte lisible d'une page HTML ou d'un PDF, une phrase ou un bloc par ligne, espaces normalisés."""
    if url.lower().split("#")[0].endswith(".pdf") or contenu[:5] == b"%PDF-":
        try:
            from pypdf import PdfReader
        except ImportError:
            return ""
        brut = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(contenu)).pages)
    else:
        h = contenu.decode("utf-8", errors="replace")
        h = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header)\b.*?</\1>", " ", h)
        h = re.sub(r"(?i)<(br|/p|/li|/h[1-6]|/div|/tr|/section|/article)\b[^>]*>", "\n", h)
        brut = html.unescape(re.sub(r"<[^>]+>", " ", h))
    lignes = [re.sub(r"\s+", " ", x).strip() for x in brut.splitlines()]
    return "\n".join(x for x in lignes if len(x) > 2)


def comparer(avant: str, apres: str) -> dict[str, list[str]]:
    d = list(difflib.ndiff(avant.splitlines(), apres.splitlines()))
    return {"ajouts": [x[2:] for x in d if x.startswith("+ ")], "retraits": [x[2:] for x in d if x.startswith("- ")]}


def date_lecture(nom: str) -> str:
    f = RACINE / "programmes" / nom / "mesures.yaml"
    try:
        return str(yaml.safe_load(f.read_text(encoding="utf-8"))["programme"].get("date_lecture", "?"))
    except (OSError, KeyError, TypeError):
        return "?"


def veiller(lire=telecharger, garder: bool = True, aujourd_hui: str | None = None) -> str:
    """Lit chaque page, compare à la lecture gardée, renvoie le rapport (markdown). lire(url) -> bytes."""
    jour = aujourd_hui or dt.date.today().isoformat()
    DOSSIER.mkdir(exist_ok=True)
    sortie = [f"# Veille des programmes — {jour}", "",
              "Lignes ajoutées ou retirées depuis la dernière lecture gardée. Une page « nouvelle » n'avait pas de "
              "lecture gardée : elle sert de point de départ.", ""]
    for nom, urls in pages().items():
        f = DOSSIER / f"{nom}.json"
        garde = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        sortie.append(f"## {nom} (fiche lue le {date_lecture(nom)})")
        sortie.append("")
        neuf = {}
        for url in urls:
            try:
                brut = lire(url)
            except Exception as err:  # noqa: BLE001 (une page injoignable ne bloque pas les autres)
                sortie.append(f"- {url} : injoignable ({type(err).__name__})")
                if url in garde:
                    neuf[url] = garde[url]
                continue
            t = texte(url, brut)
            emp = hashlib.sha256(brut).hexdigest()[:16]
            ancien = garde.get(url)
            neuf[url] = {"empreinte": emp, "texte": t, "lu_le": jour}
            if ancien is None:
                sortie.append(f"- {url} : nouvelle ({len(t.splitlines())} lignes)")
            elif ancien["empreinte"] == emp or ancien["texte"] == t:
                sortie.append(f"- {url} : inchangée depuis le {ancien['lu_le']}")
            else:
                c = comparer(ancien["texte"], t)
                sortie.append(f"- {url} : **changée** depuis le {ancien['lu_le']} "
                              f"({len(c['ajouts'])} lignes ajoutées, {len(c['retraits'])} retirées)")
                for x in c["ajouts"][:40]:
                    sortie.append(f"    - + {x}")
                for x in c["retraits"][:20]:
                    sortie.append(f"    - − {x}")
        sortie.append("")
        if garder:
            f.write_text(json.dumps(neuf, ensure_ascii=False, indent=1), encoding="utf-8")
    rapport = "\n".join(sortie)
    (DOSSIER / "rapport.md").write_text(rapport, encoding="utf-8")
    return rapport


if __name__ == "__main__":
    print(veiller(garder="--essai" not in sys.argv))
