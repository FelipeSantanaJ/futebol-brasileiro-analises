"""Canonicalização de nomes de clubes e estádios.

O dataset bruto traz o mesmo clube/estádio grafado de várias formas ao longo dos
anos. Aqui ficam os mapas de nome bruto -> id canônico. A fonte da verdade é este
módulo; `python -m futebrasil.lookups` grava um snapshot em data/external/ para
consulta.

Sobre estádios reconstruídos: quando um estádio foi demolido e reconstruído no
mesmo terreno, tratamos as duas eras como estádios diferentes, porque a pergunta
da análise é sobre a praça específica em que o clube mandou o jogo:
  - Palestra Itália (até 2010)      != Allianz Parque (2014+)   — Palmeiras
  - Fonte Nova antiga (até 2007)    != Arena Fonte Nova (2013+) — Bahia
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from .caminhos import EXTERNO


def sem_acento(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """minúsculas, sem acento, sem pontuação, espaços colapsados."""
    if texto is None:
        return ""
    t = sem_acento(str(texto)).lower().replace("\xa0", " ")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def marca_portoes_fechados(arena_bruta: str) -> bool:
    """O dataset marca alguns jogos sem público com sufixo *(PF) / (*PF)."""
    return bool(re.search(r"\(\*?pf\*?\)", str(arena_bruta).lower()))


def _limpa_arena(arena_bruta: str) -> str:
    s = str(arena_bruta).replace("\xa0", " ")
    s = re.sub(r"\*?\(\*?pf\*?\)\*?", "", s, flags=re.I)  # tira marcador de portões fechados
    return s.strip()


# --------------------------------------------------------------------------- #
# Clubes                                                                      #
# --------------------------------------------------------------------------- #
# O dataset já é razoavelmente consistente nos nomes de clube. Mantemos os ids
# como slug do nome usado no dataset; aliases só onde há divergência real.
CLUBES_ALIAS = {
    "athletico paranaense": "athletico-pr",
    "atletico paranaense": "athletico-pr",
    "atletico-pr": "athletico-pr",
    "red bull bragantino": "bragantino",   # troca de controle em 2019; mesmo clube/CNPJ
    "rb bragantino": "bragantino",
    "vasco da gama": "vasco",
}


def clube_id(nome_bruto: str) -> str:
    n = normalizar(nome_bruto)
    if n in CLUBES_ALIAS:
        return CLUBES_ALIAS[n]
    return n.replace(" ", "-")


NOMES_EXIBICAO = {
    "athletico-pr": "Athletico-PR", "atletico-mg": "Atlético-MG",
    "atletico-go": "Atlético-GO", "america-mg": "América-MG", "america-rn": "América-RN",
    "botafogo-rj": "Botafogo", "sao-paulo": "São Paulo", "sao-caetano": "São Caetano",
    "santo-andre": "Santo André", "gremio": "Grêmio", "goias": "Goiás", "vitoria": "Vitória",
    "ceara": "Ceará", "nautico": "Náutico", "parana": "Paraná", "avai": "Avaí",
    "ponte-preta": "Ponte Preta", "gremio-prudente": "Grêmio Prudente",
    "csa": "CSA", "cuiaba": "Cuiabá", "criciuma": "Criciúma", "coritiba": "Coritiba",
}


def nome_exibicao(clube_id_: str) -> str:
    return NOMES_EXIBICAO.get(clube_id_, clube_id_.replace("-", " ").title())


# --------------------------------------------------------------------------- #
# Estádios                                                                    #
# --------------------------------------------------------------------------- #
# id -> (nome de exibição, cidade, uf, [padrões que casam com o nome bruto])
# Os padrões são comparados sobre a forma normalizada (sem acento, minúsculo,
# sem "estádio"/"arena"). Ordem importa: o primeiro padrão que casar vence.
ESTADIOS = {
    "maracana":        ("Maracanã", "Rio de Janeiro", "RJ", ["maracana"]),
    "mineirao":        ("Mineirão", "Belo Horizonte", "MG", ["mineirao"]),
    "morumbi":         ("Morumbi", "São Paulo", "SP", ["morumbi", "morumbis", "cicero pompeu", "doutor adhemar de barros", "dr adhemar de barros"]),
    "arena_corinthians": ("Neo Química Arena", "São Paulo", "SP", ["neo quimica", "corinthians", "itaquer"]),
    "allianz_parque":  ("Allianz Parque", "São Paulo", "SP", ["allianz"]),
    "palestra_italia": ("Palestra Itália (antigo)", "São Paulo", "SP", ["palestra italia", "parque antartica"]),
    "pacaembu":        ("Pacaembu", "São Paulo", "SP", ["pacaembu", "paulo machado de carvalho", "municipal general", "municipal paulo"]),
    "vila_belmiro":    ("Vila Belmiro", "Santos", "SP", ["vila belmiro", "urbano caldeira"]),
    "caninde":         ("Canindé", "São Paulo", "SP", ["caninde", "oswaldo teixeira duarte", "osvaldo teixeira duarte"]),
    "moises_lucarelli": ("Moisés Lucarelli", "Campinas", "SP", ["moises lucarelli", "lucarelli"]),
    "brinco_de_ouro":  ("Brinco de Ouro da Princesa", "Campinas", "SP", ["brinco de ouro"]),
    "anacleto_campanella": ("Anacleto Campanella", "São Caetano do Sul", "SP", ["anacleto campanella", "campanella"]),
    "bruno_jose_daniel": ("Bruno José Daniel", "Santo André", "SP", ["bruno jose daniel", "bruno j daniel"]),
    "nabizao":         ("Nabi Abi Chedid", "Bragança Paulista", "SP", ["nabi abi chedid", "nabizao"]),
    "arena_barueri":   ("Arena Barueri", "Barueri", "SP", ["barueri"]),
    "prudentao":       ("Prudentão", "Presidente Prudente", "SP", ["prudentao", "eduardo jose farah"]),

    "beira_rio":       ("Beira-Rio", "Porto Alegre", "RS", ["beira rio", "beira-rio", "jose pinheiro borda", "pinheiro borda"]),
    "arena_gremio":    ("Arena do Grêmio", "Porto Alegre", "RS", ["do gremio"]),
    "olimpico_goiania": ("Olímpico Pedro Ludovico", "Goiânia", "GO", ["pedro ludovico", "olimpico regional"]),
    "olimpico_poa":    ("Olímpico Monumental", "Porto Alegre", "RS", ["olimpico monumental", "olimpico"]),
    "alfredo_jaconi":  ("Alfredo Jaconi", "Caxias do Sul", "RS", ["alfredo jaconi", "jaconi"]),
    "centenario_caxias": ("Centenário", "Caxias do Sul", "RS", ["centenario"]),
    "estadio_do_vale": ("Estádio do Vale", "Novo Hamburgo", "RS", ["do vale"]),

    "arena_da_baixada": ("Ligga Arena (Arena da Baixada)", "Curitiba", "PR", ["baixada", "joaquim americo", "kyocera", "ligga"]),
    "couto_pereira":   ("Couto Pereira", "Curitiba", "PR", ["couto pereira"]),
    "vila_capanema":   ("Durival de Brito (Vila Capanema)", "Curitiba", "PR", ["vila capanema", "durival de brito", "durival britto"]),
    "pinheirao":       ("Pinheirão", "Curitiba", "PR", ["pinheirao"]),
    "cafe":            ("Estádio do Café", "Londrina", "PR", ["do cafe"]),
    "willie_davids":   ("Willie Davids", "Maringá", "PR", ["willie davids"]),

    "orlando_scarpelli": ("Orlando Scarpelli", "Florianópolis", "SC", ["orlando scarpelli", "scarpelli"]),
    "ressacada":       ("Ressacada", "Florianópolis", "SC", ["ressacada", "aderbal ramos"]),
    "arena_conda":     ("Arena Condá", "Chapecó", "SC", ["conda"]),
    "heriberto_hulse": ("Heriberto Hülse", "Criciúma", "SC", ["heriberto hulse", "heriberto hulse"]),
    "arena_joinville": ("Arena Joinville", "Joinville", "SC", ["joinville"]),

    "independencia":   ("Independência (Raimundo Sampaio)", "Belo Horizonte", "MG", ["independencia", "raimundo sampaio"]),
    "arena_mrv":       ("Arena MRV", "Belo Horizonte", "MG", ["mrv"]),
    "arena_do_jacare": ("Arena do Jacaré", "Sete Lagoas", "MG", ["jacare", "joaquim henrique nogueira"]),
    "parque_do_sabia": ("Parque do Sabiá", "Uberlândia", "MG", ["parque do sabia", "sabia"]),
    "ipatingao":       ("Ipatingão", "Ipatinga", "MG", ["ipatingao", "ipatinga", "joao lamego"]),
    "mario_helenio":   ("Mário Helênio", "Juiz de Fora", "MG", ["mario helenio", "juiz de fora"]),

    "sao_januario":    ("São Januário", "Rio de Janeiro", "RJ", ["sao januario", "januario", "vasco da gama"]),
    "engenhao":        ("Nilton Santos (Engenhão)", "Rio de Janeiro", "RJ", ["nilton santos", "engenhao", "joao havelange", "olimpico joao"]),
    "luso_brasileiro": ("Luso-Brasileiro", "Rio de Janeiro", "RJ", ["luso brasileiro", "luso-brasileiro"]),
    "giulite_coutinho": ("Giulite Coutinho", "Mesquita", "RJ", ["giulite coutinho", "coutinho"]),
    "raulino_de_oliveira": ("Raulino de Oliveira", "Volta Redonda", "RJ", ["raulino de oliveira", "raulino"]),
    "moacyrzao":       ("Moacyrzão", "Macaé", "RJ", ["moacyrzao", "claudio moacyr"]),
    "caio_martins":    ("Caio Martins", "Niterói", "RJ", ["caio martins"]),

    "barradao":        ("Barradão", "Salvador", "BA", ["barradao", "manoel barradas"]),
    "arena_fonte_nova": ("Arena Fonte Nova", "Salvador", "BA", ["itaipava arena fonte nova", "arena fonte nova", "casa de apostas"]),
    "fonte_nova_velha": ("Fonte Nova (antiga)", "Salvador", "BA", ["fonte nova", "octavio mangabeira"]),
    "pituacu":         ("Pituaçu", "Salvador", "BA", ["pituacu"]),
    "joia_da_princesa": ("Joia da Princesa", "Feira de Santana", "BA", ["joia da princesa", "alberto oliveira"]),

    "adelmar_costa_carvalho": ("Ilha do Retiro", "Recife", "PE", ["adelmar da costa carvalho", "ilha do retiro"]),
    "aflitos":         ("Aflitos", "Recife", "PE", ["aflitos"]),
    "arruda":          ("Arruda", "Recife", "PE", ["arruda", "rego maciel"]),
    "arena_pernambuco": ("Arena de Pernambuco", "São Lourenço da Mata", "PE", ["pernambuco"]),

    "serra_dourada":   ("Serra Dourada", "Goiânia", "GO", ["serra dourada"]),
    "serrinha":        ("Serrinha (Hailé Pinheiro)", "Goiânia", "GO", ["serrinha", "haile pinheiro"]),
    "antonio_accioly": ("Antônio Accioly", "Goiânia", "GO", ["antonio accioly", "accioly"]),

    "castelao_ma":     ("Castelão", "São Luís", "MA", ["castelao de sao luis", "sao luis", "joao castelo"]),
    "arena_castelao":  ("Arena Castelão", "Fortaleza", "CE", ["placido castelo", "arena castelao", "castelao"]),
    "presidente_vargas": ("Presidente Vargas", "Fortaleza", "CE", ["presidente vargas", "pres vargas"]),

    "arena_pantanal":  ("Arena Pantanal", "Cuiabá", "MT", ["pantanal"]),
    "morenao":         ("Morenão", "Campo Grande", "MS", ["morenao", "pedro pedrossian"]),
    "mangueirao":      ("Mangueirão", "Belém", "PA", ["mangueirao", "olimpico do para"]),
    "curuzu":          ("Curuzu", "Belém", "PA", ["curuzu", "leonidas castro"]),
    "arena_amazonia":  ("Arena da Amazônia", "Manaus", "AM", ["amazonia", "vivaldo lima", "vivaldao"]),
    "rei_pele":        ("Rei Pelé", "Maceió", "AL", ["rei pele"]),
    "batistao":        ("Batistão", "Aracaju", "SE", ["batistao", "lourival baptista"]),

    "machadao":        ("Machadão", "Natal", "RN", ["machadao"]),
    "arena_das_dunas": ("Arena das Dunas", "Natal", "RN", ["dunas"]),

    "mane_garrincha":  ("Mané Garrincha", "Brasília", "DF", ["mane garrincha", "garrincha", "nacional de brasilia", "brb", "nacional mane"]),
    "bezerrao":        ("Bezerrão", "Gama", "DF", ["bezerrao", "walmir campelo"]),
    "serejao":         ("Serejão", "Taguatinga", "DF", ["serejao", "abadio dos santos"]),

    "kleber_andrade":  ("Kléber Andrade", "Cariacica", "ES", ["kleber andrade"]),
}

# forma pré-normalizada dos padrões, calculada uma vez
_PADROES = [
    (eid, [normalizar(p) for p in dados[3]])
    for eid, dados in ESTADIOS.items()
]


def estadio_id(arena_bruta: str) -> str:
    n = normalizar(_limpa_arena(arena_bruta))
    if not n:
        return "desconhecido"
    for eid, padroes in _PADROES:
        for p in padroes:
            if p and p in n:
                return eid
    # sem correspondência: devolve um slug estável (cai como "casa não-principal")
    return "outro__" + n.replace(" ", "_")[:40]


def estadio_meta() -> pd.DataFrame:
    linhas = [
        {"estadio_id": eid, "estadio": nome, "cidade": cid, "uf": uf}
        for eid, (nome, cid, uf, _) in ESTADIOS.items()
    ]
    linhas.append({"estadio_id": "desconhecido", "estadio": "Desconhecido", "cidade": None, "uf": None})
    return pd.DataFrame(linhas)


def _snapshot() -> None:
    """Grava data/external/*.csv a partir dos mapas deste módulo."""
    EXTERNO.mkdir(parents=True, exist_ok=True)
    estadio_meta().to_csv(EXTERNO / "estadios_canonico.csv", index=False, encoding="utf-8")
    alias_rows = []
    for eid, (_, _, _, padroes) in ESTADIOS.items():
        for p in padroes:
            alias_rows.append({"padrao": p, "estadio_id": eid})
    pd.DataFrame(alias_rows).to_csv(EXTERNO / "estadios_padroes.csv", index=False, encoding="utf-8")
    pd.DataFrame(
        [{"alias": k, "clube_id": v} for k, v in CLUBES_ALIAS.items()]
    ).to_csv(EXTERNO / "clubes_alias.csv", index=False, encoding="utf-8")
    print(f"snapshot gravado em {EXTERNO}")


if __name__ == "__main__":
    _snapshot()
