import unicodedata, re

# Transfermarkt club id -> (clube canônico, nome no período por temporada)
CLUBES = {
    "10010": "Bahia", "1023": "Palmeiras", "10247": "Portuguesa", "10492": "Juventude", "10870": "Fortaleza",
    "1134": "Ponte Preta", "15172": "Atlético-GO", "1751": "América-RN", "1755": "Guarani", "17776": "Chapecoense",
    "1785": "Santa Cruz", "18545": "CSA", "199": "Corinthians", "2029": "Ceará", "2035": "Avaí", "210": "Grêmio",
    "2125": "Vitória", "221": "Santos", "2462": "Fluminense", "2646": "Náutico", "28022": "Cuiabá",
    "2863": "América-MG", "291": "São Caetano", "309": "Paraná", "3197": "Goiás", "3270": "Ipatinga",
    "330": "Atlético-MG", "3330": "Joinville", "3876": "Mirassol", "3973": "Brasiliense", "4064": "Figueirense",
    "537": "Botafogo", "585": "São Paulo", "609": "Cruzeiro", "614": "Flamengo", "6347": "Paysandu",
    "6600": "Internacional", "679": "Athletico-PR", "7178": "Criciúma", "7478": "Santo André", "776": "Coritiba",
    "8698": "Grêmio Barueri/Prudente", "8718": "Sport", "8793": "Bragantino", "978": "Vasco",
}


def nome_epoca(tm_id, ano):
    c = CLUBES[tm_id]
    if tm_id == "679": return "Atlético-PR" if ano <= 2018 else "Athletico-PR"
    if tm_id == "8698": return "Grêmio Barueri" if ano == 2009 else "Grêmio Prudente"
    if tm_id == "8793": return "RB Bragantino" if ano >= 2020 else "Bragantino"
    return c


def fold(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# nomes da base adaoduque -> tm id
ADAO = {"America-MG": "2863", "America-RN": "1751", "Athletico-PR": "679", "Atletico-GO": "15172", "Atletico-MG": "330",
        "Avai": "2035", "Bahia": "10010", "Barueri": "8698", "Botafogo-RJ": "537", "Bragantino": "8793",
        "Brasiliense": "3973", "CSA": "18545", "Ceara": "2029", "Chapecoense": "17776", "Corinthians": "199",
        "Coritiba": "776", "Criciuma": "7178", "Cruzeiro": "609", "Cuiaba": "28022", "Figueirense": "4064",
        "Flamengo": "614", "Fluminense": "2462", "Fortaleza": "10870", "Goias": "3197", "Gremio": "210",
        "Gremio Prudente": "8698", "Guarani": "1755", "Internacional": "6600", "Ipatinga": "3270", "Joinville": "3330",
        "Juventude": "10492", "Nautico": "2646", "Palmeiras": "1023", "Parana": "309", "Paysandu": "6347",
        "Ponte Preta": "1134", "Portuguesa": "10247", "Santa Cruz": "1785", "Santo Andre": "7478", "Santos": "221",
        "Sao Caetano": "291", "Sao Paulo": "585", "Sport": "8718", "Vasco": "978", "Vitoria": "2125", "Mirassol": "3876"}

# slugs de equipe do O Gol -> tm id (conferido manualmente; não aprender por data, pois datas de jogos adiados divergem)
SLUG_OGOL = {"america-mineiro": "2863", "america-rn": "1751", "athletico-paranaense": "679", "atletico-paranaense": "679",
             "atletico-goianiense": "15172", "atletico-mineiro": "330", "avai": "2035", "bahia": "10010", "botafogo": "537",
             "brasiliense": "3973", "ceara": "2029", "chapecoense": "17776", "corinthians": "199", "coritiba": "776",
             "criciuma": "7178", "cruzeiro": "609", "csa": "18545", "cuiaba": "28022", "figueirense": "4064", "flamengo": "614",
             "fluminense": "2462", "fortaleza": "10870", "goias": "3197", "gremio": "210", "gremio-barueri": "8698",
             "gremio-prudente": "8698", "barueri": "8698", "guarani": "1755", "internacional": "6600", "ipatinga": "3270",
             "joinville": "3330", "juventude": "10492", "mirassol": "3876", "nautico": "2646", "palmeiras": "1023",
             "parana": "309", "paysandu": "6347", "ponte-preta": "1134", "portuguesa": "10247", "red-bull-bragantino": "8793",
             "bragantino": "8793", "santa-cruz": "1785", "santo-andre": "7478", "santos": "221", "sao-caetano": "291",
             "sao-paulo": "585", "sport": "8718", "vasco": "978", "vitoria": "2125"}
