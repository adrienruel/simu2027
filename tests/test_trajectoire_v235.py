"""Étape 1 : le bloc comptable de la trajectoire reproduit la v235 (scénario retenu, prudent).

Entrées et cibles : reference/cibles/trajectoire.csv (valeurs de la v235).
Les participations remises au fonds sont, pour l'instant, déduites des cibles ;
elles seront calculées par le module du remboursement de 35 %.
"""
import csv
from pathlib import Path

import pytest

from moteur.parametres import Parametres
from moteur.trajectoire import Annee, calculer

CIBLES = Path(__file__).resolve().parent.parent / "reference" / "cibles" / "trajectoire.csv"
P = Parametres()
TOLERANCE_MD = 0.01


def _cibles():
    lignes = {r[0][:25]: [float(x) for x in r[1:]] for r in csv.reader(CIBLES.open(encoding="utf-8")) if r[0] != "poste"}
    return lambda debut: next(v for k, v in lignes.items() if k.startswith(debut))


g = _cibles()
ANNEES = list(range(2029, 2074))


def _entrees():
    pib, rec = g("PIB"), g("Recettes (e")
    sa, re_, rui, inv, aut, cd = g("Santé"), g("Retraites"), g("RUI"), g("Investissement"), g("Autres"), g("Charge")
    so, de = g("Solde budg"), g("Dette en")
    dette_prec = P.val("trajectoire.dette_depart")
    out = []
    for i, an in enumerate(ANNEES):
        participations = dette_prec - so[i] - de[i]  # à remplacer par le module du remboursement
        out.append(Annee(an, pib[i], rec[i], sa[i], re_[i], rui[i], inv[i], aut[i], cd[i], participations))
        dette_prec = de[i]
    return out


RES = calculer(_entrees(), P.val("trajectoire.dette_depart"), P.val("trajectoire.inflation"))


@pytest.mark.parametrize("attr, poste", [
    ("depenses", "Dépenses totales"), ("solde", "Solde budg"),
    ("solde_primaire", "Solde prim"), ("dette", "Dette en"),
])
def test_md_eur(attr, poste):
    for a, cible in zip(RES, g(poste)):
        assert getattr(a, attr) == pytest.approx(cible, abs=TOLERANCE_MD), a.annee


@pytest.mark.parametrize("attr, poste", [("dette_pib", "Dette /"), ("solde_maastricht_pib", "Solde public")])
def test_ratios(attr, poste):
    for a, cible in zip(RES, g(poste)):
        assert getattr(a, attr) == pytest.approx(cible, abs=1e-6), a.annee


def test_participations_remises_au_fonds():
    """Seules 2047 et 2048 portent des participations ; leur total = 135 Md€ (après décote)."""
    non_nulles = {a.annee: a.participations_fonds for a in RES if abs(a.participations_fonds) > TOLERANCE_MD}
    assert set(non_nulles) == {2047, 2048}
    assert sum(non_nulles.values()) == pytest.approx(135.0, abs=0.01)


def test_deficits_publies():
    d = {a.annee: -a.solde_maastricht_pib * 100 for a in RES}
    assert (round(d[2029], 2), round(d[2032], 2), round(d[2037], 2)) == (4.67, 3.81, 2.31)
