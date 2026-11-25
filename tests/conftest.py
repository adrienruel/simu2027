"""Accélérations propres à la suite de tests : le moteur n'est pas modifié.

Lecture YAML mémorisée (25/11/2026). Chaque `Parametres()` relit et analyse tous les fichiers de paramètres, avec le
chargeur strict du moteur, en Python pur. La suite en construit plus de 2 400, soit environ 85 s sur 200 passées dans
l'analyse YAML, pour une dizaine de fichiers. Ici, le premier passage d'un texte donné passe par le vrai chargeur
(contrôle des clés en double compris) ; les suivants reçoivent une copie neuve du résultat (pickle, ≈ 0,6 ms contre
≈ 120 ms pour l'analyse). La clé est le texte lui-même : un fichier modifié pendant la suite, ou un fichier de test
écrit dans tmp_path, est donc analysé à nouveau. Désactiver : `SIMU_SANS_CACHE_YAML=1 python -m pytest`.
"""
from __future__ import annotations

import os
import pickle

import yaml

if not os.environ.get("SIMU_SANS_CACHE_YAML"):
    _load_origine = yaml.load
    _memo: dict = {}

    def _load_memorise(stream, Loader=None):
        if not isinstance(stream, (str, bytes)):
            return _load_origine(stream, Loader=Loader)
        cle = (Loader, stream)
        b = _memo.get(cle)
        if b is None:
            r = _load_origine(stream, Loader=Loader)
            _memo[cle] = pickle.dumps(r, protocol=pickle.HIGHEST_PROTOCOL)
            return r
        return pickle.loads(b)

    yaml.load = _load_memorise  # yaml.safe_load passe aussi par yaml.load
