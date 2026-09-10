"""Caminhos do projeto / project paths."""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

DADOS = RAIZ / "data"
BRUTO = DADOS / "raw"
INTERIM = DADOS / "interim"
PROCESSADO = DADOS / "processed"
EXTERNO = DADOS / "external"

ANALISES = RAIZ / "analyses"


def garantir_dirs() -> None:
    for d in (BRUTO, INTERIM, PROCESSADO, EXTERNO):
        d.mkdir(parents=True, exist_ok=True)
