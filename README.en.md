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
└── external/       # canonicalisation tables and source registry
src/futebrasil/
├── dados.py        # download and provenance
├── lookups.py      # canonical club and stadium names
├── limpeza.py      # builds the clean base
├── metricas.py     # home/away ppg, points share, goal diff — both factors
├── modelos.py      # opponent-adjusted host effect (Poisson goal model)
├── tendencia.py    # is the factor rising or falling? (per-club slope)
├── validacao.py    # rebuilds the final table and checks it against reference
└── pipeline.py     # download / prepare / validate
analyses/
└── 01-fator-mandante-e-fator-casa/
    ├── run.py
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
```

`pipeline tudo` writes `data/processed/*.parquet` plus a validation report with
the reconstructed final table for every edition (all 22 match the official
champion).

## Sources

Match data: [adaoduque/Brasileirao_Dataset](https://github.com/adaoduque/Brasileirao_Dataset),
compiled from CBF match reports and globoesporte. Details, licensing and known
limitations in [data/README.md](data/README.md).

## Next

- Collect per-match xG (FBref) for analyses that need chance quality, not just
  results.
- Série B and C; state leagues; Copa do Brasil.
- Refereeing, ball-in-play time and stoppage time as channels of the host effect.
