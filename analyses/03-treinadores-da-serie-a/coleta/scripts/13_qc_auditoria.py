"""Testes de consistência e resumo de auditoria. Saída: relatorio/_auditoria.md e dados/auditoria_resumo_*.csv"""
import pathlib, sys
import pandas as pd, numpy as np
BASE = pathlib.Path(__file__).resolve().parent.parent; D = BASE / "dados"; OUT = BASE / "relatorio"; OUT.mkdir(exist_ok=True)
A = pd.read_csv(D / "treinadores_por_partida_2003_2025.csv", dtype={"tm_id_jogo": str})
P = pd.read_csv(D / "partidas_serie_a_2003_2025.csv", dtype={"tm_id_jogo": str})
PS = pd.read_csv(D / "passagens_treinadores_2003_2025.csv")
L = []
def ok(nome, cond, det=""): L.append(f"| {nome} | {'OK' if cond else 'FALHOU'} | {det} |")

# ---------------- testes
esperado = {2003: 552, 2004: 552, 2005: 462, 2016: 379}
cont = P.groupby("temporada").size()
ok("Partidas por temporada = formato da edição", all(cont.get(y, 0) == esperado.get(y, 380) for y in range(2003, 2026)),
   "2003-04: 552; 2005: 462; 2006-2025: 380 (2016: 379 — Chapecoense × Atlético-MG não disputado)")
ok("Nenhuma partida duplicada (temporada, mandante, visitante)", not P.duplicated(["temporada", "mandante", "visitante"]).any())
ok("Cada partida tem exatamente 2 linhas na tabela analítica", (A.groupby("tm_id_jogo").size() == 2).all())
m = A.pivot_table(index="tm_id_jogo", columns="casa_fora", values=["gols_feitos", "gols_sofridos"], aggfunc="first")
ok("Gols feitos de um lado = gols sofridos do outro", ((m["gols_feitos"]["casa"] == m["gols_sofridos"]["fora"]) & (m["gols_feitos"]["fora"] == m["gols_sofridos"]["casa"])).all())
g = A.groupby("treinador_id").agg(j=("pontos", "size"), v=("resultado", lambda s: (s == "V").sum()), e=("resultado", lambda s: (s == "E").sum()), d=("resultado", lambda s: (s == "D").sum()))
ok("V + E + D = jogos (todos os treinadores)", ((g.v + g.e + g.d) == g.j).all())
pts = A.groupby("tm_id_jogo").pontos.sum()
res = np.where(P.gols_mandante > P.gols_visitante, "mandante", np.where(P.gols_mandante == P.gols_visitante, "empate", "visitante"))
ok("Coluna resultado do arquivo de partidas coerente com o placar", (res == P.resultado).all())
hm = A[A.casa_fora == "casa"].set_index("tm_id_jogo").reindex(P.tm_id_jogo)
ok("Placar e treinadores do arquivo de partidas = tabela analítica", (hm.gols_feitos.values == P.gols_mandante.values).all() and (hm.treinador.values == P.treinador_mandante.values).all())
ok("Pontos por partida ∈ {2 (empate), 3 (vitória)}", pts.isin([2, 3]).all())
pa = P[P.confere_placar_adaoduque.notna() & (P.confere_placar_adaoduque.astype(str) != "")]
conf_ad = (pa.confere_placar_adaoduque.astype(str) == "True").mean()
ok("Placar TM = placar adaoduque/CBF (2003-2024)", conf_ad > 0.995, f"{conf_ad:.2%} de {len(pa)} partidas")
# placares x matriz de confrontos da Wikipédia (pt), quando existe
import io, re
sys.path.insert(0, str(BASE / "scripts"))
from wiki_parse import clube as wclube
wrows = []
for y in range(2003, 2026):
    h = (BASE / "raw" / "wiki" / f"{y}.html").read_text(encoding="utf-8")
    i = h.find('id="Confrontos"')
    if i < 0: continue
    j = h.find("<h2", i + 10)
    try: ts = pd.read_html(io.StringIO(h[i:j]))
    except Exception: continue
    for t in ts:
        n = len(t)
        if t.shape[1] != n + 1 or n < 18: continue
        names = [wclube(x) for x in t.iloc[:, 0]]
        for a in range(n):
            for b in range(n):
                v = str(t.iloc[a, b + 1])
                m = re.match(r"^\s*(\d+)\s*[–-]\s*(\d+)", v)
                if a != b and m and names[a] and names[b]:
                    wrows.append(dict(temporada=y, mandante=names[a], visitante=names[b], placar_wiki=f"{m.group(1)}-{m.group(2)}"))
        break
