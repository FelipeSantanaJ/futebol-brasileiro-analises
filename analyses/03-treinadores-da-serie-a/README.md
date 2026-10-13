# 03 — Treinadores da Série A (2003–2025)

[English](README.en.md)

## A pergunta

Quem foram os melhores e os piores treinadores da Série A na era dos pontos
corridos — por aproveitamento, vitórias, derrotas, ataque, defesa, por clube,
por temporada e em casa × fora?

Responder a isso exige, antes de qualquer ranking, uma base confiável de
**treinador × partida**: cada jogo atribuído a quem estava de fato no banco,
inclusive quando o clube trocou de técnico no meio do campeonato. A base pública
mais usada (a mesma das análises 01 e 02) tem os campos `tecnico_mandante` /
`tecnico_visitante` **vazios antes de 2014**. Por isso esta análise tem duas
partes: **montar e validar a base** e, só depois, **ranquear**.

## Recorte

Série A, **2003 a 2025** (23 edições). São 9.165 partidas — 9.166 programadas
menos Chapecoense × Atlético-MG de 2016, não disputada após o acidente aéreo — e
**18.330 jogos-lado** (uma linha por clube por partida). Inclui 2025, que não
está na base das análises 01 e 02.

## Como a base foi montada

Quatro fontes, cada uma com um papel:

