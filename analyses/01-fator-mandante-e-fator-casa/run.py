"""Análise 01 — fator mandante e fator casa na era pontos corridos (2003–2024).

Gera as tabelas e figuras em outputs/. Rode depois do pipeline de dados:

    python -m futebrasil.pipeline tudo
    python analyses/01-fator-mandante-e-fator-casa/run.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from futebrasil import metricas, modelos, tendencia
from futebrasil.limpeza import carregar_partidas, carregar_time_jogo
from futebrasil.lookups import estadio_meta, nome_exibicao

_ESTADIO_NOME = estadio_meta().set_index("estadio_id")["estadio"].to_dict()

AQUI = Path(__file__).parent
TAB = AQUI / "outputs" / "tables"
FIG = AQUI / "outputs" / "figures"

AZUL, VERM, CINZA = "#1f4e79", "#c0392b", "#8a8f98"
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})


def salvar_tabela(df: pd.DataFrame, nome: str) -> None:
    df.to_csv(TAB / nome, index=False, encoding="utf-8", float_format="%.4f")
    print(f"  tabela  {nome}  ({len(df)} linhas)")


def salvar_fig(fig, nome: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / nome, bbox_inches="tight")
    plt.close(fig)
    print(f"  figura  {nome}")


# --------------------------------------------------------------------------- #
def tabelas(partidas, longo):
    ag = metricas.liga_agregada(longo)
    salvar_tabela(ag, "agregado_liga.csv")

    lt = metricas.liga_por_temporada(longo)
    salvar_tabela(lt, "ano_a_ano_liga.csv")

    painel = metricas.painel_clube_temporada(longo)
    salvar_tabela(painel, "ano_a_ano_por_clube.csv")

    clube = metricas.clube_agregado(longo)
    mod_clube = modelos.efeito_mando_por_clube(partidas)
    clube = clube.merge(mod_clube[["clube", "fator_gols_mando", "p_valor"]], on="clube", how="left")
    salvar_tabela(clube, "agregado_por_clube.csv")

    tc = tendencia.tendencia_por_clube(painel)
    salvar_tabela(tc, "tendencia_por_clube.csv")

    fc = metricas.fator_casa_por_estadio(longo, min_jogos=15)
    salvar_tabela(fc, "fator_casa_por_estadio.csv")

    tce = tendencia.tendencia_por_estadio(longo)
    salvar_tabela(tce, "tendencia_por_clube_estadio.csv")

    salvar_tabela(modelos.efeito_mando_global(partidas), "modelo_efeito_mando_janela.csv")
    salvar_tabela(modelos.efeito_mando_sem_publico(partidas), "modelo_efeito_mando_sem_publico.csv")
    salvar_tabela(mod_clube, "modelo_efeito_mando_por_clube.csv")

    return dict(liga_ano=lt, painel=painel, clube=clube, tend_clube=tc, fator_casa=fc)


# --------------------------------------------------------------------------- #
def fig_liga_ano(lt):
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.axvspan(2019.5, 2021.5, color=CINZA, alpha=0.15, lw=0)
    ax.plot(lt["temporada"], lt["vantagem_ppg"], "-o", color=AZUL, lw=2,
            label="vantagem de mando (pts/jogo casa − fora)")
    media = np.average(lt["vantagem_ppg"], weights=lt["n_casa"])
    ax.axhline(media, color=VERM, ls="--", lw=1, label=f"média do período = {media:.2f}")
    z = np.polyfit(lt["temporada"], lt["vantagem_ppg"], 1)
    ax.plot(lt["temporada"], np.polyval(z, lt["temporada"]), color=VERM, lw=1.4,
            label=f"tendência linear ({z[0]*10:+.2f}/década)")
    ax.set_xlabel("temporada"); ax.set_ylabel("pontos por jogo")
    ax.set_title("Fator mandante na Série A ano a ano — pontos corridos")
    ax.text(2020.5, ax.get_ylim()[0] + 0.03, "pandemia\n(sem público)",
            ha="center", va="bottom", fontsize=8, color=CINZA)
    ax.legend(fontsize=8, loc="upper right")
    salvar_fig(fig, "01_liga_fator_mandante_ano_a_ano.png")


def fig_modelo_janela(partidas):
    mj = modelos.efeito_mando_global(partidas)
    mj = mj[mj["janela"] != "2003-2024"]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    y = np.arange(len(mj))
    ax.hlines(y, mj["ic95_baixo"], mj["ic95_alto"], color=AZUL, lw=3, alpha=0.5)
    ax.plot(mj["fator_gols_mando"], y, "o", color=AZUL)
    ax.axvline(1.0, color=CINZA, lw=1)
    ax.set_yticks(y); ax.set_yticklabels(mj["janela"])
    ax.set_xlabel("fator multiplicativo nos gols do mandante (modelo de Poisson, ajustado ao adversário)")
    ax.set_title("O empurrão do mando encolheu — gols marcados em casa")
    salvar_fig(fig, "02_modelo_efeito_mando_por_janela.png")


def fig_ranking_clubes(clube):
    d = clube[clube["n_casa"] >= 150].sort_values("vantagem_ppg")
    fig, ax = plt.subplots(figsize=(8, max(4, 0.32 * len(d))))
    ax.barh(d["clube"].map(nome_exibicao), d["vantagem_ppg"], color=AZUL)
    ax.axvline(d["vantagem_ppg"].mean(), color=VERM, ls="--", lw=1)
    ax.set_xlabel("vantagem de mando (pts/jogo), 2003–2024")
    ax.set_title("Quem mais aproveitou jogar em casa (clubes com ≥150 jogos de mando)")
    salvar_fig(fig, "03_ranking_clubes_fator_mandante.png")


def fig_small_multiples(painel, tend_clube):
    clubes = tend_clube.sort_values("inclinacao_por_decada")["clube"].tolist()
    ncol = 4
    nrow = int(np.ceil(len(clubes) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(3 * ncol, 2 * nrow), sharex=True, sharey=True)
    for ax, clube in zip(axes.flat, clubes):
        g = painel[painel["clube"] == clube]
        ax.axhline(0, color=CINZA, lw=0.6)
        ax.plot(g["temporada"], g["vantagem_ppg"], "-", color=AZUL, lw=1, alpha=0.8)
        if len(g) >= 3:
            z = np.polyfit(g["temporada"], g["vantagem_ppg"], 1)
            ax.plot(g["temporada"], np.polyval(z, g["temporada"]), color=VERM, lw=1.4)
        classe = tend_clube.loc[tend_clube["clube"] == clube, "classe"].iloc[0]
        ax.set_title(f"{nome_exibicao(clube)} · {classe}", fontsize=8)
    for ax in axes.flat[len(clubes):]:
        ax.set_visible(False)
    fig.suptitle("Fator mandante por clube, ano a ano (linha vermelha = tendência)", y=1.005)
    salvar_fig(fig, "04_tendencia_por_clube_small_multiples.png")


def fig_troca_de_casa(fator_casa):
    trocaram = fator_casa.groupby("clube").filter(lambda g: g["estadio_id"].nunique() >= 2)
    trocaram = trocaram.sort_values(["clube", "temporada_ini"])
    ordem_clubes = trocaram.groupby("clube")["temporada_ini"].min().sort_values().index

    rotulos, valores, cores, divisores = [], [], [], []
    paleta = [AZUL, VERM, CINZA]
    for clube in ordem_clubes:
        g = trocaram[trocaram["clube"] == clube]
        for k, (_, r) in enumerate(g.iterrows()):
            est = _ESTADIO_NOME.get(r["estadio_id"], r["estadio_id"])
            rotulos.append(f"{nome_exibicao(clube)} — {est}  ({r['temporada_ini']}–{r['temporada_fim']}, {r['n_jogos_casa']}j)")
            valores.append(r["vantagem_ppg"])
            cores.append(paleta[min(k, 2)])
        divisores.append(len(rotulos) - 0.5)

    y = np.arange(len(rotulos))
    fig, ax = plt.subplots(figsize=(9.5, max(4, 0.34 * len(rotulos))))
    ax.barh(y, valores, color=cores)
    for d in divisores[:-1]:
        ax.axhline(d, color="white", lw=2)
    ax.axvline(0, color=CINZA, lw=1)
    ax.set_yticks(y); ax.set_yticklabels(rotulos, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("vantagem de mando naquela praça (pts/jogo vs. o mesmo clube fora, mesmas temporadas)")
    ax.set_title("Fator casa por estádio — clubes que trocaram de casa (2003–2024)")
    salvar_fig(fig, "05_fator_casa_troca_de_estadio.png")


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    partidas = carregar_partidas()
    longo = carregar_time_jogo()

    print("tabelas:")
    d = tabelas(partidas, longo)

    print("figuras:")
    fig_liga_ano(d["liga_ano"])
    fig_modelo_janela(partidas)
    fig_ranking_clubes(d["clube"])
    fig_small_multiples(d["painel"], d["tend_clube"])
    fig_troca_de_casa(d["fator_casa"])
    print("ok")


if __name__ == "__main__":
    main()
