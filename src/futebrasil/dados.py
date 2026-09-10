"""Download dos dados brutos e registro de proveniência.

Fonte primária: adaoduque/Brasileirao_Dataset (GitHub), compilado a partir das
súmulas da CBF e do globoesporte. Ver data/README.md.
"""
from __future__ import annotations

import hashlib
from datetime import date

import pandas as pd
import requests

from .caminhos import BRUTO, EXTERNO, garantir_dirs

BASE = "https://raw.githubusercontent.com/adaoduque/Brasileirao_Dataset/master"

ARQUIVOS = {
    # nome local            arquivo remoto                              uso
    "partidas": "campeonato-brasileiro-full.csv",
    "gols": "campeonato-brasileiro-gols.csv",
    "cartoes": "campeonato-brasileiro-cartoes.csv",
    "estatisticas": "campeonato-brasileiro-estatisticas-full.csv",
}

_TIMEOUT = 60


def _sha256(caminho) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def baixar(force: bool = False) -> pd.DataFrame:
    """Baixa os 4 CSVs para data/raw/ e atualiza data/external/fontes.csv.

    Retorna o registro de proveniência.
    """
    garantir_dirs()
    linhas = []
    for nome, arquivo in ARQUIVOS.items():
        destino = BRUTO / arquivo
        if destino.exists() and not force:
            print(f"[baixar] {arquivo} já existe (use force=True para rebaixar)")
        else:
            url = f"{BASE}/{arquivo}"
            print(f"[baixar] GET {url}")
            r = requests.get(url, timeout=_TIMEOUT)
            r.raise_for_status()
            destino.write_bytes(r.content)
        linhas.append(
            {
                "nome": nome,
                "arquivo": arquivo,
                "fonte": "adaoduque/Brasileirao_Dataset",
                "url": f"{BASE}/{arquivo}",
                "bytes": destino.stat().st_size,
                "sha256": _sha256(destino),
                "baixado_em": date.today().isoformat(),
            }
        )
    reg = pd.DataFrame(linhas)
    reg.to_csv(EXTERNO / "fontes.csv", index=False, encoding="utf-8")
    print(f"[baixar] proveniência salva em {EXTERNO / 'fontes.csv'}")
    return reg


def caminho_bruto(nome: str):
    return BRUTO / ARQUIVOS[nome]


def carregar_bruto(nome: str) -> pd.DataFrame:
    """Lê um CSV bruto. O dataset é UTF-8; caímos para latin-1 se necessário."""
    caminho = caminho_bruto(nome)
    if not caminho.exists():
        raise FileNotFoundError(
            f"{caminho} não encontrado — rode `python -m futebrasil.pipeline baixar` primeiro"
        )
    try:
        return pd.read_csv(caminho, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, dtype=str, encoding="latin-1")
