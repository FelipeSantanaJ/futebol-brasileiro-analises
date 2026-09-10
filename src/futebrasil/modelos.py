"""Efeito de mando ajustado ao adversário (modelo de gols de Poisson).

Cada partida vira duas linhas (uma por clube). O número de gols marcados é
modelado como:

    gols ~ força de ataque do time + força de defesa do adversário + mando

com dummies de time. O coeficiente de `mando` (exponenciado) é o fator
multiplicativo nos gols quando se joga em casa, já descontada a qualidade dos
dois times. É o número "controlado" que acompanha o split descritivo de ppg.

Rodamos por janelas (blocos de temporadas) para ver o efeito encolher no tempo,
e uma versão com interação time×mando para o efeito por clube.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

_POISSON = sm.families.Poisson()


def _linhas_time(partidas: pd.DataFrame) -> pd.DataFrame:
    p = partidas.dropna(subset=["gols_mandante", "gols_visitante"]).copy()
    casa = pd.DataFrame({
        "temporada": p["temporada"],
        "time": p["clube_mandante"], "adv": p["clube_visitante"],
        "gols": p["gols_mandante"].astype(int), "mando": 1,
        "sem_publico": p["sem_publico"].astype(int),
    })
    fora = pd.DataFrame({
        "temporada": p["temporada"],
        "time": p["clube_visitante"], "adv": p["clube_mandante"],
        "gols": p["gols_visitante"].astype(int), "mando": 0,
        "sem_publico": p["sem_publico"].astype(int),
    })
    return pd.concat([casa, fora], ignore_index=True)


def efeito_mando_global(partidas: pd.DataFrame, janelas: list[tuple[int, int]] | None = None) -> pd.DataFrame:
    """Fator multiplicativo de gols do mando, geral e por janela de temporadas."""
    if janelas is None:
        janelas = [(2003, 2024), (2003, 2008), (2009, 2014),
                   (2015, 2019), (2020, 2021), (2022, 2024)]
    linhas = []
    for ini, fim in janelas:
        d = _linhas_time(partidas.query("@ini <= temporada <= @fim"))
        fit = smf.glm("gols ~ C(time) + C(adv) + mando", data=d, family=_POISSON).fit()
        coef = fit.params["mando"]
        se = fit.bse["mando"]
        linhas.append({
            "janela": f"{ini}-{fim}",
            "n_jogos": len(d) // 2,
            "fator_gols_mando": np.exp(coef),
            "ic95_baixo": np.exp(coef - 1.96 * se),
            "ic95_alto": np.exp(coef + 1.96 * se),
            "coef": coef, "se": se, "p_valor": fit.pvalues["mando"],
        })
    return pd.DataFrame(linhas)


def efeito_mando_sem_publico(partidas: pd.DataFrame) -> pd.DataFrame:
    """Compara o efeito de mando com e sem público (interação mando×sem_publico)."""
    d = _linhas_time(partidas.query("2019 <= temporada <= 2022"))
    fit = smf.glm("gols ~ C(time) + C(adv) + mando * sem_publico",
                  data=d, family=_POISSON).fit()
    termos = ["mando", "mando:sem_publico"]
    return pd.DataFrame({
        "termo": termos,
        "coef": [fit.params[t] for t in termos],
        "fator": [np.exp(fit.params[t]) for t in termos],
        "p_valor": [fit.pvalues[t] for t in termos],
    })


def efeito_mando_por_clube(partidas: pd.DataFrame, min_jogos: int = 80) -> pd.DataFrame:
    """Efeito de mando por clube, via interação C(time):mando."""
    d = _linhas_time(partidas)
    freq = d[d["mando"] == 1]["time"].value_counts()
    manter = freq[freq >= min_jogos].index
    d = d[d["time"].isin(manter) & d["adv"].isin(manter)].copy()

    fit = smf.glm("gols ~ C(time) + C(adv) + C(time):mando",
                  data=d, family=_POISSON).fit()

    import re

    linhas = []
    for termo in fit.params.index:
        if "mando" not in termo or ":" not in termo:
            continue
        m = re.search(r"\[T?\.?([^\]]+)\]", termo)
        if not m:
            continue
        clube = m.group(1)
        coef, se = fit.params[termo], fit.bse[termo]
        linhas.append({
            "clube": clube,
            "fator_gols_mando": np.exp(coef),
            "ic95_baixo": np.exp(coef - 1.96 * se),
            "ic95_alto": np.exp(coef + 1.96 * se),
            "p_valor": fit.pvalues[termo],
        })
    return pd.DataFrame(linhas).sort_values("fator_gols_mando", ascending=False).reset_index(drop=True)
