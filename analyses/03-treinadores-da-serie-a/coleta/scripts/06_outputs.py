"""Gera os CSVs finais a partir de raw/_sides.pkl e raw/_meta.pkl."""
import pathlib, sys
import pandas as pd
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import CLUBES, nome_epoca, fold

BASE = pathlib.Path(__file__).resolve().parent.parent
R, D = BASE / "raw", BASE / "dados"; D.mkdir(exist_ok=True)
S = pd.read_pickle(R / "_sides.pkl"); M = pd.read_pickle(R / "_meta.pkl")
fx, pname = M["fx"], M["pname"]
tm2og = {v: k for k, v in M["og2tm"].items()}
fx["ogol_id"] = fx.tm_id_jogo.map(tm2og)
if "atribuicao_original" not in S: S["atribuicao_original"] = ""
S["atribuicao_original"] = S.atribuicao_original.fillna("")

# ------------------------------------------------------------ tabela analítica (uma linha por clube/treinador por partida)
f = fx.set_index("tm_id_jogo")
rows = []
for r in S.itertuples():
    m = f.loc[r.tm_id_jogo]
    casa = r.lado == "m"
    gf, ga = (m.gm, m.gv) if casa else (m.gv, m.gm)
    res = "V" if gf > ga else ("E" if gf == ga else "D")
    rows.append(dict(
        temporada=r.temporada, data=r.data, rodada=m.rodada,
        clube=CLUBES[r.clube_tm_id], clube_nome_epoca=nome_epoca(r.clube_tm_id, r.temporada),
        treinador=r.treinador if r.treinador else "DESCONHECIDO", treinador_id=r.pessoa,
        adversario=m.visitante if casa else m.mandante, casa_fora="casa" if casa else "fora",
        gols_feitos=gf, gols_sofridos=ga, resultado=res, pontos={"V": 3, "E": 1, "D": 0}[res],
        status_atribuicao=r.status, fonte=r.fonte,
        nome_original_tm=r.tm_nome, nome_original_ogol=r.og_nome, nome_original_cbf=r.cbf_nome,
        atribuicao_original=r.atribuicao_original, observacao="; ".join(x for x in (r.obs, r.regra) if x),
        tm_id_jogo=r.tm_id_jogo, ogol_id=m.ogol_id if pd.notna(m.ogol_id) else ""))
A = pd.DataFrame(rows).sort_values(["temporada", "data", "tm_id_jogo", "casa_fora"])
A.to_csv(D / "treinadores_por_partida_2003_2025.csv", index=False, encoding="utf-8-sig")

# ------------------------------------------------------------ partidas (uma linha por jogo)
H = A[A.casa_fora == "casa"].set_index("tm_id_jogo"); V = A[A.casa_fora == "fora"].set_index("tm_id_jogo")
P = fx.set_index("tm_id_jogo")
P = pd.DataFrame(dict(
    temporada=P.temporada, rodada=P.rodada, data=P.data, hora=P.hora,
    mandante=P.mandante, visitante=P.visitante, mandante_nome_epoca=P.mandante_nome_epoca, visitante_nome_epoca=P.visitante_nome_epoca,
    treinador_mandante=H.treinador, treinador_visitante=V.treinador,
    gols_mandante=P.gm, gols_visitante=P.gv,
    resultado=pd.Series(["mandante" if a > b else ("empate" if a == b else "visitante") for a, b in zip(P.gm, P.gv)], index=P.index),
    status_mandante=H.status_atribuicao, status_visitante=V.status_atribuicao,
    fonte_treinador_mandante=H.fonte, fonte_treinador_visitante=V.fonte,
    placar_cbf_adaoduque=P.ad_gm.fillna("").astype(str) + "-" + P.ad_gv.fillna("").astype(str),
    ogol_id=P.ogol_id, fonte_partida="Transfermarkt (lista de jogos BRA1); placar conferido com adaoduque/CBF (2003-2024) e matriz de confrontos da Wikipédia")).reset_index()
P["confere_placar_adaoduque"] = [("" if pc == "-" else str(pc == f"{a}-{b}")) for pc, a, b in zip(P.placar_cbf_adaoduque, P.gols_mandante, P.gols_visitante)]
P = P.sort_values(["temporada", "data", "tm_id_jogo"])
P.to_csv(D / "partidas_serie_a_2003_2025.csv", index=False, encoding="utf-8-sig")

