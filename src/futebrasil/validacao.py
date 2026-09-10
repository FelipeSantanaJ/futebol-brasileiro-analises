"""Checagens de sanidade sobre a base tratada.

Reconstrói a classificação de cada edição a partir dos jogos e confere:
  - nº de jogos por edição bate com a grade;
  - cada clube jogou 2·(N−1) partidas (turno e returno completos);
  - gols de mandante somam igual pelos dois lados;
  - o campeão reconstruído bate com uma lista de referência conhecida.

Grava data/processed/validacao_temporadas.csv.
"""
from __future__ import annotations

import pandas as pd

from .caminhos import PROCESSADO

# campeões inequívocos, para bater o ponteiro (fonte: registros oficiais da CBF / Wikipédia)
CAMPEOES_REF = {
    2003: "cruzeiro", 2004: "santos", 2005: "corinthians", 2006: "sao-paulo",
    2007: "sao-paulo", 2008: "sao-paulo", 2009: "flamengo", 2010: "fluminense",
    2011: "corinthians", 2012: "fluminense", 2013: "cruzeiro", 2014: "cruzeiro",
    2015: "corinthians", 2016: "palmeiras", 2017: "corinthians", 2018: "palmeiras",
    2019: "flamengo", 2020: "flamengo", 2021: "atletico-mg", 2022: "palmeiras",
    2023: "palmeiras", 2024: "botafogo-rj",
}


def classificacao(longo: pd.DataFrame, temporada: int) -> pd.DataFrame:
    g = longo[longo["temporada"] == temporada]
    tab = g.groupby("clube").agg(
        J=("pts", "size"), P=("pts", "sum"),
        V=("vitoria", "sum"), E=("empate", "sum"), D=("derrota", "sum"),
        GP=("gols_pro", "sum"), GC=("gols_contra", "sum"),
    )
    tab["SG"] = tab["GP"] - tab["GC"]
    return tab.sort_values(["P", "V", "SG", "GP"], ascending=False)


def validar(longo: pd.DataFrame, partidas: pd.DataFrame, salvar: bool = True) -> pd.DataFrame:
    linhas = []
    for temporada in sorted(longo["temporada"].unique()):
        g = longo[longo["temporada"] == temporada]
        p = partidas[partidas["temporada"] == temporada]
        tab = classificacao(longo, temporada)
        n_clubes = g["clube"].nunique()
        jogos_por_clube = g.groupby("clube").size()
        campeao = tab.index[0]
        ref = CAMPEOES_REF.get(temporada)
        linhas.append({
            "temporada": temporada,
            "n_jogos": len(p),
            "n_clubes": n_clubes,
            "jogos_clube_min": int(jogos_por_clube.min()),
            "jogos_clube_max": int(jogos_por_clube.max()),
            "turno_returno_completo": bool((jogos_por_clube == 2 * (n_clubes - 1)).all()),
            "gols_batem": int(p["gols_mandante"].sum()) == int(g[g["mandante"]]["gols_pro"].sum()),
            "campeao_reconstruido": campeao,
            "pts_campeao": int(tab.iloc[0]["P"]),
            "campeao_ref": ref,
            "bate_campeao": (ref is None) or (campeao == ref),
        })
    out = pd.DataFrame(linhas)
    if salvar:
        out.to_csv(PROCESSADO / "validacao_temporadas.csv", index=False, encoding="utf-8")
        print(f"[validação] {PROCESSADO / 'validacao_temporadas.csv'}")
    falhas = out[~out["bate_campeao"] | ~out["gols_batem"]]
    if len(falhas):
        print("[validação] DIVERGÊNCIAS:")
        print(falhas.to_string(index=False))
    else:
        print("[validação] todas as edições batem com a referência")
    return out


if __name__ == "__main__":
    from .limpeza import carregar_partidas, carregar_time_jogo

    validar(carregar_time_jogo(), carregar_partidas())
