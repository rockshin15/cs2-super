import json
from models.player import Player
from models.team import Team

class DataManager:
    def __init__(self, filepath: str = "data/database.json"):
        self.filepath = filepath
        self.times = {}
        self.jogadores = {}
        self.save_info = {}

    def carregar_jogo(self):
        """Lê o JSON e converte os dados brutos em objetos Python."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
        self.save_info = dados["save_info"]

        # 1. Carrega os Times
        for t_data in dados["times"]:
            self.times[t_data["id"]] = Team(
                id=t_data["id"],
                nome=t_data["nome"],
                saldo=t_data["financas"]["saldo"],
                taticas=t_data["taticas"]
            )

        # 2. Carrega os Jogadores e vincula aos Times
        for p_data in dados["jogadores"]:
            jogador = Player(
                id=p_data["id"],
                team_id=p_data["team_id"],
                nome=p_data["nome"],
                nickname=p_data["nickname"],
                idade=p_data["idade"],
                funcao_principal=p_data["funcao"],
                mira=p_data["atributos"]["mira"],
                gamesense=p_data["atributos"]["gamesense"],
                clutch=p_data["atributos"]["clutch"],
                potencial=p_data["ocultos"]["potencial"],
                profissionalismo=p_data["ocultos"]["profissionalismo"],
                ego=p_data["ocultos"]["ego"],
                personalidade=p_data["ocultos"]["personalidade"],
                salario=p_data["contrato"]["salario"],
                moral=p_data["status"]["moral"],
                fadiga=p_data["status"]["fadiga"]
            )

            # Adiciona o jogador ao dicionário global de busca rápida
            self.jogadores[jogador.id] = jogador

            # Adiciona o jogador fisicamente na lista 'elenco' do seu time correspondente
            if jogador.team_id in self.times:
                self.times[jogador.team_id].elenco.append(jogador)
                
        print(f"Banco de dados carregado: {len(self.times)} times e {len(self.jogadores)} jogadores ativos.")

    def salvar_jogo(self):
        """Aqui faremos o processo inverso no futuro (Salvar progresso)."""
        pass