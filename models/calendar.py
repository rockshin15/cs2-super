from dataclasses import dataclass
from typing import Optional

@dataclass
class EventoCalendario:
    dia_inicio: int
    dia_fim: int
    nome: str
    tipo: str  # "Campeonato", "Ferias", "Bootcamp"

class CalendarioGlobal:
    def __init__(self):
        # Cronograma anual baseado num ciclo de 365 dias
        self.eventos = [
            EventoCalendario(15, 30, "IEM Katowice", "Campeonato"),
            EventoCalendario(70, 85, "Bootcamp de Primavera", "Bootcamp"),
            EventoCalendario(120, 140, "PGL Major", "Campeonato"),
            EventoCalendario(180, 210, "Férias (Player Break)", "Ferias"),
            EventoCalendario(250, 265, "Bootcamp de Outono", "Bootcamp"),
            EventoCalendario(310, 330, "IEM Cologne", "Campeonato")
        ]

    def obter_evento_do_dia(self, dia_atual: int) -> Optional[EventoCalendario]:
        """Descobre o que está a acontecer no dia atual do ano."""
        dia_no_ano = (dia_atual - 1) % 365 + 1
        for evento in self.eventos:
            if evento.dia_inicio <= dia_no_ano <= evento.dia_fim:
                return evento
        return None

    def processar_efeitos_do_dia(self, dia_atual: int, times: dict):
        """Aplica fadiga, treino ou descanso aos elencos dependendo do calendário."""
        evento = self.obter_evento_do_dia(dia_atual)
        
        for time in times.values():
            for p in time.elenco:
                if evento and evento.tipo == "Ferias":
                    # Férias recuperam a equipa totalmente física e mentalmente
                    p.fadiga = 0.0
                    p.moral = max(80.0, p.moral) 
                elif evento and evento.tipo == "Bootcamp":
                    # Treino intenso cansa, mas acelera a inteligência tática
                    p.fadiga = min(100.0, p.fadiga + 3.0) 
                    if p.gamesense < p.potencial + 5:
                        p.gamesense = round(p.gamesense + 0.05, 2)
                else:
                    # Em dias normais (ou intervalos), a fadiga cai naturalmente se não houver jogos
                    p.fadiga = max(0.0, p.fadiga - 1.5)