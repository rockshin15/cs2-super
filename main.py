import asyncio
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, TabbedContent, TabPane, Label, Button, DataTable, Select, RadioSet, RadioButton, RichLog
from textual.containers import Vertical, Horizontal, Grid
from data.database import DataManager
from models.match_engine import RoundSimulator
from models.economy import TeamState, PlayerEconomy, fase_de_compra, distribuir_recompensas
from models.stats import PlayerStats
from models.calendar import CalendarioGlobal
from models.veto import VetoSystem
from models.tournament import Tournament

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
        yield Label("Mercado Global de Transferências", classes="tab_title")
        yield Label("Selecione um jogador para contratar (O valor será deduzido do saldo do clube).")
        yield DataTable(id="market_table")

    def on_mount(self) -> None:
        self.atualizar_tabela()

    def atualizar_tabela(self) -> None:
        table = self.query_one("#market_table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Nome", "Equipa", "Mira", "Tático", "Potencial", "Preço")

        db = self.app.db
        id_seu_time = db.save_info["equipa_controlada_id"]

        # Lista todos os jogadores que NÃO estão no seu time
        for jogador in db.jogadores.values():
            if jogador.team_id != id_seu_time:
                nome_time = db.times[jogador.team_id].nome if jogador.team_id in db.times else "Agente Livre"
                
                table.add_row(
                    jogador.id,
                    jogador.nickname,
                    nome_time,
                    f"{jogador.mira:.1f}",
                    f"{jogador.gamesense:.1f}",
                    f"{jogador.potencial:.1f}",
                    f"$ {jogador.multa_rescisoria:,}",
                    key=jogador.id
                )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Dispara quando o utilizador clica numa linha para comprar."""
        player_id = str(event.row_key.value)
        self.app.processar_compra(player_id)
        self.atualizar_tabela()

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
        from models.veto import VetoSystem
        from models.economy import TeamState, PlayerEconomy, fase_de_compra, distribuir_recompensas
        from models.stats import PlayerStats
        from models.match_engine import RoundSimulator
        
        log_widget = self.query_one("#match_log", RichLog)
        table = self.query_one("#live_scoreboard", DataTable)

        app = self.app
        db = app.db
        id_do_seu_time = db.save_info["equipa_controlada_id"]
        seu_time = db.times.get(id_do_seu_time)
        
        # 1. DEFINIR O ADVERSÁRIO (Verifica se há um torneio ativo)
        time_adversario = None
        if hasattr(app, 'torneio_ativo') and app.torneio_ativo:
            # Procura na chave do campeonato contra quem vai jogar
            for t1, t2 in app.torneio_ativo.chaveamento:
                if t1.id == id_do_seu_time: 
                    time_adversario = t2
                elif t2.id == id_do_seu_time: 
                    time_adversario = t1
            
            # Se não encontrou o seu time na chave, é porque já foi eliminado
            if not time_adversario:
                log_widget.write("[bold yellow]A sua equipa já foi eliminada ou não joga hoje.[/]")
                return
                
            log_widget.write(f"[bold magenta]🏆 {app.torneio_ativo.nome} - {app.torneio_ativo.fase_atual}[/]")
        else:
            # Amigável de treino se não houver torneio a decorrer
            time_adversario = db.times.get("team_01") 

        if not seu_time or not time_adversario:
            log_widget.write("[bold red]Erro: Equipas não encontradas no banco de dados![/]")
            return

        # 2. NOVA FASE: PICK & BAN
        sistema_veto = VetoSystem(seu_time, time_adversario)
        mapa_jogado, logs_veto = sistema_veto.realizar_veto_bo1()
        
        for linha in logs_veto:
            await asyncio.sleep(0.6) # Dá um tempinho para lermos cada ban
            log_widget.write(linha)
            
        await asyncio.sleep(1.5) # Pausa dramática antes de o jogo começar
        # -----------------------------

        # 3. INICIALIZA O ESTADO ECONÓMICO E ESTATÍSTICO
        state_tr = TeamState(seu_time.nome)
        state_ct = TeamState(time_adversario.nome)

        for p in seu_time.elenco + time_adversario.elenco:
            p.economia = PlayerEconomy()
            p.estatisticas = PlayerStats()  # Adiciona os stats em branco
            p.vantagem_arma_atual = 0
            p.sobreviveu_round_anterior = False

        # PLACAR GERAL DA PARTIDA
        rounds_tr = 0 # Pontos da Sua Equipe
        rounds_ct = 0 # Pontos do Adversário
        vencedor_partida = None

        # 4. EXECUTAR A PARTIDA (Formato MR12 - Máximo de 24 rounds)
        for round_num in range(1, 25):
            log_widget.write(f"\n[bold yellow]=== Iniciando Round {round_num} (Placar: {seu_time.nome} {rounds_tr} x {rounds_ct} {time_adversario.nome}) ===[/]")
            
            # FASE DE COMPRA
            log_compra_tr = fase_de_compra(state_tr, seu_time.elenco)
            log_compra_ct = fase_de_compra(state_ct, time_adversario.elenco)
            log_widget.write(f"[italic gray]{log_compra_tr}[/]")
            log_widget.write(f"[italic gray]{log_compra_ct}[/]")
            await asyncio.sleep(1)

            # SIMULAÇÃO DO ROUND
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
                
            # Atualiza o placar do jogo
            if vencedor == "TR":
                rounds_tr += 1
            else:
                rounds_ct += 1

            # Atualiza a Tabela com o dinheiro real e as ESTATÍSTICAS
            table.clear()
            for p in seu_time.elenco + time_adversario.elenco:
                rating_atual = p.estatisticas.calcular_rating()
                linha_kda = f"{p.estatisticas.kills} / {p.estatisticas.deaths}"
                table.add_row(p.nickname, linha_kda, f"{p.estatisticas.get_adr()} ADR", f"{rating_atual} RTG", f"${p.economia.dinheiro}")

            await asyncio.sleep(2)
            
            # Condição de Vitória do Mapa (Quem fizer 13 pontos ganha)
            if rounds_tr == 13:
                vencedor_partida = "TR"
                break
            elif rounds_ct == 13:
                vencedor_partida = "CT"
                break

        # 5. FIM DE JOGO: EVOLUÇÃO E RPG
        log_widget.write(f"\n[bold magenta]=== FIM DE PARTIDA: {seu_time.nome} {rounds_tr} x {rounds_ct} {time_adversario.nome} ===[/]")
        log_widget.write("[bold magenta]--- EVOLUÇÃO DOS ATLETAS ---[/]")
        
        for p in seu_time.elenco + time_adversario.elenco:
            # Puxa o Rating REAL de acordo com as kills/mortes do jogo!
            rating_real = p.estatisticas.calcular_rating()
            
            mira_anterior = p.mira
            tatico_anterior = p.gamesense
            
            p.ganhar_experiencia(rating_real)
            
            # Avisa se o jogador evoluiu ou caiu de rendimento
            if (p.mira - mira_anterior) > 0.05 or (p.gamesense - tatico_anterior) > 0.05:
                log_widget.write(f"[green]📈 {p.nickname} ({rating_real} Rating) evoluiu! (Mira: {p.mira} | Tático: {p.gamesense})[/]")
            elif (p.mira - mira_anterior) < -0.05:
                log_widget.write(f"[red]📉 A idade pesou para {p.nickname}. Reflexos diminuíram. (Mira: {p.mira})[/]")

        log_widget.write("\n[bold cyan]Os jogadores envelheceram ligeiramente e estão mais fatigados.[/]")
        self.app.db.salvar_jogo() # <--- SALVAR APÓS O JOGO (Estatísticas mudaram)
        self.app.notify("Resultado e evoluções guardados.", title="Fim de Match")
        # 6. RESOLUÇÃO DO TORNEIO (Avançar Fase e Premiação)
        if hasattr(app, 'torneio_ativo') and app.torneio_ativo:
            # Regista se você ganhou ou perdeu
            time_vencedor = seu_time if vencedor_partida == "TR" else time_adversario
            app.torneio_ativo.registrar_vencedor(time_vencedor)
            
            log_widget.write(f"\n[bold yellow]--- Simulando outros jogos da {app.torneio_ativo.fase_atual} ---[/]")
            
            # Simula o resto da chave do torneio (Computador vs Computador)
            for t1, t2 in app.torneio_ativo.chaveamento:
                if t1.id != seu_time.id and t2.id != seu_time.id: # Ignora o jogo que o utilizador acabou de jogar
                    vencedor_ia, log_ia = app.torneio_ativo.simular_jogo_ia_vs_ia(t1, t2)
                    app.torneio_ativo.registrar_vencedor(vencedor_ia)
                    log_widget.write(log_ia)
                    await asyncio.sleep(0.5)

            # Avança a fase do torneio (e paga os prémios em dinheiro se necessário)
            mensagem_fase = app.torneio_ativo.avancar_fase()
            log_widget.write(f"\n[bold green]{mensagem_fase}[/]")
            
            # Se o torneio acabou, notifica e limpa o estado
            if app.torneio_ativo.fase_atual == "Encerrado":
                app.notify(f"{app.torneio_ativo.campeao.nome} venceu o torneio!", title="Torneio Encerrado", timeout=6)
                app.torneio_ativo = None

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
        self.calendario = CalendarioGlobal() # <- Injetamos o Calendário aqui
        self.torneio_ativo = None

    def processar_compra(self, player_id: str) -> None:
        db = self.db
        id_seu_time = db.save_info["equipa_controlada_id"]
        seu_time = db.times.get(id_seu_time)
        jogador = db.jogadores.get(player_id)

        if not seu_time or not jogador:
            return

        # 1. Verificar se tem dinheiro suficiente
        if seu_time.saldo >= jogador.multa_rescisoria:
            # 2. Retirar o jogador da equipa antiga (se houver)
            if jogador.team_id in db.times:
                db.times[jogador.team_id].elenco.remove(jogador)

            # 3. Pagar a transferência e mudar de equipa
            seu_time.saldo -= jogador.multa_rescisoria
            jogador.team_id = id_seu_time
            seu_time.elenco.append(jogador)
            
            # 4. Ajustar contrato (Agente livre passa a ter salário mas perde multa imediata)
            jogador.multa_rescisoria = int(jogador.salario * 1.5) # Nova multa padrão

            self.notify(f"{jogador.nickname} contratado com sucesso!", title="Transferência Concluída")
            self.atualizar_dashboard() # Para atualizar o saldo visível
            self.db.salvar_jogo() # <--- SALVE AQUI
        else:
            self.notify("Saldo insuficiente para pagar a cláusula!", title="Erro", variant="error")
    
    # Atualize também o ClubTab para mostrar o saldo real
    def atualizar_dashboard(self) -> None:
        try:
            db = self.db
            id_seu_time = db.save_info["equipa_controlada_id"]
            seu_time = db.times.get(id_seu_time)
            
            # 1. Atualiza Finanças
            if seu_time:
                try:
                    self.query_one("#finances", Label).update(f"Saldo em Caixa: $ {seu_time.saldo:,}")
                except Exception:
                    pass

            # 2. Atualiza Calendário e Status
            dia_atual = db.save_info["dia_atual"]
            evento = self.calendario.obter_evento_do_dia(dia_atual)
            lbl_evento = self.query_one("#next_match", Label)
            if evento:
                lbl_evento.update(f"📅 Dia {dia_atual} | Evento Atual: {evento.nome} ({evento.tipo})")
            else:
                lbl_evento.update(f"📅 Dia {dia_atual} | Treino Regular na Base")
                
            # Calcula e atualiza a média de fadiga e moral da SUA equipa
            id_do_seu_time = self.db.save_info["equipa_controlada_id"]
            seu_time = self.db.times.get(id_do_seu_time)
            
            if seu_time and seu_time.elenco:
                media_fadiga = sum(p.fadiga for p in seu_time.elenco) / len(seu_time.elenco)
                media_moral = sum(p.moral for p in seu_time.elenco) / len(seu_time.elenco)
                
                lbl_status = self.query_one("#team_status", Label)
                lbl_status.update(f"📊 Estado da Equipa: Moral {media_moral:.1f} | Fadiga Média: {media_fadiga:.1f}%")
        except Exception:
            pass # Ignora se a interface ainda estiver a carregar

    def on_mount(self) -> None:
        nome_treinador = self.db.save_info.get("manager_nome", "Treinador")
        self.notify(f"Bem-vindo de volta, {nome_treinador}!", title="Save Carregado")
        self.atualizar_dashboard() # Pinta o ecrã com o dia correto ao abrir o jogo

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
        """Ação ativada ao apertar Espaço ou o botão de Avançar Dia."""
        db = self.db
        dia_atual = db.save_info["dia_atual"]
        db.salvar_jogo() # <--- SALVAR AQUI
        self.atualizar_dashboard()
        self.notify("Progresso guardado automaticamente.", title="Dia Encerrado")

        evento = self.calendario.obter_evento_do_dia(dia_atual)
        if evento and evento.tipo == "Campeonato" and self.torneio_ativo is None:
            self.torneio_ativo = self.calendario.inicializar_campeonato(evento.nome, db.times)
            self.notify(f"O {evento.nome} começou! Verifique a aba de jogos.", title="🏆 Torneio")

        self.calendario.processar_efeitos_do_dia(dia_atual, db.times)
        db.save_info["dia_atual"] += 1
        self.atualizar_dashboard()

        # 1. Aplica o RPG e Física (Cansaço, Treino de Bootcamp, Descanso)
        self.calendario.processar_efeitos_do_dia(dia_atual, db.times)
        
        # 2. O Tempo avança
        db.save_info["dia_atual"] += 1
        novo_dia = db.save_info["dia_atual"]
        
        # 3. Atualiza as Labels do Ecrã
        self.atualizar_dashboard()
        
        evento_novo = self.calendario.obter_evento_do_dia(novo_dia)
        nome_evento = evento_novo.nome if evento_novo else "Dia Normal"
        self.notify(f"A avançar para o Dia {novo_dia}...", title=nome_evento)

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