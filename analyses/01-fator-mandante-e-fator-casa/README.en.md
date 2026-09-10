# 01 — Host factor and home-ground factor in Série A (2003–2024)

[Português](README.md)

## The question

How much was playing at home worth to Série A clubs in the round-robin era? And,
separating two things that usually get treated as one:

- **Host factor** (`fator mandante`) — the effect of being the designated home
  side, wherever the match is played.
- **Home-ground factor** (`fator casa`) — the effect of hosting **at that
  specific stadium**. It matters because several clubs changed grounds over the
  period: Corinthians hosted at Morumbi, at Pacaembu, and since 2014 at the Arena
  in Itaquera; Palmeiras left Palestra Itália, passed through Pacaembu and
  Barueri, and moved to Allianz Parque; Grêmio swapped the Olímpico for the
  Arena; Atlético-MG rotated between Mineirão, Independência and Arena MRV.

For each factor the analysis gives three cuts: **aggregate** (all seasons
pooled), **year by year**, and **trend** — whether the factor rose or fell for
each club over time.

## How it was measured

Base: `data/processed/time_jogo.parquet` (two rows per match, one per club). All
metrics are **per game**, so editions with different numbers of rounds compare.

- **Descriptive split** — points per game (ppg) as home side vs. ppg as visitor.
  The gap is `vantagem_ppg`. Also `share_pts_casa` = home points ÷ (home + away
  points); 0.5 would mean "no advantage at all".
- **Poisson goal model** (`src/futebrasil/modelos.py`) — for the
  opponent-adjusted number. Each match becomes two rows; goals scored are modelled
  as `goals ~ team attack + opponent defence + host`, with club dummies. The
  `host` coefficient, exponentiated, is the **multiplicative factor on goals** for
  the home side, net of both teams' quality. Run over season windows to watch the
  effect move.
- **Trend** (`src/futebrasil/tendencia.py`) — for each club, a weighted least
  squares line (weight = number of home games that year) of `vantagem_ppg`
  against season. Classification uses the slope's 95% CI: **Rising** (CI all
  positive), **Falling** (CI all negative), **Flat** (CI crosses zero). Labels in
  the tables are in Portuguese: Subindo / Caindo / Estável.
- **Home-ground factor by stadium** — among home games at each season's primary
  ground, group by (club, stadium). The baseline is the same club's record **as a
  visitor in the same seasons** — a simple control for squad strength and era.
  `vantagem_ppg` here is the **marginal** advantage (home − away), not raw home
  strength.

Out of scope: 2001 and 2002 (knockout stages). Source, validation and
limitations in [../../data/README.md](../../data/README.md).

## Host factor — aggregate

Pooling 2003–2024 (8,785 matches):

| | home side | visitor |
|---|---:|---:|
| points per game | **1.75** | 0.98 |
| win rate | 49.6% | 24.0% |
| goals per game | 1.54 | 1.03 |

The home side took **64.1% of all points** on offer. By the Poisson model, home
teams score **1.49× more goals** (95% CI 1.46–1.54), adjusting for opponent
strength.

## Host factor — year by year

![Host factor in Série A, year by year](outputs/figures/01_liga_fator_mandante_ano_a_ano.png)

The raw advantage swings a lot from year to year, but the slope is negative —
about **−0.14 points per game per decade**. Two years break the pattern: 2017
(advantage of just 0.45, the lowest in the series) and 2018 (1.06, the highest).
The model tells the same story with less noise:

![Host effect by season window](outputs/figures/02_modelo_efeito_mando_por_janela.png)

The goal factor sits around **1.54 from 2003 to 2019** and drops to **1.33 in
2020–2021** and **1.37 in 2022–2024**. The confidence intervals of the last two
windows don't touch the earlier ones — the decline is real, not fluctuation.

### No crowds (pandemic)

In the crowd-free matches of 2020–2021, the raw advantage fell from ~0.79 ppg
(with crowds) to **0.55**. In the model, the `host × no_crowd` interaction gives
a factor of **0.87** (p = 0.04): playing without a crowd cuts about **13% of the
home side's goal boost**. The effect doesn't vanish — part of the host factor is
familiar pitch, opponent travel and refereeing lean — but it shrinks measurably.

## Host factor — by club

![Clubs ranked by host factor](outputs/figures/03_ranking_clubes_fator_mandante.png)

