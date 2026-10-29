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
