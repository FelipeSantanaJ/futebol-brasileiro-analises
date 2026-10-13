"""Cruza Transfermarkt (TM, súmula) x O Gol (lista 'jogos realizados' do treinador) x CBF/adaoduque (2014-2024)
e atribui um treinador por partida/lado. Identidade do treinador = ID Transfermarkt.
Saídas: raw/_sides.pkl, raw/_meta.pkl"""
import pathlib, sys, json, re
import pandas as pd
from collections import Counter, defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import CLUBES, nome_epoca, fold, ADAO, SLUG_OGOL

BASE = pathlib.Path(__file__).resolve().parent.parent
R = BASE / "raw"
MAN = json.load(open(BASE / "scripts" / "ajustes_manuais.json", encoding="utf-8"))

# ---------------------------------------------------------------- partidas (TM)
fx = pd.read_csv(R / "tm_fixtures.csv", dtype=str)
nao_disputada = fx[~fx.placar.str.match(r"^\d+:\d+$")]
fx = fx[fx.placar.str.match(r"^\d+:\d+$")].copy()
fx["temporada"] = fx.temporada.astype(int); fx["rodada"] = fx.rodada.astype(int)
fx[["gm", "gv"]] = fx.placar.str.split(":", expand=True).astype(int)
fx["mandante"] = fx.mandante_tm_id.map(CLUBES); fx["visitante"] = fx.visitante_tm_id.map(CLUBES)
assert fx.mandante.notna().all() and fx.visitante.notna().all()
fx["mandante_nome_epoca"] = [nome_epoca(i, y) for i, y in zip(fx.mandante_tm_id, fx.temporada)]
fx["visitante_nome_epoca"] = [nome_epoca(i, y) for i, y in zip(fx.visitante_tm_id, fx.temporada)]
fx = fx.merge(pd.read_csv(R / "tm_coaches.csv", dtype=str).fillna(""), on="tm_id_jogo", how="left")

# ---------------------------------------------------------------- O Gol: id do jogo -> jogo TM (via slug data-mandante-visitante)
og = pd.read_csv(R / "ogol_parsed.csv", dtype=str).fillna("")
og = og[og.og_baixado == "1"]
fxd = defaultdict(list)
for r in fx.itertuples(): fxd[(r.data, r.gm, r.gv)].append(r)
votes = defaultdict(Counter)
for r in og.itertuples():
    if not r.og_gm: continue
    c = fxd.get((r.data, int(r.og_gm), int(r.og_gv)), [])
    if len(c) == 1:
        votes[r.og_mand][c[0].mandante_tm_id] += 1; votes[r.og_vis][c[0].visitante_tm_id] += 1
slug2tm = dict(SLUG_OGOL)
for s_, v in votes.items():  # checagem: votos por data+placar devem concordar com o dicionário
    if s_ in slug2tm and v.most_common(1)[0][0] != slug2tm[s_]: print('AVISO slug', s_, v.most_common(2))
links = pd.read_csv(R / "ogol_links.csv", dtype=str).drop_duplicates("ogol_id")
bydate = defaultdict(list)
for r in fx.itertuples(): bydate[r.data].append(r)
def split_slug(slug):
    d, rest = slug[:10], slug[11:]
    parts = rest.split("-")
    for k in range(1, len(parts)):
        a, b = "-".join(parts[:k]), "-".join(parts[k:])
        if a in slug2tm and b in slug2tm: return d, slug2tm[a], slug2tm[b], a, b
    for k in range(1, len(parts)):  # um dos lados desconhecido: resolve pela data
        a, b = "-".join(parts[:k]), "-".join(parts[k:])
        for known, pos in ((a, 0), (b, 1)):
            if known in slug2tm:
                c = [x for x in bydate[d] if (x.mandante_tm_id if pos == 0 else x.visitante_tm_id) == slug2tm[known]]
                if len(c) == 1:
                    other = b if pos == 0 else a
                    return d, c[0].mandante_tm_id, c[0].visitante_tm_id, a, b
    return None
