"""
Estado por sessão - CORREÇÃO DO BUG DE TROCA DE USUÁRIO
Cada usuário terá seu próprio estado isolado
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
    
    def __post_init__(self):
        """Log de criação da sessão"""
        logger.info(f"🔐 [NOVA SESSÃO] ID: {self.session_id}, Thread: {self.thread_id}")
    
    def reset_dados(self):
        """Limpa todos os dados (útil para logout)"""
        logger.info(f"🔄 [RESET SESSÃO {self.session_id}] Usuário antes: {self.get_nome_usuario()}")
        
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
        """Verifica se há alterações não salvas"""
        return len(self.alteracoes_pendentes) > 0


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