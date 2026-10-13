"""Coleta a lista de jogos da Série A (Transfermarkt, BRA1) por temporada 2003-2025.
Saída: raw/tm_fixtures.csv (uma linha por jogo, com id da súmula TM)."""
import re, time, html, csv, pathlib, requests
from bs4 import BeautifulSoup

BASE = pathlib.Path(__file__).resolve().parent.parent
RAW = BASE / "raw" / "tm_fixtures_html"; RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def get(url):
    for i in range(6):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code == 200:
            return r.content.decode("utf-8", errors="replace") if b"charset=utf-8" in r.content[:3000].lower() else r.text
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"{url} -> {r.status_code}")

rows = []
for year in range(2003, 2026):
    f = RAW / f"{year}.html"
    if not f.exists():
        url = f"https://www.transfermarkt.com.br/campeonato-brasileiro-serie-a/gesamtspielplan/wettbewerb/BRA1?saison_id={year-1}&spieltagVon=1&spieltagBis=46"
        f.write_text(get(url), encoding="utf-8"); time.sleep(2)
    soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
    n0 = len(rows)
    for box in soup.select("div.box"):
        hl = box.select_one("div.content-box-headline")
        if not hl or "Rodada" not in hl.get_text(): continue
        rodada = int(re.match(r"\s*(\d+)", hl.get_text()).group(1))
        data = hora = ""
        for tr in box.select("tbody tr"):
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 7: continue  # linha só de data (versão mobile)
            a = tds[0].find("a")
            if a and "datum" in a.get("href", ""):
                data = a["href"].split("/")[-1]
            t = tds[1].get_text(strip=True)
            if t: hora = t
            res = tr.select_one("a.ergebnis-link")
            teams = [x for x in tr.select("td.hauptlink a") if "/verein/" in x.get("href", "")]
            if not res or len(teams) < 2: continue
            hid = re.search(r"/verein/(\d+)", teams[0]["href"]).group(1)
            aid = re.search(r"/verein/(\d+)", teams[-1]["href"]).group(1)
            rows.append(dict(temporada=year, rodada=rodada, data=data, hora=hora,
                             tm_id_jogo=res["id"], mandante_tm=teams[0]["title"], mandante_tm_id=hid,
                             visitante_tm=teams[-1]["title"], visitante_tm_id=aid,
                             placar=res.get_text(strip=True)))
    print(year, len(rows) - n0, flush=True)

with open(BASE / "raw" / "tm_fixtures.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