| Fonte | O que fornece | Cobertura |
|---|---|---|
| **Transfermarkt** — súmula de cada jogo | partidas, placar e o técnico de cada lado, com ID único por pessoa | 2003–2025 · 18.208 lados com nome |
| **O Gol (zerozero)** — página "jogos realizados" de cada técnico | quais jogos cada técnico dirigiu, em casa ou fora | 2003–2025 · 17.413 lados |
| **CBF** (via [adaoduque/Brasileirao_Dataset](https://github.com/adaoduque/Brasileirao_Dataset)) | técnico da súmula oficial, placar | técnico 2014–2024; placar 2003–2024 |
| **Wikipédia** (en 2003–04; pt 2008–25) | 510 trocas de técnico com data; matriz de placares | validação externa |

Cada lado recebe um **status**: `confirmado` (duas ou mais fontes jogo a jogo
apontam a mesma pessoa), `provável` (uma fonte, sem contradição), `inferido`,
`ambíguo` ou `sem_treinador`. Regras principais:

- **Quem estava no banco leva o jogo.** Nada de "técnico da temporada". O
  interino que assumiu numa transição entre técnicos conta.
- **Ausência pontual volta ao titular.** Até 2 jogos de outro nome *entre* jogos
  do mesmo técnico na mesma temporada (suspensão, doença) são creditados ao
  titular — critério inspirado no levantamento de rotatividade do ge. O nome
  original fica na coluna `atribuicao_original` (80 lados).
- **Conflito entre fontes**, nesta ordem: O Gol + CBF contra o Transfermarkt →
  data da troca na Wikipédia → mesmo técnico antes e depois → senão `ambíguo`.
- **Impossibilidade cronológica:** um técnico não pode estar em um clube enquanto
  tem jogos confirmados em outro.

Uma armadilha documentada: as **súmulas** do O Gol servidas a um coletor trazem
escalações de outros jogos e placares que quase nunca batem com a CBF — foram
descartadas. As listas por técnico do mesmo site concordam 97,9% com a CBF, de
forma independente do Transfermarkt, e foram usadas.

Detalhes e reprodução em [coleta/README.md](coleta/README.md).

## Qualidade da base

![Status da atribuição por temporada](outputs/figures/01_qualidade_da_base_por_temporada.png)

- **94,9%** dos jogos-lado confirmados por 2+ fontes; 99,3% confirmados ou prováveis.
- **127 partidas** continuam com ao menos um lado incerto, concentradas em
  2005–2006 (Ponte Preta 2006 tem 11 jogos sem técnico em nenhuma fonte).
- Validação **independente**: das 510 trocas registradas na Wikipédia, **498**
  aparecem na sequência reconstruída sem usar a Wikipédia na atribuição.
- O número de trocas por temporada (sem interinos de até 3 jogos) bate com o
  publicado pelo ge: 2003 39 × 40; 2010 33 × 31; 2015 30 × 32; 2023 25 × 25.
- Placares: 100% iguais à CBF (8.785 jogos) e 99,75% iguais à Wikipédia.
- Sensibilidade: refazendo os rankings só com lados confirmados/prováveis, o Top
  20 de aproveitamento não muda e o Bottom 20 troca um nome.

Auditoria completa (14 testes de consistência, todos aprovados) em
[coleta/auditoria.md](coleta/auditoria.md).

## Resultados

Filtros fixos: **20, 50 ou 100 jogos** para carreira, **5 jogos** por temporada,
**10 jogos** em cada mando, **20 jogos** no clube. Empates exatos dividem a
posição; o critério secundário é sempre "mais jogos". Média da liga: 45,6% de
aproveitamento (empates distribuem 2 pontos, não 3).

### Aproveitamento × tamanho da carreira

![Aproveitamento × jogos](outputs/figures/02_aproveitamento_x_jogos.png)

Com 20+ jogos lideram Jorge Jesus (83,9% em 29 jogos), Filipe Luís (69,4%, 48)
e Artur Jorge (69,3%, 38). Entre carreiras longas o quadro é outro:

![Aproveitamento com 100+ jogos](outputs/figures/03_aproveitamento_100_jogos.png)

| Com 100+ jogos | J | Aprov. | | Com 100+ jogos | J | Aprov. |
|---|---:|---:|---|---|---:|---:|
| Abel Ferreira | 206 | 62,8% | | Gilson Kleina | 224 | 36,8% |
| Jorge Sampaoli | 116 | 57,5% | | Marquinhos Santos | 159 | 39,4% |
| Muricy Ramalho | 441 | 57,2% | | Eduardo Baptista | 162 | 39,5% |
| Levir Culpi | 207 | 54,8% | | Jorginho (J. de Amorim) | 189 | 39,9% |
| Tite | 376 | 54,3% | | Mário Sérgio | 111 | 40,5% |

**Vitórias:** volume e frequência são coisas diferentes. Cuca tem mais vitórias
(266 em 612 jogos), seguido de Renato Gaúcho e Luxemburgo (229 cada), todos com
cerca de 43% de vitórias por jogo. Só cinco técnicos estão ao mesmo tempo no top
20 de vitórias absolutas e no top 20 de % de vitórias: Abel Ferreira, Muricy,
Tite, Levir Culpi e Emerson Leão.

**Derrotas:** Vagner Mancini lidera as derrotas absolutas (188 em 454 jogos) —
mais derrotas não é o mesmo que pior técnico: oito dos dez líderes em derrotas
absolutas têm aproveitamento acima da média da liga.

**Ataque e defesa:** por jogo, Jorge Jesus (2,45 gols/j) e Filipe Luís (0,71
sofridos/j) lideram com 20+ jogos; com 100+ jogos, Emerson Leão (1,66) e Abel
Ferreira (0,89).

**Melhores trabalhos de temporada** (19+ jogos): Jorge Jesus/Flamengo 2019
(83,9%), Felipão/Palmeiras 2018 (81,8%), Cuca/Atlético-MG 2021 (73,7%).

### Casa × fora

![Casa × fora](outputs/figures/05_casa_x_fora.png)

Entre os 146 técnicos com 10+ jogos em cada mando, o aproveitamento em casa é,
em média, **24,1 pontos percentuais** maior que fora — o mesmo fenômeno de liga
da análise 01, visto pelo lado do treinador.

### Campeonato de treinadores

Cada temporada vira uma "liga" de técnicos ordenada por aproveitamento (só quem
teve 10+ jogos no ano, somando todos os clubes que dirigiu): o 1º é o campeão e
os 4 piores são os rebaixados.

![Títulos e rebaixamentos](outputs/figures/04_campeonato_titulos_e_rebaixamentos.png)

Muricy Ramalho é o maior campeão (2006, 2007 e 2008); Luxemburgo, Tite, Cuca,
Abel Braga e Marcelo Oliveira têm 2 títulos cada. Vagner Mancini e Jorginho
(Jorge de Amorim) foram "rebaixados" 3 vezes. Renato Gaúcho ficou 6 vezes no top
4 sem nenhum título e com 2 rebaixamentos (2008 e 2009).

## Ressalvas

- **Aproveitamento mede trabalho e elenco juntos.** Clubes de maior orçamento
  concentram os melhores números (Flamengo tem 10 de 18 técnicos com 20+ jogos
  acima de 55%). Os rankings não isolam o mérito do treinador.
- **Amostras curtas:** com mínimo de 20 jogos, carreiras curtas e marcantes
  dominam os extremos — por isso os cortes de 50 e 100 jogos.
- **2005–2007** não têm tabela de trocas na Wikipédia; ali a validação é só
  Transfermarkt × O Gol.
- **Bordas de temporada** (ex.: Renato poupado nas últimas rodadas de 2016, 2017
  e 2019) ficam com quem estava no banco; a regra de ausência só vale entre
  jogos do mesmo técnico.
- Dados derivados de páginas do Transfermarkt e do O Gol, publicados aqui para
  fins de estudo, com as fontes citadas.

## Arquivos

- `apresentacao/treinadores_serie_a_2003_2025.pdf` — apresentação com os resultados (50 slides).
- `run.py` — gera as tabelas e figuras a partir da base em
  `data/external/treinadores/` (não acessa a internet).
- `outputs/tables/` — `compilado_treinadores` (todos os 353 técnicos, com títulos
  e rebaixamentos), `rankings_carreira` (top/bottom 20 de cada métrica nos cortes
  de 20, 50 e 100 jogos), `extremos_por_temporada`, `por_clube_min20`,
  `por_clube_min50_com_recuo` (31 clubes com 5+ temporadas; o mínimo recua para
  40/30/20/10 quando faltam 2 técnicos elegíveis), `trabalhos_por_temporada`,
  `historico_mandante`, `historico_visitante`, `casa_x_fora`,
  `campeonato_treinadores_por_ano`, `campeonato_resumo_por_ano`.
- `outputs/figures/` — as 5 figuras acima.
- `coleta/` — scripts que montam a base (raspagem, cruzamento, validação).
- `src/futebrasil/treinadores.py` — carga da base, agregação, rankings com
  empates, séries e campeonato de treinadores.
