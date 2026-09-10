"""Métricas descritivas de fator mandante e fator casa.

Convenções:
  ppg              pontos por jogo
  vantagem_ppg     ppg como mandante − ppg como visitante (mesmo recorte)
  share_pts_casa   pts em casa / (pts em casa + pts fora); 0,5 = sem vantagem
  Todas as taxas são por jogo, para comparar edições com nº de rodadas diferente.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _agg_por_mando(longo: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    g = longo.groupby(chaves + ["mandante"], observed=True).agg(
        n=("pts", "size"),
        pts=("pts", "sum"),
        v=("vitoria", "sum"),
        e=("empate", "sum"),
        d=("derrota", "sum"),
        gp=("gols_pro", "sum"),
        gc=("gols_contra", "sum"),
    )
    casa = g.xs(True, level="mandante")
    fora = g.xs(False, level="mandante")
    out = pd.DataFrame(index=casa.index.union(fora.index))
    out["n_casa"] = casa["n"].reindex(out.index)
    out["n_fora"] = fora["n"].reindex(out.index)
    out["pts_casa"] = casa["pts"].reindex(out.index)
    out["pts_fora"] = fora["pts"].reindex(out.index)
    out["ppg_casa"] = out["pts_casa"] / out["n_casa"]
    out["ppg_fora"] = out["pts_fora"] / out["n_fora"]
    out["vantagem_ppg"] = out["ppg_casa"] - out["ppg_fora"]
    out["share_pts_casa"] = out["pts_casa"] / (out["pts_casa"] + out["pts_fora"])
    out["pct_vitoria_casa"] = casa["v"].reindex(out.index) / out["n_casa"]
    out["pct_empate_casa"] = casa["e"].reindex(out.index) / out["n_casa"]
    out["pct_derrota_casa"] = casa["d"].reindex(out.index) / out["n_casa"]
    out["saldo_casa_pj"] = (casa["gp"] - casa["gc"]).reindex(out.index) / out["n_casa"]
    out["gols_pro_casa_pj"] = casa["gp"].reindex(out.index) / out["n_casa"]
    out["gols_contra_casa_pj"] = casa["gc"].reindex(out.index) / out["n_casa"]
    return out.reset_index()


def painel_clube_temporada(longo: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (clube, temporada): fator mandante daquele ano."""
    return _agg_por_mando(longo, ["clube", "temporada"]).sort_values(
        ["clube", "temporada"]
    ).reset_index(drop=True)


def liga_por_temporada(longo: pd.DataFrame) -> pd.DataFrame:
    """Fator mandante agregado da liga, ano a ano (+ recorte com/sem público)."""
    base = _agg_por_mando(longo, ["temporada"])
    sem_pub = (
        _agg_por_mando(longo[longo["sem_publico"]], ["temporada"])
        .set_index("temporada")[["vantagem_ppg", "share_pts_casa", "n_casa"]]
        .add_suffix("_sem_publico")
    )
    return base.merge(sem_pub, on="temporada", how="left")


def liga_agregada(longo: pd.DataFrame) -> pd.DataFrame:
    """Uma linha só: fator mandante de toda a era pontos corridos."""
    out = _agg_por_mando(longo.assign(_k=1), ["_k"]).drop(columns="_k")
    out.insert(0, "recorte", "2003-2024 (tudo)")
    com = _agg_por_mando(longo[~longo["sem_publico"]].assign(_k=1), ["_k"]).drop(columns="_k")
    com.insert(0, "recorte", "com público")
    sem = _agg_por_mando(longo[longo["sem_publico"]].assign(_k=1), ["_k"]).drop(columns="_k")
    sem.insert(0, "recorte", "sem público (pandemia)")
    return pd.concat([out, com, sem], ignore_index=True)


def clube_agregado(longo: pd.DataFrame, min_jogos: int = 30) -> pd.DataFrame:
    """Fator mandante por clube, todas as edições somadas."""
    out = _agg_por_mando(longo, ["clube"])
    out = out[out["n_casa"] >= min_jogos]
    return out.sort_values("vantagem_ppg", ascending=False).reset_index(drop=True)


def fator_casa_por_estadio(longo: pd.DataFrame, min_jogos: int = 15) -> pd.DataFrame:
    """Fator casa por (clube, estádio) entre os jogos de mando.

    A linha de base é o desempenho do MESMO clube como visitante NAS MESMAS
    temporadas em que mandou naquele estádio — controla, de forma simples, a
    força do elenco e a época.
    """
    mand = longo[longo["mandante"] & ~longo["mando_fora_de_casa"]]
    fora = longo[~longo["mandante"]]

    linhas = []
    for (clube, estadio_id), g in mand.groupby(["clube", "estadio_id"], observed=True):
        if len(g) < min_jogos:
            continue
        temps = g["temporada"].unique()
        base = fora[(fora["clube"] == clube) & (fora["temporada"].isin(temps))]
        if base.empty:
            continue
        linhas.append({
            "clube": clube,
            "estadio_id": estadio_id,
            "temporada_ini": int(g["temporada"].min()),
            "temporada_fim": int(g["temporada"].max()),
            "n_temporadas": len(temps),
            "n_jogos_casa": len(g),
            "ppg_casa": g["pts"].mean(),
            "ppg_fora_mesmas_temps": base["pts"].mean(),
            "vantagem_ppg": g["pts"].mean() - base["pts"].mean(),
            "pct_vitoria_casa": g["vitoria"].mean(),
            "saldo_casa_pj": g["saldo"].mean(),
        })
    out = pd.DataFrame(linhas)
    if out.empty:
        return out
    # posição do estádio dentro do próprio clube (fortaleza vs. resto)
    out["vantagem_vs_media_clube"] = out["vantagem_ppg"] - out.groupby("clube")["vantagem_ppg"].transform("mean")
    return out.sort_values(["clube", "temporada_ini"]).reset_index(drop=True)


def wilson_ic(sucessos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson para uma proporção (ex.: % de vitória em casa)."""
    if n == 0:
        return (np.nan, np.nan)
    p = sucessos / n
    denom = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / denom
    margem = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (centro - margem, centro + margem)
