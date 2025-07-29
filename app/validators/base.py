"""
Classes base para o sistema de validação centralizado
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class ValidationError(Exception):
    """Exceção específica para erros de validação"""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


@dataclass
class ValidationResult:
    """
    Resultado padronizado de validação
    
    Attributes:
        valid: Se a validação passou
        errors: Lista de mensagens de erro
        warnings: Lista de mensagens de aviso
        data: Dados adicionais retornados pela validação
        field: Campo específico relacionado ao resultado (opcional)
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    field: Optional[str] = None
    
    def add_error(self, message: str, code: str = None):
        """Adiciona uma mensagem de erro"""
        self.errors.append(message)
        self.valid = False
        if code:
            self.data[f"error_code_{len(self.errors)}"] = code
    
    def add_warning(self, message: str, code: str = None):
        """Adiciona uma mensagem de aviso"""
        self.warnings.append(message)
        if code:
            self.data[f"warning_code_{len(self.warnings)}"] = code
    
    def add_data(self, key: str, value: Any):
        """Adiciona dados adicionais ao resultado"""
        self.data[key] = value
    
    def merge(self, other: 'ValidationResult'):
        """Combina este resultado com outro"""
        if not other.valid:
            self.valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.data.update(other.data)
    
    @property
    def has_errors(self) -> bool:
        """Verifica se há erros"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Verifica se há avisos"""
        return len(self.warnings) > 0
    
    @property
    def summary(self) -> str:
        """Retorna um resumo textual do resultado"""
        if self.valid and not self.has_warnings:
            return "✅ Validação passou"
        elif self.valid and self.has_warnings:
            return f"⚠️ Validação passou com {len(self.warnings)} aviso(s)"
        else:
            return f"❌ Validação falhou com {len(self.errors)} erro(s)"
    
    def __bool__(self) -> bool:
        """Permite usar ValidationResult em contextos booleanos"""
        return self.valid


