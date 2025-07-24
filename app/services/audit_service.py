"""
Serviço de Auditoria - Rastreamento de preenchimentos e aprovações - VERSÃO CORRIGIDA COM SESSÃO
"""
from datetime import datetime
import pytz
from typing import Dict, Any, List, Tuple
from ..core.session_state import get_session_state
from ..config.logging_config import setup_logger

logger = setup_logger("audit_service")


class AuditService:
    """Serviço responsável pelo controle de auditoria do sistema"""
    
    @staticmethod
    def obter_timestamp_brasilia() -> str:
        """Retorna timestamp atual no formato SharePoint (Brasília)"""
        agora = datetime.now(pytz.timezone("America/Campo_Grande"))
        return agora.strftime("%Y-%m-%dT%H:%M:%S")
    
    @staticmethod
    def obter_email_usuario_atual(page) -> str:
        """Obtém email do usuário logado"""
        session = get_session_state(page)
        usuario = session.get_usuario_atual()
        if not usuario:
            return "sistema@suzano.com.br"
        
        # Tenta diferentes campos possíveis para email
        campos_email = ['Email', 'email', 'EMAIL', 'UserName', 'Login']
        
        for campo in campos_email:
            email = usuario.get(campo, '')
            if email and isinstance(email, str) and '@' in email:
                return email.strip().lower()
        
        # Fallback: se não encontrar email, usa ID + domínio
        user_id = usuario.get('ID', 'usuario')
        return f"user{user_id}@suzano.com.br"
    
    @staticmethod
    def adicionar_auditoria_preenchimento(page, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adiciona dados de auditoria para preenchimento - SEMPRE atualiza timestamp
        
        Args:
            page: Página do Flet para acessar sessão
            dados: Dados que serão enviados ao SharePoint
            
        Returns:
            Dict com dados + auditoria de preenchimento
        """
        email_usuario = AuditService.obter_email_usuario_atual(page)
        timestamp = AuditService.obter_timestamp_brasilia()
        
        # Copia dados originais
        dados_com_auditoria = dados.copy()
        
        # SEMPRE adiciona/atualiza dados de preenchimento
        dados_com_auditoria.update({
            "Preenchido_por": email_usuario,
            "Data_Preenchimento": timestamp
        })
        
        logger.info(f"📝 Auditoria preenchimento: {email_usuario} em {timestamp}")
        
        return dados_com_auditoria
    
    @staticmethod
    def adicionar_auditoria_aprovacao(
        page,
        dados: Dict[str, Any],
        status: str, 
        justificativa: str = None
    ) -> Dict[str, Any]:
        """
        Adiciona dados de auditoria para aprovação/reprovação
        
        Args:
            page: Página do Flet para acessar sessão
            dados: Dados base
            status: "Aprovado" ou "Reprovado"
            justificativa: Justificativa da reprovação (opcional)
            
        Returns:
            Dict com dados + auditoria de aprovação
        """
        email_usuario = AuditService.obter_email_usuario_atual(page)
        timestamp = AuditService.obter_timestamp_brasilia()
        
        # Copia dados base
        dados_com_auditoria = dados.copy()
        
        # Adiciona dados de aprovação
        dados_com_auditoria.update({
            "Status": status,
            "Aprovado_por": email_usuario,
            "Data_Aprovacao": timestamp
        })
        
        # Adiciona justificativa se for reprovação
        if status == "Reprovado" and justificativa:
            dados_com_auditoria["Reprova"] = justificativa
        
        logger.info(f"✅ Auditoria {status.lower()}: {email_usuario} em {timestamp}")
        
        return dados_com_auditoria
    
    @staticmethod
    def processar_preenchimento_com_auditoria(
        page,
        evento: str,
        df_evento,
        alteracoes_pendentes: Dict[str, Dict[str, Any]]
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Processa preenchimento SEMPRE com auditoria atualizada
        
        Args:
            page: Página do Flet para acessar sessão
            evento: Nome do evento
            df_evento: DataFrame do evento
            alteracoes_pendentes: Alterações pendentes do estado
            
        Returns:
            Lista de tuplas (item_id, dados) para atualização no SharePoint
        """
        atualizacoes_lote = []
        
        # Determina status do evento após alterações
        from ..services.evento_processor import EventoProcessor
        status_evento = EventoProcessor.calcular_status_evento(df_evento, alteracoes_pendentes)
        
        # Processa cada registro com alterações
        for _, row in df_evento.iterrows():
            row_id = str(row["ID"]).strip()
            chave_alteracao = f"{evento}_{row_id}"
            
            if chave_alteracao in alteracoes_pendentes:
                alteracoes = alteracoes_pendentes[chave_alteracao]
                
                # Valores atuais do DataFrame
                valor_motivo_df = row.get("Motivo", "")
                valor_previsao_df = row.get("Previsao_Liberacao", "")
                valor_obs_df = row.get("Observacoes", "")
                
                # Aplica alterações pendentes
                valor_motivo_final = alteracoes.get("Motivo", valor_motivo_df)
                valor_previsao_final = alteracoes.get("Previsao_Liberacao", valor_previsao_df)
                valor_obs_final = alteracoes.get("Observacoes", valor_obs_df)
                
                # Prepara dados base
                from ..services.data_formatter import DataFormatter
                dados_base = {
                    "Motivo": DataFormatter.formatar_valor_sharepoint(valor_motivo_final),
                    "Previsao_Liberacao": DataFormatter.formatar_valor_sharepoint(
                        valor_previsao_final, "Previsao_Liberacao"
                    ),
                    "Observacoes": DataFormatter.formatar_valor_sharepoint(valor_obs_final),
                    "Status": status_evento
                }
                
                # SEMPRE adiciona auditoria de preenchimento para qualquer alteração
                dados_finais = AuditService.adicionar_auditoria_preenchimento(page, dados_base)
                
                atualizacoes_lote.append((int(row_id), dados_finais))
        
        logger.info(f"📊 Preparadas {len(atualizacoes_lote)} atualizações com auditoria atualizada")
        return atualizacoes_lote
    
    @staticmethod
    def processar_aprovacao_com_auditoria(
        page,
        df_evento,
        status: str,
        justificativa: str = None
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Processa aprovação/reprovação com auditoria
        
        Args:
            page: Página do Flet para acessar sessão
            df_evento: DataFrame do evento
            status: "Aprovado" ou "Reprovado"
            justificativa: Justificativa da reprovação
            
        Returns:
            Lista de tuplas (item_id, dados) para atualização
        """
        atualizacoes_aprovacao = []
        
        # Dados base (podem ser vazios para aprovação)
        dados_base = {}
        
        # Adiciona auditoria de aprovação
        dados_finais = AuditService.adicionar_auditoria_aprovacao(page, dados_base, status, justificativa)
        
        # Aplica para todos os registros do evento
        for _, row in df_evento.iterrows():
            atualizacoes_aprovacao.append((int(row["ID"]), dados_finais))
        
        logger.info(f"📊 Preparadas {len(atualizacoes_aprovacao)} {status.lower()}ções com auditoria")
        return atualizacoes_aprovacao


# Instância global do serviço
audit_service = AuditService()


# Funções de conveniência para uso direto - CORRIGIDAS
def processar_preenchimento_com_auditoria(page, evento: str, df_evento, alteracoes_pendentes: Dict[str, Dict[str, Any]]) -> List[Tuple[int, Dict[str, Any]]]:
    """Processa preenchimento com auditoria sempre atualizada"""
    return audit_service.processar_preenchimento_com_auditoria(page, evento, df_evento, alteracoes_pendentes)


def processar_aprovacao_com_auditoria(page, df_evento, status: str, justificativa: str = None) -> List[Tuple[int, Dict[str, Any]]]:
    """Processa aprovação com auditoria"""
    return audit_service.processar_aprovacao_com_auditoria(page, df_evento, status, justificativa)


def obter_usuario_logado(page) -> str:
    """Obtém email do usuário logado"""
    return audit_service.obter_email_usuario_atual(page)


def obter_timestamp_atual() -> str:
    """Obtém timestamp atual formatado"""
    return audit_service.obter_timestamp_brasilia()