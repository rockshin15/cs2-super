from dataclasses import dataclass

MAX_MONEY = 16000
START_MONEY = 800
KILL_REWARD = 300
REWARD_WIN = 3250
REWARD_LOSS_BASE = 1400
LOSS_BONUS_INCREMENT = 500
PLANT_BONUS = 800

@dataclass
class PlayerEconomy:
    dinheiro: int = START_MONEY

    def adicionar_dinheiro(self, valor: int):
        self.dinheiro = min(self.dinheiro + valor, MAX_MONEY)

    def gastar(self, valor: int) -> bool:
        if self.dinheiro >= valor:
            self.dinheiro -= valor
            return True
        return False

class TeamState:
    def __init__(self, nome: str):
        self.nome = nome
        self.loss_streak = 0
        self.rounds_ganhos = 0

    def get_loss_bonus(self) -> int:
        streak_limitada = min(self.loss_streak, 4)
        return REWARD_LOSS_BASE + (streak_limitada * LOSS_BONUS_INCREMENT)

KITS = {
    "Eco": {"custo": 0, "peso_arma": -15, "descricao": "Pistolas"},
    "Force": {"custo": 2000, "peso_arma": -5, "descricao": "SMGs/Coletes"},
    "Full Buy": {"custo": 4500, "peso_arma": 10, "descricao": "Rifles/Granadas"},
    "AWP Buy": {"custo": 6500, "peso_arma": 25, "descricao": "AWP/Colete"}
}

def fase_de_compra(team_state: TeamState, jogadores: list, decisao_manager="Automatico"):
    dinheiro_total = sum(p.economia.dinheiro for p in jogadores)
    media_dinheiro = dinheiro_total / len(jogadores) if jogadores else 0

    if decisao_manager == "Eco" or media_dinheiro < 2000:
        tipo_compra = "Eco"
    elif decisao_manager == "Force" or (media_dinheiro < 4500 and team_state.loss_streak > 1):
        tipo_compra = "Force"
    else:
        tipo_compra = "Full Buy"

    log_compras = f"🛒 {team_state.nome} decide fazer: {tipo_compra}."

    for jogador in jogadores:
        kit_desejado = KITS["AWP Buy"] if jogador.funcao_principal == "AWPer" and tipo_compra == "Full Buy" else KITS[tipo_compra]

        # Só compra se morreu no round passado ou se o kit que sobrou for pior que o desejado
        precisa_comprar = not getattr(jogador, 'sobreviveu_round_anterior', False) or getattr(jogador, 'vantagem_arma_atual', -20) < kit_desejado["peso_arma"]

        if precisa_comprar:
            if jogador.economia.gastar(kit_desejado["custo"]):
                jogador.vantagem_arma_atual = kit_desejado["peso_arma"]
            else:
                # Compra o que o dinheiro permitir
                if jogador.economia.gastar(2000):
                    jogador.vantagem_arma_atual = KITS["Force"]["peso_arma"]
                else:
                    jogador.vantagem_arma_atual = KITS["Eco"]["peso_arma"]
        
        # Limpa a flag para o round que vai começar
        jogador.sobreviveu_round_anterior = False

    return log_compras

def distribuir_recompensas(vencedor: str, team_tr: TeamState, team_ct: TeamState, jogadores_tr: list, jogadores_ct: list, c4_plantada: bool):
    if vencedor == "TR":
        for p in jogadores_tr: p.economia.adicionar_dinheiro(REWARD_WIN)
        team_tr.loss_streak = 0
        team_tr.rounds_ganhos += 1
        
        bonus_ct = team_ct.get_loss_bonus()
        for p in jogadores_ct: p.economia.adicionar_dinheiro(bonus_ct)
        team_ct.loss_streak += 1
    else:
        for p in jogadores_ct: p.economia.adicionar_dinheiro(REWARD_WIN)
        team_ct.loss_streak = 0
        team_ct.rounds_ganhos += 1
        
        bonus_tr = team_tr.get_loss_bonus()
        if c4_plantada: bonus_tr += PLANT_BONUS
        for p in jogadores_tr: p.economia.adicionar_dinheiro(bonus_tr)
        team_tr.loss_streak += 1

    return f"💰 Economia: Loss Bonus TR (${team_tr.get_loss_bonus()}) | Loss Bonus CT (${team_ct.get_loss_bonus()})"