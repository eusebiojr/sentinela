import threading
import time
from typing import Callable, Optional
from ..config.logging_config import setup_logger
from ..config.settings import refresh_config

logger = setup_logger("auto_refresh")


class AutoRefreshService:
    """Serviço de atualização automática - CORRIGIDO para não perder dados do usuário"""
    
    def __init__(self, page, app_controller):
        self.page = page
        self.app_controller = app_controller
        
        # ===== CORREÇÃO CRÍTICA: DESABILITADO POR PADRÃO =====
        self.timer_ativo = False
        self.timer_pausado = False
        self.usuario_habilitou = False  # ⚡ PADRÃO: FALSE (DESABILITADO)
        
        # Thread de controle
        self.thread_timer = None
        self.parar_thread = False
        
        # Callbacks
        self.callback_atualizacao = None
        self.callback_status_mudou = None
        
        # Controle de tempo
        self.segundos_restantes = 0
        self.ultima_atualizacao = None
        
        # ===== Controle de campos preenchidos =====
        self.campos_monitorados = set()  # IDs de campos sendo monitorados
        self.usuario_digitando = False
        
        logger.info("🔄 AutoRefreshService inicializado - DESABILITADO por padrão")
        
    def configurar_callbacks(self, callback_atualizacao: Callable = None, 
                           callback_status_mudou: Callable = None):
        """Configura callbacks para eventos do timer"""
        self.callback_atualizacao = callback_atualizacao
        self.callback_status_mudou = callback_status_mudou
    
    def habilitar_usuario(self, habilitado: bool):
        """
        ✅ FUNÇÃO PRINCIPAL: Habilita/desabilita auto-refresh conforme configuração do usuário
        
        Esta é a ÚNICA forma de ativar o auto-refresh!
        """
        self.usuario_habilitou = habilitado
        
        if habilitado:
            logger.info("🔄 Auto-refresh HABILITADO pelo usuário")
            if not self.timer_ativo:
                self.iniciar_timer()
        else:
            logger.info("🔕 Auto-refresh DESABILITADO pelo usuário")
            if self.timer_ativo:
                self.parar_timer()
        
        self._notificar_mudanca_status()
    
    def iniciar_timer(self):
        """Inicia o timer de auto-refresh - APENAS se habilitado pelo usuário"""
        if not self.usuario_habilitou:
            logger.info("🔕 Auto-refresh desabilitado pelo usuário - não iniciando timer")
            return
            
        if self.timer_ativo:
            logger.warning("⚠️ Timer já está ativo")
            return
            
        self.timer_ativo = True
        self.timer_pausado = False
        self.parar_thread = False
        self.segundos_restantes = refresh_config.auto_refresh_interval_seconds
        
        # Inicia thread do timer
        self.thread_timer = threading.Thread(target=self._executar_timer, daemon=True)
        self.thread_timer.start()
        
        logger.info(f"🔄 Auto-refresh iniciado - intervalo: {refresh_config.auto_refresh_interval_seconds/60:.0f} minutos")
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
            self.segundos_restantes = refresh_config.auto_refresh_interval_seconds
            logger.info("▶️ Auto-refresh retomado")
            self._notificar_mudanca_status()
    
    # ===== DETECÇÃO AUTOMÁTICA DE CAMPOS PREENCHIDOS =====
    
    def registrar_campo_digitacao(self, campo_id: str):
        """
        Registra que usuário começou a digitar em um campo
        Pausa automaticamente o timer para evitar perda de dados
        """
        if not self.timer_ativo:
            return
            
        self.campos_monitorados.add(campo_id)
        
        if not self.usuario_digitando:
            self.usuario_digitando = True
            self.pausar_timer("usuário digitando")
            logger.info(f"⌨️ Usuário digitando no campo {campo_id} - timer pausado automaticamente")
    
    def desregistrar_campo_digitacao(self, campo_id: str):
        """
        Remove campo do monitoramento
        Retoma timer se não há mais campos sendo preenchidos
        """
        self.campos_monitorados.discard(campo_id)
        
        if len(self.campos_monitorados) == 0 and self.usuario_digitando:
            self.usuario_digitando = False
            # Aguarda 30 segundos antes de retomar (tempo para usuário continuar digitando)
            threading.Timer(refresh_config.user_typing_delay_seconds, self._verificar_retomar_timer).start()
            logger.info(f"⏱️ Campo {campo_id} liberado - verificação de retomada em 30s")
    
    def _verificar_retomar_timer(self):
        """Verifica se pode retomar timer após delay"""
        if len(self.campos_monitorados) == 0 and not self.usuario_digitando:
            self.retomar_timer()
            logger.info("▶️ Timer retomado automaticamente após fim da digitação")
    
    def limpar_campos_monitorados(self):
        """Limpa todos os campos monitorados (útil ao sair de uma tela)"""
        self.campos_monitorados.clear()
        self.usuario_digitando = False
    
    # ===== MÉTODOS EXISTENTES (INALTERADOS) =====
    
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
            motivo = "digitando" if self.usuario_digitando else "pausado"
            return {
                "estado": "pausado",
                "descricao": f"Pausado ({motivo})", 
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
                    self.segundos_restantes = refresh_config.auto_refresh_interval_seconds  # Reinicia ciclo
                
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


# ===== INSTÂNCIA GLOBAL CORRIGIDA =====
auto_refresh_service = None


def inicializar_auto_refresh(page, app_controller):
    """
    Inicializa o serviço global de auto-refresh
    ⚡ IMPORTANTE: Service inicia DESABILITADO por padrão
    """
    global auto_refresh_service
    auto_refresh_service = AutoRefreshService(page, app_controller)
    logger.info("🔄 AutoRefreshService inicializado - DESABILITADO por padrão")
    return auto_refresh_service


def obter_auto_refresh_service():
    """Obtém instância global do auto-refresh service"""
    return auto_refresh_service


# ===== FUNÇÃO AUXILIAR PARA CAMPOS DE ENTRADA =====
def criar_campo_monitorado(campo_base, campo_id: str):
    """
    Wrapper para campos de entrada que registra automaticamente
    digitação para pausar o auto-refresh
    
    Args:
        campo_base: Campo Flet original (TextField, etc.)
        campo_id: ID único do campo para monitoramento
        
    Returns:
        Campo com monitoramento automático integrado
    """
    auto_refresh = obter_auto_refresh_service()
    
    def on_focus_wrapper(e):
        """Registra início da digitação"""
        if auto_refresh:
            auto_refresh.registrar_campo_digitacao(campo_id)
        
        # Chama callback original se existir
        if hasattr(campo_base, '_original_on_focus'):
            campo_base._original_on_focus(e)
    
    def on_blur_wrapper(e):
        """Registra fim da digitação"""
        if auto_refresh:
            auto_refresh.desregistrar_campo_digitacao(campo_id)
        
        # Chama callback original se existir
        if hasattr(campo_base, '_original_on_blur'):
            campo_base._original_on_blur(e)
    
    # Preserva callbacks originais
    if campo_base.on_focus:
        campo_base._original_on_focus = campo_base.on_focus
    if campo_base.on_blur:
        campo_base._original_on_blur = campo_base.on_blur
    
    # Aplica novos callbacks
    campo_base.on_focus = on_focus_wrapper
    campo_base.on_blur = on_blur_wrapper
    
    return campo_base