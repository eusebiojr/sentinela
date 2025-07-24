"""
Serviço de Processamento Automático de Status - Não Tratado
"""
import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import List, Tuple, Dict, Any
from ..config.logging_config import setup_logger
from ..services.sharepoint_client import SharePointClient

logger = setup_logger("auto_status_service")


class AutoStatusService:
    """Serviço para processamento automático de status 'Não Tratado'"""
    
    # Limite de tempo em horas para marcar como "Não Tratado"
    LIMITE_HORAS = 2
    
    @staticmethod
    def obter_timezone_brasilia():
        """Retorna timezone de Brasília"""
        return pytz.timezone("America/Campo_Grande")
    
    @staticmethod
    def calcular_tempo_decorrido_evento(data_entrada_str: str) -> float:
        """
        Calcula tempo decorrido desde a entrada do evento
        
        Args:
            data_entrada_str: Data/hora de entrada formatada
            
        Returns:
            float: Horas decorridas ou 0 se inválido
        """
        if not data_entrada_str or str(data_entrada_str).strip() == "":
            return 0
        
        try:
            # Timezone de Brasília
            tz_brasilia = AutoStatusService.obter_timezone_brasilia()
            agora = datetime.now(tz_brasilia)
            
            # Parse da data de entrada
            if "/" in str(data_entrada_str):
                # Formato: "24/07/2025 15:30"
                dt_entrada = datetime.strptime(str(data_entrada_str).strip(), "%d/%m/%Y %H:%M")
                dt_entrada = tz_brasilia.localize(dt_entrada)
            else:
                # Formato ISO ou outro
                dt_entrada = pd.to_datetime(data_entrada_str, errors="coerce")
                if pd.isnull(dt_entrada):
                    return 0
                
                if dt_entrada.tzinfo is None:
                    dt_entrada = tz_brasilia.localize(dt_entrada)
                else:
                    dt_entrada = dt_entrada.tz_convert(tz_brasilia)
            
            # Calcula diferença em horas
            diferenca = agora - dt_entrada
            horas = diferenca.total_seconds() / 3600
            
            return max(0, horas)  # Não retorna valores negativos
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular tempo decorrido: {e}")
            return 0
    
    @staticmethod
    def identificar_eventos_para_nao_tratado(df_desvios: pd.DataFrame) -> pd.DataFrame:
        """
        Identifica eventos que devem ser marcados como "Não Tratado"
        
        Args:
            df_desvios: DataFrame com todos os desvios
            
        Returns:
            DataFrame com eventos que precisam ser marcados
        """
        if df_desvios.empty:
            return pd.DataFrame()
        
        # Filtra apenas eventos que não estão finalizados
        eventos_ativos = df_desvios[
            ~df_desvios["Status"].isin(["Aprovado", "Não Tratado"])
        ].copy()
        
        if eventos_ativos.empty:
            return pd.DataFrame()
        
        # Adiciona coluna de tempo decorrido
        eventos_ativos["tempo_decorrido_horas"] = eventos_ativos["Data/Hora Entrada"].apply(
            AutoStatusService.calcular_tempo_decorrido_evento
        )
        
        # Filtra eventos com mais de 2 horas
        eventos_expirados = eventos_ativos[
            eventos_ativos["tempo_decorrido_horas"] > AutoStatusService.LIMITE_HORAS
        ]
        
        if not eventos_expirados.empty:
            logger.info(f"🔍 Encontrados {len(eventos_expirados)} registros para marcar como 'Não Tratado'")
        
        return eventos_expirados
    
    @staticmethod
    def processar_nao_tratado_automatico(df_eventos_expirados: pd.DataFrame) -> int:
        """
        Processa mudança de status para "Não Tratado" automaticamente
        
        Args:
            df_eventos_expirados: DataFrame com eventos expirados
            
        Returns:
            int: Número de registros atualizados
        """
        if df_eventos_expirados.empty:
            return 0
        
        try:
            # Prepara dados para auditoria automática
            tz_brasilia = AutoStatusService.obter_timezone_brasilia()
            timestamp_atual = datetime.now(tz_brasilia).strftime("%Y-%m-%dT%H:%M:%S")
            
            # Dados para atualização
            dados_atualizacao = {
                "Status": "Não Tratado",
                "Aprovado_por": "sistema@suzano.com.br",
                "Data_Aprovacao": timestamp_atual
            }
            
            # Prepara lista de atualizações
            atualizacoes_lote = []
            for _, row in df_eventos_expirados.iterrows():
                item_id = int(row["ID"])
                atualizacoes_lote.append((item_id, dados_atualizacao.copy()))
            
            # Executa atualizações em lote
            if atualizacoes_lote:
                logger.info(f"📤 Enviando {len(atualizacoes_lote)} atualizações para SharePoint...")
                sucessos = SharePointClient.atualizar_lote(atualizacoes_lote)
                
                if sucessos > 0:
                    logger.info(f"✅ {sucessos} evento(s) marcado(s) como 'Não Tratado' automaticamente")
                else:
                    logger.warning(f"⚠️ Falha ao atualizar eventos no SharePoint")
                
                return sucessos
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar 'Não Tratado' automático: {e}")
            return 0
        
        return 0
    
    @staticmethod
    def executar_verificacao_automatica(df_desvios: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Executa verificação completa e processamento automático
        
        Args:
            df_desvios: DataFrame com todos os desvios
            
        Returns:
            Tuple[DataFrame filtrado, int atualizações realizadas]
        """
        logger.info("🔄 Iniciando verificação automática de status 'Não Tratado'...")
        
        # 1. Identifica eventos expirados
        eventos_expirados = AutoStatusService.identificar_eventos_para_nao_tratado(df_desvios)
        
        # 2. Processa mudanças se houver eventos expirados
        atualizacoes_realizadas = 0
        if not eventos_expirados.empty:
            atualizacoes_realizadas = AutoStatusService.processar_nao_tratado_automatico(eventos_expirados)
            
            # 3. Atualiza status no DataFrame local (para não esperar próximo carregamento)
            if atualizacoes_realizadas > 0:
                # Marca eventos processados como "Não Tratado" no DataFrame atual
                ids_processados = eventos_expirados["ID"].tolist()
                df_desvios.loc[df_desvios["ID"].isin(ids_processados), "Status"] = "Não Tratado"
        
        # 4. Filtra eventos "Não Tratado" do resultado
        df_filtrado = df_desvios[df_desvios["Status"] != "Não Tratado"].copy()
        
        registros_filtrados = len(df_desvios) - len(df_filtrado)
        if registros_filtrados > 0:
            logger.info(f"🚫 {registros_filtrados} evento(s) 'Não Tratado' filtrado(s) da interface")
        
        logger.info("✅ Verificação automática de status concluída")
        
        return df_filtrado, atualizacoes_realizadas


# Instância global do serviço
auto_status_service = AutoStatusService()


# Funções de conveniência
def executar_verificacao_automatica(df_desvios: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Executa verificação automática de status"""
    return auto_status_service.executar_verificacao_automatica(df_desvios)


def filtrar_nao_tratados(df_desvios: pd.DataFrame) -> pd.DataFrame:
    """Filtra eventos 'Não Tratado' do DataFrame"""
    if df_desvios.empty:
        return df_desvios
    
    return df_desvios[df_desvios["Status"] != "Não Tratado"].copy()


def calcular_tempo_decorrido(data_entrada_str: str) -> float:
    """Calcula tempo decorrido de um evento"""
    return auto_status_service.calcular_tempo_decorrido_evento(data_entrada_str)