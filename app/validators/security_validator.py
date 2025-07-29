"""
Validador de segurança
Centraliza validações relacionadas à segurança do sistema
"""
import re
from typing import Any, Dict, List

from .base import BaseValidator, ValidationResult, ValidationMessages, ValidationType


class SecurityValidator(BaseValidator):
    """
    Validador especializado em aspectos de segurança
    
    Suporta validações de:
    - Políticas de senha
    - Permissões de acesso
    - Sanitização de inputs
    - Validações de autenticação
    """
    
    def __init__(self):
        super().__init__("SecurityValidator")
        
        # Configurações de segurança (conforme configuração Suzano)
        self.password_config = {
            'min_length': 6,
            'max_length': 50,
            'require_letter': False,  # Conforme política Suzano simplificada
            'require_number': False,
            'require_special': False,
            'forbidden_patterns': ['123456', 'password', 'senha']
        }
    
    def _validate_impl(self, value: Any, context: Dict, result: ValidationResult, **kwargs):
        """Implementação principal - redireciona para validador específico"""
        security_type = kwargs.get('security_type', 'unknown')
        
        if security_type == 'password':
            self._validate_password_policy(value, result, **kwargs)
        elif security_type == 'permission':
            self._validate_permission(value, result, **kwargs)
        elif security_type == 'access':
            self._validate_access_control(value, result, **kwargs)
        elif security_type == 'input_sanitization':
            self._validate_input_sanitization(value, result, **kwargs)
        else:
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.UNKNOWN_VALIDATION,
                    type=security_type
                )
            )
    
    def validate_by_type(self, security_type: str, value: Any, **kwargs) -> ValidationResult:
        """
        Método público para validar por tipo específico de segurança
        
        Args:
            security_type: Tipo de validação de segurança
            value: Valor a ser validado
            **kwargs: Parâmetros específicos
            
        Returns:
            ValidationResult: Resultado da validação
        """
        return self.validate(value, security_type=security_type, **kwargs)
    
    # =================== VALIDADORES ESPECÍFICOS ===================
    
    def _validate_password_policy(self, password: Any, result: ValidationResult, **kwargs):
        """
        Valida política de senha conforme configuração Suzano
        
        Args:
            password: Senha a ser validada
        """
        password_str = self._ensure_string(password)
        
        # Se senha vazia
        if not password_str:
            result.add_error("Senha não pode estar vazia")
            return
        
        # Configurações podem ser sobrescritas via kwargs
        config = self.password_config.copy()
        config.update(kwargs.get('password_config', {}))
        
        # Valida comprimento mínimo
        if len(password_str) < config['min_length']:
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.PASSWORD_TOO_SHORT,
                    min_length=config['min_length']
                )
            )
        
        # Valida comprimento máximo
        if len(password_str) > config['max_length']:
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.PASSWORD_TOO_LONG,
                    max_length=config['max_length']
                )
            )
        
        # Validações opcionais (dependem da configuração)
        if config['require_letter'] and not re.search(r'[a-zA-Z]', password_str):
            result.add_error("Senha deve conter pelo menos uma letra")
        
        if config['require_number'] and not re.search(r'\d', password_str):
            result.add_error("Senha deve conter pelo menos um número")
        
        if config['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password_str):
            result.add_error("Senha deve conter pelo menos um caractere especial")
        
        # Verifica padrões proibidos
        password_lower = password_str.lower()
        for forbidden in config['forbidden_patterns']:
            if forbidden.lower() in password_lower:
                result.add_error(f"Senha não pode conter '{forbidden}'")
        
        # Dados úteis para feedback
        result.add_data('password_length', len(password_str))
        result.add_data('has_letter', bool(re.search(r'[a-zA-Z]', password_str)))
        result.add_data('has_number', bool(re.search(r'\d', password_str)))
        result.add_data('has_special', bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password_str)))
        
        # Avaliação de força (informativa)
        strength_score = self._calculate_password_strength(password_str)
        result.add_data('strength_score', strength_score)
        result.add_data('strength_level', self._get_strength_level(strength_score))
    
    def _validate_permission(self, permission_data: Dict, result: ValidationResult, **kwargs):
        """
        Valida permissões de usuário
        
        Args:
            permission_data: Dict com dados de permissão
                - user_profile: Perfil do usuário
                - required_permission: Permissão necessária
                - resource: Recurso sendo acessado
        """
        user_profile = permission_data.get('user_profile', '').lower().strip()
        required_permission = permission_data.get('required_permission', '').lower().strip()
        resource = permission_data.get('resource', '')
        
        # Matriz de permissões por perfil
        permission_matrix = {
            'operador': ['read', 'write'],
            'preenchedor': ['read', 'write'],
            'aprovador': ['read', 'write', 'approve', 'reject'],
            'torre': ['read', 'write', 'approve', 'reject', 'admin'],
            'admin': ['read', 'write', 'approve', 'reject', 'admin', 'delete']
        }
        
        # Verifica se perfil existe
        if user_profile not in permission_matrix:
            result.add_error(f"Perfil de usuário inválido: {user_profile}")
            return
        
        # Verifica se tem a permissão necessária
        user_permissions = permission_matrix[user_profile]
        if required_permission not in user_permissions:
            result.add_error(
                f"Usuário com perfil '{user_profile}' não possui permissão '{required_permission}' "
                f"para o recurso '{resource}'"
            )
        
        # Dados úteis
        result.add_data('user_profile', user_profile)
        result.add_data('user_permissions', user_permissions)
        result.add_data('required_permission', required_permission)
        result.add_data('has_permission', required_permission in user_permissions)
    
    def _validate_access_control(self, access_data: Dict, result: ValidationResult, **kwargs):
        """
        Valida controle de acesso baseado em contexto
        
        Args:
            access_data: Dict com dados de acesso
                - user_areas: Áreas do usuário
                - resource_area: Área do recurso
                - action: Ação sendo executada
        """
        user_areas = access_data.get('user_areas', [])
        resource_area = access_data.get('resource_area', '').lower().strip()
        action = access_data.get('action', '').lower().strip()
        
        # Normaliza áreas do usuário
        user_areas_normalized = [area.lower().strip() for area in user_areas]
        
        # Verifica se usuário tem acesso à área do recurso
        has_area_access = (
            'geral' in user_areas_normalized or 
            'all' in user_areas_normalized or
            resource_area in user_areas_normalized
        )
        
        if not has_area_access:
            result.add_error(
                f"Usuário não possui acesso à área '{resource_area}'. "
                f"Áreas disponíveis: {', '.join(user_areas)}"
            )
        
        # Validações específicas por ação
        if action == 'write' and not has_area_access:
            result.add_error("Permissão de escrita negada para esta área")
        elif action == 'approve' and resource_area not in user_areas_normalized:
            result.add_error("Apenas usuários da mesma área podem aprovar")
        
        # Dados úteis
        result.add_data('user_areas_normalized', user_areas_normalized)
        result.add_data('resource_area', resource_area)
        result.add_data('has_area_access', has_area_access)
    
    def _validate_input_sanitization(self, input_value: Any, result: ValidationResult, **kwargs):
        """
        Valida e sanitiza inputs para prevenir injeções
        
        Args:
            input_value: Valor de entrada a ser validado
        """
        input_str = self._ensure_string(input_value)
        
        # Padrões suspeitos
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Scripts HTML
            r'javascript:',                # JavaScript URLs
            r'on\w+\s*=',                 # Event handlers HTML
            r'<iframe[^>]*>',             # IFrames
            r'eval\s*\(',                 # Eval JavaScript
            r'exec\s*\(',                 # Exec Python
            r'__import__',                # Import Python
            r'\.\./',                     # Directory traversal
            r'SELECT\s+.*FROM',           # SQL injection (básico)
            r'DROP\s+TABLE',              # SQL Drop
            r'INSERT\s+INTO',             # SQL Insert
            r'UPDATE\s+.*SET',            # SQL Update
        ]
        
        # Verifica padrões suspeitos
        found_patterns = []
        for pattern in suspicious_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                found_patterns.append(pattern)
        
        if found_patterns:
            result.add_error(
                f"Input contém padrões suspeitos de injeção: {len(found_patterns)} padrão(ões) detectado(s)"
            )
            result.add_data('suspicious_patterns', found_patterns)
        
        # Sanitização básica
        sanitized_value = input_str
        
        # Remove/escapa caracteres perigosos
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            if char in sanitized_value:
                sanitized_value = sanitized_value.replace(char, f'&#{ord(char)};')
        
        # Dados úteis
        result.add_data('original_value', input_str)
        result.add_data('sanitized_value', sanitized_value)
        result.add_data('was_sanitized', sanitized_value != input_str)
    
    # =================== MÉTODOS UTILITÁRIOS ===================
    
    def _calculate_password_strength(self, password: str) -> int:
        """
        Calcula força da senha (0-100)
        
        Args:
            password: Senha a ser avaliada
            
        Returns:
            int: Score de força (0-100)
        """
        score = 0
        
        # Comprimento (máximo 25 pontos)
        length_score = min(25, len(password) * 2)
        score += length_score
        
        # Variedade de caracteres (máximo 75 pontos)
        if re.search(r'[a-z]', password):
            score += 15  # Minúsculas
        if re.search(r'[A-Z]', password):
            score += 15  # Maiúsculas
        if re.search(r'\d', password):
            score += 15  # Números
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15  # Especiais
        if len(set(password)) > len(password) * 0.7:
            score += 15  # Diversidade de caracteres
        
        return min(100, score)
    
    def _get_strength_level(self, score: int) -> str:
        """
        Converte score numérico em nível textual
        
        Args:
            score: Score de força (0-100)
            
        Returns:
            str: Nível de força
        """
        if score >= 80:
            return "Forte"
        elif score >= 60:
            return "Média"
        elif score >= 40:
            return "Fraca"
        else:
            return "Muito Fraca"
    
    # =================== MÉTODOS PÚBLICOS ESPECÍFICOS ===================
    
    def validate_password_policy(self, password: str, **config_overrides) -> ValidationResult:
        """
        Método público para validar política de senha
        
        Compatível com SuzanoPasswordService.validar_politica_senha()
        
        Args:
            password: Senha a ser validada
            **config_overrides: Sobrescrever configurações padrão
            
        Returns:
            ValidationResult: Resultado da validação
        """
        return self.validate_by_type('password', password, password_config=config_overrides)
    
    def validate_user_permission(self, user_profile: str, required_permission: str, 
                                resource: str = "") -> ValidationResult:
        """Método público para validar permissão de usuário"""
        permission_data = {
            'user_profile': user_profile,
            'required_permission': required_permission,
            'resource': resource
        }
        return self.validate_by_type('permission', permission_data)
    
    def validate_area_access(self, user_areas: List[str], resource_area: str, 
                           action: str = "read") -> ValidationResult:
        """Método público para validar acesso por área"""
        access_data = {
            'user_areas': user_areas,
            'resource_area': resource_area,
            'action': action
        }
        return self.validate_by_type('access', access_data)
    
    def sanitize_input(self, input_value: str, validate_only: bool = False) -> ValidationResult:
        """
        Método público para sanitizar entrada
        
        Args:
            input_value: Valor a ser sanitizado
            validate_only: Se True, apenas valida sem sanitizar
            
        Returns:
            ValidationResult: Resultado com valor sanitizado em data['sanitized_value']
        """
        result = self.validate_by_type('input_sanitization', input_value)
        
        if validate_only:
            # Remove valor sanitizado se só está validando
            result.data.pop('sanitized_value', None)
        
        return result
    
    # =================== VALIDADORES COMPOSTOS ===================
    
    def validate_user_session(self, user_data: Dict) -> ValidationResult:
        """
        Valida dados completos de uma sessão de usuário
        
        Args:
            user_data: Dict com dados do usuário
                - profile: Perfil do usuário
                - areas: Áreas de acesso
                - email: Email do usuário
                - last_login: Último login
                
        Returns:
            ValidationResult: Resultado consolidado
        """
        resultado_final = ValidationResult(valid=True)
        
        # Valida perfil
        profile = user_data.get('profile', '')
        if profile:
            profile_result = self.validate_user_permission(
                profile, 'read', 'basic_access'
            )
            resultado_final.merge(profile_result)
        
        # Valida áreas
        areas = user_data.get('areas', [])
        if not areas:
            resultado_final.add_error("Usuário deve ter pelo menos uma área de acesso")
        
        # Valida email se fornecido
        email = user_data.get('email', '')
        if email:
            from .field_validator import FieldValidator
            field_validator = FieldValidator()
            email_result = field_validator.validate_email_field(email, required=False)
            resultado_final.merge(email_result)
        
        # Dados da sessão
        resultado_final.add_data('session_valid', resultado_final.valid)
        resultado_final.add_data('user_profile', profile)
        resultado_final.add_data('user_areas_count', len(areas))
        
        return resultado_final
    
    def validate_password_change(self, current_password: str, new_password: str, 
                                confirm_password: str) -> ValidationResult:
        """
        Valida troca de senha completa
        
        Args:
            current_password: Senha atual
            new_password: Nova senha
            confirm_password: Confirmação da nova senha
            
        Returns:
            ValidationResult: Resultado consolidado
        """
        resultado_final = ValidationResult(valid=True)
        
        # Valida senha atual não vazia
        if not current_password or not current_password.strip():
            resultado_final.add_error("Senha atual é obrigatória")
        
        # Valida nova senha
        new_pass_result = self.validate_password_policy(new_password)
        resultado_final.merge(new_pass_result)
        
        # Valida confirmação
        if new_password != confirm_password:
            resultado_final.add_error("Nova senha e confirmação não conferem")
        
        # Verifica se nova senha é diferente da atual
        if current_password == new_password:
            resultado_final.add_warning("Nova senha é igual à senha atual")
        
        # Dados úteis
        if new_pass_result.valid:
            resultado_final.add_data('new_password_strength', 
                                   new_pass_result.data.get('strength_level', 'Desconhecida'))
        
        return resultado_final