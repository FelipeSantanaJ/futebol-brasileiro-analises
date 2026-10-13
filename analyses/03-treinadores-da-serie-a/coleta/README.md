# Coleta — base treinador × partida

Scripts que montaram `data/external/treinadores/`. Eles **raspam páginas web**
(Transfermarkt, O Gol e Wikipédia), demoram horas e dependem da estrutura atual
desses sites; por isso a base pronta é versionada e o `run.py` da análise não os
executa. Ficam aqui para auditoria e reprodução.

Rodam a partir desta pasta (`coleta/`): gravam o HTML bruto em `raw/` (~600 MB,
fora do git), os arquivos finais em `dados/` e o relatório de auditoria em
`relatorio/`. Os arquivos versionados em `data/external/treinadores/` são cópias
de `dados/`.

| Ordem | Script | O que faz |
|---|---|---|
| 1 | `01_tm_fixtures.py` | calendário da Série A no Transfermarkt, 2003–2025 (9.166 jogos com ID da súmula) |
| 2 | `02_tm_reports.py` | baixa cada súmula do Transfermarkt (retomável; `rev` percorre de trás para frente) |
| 3 | `03_ogol_scrape.py`, `03b_ogol_rev.py` | calendário e páginas de jogo do O Gol (usadas só para ligar IDs; o técnico dessas páginas é descartado) |
| 4 | `04_parse.py` | extrai técnicos das súmulas (TM) e times/placar das páginas O Gol |
| 5 | `09_ogol_treinadores.py` | ID O Gol de cada técnico (busca do site) e suas listas "jogos realizados" por temporada |
| 6 | `10_ogol_faltantes.py`, `11_ogol_lacunas.py`, `12_ogol_wiki_alvos.py` | completa o O Gol: técnicos não achados na busca, lacunas por clube e técnicos citados pela Wikipédia |
| 7 | `wiki_parse.py` | tabelas de troca de técnico da Wikipédia, com datas |
| 8 | `05_build.py` | cruza TM × O Gol × CBF × Wikipédia, normaliza nomes e aplica as regras de atribuição |
| 9 | `06_outputs.py` | grava as tabelas finais (partidas, treinador por partida, passagens, normalização, auditoria) |
| 10 | `08_valida_wiki.py` | valida as trocas contra a Wikipédia (`SEM_WIKI=1` gera a versão independente) |
| 11 | `13_qc_auditoria.py` | 14 testes de consistência e resumo de auditoria (`auditoria.md`) |

Apoio: `common.py` (clubes, slugs), `parsers.py` (leitura das páginas),
`ajustes_manuais.json` (homônimos e outros ajustes, cada um justificado).

Os passos 5 e 6 precisam do resultado do passo 8 (mapa de jogos O Gol × TM);
na prática a ordem foi 1–4, 8, 5–6, 8 de novo, 9–11.

## Armadilhas encontradas

- **Súmulas do O Gol corrompidas para coletores:** escalações de outros jogos
  (ex.: Santos × Paysandu 2003 com técnicos de Austrália × Turquia) e placares
  que batem com a CBF em ~3% dos jogos. Descartadas; as listas por técnico do
  mesmo site são confiáveis (97,9% de concordância com a CBF).
- **A busca do O Gol é AJAX** (`jqc_search_solr.php?queryString=`).
- **Slug de time → clube** não pode ser aprendido por data (jogos adiados têm
  datas diferentes em cada fonte): o mapa é fixo em `common.py`.
- **Perfis duplicados no Transfermarkt** (ex.: Marcelo Oliveira com dois IDs)
  são unificados quando apontam ao mesmo técnico no O Gol.
