"""
Auto Refresh Service - Controla atualização automática com pausa inteligente
Localização: app/services/auto_refresh_service.py
"""
import threading
import time
from typing import Callable, Optional
from ..config.logging_config import setup_logger

logger = setup_logger("auto_refresh")


class AutoRefreshService:
    """Serviço de atualização automática com controle inteligente de pausa"""
    
    def __init__(self, page, app_controller):
        self.page = page
        self.app_controller = app_controller
        
        # Configuração do timer
        self.intervalo_segundos = 600  # 10 minutos
        self.timer_ativo = False
        self.timer_pausado = False
        self.usuario_habilitou = False
        
        # Thread de controle
        self.thread_timer = None
        self.parar_thread = False
        
        # Callbacks
        self.callback_atualizacao = None
        self.callback_status_mudou = None
        
        # Controle de tempo
        self.segundos_restantes = 0
        self.ultima_atualizacao = None
        
    def configurar_callbacks(self, callback_atualizacao: Callable = None, 
                           callback_status_mudou: Callable = None):
        """Configura callbacks para eventos do timer"""
        self.callback_atualizacao = callback_atualizacao
        self.callback_status_mudou = callback_status_mudou
    
    def iniciar_timer(self):
        """Inicia o timer de auto-refresh"""
        if not self.usuario_habilitou:
            logger.info("🔕 Auto-refresh desabilitado pelo usuário")
            return
            
        if self.timer_ativo:
            logger.warning("⚠️ Timer já está ativo")
            return
            
        self.timer_ativo = True
        self.timer_pausado = False
        self.parar_thread = False
        self.segundos_restantes = self.intervalo_segundos
        
        # Inicia thread do timer
        self.thread_timer = threading.Thread(target=self._executar_timer, daemon=True)
        self.thread_timer.start()
        
        logger.info(f"🔄 Auto-refresh iniciado - intervalo: {self.intervalo_segundos/60:.0f} minutos")
        self._notificar_mudanca_status()
    
    def parar_timer(self):
        """Para completamente o timer"""
        self.parar_thread = True
        self.timer_ativo = False
        self.timer_pausado = False
        
        if self.thread_timer and self.thread_timer.is_alive():
            self.thread_timer.join(timeout=1)
            
        logger.info("🛑 Auto-refresh parado")
        self._notificar_mudanca_status()
    
    def pausar_timer(self, motivo: str = "campos preenchidos"):
        """Pausa o timer (mantém thread ativa, mas não executa refresh)"""
        if not self.timer_ativo:
            return
            
        if not self.timer_pausado:
            self.timer_pausado = True
            logger.info(f"⏸️ Auto-refresh pausado: {motivo}")
            self._notificar_mudanca_status()
    
    def retomar_timer(self):
        """Retoma o timer pausado"""
        if not self.timer_ativo:
            return
            
        if self.timer_pausado:
            self.timer_pausado = False
            # Reinicia contador quando retoma
            self.segundos_restantes = self.intervalo_segundos
            logger.info("▶️ Auto-refresh retomado")
            self._notificar_mudanca_status()
    
    def habilitar_usuario(self, habilitado: bool):
        """Habilita/desabilita auto-refresh conforme configuração do usuário"""
        self.usuario_habilitou = habilitado
        
        if habilitado and not self.timer_ativo:
            self.iniciar_timer()
        elif not habilitado and self.timer_ativo:
            self.parar_timer()
    
    def obter_status(self) -> dict:
        """Retorna status atual do timer"""
        if not self.usuario_habilitou:
            return {
                "estado": "desabilitado",
                "descricao": "Auto-refresh desabilitado",
                "icone": "🔕",
                "segundos_restantes": 0
            }
        elif not self.timer_ativo:
            return {
                "estado": "inativo", 
                "descricao": "Auto-refresh inativo",
                "icone": "⏹️",
                "segundos_restantes": 0
            }
        elif self.timer_pausado:
            return {
                "estado": "pausado",
                "descricao": "Pausado (campos preenchidos)", 
                "icone": "⏸️",
                "segundos_restantes": 0
            }
        else:
            minutos = self.segundos_restantes // 60
            segundos = self.segundos_restantes % 60
            return {
                "estado": "ativo",
                "descricao": f"Ativo ({minutos}min {segundos:02d}s)",
                "icone": "🔄", 
                "segundos_restantes": self.segundos_restantes
            }
    
    def _executar_timer(self):
        """Thread principal do timer"""
        logger.info("🏁 Thread do auto-refresh iniciada")
        
        while not self.parar_thread and self.timer_ativo:
            try:
                # Decrementa apenas se não estiver pausado
                if not self.timer_pausado and self.segundos_restantes > 0:
                    self.segundos_restantes -= 1
                
                # Executa refresh quando tempo acabar (e não estiver pausado)
                if self.segundos_restantes <= 0 and not self.timer_pausado:
                    self._executar_refresh()
                    self.segundos_restantes = self.intervalo_segundos  # Reinicia ciclo
                
                # Aguarda 1 segundo
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Erro na thread do timer: {e}")
                break
        
        logger.info("🏁 Thread do auto-refresh finalizada")
    
    def _executar_refresh(self):
        """Executa a atualização de dados"""
        try:
            logger.info("🔄 Executando auto-refresh...")
            self.ultima_atualizacao = time.time()
            
            # Chama callback personalizado se definido
            if self.callback_atualizacao:
                self.callback_atualizacao()
            else:
                # Fallback para app_controller
                if hasattr(self.app_controller, 'atualizar_dados'):
                    self.app_controller.atualizar_dados()
            
            logger.info("✅ Auto-refresh executado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro durante auto-refresh: {e}")
    
    def _notificar_mudanca_status(self):
        """Notifica mudança de status via callback"""
        if self.callback_status_mudou:
            try:
                status = self.obter_status()
                self.callback_status_mudou(status)
            except Exception as e:
                logger.error(f"❌ Erro ao notificar mudança de status: {e}")
    
    def obter_tempo_formatado(self) -> str:
        """Retorna tempo restante formatado"""
        if self.segundos_restantes <= 0:
            return "00:00"
        
        minutos = self.segundos_restantes // 60
        segundos = self.segundos_restantes % 60
        return f"{minutos:02d}:{segundos:02d}"


# Instância global (será inicializada no app_controller)
auto_refresh_service = None


def inicializar_auto_refresh(page, app_controller):
    """Inicializa o serviço global de auto-refresh"""
    global auto_refresh_service
    auto_refresh_service = AutoRefreshService(page, app_controller)
    return auto_refresh_service


def obter_auto_refresh_service():
    """Obtém instância global do auto-refresh service"""
    return auto_refresh_service