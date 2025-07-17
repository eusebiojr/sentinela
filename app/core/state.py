"""
Estado centralizado da aplicação Sentinela
"""
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Any, List
from ..utils.data_utils import DataUtils


@dataclass
class AppState:
    """Estado centralizado da aplicação"""
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
    
    def reset_dados(self):
        """Limpa todos os dados (útil para logout)"""
        self.usuario = None
        self.df_usuarios = pd.DataFrame()
        self.df_desvios = pd.DataFrame()
        self.alteracoes_pendentes = {}
        self.estado_expansao = {}
        self.dados_carregados = False
        self.carregamento_em_progresso = False
    
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


# Instância global do estado
app_state = AppState()