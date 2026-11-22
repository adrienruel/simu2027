"""Taux d'emploi par âge qui suivent la projection de l'Insee, et canal école par cohortes (phase P, 19/11/2026)."""
from __future__ import annotations

import pytest

from moteur import canaux_declares as cd
from moteur import statu_quo as sq
from moteur.demographie import taux_emploi_par_age
from moteur.parametres import Parametres


def test_taux_de_2025_inchanges_et_seniors_en_hausse():
    p = Parametres()
    t25, t40 = taux_emploi_par_age(p, 2025), taux_emploi_par_age(p, 2040)
    base = p.val("demographie.taux_emploi_age")
    assert t25[62] == pytest.approx(base["60-64"])
    assert t40[30] == pytest.approx(base["25-49"] * 87.8 / 87.9)  # roadmap 2.3 : 25-54 ans selon la figure 2
    # rapport de la projection de l'Insee (figure 3) : 57,7 % en 2040 contre ≈ 42,0 % en 2025
    proj = p.val("demographie.taux_activite_seniors_projection")["60-64"]
    v25 = proj[2021] + (proj[2030] - proj[2021]) * 4 / 9
    assert t40[62] == pytest.approx(base["60-64"] * proj[2040] / v25)
    assert taux_emploi_par_age(p, 2090)[67] == pytest.approx(taux_emploi_par_age(p, 2070)[67])


def test_option_desactivee_redonne_les_taux_figes():
    q = Parametres().avec({"demographie.taux_emploi_tendance": False})
    assert taux_emploi_par_age(q, 2050) == taux_emploi_par_age(q, 2025)
    e0 = sq.effectifs(q, "prudent")
    e1 = sq.effectifs(Parametres(), "prudent")
    assert e1[2040]["emploi"] > e0[2040]["emploi"]
    assert e1[2026]["emploi"] == pytest.approx(e0[2026]["emploi"], rel=0.01)  # un an après les taux observés


def test_part_des_cohortes_ecole_croissante_et_bornee():
    p = Parametres()
    parts = [cd.part_cohortes_ecole(p, "median", t, 2045) for t in range(2044, 2074)]
    assert parts[0] == 0.0
    assert all(b >= a for a, b in zip(parts, parts[1:]))
    assert 0 < parts[-1] < 1
