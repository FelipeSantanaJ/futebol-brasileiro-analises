"""O Gol (zerozero): lista de jogos por rodada de cada edição 2003-2025 e súmula de cada jogo.
Retomável. Saídas: raw/ogol_rounds/<ano>_<rodada>.html, raw/ogol_matches/<id>.html.gz, raw/ogol_links.csv"""
import re, time, gzip, csv, pathlib, random, requests
from concurrent.futures import ThreadPoolExecutor

BASE = pathlib.Path(__file__).resolve().parent.parent
RD = BASE / "raw" / "ogol_rounds"; RD.mkdir(parents=True, exist_ok=True)
MD = BASE / "raw" / "ogol_matches"; MD.mkdir(parents=True, exist_ok=True)
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"})
ED = {2003: 2489, 2004: 457, 2005: 865, 2006: 1247, 2007: 1425, 2008: 2003, 2009: 5268, 2010: 13881, 2011: 21248, 2012: 42483,
      2013: 56933, 2014: 67145, 2015: 79735, 2016: 96361, 2017: 104349, 2018: 122072, 2019: 131709, 2020: 142460, 2021: 154298,
      2022: 162047, 2023: 172507, 2024: 184443, 2025: 194851}
NR = {2003: 46, 2004: 46, 2005: 42}

def get(url, minlen=20000):
    for i in range(8):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > minlen:
                time.sleep(random.uniform(0.8, 1.5)); return r.content
        except Exception:
            pass
        time.sleep(15 * (i + 1))
    print("FALHA", url, flush=True); return None

links = []
CD = BASE / "raw" / "ogol_cal"; CD.mkdir(exist_ok=True)
for y, eid in ED.items():
    pg = 1; got = set()
    while True:
        f = CD / f"{y}_{pg:02d}.html"
        if not f.exists():
            c = get(f"https://www.ogol.com.br/edicao/brasileirao-serie-a-{y}/{eid}/calendario?fase_in=0&equipa=0&estado=&filtro=&op=calendario&page={pg}", 5000)
            if not c: break
            f.write_bytes(c)
        h = f.read_text(encoding="utf-8", errors="replace")
        ids = set(re.findall(r'href="/jogo/([0-9]{4}-[0-9]{2}-[0-9]{2}-[^"/]+)/(\d+)"', h))
        new = ids - got
        if not new: break
        got |= ids; pg += 1
    for slug, mid in sorted(got):
        links.append(dict(temporada=y, rodada="", slug=slug, ogol_id=mid))
    print(y, len(got), flush=True)

with open(BASE / "raw" / "ogol_links.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(links[0])); w.writeheader(); w.writerows(links)

def fetch(l):
    f = MD / f"{l['ogol_id']}.html.gz"
    if f.exists(): return
    c = get(f"https://www.ogol.com.br/jogo/{l['slug']}/{l['ogol_id']}")
    if c: f.write_bytes(gzip.compress(c))

uniq = {l["ogol_id"]: l for l in links}.values()
done = 0
with ThreadPoolExecutor(2) as ex:
    for _ in ex.map(fetch, uniq):
        done += 1
        if done % 250 == 0: print("jogos", done, flush=True)
print("fim", flush=True)
