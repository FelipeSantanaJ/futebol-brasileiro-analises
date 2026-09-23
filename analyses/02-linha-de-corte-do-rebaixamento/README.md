# 02 — Linha de corte do rebaixamento e ritmo em pontos (2006–2024)

[English](README.en.md)

## A pergunta

Quantos pontos, historicamente, bastam para escapar do rebaixamento na Série A?
E, no meio da temporada — quando um clube ainda não sabe se vai se salvar —,
dá para transformar "ritmo até aqui" em uma probabilidade de queda, e não só em
projeções soltas de mínimo/média/máximo?

O gatilho foi a campanha do Corinthians em 2024: 32 pontos em 30 rodadas, a pior
marca do clube na era dos pontos corridos até ali. Em vez de tratar isso como uma
pergunta só sobre um clube numa temporada, a análise trata como uma pergunta
geral — construída para valer para qualquer time, em qualquer rodada — e usa 2024
como estudo de caso no fim.

## Recorte

Série A, **era de 20 clubes / 38 rodadas / 4 rebaixados**, ou seja **2006 em
diante**. 2003 (24 clubes) e 2004–2005 (24 e 22 clubes) tiveram formatos
diferentes de acesso e rebaixamento e ficam fora — detalhes em
[../../data/README.md](../../data/README.md).

## Como foi medido

Duas frentes que se cruzam:

- **Linha de segurança (descritivo)** — pontos do **16º colocado** (última vaga
  na Série A) e do **17º colocado** (primeiro rebaixado) ao fim de cada
  temporada, reconstruídos rodada a rodada a partir de
  `data/processed/time_jogo.parquet` com a mesma lógica de classificação usada
  para validar os campeões (`src/futebrasil/validacao.py`: pontos, vitórias,
  saldo, gols pró). Tendência ao longo dos anos por mínimos quadrados
  ponderados (mesma rotina de `src/futebrasil/tendencia.py` usada na análise 01,
  agora exposta como `ajustar_reta` para reaproveito).
