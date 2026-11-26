"""Roadmap 2.4 (22/11/2026) : prime d'activité d'un emploi en plus selon la famille de qui le prend.

Le moteur (noyau.ppa_par_emploi) comptait la prime d'activité d'une personne seule pour chaque emploi créé. Ce script
la calcule sur la population de la microsimulation : chaque chômeur de 18 à 64 ans prend un emploi toute l'année au
salaire d'un emploi créé (emploi.cout_emploi_cree_smic × coût du SMIC), son allocation de chômage s'arrête, le reste
du ménage ne change pas. Rapport = prime d'activité en plus de sa famille (moyenne pondérée sur les chômeurs) /
prime d'activité d'une personne seule au même salaire (table d'OpenFisca du moteur). Prime théorique (recours
complet), comme la table de la personne seule. Le RSA et les aides au logement en moins sont donnés pour
information (le moteur les compte par emploi.allocation_chomeur_evitee).

    python -m outils.ppa_emplois      → valeurs à reporter dans economie.yaml : emploi.prime_activite_familles
                                         (rapport), allocation_chomeur_evitee et ses deux parts
"""
from __future__ import annotations

import numpy as np

from moteur.parametres import Parametres
from moteur.systeme_actuel import _interp, _table_openfisca
from outils import openfisca_population as op


def brut_emploi_cree(p: Parametres) -> float:
    T = _table_openfisca()
    c = _interp(p.val("profils.smic_brut_mensuel_2026") * 12, T["brut"], T["cout_du_travail"]) * p.val("emploi.cout_emploi_cree_smic")
    return _interp(c, T["cout_du_travail"], T["brut"]), _interp(c, T["cout_du_travail"], T["ppa"])


def calcul() -> dict:
    p = Parametres()
    b, ppa_seul = brut_emploi_cree(p)
    lignes = op.lire()
    ch = lambda l: l["statut"] == "chomeur" and 18 <= int(l["age"]) <= 64  # noqa: E731
    menages = {l["menage"] for l in lignes if ch(l)}
    sous = [dict(l) for l in lignes if l["menage"] in menages]
    variante = []
    for l in sous:
        l = dict(l)
        if ch(l):
            l.update(statut="salarie_prive", salaire_brut=b, mois_travailles=12, debut_mois=0, chomage_brut=0.0)
        variante.append(l)
    an = "2026"
    res = {}
    for nom, lg in (("avant", sous), ("apres", variante)):
        sim, s = op.simulation(lg)
        res[nom] = {v: sim.calculate_add(v, an) for v in ("ppa", "rsa", "aide_logement")}
        poids_fam = np.zeros(s["n_familles"])
        np.maximum.at(poids_fam, s["famille"], np.array([float(l["poids"]) for l in lg]))
        res[nom]["poids"] = poids_fam
        del sim
    w = res["avant"]["poids"]
    n = sum(float(l["poids"]) for l in sous if ch(l))
    d = {v: float((w * (res["apres"][v] - res["avant"][v])).sum()) / n for v in ("ppa", "rsa", "aide_logement")}
    # allocation de chômage arrêtée : moyenne par chômeur (26/11/2026 : calculée ici, avant reportée à la main)
    alloc = sum(float(l["poids"]) * float(l["chomage_brut"]) for l in sous if ch(l)) / n
    total = alloc - d["rsa"] - d["aide_logement"]
    return {"brut": b, "ppa_seul": ppa_seul, "chomeurs": n, "ppa_famille": d["ppa"], "rsa": d["rsa"],
            "aide_logement": d["aide_logement"], "rapport": d["ppa"] / ppa_seul, "allocation": alloc,
            # valeurs à reporter dans economie.yaml (emploi.*)
            "allocation_chomeur_evitee": total, "part_allocation_assurance_chomage": alloc / total,
            "part_allocation_logement": -d["aide_logement"] / total}


if __name__ == "__main__":
    r = calcul()
    print({k: round(v, 3) for k, v in r.items()})
