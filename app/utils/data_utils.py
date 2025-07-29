"""
Utilitários para processamento de dados - MIGRADO PARA VALIDAÇÕES CENTRALIZADAS
"""
import pandas as pd
import pytz
import re
from datetime import datetime
from ..services.data_formatter import DataFormatter

# 🚀 NOVA IMPORTAÇÃO - Usa sistema centralizado para validações de auditoria
from ..validators import business_validator


class DataUtils:
    """Utilitários para processamento e manipulação de dados com validações centralizadas"""
    
    @staticmethod
    def processar_desvios(df: pd.DataFrame) -> pd.DataFrame:
        """Processa e normaliza dados de desvios incluindo verificação automática de status"""
        if df.empty:
            return df

        # Normaliza tipos de alerta
        if "Tipo_Alerta" in df.columns:
            df["Tipo_Alerta"] = df["Tipo_Alerta"].str.strip().str.lower().replace({
                "informativo": "Alerta Informativo",
                "alerta informativo": "Alerta Informativo",
                "n1": "Tratativa N1", "tratativa n1": "Tratativa N1",
                "n2": "Tratativa N2", "tratativa n2": "Tratativa N2",
                "n3": "Tratativa N3", "tratativa n3": "Tratativa N3",
                "n4": "Tratativa N4", "tratativa n4": "Tratativa N4"
            })
        else:
            df["Tipo_Alerta"] = "Alerta Informativo"

        # Processa datas de previsão
        if "Previsao_Liberacao" in df.columns:
            df["Previsao_Liberacao"] = pd.to_datetime(df["Previsao_Liberacao"], errors="coerce", utc=True)
            try:
                df["Previsao_Liberacao"] = df["Previsao_Liberacao"].dt.tz_convert("America/Campo_Grande")
            except:
                pass

        # Processa colunas de auditoria de datas + Created
        colunas_data_auditoria = ["Data_Preenchimento", "Data_Aprovacao", "Criado"]
        for coluna in colunas_data_auditoria:
            if coluna in df.columns:
                df[coluna] = pd.to_datetime(df[coluna], errors="coerce", utc=True)
                try:
                    df[coluna] = df[coluna].dt.tz_convert("America/Campo_Grande")
                except:
                    pass

        # Renomeia colunas para padronização - ADICIONADO Created → Criado
        rename_map = {
            "Title": "Titulo",
            "Created": "Criado",
            "Ponto_de_Interesse": "PontodeInteresse",
            "Data_Hora_Entrada": "Data/Hora Entrada",
            "Data Entrada": "Data/Hora Entrada"
        }
        df = df.rename(columns=rename_map)

        # Adiciona todas as colunas necessárias incluindo auditoria
        colunas_necessarias = [
            "Observacoes", "Status", "Motivo",
            "Preenchido_por", "Data_Preenchimento",
            "Aprovado_por", "Data_Aprovacao"
        ]
        
        for col in colunas_necessarias:
            if col not in df.columns:
                if col in ["Data_Preenchimento", "Data_Aprovacao"]:
                    df[col] = pd.NaT
                else:
                    df[col] = ""

        # NOVO: Executa verificação automática de status "Não Tratado"
        try:
            from ..services.auto_status_service import executar_verificacao_automatica
            df_processado, atualizacoes = executar_verificacao_automatica(df)
            
            if atualizacoes > 0:
                print(f"🔄 Sistema processou {atualizacoes} evento(s) como 'Não Tratado' automaticamente")
            
            return df_processado
            
        except Exception as e:
            print(f"⚠️ Erro na verificação automática de status: {e}")
            # Em caso de erro, apenas filtra os "Não Tratado" existentes
            return df[df["Status"] != "Não Tratado"].copy() if "Status" in df.columns else df

    @staticmethod
    def parse_titulo(titulo: str) -> tuple:
        """Parse básico do título do evento (versão simplificada)"""
        partes = titulo.split('_')
        if len(partes) < 5:
            return "", "", ""

        tipo = partes[-3]
        poi_raw = partes[1].upper()
        data_str = partes[-2]
        hora_str = partes[-1]

        # Mapeamento de POIs
        poi_map = {
            "PAAGUACLARA": "P.A. Água Clara",
            "CARREGAMENTOFABRICARRP": "Fábrica RRP",
            "OFICINAJSL": "Oficina JSL",
            "TERMINALINOCENCIA": "Terminal Inocência"
        }
        poi_amigavel = next((v for k, v in poi_map.items() if k in poi_raw), poi_raw.title())

        # Mapeamento de tipos
        tipo_map = {
            "Informativo": "Alerta Informativo",
            "N1": "Tratativa N1", "N2": "Tratativa N2",
            "N3": "Tratativa N3", "N4": "Tratativa N4"
        }
        tipo_amigavel = tipo_map.get(tipo, tipo)

        # Processa data/hora
        try:
            datahora = datetime.strptime(data_str + "_" + hora_str, "%d%m%Y_%H%M%S")
            datahora_fmt = datahora.strftime("%d/%m %H:00")
        except:
            datahora_fmt = f"{data_str} {hora_str}"

        return tipo_amigavel, poi_amigavel, datahora_fmt

    @staticmethod
    def obter_areas_usuario(usuario: dict) -> list:
        """Extrai e normaliza áreas do usuário"""
        areas = usuario.get("Area", "")
        if isinstance(areas, list):
            return [a.strip().lower() for a in areas if a]
        if isinstance(areas, str):
            return [a.strip().lower() for a in re.split(r'[;\n]+', areas) if a.strip()]
        return []

    @staticmethod
    def formatar_data(valor) -> str:
        """Wrapper para formatação de data (delegação para DataFormatter)"""
        return DataFormatter.formatar_data_exibicao(valor)
    
    @staticmethod
    def extrair_informacoes_auditoria(df: pd.DataFrame) -> dict:
        """
        🚀 MIGRADO - Extrai informações de auditoria usando validação centralizada
        
        Args:
            df: DataFrame com os registros
            
        Returns:
            Dict com informações de auditoria consolidadas
        """
        if df.empty:
            return {
                "tem_auditoria": False,
                "preenchimento": {},
                "aprovacao": {},
                "integridade_ok": False
            }
        
        # 🚀 USA VALIDADOR CENTRALIZADO para verificar integridade
        validation_result = business_validator.validate_integridade_auditoria(df)
        
        # Pega primeiro registro (todos do evento têm mesmo histórico)
        primeiro_registro = df.iloc[0]
        
        # Informações de preenchimento
        preenchimento = {
            "usuario": primeiro_registro.get("Preenchido_por", ""),
            "data_raw": primeiro_registro.get("Data_Preenchimento", ""),
            "data_formatada": ""
        }
        
        if preenchimento["data_raw"] and pd.notnull(preenchimento["data_raw"]):
            preenchimento["data_formatada"] = DataFormatter.formatar_data_exibicao(
                preenchimento["data_raw"]
            )
        
        # Informações de aprovação
        aprovacao = {
            "usuario": primeiro_registro.get("Aprovado_por", ""),
            "data_raw": primeiro_registro.get("Data_Aprovacao", ""),
            "data_formatada": "",
            "status": primeiro_registro.get("Status", "")
        }
        
        if aprovacao["data_raw"] and pd.notnull(aprovacao["data_raw"]):
            aprovacao["data_formatada"] = DataFormatter.formatar_data_exibicao(
                aprovacao["data_raw"]
            )
        
        # Determina se tem auditoria
        tem_auditoria = bool(
            preenchimento["usuario"] or 
            aprovacao["usuario"]
        )
        
        return {
            "tem_auditoria": tem_auditoria,
            "preenchimento": preenchimento,
            "aprovacao": aprovacao,
            "integridade_ok": validation_result.valid,  # 🚀 NOVO: Status de integridade
            "problemas_integridade": validation_result.errors  # 🚀 NOVO: Lista de problemas
        }
    
    @staticmethod
    def filtrar_por_periodo_auditoria(
        df: pd.DataFrame, 
        data_inicio: datetime = None, 
        data_fim: datetime = None,
        tipo_auditoria: str = "ambos"
    ) -> pd.DataFrame:
        """Filtra registros por período de auditoria (sem alterações)"""
        if df.empty:
            return df
        
        df_filtrado = df.copy()
        
        # Aplica filtros de data conforme tipo solicitado
        if tipo_auditoria in ["preenchimento", "ambos"] and "Data_Preenchimento" in df.columns:
            if data_inicio:
                df_filtrado = df_filtrado[
                    (df_filtrado["Data_Preenchimento"].isna()) |
                    (df_filtrado["Data_Preenchimento"] >= data_inicio)
                ]
            
            if data_fim:
                df_filtrado = df_filtrado[
                    (df_filtrado["Data_Preenchimento"].isna()) |
                    (df_filtrado["Data_Preenchimento"] <= data_fim)
                ]
        
        if tipo_auditoria in ["aprovacao", "ambos"] and "Data_Aprovacao" in df.columns:
            if data_inicio:
                df_filtrado = df_filtrado[
                    (df_filtrado["Data_Aprovacao"].isna()) |
                    (df_filtrado["Data_Aprovacao"] >= data_inicio)
                ]
            
            if data_fim:
                df_filtrado = df_filtrado[
                    (df_filtrado["Data_Aprovacao"].isna()) |
                    (df_filtrado["Data_Aprovacao"] <= data_fim)
                ]
        
        return df_filtrado
    
    @staticmethod
    def obter_estatisticas_auditoria(df: pd.DataFrame) -> dict:
        """
        🚀 MELHORADO - Calcula estatísticas de auditoria com validação centralizada
        
        Args:
            df: DataFrame com registros
            
        Returns:
            Dict com estatísticas de auditoria
        """
        if df.empty:
            return {
                "total_registros": 0,
                "preenchidos": 0,
                "aprovados": 0,
                "reprovados": 0,
                "pendentes": 0,
                "usuarios_ativos": [],
                "periodo_atividade": {},
                "integridade_ok": True,
                "problemas_encontrados": 0
            }
        
        # 🚀 USA VALIDADOR CENTRALIZADO para verificar integridade
        validation_result = business_validator.validate_integridade_auditoria(df)
        
        total_registros = len(df)
        
        # Contadores por status
        preenchidos = len(df[df["Preenchido_por"].notnull() & (df["Preenchido_por"] != "")])
        aprovados = len(df[df["Status"] == "Aprovado"])
        reprovados = len(df[df["Status"] == "Reprovado"])
        pendentes = total_registros - preenchidos
        
        # Usuários ativos (preenchimento e aprovação)
        usuarios_preenchimento = df[df["Preenchido_por"].notnull() & (df["Preenchido_por"] != "")]["Preenchido_por"].unique().tolist()
        usuarios_aprovacao = df[df["Aprovado_por"].notnull() & (df["Aprovado_por"] != "")]["Aprovado_por"].unique().tolist()
        
        usuarios_ativos = list(set(usuarios_preenchimento + usuarios_aprovacao))
        
        # Período de atividade
        periodo_atividade = {}
        
        # Período de preenchimentos
        datas_preenchimento = df[df["Data_Preenchimento"].notnull()]["Data_Preenchimento"]
        if not datas_preenchimento.empty:
            periodo_atividade["preenchimento"] = {
                "primeiro": datas_preenchimento.min(),
                "ultimo": datas_preenchimento.max()
            }
        
        # Período de aprovações
        datas_aprovacao = df[df["Data_Aprovacao"].notnull()]["Data_Aprovacao"]
        if not datas_aprovacao.empty:
            periodo_atividade["aprovacao"] = {
                "primeiro": datas_aprovacao.min(),
                "ultimo": datas_aprovacao.max()
            }
        
        return {
            "total_registros": total_registros,
            "preenchidos": preenchidos,
            "aprovados": aprovados,
            "reprovados": reprovados,
            "pendentes": pendentes,
            "usuarios_ativos": usuarios_ativos,
            "periodo_atividade": periodo_atividade,
            "integridade_ok": validation_result.valid,  # 🚀 NOVO: Status de integridade
            "problemas_encontrados": len(validation_result.errors)  # 🚀 NOVO: Quantidade de problemas
        }
    
    @staticmethod
    def validar_integridade_auditoria(df: pd.DataFrame) -> dict:
        """
        🚀 MIGRADO - Valida integridade dos dados de auditoria usando sistema centralizado
        
        Args:
            df: DataFrame para validar
            
        Returns:
            Dict com resultado da validação (formato compatível com código existente)
        """
        # 🚀 USA VALIDADOR CENTRALIZADO - Substitui lógica inline antiga
        validation_result = business_validator.validate_integridade_auditoria(df)
        
        return {
            "valido": validation_result.valid,
            "problemas": validation_result.errors,
            "total_verificado": validation_result.data.get("total_verificado", len(df) if not df.empty else 0)
        }


# 🚀 FUNÇÕES DE CONVENIÊNCIA - Para uso direto com validações centralizadas

def validar_integridade_auditoria_rapido(df: pd.DataFrame) -> bool:
    """Validação rápida de integridade de auditoria"""
    if df.empty:
        return True
    
    validation_result = business_validator.validate_integridade_auditoria(df)
    return validation_result.valid

def obter_problemas_auditoria(df: pd.DataFrame) -> list:
    """Obtém lista de problemas de auditoria encontrados"""
    if df.empty:
        return []
    
    validation_result = business_validator.validate_integridade_auditoria(df)
    return validation_result.errors

def extrair_auditoria_com_validacao(df: pd.DataFrame) -> dict:
    """Extrai informações de auditoria com validação integrada"""
    return DataUtils.extrair_informacoes_auditoria(df)

def calcular_estatisticas_com_integridade(df: pd.DataFrame) -> dict:
    """Calcula estatísticas incluindo validação de integridade"""
    return DataUtils.obter_estatisticas_auditoria(df)