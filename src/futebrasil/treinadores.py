"""Treinadores da Série A: base treinador × partida e métricas.

A base (`data/external/treinadores/treinadores_por_partida_2003_2025.csv`) tem uma
linha por clube por partida, com o treinador que comandou o time naquele jogo,
o status da atribuição e a fonte. Ela é montada pela coleta em
`analyses/03-treinadores-da-serie-a/coleta/` (Transfermarkt + O Gol + CBF +
Wikipédia) e versionada pronta, porque a coleta depende de raspagem web.

Funções principais:
    carregar()                -> base analítica (sem lados de treinador desconhecido)
    agregar(df, chaves)       -> jogos, V-E-D, aproveitamento, gols, saldo
    ranquear(df, col, ...)    -> ordena com empate explícito (posição "min")
    series(resultados, pts)   -> maiores séries e melhor/pior trecho de 10 jogos
    campeonato(df)            -> "campeonato de treinadores" por temporada
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from futebrasil.caminhos import EXTERNO

PASTA = EXTERNO / "treinadores"
BASE = PASTA / "treinadores_por_partida_2003_2025.csv"
STATUS_CONFIAVEIS = ("confirmado", "provável")


def carregar(incluir_desconhecidos: bool = False) -> pd.DataFrame:
    """Base analítica: uma linha por (partida, clube) com treinador, gols e pontos."""
    df = pd.read_csv(BASE, dtype={"tm_id_jogo": str})
    if not incluir_desconhecidos:
        df = df[df["treinador"] != "DESCONHECIDO"]
    return df.reset_index(drop=True)


def agregar(df: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Métricas por grupo. Aproveitamento = pontos / (3 × jogos)."""
    g = df.groupby(chaves, dropna=False)
    out = g.agg(
        jogos=("pontos", "size"),
        V=("resultado", lambda s: int((s == "V").sum())),
        E=("resultado", lambda s: int((s == "E").sum())),
        D=("resultado", lambda s: int((s == "D").sum())),
        pontos=("pontos", "sum"),
        GF=("gols_feitos", "sum"),
        GA=("gols_sofridos", "sum"),
        clubes=("clube", lambda s: ", ".join(dict.fromkeys(s))),
    ).reset_index()
    out["aprov"] = out["pontos"] / (3 * out["jogos"])
    out["pctV"] = out["V"] / out["jogos"]
    out["pctE"] = out["E"] / out["jogos"]
    out["pctD"] = out["D"] / out["jogos"]
    out["SG"] = out["GF"] - out["GA"]
    out["GFj"] = out["GF"] / out["jogos"]
    out["GAj"] = out["GA"] / out["jogos"]
    out["SGj"] = out["SG"] / out["jogos"]
    return out


def ranquear(df: pd.DataFrame, col: str, crescente: bool, n: int | None = None,
             minimo: int | None = None, col_jogos: str = "jogos") -> pd.DataFrame:
    """Ordena por `col` (critério secundário explícito: mais jogos).

    `pos` usa ranking "min": empates exatos dividem a mesma posição e `empate`
    marca "=". `n` corta pela posição (não pelo número de linhas), para não
    esconder empates na última vaga.
    """
    d = df if minimo is None else df[df[col_jogos] >= minimo]
    d = d.sort_values([col, col_jogos], ascending=[crescente, False]).copy()
    d["pos"] = d[col].round(10).rank(method="min", ascending=crescente).astype(int)
    d["empate"] = np.where(d.duplicated(col, keep=False), "=", "")
    return d if n is None else d[d["pos"] <= n]


def series(resultados: list[str], pontos: list[int]) -> dict:
    """Maiores séries de vitórias, derrotas, invicta e sem vencer, e o melhor e o
    pior aproveitamento em 10 jogos seguidos (NaN se houver menos de 10 jogos)."""
    out = {}
    for nome, cond in (("seq_vitorias", lambda r: r == "V"), ("seq_derrotas", lambda r: r == "D"),
                       ("seq_invicta", lambda r: r != "D"), ("seq_sem_vencer", lambda r: r != "V")):
        melhor = atual = 0
        for r in resultados:
            atual = atual + 1 if cond(r) else 0
            melhor = max(melhor, atual)
        out[nome] = melhor
    if len(pontos) >= 10:
        janela = pd.Series(pontos).rolling(10).sum().dropna() / 30
        out["melhor_10j"], out["pior_10j"] = janela.max(), janela.min()
    else:
        out["melhor_10j"] = out["pior_10j"] = np.nan
    return out


def campeonato(df: pd.DataFrame, min_jogos: int = 10, n_rebaixados: int = 4) -> pd.DataFrame:
    """Uma 'liga' de treinadores por temporada, ordenada por aproveitamento.

    Soma todos os clubes que o técnico dirigiu no ano; entram só técnicos com
    `min_jogos`+ jogos. Campeão = 1º; rebaixados = os `n_rebaixados` piores
    aproveitamentos (empate exato na linha de corte rebaixa todos os empatados).
    """
    ano = agregar(df, ["temporada", "treinador_id", "treinador"])
    ano = ano[ano["jogos"] >= min_jogos]
    tabelas = []
    for _, g in ano.groupby("temporada"):
        g = g.sort_values(["aprov", "jogos"], ascending=[False, False]).copy()
        g["posicao"] = g["aprov"].round(10).rank(method="min", ascending=False).astype(int)
        g["participantes"] = len(g)
        g["campeao"] = g["posicao"] == 1
        g["vice"] = g["posicao"] == 2
        g["top4"] = g["posicao"] <= 4
        corte = g["aprov"].round(10).nsmallest(n_rebaixados).max()
        g["rebaixado"] = g["aprov"].round(10) <= corte
        tabelas.append(g)
    return pd.concat(tabelas, ignore_index=True)
