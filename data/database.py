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

        self.save_info = data.get("save_info", {"dia_atual": 1})

        # --- 1. CARREGAR JOGADORES ---
        jogadores_raw = data.get("jogadores", data.get("players", []))
        
        # Adapta se vier como Lista (setup_game) ou Dicionário (salvar_jogo)
        if isinstance(jogadores_raw, dict):
            iterador_jogadores = jogadores_raw.items()
        else:
            iterador_jogadores = [(p["id"], p) for p in jogadores_raw]

        for p_id, p_data in iterador_jogadores:
            # Usa .get() para evitar erros se faltar alguma chave no JSON antigo
            attrs = p_data.get("atributos", p_data)
            ocultos = p_data.get("ocultos", p_data)
            contrato = p_data.get("contrato", {})
            status = p_data.get("status", {})

            jogador = Player(
                id=p_id,
                nome=p_data.get("nome", "Desconhecido"),
                nickname=p_data.get("nickname", "Player"),
                idade=p_data.get("idade", 20.0),
                funcao_principal=p_data.get("funcao_principal", p_data.get("funcao", "Rifler")),
                mira=attrs.get("mira", 50.0),
                gamesense=attrs.get("gamesense", 50.0),
                clutch=attrs.get("clutch", 50.0),
                potencial=ocultos.get("potencial", 70.0),
                profissionalismo=ocultos.get("profissionalismo", 50.0),
                team_id=p_data.get("team_id", ""),
                ego=attrs.get("ego", 50.0),
                personalidade=p_data.get("personalidade", "Neutro"),
                salario=contrato.get("salario", 1000),
                multa_rescisoria=contrato.get("multa_rescisoria", 15000),
                moral=status.get("moral", 80.0),
                fadiga=status.get("fadiga", 0.0)
            )
            self.jogadores[p_id] = jogador

        # --- 2. CARREGAR EQUIPAS ---
        times_raw = data.get("times", data.get("teams", []))
        
        if isinstance(times_raw, dict):
            iterador_times = times_raw.items()
        else:
            iterador_times = [(t["id"], t) for t in times_raw]

        for t_id, t_data in iterador_times:
            equipa = Team(
                id=t_id,
                nome=t_data.get("nome", "Equipa"),
                saldo=t_data.get("saldo", 0),
                taticas=t_data.get("taticas", {"ritmo_tr": "default", "postura_ct": "balanced", "permaban": "Vertigo"})
            )
            
            # Vincula os objetos Player reais ao elenco da equipa
            lista_elenco = t_data.get("elenco", [])
            
            # Garante compatibilidade caso o elenco esteja guardado como Dicionário ou Strings(IDs)
            if len(lista_elenco) > 0 and isinstance(lista_elenco[0], dict):
                equipa.elenco = [self.jogadores.get(p["id"]) for p in lista_elenco if p["id"] in self.jogadores]
            else:
                equipa.elenco = [self.jogadores.get(pid) for pid in lista_elenco if pid in self.jogadores]
                
            self.times[t_id] = equipa

        return True

    def salvar_jogo(self):
        """Converte os objetos atuais de volta para JSON e guarda no disco."""
        data = {
            "save_info": self.save_info,
            "times": {},
            "jogadores": {}
        }

        # Serializar Jogadores
        for p_id, p in self.jogadores.items():
            data["jogadores"][p_id] = {
                "id": p.id,
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
            data["times"][t_id] = {
                "id": t.id,
                "nome": t.nome,
                "saldo": t.saldo,
                "taticas": t.taticas,
                "elenco": [p.id for p in t.elenco] # Guarda apenas os IDs
            }

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return True