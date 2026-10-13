"""Análise 03 — treinadores da Série A (2003–2025).

Lê a base treinador × partida já validada (data/external/treinadores/) e gera
as tabelas e figuras em outputs/. A base é montada pela coleta em coleta/
(ver coleta/README.md); este script não acessa a internet.

    python analyses/03-treinadores-da-serie-a/run.py
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

AZUL, VERM, CINZA, VERDE, LARANJA = "#1f4e79", "#c0392b", "#8a8f98", "#2e7d32", "#d9822b"
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})

CORTES_CARREIRA = (20, 50, 100)   # mínimos de jogos para rankings de carreira
MIN_ANO = 5                       # mínimo de jogos na temporada
MIN_MANDO = 10                    # mínimo de jogos em casa e fora
MIN_CLUBE = 20                    # mínimo de jogos no clube (versão A)
METRICAS = [  # (nome, coluna, maior_é_melhor)
    ("aproveitamento", "aprov", True), ("vitorias", "V", True), ("pct_vitorias", "pctV", True),
    ("derrotas", "D", False), ("pct_derrotas", "pctD", False),
    ("gols_feitos", "GF", True), ("gols_feitos_por_jogo", "GFj", True),
    ("gols_sofridos", "GA", False), ("gols_sofridos_por_jogo", "GAj", False),
]


def salvar_tabela(df: pd.DataFrame, nome: str) -> None:
    df.to_csv(TAB / nome, index=False, encoding="utf-8", float_format="%.4f")
    print(f"  tabela  {nome}  ({len(df)} linhas)")


def salvar_fig(fig, nome: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / nome, bbox_inches="tight")
    plt.close(fig)
    print(f"  figura  {nome}")


# --------------------------------------------------------------------------- #
def rankings_carreira(H: pd.DataFrame) -> pd.DataFrame:
    """Top 20 e bottom 20 de cada métrica, para cada corte de jogos (formato longo)."""
    linhas = []
    for minimo in CORTES_CARREIRA:
        for nome, col, _ in METRICAS:
            for lado, cres in (("maior", False), ("menor", True)):
                r = tr.ranquear(H, col, cres, 20, minimo)
                for x in r.itertuples():
                    linhas.append(dict(minimo_jogos=minimo, metrica=nome, lado=lado, pos=x.pos, empate=x.empate,
                                       treinador=x.treinador, jogos=x.jogos, V=x.V, E=x.E, D=x.D,
                                       valor=getattr(x, col), aprov=x.aprov))
    return pd.DataFrame(linhas)


def extremos_por_grupo(df: pd.DataFrame, grupo: str, minimo: int, rotulo: str = "treinador") -> pd.DataFrame:
    """Para cada grupo (temporada, clube...), o maior e o menor valor de cada métrica (empates juntos)."""
    linhas = []
    for chave, g in df[df["jogos"] >= minimo].groupby(grupo):
        linha = {grupo: chave, "elegiveis": len(g)}
        for nome, col, _ in METRICAS:
            for lado, cres in (("maior", False), ("menor", True)):
                r = tr.ranquear(g, col, cres, 1)
                linha[f"{nome}_{lado}"] = " / ".join(f"{t} ({v:.3f}, {j}j)" if isinstance(v, float) else f"{t} ({v}, {j}j)"
                                                     for t, v, j in zip(r[rotulo], r[col], r["jogos"]))
        linhas.append(linha)
    return pd.DataFrame(linhas)


def por_clube(TC: pd.DataFrame, temporadas_clube: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clubes com 5+ temporadas. Versão A: mínimo 20 jogos no clube. Versão B: mínimo 50,
    recuando para 40/30/20/10 enquanto o clube não tiver pelo menos 2 técnicos elegíveis."""
    clubes = sorted(temporadas_clube[temporadas_clube >= 5].index)
    a, b = [], []
    for cl in clubes:
        g = TC[TC["clube"] == cl]
        a.append(g[g["jogos"] >= MIN_CLUBE].assign(minimo_usado=MIN_CLUBE))
        for m in (50, 40, 30, 20, 10):
            q = g[g["jogos"] >= m]
            if len(q) >= 2:
                break
        b.append(q.assign(minimo_usado=m))
    A = pd.concat(a); B = pd.concat(b)
    A = extremos_por_grupo(A, "clube", MIN_CLUBE).merge(A.groupby("clube").minimo_usado.first().reset_index())
    B = extremos_por_grupo(B, "clube", 0).merge(B.groupby("clube").minimo_usado.first().reset_index())
    return A, B