key = {(r.temporada, r.mandante_tm_id, r.visitante_tm_id): r.tm_id_jogo for r in fx.itertuples()}
og2tm = {}
for _ in range(2):  # 2 passadas para aproveitar slugs aprendidos
    for r in links.itertuples():
        if r.ogol_id in og2tm: continue
        s = split_slug(r.slug)
        if s:
            k = (int(r.temporada), s[1], s[2])
            if k in key: og2tm[r.ogol_id] = key[k]
print(f"O Gol: {len(og2tm)} de {len(links)} jogos ligados ao TM", flush=True)

# ---------------------------------------------------------------- O Gol: evidência por jogo/lado
ids = pd.read_csv(R / "ogol_coach_ids.csv", dtype=str).fillna("")
cg = pd.read_csv(R / "ogol_coach_games.csv", dtype=str).fillna("")
# perfis duplicados no TM: dois IDs TM -> mesmo técnico O Gol e nomes compatíveis => mesma pessoa
ntm = pd.concat([fx.tm_tec_m_id, fx.tm_tec_v_id]).value_counts()
CANON, MERGES = {}, []
for oid, g in ids[ids.ogol_coach_id != ""].groupby("ogol_coach_id"):
    if len(g) < 2: continue
    nomes = {fold(n) for n in g.nome_tm}
    if len(nomes) == 1 or all(set(fold(a).split()) & set(fold(b).split()) for a in g.nome_tm for b in g.nome_tm):
        main = max(g.tm, key=lambda t: ntm.get(t, 0))
        for t in g.tm:
            if t != main: CANON[t] = main; MERGES.append(dict(tm_id=t, tm_id_unificado=main, nome=g.nome_tm.iloc[0], ogol_coach_id=oid))
    else:
        print("ATENÇÃO: IDs TM distintos com mesmo O Gol e nomes diferentes:", g[["tm", "nome_tm"]].values.tolist())
for a, b in MAN.get("unir_tm", []): CANON[a] = b; MERGES.append(dict(tm_id=a, tm_id_unificado=b, nome="(manual)", ogol_coach_id=""))
pd.DataFrame(MERGES).to_csv(R / "_tm_ids_unificados.csv", index=False)
for c in ("tm_tec_m_id", "tm_tec_v_id"): fx[c] = fx[c].map(lambda t: CANON.get(t, t))
cg["tm"] = cg.tm.map(lambda t: CANON.get(t, t)); ids["tm"] = ids.tm.map(lambda t: CANON.get(t, t))
ids = ids.assign(_o=(ids.status == "nao_encontrado")).sort_values("_o").drop_duplicates("tm").drop(columns="_o")
cg["tm_id_jogo"] = cg.ogol_id.map(og2tm)
# fallback não-circular: data (±3 dias) + adversário (slug do O Gol -> clube) no lado oposto
fxl = fx[["tm_id_jogo", "data", "mandante_tm_id", "visitante_tm_id"]].assign(d=lambda x: pd.to_datetime(x.data))
for i in cg.index[cg.tm_id_jogo.isna()]:
    adv = slug2tm.get(cg.at[i, "adversario_slug"]); d = pd.to_datetime(cg.at[i, "data"])
    if not adv: continue
    col = "visitante_tm_id" if cg.at[i, "cf"] == "C" else "mandante_tm_id"
    c = fxl[(fxl[col] == adv) & ((fxl.d - d).abs() <= pd.Timedelta(days=3))]
    if len(c) == 1: cg.at[i, "tm_id_jogo"] = c.tm_id_jogo.iloc[0]; og2tm[cg.at[i, "ogol_id"]] = c.tm_id_jogo.iloc[0]
