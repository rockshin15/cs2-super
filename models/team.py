from dataclasses import dataclass, field
from typing import List

@dataclass
class Team:
    id: str
    nome: str
    saldo: int
    taticas: dict
    # O elenco começa como uma lista vazia e será preenchido pelo nosso carregador
    elenco: list = field(default_factory=list)