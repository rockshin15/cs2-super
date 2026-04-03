from dataclasses import dataclass

@dataclass
class Player:
    nome: str
    nickname: str
    idade: float
    funcao_principal: str
    
    # Atributos Visíveis (Mecânica e Tática)
    mira: float
    gamesense: float
    clutch: float
    
    # Atributos Ocultos (RPG / Evolução)
    potencial: float
    profissionalismo: float
    
    # Atributos dinâmicos preenchidos pela Factory ou JSON (com valores padrão)
    id: str = ""
    team_id: str = ""
    ego: float = 50.0
    personalidade: str = "Neutro"
    salario: int = 0
    multa_rescisoria: int = 0  # ADICIONE ESTA LINHA
    moral: float = 80.0
    fadiga: float = 0.0

    @property
    def mira_efetiva(self) -> float:
        """A mira cai drasticamente se o jogador estiver exausto."""
        penalidade_fadiga = 0.0
        if self.fadiga > 60:
            penalidade_fadiga = (self.fadiga - 60) * 0.5
        return max(1.0, self.mira - penalidade_fadiga)

    @property
    def clutch_efetivo(self) -> float:
        """O poder de decisão é afetado pela confiança (moral)."""
        modificador_moral = 0.0
        if self.moral < 40:
            modificador_moral = -15.0 # Tremedeira
        elif self.moral > 85:
            modificador_moral = 10.0  # Confiante, no auge
        return min(100.0, max(1.0, self.clutch + modificador_moral))

    def calcular_rating_geral(self) -> float:
        """Calcula a média geral de habilidade do jogador."""
        return (self.mira + self.gamesense + self.clutch) / 3
    
    def ganhar_experiencia(self, rating_partida: float):
        """Atualiza os atributos do jogador após uma partida, simulando o ciclo de vida real."""
        import random
        
        # 1. Impacto da Performance (Moral e Multiplicador de XP)
        if rating_partida >= 1.15:
            self.moral = min(100.0, self.moral + 5)
            multiplicador_xp = 1.3 # Boa performance acelera o aprendizado
        elif rating_partida <= 0.85:
            self.moral = max(0.0, self.moral - 5)
            multiplicador_xp = 0.6 # Má fase trava o desenvolvimento
        else:
            multiplicador_xp = 1.0

        crescimento_mira = 0.0
        crescimento_tatico = 0.0

        # 2. Curva de Idade (Mecânica decai, Inteligência sobe)
        if self.idade < 24:
            # Prodígios: Explodem em mecânica, aprendem tática aos poucos
            crescimento_mira = random.uniform(0.1, 0.4) * multiplicador_xp
            crescimento_tatico = random.uniform(0.05, 0.2) * multiplicador_xp
        elif 24 <= self.idade <= 28:
            # Auge: Mecânica no pico, evolução tática forte
            crescimento_mira = random.uniform(0.0, 0.15) * multiplicador_xp
            crescimento_tatico = random.uniform(0.1, 0.3) * multiplicador_xp
        else:
            # Veteranos (>28): Reflexos caem, mas o cérebro compensa
            crescimento_mira = random.uniform(-0.3, -0.05)
            crescimento_tatico = random.uniform(0.0, 0.15) * multiplicador_xp

        # 3. Barreira do Potencial (Não podem crescer infinitamente)
        # O crescimento diminui drasticamente à medida que se aproximam do teto
        if self.mira < self.potencial:
            distancia_teto = (self.potencial - self.mira) / 100.0
            self.mira += crescimento_mira * distancia_teto
        elif crescimento_mira < 0: 
            # Permite perder mira mesmo estando no teto
            self.mira += crescimento_mira

        # O Gamesense pode ultrapassar o teto mecânico em 5 pontos (inteligência supera talento)
        if self.gamesense < (self.potencial + 5):
            distancia_teto_tatico = ((self.potencial + 5) - self.gamesense) / 100.0
            self.gamesense += crescimento_tatico * distancia_teto_tatico

        # 4. Limites Finais, Fadiga e Envelhecimento
        self.mira = max(1.0, min(100.0, round(self.mira, 2)))
        self.gamesense = max(1.0, min(100.0, round(self.gamesense, 2)))
        
        self.fadiga = min(100.0, self.fadiga + random.uniform(5.0, 12.0))
        # Cada partida avança ligeiramente a idade do jogador
        self.idade = round(self.idade + 0.01, 2)