class BaseValidator(ABC):
    """
    Classe base para todos os validadores
    
    Define a interface comum e métodos utilitários
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
    
    def validate(self, value: Any, context: Dict = None, **kwargs) -> ValidationResult:
        """
        Método principal de validação
        
        Args:
            value: Valor a ser validado
            context: Contexto adicional para validação
            **kwargs: Parâmetros específicos do validador
            
        Returns:
            ValidationResult: Resultado da validação
        """
        context = context or {}
        result = ValidationResult(valid=True)
        
        try:
            self._validate_impl(value, context, result, **kwargs)
        except ValidationError as e:
            result.add_error(e.message, e.code)
        except Exception as e:
            result.add_error(f"Erro interno de validação: {str(e)}", "INTERNAL_ERROR")
        
        return result
    
    @abstractmethod
    def _validate_impl(self, value: Any, context: Dict, result: ValidationResult, **kwargs):
        """
        Implementação específica da validação
        Deve ser sobrescrita pelas classes filhas
        
        Args:
            value: Valor a ser validado
            context: Contexto da validação
            result: Objeto resultado para adicionar erros/dados
            **kwargs: Parâmetros específicos
        """
        pass
    
    def _ensure_string(self, value: Any) -> str:
        """Converte valor para string de forma segura"""
        if value is None:
            return ""
        return str(value).strip()
    
    def _ensure_not_empty(self, value: str, field_name: str = "Campo") -> ValidationResult:
        """Valida se um campo não está vazio"""
        result = ValidationResult(valid=True)
        if not value or not value.strip():
            result.add_error(f"{field_name} não pode estar vazio")
        return result
    
    def _log_validation(self, value: Any, result: ValidationResult):
        """Log interno de validação (para debug)"""
        status = "✅" if result.valid else "❌"
        print(f"{status} [{self.name}] Validação: {type(value).__name__} -> {result.summary}")


class CompositeValidator(BaseValidator):
    """
    Validador composto que executa múltiplos validadores
    
    Permite combinar diferentes validadores em uma única operação
    """
    
    def __init__(self, validators: List[BaseValidator], name: str = "CompositeValidator"):
        super().__init__(name)
        self.validators = validators
    
    def _validate_impl(self, value: Any, context: Dict, result: ValidationResult, **kwargs):
        """Executa todos os validadores em sequência"""
        for validator in self.validators:
            sub_result = validator.validate(value, context, **kwargs)
            result.merge(sub_result)
            
            # Se stop_on_first_error estiver ativo e houver erro, para
            if kwargs.get('stop_on_first_error', False) and not sub_result.valid:
                break
    
    def add_validator(self, validator: BaseValidator):
        """Adiciona um novo validador à composição"""
        self.validators.append(validator)
    
    def remove_validator(self, validator_name: str):
        """Remove um validador específico pelo nome"""
        self.validators = [v for v in self.validators if v.name != validator_name]


class ValidationMessages:
    """
    Centralizador de mensagens de validação em português
    
    Facilita manutenção e possível internacionalização futura
    """
    
    # Mensagens de campos básicos
    FIELD_REQUIRED = "{field} é obrigatório"
    FIELD_INVALID_FORMAT = "{field} tem formato inválido"
    FIELD_TOO_SHORT = "{field} deve ter pelo menos {min_length} caracteres"
    FIELD_TOO_LONG = "{field} não pode ter mais de {max_length} caracteres"
    
    # Mensagens de data/hora
    DATE_INVALID_FORMAT = "Data deve estar no formato dd/mm/aaaa"
    TIME_INVALID_FORMAT = "Hora deve estar no formato hh:mm"
    DATETIME_PAST = "Data/hora deve ser no futuro"
    DATETIME_TOO_FAR = "Data/hora não pode ser superior a {max_days} dias"
    
    # Mensagens de negócio
    OBSERVACAO_OBRIGATORIA = "Observação é obrigatória quando motivo é 'Outros'"
    PREVISAO_POSTERIOR = "Previsão deve ser posterior à data de entrada: {data_entrada}"
    ACESSO_NEGADO = "Usuário não tem acesso a este ponto de interesse"
    
    # Mensagens de segurança
    PASSWORD_TOO_SHORT = "Senha deve ter pelo menos {min_length} caracteres"
    PASSWORD_TOO_LONG = "Senha não pode ter mais de {max_length} caracteres"
    PASSWORD_WEAK = "Senha deve conter ao menos uma letra e um número"
    
    # Mensagens de sistema
    INTERNAL_ERROR = "Erro interno do sistema"
    UNKNOWN_VALIDATION = "Tipo de validação desconhecido: {type}"
    
    @classmethod
    def format_message(cls, message_template: str, **kwargs) -> str:
        """
        Formata uma mensagem com parâmetros
        
        Args:
            message_template: Template da mensagem
            **kwargs: Parâmetros para substituição
            
        Returns:
            str: Mensagem formatada
        """
        try:
            return message_template.format(**kwargs)
        except KeyError as e:
            return f"Erro ao formatar mensagem: parâmetro {e} não encontrado"
        except Exception:
            return message_template  # Retorna template original em caso de erro


# Tipos de validação suportados (para referência)
class ValidationType:
    """Constantes para tipos de validação"""
    
    # Campos básicos
    REQUIRED = "required"
    EMAIL = "email"
    PHONE = "phone"
    TEXT = "text"
    NUMBER = "number"
    
    # Data/hora
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    
    # Negócio
    MOTIVO_OBSERVACAO = "motivo_observacao"
    PREVISAO_POSTERIOR = "previsao_posterior"
    ACESSO_POI = "acesso_poi"
    
    # Segurança
    PASSWORD = "password"
    PERMISSION = "permission"
    ACCESS = "access"


# Função utilitária para criar resultado de sucesso rápido
def success_result(data: Dict = None) -> ValidationResult:
    """Cria um resultado de validação bem-sucedida"""
    result = ValidationResult(valid=True)
    if data:
        result.data.update(data)
    return result


# Função utilitária para criar resultado de erro rápido
def error_result(message: str, field: str = None, code: str = None) -> ValidationResult:
    """Cria um resultado de validação com erro"""
    result = ValidationResult(valid=False, field=field)
    result.add_error(message, code)
    return result