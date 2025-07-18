"""
Configurações do SharePoint para o Sistema Sentinela - Suzano
"""
import os
from typing import Dict, Any

class SharePointConfig:
    """Configurações centralizadas do SharePoint - Suzano"""
    
    # Configurações de conexão - Suzano
    SITE_URL = os.getenv('SHAREPOINT_SITE_URL', 'https://suzano.sharepoint.com/sites/Controleoperacional')
    USERNAME = os.getenv('SHAREPOINT_USERNAME', 'usuario@suzano.com')
    PASSWORD = os.getenv('SHAREPOINT_PASSWORD', 'senha_do_usuario')
    
    # Configurações das listas - Suzano
    LISTA_USUARIOS = os.getenv('SHAREPOINT_LISTA_USUARIOS', 'UsuariosPainelTorre')
    LISTA_DESVIOS = os.getenv('SHAREPOINT_LISTA_DESVIOS', 'Desvios')
    
    # Configurações de segurança (simplificadas conforme solicitado)
    USAR_CRIPTOGRAFIA = False  # Senha em texto plano conforme estrutura atual
    
    # Política de senhas (simplificada)
    SENHA_MIN_CARACTERES = 6
    SENHA_MAX_CARACTERES = 50
    SENHA_REQUER_LETRA = False
    SENHA_REQUER_NUMERO = False
    SENHA_REQUER_ESPECIAL = False
    
    # Configurações de log
    HABILITAR_LOG_SENHA = True
    NIVEL_LOG = 'INFO'
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        Retorna configurações como dicionário
        
        Returns:
            Dict com todas as configurações
        """
        return {
            'site_url': cls.SITE_URL,
            'username': cls.USERNAME,
            'password': cls.PASSWORD,
            'lista_usuarios': cls.LISTA_USUARIOS,
            'lista_desvios': cls.LISTA_DESVIOS,
            'usar_criptografia': cls.USAR_CRIPTOGRAFIA,
            'senha_config': {
                'min_caracteres': cls.SENHA_MIN_CARACTERES,
                'max_caracteres': cls.SENHA_MAX_CARACTERES,
                'requer_letra': cls.SENHA_REQUER_LETRA,
                'requer_numero': cls.SENHA_REQUER_NUMERO,
                'requer_especial': cls.SENHA_REQUER_ESPECIAL
            },
            'log': {
                'habilitar_log_senha': cls.HABILITAR_LOG_SENHA,
                'nivel': cls.NIVEL_LOG
            }
        }
    
    @classmethod
    def validar_configuracoes(cls) -> bool:
        """
        Valida se as configurações estão corretas
        
        Returns:
            bool: True se configurações válidas
        """
        required_configs = [
            cls.SITE_URL,
            cls.USERNAME,
            cls.PASSWORD,
            cls.LISTA_USUARIOS
        ]
        
        return all(config and config.strip() for config in required_configs)
    
    @classmethod
    def get_campos_sharepoint(cls) -> Dict[str, str]:
        """
        Mapeia campos da aplicação para campos do SharePoint - Suzano
        
        Returns:
            Dict com mapeamento de campos
        """
        return {
            # Campos de usuário - conforme lista UsuariosPainelTorre
            'usuario_id': 'ID',
            'email': 'Email',
            'senha': 'Senha',  # Senha em texto plano
            'nome': 'NomeExibicao',
            'perfil': 'Perfil',
            'area': 'Area',
            
            # Campos de desvio (manter estrutura original)
            'desvio_id': 'ID',
            'numero_evento': 'NumeroEvento',
            'data_evento': 'DataEvento',
            'area_desvio': 'Area',
            'descricao': 'Descricao',
            'status': 'Status',
            'responsavel': 'Responsavel'
        }


# Instância das configurações
config = SharePointConfig()

# Validação automática
if not config.validar_configuracoes():
    print("⚠️ ATENÇÃO: Configurações do SharePoint incompletas!")
    print("Configure as variáveis de ambiente ou edite sharepoint_config.py")
else:
    print("✅ Configurações do SharePoint Suzano validadas")