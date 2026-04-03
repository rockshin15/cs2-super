import json
import random
from generators.player_factory import PlayerFactory

def gerar_mundo_inicial():
    print("Iniciando a criação do mundo...")
    factory = PlayerFactory()
    
    # 1. Definir os times base
    nomes_times = ["NAVI", "Faze Clan", "Vitality", "G2 Esports", "MOUZ", "Sua Equipe", "Liquid", "Cloud9"]
    times = []
    jogadores_globais = []
    
    id_counter_team = 1
    id_counter_player = 1
    
    for nome in nomes_times:
        team_id = f"team_{id_counter_team:02d}"
        
        # Cria a estrutura do time
        time = {
            "id": team_id,
            "nome": nome,
            "reputacao": random.randint(70, 99) if nome != "Sua Equipe" else 50,
            "financas": {
                "saldo": random.randint(1000000, 3000000) if nome != "Sua Equipe" else 500000,
                "orcamento_transferencias": 500000
            },
            "taticas": {
                "ritmo_tr": "default",
                "postura_ct": "balanced",
                "permaban": random.choice(["Vertigo", "Anubis", "Nuke", "Mirage"])
            }
        }
        times.append(time)
        
        # 2. Gerar 5 jogadores para cada time garantindo as funções
        funcoes_necessarias = ["IGL", "AWPer", "Entry", "Support", "Anchor"]
        
        for funcao in funcoes_necessarias:
            # Pede para a fábrica gerar um jogador
            # Se for "Sua Equipe", geramos jogadores um pouco piores para dar desafio
            tier = "Alto" if nome in ["NAVI", "Faze Clan", "Vitality"] else ("Baixo" if nome == "Sua Equipe" else "Médio")
            
            # Aqui ajustamos levemente a fábrica para aceitar a função forçada
            novo_jogador = factory.gerar_novo_jogador(tier_alvo=tier)
            novo_jogador.funcao_principal = funcao 
            novo_jogador.team_id = team_id
            novo_jogador.id = f"ply_{id_counter_player:03d}"
            
            # Converte a dataclass do jogador para um dicionário que o JSON entenda
            jogador_dict = {
                "id": novo_jogador.id,
                "team_id": novo_jogador.team_id,
                "nome": novo_jogador.nome,
                "nickname": novo_jogador.nickname,
                "idade": novo_jogador.idade,
                "funcao": novo_jogador.funcao_principal,
                "atributos": {
                    "mira": novo_jogador.mira,
                    "gamesense": novo_jogador.gamesense,
                    "clutch": novo_jogador.clutch
                },
                "ocultos": {
                    "potencial": novo_jogador.potencial,
                    "profissionalismo": novo_jogador.profissionalismo,
                    "ego": getattr(novo_jogador, 'ego', 50),
                    "personalidade": getattr(novo_jogador, 'personalidade', 'Profissional')
                },
                "status": {
                    "moral": novo_jogador.moral,
                    "fadiga": novo_jogador.fadiga
                },
                "contrato": {
                    "salario": novo_jogador.salario,
                    "multa_rescisoria": novo_jogador.salario * 50,
                    "meses_restantes": random.randint(6, 24)
                }
            }
            jogadores_globais.append(jogador_dict)
            id_counter_player += 1
            
        id_counter_team += 1

    # 3. Gerar Free Agents (Jogadores sem time para o mercado)
    print("Gerando jogadores livres no mercado...")
    for _ in range(30):
        livre = factory.gerar_novo_jogador(tier_alvo=random.choice(["Baixo", "Médio"]))
        livre.id = f"ply_{id_counter_player:03d}"
        livre.team_id = "free_agent"
        # ... (mesmo processo de conversão para dicionário)
        jogador_dict = {
             "id": livre.id, "team_id": livre.team_id, "nome": livre.nome, "nickname": livre.nickname,
             "idade": livre.idade, "funcao": livre.funcao_principal,
             "atributos": {"mira": livre.mira, "gamesense": livre.gamesense, "clutch": livre.clutch},
             "ocultos": {"potencial": livre.potencial, "profissionalismo": livre.profissionalismo, "ego": 50, "personalidade": "Neutro"},
             "status": {"moral": 80.0, "fadiga": 0.0},
             "contrato": {"salario": livre.salario, "multa_rescisoria": 0, "meses_restantes": 0}
        }
        jogadores_globais.append(jogador_dict)
        id_counter_player += 1

    # 4. Montar a estrutura final e salvar
    banco_de_dados = {
        "save_info": {
            "manager_nome": "Treinador",
            "equipa_controlada_id": "team_06", # Corresponde a "Sua Equipe"
            "dia_atual": 1,
            "versao_db": "1.0"
        },
        "times": times,
        "jogadores": jogadores_globais
    }

    # Salva no arquivo
    with open("data/database.json", "w", encoding="utf-8") as f:
        json.dump(banco_de_dados, f, indent=4, ensure_ascii=False)
        
    print("Mundo gerado com sucesso em data/database.json!")

if __name__ == "__main__":
    gerar_mundo_inicial()