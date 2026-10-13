"""Para clube-temporadas com lados ambíguos, busca no O Gol a lista de jogos dos técnicos citados pela Wikipédia
naquela troca (entrante/saída) e acrescenta em raw/ogol_coach_games.csv."""
import pathlib, sys, re, time, random
import pandas as pd, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import fold, CLUBES

BASE = pathlib.Path(__file__).resolve().parent.parent; R = BASE / "raw"
src = open(BASE / "scripts" / "09_ogol_treinadores.py", encoding="utf-8").read()
ns = {"re": re}; exec(src[src.index("RID = "):src.index("ED_IDS =")], ns); parse = ns["parse"]
ED_IDS = eval(src.split("ED_IDS = ")[1].split("\n")[0])
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"})
def get(url):
    for i in range(5):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 200:
                time.sleep(random.uniform(0.6, 1.2)); return r.content
        except Exception: pass
        time.sleep(10 * (i + 1))
    return b""

Sd = pd.read_pickle(R / "_sides.pkl"); WK = pd.read_csv(R / "wiki_changes.csv")
inv = {v: k for k, v in CLUBES.items()}; WK["cl"] = WK.clube.map(inv)
ids = pd.read_csv(R / "ogol_coach_ids.csv", dtype=str).fillna("")
cg = pd.read_csv(R / "ogol_coach_games.csv", dtype=str).fillna("")
fetched = set(zip(cg.ogol_coach_id, cg.temporada.astype(str)))
alvo = Sd[Sd.status == "ambíguo"][["clube_tm_id", "temporada"]].drop_duplicates()
nomes = set()
for r in alvo.itertuples():
    for w in WK[(WK.cl == r.clube_tm_id) & (WK.temporada == r.temporada)].itertuples():
        nomes.add((w.saiu, r.temporada)); nomes.add((w.entrou, r.temporada))

def ogid(nome):
    f = fold(nome)
    m = ids[(ids.nome_tm.map(fold) == f) | (ids.nome_ogol.map(fold) == f)]
    m = m[m.ogol_coach_id != ""]
    if len(m): return m.ogol_coach_id.iloc[0], m.tm.iloc[0]
    h = get("https://www.ogol.com.br/jqc_search_solr.php?queryString=" + requests.utils.quote(nome)).decode("utf-8", "replace")
    c = re.findall(r'href="/treinador/([^/"]+)/(\d+)\?search=1"', h)
    c = [x for x in c if fold(x[0].replace("-", " ")) == f] or c[:1]
    return (c[0][1], f"og:{c[0][1]}") if c else (None, None)

novos, add = [], []
for nome, y in sorted(nomes):
    nome = re.sub(r"\s*\(.*", "", nome).strip()
    if not nome or nome.lower() == "nan": continue
    oid, person = ogid(nome)
    if not oid or (oid, str(y)) in fetched: continue
    h = get(f"https://www.ogol.com.br/treinador/-/{oid}/jogos-realizados?grp=1&epoca_id={int(y) - 1871}").decode("utf-8", "replace")
    rows = [dict(r, ogol_coach_id=oid, tm=person, temporada=str(y)) for r in parse(h) if r["edicao_id"] in ED_IDS]
    fetched.add((oid, str(y))); add += rows
    if person.startswith("og:") and person not in set(ids.tm): novos.append(dict(tm=person, nome_tm="", ogol_coach_id=oid, nome_ogol=nome, n_cand=0, status="so_ogol"))
    print(nome, y, oid, len(rows), flush=True)
pd.concat([cg, pd.DataFrame(add, dtype=str)]).drop_duplicates().to_csv(R / "ogol_coach_games.csv", index=False, encoding="utf-8")
pd.concat([ids, pd.DataFrame(novos)]).drop_duplicates("tm").to_csv(R / "ogol_coach_ids.csv", index=False, encoding="utf-8")
