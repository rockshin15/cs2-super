import random

NACIONALIDADES = ["Brasil", "Dinamarca", "Ucrânia", "Suécia", "França", "EUA"]

NOMES = {
    "Brasil": ["Gabriel", "Kaike", "Andrei", "Yuri", "Epitácio", "Marcelo", "Fernando"],
    "Dinamarca": ["Peter", "Nicolai", "Lukas", "Casper", "Emil", "Mathias", "Kristian"],
    "Ucrânia": ["Oleksandr", "Valeriy", "Ilya", "Viktor", "Danylo", "Igor"],
    "Suécia": ["Olof", "Jesper", "Freddy", "Ludvig", "Robin", "Hampus"],
    "França": ["Mathieu", "Dan", "Richard", "Kenny", "Cédric", "Nathan"],
    "EUA": ["Jonathan", "Nicholas", "Jake", "Russel", "Timothy", "Vincent"]
}

SOBRENOMES = {
    "Brasil": ["Toledo", "Cerato", "Piovezan", "Santos", "Costa", "Silva", "Ferreira"],
    "Dinamarca": ["Rasmussen", "Reedtz", "Rossander", "Møller", "Reif", "Larsen"],
    "Ucrânia": ["Kostyliev", "Vakhovskiy", "Osipov", "Orudzhev", "Teslenko"],
    "Suécia": ["Kajbjer", "Wecksell", "Johansson", "Brolin", "Rönnquist"],
    "França": ["Herbaut", "Madesclaire", "Papillon", "Schrub", "Guipouy"],
    "EUA": ["Jablonowski", "Cannella", "Yip", "Van Dulken", "Ta"]
}

PREFIXOS_NICK = ["x", "dark", "god", "cold", "snip", "neo", "zer", "k", "v", "z"]
SUFIXOS_NICK = ["zera", "y", "er", "en", "is", "1", "x", "king", "shot"]

def gerar_nickname() -> str:
    """Gera um nickname ao estilo CS."""
    if random.random() < 0.2:
        return random.choice(PREFIXOS_NICK).capitalize()
    return (random.choice(PREFIXOS_NICK) + random.choice(SUFIXOS_NICK)).capitalize()