# Auditoria

## Testes de consistência

| Teste | Resultado | Detalhe |
|---|---|---|
| Partidas por temporada = formato da edição | OK | 2003-04: 552; 2005: 462; 2006-2025: 380 (2016: 379 — Chapecoense × Atlético-MG não disputado) |
| Nenhuma partida duplicada (temporada, mandante, visitante) | OK |  |
| Cada partida tem exatamente 2 linhas na tabela analítica | OK |  |
| Gols feitos de um lado = gols sofridos do outro | OK |  |
| V + E + D = jogos (todos os treinadores) | OK |  |
| Coluna resultado do arquivo de partidas coerente com o placar | OK |  |
| Placar e treinadores do arquivo de partidas = tabela analítica | OK |  |
| Pontos por partida ∈ {2 (empate), 3 (vitória)} | OK |  |
| Placar TM = placar adaoduque/CBF (2003-2024) | OK | 100.00% de 8785 partidas |
| Placar TM = matriz de confrontos da Wikipédia | OK | 99.75% de 7643 partidas (20 temporadas; 2025: 100.00% de 380) |
| Nenhum treinador em dois clubes na mesma data | OK | 0 casos |
| Passagens (atribuições não incertas) de um treinador em clubes diferentes não se sobrepõem | OK | 0 sobreposições: [] |
| Nenhum nome padronizado com duas identidades | OK |  |
| Nenhuma identidade com dois nomes padronizados | OK |  |

## Números da base

- Partidas: **9165** (9.166 programadas; 1 não disputada excluída: Chapecoense × Atlético-MG, 2016).
- Lados treinador×partida: **18330**.
- Status: confirmado: 17388, provável: 814, ambíguo: 91, sem_treinador: 32, inferido: 5.
- Fontes por lado: TM+OG: 9254, TM+OG+CBF: 7646, TM: 595, TM+CBF: 466, OG+Wiki: 102, OG+CBF: 91, OG: 79, TM+Wiki: 60, (nenhuma): 37.
- Lados com **uma só fonte** (TM ou OG): 674.
- Lados sem treinador identificado: 32; inferidos por continuidade: 5; ambíguos: 91.
- **127 partidas ainda possuem atribuição incerta** (ao menos um lado ambíguo, inferido ou sem treinador).
- **Lados com treinador conflitante entre fontes (TM × O Gol): 428** — resolvidos por O Gol+CBF contra o TM: 83; pela data da troca na Wikipédia: 163; por continuidade: 50; ainda ambíguos: 85 (o restante caiu na regra de ausência pontual ou de impossibilidade cronológica).
- Ausências pontuais devolvidas ao titular (regra de suspensão/ausência): 80 lados.
- Divergências CBF × (TM+OG) em que a súmula CBF traz outro nome (auxiliar no banco): 146 lados.
- Treinadores distintos: 353; identificados por uma única fonte em toda a carreira: 13 (Claudiomiro, Gilson Gênio, Júlio César Leal, Júnior, Leonardo Galbes, Mozart, Murtosa, Mário Jorge, Paulo Campos, Pedro Santilli, Riva Carli, Roberto Cavalo, Toninho Barroso).
- Passagens (sequências contínuas treinador×clube): 1165; prováveis interinos (≤3 jogos entre dois técnicos diferentes): 174.
- Trocas de comando dentro das temporadas (reconstruídas): 833.
