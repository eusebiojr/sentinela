"""
Header com layout organizado e logo Suzano - VERSÃO FINAL AJUSTADA
Substitui o arquivo app/ui/components/modern_header.py
"""
import flet as ft
from ...core.session_state import get_session_state
from ...utils.ui_utils import get_screen_size, mostrar_mensagem
from ...services.ticket_service import ticket_service
from ..components.ticket_modal import criar_modal_ticket
from ...config.logging_config import setup_logger
logger = setup_logger("tabela_justificativas")

try:
    from ...services.ticket_service import ticket_service
    TICKET_SERVICE_AVAILABLE = True
except ImportError:
    TICKET_SERVICE_AVAILABLE = False
    ticket_service = None

try:
    from ..components.ticket_modal import criar_modal_ticket
    TICKET_MODAL_AVAILABLE = True
except ImportError:
    TICKET_MODAL_AVAILABLE = False
    criar_modal_ticket = None

# Importa o serviço funcional de senha
try:
    from ...services.suzano_password_service import suzano_password_service
    PASSWORD_SERVICE_AVAILABLE = True
except ImportError:
    PASSWORD_SERVICE_AVAILABLE = False
    suzano_password_service = None

# Função auxiliar para salvar configurações
def salvar_configuracoes_usuario(page, config: dict):
    """Salva configurações do usuário"""
    try:
        session = get_session_state(page)
        for chave, valor in config.items():
            session.salvar_configuracao_usuario(chave, valor)
        print(f"Configurações salvas: {config}")
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        raise e


