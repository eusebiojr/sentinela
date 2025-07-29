"""
Sistema de Validação Centralizado - Sentinela Suzano - VERSÃO FINAL COMPLETA
Centraliza todas as validações da aplicação em um padrão único
"""

from .base import ValidationResult, BaseValidator, ValidationError
from .field_validator import FieldValidator
from .business_validator import BusinessValidator
from .security_validator import SecurityValidator

# Instâncias globais para uso direto
field_validator = FieldValidator()
business_validator = BusinessValidator()
security_validator = SecurityValidator()

# Funções de conveniência para compatibilidade com código existente
def validate_field(field_type: str, value, **kwargs) -> ValidationResult:
    """
    Valida um campo específico
    
    Args:
        field_type: Tipo do campo ('email', 'date', 'required', etc.)
        value: Valor a ser validado
        **kwargs: Parâmetros adicionais específicos do validador
        
    Returns:
        ValidationResult: Resultado da validação
    """
    return field_validator.validate_by_type(field_type, value, **kwargs)

def validate_business_rule(rule_name: str, data: dict, **kwargs) -> ValidationResult:
    """
    Valida uma regra de negócio específica
    
    Args:
        rule_name: Nome da regra ('motivo_observacao', 'previsao_posterior', etc.)
        data: Dados para validação
        **kwargs: Parâmetros adicionais
        
    Returns:
        ValidationResult: Resultado da validação
    """
    return business_validator.validate_rule(rule_name, data, **kwargs)

def validate_security(security_type: str, value, **kwargs) -> ValidationResult:
    """
    Valida aspectos de segurança
    
    Args:
        security_type: Tipo de validação ('password', 'access', 'permission')
        value: Valor a ser validado
        **kwargs: Parâmetros adicionais
        
    Returns:
        ValidationResult: Resultado da validação
    """
    return security_validator.validate_by_type(security_type, value, **kwargs)

# 🚀 NOVAS FUNÇÕES - Para funcionalidades migradas

def validate_user_access(poi_amigavel: str, areas_usuario: list, localizacao: str = "RRP") -> bool:
    """
    🚀 NOVA - Validação de acesso do usuário ao POI (migrada do EventoProcessor)
    
    Args:
        poi_amigavel: Nome amigável do POI
        areas_usuario: Lista de áreas do usuário
        localizacao: Código da localização (RRP/TLS)
        
    Returns:
        bool: True se usuário tem acesso
    """
    result = business_validator.validate_acesso_usuario_poi(poi_amigavel, areas_usuario, localizacao)
    return result.valid

def validate_audit_integrity(df_registros) -> dict:
    """
    🚀 NOVA - Validação de integridade de auditoria (migrada do DataUtils)
    
    Args:
        df_registros: DataFrame com registros para validar
        
    Returns:
        Dict com resultado da validação
    """
    result = business_validator.validate_integridade_auditoria(df_registros)
    return {
        "valido": result.valid,
        "problemas": result.errors,
        "total_verificado": result.data.get("total_verificado", 0),
        "problemas_encontrados": result.data.get("problemas_encontrados", 0)
    }

# Funções de compatibilidade para facilitar migração gradual
def validar_observacao_obrigatoria(motivo: str, observacao: str) -> dict:
    """
    DEPRECATED: Use validate_business_rule('motivo_observacao', {...})
    Mantido para compatibilidade com DataValidator existente
    """
    result = business_validator.validate_motivo_observacao(motivo, observacao)
    return {
        "valido": result.valid,
        "erro": result.errors[0] if result.errors else "",
        "obrigatoria": motivo and motivo.strip().lower() == "outros"
    }

def validar_data_hora(data_str: str, hora_str: str) -> dict:
    """
    DEPRECATED: Use validate_field('datetime', {...})
    Mantido para compatibilidade com DataValidator existente
    """
    result = field_validator.validate_datetime_fields(data_str, hora_str)
    return {
        "valido": result.valid,
        "erro": result.errors[0] if result.errors else "",
        "data_formatada": result.data.get("formatted_datetime", ""),
        "datetime_obj": result.data.get("datetime_obj")
    }

