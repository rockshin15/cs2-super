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