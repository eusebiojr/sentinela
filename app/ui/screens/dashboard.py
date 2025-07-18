"""
Tela principal do dashboard - VERSÃO FINAL LIMPA
"""
import flet as ft
from ...core.state import app_state
from ...utils.ui_utils import get_screen_size
from ..components.cards import DashboardCards
from ..components.eventos_otimizado import EventosManagerOtimizado
from ..components.modern_header import ModernHeader


class DashboardScreen:
    """Tela principal do dashboard"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.cards_component = DashboardCards(page)
        self.eventos_manager = EventosManagerOtimizado(page, app_controller)
        self.modern_header = ModernHeader(page, app_controller)
        
    def mostrar(self):
        """Exibe a tela do dashboard"""
        # Header moderno
        header = self.modern_header.criar_header()
        
        # Cards dashboard
        dashboard_cards = self._criar_dashboard_cards()
        
        # Lista de eventos
        eventos_lista = self._criar_eventos_lista()
        
        # Rodapé
        rodape = self._criar_rodape()
        
        # Layout principal otimizado
        layout_principal = ft.Column([
            header,  # Header fixo no topo
            ft.Container(  # Container para cards com altura controlada
                content=dashboard_cards,
                bgcolor=ft.colors.GREY_50
            ),
            ft.Container(  # Container para eventos - expansível
                content=eventos_lista,
                expand=True,
                bgcolor=ft.colors.GREY_50
            ),
            rodape  # Rodapé fixo
        ], 
        spacing=0,
        expand=True
        )
        
        # Atualiza a página
        self.page.clean()
        self.page.add(layout_principal)
        self.page.update()
    
    def _criar_dashboard_cards(self):
        """Cria os cards do dashboard"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=15), 
                self.cards_component.criar_cards()
            ]), 
            padding=ft.padding.only(left=20, right=20, top=10, bottom=15)
        )
    
    def _criar_eventos_lista(self):
        """Cria a lista de eventos"""
        return self.eventos_manager.criar_lista_eventos()
    
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