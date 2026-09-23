# Análises de Futebol Brasileiro

[English](README.en.md)

Repositório de análises quantitativas do futebol brasileiro, com foco no
Campeonato Brasileiro da Série A na **era dos pontos corridos (2003 em diante)** —
mas sem se limitar a isso. Cada análise fica numa pasta própria em
[analyses/](analyses/), com o código que a gera, as tabelas de saída, os
gráficos e um texto explicando método e resultados em português e inglês.

Projeto pessoal, em construção.

## Análises

| # | Tema | Status |
|---|------|--------|
| [01](analyses/01-fator-mandante-e-fator-casa/) | Fator mandante × fator casa — quanto jogar em casa valeu na Série A, separando o efeito do **mando de campo** do efeito da **praça específica** | ✅ concluída |
| [02](analyses/02-linha-de-corte-do-rebaixamento/) | Linha de corte do rebaixamento — quantos pontos bastam para escapar, e se dá para transformar o ritmo em pontos de um clube numa probabilidade de queda | ✅ concluída |

**Fator mandante** é o efeito de ter o mando do jogo (mandante × visitante).
**Fator casa** é o efeito de mandar naquele estádio específico — separação que
importa porque vários clubes trocaram de casa no período (o Corinthians mandou
no Morumbi, no Pacaembu e hoje na Arena; o Palmeiras saiu do Palestra Itália
para o Allianz; o Grêmio, do Olímpico para a Arena).

Resumo da 01: na média de 2003–2024 o mandante fez **1,75 ponto por jogo** contra
**0,98 do visitante** — 64% dos pontos ficaram com quem jogou em casa. Ajustando
pela força dos times, o mandante marca **1,49× mais gols**. Esse empurrão
**encolheu** ao longo do período e caiu mais ainda nos jogos sem público da
pandemia. No nível de clube a queda quase não é individualmente significativa —
é um fenômeno de liga.

Resumo da 02: de 2006 a 2023 o 17º colocado (primeiro rebaixado) fechou a Série A
com **41,7 pontos em média**, sem tendência de alta ou queda ao longo dos anos. Um
modelo logístico treinado nesse histórico, aplicado ao ritmo de cada clube em
rodadas de corte fixas, converge para a mesma linha (**41,6 pontos** projetados
na rodada 35) e acerta **18 dos 20 clubes** de 2024 ao classificá-los acima ou
abaixo de 50% de risco — inclusive o Corinthians, que estava em **exatos 49,2%**
na rodada 30 antes de arrancar 24 pontos nas 8 rodadas finais.

## Escopo e recorte

- **Competição:** Campeonato Brasileiro, Série A.
- **Período:** 2003 em diante. Foi a primeira edição disputada em pontos corridos
  de ida e volta (24 clubes / 46 rodadas em 2003–2004; 22 / 42 em 2005; 20 / 38
  desde 2006). 2001 e 2002 tiveram fase de mata-mata e ficam de fora para não
  misturar formatos.
- **Temporada × ano-calendário:** a edição de 2020 terminou em fevereiro de 2021.
  A temporada é atribuída pela grade de jogos de cada edição, não pelo ano da
  data.

## Estrutura

```
data/
├── raw/            # CSVs brutos baixados (não versionado)
├── processed/      # partidas.parquet, time_jogo.parquet — base tratada
└── external/       # tabelas de canonicalização e registro de fontes
src/futebrasil/
├── dados.py        # download e proveniência
├── lookups.py      # nomes canônicos de clubes e estádios
├── limpeza.py      # monta a base tratada
├── metricas.py     # ppg casa/fora, share, saldo — fator mandante e fator casa
├── modelos.py      # efeito de mando ajustado ao adversário (Poisson de gols)
├── tendencia.py    # o fator está subindo ou caindo? (inclinação por clube)
├── validacao.py    # reconstrói a classificação e confere com a referência
├── permanencia.py  # linha de segurança do rebaixamento e modelo de ritmo em pontos
└── pipeline.py     # baixar / preparar / validar
analyses/
├── 01-fator-mandante-e-fator-casa/
│   ├── run.py
│   ├── outputs/{tables,figures}/
│   └── README.md
└── 02-linha-de-corte-do-rebaixamento/
    ├── run.py
    ├── outputs/{tables,figures}/
    └── README.md
```

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows;  source .venv/bin/activate no Linux/Mac
pip install -e .

python -m futebrasil.pipeline tudo          # baixa, trata e valida os dados
python analyses/01-fator-mandante-e-fator-casa/run.py
python analyses/02-linha-de-corte-do-rebaixamento/run.py
```

`pipeline tudo` grava `data/processed/*.parquet` e um relatório de validação com a
classificação reconstruída de cada edição (as 22 batem com o campeão oficial).

## Fontes

Base de partidas: [adaoduque/Brasileirao_Dataset](https://github.com/adaoduque/Brasileirao_Dataset),
compilada a partir das súmulas da CBF e do globoesporte. Detalhes, licenças e
limitações em [data/README.md](data/README.md).

## Próximos passos

- Coletar xG por partida (FBref) para as análises que dependem de qualidade de
  chance, não só de resultado.
- Séries B e C; estaduais; Copa do Brasil.
- Arbitragem, tempo de bola rolando e acréscimos como canais do fator mandante.
