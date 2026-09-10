"""O fator está subindo ou caindo? Inclinação por clube (e por clube/estádio).

Para cada série (clube ao longo das temporadas) ajustamos uma reta por mínimos
quadrados ponderados — peso = nº de jogos de mando naquele ano — da métrica de
vantagem contra a temporada (centrada). A classificação usa o IC 95% da
inclinação:

  Subindo   IC inteiramente > 0
  Caindo    IC inteiramente < 0
  Estável   IC cruza o zero

A inclinação é reportada por década (×10) por ser mais legível.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def _ajustar(series_x: np.ndarray, series_y: np.ndarray, pesos: np.ndarray) -> dict:
    x = series_x - series_x.mean()
    X = sm.add_constant(x)
    modelo = sm.WLS(series_y, X, weights=pesos).fit()
    params = np.asarray(modelo.params)
    pvalues = np.asarray(modelo.pvalues)
    inc = params[1]
    ic_low, ic_high = np.asarray(modelo.conf_int())[1]
    if ic_low > 0:
        classe = "Subindo"
    elif ic_high < 0:
        classe = "Caindo"
    else:
        classe = "Estável"
    theil = _theil_sen(x, series_y)
    return {
        "inclinacao_por_temporada": inc,
        "inclinacao_por_decada": inc * 10,
        "ic95_baixo_decada": ic_low * 10,
        "ic95_alto_decada": ic_high * 10,
        "p_valor": pvalues[1],
        "r2": modelo.rsquared,
        "classe": classe,
        "inclinacao_theil_sen_decada": theil * 10 if theil is not None else np.nan,
        "media_metrica": np.average(series_y, weights=pesos),
        "n_temporadas": len(series_y),
    }


def _theil_sen(x: np.ndarray, y: np.ndarray):
    try:
        from scipy.stats import theilslopes
    except ImportError:
        return None
    if len(x) < 3:
        return None
    return theilslopes(y, x)[0]


def tendencia_por_clube(
    painel: pd.DataFrame, metrica: str = "vantagem_ppg", min_temporadas: int = 6
) -> pd.DataFrame:
    linhas = []
    for clube, g in painel.groupby("clube"):
        g = g.dropna(subset=[metrica, "n_casa"])
        if len(g) < min_temporadas:
            continue
        res = _ajustar(g["temporada"].to_numpy(float), g[metrica].to_numpy(float),
                       g["n_casa"].to_numpy(float))
        res["clube"] = clube
        res["temporada_ini"] = int(g["temporada"].min())
        res["temporada_fim"] = int(g["temporada"].max())
        linhas.append(res)
    cols = ["clube", "temporada_ini", "temporada_fim", "n_temporadas", "media_metrica",
            "inclinacao_por_decada", "ic95_baixo_decada", "ic95_alto_decada",
            "inclinacao_theil_sen_decada", "p_valor", "r2", "classe",
            "inclinacao_por_temporada"]
    return pd.DataFrame(linhas)[cols].sort_values("inclinacao_por_decada").reset_index(drop=True)


def tendencia_liga(liga_ano: pd.DataFrame, metrica: str = "vantagem_ppg") -> pd.Series:
    g = liga_ano.dropna(subset=[metrica])
    res = _ajustar(g["temporada"].to_numpy(float), g[metrica].to_numpy(float),
                   g["n_casa"].to_numpy(float))
    res["metrica"] = metrica
    return pd.Series(res)


def tendencia_por_estadio(
    longo: pd.DataFrame, metrica: str = "vantagem_ppg", min_temporadas: int = 4
) -> pd.DataFrame:
    """Painel (clube, estádio, temporada) e a inclinação da vantagem em cada casa.

    Vantagem no ano = ppg de mando naquele estádio − ppg do clube como visitante
    na mesma temporada.
    """
    mand = longo[longo["mandante"] & ~longo["mando_fora_de_casa"]]
    fora = longo[~longo["mandante"]]

    base_fora = (
        fora.groupby(["clube", "temporada"])["pts"].mean().rename("ppg_fora_ano").reset_index()
    )
    ct = (
        mand.groupby(["clube", "estadio_id", "temporada"])
        .agg(n_casa=("pts", "size"), ppg_casa=("pts", "mean"))
        .reset_index()
        .merge(base_fora, on=["clube", "temporada"], how="left")
    )
    ct["vantagem_ppg"] = ct["ppg_casa"] - ct["ppg_fora_ano"]

    linhas = []
    for (clube, estadio_id), g in ct.groupby(["clube", "estadio_id"]):
        g = g.dropna(subset=[metrica, "n_casa"])
        if len(g) < min_temporadas:
            continue
        res = _ajustar(g["temporada"].to_numpy(float), g[metrica].to_numpy(float),
                       g["n_casa"].to_numpy(float))
        res.update({
            "clube": clube, "estadio_id": estadio_id,
            "temporada_ini": int(g["temporada"].min()),
            "temporada_fim": int(g["temporada"].max()),
        })
        linhas.append(res)
    if not linhas:
        return pd.DataFrame()
    cols = ["clube", "estadio_id", "temporada_ini", "temporada_fim", "n_temporadas",
            "media_metrica", "inclinacao_por_decada", "ic95_baixo_decada",
            "ic95_alto_decada", "p_valor", "classe"]
    return pd.DataFrame(linhas)[cols].sort_values(["clube", "estadio_id"]).reset_index(drop=True)
