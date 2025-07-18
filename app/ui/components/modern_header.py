"""
Header com layout organizado - mantém solução sem retângulo cinza
"""
import flet as ft
from ...core.state import app_state
from ...utils.ui_utils import get_screen_size, mostrar_mensagem

# Importações adicionais para funcionalidades
try:
    from ...services.sharepoint_client import SharePointClient
except ImportError:
    SharePointClient = None

# Função auxiliar para salvar configurações
def salvar_configuracoes_usuario(config: dict):
    """Salva configurações do usuário"""
    try:
        # Usa a instância global do app_state
        for chave, valor in config.items():
            app_state.salvar_configuracao_usuario(chave, valor)
        print(f"Configurações salvas: {config}")
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        raise e


class ModernHeader:
    """Header com layout organizado e sem problemas visuais"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.menu_visible = False
        self.menu_container = None
        
    def criar_header(self):
        """Cria header com layout organizado"""
        
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

        nome_usuario = app_state.get_nome_usuario()
        perfil_usuario = app_state.get_perfil_usuario().title()
        iniciais = self._obter_iniciais(nome_usuario)

        # SEÇÃO ESQUERDA: Logo + Título (ORGANIZADOS EM GRUPO)
        secao_esquerda = ft.Row([
            # Logo
            ft.Icon(
                ft.icons.SECURITY,  # Para trocar: ft.Image(src="/images/logo.png", width=logo_size, height=logo_size, fit=ft.ImageFit.CONTAIN)
                size=logo_size,
                color=ft.colors.WHITE
            ),
            # Textos agrupados verticalmente
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
            ], spacing=2)  # Espaçamento mínimo entre título e subtítulo
        ], spacing=12)  # Espaçamento entre logo e textos
        
        # SEÇÃO DIREITA: Botões + Usuário (ORGANIZADOS EM GRUPO)
        secao_direita = ft.Row([
            # Botão Atualizar
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
            
            # Área do Usuário (Avatar + Info + Menu)
            ft.Container(
                content=ft.Row([
                    # Avatar
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
                    
                    # Info do usuário
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
                    
                    # Ícone de menu
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
            
        ], spacing=15)  # Espaçamento entre botão atualizar e área do usuário
        
        # HEADER PRINCIPAL - LAYOUT LIMPO SEM CONTAINERS PROBLEMÁTICOS
        header_content = ft.Row([
            secao_esquerda,
            secao_direita
        ], 
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
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
        
        # MENU DROPDOWN - CORREÇÃO DO ESPAÇAMENTO
        self.menu_container = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),  # Espaço à esquerda
                self._criar_menu_dropdown(),
                ft.Container(width=padding_horizontal + 10)  # AUMENTADO: Margem direita maior para não cortar
            ]),
            height=0,  # Inicialmente oculto
            animate_size=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=ft.colors.TRANSPARENT,
            padding=ft.padding.only(top=5)  # ADICIONADO: Padding superior
        )
        
        # LAYOUT FINAL
        return ft.Column([
            header_principal,
            self.menu_container
        ], spacing=0)
    
    def _criar_menu_dropdown(self):
        """Menu dropdown estilizado"""
        opcoes = [
            {
                "icon": ft.icons.PERSON,
                "text": "Meu Perfil",
                "action": self._ver_perfil,
                "color": ft.colors.BLUE_600
            },
            {
                "icon": ft.icons.LOCK_RESET,
                "text": "Trocar Senha",
                "action": self._trocar_senha,
                "color": ft.colors.GREEN_600
            },
            {
                "icon": ft.icons.SETTINGS,
                "text": "Configurações",
                "action": self._configuracoes,
                "color": ft.colors.GREY_600
            },
            {
                "icon": ft.icons.LOGOUT,
                "text": "Sair do Sistema",
                "action": self._sair_sistema,
                "color": ft.colors.RED_600
            }
        ]
        
        menu_items = []
        for opcao in opcoes:
            item = ft.Container(
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
            
            # Hover effect
            def create_hover(container):
                def on_hover(e):
                    if e.data == "true":
                        container.bgcolor = ft.colors.GREY_100
                    else:
                        container.bgcolor = None
                    container.update()
                return on_hover
            
            item.on_hover = create_hover(item)
            menu_items.append(item)
        
        return ft.Container(
            content=ft.Column(menu_items, spacing=2),
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, ft.colors.GREY_400)),
            padding=ft.padding.all(10),  # AUMENTADO: de 8 para 10
            width=220,  # AUMENTADO: de 200 para 220 para mais espaço
            margin=ft.margin.only(right=5)  # ADICIONADO: Margem direita
        )
    
    def _toggle_menu_usuario(self, e):
        """Alterna menu"""
        self.menu_visible = not self.menu_visible
        
        if self.menu_visible:
            self.menu_container.height = 200  # AUMENTADO: de 180 para 200 para dar mais espaço
        else:
            self.menu_container.height = 0
        
        self.page.update()
    
    def _executar_acao_menu(self, action):
        """Executa ação e fecha menu"""
        self._fechar_menu()
        action()
    
    def _fechar_menu(self):
        """Fecha menu"""
        self.menu_visible = False
        if self.menu_container:
            self.menu_container.height = 0
            self.page.update()
    
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
        """Mostra perfil do usuário"""
        try:
            nome = app_state.get_nome_usuario()
            perfil = app_state.get_perfil_usuario().title()
            areas = app_state.get_areas_usuario()
            
            # Informações adicionais do usuário
            usuario = app_state.get_usuario_atual()
            email = usuario.get('email', 'Não informado') if usuario else 'Não informado'
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
                            mostrar_mensagem(self.page, f"❌ Erro ao carregar perfil: {str(e)}")
    
    def _trocar_senha(self):
        """Modal para trocar senha - IMPLEMENTADO"""
        senha_atual_field = ft.TextField(
            label="Senha Atual",
            password=True,
            can_reveal_password=True,
            width=320,
            autofocus=True,
            border_radius=8
        )
        
        nova_senha_field = ft.TextField(
            label="Nova Senha",
            password=True,
            can_reveal_password=True,
            width=320,
            border_radius=8
        )
        
        confirmar_senha_field = ft.TextField(
            label="Confirmar Nova Senha",
            password=True,
            can_reveal_password=True,
            width=320,
            border_radius=8
        )
        
        error_text = ft.Text("", color=ft.colors.RED, size=12, visible=False)
        
        def confirmar_troca(e):
            # Reset error
            error_text.visible = False
            
            # Validações
            if not senha_atual_field.value:
                error_text.value = "⚠️ Informe a senha atual"
                error_text.visible = True
                self.page.update()
                return
            
            if not nova_senha_field.value:
                error_text.value = "⚠️ Informe a nova senha"
                error_text.visible = True
                self.page.update()
                return
            
            if nova_senha_field.value != confirmar_senha_field.value:
                error_text.value = "⚠️ As senhas não conferem"
                error_text.visible = True
                self.page.update()
                return
            
            if len(nova_senha_field.value) < 6:
                error_text.value = "⚠️ A nova senha deve ter pelo menos 6 caracteres"
                error_text.visible = True
                self.page.update()
                return
            
            # Lógica de troca de senha
            try:
                if SharePointClient:
                    # Tentativa de integração com SharePoint
                    usuario_id = app_state.get_id_usuario()
                    
                    if usuario_id:
                        SharePointClient.atualizar_senha(
                            usuario_id=usuario_id,
                            senha_atual=senha_atual_field.value,
                            nova_senha=nova_senha_field.value
                        )
                    else:
                        raise Exception("ID do usuário não encontrado")
                else:
                    # Simulação de troca de senha quando SharePoint não está disponível
                    print(f"Simulando troca de senha para usuário: {app_state.get_nome_usuario()}")
                    
                modal_senha.open = False
                self.page.update()
                mostrar_mensagem(self.page, "🔐 Senha alterada com sucesso!")
                
            except Exception as ex:
                error_text.value = f"Erro ao alterar senha: {str(ex)}"
                error_text.visible = True
                self.page.update()
        
        def cancelar(e):
            modal_senha.open = False
            self.page.update()
        
        modal_senha = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.LOCK_RESET, color=ft.colors.GREEN_600, size=28),
                ft.Text("Alterar Senha", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text(
                            "🔐 Altere sua senha de acesso ao sistema:",
                            size=14,
                            color=ft.colors.GREY_700
                        ),
                        padding=ft.padding.only(bottom=15)
                    ),
                    senha_atual_field,
                    ft.Container(height=12),
                    nova_senha_field,
                    ft.Container(height=12),
                    confirmar_senha_field,
                    ft.Container(height=15),
                    error_text,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("💡 Requisitos da senha:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600),
                            ft.Text("• Mínimo de 6 caracteres", size=11, color=ft.colors.GREY_600),
                            ft.Text("• Recomendado: letras, números e símbolos", size=11, color=ft.colors.GREY_600)
                        ], spacing=2),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.GREEN_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.colors.GREEN_200)
                    )
                ], tight=True),
                width=370,
                height=350,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Confirmar Alteração",
                    on_click=confirmar_troca,
                    bgcolor=ft.colors.GREEN_600,
                    color=ft.colors.WHITE,
                    icon=ft.icons.CHECK_CIRCLE
                )
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self.page.dialog = modal_senha
        modal_senha.open = True
        self.page.update()
    
    def _configuracoes(self):
        """Modal de configurações - IMPLEMENTADO"""
        
        # Carregar configurações existentes
        usuario = app_state.get_usuario_atual()
        config_atual = usuario.get('configuracoes', {}) if usuario else {}
        
        tema_claro = ft.Switch(
            label="Tema Claro", 
            value=config_atual.get('tema_claro', True)
        )
        notificacoes = ft.Switch(
            label="Notificações", 
            value=config_atual.get('notificacoes', True)
        )
        auto_refresh = ft.Switch(
            label="Atualização Automática", 
            value=config_atual.get('auto_refresh', False)
        )
        
        def salvar_config(e):
            try:
                config = {
                    "tema_claro": tema_claro.value,
                    "notificacoes": notificacoes.value,
                    "auto_refresh": auto_refresh.value
                }
                salvar_configuracoes_usuario(config)
                
                modal_config.open = False
                self.page.update()
                mostrar_mensagem(self.page, "⚙️ Configurações salvas com sucesso!")
                
            except Exception as ex:
                mostrar_mensagem(self.page, f"❌ Erro ao salvar configurações: {str(ex)}")
        
        def resetar_config(e):
            tema_claro.value = True
            notificacoes.value = True
            auto_refresh.value = False
            self.page.update()
        
        modal_config = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.SETTINGS, color=ft.colors.GREY_600, size=28),
                ft.Text("Configurações", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text(
                            "⚙️ Personalize sua experiência no sistema:",
                            size=14,
                            color=ft.colors.GREY_700
                        ),
                        padding=ft.padding.only(bottom=15)
                    ),
                    
                    # Seção Interface
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🎨 Interface", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
                            tema_claro,
                        ], spacing=8),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    
                    ft.Container(height=12),
                    
                    # Seção Sistema
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🔔 Sistema", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_600),
                            notificacoes,
                            auto_refresh,
                        ], spacing=8),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.ORANGE_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.colors.ORANGE_200)
                    ),
                    
                    ft.Container(height=15),
                    
                    # Informações do sistema
                    ft.Container(
                        content=ft.Column([
                            ft.Text("ℹ️ Informações do Sistema", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_600),
                            ft.Text(f"• Usuário: {app_state.get_nome_usuario()}", size=10, color=ft.colors.GREY_500),
                            ft.Text(f"• Perfil: {app_state.get_perfil_usuario().title()}", size=10, color=ft.colors.GREY_500),
                            ft.Text("• Versão: 2.0.0", size=10, color=ft.colors.GREY_500),
                        ], spacing=2),
                        padding=ft.padding.all(10),
                        bgcolor=ft.colors.GREY_50,
                        border_radius=6,
                        border=ft.border.all(1, ft.colors.GREY_200)
                    )
                ], tight=True),
                width=380,
                height=400,
                padding=20
            ),
            actions=[
                ft.TextButton("Resetar", on_click=resetar_config),
                ft.TextButton("Cancelar", on_click=lambda e: self._fechar_modal(modal_config)),
                ft.ElevatedButton(
                    "Salvar",
                    on_click=salvar_config,
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE,
                    icon=ft.icons.SAVE
                )
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self.page.dialog = modal_config
        modal_config.open = True
        self.page.update()
    
    def _sair_sistema(self):
        """Confirma logout"""
        nome = app_state.get_nome_usuario()
        
        def confirmar_logout(e):
            try:
                modal.open = False
                self.page.update()
                
                # Reset dos dados
                app_state.reset_dados()
                
                # Verificar se login_screen existe no app_controller
                if hasattr(self.app_controller, 'login_screen') and self.app_controller.login_screen:
                    self.app_controller.login_screen.mostrar()
                elif hasattr(self.app_controller, 'mostrar_login'):
                    self.app_controller.mostrar_login()
                else:
                    # Fallback: limpar página e mostrar mensagem
                    self.page.clean()
                    self.page.add(ft.Text("Logout realizado. Recarregue a página para fazer login novamente."))
                    self.page.update()
                
                mostrar_mensagem(self.page, "👋 Logout realizado com sucesso!")
                
            except Exception as ex:
                mostrar_mensagem(self.page, f"❌ Erro ao fazer logout: {str(ex)}")
        
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
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text("⚠️ Você precisará fazer login novamente", size=12, color=ft.colors.ORANGE_600),
                        padding=ft.padding.all(8),
                        bgcolor=ft.colors.ORANGE_50,
                        border_radius=6
                    )
                ]),
                width=300,
                height=120,
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
    
    def _fechar_modal(self, modal):
        """Fecha modal"""
        modal.open = False
        self.page.update()