- **Modelo de ritmo (regressão logística)** — para cada temporada de 2006 a
  2023 e cada clube, calculamos os pontos acumulados em rodadas de corte fixas
  (10, 15, 20, 25, 30, 35) e se o clube terminou entre os 4 rebaixados. Em cada
  rodada de corte, ajustamos

  `rebaixado ~ pontos por jogo acumulados até ali`

  por regressão logística (`src/futebrasil/permanencia.py`). Um modelo por
  rodada, não uma única regressão com interação rodada×ritmo — a pergunta que
  importa sempre é local ("dado que estou na rodada R, com esse ritmo, qual a
  chance?"), e ajustar por rodada evita ter que impor uma forma para como o
  efeito do ritmo muda ao longo da temporada.

  Do coeficiente sai o **ritmo (pontos por jogo) em que o modelo prevê 50% de
  risco**, convertido em pontos projetados ao fim de 38 rodadas. A validação é
  **fora da amostra por temporada** (leave-one-season-out: cada uma das 18
  temporadas de treino sai inteira de uma vez, o modelo é reajustado sem ela e
  testado só nela) — com um único regressor e painel pequeno, é o jeito mais
  direto de checar se o ajuste generaliza. Métricas: AUC e Brier score.

2024 fica **fora do treino** o tempo todo — entra só como aplicação do modelo,
no fim.

## Linha de segurança — histórico

![Linha de corte do rebaixamento, 2006–2023](outputs/figures/01_linha_de_seguranca_historica.png)

Entre 2006 e 2023, o **17º colocado** terminou com **41,7 pontos em média**
(mínimo 36 em 2019, máximo 46 em 2009/2013/2021) e o **16º colocado** com
**43,3** — uma "zona cinzenta" de 1 a 6 pontos entre estar dentro e estar fora.
A inclinação ao longo dos anos é **de -1,1 ponto por década, mas não
significativa** (IC 95% -3,5 a +1,2; p = 0,31): diferente do fator mandante da
análise 01, aqui **não há evidência de tendência** — o custo de se salvar
oscila ano a ano, mas não está subindo nem caindo de forma consistente.

## Ritmo em pontos e probabilidade de queda

![Pontos necessários e poder preditivo por rodada](outputs/figures/02_modelo_pontos_necessarios_por_rodada.png)

O modelo logístico, ajustado célula por célula do painel 2006–2023, converge
para a mesma linha do método descritivo: a rodada 35 projeta **41,6 pontos**
para 50% de risco — a **0,1 ponto** da média histórica do 17º colocado (41,7).
Dois métodos independentes (contagem direta de posição final × regressão sobre
ritmo) chegam praticamente ao mesmo número.

Quanto mais cedo na temporada, mais o "ritmo até aqui" superestima o corte —
na rodada 10 o modelo projeta só 26,7 pontos para 50% de risco, porque times
que abrem a temporada mal em geral ainda têm tempo (e motivos estatísticos,
como regressão à média) para melhorar. O poder preditivo sobe junto: a **AUC
fora da amostra** vai de **0,77 na rodada 10** para **0,96 na rodada 30** e
**0,98 na rodada 35**, e o Brier score cai de 0,134 para 0,044 no mesmo
intervalo — o ritmo sozinho, sem nenhuma outra informação, já separa bem quem
cai de quem fica a partir da metade do campeonato.

## Estudo de caso — Corinthians 2024

![Trajetória do Corinthians em 2024 contra a linha histórica](outputs/figures/03_trajetoria_corinthians_2024.png)

Na rodada 30, o Corinthians tinha **32 pontos** (1,067 ponto por jogo) — abaixo
das duas médias históricas (41,7 e 43,3) e exatamente no ritmo que o modelo
(treinado só em 2006–2023, sem ver 2024) classifica como **49,2% de chance de
cair**: um cara-ou-coroa. Dali em diante o time somou **24 pontos nas últimas 8
rodadas** (3,0 pontos por jogo, ritmo de primeiro time do turno), fechou com 56
e terminou a boa distância da degola.

![Pelotão do rebaixamento em 2024 pela rodada 30](outputs/figures/04_pelotao_rebaixamento_2024_rodada30.png)

Olhando o pelotão inteiro na rodada 30 (tabela completa em
[outputs/tables/caso_2024_rodada30.csv](outputs/tables/caso_2024_rodada30.csv)):
o modelo acertou **18 dos 20 clubes** ao classificar acima ou abaixo de 50% de
risco. As duas exceções são o oposto do Corinthians — **Athletico-PR** (34 pts,
26% de risco pelo modelo) e **Criciúma** (36 pts, 12%) tinham ritmo melhor que
o Corinthians na mesma rodada e mesmo assim caíram, porque pioraram no returno
enquanto o Corinthians melhorou. O ritmo acumulado é um bom resumo do que já
aconteceu; não prevê virada de chave.

## Ressalvas

- O modelo usa **um único regressor** (ritmo em pontos). Não entra força do
  elenco, calendário restante, nem momento (sequência de resultados recentes)
  — deliberadamente, para isolar a pergunta "o placar até aqui já diz alguma
  coisa?" antes de qualquer variável extra. As duas falhas do estudo de caso
  (Athletico-PR, Criciúma) são exatamente o tipo de informação que ficou de
  fora.
- Com ritmos muito separados nas rodadas mais avançadas (rodada 35: quase
  nenhum time "no meio do caminho" entre salvo e rebaixado), o ajuste logístico
  esbarra em quase-separação — o coeficiente ainda é estimado e o p-valor é
  válido, mas o intervalo de confiança do coeficiente é largo nessas rodadas. A
  AUC e o Brier fora da amostra continuam a leitura mais confiável do
  desempenho.
- Painel pequeno: 18 temporadas de treino × 20 clubes = 360 linhas por rodada
  de corte. A validação fora da amostra (leave-one-season-out) existe
  justamente para não confiar demais no ajuste dentro da amostra.
- A "linha de segurança" descritiva olha só posição final, não pontos por jogo
  — não é comparável entre temporadas de formato diferente, por isso o recorte
  em 2006+.

## Metodologia

Regressão logística é uma metodologia nova neste portfólio; a formulação,
suposições e interpretação (razão de chances, pseudo-R², validação fora da
amostra) estão documentadas em
[statistical-methodologies](https://github.com/FelipeSantanaJ/statistical-methodologies)
— nível 2 (intuição) e nível 3 (formulação completa). A tendência da linha de
segurança reaproveita o método de mínimos quadrados ponderados já usado na
análise 01, também documentado lá.

## Arquivos

- `run.py` — gera tudo abaixo.
- `outputs/tables/` — `linha_de_seguranca_por_temporada`,
  `tendencia_linha_de_seguranca`, `painel_ritmo_temporada_clube`,
  `modelo_ritmo_por_rodada`, `validacao_fora_da_amostra`,
  `caso_2024_rodada30`, `trajetoria_corinthians_2024`.
- `outputs/figures/` — as 4 figuras acima.
- `src/futebrasil/permanencia.py` — linha de segurança, painel de ritmo, ajuste
  do modelo por rodada, validação fora da amostra.
