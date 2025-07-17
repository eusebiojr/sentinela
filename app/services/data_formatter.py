"""
Formatador de dados - conversões e formatações
"""
import pandas as pd
import pytz
from datetime import datetime
from typing import Any


class DataFormatter:
    """Classe especializada para formatação de dados"""
    
    @staticmethod
    def formatar_valor_sharepoint(valor: Any, campo: str = None) -> Any:
        """Formata valor para envio ao SharePoint"""
        if valor == "— Selecione —":
            return ""
        
        if campo == "Previsao_Liberacao":
            if valor is None or str(valor).strip() == "" or str(valor).lower() in ("none", "nat"):
                return None
            
            if isinstance(valor, pd.Timestamp) or isinstance(valor, datetime):
                return valor.strftime("%Y-%m-%dT%H:%M:%S")
            
            try:
                if "/" in str(valor):
                    dt = datetime.strptime(str(valor).strip(), "%d/%m/%Y %H:%M")
                    return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except:
                pass
            
            return str(valor).strip() if valor else None
        else:
            if valor is None or str(valor).lower() in ("none", "nat"):
                return ""
            return str(valor).strip()
    
    @staticmethod
    def formatar_data_exibicao(valor: Any) -> str:
        """Formata data para exibição na interface"""
        if pd.isnull(valor) or str(valor).strip().lower() in ("none", ""):
            return ""
        
        try:
            if isinstance(valor, str):
                try:
                    dt = datetime.strptime(valor, "%d/%m/%Y %H:%M")
                    dt = pytz.timezone("America/Campo_Grande").localize(dt)
                except ValueError:
                    dt = pd.to_datetime(valor, errors="coerce", utc=True)
            else:
                dt = pd.to_datetime(valor, errors="coerce", utc=True)
            
            if pd.isnull(dt):
                return str(valor)
            
            if dt.tzinfo is None:
                dt = pytz.timezone("America/Campo_Grande").localize(dt)
            else:
                dt = dt.tz_convert("America/Campo_Grande")
            
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return str(valor)
    
    @staticmethod
    def formatar_tempo_decorrido(horas: float) -> str:
        """Formata tempo decorrido para exibição"""
        if horas == 0:
            return "0h"
        elif horas < 1:
            minutos = int(horas * 60)
            return f"{minutos}min"
        elif horas < 24:
            return f"{horas:.1f}h"
        else:
            dias = int(horas // 24)
            horas_restantes = horas % 24
            if horas_restantes < 1:
                return f"{dias}d"
            else:
                return f"{dias}d {horas_restantes:.0f}h"
    
    @staticmethod
    def safe_str(valor: Any) -> str:
        """Converte valor para string de forma segura"""
        if pd.isnull(valor) or valor is None:
            return ""
        return str(valor)