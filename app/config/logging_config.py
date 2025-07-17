"""
Configuração de logging personalizada para o Sentinela
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path


class CustomFormatter(logging.Formatter):
    """Formatter personalizado com cores e timestamps"""
    
    # Cores para diferentes níveis
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Adiciona timestamp brasileiro
        record.timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Formato da mensagem
        log_format = f"[{record.timestamp}] {record.levelname}: {record.getMessage()}"
        
        # Adiciona cor se for terminal
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            log_format = f"{color}{log_format}{self.COLORS['RESET']}"
        
        return log_format


def setup_logger(name: str = "sentinela", level: str = "INFO") -> logging.Logger:
    """Configura e retorna logger personalizado"""
    logger = logging.getLogger(name)
    
    # Limpa handlers existentes para evitar conflitos
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Configura nível baseado no parâmetro
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Desabilita propagação para evitar duplicação
    logger.propagate = False

    # Handler para console
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())

    # Força flush imediato dos logs
    original_emit = console_handler.emit

    def emit_with_flush(record):
        original_emit(record)
        sys.stderr.flush()
    
    console_handler.emit = emit_with_flush
    logger.addHandler(console_handler)

    # Handler para arquivo (apenas se não for Cloud Run)
    if os.getenv("ENVIRONMENT") != "production":
        setup_file_logging(logger)

    return logger


def setup_file_logging(logger: logging.Logger):
    """Configura logging em arquivo para desenvolvimento local"""
    try:
        # Cria diretório de logs se não existir
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Nome do arquivo de log com timestamp
        log_filename = f"sentinela_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = logs_dir / log_filename

        # Handler de arquivo
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Log inicial informando onde encontrar os logs
        logger.info(f"📁 Logs sendo salvos em: {log_filepath}")
        
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível configurar logging em arquivo: {e}")


def setup_cloud_logging():
    """Configura logging para Google Cloud (opcional)"""
    try:
        # Apenas se estiver em produção e cloud logging disponível
        if os.getenv("ENVIRONMENT") == "production":
            try:
                from google.cloud import logging as cloud_logging
                
                # Configura client do Cloud Logging
                client = cloud_logging.Client()
                client.setup_logging()
                
                return True
            except ImportError:
                # Cloud logging não disponível, usa logging padrão
                pass
    except Exception:
        pass
    
    return False