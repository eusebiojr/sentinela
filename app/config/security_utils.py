"""
Utilitários de segurança para Sistema Sentinela
Inclui hashing seguro de senhas e verificação
"""
import hashlib
import secrets
import base64
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PasswordSecurity:
    """Classe para operações seguras com senhas"""
    
    # Configurações de segurança
    SALT_LENGTH = 32  # 32 bytes = 256 bits
    ITERATIONS = 100000  # PBKDF2 iterations (OWASP recomenda 100k+)
    HASH_LENGTH = 32  # SHA-256 output
    
    @classmethod
    def generate_salt(cls) -> bytes:
        """Gera salt criptograficamente seguro"""
        return secrets.token_bytes(cls.SALT_LENGTH)
    
    @classmethod
    def hash_password(cls, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Gera hash seguro da senha usando PBKDF2-SHA256
        
        Args:
            password: Senha em texto plano
            salt: Salt opcional (gera novo se None)
            
        Returns:
            Tupla (hash_base64, salt_base64)
        """
        if salt is None:
            salt = cls.generate_salt()
        
        # PBKDF2 com SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            cls.ITERATIONS
        )
        
        # Converte para base64 para armazenamento
        hash_b64 = base64.b64encode(password_hash).decode('ascii')
        salt_b64 = base64.b64encode(salt).decode('ascii')
        
        return hash_b64, salt_b64
    
    @classmethod
    def verify_password(cls, password: str, stored_hash: str, stored_salt: str) -> bool:
        """
        Verifica se senha corresponde ao hash armazenado
        
        Args:
            password: Senha em texto plano
            stored_hash: Hash armazenado (base64)
            stored_salt: Salt armazenado (base64)
            
        Returns:
            True se senha está correta
        """
        try:
            # Decodifica salt e hash armazenados
            salt = base64.b64decode(stored_salt)
            stored_hash_bytes = base64.b64decode(stored_hash)
            
            # Gera hash da senha fornecida com mesmo salt
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                cls.ITERATIONS
            )
            
            # Comparação segura contra timing attacks
            return secrets.compare_digest(password_hash, stored_hash_bytes)
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de senha: {e}")
            return False
    
    @classmethod
    def create_password_record(cls, password: str) -> Dict[str, str]:
        """
        Cria registro completo da senha para armazenamento
        
        Args:
            password: Senha em texto plano
            
        Returns:
            Dict com hash, salt e metadados
        """
        hash_value, salt_value = cls.hash_password(password)
        
        return {
            'hash': hash_value,
            'salt': salt_value,
            'algorithm': 'PBKDF2-SHA256',
            'iterations': cls.ITERATIONS,
            'version': '1.0'
        }
    
    @classmethod
    def is_legacy_password(cls, password_data: Any) -> bool:
        """
        Verifica se senha está em formato legado (texto plano)
        
        Args:
            password_data: Dados da senha do SharePoint
            
        Returns:
            True se é formato legado
        """
        if isinstance(password_data, str):
            # Se é string simples, provavelmente é texto plano
            return not password_data.startswith('{')
        
        if isinstance(password_data, dict):
            # Se tem estrutura mas não tem hash, é legado
            return 'hash' not in password_data
        
        return True
    
    @classmethod
    def migrate_legacy_password(cls, plain_password: str) -> Dict[str, str]:
        """
        Migra senha em texto plano para formato seguro
        
        Args:
            plain_password: Senha em texto plano
            
        Returns:
            Registro de senha seguro
        """
        logger.info("🔄 Migrando senha legado para formato seguro")
        return cls.create_password_record(plain_password)


class SessionSecurity:
    """Utilitários para segurança de sessão"""
    
    @staticmethod
    def generate_session_token() -> str:
        """Gera token de sessão seguro"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Gera token CSRF seguro"""
        return secrets.token_urlsafe(24)


class InputSanitizer:
    """Sanitização segura de inputs"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """
        Sanitiza string para prevenir injeções
        
        Args:
            input_str: String de entrada
            max_length: Comprimento máximo
            
        Returns:
            String sanitizada
        """
        if not isinstance(input_str, str):
            return ""
        
        # Remove caracteres perigosos
        sanitized = input_str.strip()
        
        # Remove caracteres de controle
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        # Limita comprimento
        sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitiza email para validação
        
        Args:
            email: Email de entrada
            
        Returns:
            Email sanitizado
        """
        if not isinstance(email, str):
            return ""
        
        # Remove espaços e converte para minúscula
        email = email.strip().lower()
        
        # Remove caracteres perigosos mas preserva @ e .
        allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789@.-_')
        email = ''.join(char for char in email if char in allowed_chars)
        
        return email[:254]  # RFC limit


# Instâncias globais
password_security = PasswordSecurity()
session_security = SessionSecurity()
input_sanitizer = InputSanitizer()


# Funções de conveniência
def hash_password_secure(password: str) -> Dict[str, str]:
    """Função helper para hash seguro de senha"""
    return password_security.create_password_record(password)


def verify_password_secure(password: str, stored_data: Dict[str, str]) -> bool:
    """Função helper para verificação segura de senha"""
    return password_security.verify_password(
        password, 
        stored_data['hash'], 
        stored_data['salt']
    )


def migrate_plain_password(plain_password: str) -> Dict[str, str]:
    """Função helper para migração de senha legado"""
    return password_security.migrate_legacy_password(plain_password)