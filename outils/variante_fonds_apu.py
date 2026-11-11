"""Variante « fonds dans les administrations publiques » d'Écologie de droite (relecture I5) : déficit et dette si les
investissements financés par le fonds restent des dépenses publiques. Écrit sorties/variante_fonds_apu.json.

    python -m outils.variante_fonds_apu
"""
from __future__ import annotations

import json
from pathlib import Path

from moteur import noyau
from moteur.parametres import Parametres

RACINE = Path(__file__).resolve().parents[1]
ANS = (2029, 2037, 2050, 2073)


def main() -> dict:
    p = Parametres()
    prog = noyau.charger("ecologie_de_droite")
    base, var = noyau.simuler(p, prog, contrefactuel=False), prog.variante_fonds_apu(p)
    out = {s: {t: {"deficit_publie": round(base[s][t]["deficit"], 2), "deficit_fonds_apu": round(var[s][t]["deficit"], 2),
                   "deficit_fonds_apu_avant_regle": round(var[s][t]["deficit_avant_regle"], 2),
                   "dette_pib_publiee": round(base[s][t]["dette_pib"], 1), "dette_pib_fonds_apu": round(var[s][t]["dette_pib"], 1),
                   "investissements_du_fonds_md": round(var[s][t]["investissements_du_fonds"], 1)} for t in ANS} for s in base}
    (RACINE / "sorties" / "variante_fonds_apu.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    for s, v in main().items():
        for t, x in v.items():
            print(f"{s:10s} {t}  déficit publié {x['deficit_publie']:6.2f}  fonds dans les APU {x['deficit_fonds_apu']:6.2f}"
                  f"  dette {x['dette_pib_publiee']:6.1f} → {x['dette_pib_fonds_apu']:6.1f} % du PIB"
                  f"  (investissements du fonds : {x['investissements_du_fonds_md']:.0f} Md€)")
