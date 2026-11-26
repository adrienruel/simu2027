"""Même règle pour les économies et les recettes de tous les programmes (roadmap du comparateur, 2.1 et 2.2).

- Une économie ou une recette nommée est estimée par le modèle dans chaque scénario : son montant monte de la crise à
  l'optimiste, et n'est identique dans les quatre scénarios que pour un barème calculé (liste ci-dessous, motivée).
- Les montants sans source ni note ne sont pas plus nombreux qu'au 16/11/2026 (liste à résorber, pas à allonger).
- Un programme ne recopie ni ne redéfinit un paramètre commun à tous (groupe programme_commun)."""
import pytest

from moteur import noyau
from moteur.parametres import Parametres
from outils.audit_economies import SCENARIOS, lignes

# montant identique dans les quatre scénarios, avec la raison
IDENTIQUES = {
    "tondelier_mesures.sous_indexation": "barème : sous-indexation mécanique des pensions au-dessus d'un seuil (DÉCISION)",
    "tondelier_mesures.malus_poids": "à revoir : malus au poids sans source, 0,3 Md€ dans tous les scénarios",
}
# économies et recettes nommées sans source ni note au 16/11/2026 (à sourcer) ; 10 autres ont une note sans source
SANS_SOURCE = {"tondelier_mesures"}  # niches_plafond, superprofits


@pytest.fixture(scope="module")
def tableau():
    return lignes()


def test_montants_croissants_de_la_crise_a_l_optimiste(tableau):
    for l in tableau:
        m = [l[f"{s}_md"] for s in SCENARIOS]
        assert m[0] <= m[1] + 1e-9 <= m[2] + 2e-9 <= m[3] + 3e-9, (l["cle"], m)


def test_montant_identique_dans_les_scenarios_seulement_si_motive(tableau):
    identiques = {l["cle"] for l in tableau if len({l[f"{s}_md"] for s in SCENARIOS}) == 1}
    assert identiques <= set(IDENTIQUES), sorted(identiques - set(IDENTIQUES))


def test_sans_source_ne_s_allonge_pas(tableau):
    sans = [l for l in tableau if not l["source"] and not l["note"]]
    assert {l["cle"].split(".")[0] for l in sans} <= SANS_SOURCE
    assert len(sans) <= 2, [l["cle"] for l in sans]


def test_aucun_programme_ne_redefinit_un_parametre_commun():
    communs = {c.split(".", 1)[1] for c in Parametres().cles() if c.startswith("programme_commun.")}
    for nom in noyau.programmes_disponibles()[1:]:
        for c in Parametres(programme=nom).cles():
            if not c.startswith(f"{nom}_") or "." not in c:
                continue
            groupe, champ = c[len(nom) + 1:].split(".", 1)
            assert f"{groupe}_{champ}" not in communs, f"{c} redéfinit programme_commun.{groupe}_{champ}"
