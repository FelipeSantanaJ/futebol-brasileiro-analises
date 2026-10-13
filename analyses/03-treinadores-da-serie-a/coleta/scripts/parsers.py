"""Parsers das súmulas salvas (Transfermarkt e O Gol)."""
import re, gzip, html


def dec(b):
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="replace")


TM_SLOT = re.compile(r'<b>Treinador</b></td>\s*<td>(.*?)</td>|<div>Treinador:</div>\s*</td>\s*<td class="bench-table__td">(.*?)</td>', re.S)
TM_A = re.compile(r'<a title="([^"]*)" id="(\d+)" href="/[^"]*/profil/trainer/\d+"')


def tm_coaches(path):
    """Retorna [(nome, id) ou (None, None)] na ordem mandante, visitante."""
    h = dec(gzip.decompress(open(path, "rb").read()))
    out = []
    for m in TM_SLOT.finditer(h):
        cell = m.group(1) if m.group(1) is not None else m.group(2)
        a = TM_A.search(cell)
        out.append((html.unescape(a.group(1)), a.group(2)) if a else (None, None))
    return out, h


OG_COACH = re.compile(r'href="/treinador/([^"/]+)/(\d+)">([^<]+)</a>')


SUBT = re.compile(r'<div class="zz-tpl-col is-6 fl-c"><div class="subtitle">([^<]*)</div>')
HDR = re.compile(r'match-header-team-name">\s*<a href="[^"]*">([^<]+)<')


def og_parse(path):
    """Retorna ([(nome,id) mandante, (nome,id) visitante], html, flag_corrompido).
    O Gol às vezes anexa a escalação de OUTRO jogo à súmula; nesse caso os times do bloco de escalação
    não batem com os do cabeçalho -> descartamos os técnicos (flag=True)."""
    h = dec(gzip.decompress(open(path, "rb").read()))
    i = h.find('<div class="subtitle">Treinadores</div>')
    coaches = []
    j = h.find('id="game_report"')
    lineup_teams = [html.unescape(x).strip() for x in SUBT.findall(h[j:j + 3000])][:2] if j >= 0 else []
    hdr = [html.unescape(x).strip() for x in HDR.findall(h)][:2]
    def tok(s): return set(re.sub(r"[^a-z0-9 ]", " ", __import__("unicodedata").normalize("NFKD", s).encode("ascii", "ignore").decode().lower()).split())
    corrupt = False
    if i >= 0 and len(lineup_teams) == 2 and len(hdr) == 2:
        corrupt = not all(tok(a) & tok(b) for a, b in zip(lineup_teams, hdr))
    if i >= 0 and not corrupt:
        seg = h[i:i + 6000]
        # dois blocos de coluna (mandante | visitante); coluna vazia = sem treinador
        cols = re.split(r'<div class="zz-tpl-col is-6 fl-c">', h[i - 40:i + 6000])[1:3]
        for c in cols:
            m = OG_COACH.search(c)
            coaches.append((html.unescape(m.group(3)).strip(), m.group(2)) if m else (None, None))
    return coaches, h, corrupt
