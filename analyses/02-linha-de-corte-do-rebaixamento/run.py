"""Análise 02 — linha de corte do rebaixamento e ritmo em pontos (2006–2024).

Gera as tabelas e figuras em outputs/. Rode depois do pipeline de dados:

    python -m futebrasil.pipeline tudo
    python analyses/02-linha-de-corte-do-rebaixamento/run.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from futebrasil import permanencia, tendencia
from futebrasil.limpeza import carregar_time_jogo
from futebrasil.validacao import classificacao
from futebrasil.lookups import nome_exibicao

AQUI = Path(__file__).parent
TAB = AQUI / "outputs" / "tables"
FIG = AQUI / "outputs" / "figures"

AZUL, VERM, CINZA, VERDE = "#1f4e79", "#c0392b", "#8a8f98", "#2e7d32"
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})

TEMPORADAS_TREINO = list(range(2006, 2024))  # exclui 2024, usada como caso de estudo
RODADAS_CORTE = [10, 15, 20, 25, 30, 35]
TEMPORADA_CASO = 2024
RODADA_CASO = 30
CLUBE_CASO = "corinthians"


def salvar_tabela(df: pd.DataFrame, nome: str) -> None:
    df.to_csv(TAB / nome, index=False, encoding="utf-8", float_format="%.4f")
    print(f"  tabela  {nome}  ({len(df)} linhas)")


def salvar_fig(fig, nome: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / nome, bbox_inches="tight")
    plt.close(fig)
    print(f"  figura  {nome}")


# --------------------------------------------------------------------------- #
def tabelas(longo: pd.DataFrame):
    seg = permanencia.linha_de_seguranca(longo)
    salvar_tabela(seg, "linha_de_seguranca_por_temporada.csv")

    tend = tendencia.ajustar_reta(
        seg["temporada"].to_numpy(float), seg["pts_17"].to_numpy(float)
    )
    salvar_tabela(pd.DataFrame([tend]), "tendencia_linha_de_seguranca.csv")

    painel = permanencia.painel_ritmo(longo, TEMPORADAS_TREINO, RODADAS_CORTE)
    salvar_tabela(painel, "painel_ritmo_temporada_clube.csv")

    modelos_tab = permanencia.modelos_por_rodada(painel, RODADAS_CORTE)
    salvar_tabela(modelos_tab, "modelo_ritmo_por_rodada.csv")

    loso = permanencia.validar_loso(painel, RODADAS_CORTE)
    salvar_tabela(loso, "validacao_fora_da_amostra.csv")

    # caso de estudo: modelo da rodada 30 treinado em 2006-2023, aplicado a 2024
    modelo_30, _ = permanencia.ajustar_modelo_rodada(painel, RODADA_CASO)
    longo24 = longo[longo["temporada"] == TEMPORADA_CASO]
    g24 = longo24.sort_values(["clube", "rodada"]).copy()
    g24["pts_acum"] = g24.groupby("clube")["pts"].cumsum()
    r30 = g24[g24["rodada"] == RODADA_CASO][["clube", "pts_acum"]].copy()
    r30["ppg_acum"] = r30["pts_acum"] / RODADA_CASO
    r30["p_rebaixamento"] = permanencia.aplicar_modelo(modelo_30, r30["ppg_acum"])
    tab24 = classificacao(longo24, TEMPORADA_CASO)
    piores4 = set(tab24.index[-4:])
    r30["rebaixado_real"] = r30["clube"].isin(piores4)
    r30["nome"] = r30["clube"].map(nome_exibicao)
    r30 = r30.sort_values("p_rebaixamento", ascending=False).reset_index(drop=True)
    salvar_tabela(r30, f"caso_{TEMPORADA_CASO}_rodada{RODADA_CASO}.csv")

    traj = permanencia.trajetoria_pontos(longo, TEMPORADA_CASO, CLUBE_CASO)
    salvar_tabela(traj, f"trajetoria_{CLUBE_CASO}_{TEMPORADA_CASO}.csv")

    return dict(seg=seg, tend=tend, painel=painel, modelos_tab=modelos_tab,
                loso=loso, r30=r30, traj=traj)


# --------------------------------------------------------------------------- #
def fig_linha_seguranca(seg: pd.DataFrame, tend: dict):
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.fill_between(seg["temporada"], seg["pts_17"], seg["pts_16"],
                     color=CINZA, alpha=0.18, label="zona cinzenta (16º a 17º)")
    ax.plot(seg["temporada"], seg["pts_17"], "-o", color=VERM, lw=1.8, ms=4,
            label="17º colocado (1º rebaixado)")
    ax.plot(seg["temporada"], seg["pts_16"], "-o", color=AZUL, lw=1.8, ms=4,
            label="16º colocado (última vaga)")
    media17 = seg["pts_17"].mean()
    ax.axhline(media17, color=VERM, ls="--", lw=1,
               label=f"média do 17º, 2006–2023 = {media17:.1f} pts")
    x = seg["temporada"].to_numpy(float)
    reta = tend["media_metrica"] + tend["inclinacao_por_temporada"] * (x - x.mean())
    ax.plot(x, reta, color=VERM, lw=1, alpha=0.5)
    ax.set_xlabel("temporada"); ax.set_ylabel("pontos em 38 rodadas")
    ax.set_title("Linha de corte do rebaixamento — Série A, era de 20 clubes (2006–2023)")
    ax.legend(fontsize=8, loc="lower right")
    salvar_fig(fig, "01_linha_de_seguranca_historica.png")


def fig_pontos_por_rodada(modelos_tab: pd.DataFrame, loso: pd.DataFrame, media17: float):
    m = modelos_tab.merge(loso, on="rodada")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

    ax1.plot(m["rodada"], m["pts_finais_50pct"], "-o", color=AZUL, lw=2)
    ax1.axhline(media17, color=VERM, ls="--", lw=1,
                label=f"média histórica do 17º = {media17:.1f} pts")
    ax1.set_xlabel("rodada de corte"); ax1.set_ylabel("pontos finais projetados (ritmo = 50% de risco)")
    ax1.set_title("Quantos pontos bastam, ao ritmo atual?")
    ax1.legend(fontsize=8)

    ax2.plot(m["rodada"], m["auc_loso"], "-o", color=VERDE, lw=2, label="AUC (fora da amostra)")
    ax2.set_ylim(0.5, 1.02)
    ax2.set_xlabel("rodada de corte"); ax2.set_ylabel("AUC")
    ax2.set_title("Poder preditivo do ritmo sozinho cresce com a rodada")
    ax2b = ax2.twinx()
    ax2b.plot(m["rodada"], m["brier_loso"], "-s", color=CINZA, lw=1.4, ms=4, label="Brier (eixo dir.)")
    ax2b.set_ylabel("Brier score", color=CINZA)
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="center right")

    salvar_fig(fig, "02_modelo_pontos_necessarios_por_rodada.png")


def fig_trajetoria_corinthians(traj: pd.DataFrame, seg: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.axhspan(0, seg["pts_17"].mean(), color=VERM, alpha=0.08)
    ax.axhline(seg["pts_17"].mean(), color=VERM, ls="--", lw=1,
               label=f"média histórica do 17º (2006–2023) = {seg['pts_17'].mean():.1f} pts")
    ax.axhline(seg["pts_16"].mean(), color=AZUL, ls=":", lw=1,
               label=f"média histórica do 16º (2006–2023) = {seg['pts_16'].mean():.1f} pts")
    ax.plot(traj["rodada"], traj["pts_acum"], "-o", color="#6a1b9a", lw=2, ms=3.5,
            label="Corinthians 2024 — pontos acumulados")
    ax.axvline(RODADA_CASO, color=CINZA, lw=1, ls="-")
    y30 = traj.loc[traj["rodada"] == RODADA_CASO, "pts_acum"].iloc[0]
    ax.annotate(f"rodada {RODADA_CASO}: {int(y30)} pts\n(modelo: ~50% de risco)",
                xy=(RODADA_CASO, y30), xytext=(RODADA_CASO - 9, y30 + 16),
                fontsize=8, color=CINZA,
                arrowprops=dict(arrowstyle="->", color=CINZA, lw=0.8))
    ax.set_xlabel("rodada"); ax.set_ylabel("pontos acumulados")
    ax.set_title("Corinthians 2024 — do sufoco à tranquilidade")
    ax.legend(fontsize=8, loc="upper left")
    salvar_fig(fig, "03_trajetoria_corinthians_2024.png")


def fig_pelotao_2024(r30: pd.DataFrame):
    d = r30[r30["pts_acum"] <= 40].sort_values("p_rebaixamento")
    cores = [VERM if x else AZUL for x in d["rebaixado_real"]]
    fig, ax = plt.subplots(figsize=(8.5, max(3.5, 0.42 * len(d))))
    y = np.arange(len(d))
    ax.barh(y, d["p_rebaixamento"] * 100, color=cores)
    ax.axvline(50, color=CINZA, lw=1, ls="--")
    for yi, (_, row) in zip(y, d.iterrows()):
        ax.text(row["p_rebaixamento"] * 100 + 1.5, yi,
                f"{int(row['pts_acum'])} pts", va="center", fontsize=8, color=CINZA)
    ax.set_yticks(y); ax.set_yticklabels(d["nome"])
    ax.set_xlabel("probabilidade de rebaixamento pelo modelo (rodada 30, %)")
    ax.set_title("Pelotão do rebaixamento em 2024 — modelo treinado em 2006–2023")
    ax.set_xlim(0, max(100, d["p_rebaixamento"].max() * 100 + 15))
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label="ficou (na Série A em 2025)"),
                       Patch(color=VERM, label="caiu para a Série B")],
              fontsize=8, loc="lower right")
    salvar_fig(fig, "04_pelotao_rebaixamento_2024_rodada30.png")


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    longo = carregar_time_jogo()

    print("tabelas:")
    d = tabelas(longo)

    print("figuras:")
    fig_linha_seguranca(d["seg"], d["tend"])
    fig_pontos_por_rodada(d["modelos_tab"], d["loso"], d["seg"]["pts_17"].mean())
    fig_trajetoria_corinthians(d["traj"], d["seg"])
    fig_pelotao_2024(d["r30"])
    print("ok")


if __name__ == "__main__":
    main()
