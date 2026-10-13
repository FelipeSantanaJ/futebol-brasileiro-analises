"""Extrai treinadores das súmulas salvas. Saídas: raw/tm_coaches.csv, raw/ogol_parsed.csv"""
import re, csv, pathlib, sys, html
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from parsers import tm_coaches, og_parse

BASE = pathlib.Path(__file__).resolve().parent.parent
R = BASE / "raw"

# --- Transfermarkt
rows = []
for fx in csv.DictReader(open(R / "tm_fixtures.csv", encoding="utf-8")):
    f = R / "tm_reports" / f"{fx['tm_id_jogo']}.html.gz"
    c = [(None, None), (None, None)]; ok = f.exists()
    if ok:
        x, _ = tm_coaches(f)
        if len(x) >= 2: c = x[:2]
    rows.append(dict(tm_id_jogo=fx["tm_id_jogo"], tm_baixado=int(ok),
                     tm_tec_m=c[0][0] or "", tm_tec_m_id=c[0][1] or "", tm_tec_v=c[1][0] or "", tm_tec_v_id=c[1][1] or ""))
with open(R / "tm_coaches.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("TM", len(rows), sum(r["tm_baixado"] for r in rows))

# --- O Gol
TEAM = re.compile(r'match-header-team-name">\s*<a href="/equipe/([a-z0-9-]+)')
TITLE = re.compile(r"<title>Estat[^<]*?Escala\S+ (.+?) (\d+)-(\d+) (.+?) :: ([^<]+)</title>")
rows = []
links = list(csv.DictReader(open(R / "ogol_links.csv", encoding="utf-8")))
seen = set()
for l in links:
    if l["ogol_id"] in seen: continue
    seen.add(l["ogol_id"])
    f = R / "ogol_matches" / f"{l['ogol_id']}.html.gz"
    if not f.exists():
        rows.append(dict(ogol_id=l["ogol_id"], slug=l["slug"], data=l["slug"][:10], og_baixado=0)); continue
    c, h, bad = og_parse(f)
    teams = []
    for m in TEAM.finditer(h):
        if m.group(1) not in teams: teams.append(m.group(1))
        if len(teams) == 2: break
    t = TITLE.search(h)
    c = (c + [(None, None)] * 2)[:2]
    rows.append(dict(ogol_id=l["ogol_id"], slug=l["slug"], data=l["slug"][:10], og_baixado=1,
                     og_mand=teams[0] if teams else "", og_vis=teams[1] if len(teams) > 1 else "",
                     og_gm=t.group(2) if t else "", og_gv=t.group(3) if t else "", og_comp=html.unescape(t.group(5)) if t else "", og_corrompido=int(bad),
                     og_tec_m=c[0][0] or "", og_tec_m_id=c[0][1] or "", og_tec_v=c[1][0] or "", og_tec_v_id=c[1][1] or ""))
with open(R / "ogol_parsed.csv", "w", newline="", encoding="utf-8") as fh:
    fn = ["ogol_id", "slug", "data", "og_baixado", "og_mand", "og_vis", "og_gm", "og_gv", "og_comp", "og_corrompido", "og_tec_m", "og_tec_m_id", "og_tec_v", "og_tec_v_id"]
    w = csv.DictWriter(fh, fieldnames=fn); w.writeheader(); w.writerows(rows)
print("OGOL", len(rows), sum(r["og_baixado"] for r in rows))
