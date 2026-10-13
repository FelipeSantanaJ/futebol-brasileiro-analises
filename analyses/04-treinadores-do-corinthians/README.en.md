# 04 — Corinthians head coaches in Série A (2003–2025)

[Português](README.md)

## The question

Of all the coaches who managed Corinthians in Série A since 2003, who had the
highest and lowest points percentage, wins, losses, goals, goal difference, and
the best and worst streaks? And, looking at the calendar, which were the club's
best and worst seasons?

## Scope and base

A cut of the coach × match base from [analysis 03](../03-treinadores-da-serie-a/)
(`data/external/treinadores/`): **856 Corinthians matches** over **22 seasons**
(in 2008 the club was in Série B), **34 coaches** and **45 spells** (unbroken
runs of the same coach in charge).

Two views:

- **Coach** — in three cuts: complete (all 34, including one-match caretakers),
  **20+ matches** for the club (13 coaches) and **50+ matches** (3: Tite, Mano
  Menezes and Fábio Carille).
- **Season** — the club's 22 Série A years.

For each cut, a "sheet" with the **highest** and **lowest** value of each metric
(raw values: for goals conceded and losing streaks, "highest" is the worst),
listing every tied name and each one's match count.

**Streaks:** longest winning, losing, unbeaten and winless runs, plus the best
and worst points percentage over 10 consecutive matches. For coaches, a streak
only counts consecutive matches within one spell; for seasons, all matches of
the year.

## Coach view

![Coaches with 20+ matches](outputs/figures/02_tecnicos_20_jogos.png)

| | Complete (34) | 20+ matches (13) | 50+ matches (3) |
|---|---|---|---|
| Highest points % | Fernando Lázaro, Jairo Leal — 100% (1 match) | Márcio Bittencourt — 71.0% (23 m) | Tite — 57.8% (206 m) |
| Lowest points % | Júnior, Cuca, Danilo — 0% (1–2 matches) | Geninho — 38.6% (44 m) | Mano Menezes — 54.5% (101 m) |
| Most matches / wins | Tite — 206 / 98 | Tite | Tite |
| Most goals per match | Bittencourt — 2.22 | Bittencourt — 2.22 | Mano — 1.37 |
| Fewest conceded per match | Tite — 0.83 | Tite — 0.83 | Tite — 0.83 |
| Best goal difference | Tite — +101 | Tite — +101 | Tite — +101 |
| Worst goal difference | Oswaldo de Oliveira — −14 | Carpegiani — −5 | Mano — +22 |
| Longest winning streak | Ramón Díaz — 9 | Ramón Díaz — 9 | Tite — 7 |
| Longest losing streak | Geninho — 6 | Geninho — 6 | Tite, Mano — 3 |
| Longest unbeaten run | Fábio Carille — 19 | Fábio Carille — 19 | Fábio Carille — 19 |
| Longest winless run | Carpegiani — 10 | Carpegiani — 10 | Fábio Carille — 8 |
| Best / worst 10-match stretch | Tite, Carille, Ramón Díaz — 93.3% / Geninho — 13.3% | same | Tite, Carille — 93.3% / Tite — 23.3% |

Full sheets (every metric, highest and lowest) in
`outputs/tables/ficha_tecnicos_{todos,min20,min50}.csv`.

Reading: Tite dominates the totals and has the meanest defence per match; the
best rate with 20+ matches belongs to Márcio Bittencourt in the 2005 title run,
who also had the strongest attack and the leakiest defence per match in that
group. The best streaks are Carille's (19 unbeaten, the start of 2017) and
Ramón Díaz's (9 straight wins at the end of 2024).

![Coach timeline](outputs/figures/03_linha_do_tempo_dos_tecnicos.png)

## Season view

![Points % by season](outputs/figures/01_aproveitamento_por_temporada.png)

| Metric | Highest | Lowest |
|---|---|---|
| Points % | 2015 — 71.1% | 2007 and 2018 — 38.6% |
| Wins | 2005 (42 m) and 2015 — 24 | 2007 — 10 |
| Losses | 2003 (46 m) — 19 | 2015 — 5 |
| Goals scored (per match) | 2005 — 87 (2.07) | 2013 — 27 (0.71) |
| Goals conceded (per match) | 2003 — 63 · per match, 2009 — 1.42 | 2013 — 22 (0.58) |
| Goal difference | 2015 — +40 | 2007 — −10 |
| Longest winning streak | 2024 — 9 | 2023 — 1 |
| Longest losing streak | 2006 — 6 | 14 seasons — 2 |
| Longest unbeaten run | 2017 — 19 | 2018 — 3 |
| Longest winless run | 2007 — 10 | 6 seasons — 3 |
| 10-match stretch | 2011, 2017, 2024 — 93.3% | 2006 — 13.3% |

2003 and 2004 had 46 matches and 2005 had 42 (38 otherwise): for totals, also
check the per-match values in `outputs/tables/temporadas.csv`.

## Caveats

- Inherits the caveats of the analysis 03 base (attribution status, brief-absence
  rule). In Corinthians matches, 843 of 856 coach assignments are confirmed by
  two or more sources and 13 are probable (one source, nothing against it); none
  is ambiguous.
- Points percentage measures the coach's job and the squad together.
- One- or two-match caretakers dominate the extremes of the complete view —
  hence the 20- and 50-match cuts.

## Files

- `apresentacao/corinthians_treinadores_2003_2025.pdf` — slide deck with the results (18 slides, in Portuguese).
- `run.py` — builds everything from `data/external/treinadores/`.
- `outputs/tables/` — `tecnicos` (34 coaches with every metric and streak),
  `ficha_tecnicos_todos`, `ficha_tecnicos_min20`, `ficha_tecnicos_min50`,
  `temporadas`, `ficha_temporadas`, `jogos_corinthians` (the 856 matches, with
  status and source of each assignment).
- `outputs/figures/` — the 3 figures above.
