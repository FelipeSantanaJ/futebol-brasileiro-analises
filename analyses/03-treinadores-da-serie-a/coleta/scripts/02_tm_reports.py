"""Baixa cada súmula (spielbericht) do Transfermarkt e extrai o treinador de cada lado.
Retomável: grava página comprimida em raw/tm_reports/<id>.html.gz e resultado em raw/tm_coaches.csv."""
import re, time, gzip, csv, pathlib, random, requests, sys
from concurrent.futures import ThreadPoolExecutor

BASE = pathlib.Path(__file__).resolve().parent.parent
OUT = BASE / "raw" / "tm_reports"; OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "pt-BR,pt;q=0.9"}
S = requests.Session(); S.headers.update(UA)

def fetch(mid):
    f = OUT / f"{mid}.html.gz"
    if f.exists() and f.stat().st_size > 5000:
        return
    for i in range(8):
        try:
            r = S.get(f"https://www.transfermarkt.com.br/spielbericht/index/spielbericht/{mid}", timeout=60)
            if r.status_code == 200 and len(r.content) > 20000:
                f.write_bytes(gzip.compress(r.content)); time.sleep(random.uniform(0.6, 1.2)); return
        except Exception:
            pass
        time.sleep(10 * (i + 1))
    print("FALHA", mid, flush=True)

ids = [r["tm_id_jogo"] for r in csv.DictReader(open(BASE / "raw" / "tm_fixtures.csv", encoding="utf-8"))]
todo = [m for m in ids if not (OUT / f"{m}.html.gz").exists()]
if "rev" in sys.argv: todo = todo[::-1]
print("faltam", len(todo), flush=True)
done = 0
with ThreadPoolExecutor(3) as ex:
    for _ in ex.map(fetch, todo):
        done += 1
        if done % 250 == 0: print(done, flush=True)
print("fim", flush=True)
