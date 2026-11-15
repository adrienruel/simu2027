"""Variante de classement commune : les fonds de capitalisation des programmes comptés parmi les administrations
publiques (APU). Règle du 15/11/2026 (Adrien) : la variante s'applique à tous les programmes qui proposent une
retraite par capitalisation par un fonds, pas seulement au sien.

Le chiffrage publié range ces fonds hors des APU (comme un fonds de pension ou le régime additionnel des
fonctionnaires géré à part). La variante les met dedans, avec trois conventions identiques pour tous :
  1. ce que le fonds paie à la place de l'État (Écologie de droite : investissements publics) redevient une
     dépense publique ;
  2. l'argent public versé au fonds (mesures marquées fonds="versement" : abondement de l'État chez Philippe, part
     des employeurs publics chez Retailleau) est consolidé, donc retiré des dépenses : c'est un transfert interne
     aux APU ;
  3. l'épargne obligatoire des salariés et des employeurs privés n'est pas comptée en recette publique, car elle
     reste due aux épargnants (convention haute, déjà celle d'Écologie de droite).
Rien ne change dans l'économie : seuls les comptes publics bougent, et ce qui en dépend (règle de trajectoire du
programme, écart de taux gagné ou perdu par la dette, moteur/noyau._deux_passes).

Un programme peut fournir ses écritures propres par `mesures_fonds_apu(p, entrees)` (Écologie de droite) ; sinon
les mesures fonds="versement" sont retirées. Programme sans fonds codé : variante identique au publié."""
from __future__ import annotations

from .noyau import ANNEES, Mesure


def ecritures(programme, p, entrees: dict) -> dict[str, list[Mesure]]:
    """{scénario: mesures de périmètre ajoutées dans la variante}."""
    if hasattr(programme, "mesures_fonds_apu"):
        return programme.mesures_fonds_apu(p, entrees)
    return {s: [Mesure(f"Fonds dans les administrations publiques : {m.nom}", m.poste,
                       {t: -v for t, v in m.valeurs.items()}, "perimetre")
                for m in e.mesures if m.fonds == "versement"] for s, e in entrees.items()}


def a_un_fonds(programme, p) -> bool:
    if not hasattr(programme, "entrees"):
        return False
    ent = programme.entrees(p, ("prudent",))
    return any(ecritures(programme, p, ent)["prudent"])


def variante(p, programme, scenarios=None) -> dict[str, dict[int, dict]]:
    """Comptes publiés (`publie`) et comptes de la variante (`apu`) de chaque scénario, calculés de la même façon
    (deux passes pour l'écart de taux, règle comprise), et le montant que le classement déplace (`deplace`, Md€ :
    + = dépense publique en plus dans la variante)."""
    from . import noyau
    from .statu_quo import SCENARIOS
    noms = [s for s in SCENARIOS if scenarios is None or s in scenarios]
    out = {}
    for s in noms:
        ref = noyau.trajectoire(p, s)

        def fabrique(plus: bool):
            def f():
                e = programme.entrees(p, (s,))[s]
                extra = ecritures(programme, p, {s: e})[s] if plus else []
                return e.mesures + extra, e.contexte, e.dynamiques, e.regle
            return f
        pub = noyau._deux_passes(p, s, fabrique(False), ref)
        apu = noyau._deux_passes(p, s, fabrique(True), ref)
        e = programme.entrees(p, (s,))[s]
        dep = ecritures(programme, p, {s: e})[s]
        out[s] = {"publie": pub, "apu": apu,
                  "deplace": {t: sum((-1 if m.poste == "recettes" else 1) * m.valeurs.get(t, 0.0) for m in dep)
                              for t in ANNEES}}
    return out
