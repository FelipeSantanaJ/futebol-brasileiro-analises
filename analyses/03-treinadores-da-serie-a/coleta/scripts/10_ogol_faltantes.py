"""Para treinadores TM não localizados na busca do O Gol: abre até 4 súmulas O Gol de jogos dele, lê o ID do
técnico do mesmo lado (só se o bloco de escalação pertencer ao jogo e o nome for compatível) e baixa as listas
'jogos realizados'. Acrescenta em raw/ogol_coach_ids.csv e raw/ogol_coach_games.csv."""
import pathlib, sys, gzip, re, time, random
import pandas as pd, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import fold
from parsers import og_parse

BASE = pathlib.Path(__file__).resolve().parent.parent; R = BASE / "raw"
src = open(BASE / "scripts" / "09_ogol_treinadores.py", encoding="utf-8").read()
ns = {"re": re}; exec(src[src.index("RID = "):src.index("ED_IDS =")], ns); parse = ns["parse"]
ED_IDS = eval(src.split("ED_IDS = ")[1].split("\n")[0])
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"})

def get(url):
    for i in range(5):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 5000:
                time.sleep(random.uniform(0.6, 1.2)); return r.content
        except Exception: pass
        time.sleep(10 * (i + 1))
    return b""

M = pd.read_pickle(R / "_meta.pkl"); tm2og = {v: k for k, v in M["og2tm"].items()}
links = pd.read_csv(R / "ogol_links.csv", dtype=str).drop_duplicates("ogol_id").set_index("ogol_id")
ids = pd.read_csv(R / "ogol_coach_ids.csv", dtype=str).fillna("")
Sd = pd.read_pickle(R / "_sides.pkl")
falt = ids[ids.status != "ok"]

def sim(a, b):
    A, B = set(fold(a).split()), set(fold(b).split())
    return bool(A & B) or fold(a).replace(" ", "") == fold(b).replace(" ", "")

novos, rows = [], []
for r in falt.itertuples():
    g = Sd[(Sd.tm_id == r.tm)].sort_values("data", ascending=False)
    g = g[g.tm_id_jogo.isin(tm2og)]
    pick = pd.concat([g.head(2), g.tail(2)]).drop_duplicates("tm_id_jogo")
    found = None
    for x in pick.itertuples():
        oid = tm2og[x.tm_id_jogo]; f = R / "ogol_matches" / f"{oid}.html.gz"
        if not f.exists():
            c = get(f"https://www.ogol.com.br/jogo/{links.loc[oid, 'slug']}/{oid}")
            if not c: continue
            f.write_bytes(gzip.compress(c))
        co, _, bad = og_parse(f)
        if bad or len(co) < 2: continue
        nm, cid = co[0 if x.lado == "m" else 1]
        if cid and sim(nm, r.nome_tm): found = (cid, nm); break
    if not found:
        novos.append(dict(tm=r.tm, nome_tm=r.nome_tm, ogol_coach_id="", nome_ogol="", n_cand=r.n_cand, status="nao_encontrado")); continue
    novos.append(dict(tm=r.tm, nome_tm=r.nome_tm, ogol_coach_id=found[0], nome_ogol=found[1], n_cand=r.n_cand, status="ok_via_sumula"))
    for ano in sorted(set(Sd[Sd.tm_id == r.tm].temporada)):
        fn = R / "ogol_coach_games" / f"{found[0]}_{ano}.html"
        if not fn.exists():
            fn.write_bytes(get(f"https://www.ogol.com.br/treinador/-/{found[0]}/jogos-realizados?grp=1&epoca_id={int(ano) - 1871}"))
        h = fn.read_text(encoding="utf-8", errors="replace")
        rows += [dict(gm, ogol_coach_id=found[0], tm=r.tm, temporada=ano) for gm in parse(h) if gm["edicao_id"] in ED_IDS]
    print(r.nome_tm, "->", found, flush=True)

ids = pd.concat([ids[ids.status == "ok"], pd.DataFrame(novos)])
ids.to_csv(R / "ogol_coach_ids.csv", index=False, encoding="utf-8")
cg = pd.concat([pd.read_csv(R / "ogol_coach_games.csv", dtype=str), pd.DataFrame(rows, dtype=str)]).drop_duplicates()
cg.to_csv(R / "ogol_coach_games.csv", index=False, encoding="utf-8")
print(ids.status.value_counts())
