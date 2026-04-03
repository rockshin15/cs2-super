import json
import os
from models.player import Player
from models.team import Team

class DataManager:
    def __init__(self, db_path="data/database.json"):
        self.db_path = db_path
        self.save_info = {}
        self.times = {}
        self.jogadores = {}

    def carregar_jogo(self):
        if not os.path.exists(self.db_path):
            return False

        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.save_info = data["save_info"]

        # 1. Carregar Jogadores
        for p_id, p_data in data["players"].items():
            jogador = Player(
                id=p_id,
                nome=p_data["nome"],
                nickname=p_data["nickname"],
                idade=p_data["idade"],
                funcao_principal=p_data["funcao_principal"],
                mira=p_data["atributos"]["mira"],
                gamesense=p_data["atributos"]["gamesense"],
                clutch=p_data["atributos"]["clutch"],
                potencial=p_data["atributos"]["potencial"],
                profissionalismo=p_data["atributos"]["profissionalismo"],
                team_id=p_data["team_id"],
                ego=p_data["atributos"].get("ego", 50.0),
                personalidade=p_data["personalidade"],
                salario=p_data["contrato"]["salario"],
                multa_rescisoria=p_data["contrato"].get("multa_rescisoria", 0),
                moral=p_data["status"]["moral"],
                fadiga=p_data["status"]["fadiga"]
            )
            self.jogadores[p_id] = jogador

        # 2. Carregar Equipas
        for t_id, t_data in data["teams"].items():
            equipa = Team(
                id=t_id,
                nome=t_data["nome"],
                saldo=t_data["saldo"],
                taticas=t_data["taticas"]
            )
            # Vincula os objetos Player reais ao elenco da equipa
            equipa.elenco = [self.jogadores[pid] for pid in t_data["elenco"] if pid in self.jogadores]
            self.times[t_id] = equipa

        return True

    def salvar_jogo(self):
        """Converte os objetos atuais de volta para JSON e guarda no disco."""
        data = {
            "save_info": self.save_info,
            "teams": {},
            "players": {}
        }

        # Serializar Jogadores
        for p_id, p in self.jogadores.items():
            data["players"][p_id] = {
                "nome": p.nome,
                "nickname": p.nickname,
                "idade": p.idade,
                "funcao_principal": p.funcao_principal,
                "team_id": p.team_id,
                "personalidade": p.personalidade,
                "atributos": {
                    "mira": p.mira,
                    "gamesense": p.gamesense,
                    "clutch": p.clutch,
                    "potencial": p.potencial,
                    "profissionalismo": p.profissionalismo,
                    "ego": p.ego
                },
                "contrato": {
                    "salario": p.salario,
                    "multa_rescisoria": p.multa_rescisoria
                },
                "status": {
                    "moral": p.moral,
                    "fadiga": p.fadiga
                }
            }

        # Serializar Equipas
        for t_id, t in self.times.items():
            data["teams"][t_id] = {
                "nome": t.nome,
                "saldo": t.saldo,
                "taticas": t.taticas,
                "elenco": [p.id for p in t.elenco] # Guarda apenas os IDs
            }

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return True