cg["lado"] = cg.cf.map({"C": "m", "F": "v"})
# técnicos 'og:<id>' (sem ID TM ligado): unifica com o ID TM que aparece no mesmo jogo/lado na maioria dos jogos, se o nome for compatível
tmside = {}
for r in fx.itertuples(): tmside[(r.tm_id_jogo, "m")] = r.tm_tec_m_id; tmside[(r.tm_id_jogo, "v")] = r.tm_tec_v_id
cg["_tm_lado"] = [tmside.get((j, l), "") for j, l in zip(cg.tm_id_jogo, cg.lado)]
tmn = dict(zip(pd.concat([fx.tm_tec_m_id, fx.tm_tec_v_id]), pd.concat([fx.tm_tec_m, fx.tm_tec_v])))
ogn = ids.set_index("tm").nome_ogol.to_dict()
OGMERGE = {}
for p, g in cg[cg.tm.str.startswith("og:")].groupby("tm"):
    v = g._tm_lado[g._tm_lado != ""].value_counts()
    if len(v) == 0: continue
    t, n = v.index[0], v.iloc[0]
    a, b = set(fold(ogn.get(p, "")).split()), set(fold(tmn.get(t, "")).split())
    if n / len(g) >= 0.6 and (a & b or fold(ogn.get(p, "")).replace(" ", "") in fold(tmn.get(t, "")).replace(" ", "")):
        OGMERGE[p] = t
cg["tm"] = cg.tm.map(lambda t: OGMERGE.get(t, t))
ids = ids[~ids.tm.isin(OGMERGE)]
pd.DataFrame([(k, ogn.get(k), v, tmn.get(v)) for k, v in OGMERGE.items()], columns=["ogol", "nome_ogol", "tm_id", "nome_tm"]).to_csv(R / "_ogol_unificados_tm.csv", index=False)
print("O Gol-only unificados a IDs TM:", len(OGMERGE), "| restantes só O Gol:", cg.tm.str.startswith("og:").groupby(cg.tm).any().sum(), flush=True)
cg = cg.dropna(subset=["tm_id_jogo", "lado"]).drop_duplicates(["tm_id_jogo", "lado", "tm"])
og_ev = cg.groupby(["tm_id_jogo", "lado"]).tm.agg(lambda s: sorted(set(s))).to_dict()
og_placar = {og2tm[r.ogol_id]: f"{r.og_gm}-{r.og_gv}" for r in og.itertuples() if r.ogol_id in og2tm and r.og_gm != ""}  # título da súmula O Gol
fx["og_placar"] = fx.tm_id_jogo.map(og_placar)
og_name = ids.set_index("tm").nome_ogol.to_dict()
og_found = set(ids[ids.status == "ok"].tm)

# ---------------------------------------------------------------- CBF (adaoduque) 2014-2024
ad = pd.read_csv(R / "br_full.csv", dtype=str).fillna("")
ad["dt"] = pd.to_datetime(ad.data, format="%d/%m/%Y")
ad["temporada"] = ad.dt.dt.year
ad.loc[(ad.dt >= "2021-01-01") & (ad.dt < "2021-04-01"), "temporada"] = 2020
ad["mandante_tm_id"] = ad.mandante.map(ADAO); ad["visitante_tm_id"] = ad.visitante.map(ADAO)
assert ad.mandante_tm_id.notna().all()
ad = ad.rename(columns={"tecnico_mandante": "cbf_tec_m", "tecnico_visitante": "cbf_tec_v", "mandante_Placar": "ad_gm", "visitante_Placar": "ad_gv"})
fx = fx.merge(ad[["temporada", "mandante_tm_id", "visitante_tm_id", "cbf_tec_m", "cbf_tec_v", "ad_gm", "ad_gv"]],
              on=["temporada", "mandante_tm_id", "visitante_tm_id"], how="left")

# ---------------------------------------------------------------- lados
sides = []
for s in ("m", "v"):
    t = fx[["tm_id_jogo", "temporada", "data", f"tm_tec_{s}", f"tm_tec_{s}_id", f"cbf_tec_{s}"]].copy()
    t.columns = ["tm_id_jogo", "temporada", "data", "tm_nome", "tm_id", "cbf_nome"]
    t["lado"] = s; t["clube_tm_id"] = fx["mandante_tm_id" if s == "m" else "visitante_tm_id"]
    sides.append(t)
S = pd.concat(sides, ignore_index=True).fillna("")
S["og_tms"] = [og_ev.get((j, l), []) for j, l in zip(S.tm_id_jogo, S.lado)]

# ---------------------------------------------------------------- nomes padronizados
tm_names = S[S.tm_id != ""].groupby("tm_id").tm_nome.agg(lambda x: x.mode()[0])
pname = {}
for tid, n in tm_names.items():
    pname[tid] = MAN.get("nomes", {}).get(tid) or n
