"""Preenche lacunas do O Gol pelo lado do clube: para jogos/lados sem evidência O Gol, abre a súmula O Gol
(só aceita se o bloco de escalação pertence ao jogo), lê o ID do técnico daquele lado e baixa a lista
'jogos realizados' dele na temporada. Treinadores que não existem no TM entram como 'og:<id>'.
Acrescenta em raw/ogol_coach_games.csv e raw/ogol_coach_ids.csv."""
import pathlib, sys, gzip, re, time, random
import pandas as pd, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
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

M = pd.read_pickle(R / "_meta.pkl"); og2tm = M["og2tm"]; tm2og = {v: k for k, v in og2tm.items()}
links = pd.read_csv(R / "ogol_links.csv", dtype=str).drop_duplicates("ogol_id").set_index("ogol_id")
Sd = pd.read_pickle(R / "_sides.pkl")
ids = pd.read_csv(R / "ogol_coach_ids.csv", dtype=str).fillna("")
og2person = {r.ogol_coach_id: r.tm for r in ids.itertuples() if r.ogol_coach_id}
cg = pd.read_csv(R / "ogol_coach_games.csv", dtype=str).fillna("")
fetched = set(zip(cg.ogol_coach_id, cg.temporada.astype(str)))
covered = set()
def recompute():
    covered.clear()
    for r in cg.itertuples():
        t = og2tm.get(r.ogol_id)
        if t: covered.add((t, "m" if r.cf == "C" else "v"))
recompute()

novos_ids, novas = [], []
tried_pages = set()
groups = Sd.groupby(["clube_tm_id", "temporada"])
for n, ((cl, y), g) in enumerate(groups):
    for attempt in range(8):
        gap = [x for x in g.sort_values("data").itertuples() if (x.tm_id_jogo, x.lado) not in covered and x.tm_id_jogo in tm2og and x.tm_id_jogo not in tried_pages]
        if not gap: break
        x = gap[len(gap) // 2] if attempt % 2 else gap[0]
        tried_pages.add(x.tm_id_jogo)
        oid = tm2og[x.tm_id_jogo]; f = R / "ogol_matches" / f"{oid}.html.gz"
        if not f.exists():
            c = get(f"https://www.ogol.com.br/jogo/{links.loc[oid, 'slug']}/{oid}")
            if not c: continue
            f.write_bytes(gzip.compress(c))
        co, _, bad = og_parse(f)
        if bad or len(co) < 2: continue
        nm, cid = co[0 if x.lado == "m" else 1]
        if not cid or (cid, str(y)) in fetched: continue
        fn = R / "ogol_coach_games" / f"{cid}_{y}.html"
        if not fn.exists(): fn.write_bytes(get(f"https://www.ogol.com.br/treinador/-/{cid}/jogos-realizados?grp=1&epoca_id={int(y) - 1871}"))
        rows = [r for r in parse(fn.read_text(encoding="utf-8", errors="replace")) if r["edicao_id"] in ED_IDS]
        person = og2person.get(cid) or f"og:{cid}"
        if cid not in og2person:
            og2person[cid] = person; novos_ids.append(dict(tm=person, nome_tm="", ogol_coach_id=cid, nome_ogol=nm, n_cand=0, status="so_ogol"))
        new = pd.DataFrame([dict(r, ogol_coach_id=cid, tm=person, temporada=str(y)) for r in rows], dtype=str)
        cg = pd.concat([cg, new]); fetched.add((cid, str(y))); novas.append(len(new))
        for r in rows:
            t = og2tm.get(r["ogol_id"])
            if t: covered.add((t, "m" if r["cf"] == "C" else "v"))
    if n % 50 == 0: print(n, len(novas), flush=True)

cg.drop_duplicates().to_csv(R / "ogol_coach_games.csv", index=False, encoding="utf-8")
pd.concat([ids, pd.DataFrame(novos_ids)]).to_csv(R / "ogol_coach_ids.csv", index=False, encoding="utf-8")
print("listas novas:", len(novas), "treinadores só O Gol:", len(novos_ids))
