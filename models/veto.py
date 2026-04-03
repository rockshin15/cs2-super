import random

MAPAS_ATIVOS = ["Mirage", "Inferno", "Nuke", "Overpass", "Vertigo", "Ancient", "Anubis"]

# Define a exigência principal de cada mapa para cruzar com os atributos do elenco
PERFIL_MAPAS = {
    "Mirage": {"foco": "mira"},
    "Inferno": {"foco": "tatico"},
    "Nuke": {"foco": "tatico"},
    "Overpass": {"foco": "tatico"},
    "Vertigo": {"foco": "mira"},
    "Ancient": {"foco": "mira"},
    "Anubis": {"foco": "mira"}
}

class VetoSystem:
    def __init__(self, time_a, time_b):
        self.time_a = time_a
        self.time_b = time_b
        self.mapas_disponiveis = list(MAPAS_ATIVOS)
        self.log_veto = []

    def _calcular_forca_mapa(self, time, mapa, adversario):
        """Calcula uma pontuação de 0 a 100 do quão bom o time é neste mapa."""
        
        # 1. Capacidade Técnica do Elenco vs Exigência do Mapa
        media_mira = sum(p.mira for p in time.elenco) / len(time.elenco) if time.elenco else 50
        media_tatico = sum(p.gamesense for p in time.elenco) / len(time.elenco) if time.elenco else 50
        
        perfil = PERFIL_MAPAS[mapa]
        bonus_tecnico = 0
        if perfil["foco"] == "mira":
            bonus_tecnico = (media_mira - 50) * 0.4 # Times com muita mira ganham bônus aqui
        elif perfil["foco"] == "tatico":
            bonus_tecnico = (media_tatico - 50) * 0.4 # Times inteligentes preferem Nuke/Overpass

        # 2. Histórico de Performance (Winrate)
        # Se não existir ainda, assumimos uma força base de 50
        stats = getattr(time, 'map_stats', {}).get(mapa, {"wins": 0, "losses": 0})
        total_jogos = stats["wins"] + stats["losses"]
        winrate = (stats["wins"] / total_jogos * 100) if total_jogos > 0 else 50.0

        # 3. Análise do Adversário (Se o inimigo amassa neste mapa, a força cai)
        stats_adv = getattr(adversario, 'map_stats', {}).get(mapa, {"wins": 0, "losses": 0})
        jogos_adv = stats_adv["wins"] + stats_adv["losses"]
        winrate_adv = (stats_adv["wins"] / jogos_adv * 100) if jogos_adv > 0 else 50.0
        medo_adversario = (winrate_adv - 50) * 0.5 # Subtrai a força baseada no quão bom o inimigo é

        return winrate + bonus_tecnico - medo_adversario

    def _escolher_ban(self, time_banindo, time_adversario):
        """A IA escolhe qual mapa remover da pool."""
        
        # 1. Verifica se o Permaban do time ainda está na mesa
        permaban = time_banindo.taticas.get("permaban")
        if permaban in self.mapas_disponiveis:
            return permaban

        # 2. Se não houver permaban, bane o mapa com a PIOR pontuação calculada
        forcas = {}
        for m in self.mapas_disponiveis:
            forcas[m] = self._calcular_forca_mapa(time_banindo, m, time_adversario)

        # Pega a chave (nome do mapa) que tem o menor valor no dicionário
        pior_mapa = min(forcas, key=forcas.get)
        return pior_mapa

    def realizar_veto_bo1(self):
        """Executa um veto Melhor de 1 (Banem até sobrar 1)."""
        self.log_veto.append("🗺️ [bold cyan]INÍCIO DO VETO (MD1)[/]")
        turno_a = True # time_a começa a banir

        while len(self.mapas_disponiveis) > 1:
            time_atual = self.time_a if turno_a else self.time_b
            time_inimigo = self.time_b if turno_a else self.time_a

            mapa_banido = self._escolher_ban(time_atual, time_inimigo)
            self.mapas_disponiveis.remove(mapa_banido)
            self.log_veto.append(f"❌ [red]{time_atual.nome} baniu {mapa_banido}[/]")
            
            turno_a = not turno_a # Passa a vez

        mapa_sobra = self.mapas_disponiveis[0]
        self.log_veto.append(f"✅ [bold green]O mapa escolhido é {mapa_sobra}![/]")
        return mapa_sobra, self.log_veto