"""
Field Monitor Service - Monitora alterações em campos para controlar auto-refresh
Localização: app/services/field_monitor_service.py
"""
from typing import Dict, Any, Set, Callable, Optional
from ..config.logging_config import setup_logger

logger = setup_logger("field_monitor")


class FieldMonitorService:
    """Serviço para monitorar alterações em campos da interface"""
    
    def __init__(self):
        # Campos atualmente alterados
        self.campos_alterados: Set[str] = set()
        
        # Valores originais dos campos (para comparação)
        self.valores_originais: Dict[str, Any] = {}
        
        # Valores atuais dos campos
        self.valores_atuais: Dict[str, Any] = {}
        
        # Callback para notificar mudanças
        self.callback_mudanca_estado = None
        
        # Estado anterior (para detectar transições)
        self.tinha_alteracoes_anterior = False
        
    def configurar_callback(self, callback: Callable[[bool], None]):
        """
        Configura callback que será chamado quando estado de alterações mudar
        
        Args:
            callback: Função que recebe bool (True = tem alterações, False = sem alterações)
        """
        self.callback_mudanca_estado = callback
    
    def registrar_campo_original(self, campo_id: str, valor: Any):
        """
        Registra valor original de um campo
        
        Args:
            campo_id: Identificador único do campo
            valor: Valor original/inicial do campo
        """
        self.valores_originais[campo_id] = valor
        self.valores_atuais[campo_id] = valor
        
        # Remove das alterações se estava marcado
        self.campos_alterados.discard(campo_id)
        
        logger.debug(f"📝 Campo registrado: {campo_id} = '{valor}'")
        self._verificar_mudanca_estado()
    
    def registrar_alteracao(self, campo_id: str, novo_valor: Any):
        """
        Registra alteração em um campo
        
        Args:
            campo_id: Identificador único do campo
            novo_valor: Novo valor do campo
        """
        # Atualiza valor atual
        self.valores_atuais[campo_id] = novo_valor
        
        # Obtém valor original (default para None se não existir)
        valor_original = self.valores_originais.get(campo_id)
        
        # Compara valores para determinar se houve alteração
        if self._valores_diferentes(valor_original, novo_valor):
            # Tem alteração
            if campo_id not in self.campos_alterados:
                self.campos_alterados.add(campo_id)
                logger.debug(f"✏️ Campo alterado: {campo_id} ('{valor_original}' → '{novo_valor}')")
        else:
            # Voltou ao valor original
            if campo_id in self.campos_alterados:
                self.campos_alterados.remove(campo_id)
                logger.debug(f"↶ Campo restaurado: {campo_id} = '{valor_original}'")
        
        self._verificar_mudanca_estado()
    
    def limpar_alteracoes(self):
        """Limpa todas as alterações (quando dados são salvos/cancelados)"""
        if self.campos_alterados:
            logger.info(f"🧹 Limpando {len(self.campos_alterados)} alteração(ões)")
            self.campos_alterados.clear()
            
            # Atualiza valores originais com os atuais
            self.valores_originais.update(self.valores_atuais)
            
            self._verificar_mudanca_estado()
    
    def limpar_campo(self, campo_id: str):
        """
        Limpa alteração de um campo específico
        
        Args:
            campo_id: Identificador do campo a limpar
        """
        if campo_id in self.campos_alterados:
            self.campos_alterados.remove(campo_id)
            logger.debug(f"🧹 Campo limpo: {campo_id}")
            
            # Atualiza valor original com o atual
            if campo_id in self.valores_atuais:
                self.valores_originais[campo_id] = self.valores_atuais[campo_id]
            
            self._verificar_mudanca_estado()
    
    def has_alteracoes_pendentes(self) -> bool:
        """
        Verifica se há alterações pendentes
        
        Returns:
            True se há campos alterados, False caso contrário
        """
        return len(self.campos_alterados) > 0
    
    def obter_campos_alterados(self) -> Set[str]:
        """
        Obtém conjunto de campos alterados
        
        Returns:
            Set com IDs dos campos alterados
        """
        return self.campos_alterados.copy()
    
    def obter_resumo_alteracoes(self) -> Dict[str, Any]:
        """
        Obtém resumo das alterações atuais
        
        Returns:
            Dict com informações sobre alterações
        """
        alteracoes_detalhadas = {}
        
        for campo_id in self.campos_alterados:
            alteracoes_detalhadas[campo_id] = {
                "valor_original": self.valores_originais.get(campo_id),
                "valor_atual": self.valores_atuais.get(campo_id)
            }
        
        return {
            "total_campos_alterados": len(self.campos_alterados),
            "tem_alteracoes": self.has_alteracoes_pendentes(),
            "campos_alterados": list(self.campos_alterados),
            "detalhes": alteracoes_detalhadas
        }
    
    def resetar_campo_para_original(self, campo_id: str):
        """
        Reseta um campo para seu valor original
        
        Args:
            campo_id: Identificador do campo a resetar
        """
        if campo_id in self.valores_originais:
            valor_original = self.valores_originais[campo_id]
            self.valores_atuais[campo_id] = valor_original
            self.campos_alterados.discard(campo_id)
            
            logger.debug(f"↶ Campo resetado: {campo_id} = '{valor_original}'")
            self._verificar_mudanca_estado()
            
            return valor_original
        
        return None
    
    def resetar_todos_campos(self):
        """Reseta todos os campos para valores originais"""
        if self.campos_alterados:
            logger.info(f"↶ Resetando {len(self.campos_alterados)} campo(s)")
            
            for campo_id in list(self.campos_alterados):
                self.resetar_campo_para_original(campo_id)
    
    def _valores_diferentes(self, valor1: Any, valor2: Any) -> bool:
        """
        Compara dois valores considerando tipos e casos especiais
        
        Args:
            valor1: Primeiro valor
            valor2: Segundo valor
            
        Returns:
            True se valores são diferentes, False se iguais
        """
        # Converte None para string vazia para comparação
        val1 = "" if valor1 is None else str(valor1).strip()
        val2 = "" if valor2 is None else str(valor2).strip()
        
        return val1 != val2
    
    def _verificar_mudanca_estado(self):
        """Verifica se estado de alterações mudou e notifica via callback"""
        tem_alteracoes_agora = self.has_alteracoes_pendentes()
        
        # Só notifica se houve mudança de estado
        if tem_alteracoes_agora != self.tinha_alteracoes_anterior:
            self.tinha_alteracoes_anterior = tem_alteracoes_agora
            
            if tem_alteracoes_agora:
                logger.info(f"📝 Alterações detectadas: {len(self.campos_alterados)} campo(s)")
            else:
                logger.info("✅ Todas alterações foram salvas/limpas")
            
            # Chama callback se configurado
            if self.callback_mudanca_estado:
                try:
                    self.callback_mudanca_estado(tem_alteracoes_agora)
                except Exception as e:
                    logger.error(f"❌ Erro ao notificar mudança de estado: {e}")


# Instância global (será inicializada no session_state)
field_monitor_service = None


def obter_field_monitor_service():
    """Obtém instância global do field monitor service"""
    return field_monitor_service


def criar_field_monitor_service():
    """Cria nova instância do field monitor service"""
    return FieldMonitorService()