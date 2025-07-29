"""
Validador de campos básicos
Centraliza validações de campos de formulário e tipos de dados
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional
import pandas as pd

from .base import BaseValidator, ValidationResult, ValidationMessages, ValidationType


class FieldValidator(BaseValidator):
    """
    Validador especializado em campos básicos de formulário
    
    Suporta validações de:
    - Campos obrigatórios
    - Formatos (email, telefone, etc.)
    - Datas e horários
    - Números e rangos
    - Textos e comprimentos
    """
    
    def __init__(self):
        super().__init__("FieldValidator")
        
        # Padrões regex para validações
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^\(\d{2}\)\s\d{4,5}-\d{4}$'),  # (11) 99999-9999
            'date_br': re.compile(r'^\d{2}/\d{2}/\d{4}$'),        # dd/mm/yyyy
            'time_24h': re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'),  # HH:MM
        }
    
    def _validate_impl(self, value: Any, context: Dict, result: ValidationResult, **kwargs):
        """Implementação principal - redireciona para validador específico"""
        field_type = kwargs.get('field_type', ValidationType.TEXT)
        
        if field_type == ValidationType.REQUIRED:
            self._validate_required(value, result, **kwargs)
        elif field_type == ValidationType.EMAIL:
            self._validate_email(value, result, **kwargs)
        elif field_type == ValidationType.DATE:
            self._validate_date(value, result, **kwargs)
        elif field_type == ValidationType.TIME:
            self._validate_time(value, result, **kwargs)
        elif field_type == ValidationType.DATETIME:
            self._validate_datetime(value, result, **kwargs)
        elif field_type == ValidationType.TEXT:
            self._validate_text(value, result, **kwargs)
        elif field_type == ValidationType.NUMBER:
            self._validate_number(value, result, **kwargs)
        else:
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.UNKNOWN_VALIDATION, 
                    type=field_type
                )
            )
    
    def validate_by_type(self, field_type: str, value: Any, **kwargs) -> ValidationResult:
        """
        Método público para validar por tipo específico
        
        Args:
            field_type: Tipo de campo a ser validado
            value: Valor a ser validado
            **kwargs: Parâmetros específicos do tipo
            
        Returns:
            ValidationResult: Resultado da validação
        """
        # 🚀 CORREÇÃO: Remove field_type dos kwargs se existir para evitar duplicação
        clean_kwargs = {k: v for k, v in kwargs.items() if k != 'field_type'}
        
        return self.validate(value, field_type=field_type, **clean_kwargs)
    
    # =================== VALIDADORES ESPECÍFICOS ===================
    
    def _validate_required(self, value: Any, result: ValidationResult, **kwargs):
        """Valida se o campo é obrigatório"""
        field_name = kwargs.get('field_name', 'Campo')
        value_str = self._ensure_string(value)
        
        if not value_str:
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.FIELD_REQUIRED,
                    field=field_name
                )
            )
    
    def _validate_email(self, value: Any, result: ValidationResult, **kwargs):
        """Valida formato de email"""
        field_name = kwargs.get('field_name', 'Email')
        value_str = self._ensure_string(value)
        
        # Se campo não é obrigatório e está vazio, passa
        if not kwargs.get('required', True) and not value_str:
            return
        
        # Se obrigatório, valida presença
        if kwargs.get('required', True):
            req_result = ValidationResult(valid=True)
            self._validate_required(value, req_result, field_name=field_name)
            result.merge(req_result)
            if not req_result.valid:
                return
        
        # Valida formato se há valor
        if value_str and not self.patterns['email'].match(value_str):
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.FIELD_INVALID_FORMAT,
                    field=field_name
                )
            )
        else:
            result.add_data('email_normalized', value_str.lower().strip())
    
    def _validate_date(self, value: Any, result: ValidationResult, **kwargs):
        """Valida formato de data brasileira (dd/mm/yyyy)"""
        field_name = kwargs.get('field_name', 'Data')
        value_str = self._ensure_string(value)
        
        # Se não obrigatório e vazio, passa
        if not kwargs.get('required', True) and not value_str:
            return
        
        # Se obrigatório, valida presença
        if kwargs.get('required', True):
            req_result = ValidationResult(valid=True)
            self._validate_required(value, req_result, field_name=field_name)
            result.merge(req_result)
            if not req_result.valid:
                return
        
        # Valida formato se há valor
        if value_str:
            if not self.patterns['date_br'].match(value_str):
                result.add_error(ValidationMessages.DATE_INVALID_FORMAT)
                return
            
            # Tenta fazer parse da data
            try:
                dt = datetime.strptime(value_str, "%d/%m/%Y")
                result.add_data('parsed_date', dt)
                result.add_data('formatted_date', value_str)
            except ValueError:
                result.add_error("Data inválida. Verifique dia, mês e ano.")
    
    def _validate_time(self, value: Any, result: ValidationResult, **kwargs):
        """Valida formato de hora (HH:MM)"""
        field_name = kwargs.get('field_name', 'Hora')
        value_str = self._ensure_string(value)
        
        # Se não obrigatório e vazio, passa
        if not kwargs.get('required', True) and not value_str:
            return
        
        # Se obrigatório, valida presença
        if kwargs.get('required', True):
            req_result = ValidationResult(valid=True)
            self._validate_required(value, req_result, field_name=field_name)
            result.merge(req_result)
            if not req_result.valid:
                return
        
        # Valida formato se há valor
        if value_str:
            if not self.patterns['time_24h'].match(value_str):
                result.add_error(ValidationMessages.TIME_INVALID_FORMAT)
                return
            
            # Tenta fazer parse da hora
            try:
                dt = datetime.strptime(value_str, "%H:%M")
                result.add_data('parsed_time', dt.time())
                result.add_data('formatted_time', value_str)
            except ValueError:
                result.add_error("Hora inválida. Use formato HH:MM.")
    
    def _validate_datetime(self, value: Any, result: ValidationResult, **kwargs):
        """Valida combinação de data e hora - VERSÃO SIMPLIFICADA SEM RECURSÃO"""
        # Pode receber um dict com 'data' e 'hora' ou uma string única
        if isinstance(value, dict):
            data_str = value.get('data', '')
            hora_str = value.get('hora', '')
        else:
            # Tenta dividir string por espaço
            value_str = self._ensure_string(value)
            if ' ' in value_str:
                parts = value_str.split(' ', 1)
                data_str, hora_str = parts[0], parts[1]
            else:
                data_str, hora_str = value_str, ''
        
        # 🚀 CORREÇÃO: Validação direta sem chamadas recursivas
        # Valida data diretamente
        if data_str:
            if not self.patterns['date_br'].match(data_str):
                result.add_error("Data deve estar no formato dd/mm/aaaa")
                return
            try:
                dt_data = datetime.strptime(data_str, "%d/%m/%Y")
                result.add_data('parsed_date', dt_data)
            except ValueError:
                result.add_error("Data inválida. Verifique dia, mês e ano.")
                return
        
        # Valida hora diretamente
        if hora_str:
            if not self.patterns['time_24h'].match(hora_str):
                result.add_error("Hora deve estar no formato HH:MM")
                return
            try:
                dt_hora = datetime.strptime(hora_str, "%H:%M")
                result.add_data('parsed_time', dt_hora.time())
            except ValueError:
                result.add_error("Hora inválida. Use formato HH:MM.")
                return
        
        # Se ambos válidos, cria datetime completo
        if data_str and hora_str and result.valid:
            try:
                dt_combined = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
                result.add_data('datetime_obj', dt_combined)
                result.add_data('formatted_datetime', f"{data_str} {hora_str}")
                
                # Validações adicionais de data/hora
                self._validate_datetime_constraints(dt_combined, result, **kwargs)
                
            except ValueError as e:
                result.add_error(f"Erro ao combinar data e hora: {str(e)}")
    
    def _validate_datetime_constraints(self, dt: datetime, result: ValidationResult, **kwargs):
        """Valida restrições adicionais de data/hora"""
        import pytz
        
        # Timezone Brasília
        tz_brasilia = pytz.timezone("America/Campo_Grande")
        agora = datetime.now(tz_brasilia)
        
        # Se deve ser no futuro
        if kwargs.get('must_be_future', False):
            dt_tz = tz_brasilia.localize(dt)
            if dt_tz <= agora:
                result.add_error(ValidationMessages.DATETIME_PAST)
        
        # Limite máximo de dias no futuro
        max_days = kwargs.get('max_days_future')
        if max_days:
            dt_tz = tz_brasilia.localize(dt)
            max_date = agora.replace(hour=23, minute=59, second=59)
            from datetime import timedelta
            max_allowed = max_date + timedelta(days=max_days)
            
            if dt_tz > max_allowed:
                result.add_error(
                    ValidationMessages.format_message(
                        ValidationMessages.DATETIME_TOO_FAR,
                        max_days=max_days
                    )
                )
        
        # Data de referência (ex: deve ser posterior à data de entrada)
        reference_date = kwargs.get('reference_date')
        if reference_date:
            if isinstance(reference_date, str):
                try:
                    ref_dt = datetime.strptime(reference_date, "%d/%m/%Y %H:%M")
                    if dt <= ref_dt:
                        result.add_error(
                            ValidationMessages.format_message(
                                ValidationMessages.PREVISAO_POSTERIOR,
                                data_entrada=reference_date
                            )
                        )
                except ValueError:
                    result.add_warning(f"Data de referência inválida: {reference_date}")
    
    def _validate_text(self, value: Any, result: ValidationResult, **kwargs):
        """Valida campos de texto"""
        field_name = kwargs.get('field_name', 'Campo')
        value_str = self._ensure_string(value)
        
        # Se obrigatório, valida presença
        if kwargs.get('required', False):
            req_result = ValidationResult(valid=True)
            self._validate_required(value, req_result, field_name=field_name)
            result.merge(req_result)
            if not req_result.valid:
                return
        
        # Valida comprimento se há valor
        if value_str:
            min_length = kwargs.get('min_length')
            max_length = kwargs.get('max_length')
            
            if min_length and len(value_str) < min_length:
                result.add_error(
                    ValidationMessages.format_message(
                        ValidationMessages.FIELD_TOO_SHORT,
                        field=field_name,
                        min_length=min_length
                    )
                )
            
            if max_length and len(value_str) > max_length:
                result.add_error(
                    ValidationMessages.format_message(
                        ValidationMessages.FIELD_TOO_LONG,
                        field=field_name,
                        max_length=max_length
                    )
                )
            
            # Dados úteis
            result.add_data('text_length', len(value_str))
            result.add_data('text_normalized', value_str.strip())
    
    def _validate_number(self, value: Any, result: ValidationResult, **kwargs):
        """Valida campos numéricos"""
        field_name = kwargs.get('field_name', 'Número')
        
        # Se obrigatório, valida presença
        if kwargs.get('required', False):
            req_result = ValidationResult(valid=True)
            self._validate_required(value, req_result, field_name=field_name)
            result.merge(req_result)
            if not req_result.valid:
                return
        
        # Se vazio e não obrigatório, passa
        value_str = self._ensure_string(value)
        if not value_str:
            return
        
        # Tenta converter para número
        try:
            if '.' in value_str or ',' in value_str:
                # Tenta float (aceita vírgula brasileira)
                num_value = float(value_str.replace(',', '.'))
            else:
                # Tenta int
                num_value = int(value_str)
            
            result.add_data('numeric_value', num_value)
            
            # Validações de range
            min_value = kwargs.get('min_value')
            max_value = kwargs.get('max_value')
            
            if min_value is not None and num_value < min_value:
                result.add_error(f"{field_name} deve ser maior ou igual a {min_value}")
            
            if max_value is not None and num_value > max_value:
                result.add_error(f"{field_name} deve ser menor ou igual a {max_value}")
                
        except (ValueError, TypeError):
            result.add_error(f"{field_name} deve ser um número válido")
    
    # =================== MÉTODOS PÚBLICOS ESPECÍFICOS ===================
    
    def validate_required_field(self, value: Any, field_name: str = "Campo") -> ValidationResult:
        """Método público para validar campo obrigatório"""
        return self.validate_by_type(ValidationType.REQUIRED, value, field_name=field_name)
    
    def validate_email_field(self, value: Any, required: bool = True) -> ValidationResult:
        """Método público para validar email"""
        return self.validate_by_type(ValidationType.EMAIL, value, required=required)
    
    def validate_date_field(self, value: Any, required: bool = True) -> ValidationResult:
        """Método público para validar data"""
        return self.validate(value, field_type=ValidationType.DATE, required=required)
    
    def validate_time_field(self, value: Any, required: bool = True) -> ValidationResult:
        """Método público para validar hora"""
        return self.validate(value, field_type=ValidationType.TIME, required=required)
    
    def validate_datetime_fields(self, data_str: str, hora_str: str, **kwargs) -> ValidationResult:
        """
        Método público para validar combinação data + hora - VERSÃO SIMPLIFICADA
        
        Compatível com validação existente em DataValidator
        """
        # 🚀 CORREÇÃO TOTAL: Implementação completamente independente
        result = ValidationResult(valid=True)
        
        try:
            # Validação direta sem chamadas para outros métodos
            data_normalizada = self._ensure_string(data_str).strip()
            hora_normalizada = self._ensure_string(hora_str).strip()
            
            # Se ambos vazios, valida como OK (campo opcional)
            if not data_normalizada and not hora_normalizada:
                return result
            
            # Se só um preenchido, erro
            if not data_normalizada or not hora_normalizada:
                result.add_error("Preencha ambos os campos ou deixe ambos em branco")
                return result
            
            # Valida formato da data
            if not self.patterns['date_br'].match(data_normalizada):
                result.add_error("Data deve estar no formato dd/mm/aaaa")
                return result
            
            # Valida formato da hora
            if not self.patterns['time_24h'].match(hora_normalizada):
                result.add_error("Hora deve estar no formato HH:MM")
                return result
            
            # Tenta criar datetime
            try:
                dt_combined = datetime.strptime(f"{data_normalizada} {hora_normalizada}", "%d/%m/%Y %H:%M")
                result.add_data('datetime_obj', dt_combined)
                result.add_data('formatted_datetime', f"{data_normalizada} {hora_normalizada}")
            except ValueError:
                result.add_error("Data ou hora inválida")
                return result
            
            # Validações de negócio (data posterior, etc.)
            reference_date = kwargs.get('reference_date')
            if reference_date and reference_date.strip():
                try:
                    if ' ' in reference_date:
                        dt_referencia = datetime.strptime(reference_date.strip(), "%d/%m/%Y %H:%M")
                    else:
                        dt_referencia = datetime.strptime(reference_date.strip(), "%d/%m/%Y")
                    
                    if dt_combined <= dt_referencia:
                        result.add_error(f"Data/hora deve ser posterior à entrada: {reference_date}")
                        return result
                except ValueError:
                    # Se não conseguir fazer parse da referência, ignora validação
                    pass
            
            # Validação de futuro
            must_be_future = kwargs.get('must_be_future', False)
            if must_be_future:
                import pytz
                agora = datetime.now(pytz.timezone("America/Campo_Grande"))
                if dt_combined <= agora.replace(tzinfo=None):
                    result.add_error("Data/hora deve ser no futuro")
                    return result
            
            # Validação de limite máximo
            max_days_future = kwargs.get('max_days_future')
            if max_days_future:
                import pytz
                from datetime import timedelta
                
                agora = datetime.now(pytz.timezone("America/Campo_Grande"))
                max_allowed = agora + timedelta(days=max_days_future)
                
                if dt_combined > max_allowed.replace(tzinfo=None):
                    result.add_error(f"Data/hora não pode ser superior a {max_days_future} dias no futuro")
                    return result
            
        except Exception as e:
            result.add_error(f"Erro interno na validação: {str(e)}")
        
        return result
    
    def validate_text_field(self, value: Any, field_name: str = "Campo", 
                           min_length: int = None, max_length: int = None, 
                           required: bool = False) -> ValidationResult:
        """Método público para validar texto"""
        return self.validate(
            value, field_type=ValidationType.TEXT,
            field_name=field_name, min_length=min_length, 
            max_length=max_length, required=required
        )
    
    def validate_number_field(self, value: Any, field_name: str = "Número",
                             min_value: float = None, max_value: float = None,
                             required: bool = False) -> ValidationResult:
        """Método público para validar número"""
        return self.validate(
            value, field_type=ValidationType.NUMBER,
            field_name=field_name, min_value=min_value,
            max_value=max_value, required=required
        )