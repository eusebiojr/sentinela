"""
Tela principal do dashboard
"""
import flet as ft
from ...core.state import app_state
from ...utils.ui_utils import get_screen_size
from ..components.cards import DashboardCards
from ..components.eventos_otimizado import EventosManagerOtimizado


class DashboardScreen:
    """Tela principal do dashboard"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.cards_component = DashboardCards(page)
        self.eventos_manager = EventosManagerOtimizado(page, app_controller)  # Versão otimizada
        
    def mostrar(self):
        """Exibe a tela do dashboard"""
        # Header
        header = self._criar_header()
        
        # Cards dashboard
        dashboard_cards = self._criar_dashboard_cards()
        
        # Lista de eventos
        eventos_lista = self._criar_eventos_lista()
        
        # Rodapé
        rodape = self._criar_rodape()
        
        # Layout principal
        self.page.clean()
        self.page.add(
            ft.Column([
                header,
                dashboard_cards,
                eventos_lista,
                rodape
            ], expand=True)
        )
        self.page.update()
    
    def _criar_header(self):
        """Cria o header da aplicação"""
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Image(
                        src="images/logo.png",
                        width=20,
                        height=20,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Container(width=10),
                    ft.Text(
                        f"Sentinela - {app_state.get_nome_usuario()}", 
                        size=24, 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.colors.WHITE
                    )
                ], spacing=0),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "🔄 Atualizar", 
                    on_click=lambda e: self.app_controller.atualizar_dados(), 
                    bgcolor=ft.colors.WHITE, 
                    color=ft.colors.BLUE_600,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6)
                    )
                )
            ]),
            padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
            bgcolor=ft.colors.BLUE_600
        )
    
    def _criar_dashboard_cards(self):
        """Cria os cards do dashboard"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=15), 
                self.cards_component.criar_cards()
            ]), 
            padding=ft.padding.only(left=20, right=20, top=10, bottom=15),
            bgcolor=ft.colors.GREY_50
        )
    
    def _criar_eventos_lista(self):
        """Cria a lista de eventos"""
        return ft.Container(
            content=self.eventos_manager.criar_lista_eventos(),
            expand=True,
            bgcolor=ft.colors.GREY_50
        )
    
    def _criar_rodape(self):
        """Cria o rodapé da aplicação"""
        return ft.Container(
            content=ft.Text(
                "Developed by Logistica MS - Suzano", 
                size=14, 
                color=ft.colors.GREY_600, 
                text_align=ft.TextAlign.CENTER
            ),
            padding=5,
            alignment=ft.alignment.center
        )