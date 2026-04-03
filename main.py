import asyncio
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TabbedContent, TabPane, Label, Button, DataTable, Select, RadioSet, RadioButton, RichLog
from textual.containers import Vertical, Horizontal, Grid
from data.database import DataManager
from models.match_engine import RoundSimulator
from models.economy import TeamState, PlayerEconomy, fase_de_compra, distribuir_recompensas
from models.stats import PlayerStats

# Componentes das Abas
class DashboardTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Próximo Jogo: NAVI vs Faze Clan (IEM Katowice Quartas de Final)", id="next_match")
        yield Label("Estado da Equipe: Moral Alta | Fadiga: 15%", id="team_status")
        with Horizontal(id="action_buttons"):
            yield Button("Avançar Dia", variant="success", id="btn_advance")
            yield Button("Simular Partida", variant="primary", id="btn_simulate", disabled=False)

class InboxTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Caixa de Entrada (1 Não Lida)", classes="tab_title")
        yield DataTable(id="inbox_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Data", "Remetente", "Assunto")
        table.add_row("02/04/2026", "Diretoria", "Expectativas para o IEM Katowice")
        table.add_row("01/04/2026", "Scout Principal", "Relatório de m0NESY concluído")

class RosterTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Elenco Principal", classes="tab_title")
        yield DataTable(id="roster_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        # Novas colunas refletindo o banco de dados [cite: 1076]
        table.add_columns("Nome", "Idade", "Função", "Mira", "Tático", "Clutch", "Potencial", "Salário")

        # Acessa o banco de dados que foi carregado na classe principal do App
        db = self.app.db
        
        # Descobre qual é o ID da sua equipe através do save_info e busca o time
        id_do_seu_time = db.save_info["equipa_controlada_id"]
        seu_time = db.times.get(id_do_seu_time)

        # Preenche a tabela varrendo a lista de jogadores do time
        if seu_time:
            for jogador in seu_time.elenco:
                table.add_row(
                    jogador.nome,
                    str(jogador.idade),
                    jogador.funcao_principal,
                    str(jogador.mira),
                    str(jogador.gamesense),
                    str(jogador.clutch),
                    str(jogador.potencial),
                    f"$ {jogador.salario:,}"
                )

class TacticsBoard(Vertical):
    """A tela da Prancheta Tática do time."""
    def compose(self) -> ComposeResult:
        yield Label("Prancheta Tática", classes="tab_title")
        
        # Grid para dividir a tela em duas colunas: Estilo e Map Pool
        with Grid(id="tactics_grid"):
            # Coluna Esquerda: Estilo de Jogo e Funções
            with Vertical(classes="tactics_column"):
                yield Label("Definições de Estilo", classes="section_title")
                yield Label("Ritmo de Ataque (TR):")
                yield Select(
                    [
                        ("Padrão (Default lento, domínio de mapa)", "default"),
                        ("Explosivo (Execuções rápidas e rushes)", "rush"),
                        ("Contato (Foco em fakes e lurkers)", "contact")
                    ],
                    prompt="Escolha o ritmo TR",
                    id="t_pace"
                )
                yield Label("Postura Defensiva (CT):")
                yield Select(
                    [
                        ("Passiva (Foco no Retake)", "retake"),
                        ("Balanceada", "balanced"),
                        ("Agressiva (Busca por First Kills)", "aggressive")
                    ],
                    prompt="Escolha a postura CT",
                    id="ct_stance"
                )
            
            # Coluna Direita: Map Pool
            with Vertical(classes="tactics_column"):
                yield Label("Prioridade de Mapas (Map Pool)", classes="section_title")
                yield Label("Defina o seu Permaban (Mapa vetado automaticamente):")
                with RadioSet(id="permaban_set"):
                    yield RadioButton("Mirage")
                    yield RadioButton("Inferno")
                    yield RadioButton("Nuke")
                    yield RadioButton("Overpass")
                    yield RadioButton("Vertigo", value=True) # Exemplo: Vertigo já vem selecionado
                    yield RadioButton("Ancient")
                    yield RadioButton("Anubis")
                    
        with Horizontal(id="save_tactics_container"):
            yield Button("Salvar Táticas", variant="success", id="btn_save_tactics")

class MarketTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Mercado de Transferências & Scouts", classes="tab_title")
        with Horizontal():
            yield Button("Buscar Jogadores", variant="default")
            yield Button("Ver Relatórios de Scout", variant="default")

class ClubTab(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Visão Geral do Clube", classes="tab_title")
        yield Label("Saldo em Caixa: $ 1.250.000", id="finances")
        yield Label("Patrocinadores Ativos: 3", id="sponsors")
        
class MatchScreen(Screen):
    """A tela onde a magia acontece: a simulação em tempo real."""

    CSS = """
    #match_grid {
        grid-size: 2;
        grid-columns: 2fr 1fr;
    }
    #log_container {
        border: solid $accent;
        background: $boost;
        margin: 1;
        height: 100%;
    }
    #scoreboard_container {
        border: double $primary;
        margin: 1;
        height: 100%;
    }
    .section_title {
        text-style: bold;
        padding-bottom: 1;
        padding-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Grid(id="match_grid"):
            with Vertical(id="log_container"):
                yield Label("TRANSMISSÃO AO VIVO", classes="section_title")
                # O RichLog permite textos coloridos e rolagem automática
                yield RichLog(id="match_log", highlight=True, markup=True)
            with Vertical(id="scoreboard_container"):
                yield Label("PLACAR DA PARTIDA", classes="section_title")
                yield DataTable(id="live_scoreboard")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#live_scoreboard", DataTable)
        table.add_columns("Jogador", "K", "D", "R", "$")

        # Inicia a narração em um processo separado (Worker)
        self.run_worker(self.simular_partida_ao_vivo(), thread=True)

    async def simular_partida_ao_vivo(self):
        """Loop assíncrono que simula os rounds e atualiza a UI."""
        log_widget = self.query_one("#match_log", RichLog)
        table = self.query_one("#live_scoreboard", DataTable)

        db = self.app.db
        id_do_seu_time = db.save_info["equipa_controlada_id"]
        seu_time = db.times.get(id_do_seu_time)
        time_adversario = db.times.get("team_01")

        if not seu_time or not time_adversario:
            log_widget.write("[bold red]Erro: Equipas não encontradas no banco de dados![/]")
            return

        # 1. Inicializa o estado económico e estatístico da partida
        state_tr = TeamState(seu_time.nome)
        state_ct = TeamState(time_adversario.nome)

        for p in seu_time.elenco + time_adversario.elenco:
            p.economia = PlayerEconomy()
            p.estatisticas = PlayerStats()  # Adiciona os stats em branco
            p.vantagem_arma_atual = 0
            p.sobreviveu_round_anterior = False

        # 2. Executar uma partida rápida de 13 rounds
        for round_num in range(1, 14):
            log_widget.write(f"\n[bold yellow]=== Iniciando Round {round_num} ===[/]")
            
            # FASE DE COMPRA
            log_compra_tr = fase_de_compra(state_tr, seu_time.elenco)
            log_compra_ct = fase_de_compra(state_ct, time_adversario.elenco)
            log_widget.write(f"[italic gray]{log_compra_tr}[/]")
            log_widget.write(f"[italic gray]{log_compra_ct}[/]")
            await asyncio.sleep(1)

            simulador = RoundSimulator(seu_time.elenco, time_adversario.elenco)
            vencedor, logs_round = simulador.simular()
            
            for linha in logs_round:
                await asyncio.sleep(0.8)
                log_widget.write(f"-> {linha}")

            # FIM DO ROUND E DISTRIBUIÇÃO DO DINHEIRO
            log_eco = distribuir_recompensas(vencedor, state_tr, state_ct, seu_time.elenco, time_adversario.elenco, simulador.c4_plantada)
            log_widget.write(f"[bold green]Vitória da equipa {vencedor}[/]")
            log_widget.write(f"[bold green]{log_eco}[/]")

            # Regista quem sobreviveu para não voltar a gastar dinheiro com armas no próximo round
            for sobrevivente in simulador.tr_vivos + simulador.ct_vivos:
                sobrevivente.sobreviveu_round_anterior = True

            # Atualiza o Placar com o dinheiro real que cada jogador tem no banco
            table.clear()
            for p in seu_time.elenco + time_adversario.elenco:
                rating_atual = p.estatisticas.calcular_rating()
                linha_kda = f"{p.estatisticas.kills} / {p.estatisticas.deaths}"
                table.add_row(p.nickname, linha_kda, f"{p.estatisticas.get_adr()} ADR", f"{rating_atual} RTG", f"${p.economia.dinheiro}")

            await asyncio.sleep(2)

        # --- FIM DE JOGO: EVOLUÇÃO E RPG ---
        log_widget.write("\n[bold magenta]=== FIM DE PARTIDA: EVOLUÇÃO DOS ATLETAS ===[/]")
        
        for p in seu_time.elenco + time_adversario.elenco:
            # Puxa o Rating REAL de acordo com as kills/mortes do jogo!
            rating_real = p.estatisticas.calcular_rating()
            
            mira_anterior = p.mira
            tatico_anterior = p.gamesense
            
            p.ganhar_experiencia(rating_real)
            
            if (p.mira - mira_anterior) > 0.05 or (p.gamesense - tatico_anterior) > 0.05:
                log_widget.write(f"[green]📈 {p.nickname} ({rating_real} Rating) evoluiu! (Mira: {p.mira} | Tático: {p.gamesense})[/]")
            elif (p.mira - mira_anterior) < -0.05:
                log_widget.write(f"[red]📉 A idade pesou para {p.nickname}. Reflexos diminuíram. (Mira: {p.mira})[/]")

        log_widget.write("\n[bold cyan]Os jogadores envelheceram ligeiramente e estão mais fatigados.[/]")

# Aplicativo Principal
class CSManagerApp(App):
    """Aplicativo principal do CS2 Manager."""
    
    CSS = """
    .tab_title { text-style: bold; padding-bottom: 1; }
    #next_match { padding: 1 2; background: $boost; text-style: bold; }
    #action_buttons { margin-top: 2; height: 3; }
    Button { margin-right: 2; }
    
    /* Novos estilos da Prancheta Tática */
    #tactics_grid {
        grid-size: 2;
        grid-gutter: 2;
        padding: 1;
    }
    .tactics_column {
        border: solid $primary;
        padding: 1;
        height: 100%;
    }
    .section_title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #save_tactics_container {
        margin-top: 1;
        align: right middle;
    }
    """

    BINDINGS = [
        ("d", "toggle_dark", "Tema (Escuro/Claro)"),
        ("space", "advance_day", "Avançar Dia"),
        ("q", "quit", "Sair")
    ]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # O __init__ garante que o banco de dados seja carregado ANTES da interface existir
        self.db = DataManager()
        self.db.carregar_jogo()

    def on_mount(self) -> None:
        """Dispara notificações quando a interface termina de carregar."""
        nome_treinador = self.db.save_info.get("manager_nome", "Treinador")
        self.notify(f"Bem-vindo de volta, {nome_treinador}!", title="Save Carregado")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                yield DashboardTab()
            with TabPane("Caixa de Entrada", id="inbox"):
                yield InboxTab()
            with TabPane("Elenco", id="roster"):
                yield RosterTab()
            with TabPane("Táticas", id="tactics"): # ADICIONAMOS A NOVA ABA AQUI
                yield TacticsBoard()
            with TabPane("Mercado", id="market"):
                yield MarketTab()
            with TabPane("Clube", id="club"):
                yield ClubTab()
        yield Footer()

    # ... (Seus eventos continuam aqui embaixo)
    # Ações e Eventos
    def action_advance_day(self) -> None:
        """Ação ativada ao apertar Espaço ou o botão."""
        self.notify("Um dia se passou...", title="Tempo Avançado")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Captura os cliques em botões."""
        if event.button.id == "btn_advance":
            self.action_advance_day()
        elif event.button.id == "btn_simulate":
            # Abre a tela de partida por cima do Dashboard
            self.push_screen(MatchScreen())

if __name__ == "__main__":
    app = CSManagerApp()
    app.run()