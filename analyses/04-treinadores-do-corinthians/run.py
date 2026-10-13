"""Análise 04 — treinadores do Corinthians na Série A (2003–2025).

Recorte da base de treinadores da análise 03 (data/external/treinadores/):
visão por técnico (completa, 20+ e 50+ jogos pelo clube) e visão por temporada,
com sequências (vitórias, derrotas, invicta, sem vencer e melhor/pior trecho de
10 jogos).

    python analyses/04-treinadores-do-corinthians/run.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from futebrasil import treinadores as tr

AQUI = Path(__file__).parent
TAB = AQUI / "outputs" / "tables"
FIG = AQUI / "outputs" / "figures"
CLUBE = "Corinthians"
CORTES = (None, 20, 50)

PRETO, CINZA, OURO, VERM = "#1b1b1b", "#8a8f98", "#b8862b", "#c0392b"
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})

# métrica, coluna (ou "max|min" para o trecho de 10 jogos)
FICHA = [("Aproveitamento", "aprov"), ("Jogos", "jogos"), ("Vitórias", "V"), ("Derrotas", "D"),
         ("Gols feitos", "GF"), ("Gols feitos por jogo", "GFj"), ("Gols sofridos", "GA"),
         ("Gols sofridos por jogo", "GAj"), ("Saldo de gols", "SG"), ("Saldo por jogo", "SGj"),
         ("Maior série de vitórias", "seq_vitorias"), ("Maior série de derrotas", "seq_derrotas"),
         ("Maior série invicta", "seq_invicta"), ("Maior série sem vencer", "seq_sem_vencer"),
         ("Aproveitamento em 10 jogos seguidos (melhor | pior trecho)", "melhor_10j|pior_10j")]


def salvar_tabela(df: pd.DataFrame, nome: str) -> None:
    df.to_csv(TAB / nome, index=False, encoding="utf-8", float_format="%.4f")
    print(f"  tabela  {nome}  ({len(df)} linhas)")


def salvar_fig(fig, nome: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / nome, bbox_inches="tight")
    plt.close(fig)
    print(f"  figura  {nome}")


def resumo(g: pd.DataFrame) -> dict:
    j = len(g); gf, ga = g["gols_feitos"].sum(), g["gols_sofridos"].sum()
    return dict(jogos=j, V=int((g.resultado == "V").sum()), E=int((g.resultado == "E").sum()),
                D=int((g.resultado == "D").sum()), pontos=int(g.pontos.sum()), aprov=g.pontos.sum() / (3 * j),
                GF=int(gf), GA=int(ga), SG=int(gf - ga), GFj=gf / j, GAj=ga / j, SGj=(gf - ga) / j)


def visao_tecnico(C: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por técnico; séries contam só jogos seguidos dentro de uma passagem."""
    linhas = []
    for t, g in C.groupby("treinador"):
        r = resumo(g); r["treinador"] = t
        seqs = [tr.series(list(p.resultado), list(p.pontos)) for _, p in g.groupby("passagem")]
        for k in ("seq_vitorias", "seq_derrotas", "seq_invicta", "seq_sem_vencer"):
            r[k] = max(s[k] for s in seqs)
        m10 = [s for s in seqs if not np.isnan(s["melhor_10j"])]
        r["melhor_10j"] = max(s["melhor_10j"] for s in m10) if m10 else np.nan
        r["pior_10j"] = min(s["pior_10j"] for s in m10) if m10 else np.nan
        r["passagens"] = g["passagem"].nunique()
        r["temporadas"] = ", ".join(str(a) for a in sorted(g.temporada.unique()))
        linhas.append(r)
    return pd.DataFrame(linhas).sort_values(["aprov", "jogos"], ascending=[False, False])


