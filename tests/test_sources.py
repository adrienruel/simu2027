"""Sources vérifiables (phase 3.4, 16/11/2026) : url et page pour le statut SOURCE."""
import csv
from pathlib import Path

import pytest

from moteur import noyau
from moteur.parametres import ErreurParametre, Parametres

RACINE = Path(__file__).resolve().parents[1]
# Parmi les vingt paramètres sourcés qui pèsent le plus, ceux dont la source n'a pas d'adresse en ligne, et pourquoi
SANS_ADRESSE_ADMISE = {
    "roussel_smic.smic_net_programme": "université d'été du PCF (août 2026) : pas de texte publié retrouvé",
    "macro.taux_apparent_2029": "cellule du classeur (Effets macro!B211), source primaire à retrouver",
    "sante_trajectoire.depenses_2024": "cartographie de l'Assurance maladie : rapport Charges et produits 2027 sans adresse stable retrouvée",
}


def _sources():
    for nom in [None] + noyau.programmes_disponibles()[1:]:
        p = Parametres(programme=nom)
        for x in p:
            if nom and f"programmes/{nom}/" not in str(p.origine[x.cle]):
                continue
            if x.statut == "SOURCE":
                yield x


def test_nouvelle_source_avec_adresse():
    """Un paramètre SOURCE sans url doit figurer dans l'arriéré (parametres/sources/sans_url.txt) ; un paramètre qui a
    reçu son url doit en être retiré."""
    arriere = {l.strip() for l in (RACINE / "parametres" / "sources" / "sans_url.txt").read_text(encoding="utf-8").splitlines()
               if l.strip() and not l.startswith("#")}
    sans = {x.cle for x in _sources() if not x.url}
    assert sans - arriere == set(), f"SOURCE sans url hors de l'arriéré : {sorted(sans - arriere)}"
    assert arriere - sans == set(), f"à retirer de sans_url.txt (url ajoutée ou paramètre disparu) : {sorted(arriere - sans)}"
    for x in _sources():
        if x.url:
            assert x.page, f"{x.cle} : url sans page (où lire la valeur dans le document)"


def test_vingt_plus_lourdes_verifiables():
    """Les vingt paramètres sourcés qui pèsent le plus sur le déficit de 2037 (sorties/sources_poids.csv) ont une url
    et une page, sauf les exceptions nommées."""
    lignes = list(csv.DictReader((RACINE / "sorties" / "sources_poids.csv").open(encoding="utf-8")))[:20]
    manquants = {l["cle"] for l in lignes if not (l["url"] and l["page"])}
    assert manquants <= set(SANS_ADRESSE_ADMISE), sorted(manquants - set(SANS_ADRESSE_ADMISE))


def test_url_reservee_aux_sources(tmp_path):
    f = tmp_path / "p.yaml"
    f.write_text("scenarios: [crise, prudent, median, optimiste]\ng:\n  x: {valeur: 1, unite: taux, statut: HYPOTHESE, url: \"https://a.fr\"}\n", encoding="utf-8")
    with pytest.raises(ErreurParametre):
        Parametres(chemin=f)
    f.write_text("scenarios: [crise, prudent, median, optimiste]\ng:\n  x: {valeur: 1, unite: taux, statut: SOURCE, source: s, url: \"a.fr\"}\n", encoding="utf-8")
    with pytest.raises(ErreurParametre):
        Parametres(chemin=f)


def _montant_max(v):
    m = v.get("montant") if isinstance(v, dict) else None
    if isinstance(m, dict):
        return max((abs(x) for x in m.values() if isinstance(x, (int, float))), default=0.0)
    return abs(m) if isinstance(m, (int, float)) else 0.0


def test_hypotheses_lourdes_justifiees():
    """Audit I4 (27/11/2026) : une mesure en HYPOTHESE de plus de 0,5 Md€ dit d'où vient son montant, par une source
    ou une note (calcul, ordre de grandeur, ou enveloppe retenue faute de chiffrage dans le programme)."""
    manquants = []
    for nom in noyau.programmes_disponibles()[1:]:
        p = Parametres(programme=nom)
        for x in p:
            if not x.cle.startswith(f"{nom}_mesures.") or x.statut != "HYPOTHESE":
                continue
            v = x.valeur if isinstance(x.valeur, dict) else {}
            if _montant_max(v) > 0.5 and not (x.source or x.note or v.get("source") or v.get("note")):
                manquants.append(x.cle)
    assert manquants == [], manquants
