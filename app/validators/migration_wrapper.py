"""
Wrapper de Migração - Compatibilidade com Código Existente
Permite migração gradual mantendo APIs antigas funcionando
"""
import warnings
from typing import Dict, Any, Tuple
import pandas as pd

# Importa novos validadores
from .field_validator import FieldValidator
from .business_validator import BusinessValidator
from .security_validator import SecurityValidator
from .base import ValidationResult


class MigrationWrapper:
    """
    Wrapper que mantém compatibilidade com as validações antigas
    permitindo migração gradual do código existente
    """
    
    def __init__(self):
        self.field_validator = FieldValidator()
        self.business_validator = BusinessValidator()
        self.security_validator = SecurityValidator()
    
    # =================== COMPATIBILIDADE COM DataValidator ===================
    
    def validar_data_hora(self, data_str: str, hora_str: str) -> Dict[str, Any]:
        """
        DEPRECATED: Mantém compatibilidade com DataValidator.validar_data_hora()
        
        Args:
            data_str: String da data (dd/mm/aaaa)
            hora_str: String da hora (hh:mm)
            
        Returns:
            Dict: Formato antigo de retorno
        """
        warnings.warn(
            "validar_data_hora() está deprecated. Use field_validator.validate_datetime_fields()",
            DeprecationWarning,
            stacklevel=2
        )
        
        result = self.field_validator.validate_datetime_fields(data_str, hora_str)
        
        return {
            "valido": result.valid,
            "erro": result.errors[0] if result.errors else "",
            "data_formatada": result.data.get("formatted_datetime", ""),
            "datetime_obj": result.data.get("datetime_obj")
        }
    
    def validar_data_posterior(self, data_nova, data_entrada_str: str) -> Dict[str, Any]:
        """
        DEPRECATED: Mantém compatibilidade com DataValidator.validar_data_posterior()
        
        Args:
            data_nova: Objeto datetime da nova data
            data_entrada_str: String da data de entrada
            
        Returns:
            Dict: Formato antigo de retorno
        """
        warnings.warn(
            "validar_data_posterior() está deprecated. Use business_validator.validate_previsao_posterior()",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Converte datetime para string se necessário
        if hasattr(data_nova, 'strftime'):
            previsao_str = data_nova.strftime("%d/%m/%Y %H:%M")
        else:
            previsao_str = str(data_nova)
        
        result = self.business_validator.validate_previsao_posterior(previsao_str, data_entrada_str)
        
        return {
            "valido": result.valid,
            "erro": result.errors[0] if result.errors else ""
        }
    
    def validar_observacao_obrigatoria(self, motivo: str, observacao: str) -> Dict[str, Any]:
        """
        DEPRECATED: Mantém compatibilidade com DataValidator.validar_observacao_obrigatoria()
        
        Args:
            motivo: Motivo selecionado
            observacao: Observação informada
            
        Returns:
            Dict: Formato antigo de retorno
        """
        warnings.warn(
            "validar_observacao_obrigatoria() está deprecated. Use business_validator.validate_motivo_observacao()",
            DeprecationWarning,
            stacklevel=2
        )
        
        result = self.business_validator.validate_motivo_observacao(motivo, observacao)
        
        return {
            "valido": result.valid,
            "erro": result.errors[0] if result.errors else "",
            "obrigatoria": result.data.get("observacao_obrigatoria", False)
        }
    
    def validar_justificativas_evento(self, df_evento: pd.DataFrame, 
                                    alteracoes_pendentes: Dict) -> Dict[str, Any]:
        """
        DEPRECATED: Mantém compatibilidade com DataValidator.validar_justificativas_evento()
        
        Args:
            df_evento: DataFrame do evento
            alteracoes_pendentes: Alterações pendentes
            
        Returns:
            Dict: Formato antigo de retorno
        """
        warnings.warn(
            "validar_justificativas_evento() está deprecated. Use business_validator.validate_evento_justificativas()",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Extrai título do evento
        titulo_evento = df_evento["Titulo"].iloc[0] if "Titulo" in df_evento.columns else ""
        
        result = self.business_validator.validate_evento_justificativas(
            df_evento, alteracoes_pendentes, titulo_evento
        )
        
        return {
            "valido": result.valid,
            "erros": result.errors
        }
    
    # =================== COMPATIBILIDADE COM SuzanoPasswordService ===================
    
    def validar_politica_senha(self, senha: str) -> Tuple[bool, str]:
        """
        DEPRECATED: Mantém compatibilidade com SuzanoPasswordService.validar_politica_senha()
        
        Args:
            senha: Senha a ser validada
            
        Returns:
            Tuple: (is_valid, message)
        """
        warnings.warn(
            "validar_politica_senha() está deprecated. Use security_validator.validate_password_policy()",
            DeprecationWarning,
            stacklevel=2
        )
        
        result = self.security_validator.validate_password_policy(senha)
        
        if result.valid:
            return True, "Senha válida"
        else:
            return False, result.errors[0] if result.errors else "Erro de validação"
    
    # =================== COMPATIBILIDADE COM EventoProcessor ===================
    
    def validar_acesso_usuario(self, poi_amigavel: str, areas_usuario: list, 
                              localizacao: str = "RRP") -> bool:
        """
        DEPRECATED: Mantém compatibilidade com EventoProcessor.validar_acesso_usuario()
        
        Args:
            poi_amigavel: Nome amigável do POI
            areas_usuario: Lista de áreas do usuário
            localizacao: Código da localização
            
        Returns:
            bool: True se usuário tem acesso
        """
        warnings.warn(
            "validar_acesso_usuario() está deprecated. Use business_validator.validate_acesso_usuario_poi()",
            DeprecationWarning,
            stacklevel=2
        )
        
        result = self.business_validator.validate_acesso_usuario_poi(
            poi_amigavel, areas_usuario, localizacao
        )
        
        return result.valid
    
    # =================== COMPATIBILIDADE GENÉRICA ===================
    
    def migrate_result_to_old_format(self, result: ValidationResult, 
                                   format_type: str = "dict") -> Any:
        """
        Converte ValidationResult para formato antigo
        
        Args:
            result: Resultado da nova validação
            format_type: Tipo de formato de retorno ("dict", "tuple", "bool")
            
        Returns:
            Any: Resultado no formato antigo
        """
        if format_type == "bool":
            return result.valid
        elif format_type == "tuple":
            return (result.valid, result.errors[0] if result.errors else "")
        else:  # dict
            return {
                "valido": result.valid,
                "erro": result.errors[0] if result.errors else "",
                "avisos": result.warnings,
                "dados": result.data
            }
    
    def create_validation_adapter(self, old_function_name: str, new_validator_method):
        """
        Cria adaptador genérico para função antiga
        
        Args:
            old_function_name: Nome da função antiga
            new_validator_method: Método novo do validador
            
        Returns:
            Function: Função adaptadora
        """
        def adapter(*args, **kwargs):
            warnings.warn(
                f"{old_function_name}() está deprecated. Use o novo sistema de validação",
                DeprecationWarning,
                stacklevel=2
            )
            
            result = new_validator_method(*args, **kwargs)
            return self.migrate_result_to_old_format(result)
        
        return adapter
    
    # =================== UTILITÁRIOS DE MIGRAÇÃO ===================
    
    def show_migration_guide(self, old_function: str = None):
        """
        Mostra guia de migração para desenvolvedores
        
        Args:
            old_function: Função específica para mostrar migração
        """
        migration_guide = {
            "validar_data_hora": {
                "old": "DataValidator.validar_data_hora(data, hora)",
                "new": "field_validator.validate_datetime_fields(data, hora)",
                "benefit": "Validação mais robusta com timezone e constraints"
            },
            "validar_observacao_obrigatoria": {
                "old": "DataValidator.validar_observacao_obrigatoria(motivo, obs)",
                "new": "business_validator.validate_motivo_observacao(motivo, obs)",
                "benefit": "Regras de negócio centralizadas e extensíveis"
            },
            "validar_politica_senha": {
                "old": "suzano_password_service.validar_politica_senha(senha)",
                "new": "security_validator.validate_password_policy(senha)",
                "benefit": "Validações de segurança unificadas e configuráveis"
            }
        }
        
        if old_function and old_function in migration_guide:
            guide = migration_guide[old_function]
            print(f"""
📋 GUIA DE MIGRAÇÃO - {old_function}

❌ Código Antigo:
   {guide['old']}

✅ Código Novo:
   {guide['new']}

🎯 Benefício:
   {guide['benefit']}
            """)
        else:
            print("""
📋 GUIA GERAL DE MIGRAÇÃO

O sistema de validação foi centralizado em 3 validadores principais:

1️⃣ FieldValidator - Campos básicos
   • validate_datetime_fields()
   • validate_email_field()
   • validate_text_field()

2️⃣ BusinessValidator - Regras de negócio
   • validate_motivo_observacao()
   • validate_previsao_posterior()
   • validate_evento_justificativas()

3️⃣ SecurityValidator - Segurança
   • validate_password_policy()
   • validate_user_permission()
   • validate_area_access()

🔄 Importação Simplificada:
   from app.validators import field_validator, business_validator, security_validator
            """)
    
    def check_deprecated_usage(self, codebase_path: str = None):
        """
        Verifica uso de funções deprecadas no código
        
        Args:
            codebase_path: Caminho para verificar (opcional)
        """
        deprecated_functions = [
            "validar_data_hora",
            "validar_observacao_obrigatoria", 
            "validar_justificativas_evento",
            "validar_politica_senha",
            "validar_acesso_usuario"
        ]
        
        print("🔍 VERIFICAÇÃO DE FUNÇÕES DEPRECADAS")
        print("-" * 50)
        
        if codebase_path:
            import os
            import re
            
            deprecated_found = {}
            
            for root, dirs, files in os.walk(codebase_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                for func in deprecated_functions:
                                    if re.search(rf'\b{func}\b', content):
                                        if file_path not in deprecated_found:
                                            deprecated_found[file_path] = []
                                        deprecated_found[file_path].append(func)
                        except Exception:
                            continue
            
            if deprecated_found:
                print("❌ Funções deprecadas encontradas:")
                for file_path, functions in deprecated_found.items():
                    print(f"   📁 {file_path}")
                    for func in functions:
                        print(f"      • {func}()")
            else:
                print("✅ Nenhuma função deprecada encontrada!")
        else:
            print("💡 Para verificar seu código, execute:")
            print("   wrapper.check_deprecated_usage('/caminho/para/seu/codigo')")


# Instância global para compatibilidade
migration_wrapper = MigrationWrapper()

# Funções globais de compatibilidade (para importação direta)
def validar_data_hora(data_str: str, hora_str: str) -> Dict[str, Any]:
    """DEPRECATED: Use field_validator.validate_datetime_fields()"""
    return migration_wrapper.validar_data_hora(data_str, hora_str)

def validar_observacao_obrigatoria(motivo: str, observacao: str) -> Dict[str, Any]:
    """DEPRECATED: Use business_validator.validate_motivo_observacao()"""
    return migration_wrapper.validar_observacao_obrigatoria(motivo, observacao)

def validar_politica_senha(senha: str) -> Tuple[bool, str]:
    """DEPRECATED: Use security_validator.validate_password_policy()"""
    return migration_wrapper.validar_politica_senha(senha)