"""Lê as tabelas de mudanças de técnico da Wikipédia (en 2003-2004; pt 2008-2025) com datas.
Saída: raw/wiki_changes.csv (temporada, clube, saiu, entrou, data_saida, data_entrada, fonte)."""
import pathlib, sys, io, re
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import fold, CLUBES

BASE = pathlib.Path(__file__).resolve().parent.parent; W = BASE / "raw" / "wiki"
MES = {m: i + 1 for i, m in enumerate("janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro".split())}
MES.update({m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())})
CLUB_ALIAS = {fold(v): v for v in CLUBES.values()}
CLUB_ALIAS.update({fold(k): v for k, v in {
    "Atlético Mineiro": "Atlético-MG", "Atlético Paranaense": "Athletico-PR", "Athletico Paranaense": "Athletico-PR", "Atlético-PR": "Athletico-PR",
    "Atlético Goianiense": "Atlético-GO", "América Mineiro": "América-MG", "América": "América-RN", "Red Bull Bragantino": "Bragantino",
    "RB Bragantino": "Bragantino", "Grêmio Barueri": "Grêmio Barueri/Prudente", "Grêmio Prudente": "Grêmio Barueri/Prudente", "Barueri": "Grêmio Barueri/Prudente",
    "Prudente": "Grêmio Barueri/Prudente", "Sport Recife": "Sport", "Vasco da Gama": "Vasco", "Paraná Clube": "Paraná"}.items()})


def clube(s): return CLUB_ALIAS.get(fold(re.sub(r"\[.*?\]", "", str(s))))


def data(s, ano):
    s = fold(re.sub(r"\[.*?\]", "", str(s)))
    m = re.search(r"(\d{1,2}) (?:de )?([a-z]+)(?: (?:de )?(\d{4}))?", s)
    if not m or m.group(2) not in MES: return None
    y = int(m.group(3)) if m.group(3) else ano
    if not m.group(3) and ano == 2020 and MES[m.group(2)] <= 3: y = 2021  # temporada 2020 terminou em fev/2021
    try: return pd.Timestamp(y, MES[m.group(2)], int(m.group(1)))
    except ValueError: return None


def nome(s): return re.sub(r"\s\d{1,2}(\s.*)?$", "", re.sub(r"\[.*?\]|\(.*?\)", "", str(s))).strip()


def tabelas(h, ids):
    for k in ids:
        i = h.find(f'id="{k}"')
        if i > 0:
            j = h.find("<h2", i + 10)
            try: return pd.read_html(io.StringIO(h[i:j if j > 0 else None]), flavor="lxml")
            except Exception: return []
    return []


rows = []
for y in range(2003, 2026):
    if y <= 2007:
        f = W / f"en_{y}.html"
        if not f.exists(): continue
        for t in tabelas(f.read_text(encoding="utf-8"), ["Coaching_changes"])[:1]:
            if "Outgoing head coach" not in t.columns: continue
            for r in t.itertuples(index=False):
                rows.append(dict(temporada=y, clube_wiki=r[0], saiu=nome(r[1]), entrou=nome(r[4]), data_saida=data(r[2], y), data_entrada=data(r[5], y), fonte="en.wikipedia"))
    else:
        for t in tabelas((W / f"{y}.html").read_text(encoding="utf-8"), ["Mudanças_de_técnicos", "Mudança_de_técnicos"]):
            c = list(t.columns)
            if "Antecessor" in c and "Sucessor" in c:
                for _, r in t.iterrows():
                    d = data(r.get("Data", ""), y)
                    rows.append(dict(temporada=y, clube_wiki=r["Clube"], saiu=nome(r["Antecessor"]), entrou=nome(r["Sucessor"]), data_saida=d, data_entrada=d, fonte="pt.wikipedia"))
            elif "Saiu" in c and "Entrou" in c:
                for _, r in t.iterrows():
                    rows.append(dict(temporada=y, clube_wiki=r["Clube"], saiu=nome(r["Saiu"]), entrou=nome(r["Entrou"]), data_saida=data(r["Saiu"], y), data_entrada=data(r["Entrou"], y), fonte="pt.wikipedia"))
C = pd.DataFrame(rows); C["clube"] = C.clube_wiki.map(clube)
C.to_csv(BASE / "raw" / "wiki_changes.csv", index=False, encoding="utf-8")
if __name__ == "__main__":
    print(len(C), C.clube.isna().sum(), C.data_saida.isna().sum()); print(C[C.clube.isna()].clube_wiki.unique())