# ------------------------------------------------------------ passagens (sequências contínuas treinador x clube, por temporada)
A2 = A.sort_values(["clube", "data", "tm_id_jogo"]).reset_index(drop=True)
A2["novo"] = (A2.treinador != A2.groupby("clube").treinador.shift())
A2["passagem_id"] = A2.novo.cumsum()
A2["seg"] = (A2.novo | (A2.temporada != A2.groupby("clube").temporada.shift())).cumsum()
seg = A2.groupby("seg").agg(treinador=("treinador", "first"), clube=("clube", "first"), temporada=("temporada", "first"),
                            inicio=("data", "min"), fim=("data", "max"), jogos=("data", "size"),
                            V=("resultado", lambda s: (s == "V").sum()), E=("resultado", lambda s: (s == "E").sum()), D=("resultado", lambda s: (s == "D").sum()),
                            fonte=("fonte", lambda s: Counter(s).most_common(1)[0][0]),
                            pct_confirmado=("status_atribuicao", lambda s: round((s == "confirmado").mean(), 3)),
                            passagem_id=("passagem_id", "first")).reset_index(drop=True)
seg["jogos_passagem_total"] = seg.groupby("passagem_id").jogos.transform("sum")
seg["status"] = seg.pct_confirmado.map(lambda x: "confirmado" if x >= 0.8 else ("provável" if x >= 0.3 else "verificar"))
# interino provável: passagem curta (<=3 jogos) entre dois treinadores diferentes na mesma temporada
pas = A2.groupby("passagem_id").agg(clube=("clube", "first"), treinador=("treinador", "first"), j=("data", "size"), t0=("temporada", "first"), t1=("temporada", "last")).reset_index()
pas["ant"] = pas.groupby("clube").treinador.shift(); pas["pos"] = pas.groupby("clube").treinador.shift(-1)
pas["ant_t"] = pas.groupby("clube").t1.shift(); pas["pos_t"] = pas.groupby("clube").t0.shift(-1)
pas["interino_provavel"] = (pas.j <= 3) & pas.ant.notna() & pas.pos.notna() & (pas.ant_t == pas.t0) & (pas.pos_t == pas.t1)
seg = seg.merge(pas[["passagem_id", "interino_provavel", "ant", "pos"]].rename(columns={"ant": "antecessor", "pos": "sucessor"}), on="passagem_id")
seg.to_csv(D / "passagens_treinadores_2003_2025.csv", index=False, encoding="utf-8-sig")

# ------------------------------------------------------------ normalização de nomes
nrows = []
for src, col_n, col_p in (("Transfermarkt", "tm_nome", "p_tm"), ("O Gol", "og_nome", "p_og")):
    g = S[S[col_p] != ""].groupby([col_n, col_p]).size().rename("jogos").reset_index()
    for r in g.itertuples():
        nrows.append(dict(nome_original=getattr(r, col_n), nome_padronizado=pname[getattr(r, col_p)], fonte=src,
                          treinador_id=getattr(r, col_p), jogos=r.jogos, observacao=""))
g = A[A.nome_original_cbf.fillna("") != ""].groupby(["nome_original_cbf", "treinador"]).size().rename("jogos").reset_index()
for r in g.itertuples():
    nrows.append(dict(nome_original=r.nome_original_cbf, nome_padronizado=r.treinador, fonte="CBF (via adaoduque)", treinador_id="",
                      jogos=r.jogos, observacao="coocorrência no mesmo jogo/lado; se nome diferir do titular, pode ser auxiliar que assinou a súmula"))
N = pd.DataFrame(nrows)
N["observacao"] = [o or ("idêntico" if fold(a) == fold(b) else "variação de grafia/apelido") for o, a, b in zip(N.observacao, N.nome_original, N.nome_padronizado)]
N.sort_values(["nome_padronizado", "fonte", "jogos"], ascending=[True, True, False]).to_csv(D / "normalizacao_treinadores.csv", index=False, encoding="utf-8-sig")

# clubes
C = []
for tid, c in CLUBES.items():
    for y in sorted(set(fx.temporada[(fx.mandante_tm_id == tid)])):
        C.append(dict(tm_id=tid, clube_padronizado=c, temporada=y, nome_no_periodo=nome_epoca(tid, y)))
C = pd.DataFrame(C)
C.groupby(["tm_id", "clube_padronizado", "nome_no_periodo"]).temporada.agg(lambda s: ",".join(map(str, s))).reset_index().to_csv(D / "normalizacao_clubes.csv", index=False, encoding="utf-8-sig")

# ------------------------------------------------------------ auditoria
au = A[(A.status_atribuicao != "confirmado") | (A.observacao != "")].copy()
au["tipo"] = au.status_atribuicao
au.loc[au.atribuicao_original != "", "tipo"] = "ausencia_pontual_reatribuida"
au.loc[au.observacao.str.contains("CBF registra", na=False) & (au.status_atribuicao == "confirmado"), "tipo"] = "cbf_diverge_(auxiliar_na_sumula)"
au.loc[au.observacao.str.contains("CBF desempata", na=False), "tipo"] = "conflito_tm_ogol_resolvido_por_cbf"
au.to_csv(D / "auditoria_treinadores.csv", index=False, encoding="utf-8-sig")
print(A.status_atribuicao.value_counts()); print(au.tipo.value_counts())
