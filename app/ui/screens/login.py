"""
Tela de login do sistema
"""
import flet as ft
from ...utils.ui_utils import get_screen_size, mostrar_mensagem
from ..components.ticket_modal import criar_modal_ticket

class LoginScreen:
    """Tela de login"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.email_field = None
        self.password_field = None
        self.btn_login = None
        
        
    def mostrar(self):
        """Exibe a tela de login COM botão de suporte"""
        # Detecta tamanho da tela para responsividade
        screen_size = get_screen_size(self.page.window_width)
        
        # Configurações responsivas
        if screen_size == "small":
            container_width = min(380, self.page.window_width - 40)
            image_size = 120
            title_size = 28
            subtitle_size = 14
            field_width = container_width - 60
            padding_container = 20
            spacing_top = 20
            spacing_middle = 30
            spacing_fields = 10
            button_height = 45
            support_button_size = 12
        elif screen_size == "medium":
            container_width = min(450, self.page.window_width - 60)
            image_size = 160
            title_size = 32
            subtitle_size = 16
            field_width = container_width - 80
            padding_container = 35
            spacing_top = 35
            spacing_middle = 35
            spacing_fields = 15
            button_height = 50
            support_button_size = 14
        else:  # large
            container_width = 500
            image_size = 200
            title_size = 36
            subtitle_size = 18
            field_width = 400
            padding_container = 50
            spacing_top = 50
            spacing_middle = 40
            spacing_fields = 15
            button_height = 55
            support_button_size = 16

        # Campos de login (manter os existentes)
        self.email_field = ft.TextField(
            label="Email",
            width=field_width,
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600,
            prefix_icon=ft.icons.EMAIL
        )

        self.password_field = ft.TextField(
            label="Senha",
            width=field_width,
            password=True,
            can_reveal_password=True,
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600,
            prefix_icon=ft.icons.LOCK,
            on_submit=self._fazer_login
        )

        # Botão de login principal
        self.btn_login = ft.ElevatedButton(
            "Entrar",
            width=field_width,
            height=button_height,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self._fazer_login
        )

        # ===== NOVO: Botão de suporte =====
        btn_suporte = ft.TextButton(
            content=ft.Row([
                ft.Icon(ft.icons.SUPPORT_AGENT, size=support_button_size, color=ft.colors.GREY_600),
                ft.Text("Reportar Problema", size=support_button_size, color=ft.colors.GREY_600)
            ], alignment=ft.MainAxisAlignment.CENTER, tight=True),
            on_click=self._abrir_ticket_suporte,
            style=ft.ButtonStyle(
                overlay_color=ft.colors.GREY_100,
                shape=ft.RoundedRectangleBorder(radius=6)
            )
        )

        # Container do formulário de login ATUALIZADO
        login_container = ft.Container(
            content=ft.Column([
                ft.Container(height=spacing_top),
                
                # Logo
                ft.Image(
                    src="/images/sentinela.png",
                    width=image_size,
                    height=image_size,
                    fit=ft.ImageFit.CONTAIN
                ),
                
                ft.Container(height=spacing_middle),
                
                # Título e subtítulo
                ft.Text("Sentinela", size=title_size, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800),
                ft.Text("Sistema de Gestão de Desvios", size=subtitle_size, color=ft.colors.GREY_600),
                
                ft.Container(height=spacing_middle),
                
                # Campos de login
                self.email_field,
                ft.Container(height=spacing_fields),
                self.password_field,
                
                ft.Container(height=spacing_fields + 10),
                
                # Botão de login
                self.btn_login,
                
                ft.Container(height=15),
                
                # ===== NOVO: Botão de suporte =====
                btn_suporte,
                
                ft.Container(height=spacing_top)
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=padding_container,
            border_radius=20,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=15, color=ft.colors.BLACK12),
            width=container_width,
            margin=ft.margin.all(20),
            alignment=ft.alignment.center
        )

        # Tela de login centralizada (manter igual)
        login_screen = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Column([
                    ft.Container(expand=True),
                    login_container,
                    ft.Container(expand=True)
                ], expand=True),
                ft.Container(expand=True)
            ]),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_50,
            expand=True
        )

        self.page.clean()
        self.page.add(login_screen)
        self.page.update()
    
    def _fazer_login(self, e):
        """Processa tentativa de login"""
        email = self.email_field.value.strip() if self.email_field.value else ""
        senha = self.password_field.value.strip() if self.password_field.value else ""
        
        if not email or not senha:
            mostrar_mensagem(self.page, "Preencha email e senha", True)
            return
        
        # Tenta fazer login
        sucesso = self.app_controller.fazer_login(email, senha)
        
        if not sucesso:
            mostrar_mensagem(self.page, "Login inválido", True)
            return
        
    def _abrir_ticket_suporte(self, e):
        """Abre modal de ticket de suporte na tela de login"""
        try:
            # Cria modal de ticket sem usuário logado
            modal_ticket = criar_modal_ticket(
                self.page, 
                callback_sucesso=self._ticket_criado_sucesso
            )
            
            # Mostra o modal
            modal_ticket.mostrar_modal(usuario_logado=None)
            
        except Exception as ex:
            print(f"❌ Erro ao abrir ticket de suporte: {str(ex)}")
            mostrar_mensagem(self.page, "Erro ao abrir formulário de suporte", True)

    def _ticket_criado_sucesso(self, ticket_id: int, dados_ticket: dict):
        """Callback executado quando ticket é criado com sucesso"""
        try:
            print(f"✅ Ticket {ticket_id} criado na tela de login")
            print(f"📧 Usuário: {dados_ticket.get('usuario')}")
            print(f"🎯 Motivo: {dados_ticket.get('motivo')}")
            
            # Aqui você pode adicionar lógica adicional se necessário
            # Por exemplo, enviar notificação para Teams
            
        except Exception as ex:
            print(f"❌ Erro no callback de sucesso: {str(ex)}")