import random

class Tournament:
    def __init__(self, nome: str, times: list):
        self.nome = nome
        self.participantes = list(times)
        self.fase_atual = "Quartas de Final"
        self.chaveamento = []
        self.vencedores_fase = []
        self.campeao = None
        
        # 💰 PREMIAÇÃO DEFINIDA DO CAMPEONATO
        self.premiacao = {
            "campeao": 500000,
            "vice": 150000,
            "semifinal": 50000
        }

    def gerar_chaveamento_inicial(self):
        """Sorteia os confrontos iniciais."""
        random.shuffle(self.participantes)
        self.chaveamento = []
        for i in range(0, len(self.participantes), 2):
            self.chaveamento.append((self.participantes[i], self.participantes[i+1]))
        return f"🏆 {self.nome}: Chaveamento gerado!"

    def simular_jogo_ia_vs_ia(self, time_a, time_b):
        """Simula jogos entre os outros times controlados pelo computador."""
        pwr_a = sum(p.mira + p.gamesense for p in time_a.elenco) / 10 if time_a.elenco else 50
        pwr_b = sum(p.mira + p.gamesense for p in time_b.elenco) / 10 if time_b.elenco else 50
        
        chance_a = pwr_a / (pwr_a + pwr_b)
        if random.random() < chance_a:
            return time_a, f"🤖 [gray]{time_a.nome} eliminou {time_b.nome}[/]"
        else:
            return time_b, f"🤖 [gray]{time_b.nome} eliminou {time_a.nome}[/]"

    def registrar_vencedor(self, time_vencedor):
        """Salva quem passou de fase."""
        if time_vencedor not in self.vencedores_fase:
            self.vencedores_fase.append(time_vencedor)

    def avancar_fase(self):
        """Move os vencedores para a próxima etapa e PAGA OS PRÊMIOS."""
        if len(self.vencedores_fase) == 4:
            self.fase_atual = "Semifinal"
            self.participantes = list(self.vencedores_fase)
            self.vencedores_fase = []
            self.gerar_chaveamento_inicial()
            return "Avançamos para as Semifinais!"
            
        elif len(self.vencedores_fase) == 2:
            self.fase_atual = "Grande Final"
            
            # 💰 Paga os 2 times que perderam na Semifinal
            eliminados_semi = [t for t in self.participantes if t not in self.vencedores_fase]
            for t in eliminados_semi:
                t.saldo += self.premiacao["semifinal"]
                
            self.participantes = list(self.vencedores_fase)
            self.vencedores_fase = []
            self.gerar_chaveamento_inicial()
            return "Avançamos para a Grande Final!"
            
        elif len(self.vencedores_fase) == 1:
            self.campeao = self.vencedores_fase[0]
            self.fase_atual = "Encerrado"
            
            # 💰 Paga o Campeão e o Vice
            self.campeao.saldo += self.premiacao["campeao"]
            vice = [t for t in self.participantes if t != self.campeao][0]
            vice.saldo += self.premiacao["vice"]
            
            return f"🏆 {self.campeao.nome} é o Campeão! (+${self.premiacao['campeao']:,})"
        
        return "Aguardando resultados da fase..."