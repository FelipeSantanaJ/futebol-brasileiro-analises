"""Valida trocas de comando reconstruídas (súmulas) contra as tabelas de mudanças de técnico da Wikipédia
(en: 2003-2004 'Coaching changes'; pt: 2008-2025 'Mudança(s) de técnicos'). Saída: dados/validacao_trocas_wikipedia.csv"""
import pathlib, sys, io, re
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import fold, CLUBES

BASE = pathlib.Path(__file__).resolve().parent.parent
W = BASE / "raw" / "wiki"
A = pd.read_csv(BASE / "dados" / "treinadores_por_partida_2003_2025.csv")
NORMNAMES = pd.read_csv(BASE / "dados" / "normalizacao_treinadores.csv")

CLUB_ALIAS = {fold(v): v for v in CLUBES.values()}
CLUB_ALIAS.update({fold(k): v for k, v in {
    "Atlético Mineiro": "Atlético-MG", "Atlético Paranaense": "Athletico-PR", "Athletico Paranaense": "Athletico-PR", "Atlético-PR": "Athletico-PR",
    "Atlético Goianiense": "Atlético-GO", "América Mineiro": "América-MG", "América-RN": "América-RN", "América": "América-RN",
    "Botafogo": "Botafogo", "Red Bull Bragantino": "Bragantino", "RB Bragantino": "Bragantino", "Grêmio Barueri": "Grêmio Barueri/Prudente",
    "Grêmio Prudente": "Grêmio Barueri/Prudente", "Barueri": "Grêmio Barueri/Prudente", "Prudente": "Grêmio Barueri/Prudente", "Sport Recife": "Sport", "Sport": "Sport",
    "Vasco da Gama": "Vasco", "Paraná Clube": "Paraná", "São Caetano": "São Caetano", "Santo André": "Santo André", "Cuiabá": "Cuiabá"}.items()})


def clube(s):
    s = re.sub(r"\[.*?\]", "", str(s)).strip()
    return CLUB_ALIAS.get(fold(s))


def limpa(s):
    s = re.sub(r"\[.*?\]|\(.*?\)", "", str(s))
    s = re.sub(r"\s\d{1,2}(\s.*)?$", "", s)  # remove datas coladas ("Geninho 15 Maio")
    return s.strip()


def tabelas(h, ids):
    for k in ids:
        i = h.find(f'id="{k}"')
        if i > 0:
            j = h.find("<h2", i + 10)
            try: return pd.read_html(io.StringIO(h[i:j if j > 0 else None]), flavor="lxml")
            except Exception: return []
    return []


ch = []
for y in range(2003, 2026):
    if y <= 2007:
        f = W / f"en_{y}.html"
        if not f.exists(): continue
        ts = tabelas(f.read_text(encoding="utf-8"), ["Coaching_changes"])
        for t in ts[:1]:
            if "Outgoing head coach" not in t.columns: continue
            for r in t.itertuples(index=False):
                ch.append(dict(temporada=y, clube_wiki=r[0], saiu=r[1], entrou=r[4], data_wiki=r[2], fonte="en.wikipedia"))
    else:
        f = W / f"{y}.html"
        ts = tabelas(f.read_text(encoding="utf-8"), ["Mudanças_de_técnicos", "Mudança_de_técnicos"])
        for t in ts:
            cols = list(t.columns)
            if "Antecessor" in cols and "Sucessor" in cols:
                for _, r in t.iterrows():
                    ch.append(dict(temporada=y, clube_wiki=r["Clube"], saiu=r["Antecessor"], entrou=r["Sucessor"], data_wiki=r.get("Data", ""), fonte="pt.wikipedia"))
            elif "Saiu" in cols and "Entrou" in cols:
                for _, r in t.iterrows():
                    ch.append(dict(temporada=y, clube_wiki=r["Clube"], saiu=r["Saiu"], entrou=r["Entrou"], data_wiki="", fonte="pt.wikipedia"))
C = pd.DataFrame(ch)
C["clube"] = C.clube_wiki.map(clube)

# nomes conhecidos de cada pessoa (todas as grafias de todas as fontes)
alias = NORMNAMES.groupby("nome_padronizado").nome_original.agg(lambda s: {fold(x) for x in s})


def mesmo(wiki_nome, treinador):
    w = fold(limpa(wiki_nome))
    if not w: return False
    nomes = alias.get(treinador, set()) | {fold(treinador)}
    for n in nomes:
        if w == n: return True
        wt, nt = w.split(), n.split()
        if len(wt) >= 1 and wt[-1] in nt and (len(wt) == 1 or wt[0] in nt or len(wt[-1]) >= 5 or any(x[:3] == wt[0][:3] for x in nt)): return True
        if len(wt) >= 2 and wt[0] in nt and len(wt[0]) >= 5 and wt[0] not in ("paulo", "marcelo", "carlos", "eduardo", "ricardo", "roberto", "antonio", "fernando", "luiz", "luis", "joao", "jose"): return True
        if len(nt) == 1 and nt[0] in wt: return True
    return False


res = []
for r in C.itertuples():
    g = A[(A.clube == r.clube) & (A.temporada == r.temporada)].sort_values("data")
    seq = [t for k, t in enumerate(g.treinador) if k == 0 or t != g.treinador.iloc[k - 1]]  # sequência de passagens
    outs = [k for k, t in enumerate(seq) if mesmo(r.saiu, t)]; ins = [k for k, t in enumerate(seq) if mesmo(r.entrou, t)]
    i_out = outs[0] if outs else None; i_in = ins[-1] if ins else None
    if r.clube is None: st = "clube_nao_mapeado"
    elif i_in is None and i_out is None: st = "nenhum_encontrado"
    elif i_in is None: st = "entrante_nao_encontrado"
    elif i_out is None: st = "saiu_nao_encontrado"  # comum: técnico saiu antes da 1ª rodada
    elif any(b > a for a in outs for b in ins): st = "ok_ordem"
    else: st = "ordem_invertida"
    res.append(dict(seq_base=" > ".join(seq), status_validacao=st,
                    primeiro_jogo_entrante=g[g.treinador == seq[i_in]].data.min() if i_in is not None else "",
                    ultimo_jogo_saiu=g[g.treinador == seq[i_out]].data.max() if i_out is not None else ""))
C = pd.concat([C, pd.DataFrame(res)], axis=1)
import os
C.to_csv(BASE / "dados" / ("validacao_trocas_wikipedia_independente.csv" if os.environ.get("SEM_WIKI") else "validacao_trocas_wikipedia.csv"), index=False, encoding="utf-8-sig")
print(C.groupby(["fonte", "status_validacao"]).size())
print(C.groupby("temporada").status_validacao.apply(lambda s: f"{(s=='ok_ordem').sum()}/{len(s)}").to_string())