for r in ids[ids.tm.str.startswith("og:")].itertuples():  # treinadores que só existem no O Gol
    pname[r.tm] = MAN.get("nomes", {}).get(r.tm) or r.nome_ogol
    tm_names[r.tm] = r.nome_ogol
pid = {t: t for t in pname}
homon = {n for n, c in Counter(pname.values()).items() if c > 1}

# ---------------------------------------------------------------- CBF: compatibilidade de nome
ALIAS = defaultdict(set)
for t, n in pname.items():
    ALIAS[t].add(fold(n)); ALIAS[t].add(fold(tm_names[t]))
    if og_name.get(t): ALIAS[t].add(fold(og_name[t]))
for t, al in MAN.get("aliases_cbf", {}).items(): ALIAS[t].update(fold(a) for a in al)
STOP = {"de", "da", "do", "dos", "das", "e", "junior", "filho", "neto", "jr"}
COMUNS = {"silva", "santos", "oliveira", "souza", "sousa", "costa", "ferreira", "pereira", "rodrigues", "alves", "lima", "gomes", "carvalho", "ribeiro", "almeida", "barbosa", "campos", "martins", "araujo", "rocha"}
def _ok(a, c):
    if c == a: return True
    at, toks = a.split(), c.split()
    if not at or not toks: return False
    sob = [t for t in toks if len(t) > 1 and t not in STOP]
    hit = [t for t in sob if t in at]
    if hit and any(t.startswith(toks[0][0]) for t in at): return True
    if any(len(t) >= 5 and t not in COMUNS for t in hit): return True
    return False
CBF_ALIAS = set()
agree = S[(S.tm_id != "") & (S.cbf_nome != "")]
pc = agree.groupby([agree.cbf_nome.map(fold), "tm_id"]).size().rename("n").reset_index(); pc.columns = ["c", "p", "n"]
tot = pc.groupby("c").n.transform("sum")
for r in pc[(pc.n >= 3) & (pc.n / tot >= 0.8)].itertuples():
    if not any(_ok(a, r.c) for a in ALIAS[r.p]): CBF_ALIAS.add((r.p, r.c))
pd.DataFrame([(pname[p], c) for p, c in CBF_ALIAS], columns=["treinador", "nome_cbf"]).to_csv(R / "_cbf_aliases_aprendidos.csv", index=False)
def cbf_ok(p, cbf):
    if not p or not cbf: return None
    c = fold(cbf)
    return (p, c) in CBF_ALIAS or any(_ok(a, c) for a in ALIAS[p])

# ---------------------------------------------------------------- atribuição por lado
recs = []
for r in S.itertuples():
    tm, ogl, cbf = r.tm_id, r.og_tms, r.cbf_nome
    k = cbf_ok(tm, cbf) if tm else None
    if tm:
        fontes = ["TM"]; obs = []
        if tm in ogl: fontes.append("OG")
        elif ogl: obs.append("O Gol atribui a " + "/".join(pname[x] for x in ogl))
        elif tm not in og_found: obs.append("treinador não localizado no O Gol")
        else: obs.append("O Gol sem registro deste jogo para o treinador")
        if k: fontes.append("CBF")
        elif k is False: obs.append(f"CBF registra '{cbf}'")
        n_ind = len(fontes)
        if n_ind >= 2: st = "confirmado"
        elif len(ogl) == 1 and k is False and cbf_ok(ogl[0], cbf):  # O Gol + CBF contra TM
            recs.append((ogl[0], "confirmado", "OG+CBF", f"TM registra {pname[tm]}; O Gol e CBF concordam")); continue
        elif ogl and tm not in ogl: st = "conflito"
        else: st = "provável"
        recs.append((tm, st, "+".join(fontes), "; ".join(obs)))
    else:
        if len(ogl) == 1:
            k2 = cbf_ok(ogl[0], cbf)
            recs.append((ogl[0], "confirmado" if k2 else "provável", "OG" + ("+CBF" if k2 else ""), "TM sem treinador"))
        else:
            recs.append(("", "sem_treinador", "", f"TM sem treinador; CBF={cbf or '-'}"))
