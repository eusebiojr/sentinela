"""
Tela de login do sistema
"""
import flet as ft
from ...utils.ui_utils import get_screen_size, mostrar_mensagem


class LoginScreen:
    """Tela de login"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.email_field = None
        self.password_field = None
        self.btn_login = None
        
    def mostrar(self):
        """Exibe a tela de login"""
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
        
        # Campos de login
        self.email_field = ft.TextField(
            label="E-mail corporativo",
            width=field_width,
            prefix_icon=ft.icons.EMAIL,
            border_radius=10,
            keyboard_type=ft.KeyboardType.EMAIL,
            autofocus=True
        )
        
        self.password_field = ft.TextField(
            label="Senha",
            width=field_width,
            prefix_icon=ft.icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            on_submit=self._fazer_login
        )
        
        self.btn_login = ft.ElevatedButton(
            text="Entrar",
            width=field_width,
            height=50,
            on_click=self._fazer_login,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE_600,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        
        # Container principal do login
        login_container = ft.Container(
            content=ft.Column([
                ft.Container(height=spacing_top),
                ft.Image(
                    src="images/sentinela.png",
                    width=image_size,
                    height=image_size,
                    fit=ft.ImageFit.CONTAIN
                ),
                ft.Text("Sentinela", size=title_size, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
                ft.Text("Faça seu login para continuar", size=subtitle_size, color=ft.colors.GREY_600),
                ft.Container(height=spacing_middle),
                self.email_field,
                ft.Container(height=spacing_fields),
                self.password_field,
                ft.Container(height=spacing_fields + 10),
                self.btn_login
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=padding_container,
            border_radius=20,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=15, color=ft.colors.BLACK12),
            width=container_width,
            margin=ft.margin.all(20),
            alignment=ft.alignment.center
        )
        
        # Tela de login centralizada
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