def visao_temporada(C: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for y, g in C.groupby("temporada"):
        r = resumo(g); r["temporada"] = y
        r.update(tr.series(list(g.resultado), list(g.pontos)))
        r["tecnicos"] = " > ".join(dict.fromkeys(g.treinador))
        linhas.append(r)
    return pd.DataFrame(linhas)


def lideres(df: pd.DataFrame, col: str, maior: bool, rotulo: str) -> tuple[str, float]:
    d = df.dropna(subset=[col])
    alvo = d[col].max() if maior else d[col].min()
    w = d[np.isclose(d[col], alvo)].sort_values("jogos", ascending=False)
    return " / ".join(f"{x} ({j}j)" for x, j in zip(w[rotulo], w["jogos"])), alvo


def ficha(df: pd.DataFrame, rotulo: str, pular: tuple[str, ...] = ()) -> pd.DataFrame:
    linhas = []
    for nome, col in FICHA:
        if col in pular:
            continue
        c1, c2 = col.split("|") if "|" in col else (col, col)
        (n_mais, v_mais), (n_menos, v_menos) = lideres(df, c1, True, rotulo), lideres(df, c2, False, rotulo)
        linhas.append(dict(metrica=nome, mais=n_mais, valor_mais=v_mais, menos=n_menos, valor_menos=v_menos))
    return pd.DataFrame(linhas)


def figuras(T: pd.DataFrame, S: pd.DataFrame, C: pd.DataFrame) -> None:
    # 1. aproveitamento por temporada, com o técnico de mais jogos no ano
    principal = C.groupby(["temporada", "treinador"]).size().reset_index(name="j").sort_values("j").groupby("temporada").tail(1).set_index("temporada").treinador
    fig, ax = plt.subplots(figsize=(12, 5))
    cor = np.where(S["aprov"] >= 0.5, PRETO, CINZA)
    ax.bar(S["temporada"].astype(str), S["aprov"] * 100, color=cor)
    for x, v in zip(S["temporada"], S["aprov"]):
        ax.text(str(x), v * 100 + 0.8, principal[x], rotation=90, ha="center", va="bottom", fontsize=7.5)
    ax.set_ylim(0, 100); ax.set_ylabel("aproveitamento (%)")
    ax.set_title("Corinthians na Série A — aproveitamento por temporada
(preto: 50% ou mais; rótulo: técnico com mais jogos no ano; 2008 o clube estava na Série B)")
    ax.tick_params(axis="x", rotation=90)
    salvar_fig(fig, "01_aproveitamento_por_temporada.png")

    # 2. técnicos com 20+ jogos
    d = T[T["jogos"] >= 20].sort_values("aprov")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(d["treinador"] + " (" + d["jogos"].astype(str) + " j)", d["aprov"] * 100,
            color=np.where(d["jogos"] >= 50, OURO, PRETO))
    ax.set_xlabel("aproveitamento (%)"); ax.set_xlim(30, 75); ax.grid(axis="y", visible=False)
    ax.set_title("Técnicos com 20+ jogos pelo Corinthians (dourado: 50+ jogos)")
    salvar_fig(fig, "02_tecnicos_20_jogos.png")

    # 3. linha do tempo dos técnicos (jogos em sequência)
    C2 = C.reset_index(drop=True)
    pas = C2.groupby("passagem").agg(treinador=("treinador", "first"), ini=("data", "min"), j=("data", "size"))
    pas["x0"] = C2.groupby("passagem").apply(lambda g: g.index.min())
    top = T[T["jogos"] >= 20]["treinador"].tolist()
    fig, ax = plt.subplots(figsize=(13, 3.6))
    cores = plt.cm.tab20(np.linspace(0, 1, len(top)))
    mapa = dict(zip(top, cores))
    for x in pas.itertuples():
        ax.barh(0, x.j, left=x.x0, color=mapa.get(x.treinador, "#d0d0d0"), edgecolor="white", linewidth=0.4)
        if x.j >= 25:
            ax.text(x.x0 + x.j / 2, 0, x.treinador.split()[0], ha="center", va="center", fontsize=7.5, color="white")
    anos = C2.groupby("temporada").apply(lambda g: g.index.min())
    ax.set_xticks(anos.values); ax.set_xticklabels(anos.index, rotation=90, fontsize=8)
    ax.set_yticks([]); ax.set_xlim(0, len(C2)); ax.grid(False)
    ax.set_title("Quem esteve no banco em cada um dos 856 jogos (cinza: técnicos com menos de 20 jogos)")
    salvar_fig(fig, "03_linha_do_tempo_dos_tecnicos.png")


def main() -> None:
    TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    C = tr.carregar()
    C = C[C["clube"] == CLUBE].sort_values(["data", "tm_id_jogo"]).reset_index(drop=True)
    C["passagem"] = (C["treinador"] != C["treinador"].shift()).cumsum()
    print(f"{len(C)} jogos, {C.temporada.nunique()} temporadas, {C.treinador.nunique()} técnicos, {C.passagem.nunique()} passagens")
    salvar_tabela(C.drop(columns=["clube_nome_epoca"], errors="ignore"), "jogos_corinthians.csv")

    T = visao_tecnico(C)
    salvar_tabela(T, "tecnicos.csv")
    for m in CORTES:
        d = T if m is None else T[T["jogos"] >= m]
        salvar_tabela(ficha(d, "treinador"), f"ficha_tecnicos_{'todos' if m is None else f'min{m}'}.csv")

    S = visao_temporada(C)
    salvar_tabela(S, "temporadas.csv")
    salvar_tabela(ficha(S, "temporada", pular=("jogos",)), "ficha_temporadas.csv")

    figuras(T, S, C)


if __name__ == "__main__":
    main()
