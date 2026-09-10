"""Monta a tabela tratada de partidas a partir do CSV bruto.

Saídas em data/processed/:
  - partidas.parquet   uma linha por jogo (visão mandante)
  - time_jogo.parquet  duas linhas por jogo (uma por clube), forma longa

Pontos que exigem cuidado e como resolvemos:

  Temporada x ano-calendário. A edição de 2020 do Brasileirão terminou em
  fevereiro de 2021, então o ano da data não identifica a temporada. O ID do
  dataset é cronológico e contíguo por edição, então atribuímos a temporada pela
  contagem de jogos conhecida de cada edição (GRADE, abaixo).

  Estádios reconstruídos. Palestra Itália e Allianz Parque (Palmeiras), Fonte
  Nova antiga e Arena Fonte Nova (Bahia) são praças diferentes — ver lookups.py.

  Portões fechados. O dataset marca 25 jogos com sufixo *(PF). A maioria dos
  jogos sem público de 2020–21 não tem marcação, então também sinalizamos a
  janela da pandemia por data (jul/2020 a nov/2021), campo `janela_sem_publico`.

  Mando fora de casa. Alguns clubes jogaram como mandantes fora da sua praça
  habitual (estádio interditado, gramado, castigo, pandemia). Para cada
  (clube, temporada) tomamos o estádio onde mais mandou como "casa principal" e
  marcamos os demais jogos como `mando_fora_de_casa` — eles entram no fator
  mandante, mas não no fator casa daquele estádio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import lookups
from .caminhos import PROCESSADO, garantir_dirs
from .dados import carregar_bruto

# edição -> número de jogos (ordem cronológica dos IDs no dataset)
GRADE = [
    (2003, 552), (2004, 552), (2005, 462),
    (2006, 380), (2007, 380), (2008, 380), (2009, 380), (2010, 380),
    (2011, 380), (2012, 380), (2013, 380), (2014, 380), (2015, 380),
    (2016, 379),  # Chapecoense x Atlético-MG (rod. 38) não disputada
    (2017, 380), (2018, 380), (2019, 380), (2020, 380), (2021, 380),
    (2022, 380), (2023, 380), (2024, 380),
]

# nº de clubes por edição, para normalizações
CLUBES_POR_EDICAO = {2003: 24, 2004: 24, 2005: 22}
for _ano in range(2006, 2025):
    CLUBES_POR_EDICAO[_ano] = 20

# janela aproximada de jogos sem público na pandemia (retomada -> volta da torcida)
COVID_INI = pd.Timestamp("2020-07-08")
COVID_FIM = pd.Timestamp("2021-11-15")


def _atribuir_temporada(partida_id: pd.Series) -> pd.Series:
    """Temporada pela ordem cronológica do ID e pela contagem de jogos da GRADE."""
    ordem = partida_id.sort_values().index
    temporadas = np.empty(len(ordem), dtype=int)
    i = 0
    for ano, n in GRADE:
        temporadas[i:i + n] = ano
        i += n
    if i != len(ordem):
        faltam = len(ordem) - i
        print(f"[limpeza] AVISO: {faltam} jogos além da grade conhecida "
              f"(esperado {i}, veio {len(ordem)}). Atribuídos a {GRADE[-1][0] + 1}.")
        temporadas[i:] = GRADE[-1][0] + 1
    return pd.Series(temporadas, index=ordem).reindex(partida_id.index)


def construir_partidas() -> pd.DataFrame:
    bruto = carregar_bruto("partidas")

    df = pd.DataFrame()
    df["partida_id"] = pd.to_numeric(bruto["ID"], errors="raise").astype(int)
    df["rodada"] = pd.to_numeric(bruto["rodata"], errors="coerce").astype("Int64")
    df["data"] = pd.to_datetime(bruto["data"], format="%d/%m/%Y", errors="coerce")
    df["temporada"] = _atribuir_temporada(df["partida_id"])

    df["clube_mandante"] = bruto["mandante"].map(lookups.clube_id)
    df["clube_visitante"] = bruto["visitante"].map(lookups.clube_id)
    df["mandante_nome"] = bruto["mandante"].str.strip()
    df["visitante_nome"] = bruto["visitante"].str.strip()

    df["gols_mandante"] = pd.to_numeric(bruto["mandante_Placar"], errors="coerce").astype("Int64")
    df["gols_visitante"] = pd.to_numeric(bruto["visitante_Placar"], errors="coerce").astype("Int64")

    df["estadio_id"] = bruto["arena"].map(lookups.estadio_id)
    df["arena_bruta"] = bruto["arena"].astype(str).str.replace("\xa0", " ").str.strip()

    meta = lookups.estadio_meta().set_index("estadio_id")
    df["estadio"] = df["estadio_id"].map(meta["estadio"]).fillna(df["arena_bruta"])
    df["estadio_cidade"] = df["estadio_id"].map(meta["cidade"])
    df["estadio_uf"] = df["estadio_id"].map(meta["uf"])

    # resultado pela ótica do mandante
    dif = df["gols_mandante"] - df["gols_visitante"]
    df["resultado"] = np.select(
        [dif > 0, dif == 0, dif < 0], ["M", "E", "V"], default=None
    )
    df["pts_mandante"] = df["resultado"].map({"M": 3, "E": 1, "V": 0}).astype("Int64")
    df["pts_visitante"] = df["resultado"].map({"M": 0, "E": 1, "V": 3}).astype("Int64")

    # portões fechados
    df["pf_marcado"] = bruto["arena"].map(lookups.marca_portoes_fechados)
    df["janela_sem_publico"] = df["data"].between(COVID_INI, COVID_FIM)
    df["sem_publico"] = df["pf_marcado"] | df["janela_sem_publico"]

    df["n_clubes_edicao"] = df["temporada"].map(CLUBES_POR_EDICAO).astype("Int64")

    # casa principal por (clube, temporada) e mando fora de casa
    df = df.merge(
        _casa_principal(df), on=["clube_mandante", "temporada"], how="left"
    )
    df["mando_fora_de_casa"] = df["estadio_id"] != df["estadio_casa_principal"]

    df = df.sort_values("partida_id").reset_index(drop=True)
    _checar_integridade(df)
    return df


def _casa_principal(df: pd.DataFrame) -> pd.DataFrame:
    cont = (
        df.groupby(["clube_mandante", "temporada", "estadio_id"])
        .size()
        .reset_index(name="n")
        .sort_values(["clube_mandante", "temporada", "n"], ascending=[True, True, False])
    )
    principal = cont.drop_duplicates(["clube_mandante", "temporada"])
    return principal.rename(columns={"estadio_id": "estadio_casa_principal"})[
        ["clube_mandante", "temporada", "estadio_casa_principal"]
    ]


def _checar_integridade(df: pd.DataFrame) -> None:
    problemas = []
    if df["resultado"].isna().any():
        problemas.append(f"{df['resultado'].isna().sum()} jogos sem placar válido")
    if df["data"].isna().any():
        problemas.append(f"{df['data'].isna().sum()} jogos sem data válida")
    desconhecidos = (df["estadio_id"].str.startswith("outro__") | df["estadio_id"].eq("desconhecido"))
    if desconhecidos.mean() > 0.03:
        problemas.append(f"{desconhecidos.mean():.1%} dos jogos com estádio não mapeado")
    # cada edição >=2006 deve ter 380 jogos (2016 = 379)
    for ano, n in GRADE:
        got = (df["temporada"] == ano).sum()
        if got != n:
            problemas.append(f"temporada {ano}: {got} jogos (esperado {n})")
    if problemas:
        print("[limpeza] checagens com ressalva:")
        for p in problemas:
            print("  -", p)
    else:
        print("[limpeza] integridade ok")


def para_forma_longa(partidas: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["partida_id", "temporada", "rodada", "data", "estadio_id", "estadio",
                 "sem_publico", "mando_fora_de_casa", "n_clubes_edicao"]

    mand = partidas[base_cols].copy()
    mand["clube"] = partidas["clube_mandante"]
    mand["adversario"] = partidas["clube_visitante"]
    mand["mandante"] = True
    mand["gols_pro"] = partidas["gols_mandante"]
    mand["gols_contra"] = partidas["gols_visitante"]
    mand["pts"] = partidas["pts_mandante"]

    vis = partidas[base_cols].copy()
    vis["clube"] = partidas["clube_visitante"]
    vis["adversario"] = partidas["clube_mandante"]
    vis["mandante"] = False
    vis["gols_pro"] = partidas["gols_visitante"]
    vis["gols_contra"] = partidas["gols_mandante"]
    vis["pts"] = partidas["pts_visitante"]
    # para o visitante o estádio não é a sua casa
    vis["estadio_id"] = "fora"
    vis["mando_fora_de_casa"] = False

    longo = pd.concat([mand, vis], ignore_index=True)
    longo["vitoria"] = (longo["pts"] == 3).astype(int)
    longo["empate"] = (longo["pts"] == 1).astype(int)
    longo["derrota"] = (longo["pts"] == 0).astype(int)
    longo["saldo"] = longo["gols_pro"] - longo["gols_contra"]
    return longo.sort_values(["partida_id", "mandante"], ascending=[True, False]).reset_index(drop=True)


def gerar(salvar: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    garantir_dirs()
    partidas = construir_partidas()
    longo = para_forma_longa(partidas)
    if salvar:
        partidas.to_parquet(PROCESSADO / "partidas.parquet", index=False)
        longo.to_parquet(PROCESSADO / "time_jogo.parquet", index=False)
        print(f"[limpeza] {len(partidas)} partidas -> {PROCESSADO}")
    return partidas, longo


def carregar_partidas() -> pd.DataFrame:
    return pd.read_parquet(PROCESSADO / "partidas.parquet")


def carregar_time_jogo() -> pd.DataFrame:
    return pd.read_parquet(PROCESSADO / "time_jogo.parquet")


if __name__ == "__main__":
    gerar()
