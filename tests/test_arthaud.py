

def test_ajouts_du_11_novembre():
    """Répartition du travail, interdiction des licenciements, égalité salariale, carburant (11/11/2026)."""
    from moteur import noyau
    from moteur.parametres import Parametres
    p = Parametres()
    prog = noyau.charger("arthaud")
    ctx = prog.contexte(p)
    c = ctx["prudent"]["emplois_canaux"][2037]
    assert c["Interdiction des licenciements : emplois maintenus par réquisition"] > 0
    noms = " ".join(c)
    assert "répartition du travail" in noms and "Égalité salariale" in noms
    # durée calculée : heures libérées = chômage du statu quo (≈ 31,8 heures)
    assert any("(31.8 heures)" in k or "(31.7 heures)" in k or "(31.9 heures)" in k for k in c)
    # dépense des réquisitions : la plus forte en crise
    b = {s: {m["nom"]: m[2037] for m in noyau.bilan_mesures(prog, p, s)} for s in ("crise", "optimiste")}
    cle = "ART-EMP-01 — interdiction des licenciements : emplois maintenus par réquisition (coût net)"
    assert b["crise"][cle] < b["optimiste"][cle] < 0
