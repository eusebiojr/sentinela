"""
Estado por sessão - VERSÃO ATUALIZADA COM AUTO-REFRESH
Localização: app/core/session_state.py
"""
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from ..utils.data_utils import DataUtils
import uuid
import threading
from ..config.logging_config import setup_logger

logger = setup_logger("session_state")


@dataclass
class SessionState:
    """Estado isolado por sessão/usuário"""
    # Identificação única da sessão
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    thread_id: int = field(default_factory=threading.get_ident)
    
    # Dados do usuário logado
    usuario: Dict[str, Any] = None
    
    # DataFrames principais
    df_usuarios: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_desvios: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    # Controle de alterações
    alteracoes_pendentes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Estado da interface
    estado_expansao: Dict[str, bool] = field(default_factory=dict)
    
    # Status de carregamento
    dados_carregados: bool = False
    carregamento_em_progresso: bool = False
    
    # NOVO: Services de auto-refresh e monitoring
    field_monitor_service: Any = None
    auto_refresh_habilitado: bool = False
    
    def __post_init__(self):
        """Inicialização da sessão"""
        logger.info(f"🔐 [NOVA SESSÃO] ID: {self.session_id}, Thread: {self.thread_id}")
        
        # Inicializa field monitor service
        self._inicializar_field_monitor()
    
    def _inicializar_field_monitor(self):
        """Inicializa o serviço de monitoramento de campos"""
        try:
            from ..services.field_monitor_service import criar_field_monitor_service
            self.field_monitor_service = criar_field_monitor_service()
            
            # Configura callback para integração com auto-refresh
            self.field_monitor_service.configurar_callback(self._on_alteracoes_mudaram)
            
            logger.info(f"✅ Field Monitor inicializado para sessão {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Field Monitor: {e}")
    
    def _on_alteracoes_mudaram(self, tem_alteracoes: bool):
        """Callback quando estado de alterações muda"""
        try:
            from ..services.auto_refresh_service import obter_auto_refresh_service
            
            auto_refresh = obter_auto_refresh_service()
            if auto_refresh and self.auto_refresh_habilitado:
                if tem_alteracoes:
                    auto_refresh.pausar_timer("campos preenchidos")
                else:
                    auto_refresh.retomar_timer()
                    
        except Exception as e:
            logger.error(f"❌ Erro ao controlar auto-refresh: {e}")
    
    def configurar_auto_refresh(self, habilitado: bool):
        """
        Configura auto-refresh para esta sessão
        
        Args:
            habilitado: True para habilitar, False para desabilitar
        """
        self.auto_refresh_habilitado = habilitado
        self.salvar_configuracao_usuario('auto_refresh', habilitado)
        
        try:
            from ..services.auto_refresh_service import obter_auto_refresh_service
            
            auto_refresh = obter_auto_refresh_service()
            if auto_refresh:
                auto_refresh.habilitar_usuario(habilitado)
                logger.info(f"🔄 Auto-refresh {'habilitado' if habilitado else 'desabilitado'} para sessão {self.session_id}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao configurar auto-refresh: {e}")
    
    def registrar_campo_original(self, campo_id: str, valor: Any):
        """Registra valor original de um campo"""
        if self.field_monitor_service:
            self.field_monitor_service.registrar_campo_original(campo_id, valor)
    
    def registrar_alteracao_campo(self, campo_id: str, novo_valor: Any):
        """Registra alteração em um campo"""
        if self.field_monitor_service:
            self.field_monitor_service.registrar_alteracao(campo_id, novo_valor)
    
    def limpar_alteracoes_campos(self):
        """Limpa todas as alterações de campos"""
        if self.field_monitor_service:
            self.field_monitor_service.limpar_alteracoes()
    
    def has_campos_alterados(self) -> bool:
        """Verifica se há campos alterados"""
        if self.field_monitor_service:
            return self.field_monitor_service.has_alteracoes_pendentes()
        return False
    
    def obter_resumo_alteracoes_campos(self) -> Dict[str, Any]:
        """Obtém resumo de alterações nos campos"""
        if self.field_monitor_service:
            return self.field_monitor_service.obter_resumo_alteracoes()
        return {"total_campos_alterados": 0, "tem_alteracoes": False}
    
    def reset_dados(self):
        """Limpa todos os dados (útil para logout)"""
        logger.info(f"🔄 [RESET SESSÃO {self.session_id}] Usuário antes: {self.get_nome_usuario()}")
        
        # Para auto-refresh se estiver ativo
        self.configurar_auto_refresh(False)
        
        # Limpa alterações de campos
        if self.field_monitor_service:
            self.field_monitor_service.limpar_alteracoes()
        
        self.usuario = None
        self.df_usuarios = pd.DataFrame()
        self.df_desvios = pd.DataFrame()
        self.alteracoes_pendentes = {}
        self.estado_expansao = {}
        self.dados_carregados = False
        self.carregamento_em_progresso = False
        
        logger.info(f"✅ [RESET COMPLETO] Sessão {self.session_id} limpa")
    
    def is_usuario_logado(self) -> bool:
        """Verifica se há usuário logado"""
        return self.usuario is not None
    
    def get_perfil_usuario(self) -> str:
        """Retorna o perfil do usuário logado"""
        if not self.is_usuario_logado():
            return ""
        return self.usuario.get("Perfil", "").strip().lower()
    
    def get_areas_usuario(self) -> List[str]:
        """Retorna as áreas do usuário logado"""
        if not self.is_usuario_logado():
            return []
        return DataUtils.obter_areas_usuario(self.usuario)
    
    def get_nome_usuario(self) -> str:
        """Retorna o nome de exibição do usuário"""
        if not self.is_usuario_logado():
            return ""
        return (self.usuario.get('NomeExibicao') or 
                self.usuario.get('nomeexibicao') or 
                self.usuario.get('Nome') or 
                self.usuario.get('nome') or 
                "Usuário")
    
    def get_usuario_atual(self) -> Dict[str, Any]:
        """Retorna dados completos do usuário atual"""
        return self.usuario if self.usuario else {}
    
    def get_id_usuario(self):
        """Retorna ID do usuário atual"""
        return self.usuario.get('ID') if self.usuario else None
    
    def atualizar_usuario(self, novos_dados: dict):
        """Atualiza dados do usuário com log"""
        usuario_antes = self.get_id_usuario()
        
        if self.usuario:
            self.usuario.update(novos_dados)
        else:
            self.usuario = novos_dados.copy()
            
        logger.info(f"👤 [USUÁRIO ATUALIZADO] Sessão: {self.session_id}, "
                   f"Antes: {usuario_antes}, Depois: {self.get_id_usuario()}")
    
    def salvar_configuracao_usuario(self, chave: str, valor):
        """Salva uma configuração específica do usuário"""
        if not self.usuario:
            self.usuario = {}
        
        if 'configuracoes' not in self.usuario:
            self.usuario['configuracoes'] = {}
        
        self.usuario['configuracoes'][chave] = valor
        logger.info(f"📝 [CONFIG] Sessão {self.session_id}: {chave} = {valor}")
        
        # NOVO: Trata configuração específica de auto-refresh
        if chave == 'auto_refresh':
            self.configurar_auto_refresh(valor)
    
    def obter_configuracao_usuario(self, chave: str, padrao=None):
        """Obtém uma configuração específica do usuário"""
        if self.usuario and 'configuracoes' in self.usuario:
            return self.usuario['configuracoes'].get(chave, padrao)
        return padrao
    
    def atualizar_alteracao(self, chave: str, campo: str, valor: Any):
        """Registra uma alteração pendente"""
        if chave not in self.alteracoes_pendentes:
            self.alteracoes_pendentes[chave] = {}
        self.alteracoes_pendentes[chave][campo] = valor
    
    def limpar_alteracoes_evento(self, evento: str):
        """Remove alterações pendentes de um evento específico"""
        chaves_para_remover = [k for k in self.alteracoes_pendentes.keys() 
                              if k.startswith(f"{evento}_")]
        for chave in chaves_para_remover:
            del self.alteracoes_pendentes[chave]
    
    def has_alteracoes_pendentes(self) -> bool:
        """Verifica se há alterações não salvas (campos OU eventos)"""
        return (len(self.alteracoes_pendentes) > 0 or 
                self.has_campos_alterados())


def get_session_state(page) -> SessionState:
    """
    Obtém ou cria o estado da sessão atual
    
    Args:
        page: Objeto page do Flet
        
    Returns:
        SessionState: Estado isolado da sessão
    """
    if not hasattr(page, '_session_state'):
        page._session_state = SessionState()
        logger.info(f"📌 [ESTADO CRIADO] Nova sessão para página {id(page)}")
    
    return page._session_state


def salvar_configuracoes_usuario(page, config: dict):
    """
    Salva configurações do usuário na sessão
    
    Args:
        page: Objeto page do Flet
        config: Dicionário com configurações
    """
    try:
        session = get_session_state(page)
        for chave, valor in config.items():
            session.salvar_configuracao_usuario(chave, valor)
        logger.info(f"✅ Configurações salvas na sessão {session.session_id}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar configurações: {e}")
        raise e