WR = pd.DataFrame(wrows)
cw = P.merge(WR, on=["temporada", "mandante", "visitante"], how="inner")
cw["ok"] = cw.placar_wiki == cw.gols_mandante.astype(str) + "-" + cw.gols_visitante.astype(str)
ok("Placar TM = matriz de confrontos da Wikipédia", cw.ok.mean() > 0.995, f"{cw.ok.mean():.2%} de {len(cw)} partidas ({cw.temporada.nunique()} temporadas; 2025: {cw[cw.temporada==2025].ok.mean():.2%} de {(cw.temporada==2025).sum()})")
cw[~cw.ok].to_csv(D / "auditoria_placares_wiki_divergentes.csv", index=False, encoding="utf-8-sig")
diverg = pa[pa.confere_placar_adaoduque.astype(str) == "False"]
diverg.to_csv(D / "auditoria_placares_divergentes.csv", index=False, encoding="utf-8-sig")
# um técnico não pode dirigir dois clubes no mesmo dia / passagens sobrepostas
x = A[A.treinador != "DESCONHECIDO"].groupby(["treinador_id", "data"]).clube.nunique()
ok("Nenhum treinador em dois clubes na mesma data", (x <= 1).all(), f"{(x > 1).sum()} casos")
ov = []
PSc = PS[PS.status != "verificar"]
Am = A[~A.status_atribuicao.isin(["ambíguo", "sem_treinador", "inferido"])]
for t, gg in Am.sort_values("data").assign(seg=lambda d: (d.clube != d.groupby("treinador").clube.shift()).cumsum()).groupby(["treinador", "seg"]).agg(clube=("clube", "first"), inicio=("data", "min"), fim=("data", "max")).reset_index().groupby("treinador"):
    gg = gg.sort_values("inicio").reset_index(drop=True)
    for i in range(1, len(gg)):
        if gg.clube[i] != gg.clube[i - 1] and gg.inicio[i] < gg.fim[i - 1]:
            ov.append((t, gg.clube[i - 1], gg.fim[i - 1], gg.clube[i], gg.inicio[i]))
ok("Passagens (atribuições não incertas) de um treinador em clubes diferentes não se sobrepõem", len(ov) == 0, f"{len(ov)} sobreposições: {ov[:5]}")
nm = A.groupby("treinador").treinador_id.nunique()
ok("Nenhum nome padronizado com duas identidades", (nm <= 1).all(), ", ".join(nm[nm > 1].index))
idn = A.groupby("treinador_id").treinador.nunique()
ok("Nenhuma identidade com dois nomes padronizados", (idn <= 1).all())

# ---------------- auditoria
tot_lados = len(A); n_part = len(P)
st = A.status_atribuicao.value_counts()
incertos = A[A.status_atribuicao.isin(["ambíguo", "sem_treinador", "inferido"])]
part_incertas = incertos.tm_id_jogo.nunique()
fontes = A.fonte.fillna("").value_counts()
uma_fonte = A[A.fonte.fillna("").isin(["TM", "OG"])]
por_ano = A.groupby("temporada").agg(lados=("pontos", "size"), confirmados=("status_atribuicao", lambda s: (s == "confirmado").sum()),
                                     provaveis=("status_atribuicao", lambda s: (s == "provável").sum()),
                                     ambiguos=("status_atribuicao", lambda s: (s == "ambíguo").sum()),
                                     sem_treinador=("status_atribuicao", lambda s: (s == "sem_treinador").sum()),
                                     inferidos=("status_atribuicao", lambda s: (s == "inferido").sum()),
                                     so_uma_fonte=("fonte", lambda s: s.fillna("").isin(["TM", "OG"]).sum()),
                                     ausencia_reatribuida=("atribuicao_original", lambda s: s.fillna("").ne("").sum()))
por_ano["pct_confirmado"] = (por_ano.confirmados / por_ano.lados).round(3)
# trocas de comando dentro da temporada (sequência já com ausências pontuais devolvidas ao titular)
tro = []
for (cl, y), gg in A.sort_values("data").groupby(["clube", "temporada"]):
    runs = []
    for t in gg.treinador:
        if runs and runs[-1][0] == t: runs[-1][1] += 1
        else: runs.append([t, 1])
    seq = [r[0] for r in runs]
    efet = [r[0] for k, r in enumerate(runs) if r[1] > 3 or k == 0]
    efet = [t for k, t in enumerate(efet) if k == 0 or t != efet[k - 1]]
    tro.append(dict(clube=cl, temporada=y, trocas=len(seq) - 1, trocas_sem_interinos_curtos=len(efet) - 1, treinadores=len(set(seq)),
                    sequencia=" > ".join(f"{t} ({n})" for t, n in runs)))
