"""
Componente de Indicador de Auto-Refresh - Mostra status visual do timer
Localização: app/ui/components/auto_refresh_indicator.py
"""
import flet as ft
import threading
import time
from typing import Dict, Any, Callable
from ...config.logging_config import setup_logger

logger = setup_logger("auto_refresh_indicator")


class AutoRefreshIndicator:
    """Componente visual para mostrar status do auto-refresh"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Componentes visuais
        self.badge_container = None
        self.status_icon = None
        self.status_text = None
        self.tooltip_text = None
        
        # Estado atual
        self.ultimo_status = {}
        
        # Thread para atualizar display
        self.thread_atualizacao = None
        self.parar_atualizacao = False
        
    def criar_indicador(self) -> ft.Container:
        """
        Cria o componente visual do indicador
        
        Returns:
            Container com o indicador visual
        """
        # Ícone de status
        self.status_icon = ft.Icon(
            ft.icons.REFRESH_ROUNDED,
            size=16,
            color=ft.colors.GREY_500
        )
        
        # Texto de status
        self.status_text = ft.Text(
            "Auto-refresh: Desabilitado",
            size=11,
            color=ft.colors.GREY_600,
            weight=ft.FontWeight.W_400
        )
        
        # Container principal
        self.badge_container = ft.Container(
            content=ft.Row([
                self.status_icon,
                self.status_text
            ], spacing=6, alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
            bgcolor=ft.colors.with_opacity(0.1, ft.colors.GREY_400),
            border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.GREY_400)),
            tooltip="Auto-refresh desabilitado",
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )
        
        # Inicia thread de atualização
        self._iniciar_atualizacao_periodica()
        
        return self.badge_container
    
    def atualizar_status(self, status: Dict[str, Any]):
        """
        Atualiza o status visual do indicador
        
        Args:
            status: Dict com estado, descrição, ícone e segundos_restantes
        """
        try:
            if not self.badge_container:
                return
                
            estado = status.get("estado", "desabilitado")
            descricao = status.get("descricao", "Auto-refresh desabilitado")
            icone = status.get("icone", "🔕")
            segundos_restantes = status.get("segundos_restantes", 0)
            
            # Atualiza ícone baseado no estado
            self._atualizar_icone(estado, icone)
            
            # Atualiza texto
            if estado == "ativo" and segundos_restantes > 0:
                minutos = segundos_restantes // 60
                segundos = segundos_restantes % 60
                texto_status = f"Auto-refresh: {minutos}min {segundos:02d}s"
            else:
                texto_status = f"Auto-refresh: {self._obter_texto_estado(estado)}"
            
            self.status_text.value = texto_status
            
            # Atualiza cores e estilo baseado no estado
            self._atualizar_estilo(estado)
            
            # Atualiza tooltip
            self._atualizar_tooltip(descricao, estado)
            
            # Salva status para comparação
            self.ultimo_status = status.copy()
            
            # Atualiza interface
            self.page.update()
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar indicador: {e}")
    
    def _atualizar_icone(self, estado: str, icone: str):
        """Atualiza ícone baseado no estado"""
        if estado == "ativo":
            self.status_icon.name = ft.icons.REFRESH_ROUNDED
            self.status_icon.color = ft.colors.BLUE_600
            # Adiciona animação de rotação para estado ativo
            self.status_icon.animate_rotation = ft.animation.Animation(2000, ft.AnimationCurve.LINEAR)
            self.status_icon.rotate = ft.transform.Rotate(angle=6.28)  # 360 graus
        elif estado == "pausado":
            self.status_icon.name = ft.icons.PAUSE_CIRCLE_OUTLINE
            self.status_icon.color = ft.colors.ORANGE_600
            self.status_icon.animate_rotation = None
            self.status_icon.rotate = None
        elif estado == "desabilitado":
            self.status_icon.name = ft.icons.REFRESH_ROUNDED
            self.status_icon.color = ft.colors.GREY_500
            self.status_icon.animate_rotation = None
            self.status_icon.rotate = None
        else:  # inativo
            self.status_icon.name = ft.icons.STOP_CIRCLE_OUTLINE
            self.status_icon.color = ft.colors.GREY_600
            self.status_icon.animate_rotation = None
            self.status_icon.rotate = None
    
    def _atualizar_estilo(self, estado: str):
        """Atualiza estilo visual baseado no estado"""
        if estado == "ativo":
            self.badge_container.bgcolor = ft.colors.with_opacity(0.1, ft.colors.BLUE_400)
            self.badge_container.border = ft.border.all(1, ft.colors.with_opacity(0.3, ft.colors.BLUE_400))
            self.status_text.color = ft.colors.BLUE_700
        elif estado == "pausado":
            self.badge_container.bgcolor = ft.colors.with_opacity(0.1, ft.colors.ORANGE_400)
            self.badge_container.border = ft.border.all(1, ft.colors.with_opacity(0.3, ft.colors.ORANGE_400))
            self.status_text.color = ft.colors.ORANGE_700
        elif estado == "desabilitado":
            self.badge_container.bgcolor = ft.colors.with_opacity(0.1, ft.colors.GREY_400)
            self.badge_container.border = ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.GREY_400))
            self.status_text.color = ft.colors.GREY_600
        else:  # inativo
            self.badge_container.bgcolor = ft.colors.with_opacity(0.1, ft.colors.GREY_500)
            self.badge_container.border = ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.GREY_500))
            self.status_text.color = ft.colors.GREY_700
    
    def _atualizar_tooltip(self, descricao: str, estado: str):
        """Atualiza tooltip com informações detalhadas"""
        if estado == "ativo":
            tooltip = f"{descricao}\n💡 Timer ativo - dados serão atualizados automaticamente"
        elif estado == "pausado":
            tooltip = f"{descricao}\n💡 Timer pausado - você tem alterações não salvas"
        elif estado == "desabilitado":
            tooltip = f"{descricao}\n💡 Vá em Configurações para habilitar"
        else:
            tooltip = f"{descricao}\n💡 Timer parado"
        
        self.badge_container.tooltip = tooltip
    
    def _obter_texto_estado(self, estado: str) -> str:
        """Converte estado para texto amigável"""
        mapeamento = {
            "ativo": "Ativo",
            "pausado": "Pausado", 
            "desabilitado": "Desabilitado",
            "inativo": "Parado"
        }
        return mapeamento.get(estado, "Desconhecido")
    
    def _iniciar_atualizacao_periodica(self):
        """Inicia thread para atualizar indicador periodicamente"""
        def atualizar_periodicamente():
            while not self.parar_atualizacao:
                try:
                    # Obtém status atual do auto-refresh
                    from ...services.auto_refresh_service import obter_auto_refresh_service
                    
                    auto_refresh = obter_auto_refresh_service()
                    if auto_refresh:
                        status_atual = auto_refresh.obter_status()
                        
                        # Só atualiza se status mudou
                        if status_atual != self.ultimo_status:
                            self.atualizar_status(status_atual)
                    
                    # Atualiza a cada 1 segundo quando ativo, 5 segundos quando não
                    if self.ultimo_status.get("estado") == "ativo":
                        time.sleep(1)
                    else:
                        time.sleep(5)
                        
                except Exception as e:
                    logger.error(f"❌ Erro na atualização periódica: {e}")
                    time.sleep(5)
        
        self.thread_atualizacao = threading.Thread(target=atualizar_periodicamente, daemon=True)
        self.thread_atualizacao.start()
        logger.info("🔄 Thread de atualização do indicador iniciada")
    
    def parar_atualizacao(self):
        """Para a thread de atualização"""
        self.parar_atualizacao = True
        if self.thread_atualizacao and self.thread_atualizacao.is_alive():
            self.thread_atualizacao.join(timeout=1)
        logger.info("🛑 Thread de atualização do indicador parada")
    
    def mostrar_toast_mudanca(self, novo_estado: str):
        """
        Mostra toast quando estado muda
        
        Args:
            novo_estado: Novo estado do timer
        """
        try:
            from ...utils.ui_utils import mostrar_mensagem
            
            if novo_estado == "pausado":
                mostrar_mensagem(
                    self.page, 
                    "⏸️ Timer pausado - você tem alterações não salvas", 
                    "info", 
                    duracao=3000
                )
            elif novo_estado == "ativo":
                mostrar_mensagem(
                    self.page, 
                    "▶️ Timer retomado - próxima atualização em 10min", 
                    "info", 
                    duracao=3000
                )
            elif novo_estado == "desabilitado":
                mostrar_mensagem(
                    self.page, 
                    "🔕 Auto-refresh desabilitado", 
                    "info", 
                    duracao=2000
                )
                
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar toast: {e}")


# Instância global
auto_refresh_indicator = None


def criar_auto_refresh_indicator(page):
    """Cria instância global do indicador"""
    global auto_refresh_indicator
    auto_refresh_indicator = AutoRefreshIndicator(page)
    return auto_refresh_indicator


def obter_auto_refresh_indicator():
    """Obtém instância global do indicador"""
    return auto_refresh_indicator