class ModernHeader:
    """Header com layout organizado e logo Suzano"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.menu_visible = False
        self.menu_container = None
        
    def criar_header(self):
        session = get_session_state(self.page)
        """Cria header com layout organizado e logo Suzano"""
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            logo_size = 32
            title_size = 18
            subtitle_size = 12
            avatar_size = 32
            padding_horizontal = 15
        elif screen_size == "medium":
            logo_size = 36
            title_size = 20
            subtitle_size = 14
            avatar_size = 36
            padding_horizontal = 20
        else:  # large
            logo_size = 40
            title_size = 22
            subtitle_size = 16
            avatar_size = 40
            padding_horizontal = 25

        nome_usuario = session.get_nome_usuario()
        perfil_usuario = session.get_perfil_usuario().title()
        iniciais = self._obter_iniciais(nome_usuario)

        # SEÇÃO ESQUERDA: Logo Suzano + Título
        secao_esquerda = ft.Row([
            # Logo Suzano
            ft.Image(
                src="/images/logo.png",
                width=logo_size,
                height=logo_size,
                fit=ft.ImageFit.CONTAIN
            ),
            ft.Column([
                ft.Text(
                    "Sentinela",
                    size=title_size,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Gestão de Desvios Logísticos",
                    size=subtitle_size,
                    color=ft.colors.with_opacity(0.9, ft.colors.WHITE),
                    italic=True
                )
            ], spacing=2)
        ], spacing=12)
        
        # SEÇÃO DIREITA: Botões + Usuário
        secao_direita = ft.Row([
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.icons.REFRESH, size=16, color=ft.colors.BLUE_600),
                    ft.Text("Atualizar", size=13, color=ft.colors.BLUE_600, weight=ft.FontWeight.W_500)
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                on_click=lambda e: self.app_controller.atualizar_dados(),
                bgcolor=ft.colors.WHITE,
                height=36,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8)
                ),
                tooltip="Atualizar dados do sistema"
            ),
            
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(
                            iniciais,
                            size=avatar_size * 0.4,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        ),
                        width=avatar_size,
                        height=avatar_size,
                        bgcolor=ft.colors.BLUE_800,
                        border_radius=avatar_size / 2,
                        alignment=ft.alignment.center,
                        border=ft.border.all(2, ft.colors.WHITE)
                    ),
                    ft.Column([
                        ft.Text(
                            nome_usuario,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=ft.colors.WHITE,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            perfil_usuario,
                            size=11,
                            color=ft.colors.with_opacity(0.8, ft.colors.WHITE)
                        )
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Icon(
                        ft.icons.KEYBOARD_ARROW_DOWN,
                        color=ft.colors.WHITE,
                        size=18
                    )
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=8,
                bgcolor=ft.colors.with_opacity(0.15, ft.colors.WHITE),
                border=ft.border.all(1, ft.colors.with_opacity(0.3, ft.colors.WHITE)),
                on_click=self._toggle_menu_usuario,
                ink=True,
                tooltip=f"Menu de {nome_usuario} - Clique para ver opções"
            )
        ], spacing=15)
        
        # HEADER PRINCIPAL
        header_content = ft.Row([
            secao_esquerda,
            secao_direita
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        header_principal = ft.Container(
            content=header_content,
            padding=ft.padding.symmetric(horizontal=padding_horizontal, vertical=12),
            bgcolor=ft.colors.BLUE_600,
            height=70,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
                offset=ft.Offset(0, 3)
            )
        )
        
        # MENU DROPDOWN
        self.menu_container = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                self._criar_menu_dropdown(),
                ft.Container(width=padding_horizontal + 10)
            ]),
            height=0,
            animate_size=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=ft.colors.TRANSPARENT,
            padding=ft.padding.only(top=5)
        )
        
        return ft.Column([
            header_principal,
            self.menu_container
        ], spacing=0)
    
    def _criar_menu_dropdown(self):
        """Menu dropdown CORRIGIDO com logoff visível"""
        opcoes = [
            {
                "icon": ft.icons.PERSON,
                "text": "Meu Perfil",
                "action": self._ver_perfil,
                "color": ft.colors.BLUE_600
            },
            {
                "icon": ft.icons.SUPPORT_AGENT,
                "text": "Abrir Chamado",
                "action": self._abrir_chamado,
                "color": ft.colors.GREEN_600
            },
            {
                "icon": ft.icons.LOCK_RESET,
                "text": "Trocar Senha",
                "action": self._trocar_senha,
                "color": ft.colors.ORANGE_600
            },
            {
                "icon": ft.icons.SETTINGS,
                "text": "Configurações",
                "action": self._configuracoes,
                "color": ft.colors.GREY_600
            },
            # ===== SEPARADOR VISUAL =====
            None,  # Separador
            # ===== LOGOFF DESTACADO =====
            {
                "icon": ft.icons.LOGOUT,
                "text": "Sair do Sistema",
                "action": self._sair_sistema,
                "color": ft.colors.RED_600,
                "destaque": True  # Marca como destacado
            }
        ]
        
        menu_items = []
        
        for opcao in opcoes:
            # Separador visual
            if opcao is None:
                separador = ft.Container(
                    height=1,
                    bgcolor=ft.colors.GREY_300,
                    margin=ft.margin.symmetric(horizontal=10, vertical=8)
                )
                menu_items.append(separador)
                continue
            
            # Estilo especial para logoff
            if opcao.get("destaque", False):
                item_container = ft.Container(
                    content=ft.Row([
                        ft.Icon(opcao["icon"], color=ft.colors.WHITE, size=18),
                        ft.Text(
                            opcao["text"],
                            color=ft.colors.WHITE,
                            weight=ft.FontWeight.W_600,
                            size=14
                        )
                    ], spacing=12),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    on_click=lambda e, action=opcao["action"]: self._executar_acao_menu(action),
                    border_radius=8,
                    bgcolor=ft.colors.RED_600,
                    margin=ft.margin.symmetric(horizontal=5, vertical=2),
                    ink=True,
                    border=ft.border.all(1, ft.colors.RED_700)
                )
            else:
                # Estilo normal
                item_container = ft.Container(
                    content=ft.Row([
                        ft.Icon(opcao["icon"], color=opcao["color"], size=18),
                        ft.Text(
                            opcao["text"],
                            color=ft.colors.GREY_800,
                            weight=ft.FontWeight.W_500,
                            size=14
                        )
                    ], spacing=12),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    on_click=lambda e, action=opcao["action"]: self._executar_acao_menu(action),
                    border_radius=6,
                    ink=True
                )
            
            # Efeito hover
            def create_hover(container, is_logout=False):
                def on_hover(e):
                    if e.data == "true":
                        if is_logout:
                            container.bgcolor = ft.colors.RED_700
                        else:
                            container.bgcolor = ft.colors.GREY_100
                    else:
                        if is_logout:
                            container.bgcolor = ft.colors.RED_600
                        else:
                            container.bgcolor = None
                    container.update()
                return on_hover
            
            item_container.on_hover = create_hover(item_container, opcao.get("destaque", False))
            menu_items.append(item_container)
        
        return ft.Container(
            content=ft.Column(menu_items, spacing=0),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, ft.colors.GREY_400)),
            padding=ft.padding.all(8),
            width=240,
            margin=ft.margin.only(right=5)
        )
    
    def _toggle_menu_usuario(self, e):
        """Toggle menu CORRIGIDO com debug"""
        try:
            print(f"🔄 Toggle menu - Estado atual: {self.menu_visible}")
            
            self.menu_visible = not self.menu_visible
            
            if self.menu_visible:
                print("📖 Abrindo menu...")
                self.menu_container.height = 280  # Aumentado para acomodar mais itens
                self.menu_container.visible = True
            else:
                print("📕 Fechando menu...")
                self.menu_container.height = 0
                self.menu_container.visible = False
            
            self.page.update()
            print(f"✅ Menu atualizado - Novo estado: {self.menu_visible}")
            
        except Exception as ex:
            print(f"❌ Erro no toggle do menu: {str(ex)}")
            # Reset forçado
            self.menu_visible = False
            if self.menu_container:
                self.menu_container.height = 0
                self.menu_container.visible = False
                self.page.update()

    def _executar_acao_menu(self, action):
        """Executa ação e fecha menu COM DEBUG"""
        try:
            print(f"🎯 Executando ação do menu...")
            self._fechar_menu()
            print(f"🚀 Chamando ação...")
            action()
            print(f"✅ Ação executada com sucesso")
        except Exception as ex:
            print(f"❌ Erro ao executar ação do menu: {str(ex)}")
            # Garante que o menu seja fechado
            self._fechar_menu()
    
    def _fechar_menu(self):
        """Fecha menu com debug"""
        try:
            print(f"🔒 Fechando menu...")
            self.menu_visible = False
            if self.menu_container:
                self.menu_container.height = 0
                self.menu_container.visible = False
                self.page.update()
            print(f"✅ Menu fechado")
        except Exception as ex:
            print(f"❌ Erro ao fechar menu: {str(ex)}")
    
    def _obter_iniciais(self, nome: str) -> str:
        """Obtém iniciais do usuário"""
        if not nome:
            return "U"
        palavras = nome.strip().split()
        if len(palavras) == 1:
            return palavras[0][:2].upper()
        else:
            return (palavras[0][0] + palavras[-1][0]).upper()
    
    def _ver_perfil(self):
        session = get_session_state(self.page)
        """Mostra perfil do usuário"""
        try:
            nome = session.get_nome_usuario()
            perfil = session.get_perfil_usuario().title()
            areas = session.get_areas_usuario()
            
            usuario = session.get_usuario_atual()
            email = usuario.get('Email', 'Não informado') if usuario else 'Não informado'
            ultimo_acesso = usuario.get('ultimo_acesso', 'Não informado') if usuario else 'Não informado'
            
            modal = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.icons.PERSON, color=ft.colors.BLUE_600, size=24),
                    ft.Text("Meu Perfil", weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"👤 Nome: {nome}", size=14),
                        ft.Text(f"📧 Email: {email}", size=14),
                        ft.Text(f"🎯 Perfil: {perfil}", size=14),
                        ft.Text(f"📍 Áreas: {', '.join(areas) if areas else 'Não especificado'}", size=14),
                        ft.Text(f"🕒 Último acesso: {ultimo_acesso}", size=14),
                    ], spacing=10),
                    width=350,
                    height=150,
                    padding=15
                ),
                actions=[ft.TextButton("Fechar", on_click=lambda e: self._fechar_modal(modal))]
            )
            
            self.page.dialog = modal
            modal.open = True
            self.page.update()
            
        except Exception as e:
            mostrar_mensagem(self.page, f"❌ Erro ao carregar perfil: {str(e)}", "error")
    
    def _trocar_senha(self):
        """Modal para trocar senha com caixa ajustada"""
        
        # Verifica se o serviço está disponível
        if not PASSWORD_SERVICE_AVAILABLE:
            mostrar_mensagem(self.page, "❌ Serviço de senha temporariamente indisponível", "error")
            return
        
        # Campos do modal
        senha_atual_field = ft.TextField(
            label="Senha Atual",
            password=True,
            can_reveal_password=True,
            width=320,
            autofocus=True,
            border_radius=8,
            helper_text="Informe sua senha atual"
        )
        
        nova_senha_field = ft.TextField(
            label="Nova Senha",
            password=True,
            can_reveal_password=True,
            width=320,
            border_radius=8,
            helper_text="Mínimo 6 caracteres"
        )
        
        confirmar_senha_field = ft.TextField(
            label="Confirmar Nova Senha",
            password=True,
            can_reveal_password=True,
            width=320,
            border_radius=8,
            helper_text="Digite novamente a nova senha"
        )
        
        # Indicadores visuais
        error_text = ft.Text("", color=ft.colors.RED, size=12, visible=False)
        loading_indicator = ft.ProgressRing(width=20, height=20, visible=False)
        
        # Status do botão
        btn_confirmar = ft.ElevatedButton(
            "Confirmar Alteração",
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            icon=ft.icons.CHECK_CIRCLE,
            disabled=False
        )
        
        def mostrar_loading(ativo: bool):
            """Controla estado de loading"""
            loading_indicator.visible = ativo
            btn_confirmar.disabled = ativo
            senha_atual_field.disabled = ativo
            nova_senha_field.disabled = ativo
            confirmar_senha_field.disabled = ativo
            
            if ativo:
                btn_confirmar.text = "Processando..."
                btn_confirmar.icon = None
            else:
                btn_confirmar.text = "Confirmar Alteração"
                btn_confirmar.icon = ft.icons.CHECK_CIRCLE
            
            self.page.update()
        
        def mostrar_erro(mensagem: str):
            """Mostra mensagem de erro no modal"""
            error_text.value = f"⚠️ {mensagem}"
            error_text.visible = True
            self.page.update()
        
        def limpar_erro():
            """Limpa mensagem de erro"""
            error_text.visible = False
            self.page.update()
        
        def confirmar_troca(e):
            """Processa a troca de senha"""
            # Reset do estado
            limpar_erro()
            
            # Validações básicas
            if not senha_atual_field.value:
                mostrar_erro("Informe a senha atual")
                return
            
            if not nova_senha_field.value:
                mostrar_erro("Informe a nova senha")
                return
            
            if nova_senha_field.value != confirmar_senha_field.value:
                mostrar_erro("As senhas não conferem")
                return
            
            if len(nova_senha_field.value) < 6:
                mostrar_erro("A nova senha deve ter pelo menos 6 caracteres")
                return
            
            # Ativa loading
            mostrar_loading(True)
            
            # Processa em background para não travar a UI
            import threading
            
            def processar_troca():
                session = get_session_state(self.page)
                try:
                    # Obtém email do usuário logado
                    usuario_atual = session.get_usuario_atual()
                    email_usuario = usuario_atual.get('Email', '') if usuario_atual else ''
                    
                    if not email_usuario:
                        # Busca email em outras possíveis chaves
                        for key in ['email', 'Email', 'EMAIL']:
                            if key in usuario_atual:
                                email_usuario = usuario_atual[key]
                                break
                    
                    if not email_usuario:
                        raise Exception("Email do usuário não encontrado no sistema")
                    
                    # Chama o serviço de troca de senha
                    resultado = suzano_password_service.alterar_senha(
                        email=email_usuario,
                        senha_atual=senha_atual_field.value,
                        nova_senha=nova_senha_field.value
                    )
                    
                    # Desativa loading
                    mostrar_loading(False)
                    
                    if resultado['sucesso']:
                        # Sucesso - fecha modal e mostra mensagem
                        modal_senha.open = False
                        self.page.update()
                        
                        mostrar_mensagem(
                            self.page, 
                            "🔐 Senha alterada com sucesso! Sua nova senha já está ativa.", 
                            "success"
                        )
                        
                    else:
                        # Erro do serviço
                        mostrar_erro(resultado.get('erro', 'Erro desconhecido'))
                
                except Exception as ex:
                    # Desativa loading em caso de erro
                    mostrar_loading(False)
                    
                    # Trata erros específicos
                    erro_msg = str(ex)
                    if "não encontrado" in erro_msg.lower():
                        mostrar_erro("Usuário não encontrado no sistema")
                    elif "senha atual incorreta" in erro_msg.lower():
                        mostrar_erro("Senha atual incorreta")
                    elif "conexão" in erro_msg.lower():
                        mostrar_erro("Erro de conexão com o servidor")
                    else:
                        mostrar_erro(f"Erro: {erro_msg}")
            
            # Executa em thread separada
            thread = threading.Thread(target=processar_troca, daemon=True)
            thread.start()
        
        def cancelar(e):
            """Cancela e fecha o modal"""
            modal_senha.open = False
            self.page.update()
        
        # Validação em tempo real para confirmação de senha
        def validar_confirmacao(e):
            """Valida confirmação de senha em tempo real"""
            if confirmar_senha_field.value and nova_senha_field.value:
                if nova_senha_field.value != confirmar_senha_field.value:
                    confirmar_senha_field.border_color = ft.colors.RED_400
                    confirmar_senha_field.helper_text = "Senhas não conferem"
                else:
                    confirmar_senha_field.border_color = ft.colors.GREEN_400
                    confirmar_senha_field.helper_text = "Senhas conferem ✓"
            else:
                confirmar_senha_field.border_color = None
                confirmar_senha_field.helper_text = "Digite novamente a nova senha"
            self.page.update()
        
        # Conecta validação
        confirmar_senha_field.on_change = validar_confirmacao
        nova_senha_field.on_change = validar_confirmacao
        
        # Conecta ação do botão
        btn_confirmar.on_click = confirmar_troca
        
        # Modal principal - CAIXA AUMENTADA
        modal_senha = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.LOCK_RESET, color=ft.colors.GREEN_600, size=28),
                ft.Text("Alterar Senha", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.SECURITY, color=ft.colors.GREEN_600, size=20),
                            ft.Text(
                                "🔐 Altere sua senha de acesso ao sistema:",
                                size=14,
                                color=ft.colors.GREY_700,
                                weight=ft.FontWeight.W_500
                            )
                        ], spacing=8),
                        padding=ft.padding.only(bottom=15)
                    ),
                    senha_atual_field,
                    ft.Container(height=12),
                    nova_senha_field,
                    ft.Container(height=12),
                    confirmar_senha_field,
                    ft.Container(height=10),
                    
                    # Dicas de segurança - MOVIDAS PARA CIMA
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.GREEN_600, size=16),
                                ft.Text("Dicas de Segurança:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600)
                            ], spacing=5),
                            ft.Text("• Use uma senha forte e única", size=11, color=ft.colors.GREY_600),
                            ft.Text("• Não compartilhe sua senha com ninguém", size=11, color=ft.colors.GREY_600),
                            ft.Text("• A alteração é imediata no sistema", size=11, color=ft.colors.GREY_600)
                        ], spacing=3),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.GREEN_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.colors.GREEN_200)
                    ),
                    
                    ft.Container(height=15),
                    ft.Row([
                        loading_indicator,
                        error_text
                    ], spacing=10)
                ], tight=True),
                width=400,  # AUMENTADO de 370 para 400
                height=500, # AUMENTADO de 420 para 500
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                btn_confirmar
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self.page.dialog = modal_senha
        modal_senha.open = True
        self.page.update()
    
    def _configuracoes(self):
        """Modal de configurações com auto-refresh DESABILITADO por padrão"""
        session = get_session_state(self.page)
        
        # Carregar configurações existentes
        usuario = session.get_usuario_atual()
        config_atual = usuario.get('configuracoes', {}) if usuario else {}
        
        tema_claro = ft.Switch(
            label="Tema Claro", 
            value=config_atual.get('tema_claro', True)
        )
        notificacoes = ft.Switch(
            label="Notificações", 
            value=config_atual.get('notificacoes', True)
        )
        
        # ===== CORREÇÃO CRÍTICA: AUTO-REFRESH DESABILITADO POR PADRÃO =====
        auto_refresh = ft.Switch(
            label="Atualização Automática (10 min)", 
            value=config_atual.get('auto_refresh', False)  # ⚡ PADRÃO: FALSE
        )
        
        # ===== NOVO: AVISO SOBRE AUTO-REFRESH =====
        aviso_auto_refresh = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.WARNING_ROUNDED, size=16, color=ft.colors.ORANGE_600),
                ft.Text(
                    "Desative se estiver preenchendo dados para evitar perda de informações",
                    size=11,
                    color=ft.colors.ORANGE_700,
                    weight=ft.FontWeight.W_400,
                    expand=True
                )
            ], spacing=6),
            padding=ft.padding.only(left=32, top=5),
            visible=auto_refresh.value  # Só mostra se auto-refresh estiver ativado
        )
        
        def on_auto_refresh_change(e):
            """Atualiza visibilidade do aviso quando auto-refresh muda"""
            aviso_auto_refresh.visible = auto_refresh.value
            self.page.update()
        
        auto_refresh.on_change = on_auto_refresh_change
        
        def salvar_config(e):
            try:
                config = {
                    "tema_claro": tema_claro.value,
                    "notificacoes": notificacoes.value,
                    "auto_refresh": auto_refresh.value
                }
                
                # ===== NOVO: APLICA IMEDIATAMENTE A CONFIGURAÇÃO DE AUTO-REFRESH =====
                from ...services.auto_refresh_service import obter_auto_refresh_service
                auto_refresh_service = obter_auto_refresh_service()
                
                if auto_refresh_service:
                    auto_refresh_service.habilitar_usuario(auto_refresh.value)
                    
                    if auto_refresh.value:
                        logger.info("🔄 Auto-refresh HABILITADO pelo usuário via configurações")
                    else:
                        logger.info("🔕 Auto-refresh DESABILITADO pelo usuário via configurações")
                
                # Salva configurações do usuário
                salvar_configuracoes_usuario(self.page, config)
                
                modal_config.open = False
                self.page.update()
                
                # Mensagem de confirmação específica
                if auto_refresh.value:
                    mostrar_mensagem(self.page, "⚙️ Configurações salvas! Auto-refresh ativado (10 min)", "success")
                else:
                    mostrar_mensagem(self.page, "⚙️ Configurações salvas! Auto-refresh desabilitado", "success")
                
            except Exception as ex:
                logger.error(f"❌ Erro ao salvar configurações: {ex}")
                mostrar_mensagem(self.page, f"❌ Erro ao salvar: {str(ex)}", "error")
        
        def cancelar(e):
            modal_config.open = False
            self.page.update()
        
        btn_confirmar = ft.ElevatedButton(
            "Salvar",
            on_click=salvar_config,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            width=120
        )
        
        # ===== MODAL ATUALIZADO COM AVISOS =====
        modal_config = ft.AlertDialog(
            title=ft.Text("⚙️ Configurações", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    # Configurações existentes
                    tema_claro,
                    ft.Container(height=10),
                    notificacoes,
                    ft.Container(height=10),
                    
                    # Auto-refresh com aviso
                    auto_refresh,
                    aviso_auto_refresh,
                    
                    ft.Container(height=15),
                    
                    # ===== NOVO: INFORMAÇÕES SOBRE AUTO-REFRESH =====
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "ℹ️ Sobre a Atualização Automática:",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE_700
                            ),
                            ft.Text(
                                "• Atualiza dados do sistema a cada 10 minutos",
                                size=11,
                                color=ft.colors.GREY_700
                            ),
                            ft.Text(
                                "• PAUSA automaticamente ao digitar em campos",
                                size=11,
                                color=ft.colors.GREEN_700,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Text(
                                "• Você pode atualizar manualmente pelo botão ↻",
                                size=11,
                                color=ft.colors.GREY_700
                            ),
                            ft.Text(
                                "• Recomendado: manter DESABILITADO durante preenchimento",
                                size=11,
                                color=ft.colors.ORANGE_700,
                                weight=ft.FontWeight.W_500
                            ),
                        ], spacing=3),
                        padding=ft.padding.all(10),
                        border_radius=6,
                        bgcolor=ft.colors.with_opacity(0.05, ft.colors.BLUE_600),
                        border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.BLUE_600))
                    )
                ], spacing=5),
                width=420,  # Aumentado para acomodar texto
                height=450  # Aumentado para acomodar avisos
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                btn_confirmar
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self.page.dialog = modal_config
        modal_config.open = True
        self.page.update()
    
    def _sair_sistema(self):
        session = get_session_state(self.page)
        """Confirma logout com modal corrigido - ESPAÇAMENTO MELHORADO"""
        nome = session.get_nome_usuario()
        
        def confirmar_logout(e):
            try:                
                # 1. Fecha modal IMEDIATAMENTE
                modal.open = False
                self.page.update()
                
                # 2. Limpa dados ANTES de mostrar tela
                session.reset_dados()
                
                # 3. Limpa cache do SharePoint se existir
                try:
                    # Se SharePointClient tem algum cache global, limpa aqui
                    pass
                except:
                    pass
                
                # 4. Pequena pausa para garantir limpeza
                import time
                time.sleep(0.2)
                
                # 5. Força recarregamento dos dados                
                if hasattr(self.app_controller, 'login_screen') and self.app_controller.login_screen:
                    # Força recarregamento dos dados
                    self.app_controller._carregar_dados_iniciais()
                else:
                    # Fallback
                    self.page.clean()
                    self.page.add(ft.Text("Logout realizado. Recarregue a página."))
                    self.page.update()
                        
            except Exception as ex:
                # Força fechamento do modal em caso de erro
                try:
                    modal.open = False
                    self.page.update()
                except:
                    pass
        
        # Modal de logout - LAYOUT COM ESPAÇAMENTO CORRIGIDO
        modal = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.LOGOUT, color=ft.colors.RED_600, size=24),
                ft.Text("Confirmar Saída", weight=ft.FontWeight.BOLD)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Olá, {nome}!", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_700),
                    ft.Container(height=8),
                    ft.Text("Tem certeza que deseja sair do sistema?", size=14),
                    ft.Container(height=20),  # AUMENTADO de 15 para 20
                    # MOVIDO PARA CIMA com mais espaço - aviso antes dos botões
                    ft.Container(
                        content=ft.Text("⚠️ Você precisará fazer login novamente", size=12, color=ft.colors.ORANGE_600),
                        padding=ft.padding.all(8),
                        bgcolor=ft.colors.ORANGE_50,
                        border_radius=6
                    ),
                    ft.Container(height=15)  # NOVO: Espaço extra após o aviso
                ]),
                width=300,
                height=150,  # AUMENTADO de 130 para 150 para acomodar o espaço extra
                padding=15
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._fechar_modal(modal)),
                ft.ElevatedButton("Sim, Sair", on_click=confirmar_logout, bgcolor=ft.colors.RED_600, color=ft.colors.WHITE)
            ]
        )
        
        self.page.dialog = modal
        modal.open = True
        self.page.update()

    def _abrir_chamado(self):
        """Abre modal de chamado de suporte"""
        try:
            # Obtém email do usuário logado
            session = get_session_state(self.page)
            email_usuario = session.usuario.get('Email', '') if session.usuario else ''
            
            # Cria modal de ticket com usuário pré-preenchido
            modal_ticket = criar_modal_ticket(
                self.page, 
                callback_sucesso=self._ticket_criado_sucesso
            )
            
            # Mostra o modal com email pré-preenchido
            modal_ticket.mostrar_modal(usuario_logado=email_usuario)
            
        except Exception as ex:
            print(f"❌ Erro ao abrir chamado: {str(ex)}")
            mostrar_mensagem(self.page, "Erro ao abrir formulário de chamado", True)

    def _ticket_criado_sucesso(self, ticket_id: int, dados_ticket: dict):
        """Callback executado quando ticket é criado com sucesso"""
        try:
            print(f"✅ Ticket {ticket_id} criado no sistema logado")
            print(f"📧 Usuário: {dados_ticket.get('usuario')}")
            print(f"🎯 Motivo: {dados_ticket.get('motivo')}")
            
            # Aqui você pode adicionar lógica adicional
            # Por exemplo, atualizar contadores, enviar notificação, etc.
            
        except Exception as ex:
            print(f"❌ Erro no callback de sucesso: {str(ex)}")

    def _fechar_menu(self):
        """Fecha o menu suspenso"""
        try:
            if self.menu_container:
                self.menu_container.visible = False
                self.menu_visible = False
                self.page.update()
        except Exception as ex:
            print(f"❌ Erro ao fechar menu: {str(ex)}")

    def _fechar_modal(self, modal):
        """Fecha modal"""
        modal.open = False
        self.page.update()




# Funções auxiliares para compatibilidade
def get_password_service_status():
    """Retorna status do serviço de senha"""
    return {
        'disponivel': PASSWORD_SERVICE_AVAILABLE,
        'funcional': PASSWORD_SERVICE_AVAILABLE and suzano_password_service is not None
    }


def testar_servico_senha():
    """Testa o serviço de senha"""
    if not PASSWORD_SERVICE_AVAILABLE:
        return {
            'connected': False,
            'message': 'Serviço não disponível',
            'details': 'Biblioteca ou configuração ausente'
        }
    
    try:
        connected = suzano_password_service.testar_conexao()
        return {
            'connected': connected,
            'message': 'Conectado com sucesso' if connected else 'Falha na conexão',
            'details': 'SharePoint acessível' if connected else 'Verificar credenciais e rede'
        }
    except Exception as e:
        return {
            'connected': False,
            'message': 'Erro no teste de conexão',
            'details': str(e)
        }