TRO = pd.DataFrame(tro)
tpe = TRO.groupby("temporada").trocas_sem_interinos_curtos.sum()
TRO.to_csv(D / "auditoria_trocas_por_clube_temporada.csv", index=False, encoding="utf-8-sig")
tpa = TRO.groupby("temporada").trocas.sum()
interinos = PS.drop_duplicates("passagem_id").interino_provavel.sum()
lance = {2003: 40, 2004: 38, 2005: 37, 2010: 31, 2015: 32, 2018: 29, 2020: 28, 2023: 25, 2024: 21}
por_ano["trocas_reconstruidas"] = tpa
por_ano["trocas_sem_interinos_curtos"] = tpe
por_ano["trocas_lance_ge"] = pd.Series(lance)
por_ano.to_csv(D / "auditoria_resumo_por_temporada.csv", encoding="utf-8-sig")
por_clube = A.groupby("clube").agg(lados=("pontos", "size"), pct_confirmado=("status_atribuicao", lambda s: round((s == "confirmado").mean(), 3)),
                                   incertos=("status_atribuicao", lambda s: s.isin(["ambíguo", "sem_treinador", "inferido"]).sum())).sort_values("pct_confirmado")
por_clube.to_csv(D / "auditoria_resumo_por_clube.csv", encoding="utf-8-sig")
obs = A.observacao.fillna("")
conf_mask = obs.str.contains("O Gol atribui|TM registra|conflito TM x O Gol")
conf_res = dict(total=int(conf_mask.sum()),
                og_cbf=int(obs.str.contains("TM registra").sum()),
                wiki=int(obs.str.contains("resolvido pela data da troca").sum()),
                continuidade=int(obs.str.contains("resolvido por continuidade").sum()),
                ambiguo=int((conf_mask & (A.status_atribuicao == "ambíguo")).sum()))
cbf_aux = int(obs.str.contains("CBF registra").sum())
so1 = A[A.treinador != "DESCONHECIDO"].groupby("treinador").fonte.agg(lambda s: set("+".join(s.fillna("")).split("+")) - {""})
so1 = so1[so1.map(lambda x: len(x) == 1)]

md = ["# Auditoria", "", "## Testes de consistência", "", "| Teste | Resultado | Detalhe |", "|---|---|---|"] + L
md += ["", "## Números da base", "",
       f"- Partidas: **{n_part}** (9.166 programadas; 1 não disputada excluída: Chapecoense × Atlético-MG, 2016).",
       f"- Lados treinador×partida: **{tot_lados}**.",
       f"- Status: " + ", ".join(f"{k}: {v}" for k, v in st.items()) + ".",
       f"- Fontes por lado: " + ", ".join(f"{k or '(nenhuma)'}: {v}" for k, v in fontes.items()) + ".",
       f"- Lados com **uma só fonte** (TM ou OG): {len(uma_fonte)}.",
       f"- Lados sem treinador identificado: {st.get('sem_treinador', 0)}; inferidos por continuidade: {st.get('inferido', 0)}; ambíguos: {st.get('ambíguo', 0)}.",
       f"- **{part_incertas} partidas ainda possuem atribuição incerta** (ao menos um lado ambíguo, inferido ou sem treinador).",
       f"- **Lados com treinador conflitante entre fontes (TM × O Gol): {conf_res['total']}** — resolvidos por O Gol+CBF contra o TM: {conf_res['og_cbf']}; pela data da troca na Wikipédia: {conf_res['wiki']}; por continuidade: {conf_res['continuidade']}; ainda ambíguos: {conf_res['ambiguo']} (o restante caiu na regra de ausência pontual ou de impossibilidade cronológica).",
       f"- Ausências pontuais devolvidas ao titular (regra de suspensão/ausência): {A.atribuicao_original.fillna('').ne('').sum()} lados.",
       f"- Divergências CBF × (TM+OG) em que a súmula CBF traz outro nome (auxiliar no banco): {A.observacao.fillna('').str.contains('CBF registra').sum()} lados.",
       f"- Treinadores distintos: {A[A.treinador!='DESCONHECIDO'].treinador_id.nunique()}; identificados por uma única fonte em toda a carreira: {len(so1)} ({', '.join(sorted(so1.index)[:40])}{'…' if len(so1)>40 else ''}).",
       f"- Passagens (sequências contínuas treinador×clube): {PS.passagem_id.nunique()}; prováveis interinos (≤3 jogos entre dois técnicos diferentes): {interinos}.",
       f"- Trocas de comando dentro das temporadas (reconstruídas): {int(tpa.sum())}.", ""]
(OUT / "_auditoria.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md)); print(por_ano.to_string()); print(por_clube.head(12).to_string())
