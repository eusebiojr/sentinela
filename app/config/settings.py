"""
Configurações centralizadas da aplicação Sentinela
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Set
from .secrets_manager import secrets_manager


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


@dataclass
class BusinessRuleConfig:
    """Regras de negócio configuráveis"""
    # Auto Status Service
    auto_status_limit_hours: int = int(os.getenv("AUTO_STATUS_LIMIT_HOURS", 2))
    
    # Alert thresholds (em minutos)
    alert_warning_minutes: int = int(os.getenv("ALERT_WARNING_MINUTES", 45))
    alert_critical_minutes: int = int(os.getenv("ALERT_CRITICAL_MINUTES", 90))
    
    # Time display threshold
    time_display_day_threshold_hours: int = int(os.getenv("TIME_DISPLAY_DAY_THRESHOLD", 24))


@dataclass
class CacheConfig:
    """Configurações de Cache"""
    # TTL padrão (5 minutos)
    default_ttl_seconds: int = int(os.getenv("CACHE_DEFAULT_TTL", 300))
    
    # TTL específicos por tipo de dados
    usuarios_ttl_seconds: int = int(os.getenv("CACHE_USUARIOS_TTL", 1800))     # 30 min
    configuracoes_ttl_seconds: int = int(os.getenv("CACHE_CONFIG_TTL", 3600)) # 1 hora
    dashboard_ttl_seconds: int = int(os.getenv("CACHE_DASHBOARD_TTL", 180))   # 3 min
    desvios_ttl_seconds: int = int(os.getenv("CACHE_DESVIOS_TTL", 60))        # 1 min
    
    # Tamanho máximo do cache
    max_cache_size: int = int(os.getenv("CACHE_MAX_SIZE", 1000))


@dataclass
class NetworkConfig:
    """Configurações de Rede e Timeouts"""
    # Teams notification timeout
    teams_timeout_seconds: int = int(os.getenv("TEAMS_TIMEOUT", 10))
    
    # SharePoint retry delay
    sharepoint_retry_delay_seconds: int = int(os.getenv("SHAREPOINT_RETRY_DELAY", 2))
    
    # Thread timeout
    thread_join_timeout_seconds: int = int(os.getenv("THREAD_TIMEOUT", 1))


@dataclass
class RefreshConfig:
    """Configurações de Auto-Refresh"""
    # Intervalo de auto-refresh (10 minutos)
    auto_refresh_interval_seconds: int = int(os.getenv("AUTO_REFRESH_INTERVAL", 600))
    
    # Delay para detectar que usuário parou de digitar
    user_typing_delay_seconds: int = int(os.getenv("USER_TYPING_DELAY", 30))


@dataclass
class FileUploadConfig:
    """Configurações de Upload de Arquivos"""
    # Tamanho máximo de arquivo (10MB)
    max_file_size_bytes: int = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
    
    # Extensões permitidas
    allowed_extensions: Set[str] = field(default_factory=lambda: {
        ext.strip() for ext in os.getenv(
            "ALLOWED_EXTENSIONS", 
            ".png,.jpg,.jpeg,.gif,.bmp,.webp"
        ).split(",")
    })


@dataclass
class ValidationConfig:
    """Configurações de Validação"""
    # Password validation
    password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", 6))
    password_max_length: int = int(os.getenv("PASSWORD_MAX_LENGTH", 50))


@dataclass
class UIConfig:
    """Configurações de Interface"""
    # Responsive breakpoints
    mobile_max_width: int = int(os.getenv("MOBILE_MAX_WIDTH", 320))
    mobile_max_height: int = int(os.getenv("MOBILE_MAX_HEIGHT", 400))
    
    # Card dimensions por screen size
    card_width_small: int = int(os.getenv("CARD_WIDTH_SMALL", 180))
    card_width_medium: int = int(os.getenv("CARD_WIDTH_MEDIUM", 200))
    card_width_large: int = int(os.getenv("CARD_WIDTH_LARGE", 220))
    
    # Spacing
    spacing_small: int = int(os.getenv("SPACING_SMALL", 12))
    spacing_medium: int = int(os.getenv("SPACING_MEDIUM", 16))
    spacing_large: int = int(os.getenv("SPACING_LARGE", 20))


@dataclass
class ColorThemeConfig:
    """Configurações de Cores"""
    # Notification colors
    color_error: str = os.getenv("COLOR_ERROR", "#FF4444")
    color_warning: str = os.getenv("COLOR_WARNING", "#FF6B35")
    color_success: str = os.getenv("COLOR_SUCCESS", "#28A745")
    color_info: str = os.getenv("COLOR_INFO", "#17A2B8")


@dataclass
class ExternalServiceConfig:
    """Configurações de Serviços Externos"""
    # Icons8 service
    icons8_base_url: str = os.getenv("ICONS8_BASE_URL", "https://img.icons8.com/color/48/000000")
    
    # Technical support icon
    support_icon_url: str = os.getenv("SUPPORT_ICON_URL", "https://img.icons8.com/color/48/000000/technical-support.png")


def load_config() -> AppConfig:
    """Carrega configurações usando o gerenciador de secrets seguro"""
    
    # Inicializa o gerenciador de secrets
    secrets_manager.initialize()
    
    # Valida secrets obrigatórios
    if not secrets_manager.validate_required_secrets():
        raise ValueError("Secrets obrigatórios não encontrados. Verifique variáveis de ambiente ou arquivo .secrets.json")
    
    return AppConfig(
        site_url=os.getenv(
            "SITE_URL", 
            "https://suzano.sharepoint.com/sites/Controleoperacional"
        ),
        usuarios_list=os.getenv("USUARIOS_LIST", "UsuariosPainelTorre"),
        desvios_list=os.getenv("DESVIOS_LIST", "Desvios"),
        username_sp=secrets_manager.get_secret("USERNAME_SP"),
        password_sp=secrets_manager.get_secret("PASSWORD_SP"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080))
    )


# Instâncias globais de configuração
config = load_config()

# Configurações específicas por categoria
business_rules = BusinessRuleConfig()
cache_config = CacheConfig()
network_config = NetworkConfig()
refresh_config = RefreshConfig()
file_upload_config = FileUploadConfig()
validation_config = ValidationConfig()
ui_config = UIConfig()
color_theme = ColorThemeConfig()
external_services = ExternalServiceConfig()