"""
Gerenciador de Secrets Seguro para Sistema Sentinela
Suporta múltiplas fontes: env vars, arquivos, Google Secret Manager
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """Gerenciador centralizado de secrets com múltiplas fontes"""
    
    def __init__(self):
        self._secrets_cache: Dict[str, str] = {}
        self._initialized = False
    
    def initialize(self):
        """Inicializa o gerenciador de secrets"""
        if self._initialized:
            return
            
        try:
            # Ordem de prioridade: env vars -> arquivo local -> Google Secret Manager
            self._load_from_environment()
            self._load_from_file()
            self._load_from_gcp_secrets()
            
            self._initialized = True
            logger.info("✅ Secrets Manager inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Secrets Manager: {e}")
            raise
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """
        Obtém um secret de forma segura
        
        Args:
            key: Nome do secret
            required: Se True, lança exceção se não encontrar
            
        Returns:
            Valor do secret ou None se não encontrado e not required
        """
        if not self._initialized:
            self.initialize()
        
        # Verifica cache primeiro
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        # Busca em diferentes fontes
        value = self._get_from_sources(key)
        
        if value:
            self._secrets_cache[key] = value
            return value
        
        if required:
            raise ValueError(f"Secret obrigatório não encontrado: {key}")
        
        return None
    
    def _load_from_environment(self):
        """Carrega secrets de variáveis de ambiente"""
        env_secrets = [
            "USERNAME_SP",
            "PASSWORD_SP", 
            "TEAMS_WEBHOOK_URL",
            "GOOGLE_CLOUD_PROJECT"
        ]
        
        for secret in env_secrets:
            value = os.getenv(secret)
            if value:
                self._secrets_cache[secret] = value
                logger.debug(f"✅ Secret carregado do env: {secret}")
    
    def _load_from_file(self):
        """Carrega secrets de arquivo local (desenvolvimento)"""
        secrets_file = Path(".secrets.json")
        
        if not secrets_file.exists():
            logger.debug("📄 Arquivo .secrets.json não encontrado")
            return
        
        try:
            with open(secrets_file, 'r') as f:
                file_secrets = json.load(f)
            
            for key, value in file_secrets.items():
                if key not in self._secrets_cache:  # Env vars têm prioridade
                    self._secrets_cache[key] = value
                    logger.debug(f"✅ Secret carregado do arquivo: {key}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao ler arquivo de secrets: {e}")
    
    def _load_from_gcp_secrets(self):
        """Carrega secrets do Google Secret Manager (produção)"""
        try:
            from google.cloud import secretmanager
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                logger.debug("🔍 GOOGLE_CLOUD_PROJECT não definido, pulando GCP secrets")
                return
            
            client = secretmanager.SecretManagerServiceClient()
            
            # Lista de secrets esperados no GCP
            gcp_secrets = [
                "sharepoint-username",
                "sharepoint-password",
                "teams-webhook-url"
            ]
            
            for secret_name in gcp_secrets:
                try:
                    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                    response = client.access_secret_version(request={"name": secret_path})
                    
                    secret_value = response.payload.data.decode("UTF-8")
                    
                    # Mapeia nomes GCP para nomes internos
                    internal_key = self._map_gcp_secret_name(secret_name)
                    
                    if internal_key not in self._secrets_cache:
                        self._secrets_cache[internal_key] = secret_value
                        logger.debug(f"✅ Secret carregado do GCP: {secret_name}")
                        
                except Exception as e:
                    logger.debug(f"⚠️ Secret GCP não encontrado {secret_name}: {e}")
                    
        except ImportError:
            logger.debug("📦 Google Cloud SDK não disponível")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao acessar GCP Secret Manager: {e}")
    
    def _get_from_sources(self, key: str) -> Optional[str]:
        """Busca secret em todas as fontes disponíveis"""
        # 1. Variável de ambiente
        value = os.getenv(key)
        if value:
            return value
        
        # 2. Cache (já carregado de arquivos/GCP)
        return self._secrets_cache.get(key)
    
    def _map_gcp_secret_name(self, gcp_name: str) -> str:
        """Mapeia nomes de secrets do GCP para nomes internos"""
        mapping = {
            "sharepoint-username": "USERNAME_SP",
            "sharepoint-password": "PASSWORD_SP", 
            "teams-webhook-url": "TEAMS_WEBHOOK_URL"
        }
        return mapping.get(gcp_name, gcp_name.upper().replace("-", "_"))
    
    def validate_required_secrets(self) -> bool:
        """
        Valida se todos os secrets obrigatórios estão disponíveis
        
        Returns:
            True se todos os secrets estão OK
        """
        required_secrets = [
            "USERNAME_SP",
            "PASSWORD_SP"
        ]
        
        missing_secrets = []
        
        for secret in required_secrets:
            try:
                value = self.get_secret(secret, required=True)
                if not value or len(value.strip()) == 0:
                    missing_secrets.append(secret)
            except ValueError:
                missing_secrets.append(secret)
        
        if missing_secrets:
            logger.error(f"❌ Secrets obrigatórios ausentes: {missing_secrets}")
            return False
        
        logger.info("✅ Todos os secrets obrigatórios estão disponíveis")
        return True
    
    def get_connection_string(self) -> Dict[str, str]:
        """Retorna credenciais do SharePoint de forma segura"""
        return {
            "username": self.get_secret("USERNAME_SP"),
            "password": self.get_secret("PASSWORD_SP"),
            "site_url": os.getenv("SITE_URL", "https://suzano.sharepoint.com/sites/Controleoperacional")
        }
    
    def clear_cache(self):
        """Limpa cache de secrets (útil para rotação)"""
        self._secrets_cache.clear()
        self._initialized = False
        logger.info("🧹 Cache de secrets limpo")


# Instância global do gerenciador
secrets_manager = SecretsManager()


def get_secret(key: str, required: bool = True) -> Optional[str]:
    """Função helper para obter secrets"""
    return secrets_manager.get_secret(key, required)


def validate_secrets() -> bool:
    """Função helper para validar secrets"""
    return secrets_manager.validate_required_secrets()