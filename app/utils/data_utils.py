"""
Utilitários para processamento de dados
"""
import pandas as pd
import pytz
import re
from datetime import datetime
from ..services.data_formatter import DataFormatter


class DataUtils:
    """Utilitários para processamento e manipulação de dados"""
    
    @staticmethod
    def processar_desvios(df: pd.DataFrame) -> pd.DataFrame:
        """Processa e normaliza dados de desvios"""
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

        # Renomeia colunas para padronização
        rename_map = {
            "Title": "Titulo",
            "Ponto_de_Interesse": "PontodeInteresse",
            "Data_Hora_Entrada": "Data/Hora Entrada",
            "Data Entrada": "Data/Hora Entrada"
        }
        df = df.rename(columns=rename_map)

        # Adiciona colunas necessárias se não existirem
        colunas_necessarias = ["Observacoes", "Status", "Motivo"]
        for col in colunas_necessarias:
            if col not in df.columns:
                df[col] = ""

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