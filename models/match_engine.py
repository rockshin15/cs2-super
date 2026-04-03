import random

def calcular_chance_duelo(atacante, defensor, vantagem_tatica: int = 0, peso_arma: int = 0) -> float:
    """Calcula a probabilidade (0 a 100) do atacante vencer o duelo."""
    chance_base = 50.0
    
    # 1. Impacto Mecânico (A mira pura)
    delta_mira = atacante.mira_efetiva - defensor.mira_efetiva 
    impacto_mira = delta_mira * 0.6 
    
    # 2. Impacto Tático e Posicionamento
    delta_gamesense = atacante.gamesense - defensor.gamesense
    impacto_tatico = (delta_gamesense * 0.3) + vantagem_tatica
    
    # 3. Cálculo Final
    chance_final = chance_base + impacto_mira + impacto_tatico + peso_arma
    
    return max(5.0, min(95.0, chance_final))

def simular_trocacao(atacante, defensor, vantagem_tatica: int = 0, peso_arma: int = 0):
    """Roda os dados para decidir quem vive e quem morre."""
    
    # Puxa a vantagem da arma comprada na fase de economia
    peso_atacante = getattr(atacante, 'vantagem_arma_atual', 0)
    peso_defensor = getattr(defensor, 'vantagem_arma_atual', 0)
    vantagem_armamento = peso_atacante - peso_defensor + peso_arma
    
    chance_vitoria_atacante = calcular_chance_duelo(atacante, defensor, vantagem_tatica, vantagem_armamento)
    
    dado = random.uniform(1.0, 100.0)
    
    if dado <= chance_vitoria_atacante:
        if hasattr(atacante, 'economia'):
            atacante.economia.adicionar_dinheiro(300) # Kill Reward
        return True, f"💥 {atacante.nickname} eliminou {defensor.nickname} com um belo tiro."
    else:
        if hasattr(defensor, 'economia'):
            defensor.economia.adicionar_dinheiro(300) # Kill Reward
        return False, f"🛡️ {defensor.nickname} segurou o ângulo e puniu o avanço de {atacante.nickname}."
    
def evento_de_utilitaria(suporte_atacante, defensor):
    """Simula o uso de granadas antes do duelo principal."""
    dado = random.randint(1, 100)
    chance_sucesso_flash = suporte_atacante.gamesense * 0.7

    if dado <= chance_sucesso_flash:
        if dado < chance_sucesso_flash * 0.3:
            return 25, f"💥 {suporte_atacante.nickname} encaixa uma pop-flash perfeita! {defensor.nickname} está cego."
        else:
            return 10, f"🔥 {suporte_atacante.nickname} usa uma Molotov, forçando {defensor.nickname} a sair do ângulo."
    else:
        if dado > 90:
            return -15, f"❌ {suporte_atacante.nickname} erra a flash e cega os próprios companheiros!"
        else:
            return 0, f"💨 As utilitárias de {suporte_atacante.nickname} não encontram impacto."

class RoundSimulator:
    def __init__(self, team_tr, team_ct):
        self.tr_vivos = list(team_tr)
        self.ct_vivos = list(team_ct)
        self.c4_plantada = False
        self.tempo_restante = 115
        self.log_do_round = []

    def adicionar_log(self, texto):
        self.log_do_round.append(texto)

    def verificar_vitoria(self):
        if not self.tr_vivos: return "CT", "Eliminação Total (CT Win)"
        if not self.ct_vivos: return "TR", "Eliminação Total (TR Win)"
        if self.c4_plantada and self.tempo_restante <= 0: return "TR", "A C4 explodiu!"
        if not self.c4_plantada and self.tempo_restante <= 0: return "CT", "Tempo esgotado!"
        return None, None

    def processar_duelo_com_trade(self, atacante, defensor):
        venceu, log = simular_trocacao(atacante, defensor)
        self.adicionar_log(log)

        if venceu:
            self.ct_vivos.remove(defensor)
            # Se restarem poucos CTs, o TR tem espaço para plantar a bomba
            if len(self.ct_vivos) <= 2 and not self.c4_plantada:
                self.c4_plantada = True
                self.adicionar_log("💣 A bomba foi plantada no bomb site!")
        else:
            self.tr_vivos.remove(atacante)
            # Sistema de Trade Kills (companheiro tenta vingar a morte)
            if self.tr_vivos:
                tr_proximo = random.choice(self.tr_vivos)
                venceu_trade, log_trade = simular_trocacao(tr_proximo, defensor, vantagem_tatica=15)
                self.adicionar_log(f"🔄 Tentativa de trade: {log_trade}")
                if venceu_trade:
                    self.ct_vivos.remove(defensor)

    def simular(self):
        self.adicionar_log("--- Round Iniciado ---")
        while True:
            vencedor, motivo = self.verificar_vitoria()
            if vencedor:
                self.adicionar_log(f"🏁 Fim de Round: {motivo}")
                return vencedor, self.log_do_round

            # Sorteia dois jogadores vivos para o duelo
            if self.tr_vivos and self.ct_vivos:
                tr = random.choice(self.tr_vivos)
                ct = random.choice(self.ct_vivos)

                # Fase de utilitárias antes do tiro
                mod, log_u = evento_de_utilitaria(tr, ct)
                if mod != 0:
                    self.adicionar_log(log_u)

                self.processar_duelo_com_trade(tr, ct)

            self.tempo_restante -= random.randint(10, 20)