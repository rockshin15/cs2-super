import random
from data.names_db import NOMES, SOBRENOMES, NACIONALIDADES, gerar_nickname
from models.player import Player

class PlayerFactory:
    def __init__(self):
        self.funcoes = ["IGL", "AWPer", "Entry", "Support", "Anchor"]
        self.personalidades = ["Lider", "Solitário", "Temperamental", "Profissional", "Estrela"]

    def _gerar_atributo(self, media: int, desvio: int) -> float:
        """Gera um número seguindo a curva de sino, preso entre 1 e 100."""
        valor = random.gauss(media, desvio)
        return max(1.0, min(100.0, valor))

    def gerar_novo_jogador(self, tier_alvo: str = "Médio") -> Player:
        nacionalidade = random.choice(NACIONALIDADES)
        nome = random.choice(NOMES[nacionalidade])
        sobrenome = random.choice(SOBRENOMES[nacionalidade])
        nickname = gerar_nickname()

        idade = round(random.uniform(16.0, 32.0), 1)
        funcao = random.choice(self.funcoes)
        personalidade = random.choice(self.personalidades)

        medias_base = {"Alto": 80, "Médio": 60, "Baixo": 45}
        media = medias_base.get(tier_alvo, 60)

        mira = self._gerar_atributo(media + (10 if funcao in ["Entry", "AWPer"] else 0), 8)
        gamesense = self._gerar_atributo(media + (15 if funcao == "IGL" else 0), 8)
        clutch = self._gerar_atributo(media + (5 if funcao == "AWPer" else 0), 10)

        if idade < 20:
            potencial = self._gerar_atributo(media + 20, 10)
        elif idade < 25:
            potencial = self._gerar_atributo(media + 10, 5)
        else:
            potencial = max(mira, gamesense, clutch) + random.uniform(0, 3)

        potencial = max(mira, min(100.0, potencial))
        ego = self._gerar_atributo(50 + (20 if funcao in ["AWPer", "Entry"] else -10), 15)

        salario = int(((mira + gamesense + clutch) / 3) * 150)
        if potencial > 85 and idade < 21:
            salario = int(salario * 1.5)

        # Instancia o jogador principal
        jogador = Player(
            nome=f"{nome} '{nickname}' {sobrenome}",
            nickname=nickname,
            idade=idade,
            funcao_principal=funcao,
            mira=round(mira, 1),
            gamesense=round(gamesense, 1),
            clutch=round(clutch, 1),
            potencial=round(potencial, 1),
            profissionalismo=round(self._gerar_atributo(65, 15), 1)
        )
        
        # Adiciona os atributos dinâmicos necessários para o JSON
        jogador.id = f"ply_{random.randint(10000, 99999)}"
        jogador.team_id = "free_agent"
        jogador.ego = round(ego, 1)
        jogador.personalidade = personalidade
        jogador.salario = salario
        jogador.moral = 80.0
        jogador.fadiga = 0.0
        
        return jogador

    def popular_mundo(self, quantidade: int) -> list[Player]:
        """Gera uma lista massiva de jogadores para preencher a base de dados."""
        mundo = []
        for _ in range(quantidade):
            tier = "Alto" if random.random() < 0.1 else "Médio"
            mundo.append(self.gerar_novo_jogador(tier))
        return mundo