"""
Utilitários para processamento de dados - COM SUPORTE ÀS COLUNAS DE AUDITORIA
"""
import pandas as pd
import pytz
import re
from datetime import datetime
from ..services.data_formatter import DataFormatter


class DataUtils:
    """Utilitários para processamento e manipulação de dados com auditoria"""
    
    @staticmethod
    def processar_desvios(df: pd.DataFrame) -> pd.DataFrame:
        """Processa e normaliza dados de desvios incluindo colunas de auditoria"""
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

        # NOVO: Processa colunas de auditoria de datas
        colunas_data_auditoria = ["Data_Preenchimento", "Data_Aprovacao"]
        for coluna in colunas_data_auditoria:
            if coluna in df.columns:
                df[coluna] = pd.to_datetime(df[coluna], errors="coerce", utc=True)
                try:
                    df[coluna] = df[coluna].dt.tz_convert("America/Campo_Grande")
                except:
                    pass

        # Renomeia colunas para padronização
        rename_map = {
            "Title": "Titulo",
            "Ponto_de_Interesse": "PontodeInteresse",
            "Data_Hora_Entrada": "Data/Hora Entrada",
            "Data Entrada": "Data/Hora Entrada"
        }
        df = df.rename(columns=rename_map)

        # ATUALIZADO: Adiciona todas as colunas necessárias incluindo auditoria
        colunas_necessarias = [
            "Observacoes", "Status", "Motivo",
            "Preenchido_por", "Data_Preenchimento",  # NOVO: Colunas de auditoria preenchimento
            "Aprovado_por", "Data_Aprovacao"         # NOVO: Colunas de auditoria aprovação
        ]
        
        for col in colunas_necessarias:
            if col not in df.columns:
                if col in ["Data_Preenchimento", "Data_Aprovacao"]:
                    df[col] = pd.NaT  # Para colunas de data
                else:
                    df[col] = ""      # Para colunas de texto

        return df

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
        NOVO: Extrai informações de auditoria de um DataFrame
        
        Args:
            df: DataFrame com os registros
            
        Returns:
            Dict com informações de auditoria consolidadas
        """
        if df.empty:
            return {
                "tem_auditoria": False,
                "preenchimento": {},
                "aprovacao": {}
            }
        
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
            "aprovacao": aprovacao
        }
    
    @staticmethod
    def filtrar_por_periodo_auditoria(
        df: pd.DataFrame, 
        data_inicio: datetime = None, 
        data_fim: datetime = None,
        tipo_auditoria: str = "ambos"
    ) -> pd.DataFrame:
        """
        NOVO: Filtra registros por período de auditoria
        
        Args:
            df: DataFrame para filtrar
            data_inicio: Data de início do período
            data_fim: Data de fim do período
            tipo_auditoria: "preenchimento", "aprovacao" ou "ambos"
            
        Returns:
            DataFrame filtrado
        """
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
        NOVO: Calcula estatísticas de auditoria
        
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
                "periodo_atividade": {}
            }
        
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
            "periodo_atividade": periodo_atividade
        }
    
    @staticmethod
    def validar_integridade_auditoria(df: pd.DataFrame) -> dict:
        """
        NOVO: Valida integridade dos dados de auditoria
        
        Args:
            df: DataFrame para validar
            
        Returns:
            Dict com resultado da validação
        """
        problemas = []
        
        if df.empty:
            return {"valido": True, "problemas": []}
        
        # Verifica registros com preenchimento sem data
        preenchidos_sem_data = df[
            (df["Preenchido_por"].notnull()) & 
            (df["Preenchido_por"] != "") & 
            (df["Data_Preenchimento"].isna())
        ]
        
        if not preenchidos_sem_data.empty:
            problemas.append(f"Encontrados {len(preenchidos_sem_data)} registros com usuário de preenchimento mas sem data")
        
        # Verifica registros com aprovação sem data
        aprovados_sem_data = df[
            (df["Aprovado_por"].notnull()) & 
            (df["Aprovado_por"] != "") & 
            (df["Data_Aprovacao"].isna())
        ]
        
        if not aprovados_sem_data.empty:
            problemas.append(f"Encontrados {len(aprovados_sem_data)} registros com usuário de aprovação mas sem data")
        
        # Verifica registros aprovados sem auditoria
        status_aprovado_sem_auditoria = df[
            (df["Status"].isin(["Aprovado", "Reprovado"])) &
            ((df["Aprovado_por"].isna()) | (df["Aprovado_por"] == ""))
        ]
        
        if not status_aprovado_sem_auditoria.empty:
            problemas.append(f"Encontrados {len(status_aprovado_sem_auditoria)} registros com status aprovado/reprovado mas sem auditoria")
        
        return {
            "valido": len(problemas) == 0,
            "problemas": problemas,
            "total_verificado": len(df)
        }