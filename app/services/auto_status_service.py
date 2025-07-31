"""
Serviço de Processamento Automático de Status - Não Tratado
MODIFICADO: Usa data/hora do desvio extraída do título ao invés da data de criação
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
    def calcular_tempo_decorrido_por_titulo(titulo: str, data_criacao_fallback: str = None) -> float:
        """
        NOVO: Calcula tempo decorrido desde o EVENTO (extraído do título)
        
        Args:
            titulo: Título do evento (ex: TLS_PACelulose_N1_31072025_020000)
            data_criacao_fallback: Data de criação para fallback se parse falhar
            
        Returns:
            float: Horas decorridas desde o evento real
        """
        if not titulo or str(titulo).strip() == "":
            return AutoStatusService.calcular_tempo_decorrido_evento(data_criacao_fallback) if data_criacao_fallback else 0
        
        try:
            # Importa location_processor para reutilizar lógica existente
            try:
                from .location_processor import location_processor
                evento_info = location_processor.parse_titulo_com_localizacao(titulo)
                data_evento = evento_info.get("data_evento")
                
                if data_evento:
                    # Calcula diferença com agora
                    tz_brasilia = AutoStatusService.obter_timezone_brasilia()
                    agora = datetime.now(tz_brasilia)
                    
                    # Garante que data_evento tem timezone
                    if data_evento.tzinfo is None:
                        data_evento = tz_brasilia.localize(data_evento)
                    else:
                        data_evento = data_evento.astimezone(tz_brasilia)
                    
                    diferenca = agora - data_evento
                    horas = diferenca.total_seconds() / 3600
                    
                    logger.debug(f"🕒 Evento {titulo}: {horas:.1f}h desde o desvio real")
                    return max(0, horas)
                    
            except ImportError:
                logger.warning("⚠️ location_processor não disponível, usando parse manual")
            
            # FALLBACK: Parse manual do título se location_processor não disponível
            return AutoStatusService._parse_manual_titulo(titulo, data_criacao_fallback)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair data do título '{titulo}': {e}")
            
            # Fallback para data de criação
            if data_criacao_fallback:
                return AutoStatusService.calcular_tempo_decorrido_evento(data_criacao_fallback)
            
            return 0
    
    @staticmethod
    def _parse_manual_titulo(titulo: str, data_criacao_fallback: str = None) -> float:
        """
        Parse manual do título no formato: LOCALIZACAO_POI_TIPO_DDMMAAAA_HHMMSS
        
        Args:
            titulo: Título do evento
            data_criacao_fallback: Fallback se parse falhar
            
        Returns:
            float: Horas decorridas
        """
        try:
            partes = titulo.split('_')
            if len(partes) < 5:
                raise ValueError("Formato de título inválido")
            
            data_str = partes[-2]  # DDMMAAAA
            hora_str = partes[-1]  # HHMMSS
            
            # Parse da data: DDMMAAAA -> DD/MM/AAAA
            if len(data_str) == 8 and len(hora_str) == 6:
                dia = data_str[:2]
                mes = data_str[2:4]
                ano = data_str[4:8]
                
                hora = hora_str[:2]
                minuto = hora_str[2:4]
                segundo = hora_str[4:6]
                
                # Cria datetime do evento
                tz_brasilia = AutoStatusService.obter_timezone_brasilia()
                data_evento = datetime(
                    int(ano), int(mes), int(dia),
                    int(hora), int(minuto), int(segundo)
                )
                data_evento = tz_brasilia.localize(data_evento)
                
                # Calcula diferença
                agora = datetime.now(tz_brasilia)
                diferenca = agora - data_evento
                horas = diferenca.total_seconds() / 3600
                
                logger.debug(f"🕒 Parse manual - Evento {titulo}: {horas:.1f}h desde {data_evento}")
                return max(0, horas)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro no parse manual do título '{titulo}': {e}")
        
        # Fallback final para data de criação
        if data_criacao_fallback:
            return AutoStatusService.calcular_tempo_decorrido_evento(data_criacao_fallback)
        
        return 0
    
    @staticmethod
    def calcular_tempo_decorrido_evento(data_criacao: str) -> float:
        """
        MANTIDO: Calcula tempo decorrido desde a CRIAÇÃO do registro (fallback)
        
        Args:
            data_criacao: Data/hora de criação do registro no SharePoint
            
        Returns:
            float: Horas decorridas desde a criação ou 0 se inválido
        """
        if not data_criacao or str(data_criacao).strip() == "":
            return 0
        
        try:
            # Timezone de Brasília
            tz_brasilia = AutoStatusService.obter_timezone_brasilia()
            agora = datetime.now(tz_brasilia)
            
            # Parse da data de criação
            if "/" in str(data_criacao):
                # Formato brasileiro: "24/07/2025 15:30"
                dt_criacao = datetime.strptime(str(data_criacao).strip(), "%d/%m/%Y %H:%M")
                dt_criacao = tz_brasilia.localize(dt_criacao)
            else:
                # Formato ISO do SharePoint: "2025-07-24T15:30:00Z"
                dt_criacao = pd.to_datetime(data_criacao, errors="coerce")
                if pd.isnull(dt_criacao):
                    return 0
                
                if dt_criacao.tzinfo is None:
                    dt_criacao = tz_brasilia.localize(dt_criacao)
                else:
                    dt_criacao = dt_criacao.tz_convert(tz_brasilia)
            
            # Calcula diferença em horas
            diferenca = agora - dt_criacao
            horas = diferenca.total_seconds() / 3600
            
            return max(0, horas)  # Não retorna valores negativos
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular tempo desde criação: {e}")
            return 0
    
    @staticmethod
    def identificar_eventos_para_nao_tratado(df_desvios: pd.DataFrame) -> pd.DataFrame:
        """
        MODIFICADO: Identifica eventos usando data/hora do DESVIO extraída do título
        
        Args:
            df_desvios: DataFrame com todos os desvios
            
        Returns:
            DataFrame com eventos que precisam ser marcados
        """
        if df_desvios.empty:
            return pd.DataFrame()
        
        # Verifica se colunas necessárias existem
        colunas_necessarias = ["Titulo", "Criado"]
        for col in colunas_necessarias:
            if col not in df_desvios.columns:
                logger.warning(f"⚠️ Coluna '{col}' não encontrada no DataFrame.")
                return pd.DataFrame()
        
        # Filtra apenas eventos que não estão finalizados
        eventos_ativos = df_desvios[
            ~df_desvios["Status"].isin(["Aprovado", "Não Tratado"])
        ].copy()
        
        if eventos_ativos.empty:
            return pd.DataFrame()
        
        # NOVA LÓGICA: Calcula tempo baseado no título (data do desvio)
        def calcular_tempo_por_linha(row):
            titulo = row.get("Titulo", "")
            data_criacao = row.get("Criado", "")
            return AutoStatusService.calcular_tempo_decorrido_por_titulo(titulo, data_criacao)
        
        eventos_ativos["tempo_decorrido_horas"] = eventos_ativos.apply(calcular_tempo_por_linha, axis=1)
        
        # Filtra eventos com mais de 2 horas desde o DESVIO
        eventos_expirados = eventos_ativos[
            eventos_ativos["tempo_decorrido_horas"] > AutoStatusService.LIMITE_HORAS
        ]
        
        if not eventos_expirados.empty:
            logger.info(f"🔍 Encontrados {len(eventos_expirados)} registros para marcar como 'Não Tratado' (baseado na data do DESVIO)")
            
            # Log adicional para debug (mostra diferença entre data do desvio e criação)
            for _, row in eventos_expirados.head(3).iterrows():
                titulo = row.get("Titulo", "N/A")
                criado = row.get("Criado", "N/A")
                tempo_desvio = row.get("tempo_decorrido_horas", 0)
                tempo_criacao = AutoStatusService.calcular_tempo_decorrido_evento(criado)
                
                logger.debug(f"📋 Evento: {titulo}")
                logger.debug(f"   ⏰ Tempo desde desvio: {tempo_desvio:.1f}h")
                logger.debug(f"   📅 Tempo desde criação: {tempo_criacao:.1f}h")
        
        return eventos_expirados
    
    @staticmethod
    def processar_nao_tratado_automatico(df_eventos_expirados: pd.DataFrame) -> int:
        """
        MANTIDO: Processa mudança de status para "Não Tratado" automaticamente
        
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
                    logger.info(f"✅ {sucessos} evento(s) marcado(s) como 'Não Tratado' automaticamente (baseado na data do DESVIO)")
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
        MANTIDO: Executa verificação completa e processamento automático
        
        Args:
            df_desvios: DataFrame com todos os desvios
            
        Returns:
            Tuple[DataFrame filtrado, int atualizações realizadas]
        """
        logger.info("🔄 Iniciando verificação automática de status 'Não Tratado' (usando data do desvio)...")
        
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
        
        logger.info("✅ Verificação automática de status concluída (usando data do desvio)")
        
        return df_filtrado, atualizacoes_realizadas


# Instância global do serviço
auto_status_service = AutoStatusService()


# Funções de conveniência - ATUALIZADAS
def executar_verificacao_automatica(df_desvios: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Executa verificação automática de status"""
    return auto_status_service.executar_verificacao_automatica(df_desvios)


def filtrar_nao_tratados(df_desvios: pd.DataFrame) -> pd.DataFrame:
    """Filtra eventos 'Não Tratado' do DataFrame"""
    if df_desvios.empty:
        return df_desvios
    
    return df_desvios[df_desvios["Status"] != "Não Tratado"].copy()


def calcular_tempo_decorrido(data_criacao: str) -> float:
    """MANTIDO: Calcula tempo decorrido desde a criação de um evento (para compatibilidade)"""
    return auto_status_service.calcular_tempo_decorrido_evento(data_criacao)


def calcular_tempo_decorrido_por_titulo(titulo: str, data_criacao_fallback: str = None) -> float:
    """NOVO: Calcula tempo decorrido desde o evento extraído do título"""
    return auto_status_service.calcular_tempo_decorrido_por_titulo(titulo, data_criacao_fallback)