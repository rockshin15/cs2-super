import random

def calcular_chance_duelo(atacante, defensor, vantagem_tatica: int = 0, peso_arma: int = 0) -> float:
    """Calcula a probabilidade (0 a 100) do atacante vencer o duelo."""
    chance_base = 50.0
    
    # 1. Impacto Mecânico (A mira pura)
    # Usamos a mira_efetiva que já calcula o cansaço do jogador
    delta_mira = atacante.mira_efetiva - defensor.mira_efetiva 
    impacto_mira = delta_mira * 0.6 # A mira tem peso forte no 1v1
    
    # 2. Impacto Tático e Posicionamento
    delta_gamesense = atacante.gamesense - defensor.gamesense
    impacto_tatico = (delta_gamesense * 0.3) + vantagem_tatica
    
    # 3. Cálculo Final
    chance_final = chance_base + impacto_mira + impacto_tatico + peso_arma
    
    # Estabelece limites: Sempre existe o "fator CS" (mínimo de 5% de chance de dar certo/errado)
    return max(5.0, min(95.0, chance_final))

def simular_trocacao(atacante, defensor, vantagem_tatica: int = 0, peso_arma: int = 0):
    """Roda os dados para decidir quem vive e quem morre."""
    chance_vitoria_atacante = calcular_chance_duelo(atacante, defensor, vantagem_tatica, peso_arma)
    
    # Rola o RNG (Um número de 1 a 100)
    dado = random.uniform(1.0, 100.0)
    
    if dado <= chance_vitoria_atacante:
        return True, f"💥 {atacante.nickname} eliminou {defensor.nickname} com um belo tiro."
    else:
        return False, f"🛡️ {defensor.nickname} segurou o ângulo e puniu o avanço de {atacante.nickname}."