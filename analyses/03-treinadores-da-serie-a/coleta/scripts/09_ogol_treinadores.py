"""Fonte independente O Gol: para cada treinador do TM, encontra o ID O Gol (busca do site) e baixa
'jogos realizados' por temporada. Saídas: raw/ogol_coach_ids.csv, raw/ogol_coach_games/<ogid>_<ano>.html, raw/ogol_coach_games.csv"""
import re, csv, time, random, pathlib, sys, html, urllib.parse
import pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import fold

BASE = pathlib.Path(__file__).resolve().parent.parent
R = BASE / "raw"; G = R / "ogol_coach_games"; G.mkdir(exist_ok=True); SR = R / "ogol_search"; SR.mkdir(exist_ok=True)
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"})
EPOCA = lambda y: y - 1871  # 2003 -> 132 (verificado no site)


def get(url, minlen=10000):
    for i in range(6):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > minlen:
                time.sleep(random.uniform(0.6, 1.2)); return r.text
        except Exception:
            pass
        time.sleep(10 * (i + 1))
    print("FALHA", url, flush=True); return ""


# --- treinadores TM x temporada x clube
t = pd.read_csv(R / "tm_coaches.csv", dtype=str).fillna("")
f = pd.read_csv(R / "tm_fixtures.csv", dtype=str)
t = t.merge(f[["tm_id_jogo", "temporada", "mandante_tm_id", "visitante_tm_id"]])
a = pd.concat([t[["tm_tec_m", "tm_tec_m_id", "temporada", "mandante_tm_id"]].set_axis(["nome", "tm", "ano", "clube"], axis=1),
               t[["tm_tec_v", "tm_tec_v_id", "temporada", "visitante_tm_id"]].set_axis(["nome", "tm", "ano", "clube"], axis=1)])
a = a[a.tm != ""]
coaches = a.groupby("tm").agg(nome=("nome", "first"), anos=("ano", lambda s: sorted(set(s)))).reset_index()

# --- resolução de ID: busca por nome
def busca(nome):
    fn = SR / (re.sub(r"[^a-z0-9]+", "_", fold(nome)) + ".html")
    if not fn.exists():
        fn.write_text(get("https://www.ogol.com.br/jqc_search_solr.php?queryString=" + urllib.parse.quote_plus(nome), 200), encoding="utf-8")
    h = fn.read_text(encoding="utf-8")
    return [(m.group(2), m.group(1).replace("-", " ")) for m in re.finditer(r'href="/treinador/([^/"]+)/(\d+)\?search=1"', h)]

def jogos(ogid, ano):
    fn = G / f"{ogid}_{ano}.html"
    if not fn.exists():
        fn.write_text(get(f"https://www.ogol.com.br/treinador/-/{ogid}/jogos-realizados?grp=1&epoca_id={EPOCA(int(ano))}", 5000), encoding="utf-8")
    return fn.read_text(encoding="utf-8")

RID = re.compile(r'^[^>]*id="(\d+)"')
def parse(h):
    out = []
    for ch in h.split("<tr")[1:]:
        ch = ch[:ch.find("</tr>")]
        m = RID.match(ch); d = re.search(r'<td class="double"\s*>([0-9-]+)</td>', ch); cf = re.search(r"<td>\((C|F|N)\)</td>", ch)
        eq = re.search(r'href="/equipe/([a-z0-9-]+)', ch); res = re.search(r'class="result"><a\s+href="/jogo/([^"/]+)/\d+">([^<]*)</a>', ch)
        ed = re.search(r'href="/edicao/([^"/]+)/(\d+)"', ch)
        if m and d and cf and eq and res and ed:
            out.append(dict(ogol_id=m.group(1), data=d.group(1), cf=cf.group(1), adversario_slug=eq.group(1), slug=res.group(1),
                            placar=res.group(2), edicao=ed.group(1), edicao_id=ed.group(2)))
    return out

ED_IDS = {"2489", "457", "865", "1247", "1425", "2003", "5268", "13881", "21248", "42483", "56933", "67145", "79735", "96361", "104349", "122072", "131709", "142460", "154298", "162047", "172507", "184443", "194851"}

def resolve(row):
    cands = busca(row.nome)
    if not cands and len(row.nome.split()) > 1:
        cands = busca(row.nome.split()[-1])
    # ordena por similaridade de nome
    def sim(n):
        A, B = set(fold(n).split()), set(fold(row.nome).split())
        return (fold(n) == fold(row.nome), len(A & B))
    cands = sorted(dict(cands).items(), key=lambda kv: sim(kv[1]), reverse=True)[:4]
    ano = row.anos[0]
    for ogid, nm in cands:
        games = [g for g in parse(jogos(ogid, ano)) if g["edicao_id"] in ED_IDS]
        if games:
            return dict(tm=row.tm, nome_tm=row.nome, ogol_coach_id=ogid, nome_ogol=nm, n_cand=len(cands), status="ok")
    return dict(tm=row.tm, nome_tm=row.nome, ogol_coach_id="", nome_ogol="", n_cand=len(cands), status="nao_encontrado")

with ThreadPoolExecutor(3) as ex:
    ids = list(ex.map(resolve, coaches.itertuples()))
ID = pd.DataFrame(ids); ID.to_csv(R / "ogol_coach_ids.csv", index=False, encoding="utf-8")
print(ID.status.value_counts(), flush=True)

# --- todas as temporadas de cada treinador
tasks = [(r.ogol_coach_id, ano, r.tm) for r in ID[ID.status == "ok"].itertuples() for ano in coaches.set_index("tm").anos[r.tm]]
def run(x):
    ogid, ano, tm = x
    return [dict(g, ogol_coach_id=ogid, tm=tm, temporada=ano) for g in parse(jogos(ogid, ano)) if g["edicao_id"] in ED_IDS]
rows = []
with ThreadPoolExecutor(3) as ex:
    for r in ex.map(run, tasks): rows += r
pd.DataFrame(rows).to_csv(R / "ogol_coach_games.csv", index=False, encoding="utf-8")
print("linhas", len(rows), flush=True)
