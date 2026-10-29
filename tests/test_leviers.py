"""Leviers : chaque levier d'économie améliore bien le solde (sens des effets)."""
from moteur.parametres import Parametres
from moteur.simulation import simuler

P = Parametres()


def _deficit(modifs, t=2037):
    return simuler(P.avec(modifs))["prudent"][t]["deficit_avant_clause"]


def test_contribution_de_transition_est_une_recette():
    """Une part de l'épargne obligatoire versée à l'État réduit le déficit (elle n'était comptée que par la clause)."""
    assert _deficit({"epargne.contribution_transition": 0.1}) < _deficit({})


def test_socle_plus_bas_reduit_le_deficit_a_long_terme():
    assert _deficit({"retraites.socle_plein": 1100}, 2073) < _deficit({}, 2073)


def test_prime_de_taux_alourdit_quand_la_dette_monte():
    """Prime de taux liée à la dette : la crise (dette qui monte) paie plus d'intérêts avec la prime que sans."""
    from moteur.macro import calculer
    avec = calculer(P.en_crise())["prudent"]
    sans = calculer(P.en_crise().avec({"macro.prime_dette": 0.0}))["prudent"]
    assert avec.charge_dette[2050] > sans.charge_dette[2050]


def test_participation_des_inactifs():
    from moteur.emploi import participation_inactifs
    e = participation_inactifs(P)
    assert e["crise"] == 0 < e["prudent"] < e["median"] < e["optimiste"]


def test_externalites_du_fonds_nulles_dans_le_prudent():
    assert P.val("macro.externalites_capital_fonds", "prudent") == 0 == P.val("macro.externalites_capital_fonds", "crise")
