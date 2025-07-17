"""
Configurações centralizadas da aplicação Sentinela
"""
import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class AppConfig:
    """Configurações centralizadas da aplicação"""
    # SharePoint
    site_url: str
    usuarios_list: str
    desvios_list: str
    username_sp: str
    password_sp: str
    
    # UI
    window_width: int = 1400
    window_maximized: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    # Server (novo para GCP)
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8080))  # Cloud Run usa PORT env var
    
    # Motivos por POI
    motivos_poi: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.motivos_poi is None:
            self.motivos_poi = {
                "PA Agua Clara": [
                    "Atestado Motorista",
                    "Brecha na escala", 
                    "Ciclo Antecipado - Aguardando Motorista", 
                    "Falta Motorista",
                    "Outros", 
                    "Refeição", 
                    "Socorro Mecânico"
                ],
                "Manutenção": [
                    "Corretiva",
                    "Falta Mecânico",
                    "Falta Material", 
                    "Inspeção", 
                    "Lavagem", 
                    "Preventiva", 
                    "Outros"
                ],
                "Terminal": [
                    "Chegada em Comboio", 
                    "Falta de Espaço", 
                    "Falta de Máquina", 
                    "Falta de Operador", 
                    "Janela de Descarga",
                    "Prioridade Ferrovia",
                    "Outros"
                ],
                "Fábrica": [
                    "Chegada em Comboio", 
                    "Emissão Nota Fiscal", 
                    "Falta de Máquina", 
                    "Falta de Material", 
                    "Falta de Operador", 
                    "Janela Carregamento", 
                    "Outros",
                    "Restrição de Tráfego"
                ]
            }


def load_config() -> AppConfig:
    """Carrega configurações de variáveis de ambiente ou valores padrão"""
    return AppConfig(
        site_url=os.getenv(
            "SITE_URL", 
            "https://suzano.sharepoint.com/sites/Controleoperacional"
        ),
        usuarios_list=os.getenv("USUARIOS_LIST", "UsuariosPainelTorre"),
        desvios_list=os.getenv("DESVIOS_LIST", "Desvios"),
        username_sp=os.getenv("USERNAME_SP", "eusebioagj@suzano.com.br"),
        password_sp=os.getenv("PASSWORD_SP", "290422@Cc"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080))
    )


# Instância global de configuração
config = load_config()