def validar_politica_senha(senha: str) -> tuple:
    """
    DEPRECATED: Use validate_security('password', senha)
    Mantido para compatibilidade com SuzanoPasswordService
    """
    result = security_validator.validate_password_policy(senha)
    return (result.valid, result.errors[0] if result.errors else "Senha válida")

def validar_acesso_usuario(poi_amigavel: str, areas_usuario: list, localizacao: str = "RRP") -> bool:
    """
    DEPRECATED: Use validate_user_access()
    Mantido para compatibilidade com EventoProcessor
    """
    return validate_user_access(poi_amigavel, areas_usuario, localizacao)

def validar_integridade_auditoria(df_registros) -> dict:
    """
    DEPRECATED: Use validate_audit_integrity()
    Mantido para compatibilidade com DataUtils
    """
    return validate_audit_integrity(df_registros)

# 🎯 FUNÇÕES DE MIGRAÇÃO - Para verificar status da migração

def verificar_status_migracao() -> dict:
    """
    Verifica status da migração do sistema de validações
    
    Returns:
        Dict com status completo da migração
    """
    return {
        "sistema_centralizado": True,
        "validadores_ativos": ["FieldValidator", "BusinessValidator", "SecurityValidator"],
        "arquivos_migrados": [
            "tabela_justificativas.py",
            "data_validator.py", 
            "suzano_password_service.py",
            "evento_processor.py",  # 🚀 NOVO
            "data_utils.py"         # 🚀 NOVO
        ],
        "funcionalidades_migradas": {
            "validacao_campos": "✅ Completa",
            "regras_negocio": "✅ Completa", 
            "validacao_seguranca": "✅ Completa",
            "validacao_acesso": "✅ Migrada do EventoProcessor",
            "validacao_auditoria": "✅ Migrada do DataUtils"
        },
        "compatibilidade_mantida": True,
        "migracao_completa": True
    }

def mostrar_guia_uso():
    """Mostra guia de uso do sistema centralizado"""
    print("""
🚀 SISTEMA DE VALIDAÇÃO CENTRALIZADO - GUIA DE USO

1️⃣ Validações de Campos:
   from app.validators import field_validator
   result = field_validator.validate_email_field("user@suzano.com.br")
   result = field_validator.validate_datetime_fields("25/12/2024", "14:30")

2️⃣ Regras de Negócio:
   from app.validators import business_validator
   result = business_validator.validate_motivo_observacao("Outros", "Descrição")
   result = business_validator.validate_evento_justificativas(df_evento, alteracoes)

3️⃣ Validações de Segurança:
   from app.validators import security_validator
   result = security_validator.validate_password_policy("minhasenha123")
   result = security_validator.validate_user_permission("torre", "admin")

4️⃣ Funções de Conveniência:
   from app.validators import validate_user_access, validate_audit_integrity
   tem_acesso = validate_user_access("P.A. Água Clara", ["pa agua clara"])
   integridade = validate_audit_integrity(df_registros)

📋 Código Antigo Continua Funcionando:
   from app.services.data_validator import DataValidator
   result = DataValidator.validar_observacao_obrigatoria(motivo, obs)  # ✅ OK

🎯 Migração 100% Completa!
    """)

__all__ = [
    # Classes principais
    'ValidationResult', 'BaseValidator', 'ValidationError',
    'FieldValidator', 'BusinessValidator', 'SecurityValidator',
    
    # Instâncias globais
    'field_validator', 'business_validator', 'security_validator',
    
    # Funções de conveniência
    'validate_field', 'validate_business_rule', 'validate_security',
    
    # 🚀 NOVAS FUNÇÕES - Migradas
    'validate_user_access', 'validate_audit_integrity',
    
    # Compatibilidade (DEPRECATED mas funcionais)
    'validar_observacao_obrigatoria', 'validar_data_hora', 'validar_politica_senha',
    'validar_acesso_usuario', 'validar_integridade_auditoria',
    
    # Funções de migração
    'verificar_status_migracao', 'mostrar_guia_uso'
]