In aggregate (clubs with ≥150 home games), **Athletico-PR** leads comfortably
(+1.03 ppg), then **Sport**, **Grêmio** and **Coritiba**. At the bottom,
**Atlético-GO** (+0.36) and, among the smaller samples, **Cuiabá** (+0.17). The
Poisson model puts Grêmio, Sport, Fortaleza and Athletico-PR as the ones who
inflate their attack most at home.

Much of the top clubs' edge comes from being **very poor on the road** (Paysandu,
Guarani and Portuguesa, all with few top-flight seasons, have the biggest gaps
for exactly that reason), so the raw ranking mixes "fortress at home" with "soft
away".

## Host factor — trend by club

![Host factor trend by club](outputs/figures/04_tendencia_por_clube_small_multiples.png)

Of 28 clubs with at least 6 seasons, **24 come out "Flat"** and **4 "Falling"**
(Vitória, Sport, Botafogo, Flamengo). **None "Rising".** So the decline in the
host factor is a **league-level** phenomenon; at club level, 15 to 22 seasons of
noisy data aren't enough to pin down an individual trend in most cases. The
direction, though, is consistent — the slopes cluster on the negative side.

## Home-ground factor — by stadium

![Home-ground factor by stadium, clubs that changed grounds](outputs/figures/05_fator_casa_troca_de_estadio.png)

Read as **marginal** advantage (home ppg − away ppg, same seasons):

| Club | Ground | Period | Games | Advantage (ppg) |
|---|---|---|---:|---:|
| Corinthians | Pacaembu | 2003–2013 | 169 | 0.74 |
| Corinthians | Neo Química Arena | 2014–2024 | 203 | **0.81** |
| Grêmio | Olímpico | 2003–2012 | 172 | **1.03** |
| Grêmio | Arena do Grêmio | 2013–2024 | 193 | 0.86 |
| Palmeiras | Palestra Itália | 2004–2009 | 109 | **0.82** |
| Palmeiras | Pacaembu (exile) | 2010–2014 | 33 | 0.42 |
| Palmeiras | Allianz Parque | 2015–2024 | 163 | 0.56 |
| Atlético-MG | Mineirão | 2003–2022 | 157 | 0.64 |
| Atlético-MG | Independência | 2012–2019 | 133 | **0.92** |
| Atlético-MG | Arena MRV | 2023–2024 | 25 | 0.63 |
| Bahia | Arena Fonte Nova | 2014–2024 | 125 | 0.85 |
| Bahia | Pituaçu (interim) | 2011–2012 | 38 | 0.29 |

Some patterns:

- **Corinthians** gained a little more advantage at the Arena than they had at
  Pacaembu (+0.81 vs. +0.74).
- **Grêmio** got more out of the Olímpico (+1.03) than they get at the Arena
  (+0.86) — though part of that is the recent Grêmio being better away.
- **Palmeiras** have their smallest marginal advantage precisely at Allianz. It's
  not that they play badly there (2.10 ppg at home) — it's that recent Palmeiras
  also score heavily away (1.54 ppg), so the **gap** narrows. The Pacaembu exile
  really was poor (+0.42).
- **Independência** confirms Atlético-MG's fortress reputation: +0.92, above
  Mineirão (+0.64) and above Arena MRV's first two years (+0.63).
- Interim grounds (Pituaçu for Bahia, Pacaembu for Palmeiras) return much less
  than the "real" home — the home effect depends on it being home.

The full table, all clubs and stadiums (≥15 home games), is in
[outputs/tables/fator_casa_por_estadio.csv](outputs/tables/fator_casa_por_estadio.csv).
The slope of the advantage within each stadium is in
`tendencia_por_clube_estadio.csv`.

## Caveats

- The descriptive split does **not** control for opponent strength; the Poisson
  model does, and tells the same story.
- The home-ground `vantagem_ppg` is marginal — a club that got good away shows a
  smaller advantage even while hosting well.
- Small samples (interim grounds, clubs with few seasons) have wide intervals;
  the `n_jogos` column is in every table.
- The no-crowd window is approximate (see [../../data/README.md](../../data/README.md)).

## Files

- `run.py` — produces everything below.
- `outputs/tables/` — `agregado_liga`, `agregado_por_clube`, `ano_a_ano_liga`,
  `ano_a_ano_por_clube`, `tendencia_por_clube`, `fator_casa_por_estadio`,
  `tendencia_por_clube_estadio`, `modelo_efeito_mando_janela`,
  `modelo_efeito_mando_por_clube`, `modelo_efeito_mando_sem_publico`.
- `outputs/figures/` — the 5 figures above.
