# Dados

## Fonte

Toda a base vem do repositório **[adaoduque/Brasileirao_Dataset](https://github.com/adaoduque/Brasileirao_Dataset)**,
que compila as informações das partidas da Série A a partir das súmulas da CBF e
do globoesporte, de 2003 até 2024. Não é dado oficial da CBF — é uma compilação
mantida pela comunidade. Por isso a base tratada passa por uma etapa de
validação (`src/futebrasil/validacao.py`): reconstruímos a classificação de cada
edição a partir dos jogos e conferimos contra o campeão oficial. As 22 edições
batem.

`data/external/fontes.csv` guarda a URL, o tamanho, o `sha256` e a data de
download de cada arquivo baixado.

### Arquivos brutos (`data/raw/`, baixados por `python -m futebrasil.pipeline baixar`)

| Arquivo | Conteúdo | Colunas principais |
|---|---|---|
| `campeonato-brasileiro-full.csv` | uma linha por partida | `ID`, `rodata` (rodada), `data` (DD/MM/AAAA), `hora`, `mandante`, `visitante`, `formacao_*`, `tecnico_*`, `vencedor` (nome ou `-`), `arena`, `mandante_Placar`, `visitante_Placar`, `mandante_Estado`, `visitante_Estado` |
| `campeonato-brasileiro-gols.csv` | um gol por linha | `partida_id`, `rodata`, `clube`, `atleta`, `minuto`, `tipo_de_gol` (ex.: `Gol Contra`, `Penalti`) |
| `campeonato-brasileiro-cartoes.csv` | um cartão por linha | `partida_id`, `rodata`, `clube`, `cartao`, `atleta`, `num_camisa`, `posicao`, `minuto` |
| `campeonato-brasileiro-estatisticas-full.csv` | uma linha por (partida, clube) | `partida_id`, `clube`, `chutes`, `chutes_no_alvo`, `posse_de_bola`, `passes`, `precisao_passes`, `faltas`, `cartao_amarelo`, `cartao_vermelho`, `impedimentos`, `escanteios` |

Cuidado com os IDs: `full.csv` e `estatisticas-full.csv` usam o mesmo `ID`
(começa em 1, em 2003). Já `gols.csv` e `cartoes.csv` usam um `partida_id` de
outra numeração e só cobrem as edições mais recentes (a partir de ~2013). Não há
xG em nenhum dos quatro arquivos.

## Base tratada (`data/processed/`, gerada por `pipeline preparar`)

### `partidas.parquet` — uma linha por jogo

| Campo | Tipo | Descrição |
|---|---|---|
| `partida_id` | int | ID original do `full.csv` |
| `temporada` | int | edição do campeonato (atribuída pela grade de jogos, não pelo ano da data) |
| `rodada` | int | |
| `data` | date | |
| `clube_mandante`, `clube_visitante` | str | id canônico do clube |
| `mandante_nome`, `visitante_nome` | str | nome como veio na fonte |
| `gols_mandante`, `gols_visitante` | int | |
| `estadio_id` | str | id canônico do estádio; `outro__*` quando não mapeado |
| `arena_bruta` | str | nome do estádio como veio na fonte |
| `estadio`, `estadio_cidade`, `estadio_uf` | str | metadados do estádio canônico |
| `resultado` | str | `M` mandante venceu · `E` empate · `V` visitante venceu |
| `pts_mandante`, `pts_visitante` | int | 3 / 1 / 0 |
| `pf_marcado` | bool | a fonte marcou o jogo com sufixo `*(PF)` (portões fechados) |
| `janela_sem_publico` | bool | data entre 08/07/2020 e 15/11/2021 (janela aproximada da pandemia) |
| `sem_publico` | bool | `pf_marcado` ou `janela_sem_publico` |
| `n_clubes_edicao` | int | 24 (2003–04), 22 (2005), 20 (2006+) |
| `estadio_casa_principal` | str | estádio onde o clube mais mandou naquela temporada |
| `mando_fora_de_casa` | bool | jogo de mando fora da casa principal da temporada |

### `time_jogo.parquet` — duas linhas por jogo (uma por clube)

Forma longa para as métricas. Campos: `partida_id`, `temporada`, `rodada`,
`data`, `clube`, `adversario`, `mandante` (bool), `estadio_id` (`fora` quando o
clube é visitante), `gols_pro`, `gols_contra`, `saldo`, `pts`, `vitoria`,
`empate`, `derrota`, `sem_publico`, `mando_fora_de_casa`, `n_clubes_edicao`.

### `validacao_temporadas.csv`

Uma linha por edição com a classificação reconstruída: nº de jogos, turno e
returno completos, gols conferidos pelos dois lados, campeão reconstruído ×
campeão oficial.

## Canonicalização (`src/futebrasil/lookups.py`)

O mesmo clube e o mesmo estádio aparecem grafados de várias formas ao longo dos
anos. O módulo `lookups.py` é a fonte da verdade dos mapeamentos; um snapshot em
CSV fica em `data/external/` (`estadios_canonico.csv`, `estadios_padroes.csv`,
`clubes_alias.csv`).

Estádios reconstruídos no mesmo terreno são tratados como praças diferentes,
porque a pergunta da análise é sobre a praça específica:

- **Palestra Itália** (até 2010) ≠ **Allianz Parque** (2014+) — Palmeiras
- **Fonte Nova antiga** (até 2013) ≠ **Arena Fonte Nova** (2014+) — Bahia

## Limitações conhecidas

- Fonte compilada por terceiros, não oficial. Mitigado pela validação por edição.
- **0,6% dos jogos** ficam com estádio não mapeado (`estadio_id` começando com
  `outro__`) — são praças com 1 a 7 jogos no período todo. Não afetam o fator
  mandante; no fator casa entram como "mando fora da casa principal".
- A janela `sem_publico` é **aproximada**. Só 25 jogos têm marcação explícita na
  fonte; o resto é inferido por data. A volta do público foi gradual e variou por
  estado ao longo de 2021.
- `gols.csv` e `cartoes.csv` não cobrem 2003–2012.
- Sem xG. A coleta via FBref fica para uma análise futura.

## Licença dos dados

O código deste repositório é MIT. Os dados em `data/` pertencem a terceiros e
seguem os termos de origem — placares, datas e resultados são fatos e não têm
proteção autoral; a compilação é do repositório citado acima. Ao reusar, cite a
fonte primária.

---

## English (short)

All data comes from **[adaoduque/Brasileirao_Dataset](https://github.com/adaoduque/Brasileirao_Dataset)**
(Série A matches 2003–2024, compiled from CBF match reports and globoesporte —
not official CBF data). The cleaning step rebuilds each season's final table from
the matches and checks it against the official champion; all 22 seasons match.
`data/external/fontes.csv` records the URL, size, `sha256` and download date of
each raw file.

Processed outputs: `partidas.parquet` (one row per match), `time_jogo.parquet`
(long form, one row per club per match), `validacao_temporadas.csv` (rebuilt
standings). Field-level dictionary is the Portuguese table above.

Rebuilt-on-the-same-site stadiums are treated as distinct grounds (Palestra
Itália ≠ Allianz Parque; old Fonte Nova ≠ Arena Fonte Nova). Known limits: 0.6%
of matches have an unmapped stadium; the `sem_publico` (no-crowd) window is
approximate; goals/cards files don't cover 2003–2012; no xG yet.
