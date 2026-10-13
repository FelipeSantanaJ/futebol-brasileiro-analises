# Brazilian Football Analytics

[Português](README.md)

Quantitative analyses of Brazilian football, focused on the top division
(Série A) in the **round-robin era (2003 onwards)** — but not limited to it. Each
analysis lives in its own folder under [analyses/](analyses/), with the code that
produces it, the output tables, the charts, and a write-up covering method and
results in Portuguese and English.

Personal project, work in progress.

## Analyses

| # | Topic | Status |
|---|-------|--------|
| [01](analyses/01-fator-mandante-e-fator-casa/) | Host factor vs. home-ground factor — how much playing at home was worth in Série A, separating the effect of **having home advantage** from the effect of **the specific ground** | ✅ done |
| [02](analyses/02-linha-de-corte-do-rebaixamento/) | Relegation safety line — how many points are enough to survive, and whether a club's points pace can be turned into an actual relegation probability | ✅ done |
| [03](analyses/03-treinadores-da-serie-a/) | Série A head coaches (2003–2025) — a coach × match base built and validated from four sources, and rankings by points percentage, wins, losses, attack, defence, club, season, home vs away and a "league of coaches" | ✅ done |

**Host factor** (`fator mandante`) is the effect of being the designated home
side. **Home-ground factor** (`fator casa`) is the effect of hosting at that
specific stadium — a distinction that matters because several clubs changed
grounds over the period (Corinthians hosted at Morumbi, at Pacaembu and now at
the Arena; Palmeiras moved from Palestra Itália to Allianz Parque; Grêmio from
the Olímpico to the Arena).

Analysis 01 in one paragraph: on average over 2003–2024 the home side took
**1.75 points per game** against **0.98** for the visitor — 64% of all points
went to whoever played at home. Adjusting for team strength, the home side scores
**1.49× more goals**. That edge **shrank** over the period and dropped further in
the crowd-free matches of the pandemic. At club level the decline is barely
significant on its own — it is a league-wide phenomenon.

Analysis 02 in one paragraph: from 2006 to 2023 the 17th-placed club (first
relegated) finished Série A with **41.7 points on average**, with no rising or
falling trend over the years. A logistic model trained on that history, applied
to each club's pace at fixed checkpoint rounds, converges to the same line
(**41.6 points** projected at round 35) and correctly classifies **18 of 20**
2024 clubs as above or below 50% risk — Corinthians included, which sat at
**exactly 49.2%** at round 30 before taking 24 points from the last 8 rounds.

Analysis 03 in one paragraph: the public match base has no coach before 2014,
so the analysis rebuilds, match by match, who was on the bench in 9,165 matches
of 2003–2025 by crossing Transfermarkt, O Gol, CBF and Wikipedia — **94.9%** of
team-matches end up confirmed by two or more sources, and **498 of 510**
coaching changes listed on Wikipedia are reproduced without using it. With 100+
matches, **Abel Ferreira** (62.8%) and **Muricy Ramalho** (57.2%) lead on points
percentage; Cuca has the most wins (266 in 612 matches). In a "league of
coaches" ranked by points percentage, Muricy has the most titles (2006–2008).

## Scope

- **Competition:** Campeonato Brasileiro, Série A.
- **Period:** 2003 onwards — the first edition played as a full double
  round-robin (24 clubs / 46 rounds in 2003–2004; 22 / 42 in 2005; 20 / 38 since
  2006). 2001 and 2002 had knockout stages and are left out to avoid mixing
  formats.
- **Season vs. calendar year:** the 2020 edition ended in February 2021. Season
  is assigned from each edition's fixture count, not from the match date's year.

## Layout

```
data/
├── raw/            # downloaded raw CSVs (gitignored)
├── processed/      # partidas.parquet, time_jogo.parquet — clean base
└── external/       # canonicalisation tables, source registry and the coach base
src/futebrasil/
├── dados.py        # download and provenance
├── lookups.py      # canonical club and stadium names
├── limpeza.py      # builds the clean base
├── metricas.py     # home/away ppg, points share, goal diff — both factors
├── modelos.py      # opponent-adjusted host effect (Poisson goal model)
├── tendencia.py    # is the factor rising or falling? (per-club slope)
├── validacao.py    # rebuilds the final table and checks it against reference
├── permanencia.py  # relegation safety line and points-pace model
├── treinadores.py  # coach × match base: aggregation, rankings, streaks, league of coaches
└── pipeline.py     # download / prepare / validate
analyses/
├── 01-fator-mandante-e-fator-casa/
│   ├── run.py
│   ├── outputs/{tables,figures}/
│   └── README.en.md
├── 02-linha-de-corte-do-rebaixamento/
│   ├── run.py
│   ├── outputs/{tables,figures}/
│   └── README.en.md
└── 03-treinadores-da-serie-a/
    ├── run.py
    ├── coleta/      # scripts that built the coach base (scraping + validation)
    ├── outputs/{tables,figures}/
    └── README.en.md
```

## Running it

```bash
python -m venv .venv
source .venv/bin/activate         # Linux/Mac;  .venv\Scripts\activate on Windows
pip install -e .

python -m futebrasil.pipeline tudo          # download, clean and validate
python analyses/01-fator-mandante-e-fator-casa/run.py
python analyses/02-linha-de-corte-do-rebaixamento/run.py
python analyses/03-treinadores-da-serie-a/run.py     # uses data/external/treinadores/ (versioned)
```

`pipeline tudo` writes `data/processed/*.parquet` plus a validation report with
the reconstructed final table for every edition (all 22 match the official
champion).

## Sources

Match data: [adaoduque/Brasileirao_Dataset](https://github.com/adaoduque/Brasileirao_Dataset),
compiled from CBF match reports and globoesporte. Details, licensing and known
limitations in [data/README.md](data/README.md).

Coaches (analysis 03): own base built from
[Transfermarkt](https://www.transfermarkt.com/), [O Gol](https://www.ogol.com.br/),
CBF (via the base above) and Wikipedia — method and validation in
[analyses/03-treinadores-da-serie-a/](analyses/03-treinadores-da-serie-a/).

## Next

- Collect per-match xG (FBref) for analyses that need chance quality, not just
  results.
- Série B and C; state leagues; Copa do Brasil.
- Refereeing, ball-in-play time and stoppage time as channels of the host effect.
