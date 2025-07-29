"""
Sistema de Validação Centralizado - Sentinela Suzano
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

__all__ = [
    # Classes principais
    'ValidationResult', 'BaseValidator', 'ValidationError',
    'FieldValidator', 'BusinessValidator', 'SecurityValidator',
    
    # Instâncias globais
    'field_validator', 'business_validator', 'security_validator',
    
    # Funções de conveniência
    'validate_field', 'validate_business_rule', 'validate_security',
    
    # Compatibilidade (DEPRECATED)
    'validar_observacao_obrigatoria', 'validar_data_hora', 'validar_politica_senha'
]