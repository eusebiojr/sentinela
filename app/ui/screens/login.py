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
        
    def _validar_resolucao(self):
        """Valida se a resolução é adequada"""
        width = self.page.window_width
        height = self.page.window_height
        
        if width < 320 or height < 400:
            # Resolução muito pequena - mostra aviso
            self._mostrar_aviso_resolucao()
            return False
        
        return True
        
    def _mostrar_aviso_resolucao(self):
        """Mostra aviso de resolução inadequada"""
        aviso = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.WARNING, color=ft.colors.ORANGE_600, size=48),
                ft.Container(height=20),
                ft.Text(
                    "Resolução Inadequada",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.ORANGE_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=15),
                ft.Text(
                    f"Resolução atual: {self.page.window_width}x{self.page.window_height}",
                    size=14,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=10),
                ft.Text(
                    "Para melhor experiência, use resolução mínima de 800x600",
                    size=12,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Continuar Mesmo Assim",
                    on_click=lambda e: self.mostrar(),
                    bgcolor=ft.colors.ORANGE_600,
                    color=ft.colors.WHITE
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
            ),
            alignment=ft.alignment.center,
            padding=30,
            bgcolor=ft.colors.WHITE,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
            width=350
        )
        
        tela_aviso = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                aviso,
                ft.Container(expand=True)
            ]),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_50,
            expand=True
        )
        
        self.page.clean()
        self.page.add(tela_aviso)
        self.page.update() 

    def mostrar(self):
        """Tela de login RESPONSIVA - Versão simples sem erros"""
        
        # Detecta dimensões
        screen_width = self.page.window_width
        screen_height = self.page.window_height
        
        print(f"🖥️ Resolução: {screen_width}x{screen_height}")
        
        # Configurações baseadas na altura
        if screen_height <= 768:  # Notebooks como 1920x1080
            # CONFIGURAÇÃO PARA NOTEBOOKS
            container_width = 540 
            image_size = 135      
            title_size = 35      
            subtitle_size = 18    
            field_width = 470     
            padding_container = 27 
            button_height = 60   
            support_button_size = 16
            use_scroll = True
            
        elif screen_height <= 900:  # Telas médias
            container_width = 610 
            image_size = 175      
            title_size = 38        
            subtitle_size = 19     
            field_width = 515      
            padding_container = 34 
            button_height = 65    
            support_button_size = 18 
            use_scroll = False
            
        else:  # Telas grandes
            container_width = 675 
            image_size = 215      
            title_size = 43       
            subtitle_size = 22     
            field_width = 540      
            padding_container = 40 
            button_height = 68     
            support_button_size = 19 
            use_scroll = False

        # Campos de entrada
        self.email_field = ft.TextField(
            label="Email corporativo",
            width=field_width,
            height=button_height,
            prefix_icon=ft.icons.EMAIL,
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600,
            on_submit=self._fazer_login
        )
        
        self.password_field = ft.TextField(
            label="Senha",
            password=True,
            can_reveal_password=True,
            width=field_width,
            height=button_height,
            prefix_icon=ft.icons.LOCK,
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600,
            on_submit=self._fazer_login
        )
        
        self.btn_login = ft.ElevatedButton(
            "Entrar no Sistema",
            on_click=self._fazer_login,
            width=field_width,
            height=button_height,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # Botão de suporte - VERSÃO SIMPLIFICADA
        btn_suporte = ft.TextButton(
            text="⚠️ Reportar Problema",
            on_click=self._abrir_ticket_suporte,
            tooltip="Problemas com login? Clique aqui"
        )

        # Conteúdo do formulário
        form_items = [
            ft.Container(height=15),  # era 10
            
            # Logo (aumentada)
            ft.Image(
                src="images/sentinela.png",
                width=image_size,
                height=image_size,
                fit=ft.ImageFit.CONTAIN
            ),
            
            ft.Container(height=27),  # era 20
            
            # Títulos
            ft.Text("Sentinela", size=title_size, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800),
            ft.Text("Sistema de Gestão de Desvios", size=subtitle_size, color=ft.colors.GREY_600),
            
            ft.Container(height=34),  # era 25
            
            # Campos
            self.email_field,
            ft.Container(height=16),  # era 12
            self.password_field,
            ft.Container(height=27),  # era 20
            
            # Botões
            self.btn_login,
            ft.Container(height=20),  # era 15
            btn_suporte,
            
            ft.Container(height=27)   # era 20
        ]

        # Container principal do formulário
        login_form = ft.Container(
            content=ft.Column(
                form_items,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            ),
            padding=padding_container,
            border_radius=15,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.BLACK12),
            width=container_width
        )

        # Container com scroll se necessário
        if use_scroll:
            # Para notebooks - com scroll
            main_content = ft.Column([
                ft.Container(height=20),
                login_form,
                ft.Container(height=20)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            )
        else:
            # Para telas grandes - sem scroll, centralizado
            main_content = ft.Column([
                ft.Container(expand=True),
                login_form,
                ft.Container(expand=True)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )

        # Tela completa
        login_screen = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                main_content,
                ft.Container(expand=True)
            ]),
            bgcolor=ft.colors.GREY_50,
            expand=True
        )

        self.page.clean()
        self.page.add(login_screen)
        self.page.update()
        
        print(f"✅ Login carregado - Scroll: {use_scroll}, Container: {container_width}px")
    
    def mostrar_com_validacao(self):
        """Mostra tela de login com validação de resolução"""
        if self._validar_resolucao():
            self.mostrar()
        else:
            self._mostrar_aviso_resolucao()

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