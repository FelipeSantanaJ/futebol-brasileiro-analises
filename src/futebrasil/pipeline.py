"""Pipeline de dados. Uso:

    python -m futebrasil.pipeline baixar      # baixa CSVs brutos
    python -m futebrasil.pipeline preparar    # gera data/processed/*.parquet
    python -m futebrasil.pipeline validar     # checagens de sanidade
    python -m futebrasil.pipeline tudo        # os três acima
"""
from __future__ import annotations

import sys


def baixar():
    from .dados import baixar as _b
    _b()


def preparar():
    from .limpeza import gerar
    from .lookups import _snapshot
    _snapshot()
    gerar()


def validar():
    from .limpeza import carregar_partidas, carregar_time_jogo
    from .validacao import validar as _v
    _v(carregar_time_jogo(), carregar_partidas())


def tudo():
    baixar()
    preparar()
    validar()


COMANDOS = {"baixar": baixar, "preparar": preparar, "validar": validar, "tudo": tudo}


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 1 or argv[0] not in COMANDOS:
        print(__doc__)
        raise SystemExit(2)
    COMANDOS[argv[0]]()


if __name__ == "__main__":
    main()
