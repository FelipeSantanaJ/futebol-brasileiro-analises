"""Sobrevivência ao rebaixamento: linha de segurança e ritmo em pontos.

Pergunta: dado que um clube está com X pontos na rodada R, qual a chance de
terminar entre os 4 rebaixados? E, historicamente, quantos pontos bastam para
escapar?

Recorte: era de 20 clubes / 38 rodadas / 4 rebaixados, ou seja 2006 em diante.
2003 (24 clubes) e 2004–2005 (24 e 22 clubes) tiveram formatos diferentes de
rebaixamento e ficam fora.

Duas frentes que se cruzam:
  - `linha_de_seguranca`   descritivo puro: pontos do 16º (última vaga) e do 17º
    (primeiro rebaixado) colocado, ano a ano.
  - `painel_ritmo` + `ajustar_modelo_rodada`
    regressão logística rebaixado ~ pontos por jogo até a rodada de corte, uma
    temporada-clube por linha. Ajustada separadamente por rodada de corte (em vez
    de uma única regressão com interação rodada×ritmo) porque a pergunta que
    importa é sempre local: "dado que estou na rodada R, com esse ritmo, qual a
    chance?" — ajustar por rodada evita ter que assumir uma forma funcional para
    como o efeito do ritmo muda ao longo da temporada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .validacao import classificacao

N_REBAIXADOS = 4


def _era_moderna(longo: pd.DataFrame) -> pd.DataFrame:
    return longo[longo["n_clubes_edicao"] == 20]


def flags_rebaixamento(longo: pd.DataFrame) -> dict[tuple[int, str], bool]:
    """(temporada, clube) -> terminou entre os `N_REBAIXADOS` últimos colocados."""
    out: dict[tuple[int, str], bool] = {}
    for temporada in sorted(longo["temporada"].unique()):
        tab = classificacao(longo, temporada)
        piores = set(tab.index[-N_REBAIXADOS:])
        for clube in tab.index:
            out[(temporada, clube)] = clube in piores
    return out


def linha_de_seguranca(longo: pd.DataFrame) -> pd.DataFrame:
    """Pontos do 16º e do 17º colocado ao fim de cada temporada (era de 20 clubes)."""
    longo = _era_moderna(longo)
    linhas = []
    for temporada in sorted(longo["temporada"].unique()):
        tab = classificacao(longo, temporada)
        linhas.append({
            "temporada": int(temporada),
            "pts_16": int(tab.iloc[15]["P"]),
            "pts_17": int(tab.iloc[16]["P"]),
        })
    return pd.DataFrame(linhas)


def painel_ritmo(longo: pd.DataFrame, temporadas: list[int], rodadas_corte: list[int]) -> pd.DataFrame:
    """Uma linha por (temporada, clube, rodada de corte): ritmo até ali e desfecho final."""
    longo = _era_moderna(longo)
    rebaix = flags_rebaixamento(longo)
    linhas = []
    for temporada in temporadas:
        g = longo[longo["temporada"] == temporada].sort_values(["clube", "rodada"]).copy()
        g["pts_acum"] = g.groupby("clube")["pts"].cumsum()
        for rodada in rodadas_corte:
            gr = g[g["rodada"] == rodada][["clube", "pts_acum"]]
            for _, row in gr.iterrows():
                pts = float(row["pts_acum"])
                linhas.append({
                    "temporada": temporada,
                    "clube": row["clube"],
                    "rodada": rodada,
                    "pts_acum": pts,
                    "ppg_acum": pts / rodada,
                    "rebaixado": int(rebaix[(temporada, row["clube"])]),
                })
    return pd.DataFrame(linhas)


def trajetoria_pontos(longo: pd.DataFrame, temporada: int, clube: str) -> pd.DataFrame:
    """Pontos acumulados rodada a rodada de um clube numa temporada."""
    g = longo[(longo["temporada"] == temporada) & (longo["clube"] == clube)].sort_values("rodada").copy()
    g["pts_acum"] = g["pts"].cumsum()
    g["ppg_acum"] = g["pts_acum"] / g["rodada"]
    return g[["rodada", "pts", "pts_acum", "ppg_acum"]].reset_index(drop=True)


def ajustar_modelo_rodada(painel: pd.DataFrame, rodada: int) -> tuple[sm.Logit, dict]:
    """Regressão logística rebaixado ~ ppg_acum para uma rodada de corte."""
    d = painel[painel["rodada"] == rodada]
    X = sm.add_constant(d["ppg_acum"].astype(float))
    y = d["rebaixado"].astype(float)
    modelo = sm.Logit(y, X).fit(disp=0)
    b0, b1 = modelo.params["const"], modelo.params["ppg_acum"]
    ppg_50 = -b0 / b1
    resumo = {
        "rodada": rodada,
        "n": len(d),
        "n_rebaixado": int(d["rebaixado"].sum()),
        "coef_ppg": b1,
        "se_ppg": modelo.bse["ppg_acum"],
        "p_valor": modelo.pvalues["ppg_acum"],
        "pseudo_r2": modelo.prsquared,
        "ppg_50pct": ppg_50,
        "pts_finais_50pct": ppg_50 * 38,
    }
    return modelo, resumo


def modelos_por_rodada(painel: pd.DataFrame, rodadas_corte: list[int]) -> pd.DataFrame:
    return pd.DataFrame([ajustar_modelo_rodada(painel, r)[1] for r in rodadas_corte])


def _auc_mannwhitney(y: np.ndarray, p: np.ndarray) -> float:
    from scipy.stats import mannwhitneyu

    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    u, _ = mannwhitneyu(pos, neg)
    return u / (len(pos) * len(neg))


def validar_loso(painel: pd.DataFrame, rodadas_corte: list[int]) -> pd.DataFrame:
    """Validação fora da amostra por temporada (leave-one-season-out).

    Com um único regressor e ~18 temporadas de treino em cada rodada de corte, é
    a forma mais direta de checar se o ajuste generaliza — sem quebrar o painel:
    cada temporada sai inteira de uma vez, não jogo a jogo.
    """
    temporadas = sorted(painel["temporada"].unique())
    linhas = []
    for rodada in rodadas_corte:
        d = painel[painel["rodada"] == rodada]
        preds, obs = [], []
        for fora in temporadas:
            treino = d[d["temporada"] != fora]
            teste = d[d["temporada"] == fora]
            if teste.empty:
                continue
            X = sm.add_constant(treino["ppg_acum"].astype(float))
            y = treino["rebaixado"].astype(float)
            modelo = sm.Logit(y, X).fit(disp=0)
            Xt = sm.add_constant(teste["ppg_acum"].astype(float), has_constant="add")
            preds.append(modelo.predict(Xt).to_numpy())
            obs.append(teste["rebaixado"].to_numpy())
        p = np.concatenate(preds)
        y = np.concatenate(obs)
        linhas.append({
            "rodada": rodada,
            "n": len(y),
            "auc_loso": _auc_mannwhitney(y, p),
            "brier_loso": float(np.mean((p - y) ** 2)),
        })
    return pd.DataFrame(linhas)


def aplicar_modelo(modelo: sm.Logit, ppg_acum: pd.Series) -> pd.Series:
    X = sm.add_constant(ppg_acum.astype(float), has_constant="add")
    return modelo.predict(X)
