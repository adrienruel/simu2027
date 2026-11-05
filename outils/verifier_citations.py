"""Vérifie que chaque citation de mesures.yaml figure mot pour mot à la page indiquée du programme."""
import re, sys, unicodedata, yaml, pathlib

def norm(t):
    t = unicodedata.normalize("NFC", t).replace("­", "").replace("'", "’")
    t = re.sub(r"-\s+(?=[a-zà-ÿ])", "", t)          # césures de fin de ligne
    return re.sub(r"\s+", " ", t).strip()

def main(yaml_path, pages_dir):
    mesures = yaml.safe_load(open(yaml_path, encoding="utf-8"))["mesures"]
    pages = {int(p.stem[1:]): norm(p.read_text(encoding="utf-8")) for p in pathlib.Path(pages_dir).glob("p*.txt")}
    tout = " ".join(pages[k] for k in sorted(pages))
    erreurs = 0
    for m in mesures:
        c, p = m.get("citation"), m.get("page")
        if not c:
            if not m.get("source_secondaire"):
                print(f"{m['id']}: ni citation ni source secondaire"); erreurs += 1
            continue
        c = norm(c)
        if p and c in pages.get(p, ""):
            continue
        ailleurs = [k for k, t in pages.items() if c in t]
        print(f"{m['id']}: citation absente de la p. {p}" + (f" (trouvée p. {ailleurs})" if ailleurs else " (introuvable)"))
        erreurs += 1
    print(f"{len(mesures)} mesures, {erreurs} erreur(s)")
    return erreurs

if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:3]) else 0)