def casa_fora(df: pd.DataFrame) -> pd.DataFrame:
    hc = tr.agregar(df[df["casa_fora"] == "casa"], ["treinador_id", "treinador"]).set_index("treinador_id")
    hf = tr.agregar(df[df["casa_fora"] == "fora"], ["treinador_id", "treinador"]).set_index("treinador_id")
    cf = hc[["treinador", "jogos", "aprov", "GFj", "GAj"]].join(
        hf[["jogos", "aprov", "GFj", "GAj"]], lsuffix="_casa", rsuffix="_fora", how="inner")
    cf = cf[(cf["jogos_casa"] >= MIN_MANDO) & (cf["jogos_fora"] >= MIN_MANDO)].reset_index()
    cf["dif_aprov"] = cf["aprov_casa"] - cf["aprov_fora"]
    cf["dif_GFj"] = cf["GFj_casa"] - cf["GFj_fora"]
    cf["dif_GAj"] = cf["GAj_casa"] - cf["GAj_fora"]
    return cf.sort_values("dif_aprov")


# --------------------------------------------------------------------------- #
def figuras(A0: pd.DataFrame, H: pd.DataFrame, CT: pd.DataFrame, CF: pd.DataFrame) -> None:
    # 1. qualidade da base por temporada
    st = A0.groupby(["temporada", "status_atribuicao"]).size().unstack(fill_value=0)
    st = st.div(st.sum(axis=1), axis=0) * 100
    ordem = [c for c in ["confirmado", "provável", "inferido", "ambíguo", "sem_treinador"] if c in st]
    cores = {"confirmado": AZUL, "provável": "#7fa7c9", "inferido": LARANJA, "ambíguo": VERM, "sem_treinador": "#333333"}
    fig, ax = plt.subplots(figsize=(11, 4.2))
    base = np.zeros(len(st))
    for c in ordem:
        ax.bar(st.index, st[c], bottom=base, color=cores[c], label=c, width=0.8)
        base += st[c].to_numpy()
    ax.set_ylim(70, 100); ax.set_ylabel("% dos jogos-lado")
    ax.set_title("Status da atribuição de treinador por temporada (eixo a partir de 70%)")
    ax.legend(ncol=5, fontsize=8, loc="lower left"); ax.set_xticks(st.index); ax.tick_params(axis="x", rotation=90)
    salvar_fig(fig, "01_qualidade_da_base_por_temporada.png")

    # 2. aproveitamento x jogos (20+), destacando quem tem 100+
    d = H[H["jogos"] >= 20]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(d["jogos"], d["aprov"] * 100, s=18, color=CINZA, alpha=0.7)
    media = A0["pontos"].sum() / (3 * len(A0)) * 100
    ax.axhline(media, color=CINZA, lw=1, ls="--"); ax.text(21, media + 0.6, f"média da liga {media:.1f}%", fontsize=8, color=CINZA)
    nomes = {"Abel Ferreira", "Muricy Ramalho", "Tite", "Cuca", "Vagner Mancini", "Gilson Kleina", "Dorival Júnior", "Levir Culpi"}
    destaque = d[d["treinador"].isin(nomes) | (d["aprov"] >= 0.6) | (d["aprov"] <= 0.27)]
    for x in destaque.itertuples():
        ax.annotate(x.treinador, (x.jogos, x.aprov * 100), fontsize=7.5, xytext=(3, 3), textcoords="offset points")
    ax.scatter(destaque["jogos"], destaque["aprov"] * 100, s=22, color=AZUL)
    ax.set_xscale("log"); ax.set_xticks([20, 50, 100, 200, 400, 600]); ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter()); ax.minorticks_off(); ax.set_xlabel("jogos na Série A 2003–2025 (escala log)"); ax.set_ylabel("aproveitamento (%)")
    ax.set_title("Aproveitamento × número de jogos — treinadores com 20+ jogos")
    salvar_fig(fig, "02_aproveitamento_x_jogos.png")

    # 3. ranking de aproveitamento, 100+ jogos
    d = tr.ranquear(H, "aprov", False, None, 100).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 11))
    cor = np.where(d["aprov"] >= media / 100, AZUL, VERM)
    ax.barh(d["treinador"] + " (" + d["jogos"].astype(str) + " j)", d["aprov"] * 100, color=cor)
    ax.axvline(media, color=CINZA, ls="--", lw=1)
    ax.set_xlabel("aproveitamento (%)"); ax.set_xlim(30, 66)
    ax.set_title("Aproveitamento na carreira — treinadores com 100+ jogos\n(azul: acima da média da liga; vermelho: abaixo)")
    ax.grid(axis="y", visible=False)
    salvar_fig(fig, "03_aproveitamento_100_jogos.png")

    # 4. campeonato de treinadores: títulos e rebaixamentos
    cnt = CT.groupby("treinador").agg(titulos=("campeao", "sum"), rebaixamentos=("rebaixado", "sum"))
    t = cnt[cnt["titulos"] > 0].sort_values(["titulos"], ascending=True).tail(12)
    r = cnt[cnt["rebaixamentos"] >= 2].sort_values("rebaixamentos", ascending=True)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 6))
    a1.barh(t.index, t["titulos"], color=AZUL); a1.set_title("Títulos no campeonato de treinadores")
    a2.barh(r.index, r["rebaixamentos"], color=VERM); a2.set_title("Rebaixamentos (2+)")
    for a in (a1, a2):
        a.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True)); a.grid(axis="y", visible=False)
    fig.suptitle("Campeonato de treinadores por aproveitamento (10+ jogos no ano; 4 piores rebaixados)", fontsize=11)
    salvar_fig(fig, "04_campeonato_titulos_e_rebaixamentos.png")

    # 5. casa x fora
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(CF["aprov_fora"] * 100, CF["aprov_casa"] * 100, s=18, color=AZUL, alpha=0.7)
    lim = [0, 100]; ax.plot(lim, lim, color=CINZA, lw=1, label="casa = fora"); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.plot(lim, [x + CF["dif_aprov"].mean() * 100 for x in lim], color=LARANJA, lw=1, ls="--",
            label=f"média: +{CF['dif_aprov'].mean() * 100:.1f} p.p. em casa")
    for x in pd.concat([CF.head(4), CF.tail(4), CF[CF.treinador == "Jorge Jesus"]]).itertuples():
        ax.annotate(x.treinador, (x.aprov_fora * 100, x.aprov_casa * 100), fontsize=7.5, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("aproveitamento fora (%)"); ax.set_ylabel("aproveitamento em casa (%)")
    ax.set_title("Casa × fora — treinadores com 10+ jogos em cada mando"); ax.legend(fontsize=8)
    salvar_fig(fig, "05_casa_x_fora.png")


# --------------------------------------------------------------------------- #
def main() -> None:
    TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    A0 = tr.carregar(incluir_desconhecidos=True)
    A = tr.carregar()

    H = tr.agregar(A, ["treinador_id", "treinador"])
    CT = tr.campeonato(A)
    cnt = CT.groupby("treinador_id").agg(temporadas_10j=("temporada", "size"), titulos=("campeao", "sum"),
                                         vices=("vice", "sum"), top4=("top4", "sum"), rebaixamentos=("rebaixado", "sum"),
                                         melhor_posicao=("posicao", "min")).reset_index()
    comp = H.merge(cnt, on="treinador_id", how="left").fillna({"temporadas_10j": 0, "titulos": 0, "vices": 0, "top4": 0, "rebaixamentos": 0})
    salvar_tabela(tr.ranquear(comp, "aprov", False), "compilado_treinadores.csv")
    salvar_tabela(rankings_carreira(H), "rankings_carreira.csv")

    Y = tr.agregar(A, ["temporada", "treinador_id", "treinador"])
    salvar_tabela(extremos_por_grupo(Y, "temporada", MIN_ANO), "extremos_por_temporada.csv")

    TC = tr.agregar(A, ["treinador_id", "treinador", "clube"])
    temporadas_clube = A.groupby("clube")["temporada"].nunique()
    pa, pb = por_clube(TC, temporadas_clube)
    salvar_tabela(pa, "por_clube_min20.csv")
    salvar_tabela(pb, "por_clube_min50_com_recuo.csv")

    TCY = tr.agregar(A, ["treinador_id", "treinador", "clube", "temporada"])
    salvar_tabela(tr.ranquear(TCY[TCY["jogos"] >= MIN_ANO], "aprov", False), "trabalhos_por_temporada.csv")

    for mando in ("casa", "fora"):
        Hm = tr.agregar(A[A["casa_fora"] == mando], ["treinador_id", "treinador"])
        salvar_tabela(tr.ranquear(Hm[Hm["jogos"] >= MIN_MANDO], "aprov", False), f"historico_{'mandante' if mando == 'casa' else 'visitante'}.csv")
    CF = casa_fora(A)
    salvar_tabela(CF, "casa_x_fora.csv")

    salvar_tabela(CT, "campeonato_treinadores_por_ano.csv")
    resumo = []
    for y, g in CT.groupby("temporada"):
        f = lambda m: " / ".join(f"{t} ({p:.1%}, {j}j)" for t, p, j in zip(g[m].treinador, g[m].aprov, g[m].jogos))
        reb = g[g.rebaixado].sort_values("aprov")
        resumo.append(dict(temporada=y, tecnicos=len(g), campeao=f(g.campeao), vice=f(g.vice),
                           rebaixados=" / ".join(f"{t} ({p:.1%}, {j}j)" for t, p, j in zip(reb.treinador, reb.aprov, reb.jogos))))
    salvar_tabela(pd.DataFrame(resumo), "campeonato_resumo_por_ano.csv")

    figuras(A0, H, CT, CF)


if __name__ == "__main__":
    main()