S["pessoa"], S["status"], S["fonte"], S["obs"] = zip(*recs)
S["cand_tm"] = S.tm_id
S["cand_og"] = [x[0] if len(x) == 1 else "" for x in S.og_tms]

# ---------------------------------------------------------------- Wikipédia (datas das trocas) para desempate
WK = pd.read_csv(R / "wiki_changes.csv", parse_dates=["data_saida", "data_entrada"])
import os
if os.environ.get("SEM_WIKI"): WK = WK.iloc[0:0]  # modo de validação independente
inv = {v: k for k, v in CLUBES.items()}
WK["clube_tm_id"] = WK.clube.map(inv)
def wmatch(wn, p):
    w = fold(wn)
    if not w or not p: return False
    for a in ALIAS[p]:
        wt, at = w.split(), a.split()
        if w == a or (wt and wt[-1] in at and (len(wt) == 1 or wt[0][:3] in {x[:3] for x in at} or len(wt[-1]) >= 5)) or (len(at) == 1 and at[0] in wt): return True
    return False
def wiki_no_comando(cl, y, d, c):
    """True/False se a Wikipédia indica que c estava no comando na data d; None se não há informação."""
    ev = []
    for w in WK[(WK.clube_tm_id == cl) & (WK.temporada == y)].itertuples():
        if pd.notna(w.data_entrada) and wmatch(w.entrou, c): ev.append((w.data_entrada, 1))
        if pd.notna(w.data_saida) and wmatch(w.saiu, c): ev.append((w.data_saida, -1))
    if not ev: return None
    ev.sort(); antes = [e for e in ev if e[0] < d]
    if antes: return antes[-1][1] == 1
    return ev[0][1] == -1  # primeiro evento é saída -> estava no cargo desde o início


def wiki_decide(cl, y, d, cands):
    d = pd.Timestamp(d)
    r = {c: wiki_no_comando(cl, y, d, c) for c in set(cands)}
    sim_ = [c for c, v in r.items() if v is True]
    return sim_[0] if len(sim_) == 1 and all(v is not True for c, v in r.items() if c != sim_[0]) else ""

# ---------------------------------------------------------------- continuidade e ausência pontual
S["dt"] = pd.to_datetime(S.data)
S = S.sort_values(["clube_tm_id", "temporada", "dt"]).reset_index(drop=True)
S["regra"] = ""; S["atribuicao_original"] = ""
OKST = ("confirmado", "provável")
for (cl, y), g in S.groupby(["clube_tm_id", "temporada"]):
    idx = list(g.index)
    for k, i in enumerate(idx):
        st = S.at[i, "status"]
        if st not in ("conflito", "sem_treinador"): continue
        prev = next((S.at[j, "pessoa"] for j in reversed(idx[:k]) if S.at[j, "status"] in OKST), "")
        nxt = next((S.at[j, "pessoa"] for j in idx[k + 1:] if S.at[j, "status"] in OKST), "")
        if st == "conflito":
            cands = [c for c in (S.at[i, "cand_tm"], S.at[i, "cand_og"]) if c]
            wd = wiki_decide(cl, y, S.at[i, "data"], cands)
            if wd:
                S.at[i, "pessoa"], S.at[i, "status"] = wd, "provável"
                S.at[i, "regra"] = "conflito TM x O Gol resolvido pela data da troca na Wikipédia"
                S.at[i, "fonte"] = ("TM" if wd == S.at[i, "cand_tm"] else "OG") + "+Wiki"
            elif prev and prev == nxt and prev in cands:
                S.at[i, "pessoa"], S.at[i, "status"] = prev, "provável"
                S.at[i, "regra"] = "conflito TM x O Gol resolvido por continuidade (mesmo técnico antes e depois)"
            else:
                hit = [c for c in cands if c in (prev, nxt)]
                S.at[i, "pessoa"] = S.at[i, "cand_tm"]; S.at[i, "status"] = "ambíguo"
                S.at[i, "regra"] = "conflito TM x O Gol em jogo de transição; mantido TM" + ("" if S.at[i, "cand_tm"] in hit else " (sem apoio de jogos vizinhos)")
        else:
            if prev and prev == nxt:
                S.at[i, "pessoa"], S.at[i, "status"], S.at[i, "regra"] = prev, "inferido", "sem treinador nas fontes; mesmo técnico antes e depois"
    # ausência pontual: <= N jogos de outro nome entre jogos do MESMO técnico -> titular (regra de suspensão/ausência)
    runs = []
    for i in idx:
        p = S.at[i, "pessoa"]
        if runs and runs[-1][0] == p: runs[-1][1].append(i)
        else: runs.append([p, [i]])
    for a in range(1, len(runs) - 1):
        p0, p1, p2 = runs[a - 1][0], runs[a][0], runs[a + 1][0]
        if p0 and p0 == p2 and p1 != p0 and len(runs[a][1]) <= MAN.get("max_ausencia", 2):
            for i in runs[a][1]:
                if f"{cl}|{y}|{S.at[i, 'data']}" in MAN.get("manter_substituto", []): continue
                orig = pname.get(p1, "-") if p1 else "-"
                S.at[i, "regra"] = (S.at[i, "regra"] + "; " if S.at[i, "regra"] else "") + f"ausência pontual do titular: fonte registra {orig}; atribuído a {pname[p0]}"
                S.at[i, "atribuicao_original"] = orig
                S.at[i, "pessoa"] = p0
                if S.at[i, "status"] == "confirmado": S.at[i, "status"] = "provável"
            runs[a][0] = p0  # mantém a sequência atualizada (evita reatribuição em cadeia)

