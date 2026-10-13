"""Segundo processo para baixar súmulas O Gol (ordem inversa); mesma lógica de 03_ogol_scrape.py."""
import csv, gzip, pathlib, time, random, requests
from concurrent.futures import ThreadPoolExecutor
BASE = pathlib.Path(__file__).resolve().parent.parent
MD = BASE / "raw" / "ogol_matches"
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"})
def fetch(l):
    f = MD / f"{l['ogol_id']}.html.gz"
    if f.exists(): return
    for i in range(8):
        try:
            r = S.get(f"https://www.ogol.com.br/jogo/{l['slug']}/{l['ogol_id']}", timeout=60)
            if r.status_code == 200 and len(r.content) > 20000:
                if not f.exists(): f.write_bytes(gzip.compress(r.content))
                time.sleep(random.uniform(0.8, 1.5)); return
        except Exception: pass
        time.sleep(15 * (i + 1))
    print("FALHA", l["ogol_id"], flush=True)
L = list({l["ogol_id"]: l for l in csv.DictReader(open(BASE / "raw" / "ogol_links.csv", encoding="utf-8"))}.values())[::-1]
with ThreadPoolExecutor(2) as ex: list(ex.map(fetch, L))
print("fim", flush=True)
