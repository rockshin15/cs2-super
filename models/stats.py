class PlayerStats:
    def __init__(self):
        self.kills = 0
        self.deaths = 0
        self.dano_causado = 0
        self.rounds_jogados = 0
        self.kast_rounds = 0 # Rounds com Kill, Assist, Survive ou Trade

    def get_adr(self):
        """Average Damage per Round (Dano Médio)"""
        return round(self.dano_causado / self.rounds_jogados, 1) if self.rounds_jogados > 0 else 0.0

    def get_kpr(self):
        """Kills per Round"""
        return self.kills / self.rounds_jogados if self.rounds_jogados > 0 else 0

    def get_dpr(self):
        """Deaths per Round"""
        return self.deaths / self.rounds_jogados if self.rounds_jogados > 0 else 0

    def get_kast_pct(self):
        """Porcentagem de rounds em que o jogador teve impacto positivo"""
        return round((self.kast_rounds / self.rounds_jogados) * 100, 1) if self.rounds_jogados > 0 else 0.0

    def calcular_rating(self):
        """Fórmula ponderada do Rating 2.0"""
        adr_impact = self.get_adr() / 100.0
        kpr_impact = self.get_kpr()
        surv_impact = 1.0 - self.get_dpr()
        kast_impact = self.get_kast_pct() / 100.0
        
        # Pesos baseados na importância de cada estatística
        rating = (kpr_impact * 0.7) + (surv_impact * 0.4) + (adr_impact * 0.5) + (kast_impact * 0.3)
        return round(max(0.0, rating), 2)