# impossibilidade cronológica: técnico não confirmado num clube enquanto tem jogos CONFIRMADOS em outro clube
# no mesmo dia ou entre dois jogos confirmados do outro clube -> usa o candidato O Gol, se houver; senão ambíguo
conf = S[S.status == "confirmado"].sort_values("dt")
cp = {p: list(zip(g.dt, g.clube_tm_id)) for p, g in conf.groupby("pessoa")}
def impossivel(p, d, cl):
    ev = cp.get(p, [])
    antes = [c for t, c in ev if t <= d][-1:]; depois = [c for t, c in ev if t >= d][:1]
    if any(t == d and c != cl for t, c in ev): return True
    return bool(antes and depois and antes[0] == depois[0] and antes[0] != cl)
for i in S.index[S.status != "confirmado"]:
    p = S.at[i, "pessoa"]
    if p and impossivel(p, S.at[i, "dt"], S.at[i, "clube_tm_id"]):
        alt = S.at[i, "cand_og"] if S.at[i, "cand_og"] and S.at[i, "cand_og"] != p else ""
        S.at[i, "regra"] = (S.at[i, "regra"] + "; " if S.at[i, "regra"] else "") + f"{pname.get(p, p)} dirigia outro clube nesta data (jogos confirmados)"
        if alt: S.at[i, "pessoa"], S.at[i, "status"], S.at[i, "fonte"] = alt, "provável", "OG"
        else: S.at[i, "status"] = "ambíguo"

# fonte única contrariada pela Wikipédia -> ambíguo (não se esconde)
for i in S.index[(S.status == "provável") & S.fonte.isin(["TM", "OG"])]:
    if wiki_no_comando(S.at[i, "clube_tm_id"], S.at[i, "temporada"], pd.Timestamp(S.at[i, "data"]), S.at[i, "pessoa"]) is False:
        S.at[i, "status"] = "ambíguo"
        S.at[i, "regra"] = (S.at[i, "regra"] + "; " if S.at[i, "regra"] else "") + "fonte única contrariada pela Wikipédia (técnico já/ainda não estava no cargo nesta data)"

S["p_tm"], S["p_og"] = S.tm_id, S.cand_og
S["og_nome"] = S.og_tms.map(lambda x: "/".join(og_name.get(t, "") or pname.get(t, "") for t in x))
S["treinador"] = S.pessoa.map(pname).fillna("")
S.to_pickle(R / "_sides.pkl")
pd.to_pickle(dict(pname=pname, pid=pid, homon=homon, slug2tm=slug2tm, fx=fx, nao_disputada=nao_disputada, tm_names=tm_names,
                  og_name=og_name, og2tm=og2tm), R / "_meta.pkl")
print(S.status.value_counts())
print(S.fonte.value_counts())
