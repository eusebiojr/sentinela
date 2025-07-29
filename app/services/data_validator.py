"""
Validador de dados - VERSÃO MIGRADA PARA SISTEMA CENTRALIZADO
Mantém API pública mas usa validadores centralizados internamente
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any

# 🚀 NOVA IMPORTAÇÃO - Usa sistema centralizado
from ..validators import field_validator, business_validator
from ..validators.migration_wrapper import migration_wrapper


class DataValidator:
    """
    Classe de validação - MIGRADA PARA SISTEMA CENTRALIZADO
    Mantém compatibilidade total com código existente
    """
    
    @staticmethod
    def validar_data_hora(data_str: str, hora_str: str) -> Dict[str, Any]:
        """
        🚀 MIGRADO - Usa FieldValidator centralizado
        Mantém API idêntica para compatibilidade
        """
        return migration_wrapper.validar_data_hora(data_str, hora_str)
    
    @staticmethod
    def validar_data_posterior(data_nova: datetime, data_entrada_str: str) -> Dict[str, Any]:
        """
        🚀 MIGRADO - Usa BusinessValidator centralizado
        Mantém API idêntica para compatibilidade
        """
        return migration_wrapper.validar_data_posterior(data_nova, data_entrada_str)
    
    @staticmethod
    def validar_observacao_obrigatoria(motivo: str, observacao: str) -> Dict[str, Any]:
        """
        🚀 MIGRADO - Usa BusinessValidator centralizado
        Mantém API idêntica para compatibilidade
        """
        return migration_wrapper.validar_observacao_obrigatoria(motivo, observacao)
    
    @staticmethod
    def validar_justificativas_evento(df_evento: pd.DataFrame, alteracoes_pendentes: Dict) -> Dict[str, Any]:
        """
        🚀 MIGRADO - Usa BusinessValidator centralizado
        Mantém API idêntica para compatibilidade
        """
        return migration_wrapper.validar_justificativas_evento(df_evento, alteracoes_pendentes)
    
    # 🚀 NOVOS MÉTODOS - Aproveitam sistema centralizado
    
    @staticmethod
    def validar_email(email: str, obrigatorio: bool = True) -> Dict[str, Any]:
        """
        NOVO - Validação de email usando sistema centralizado
        
        Args:
            email: Email a ser validado
            obrigatorio: Se o campo é obrigatório
            
        Returns:
            Dict no formato compatível
        """
        result = field_validator.validate_email_field(email, required=obrigatorio)
        return migration_wrapper.migrate_result_to_old_format(result)
    
    @staticmethod
    def validar_texto(texto: str, campo_nome: str = "Campo", 
                     min_chars: int = None, max_chars: int = None,
                     obrigatorio: bool = False) -> Dict[str, Any]:
        """
        NOVO - Validação de texto usando sistema centralizado
        
        Args:
            texto: Texto a ser validado
            campo_nome: Nome do campo para mensagens
            min_chars: Mínimo de caracteres
            max_chars: Máximo de caracteres
            obrigatorio: Se o campo é obrigatório
            
        Returns:
            Dict no formato compatível
        """
        result = field_validator.validate_text_field(
            texto, campo_nome, min_chars, max_chars, obrigatorio
        )
        return migration_wrapper.migrate_result_to_old_format(result)
    
    @staticmethod
    def validar_numero(numero: Any, campo_nome: str = "Número",
                      valor_min: float = None, valor_max: float = None,
                      obrigatorio: bool = False) -> Dict[str, Any]:
        """
        NOVO - Validação de número usando sistema centralizado
        
        Args:
            numero: Número a ser validado
            campo_nome: Nome do campo
            valor_min: Valor mínimo permitido
            valor_max: Valor máximo permitido
            obrigatorio: Se o campo é obrigatório
            
        Returns:
            Dict no formato compatível
        """
        result = field_validator.validate_number_field(
            numero, campo_nome, valor_min, valor_max, obrigatorio
        )
        return migration_wrapper.migrate_result_to_old_format(result)
    
    @staticmethod
    def validar_acesso_poi(poi_amigavel: str, areas_usuario: list, 
                          localizacao: str = "RRP") -> bool:
        """
        NOVO - Validação de acesso usando sistema centralizado
        
        Args:
            poi_amigavel: Nome amigável do POI
            areas_usuario: Lista de áreas do usuário
            localizacao: Código da localização
            
        Returns:
            bool: True se usuário tem acesso
        """
        result = business_validator.validate_acesso_usuario_poi(
            poi_amigavel, areas_usuario, localizacao
        )
        return result.valid
    
    @staticmethod
    def validar_evento_completo(df_evento: pd.DataFrame, alteracoes_pendentes: Dict,
                               titulo_evento: str = "") -> Dict[str, Any]:
        """
        NOVO - Validação completa de evento usando sistema centralizado
        
        Args:
            df_evento: DataFrame do evento
            alteracoes_pendentes: Alterações pendentes
            titulo_evento: Título do evento
            
        Returns:
            Dict com resultado detalhado da validação
        """
        result = business_validator.validate_evento_justificativas(
            df_evento, alteracoes_pendentes, titulo_evento
        )
        
        return {
            "valido": result.valid,
            "erros": result.errors,
            "avisos": result.warnings,
            "total_registros": result.data.get("total_registros", 0),
            "registros_com_erro": result.data.get("registros_com_erro", 0)
        }
    
    # 🚀 MÉTODOS DE CONVENIÊNCIA - Facilitam uso direto
    
    @staticmethod
    def validar_previsao_liberacao(previsao_str: str, data_entrada_str: str,
                                  obrigar_futuro: bool = False) -> Dict[str, Any]:
        """
        NOVO - Validação específica de previsão de liberação
        
        Args:
            previsao_str: String da previsão (dd/mm/yyyy hh:mm)
            data_entrada_str: String da data de entrada
            obrigar_futuro: Se deve obrigar data no futuro
            
        Returns:
            Dict com resultado da validação
        """
        result = business_validator.validate_previsao_posterior(
            previsao_str, data_entrada_str, must_be_future=obrigar_futuro
        )
        return migration_wrapper.migrate_result_to_old_format(result)
    
    @staticmethod
    def validar_multiplos_campos(campos: Dict[str, Any]) -> Dict[str, Any]:
        """
        NOVO - Validação de múltiplos campos em uma chamada
        
        Args:
            campos: Dict com {nome_campo: {tipo, valor, config}}
            
        Returns:
            Dict consolidado com todos os resultados
        """
        resultado_consolidado = {
            "valido": True,
            "erros": [],
            "avisos": [],
            "campos_validados": 0,
            "campos_com_erro": 0
        }
        
        for nome_campo, config in campos.items():
            tipo = config.get("tipo", "texto")
            valor = config.get("valor")
            params = config.get("params", {})
            
            if tipo == "email":
                result = field_validator.validate_email_field(valor, **params)
            elif tipo == "texto":
                result = field_validator.validate_text_field(valor, nome_campo, **params)
            elif tipo == "numero":
                result = field_validator.validate_number_field(valor, nome_campo, **params)
            elif tipo == "data_hora":
                data = params.get("data", "")
                hora = params.get("hora", "")
                result = field_validator.validate_datetime_fields(data, hora, **params)
            else:
                continue  # Tipo não suportado
            
            resultado_consolidado["campos_validados"] += 1
            
            if not result.valid:
                resultado_consolidado["valido"] = False
                resultado_consolidado["campos_com_erro"] += 1
                for erro in result.errors:
                    resultado_consolidado["erros"].append(f"{nome_campo}: {erro}")
            
            for aviso in result.warnings:
                resultado_consolidado["avisos"].append(f"{nome_campo}: {aviso}")
        
        return resultado_consolidado
    
    # 🧹 MÉTODOS DEPRECADOS - Para remoção futura
    
    @staticmethod
    def validar_politica_senha(senha: str) -> tuple:
        """
        ⚠️ DEPRECATED - Use SecurityValidator diretamente
        Mantido apenas para compatibilidade
        """
        import warnings
        warnings.warn(
            "DataValidator.validar_politica_senha() está deprecated. "
            "Use security_validator.validate_password_policy()",
            DeprecationWarning,
            stacklevel=2
        )
        
        return migration_wrapper.validar_politica_senha(senha)


# 🚀 FUNÇÕES DE CONVENIÊNCIA - Para uso direto sem instanciar classe

def validar_campo_obrigatorio(valor: Any, nome_campo: str = "Campo") -> bool:
    """Validação rápida de campo obrigatório"""
    result = field_validator.validate_required_field(valor, nome_campo)
    return result.valid

def validar_motivo_observacao_rapido(motivo: str, observacao: str) -> bool:
    """Validação rápida de motivo + observação"""
    result = business_validator.validate_motivo_observacao(motivo, observacao)
    return result.valid

def obter_mensagem_erro_validacao(motivo: str, observacao: str) -> str:
    """Obtém mensagem de erro específica para motivo + observação"""
    result = business_validator.validate_motivo_observacao(motivo, observacao)
    return result.errors[0] if result.errors else ""

def validar_data_brasileira(data_str: str) -> bool:
    """Validação rápida de data no formato brasileiro"""
    result = field_validator.validate_date_field(data_str, required=False)
    return result.valid

def validar_hora_24h(hora_str: str) -> bool:
    """Validação rápida de hora no formato 24h"""
    result = field_validator.validate_time_field(hora_str, required=False)
    return result.valid


# 🚀 CLASSE UTILITÁRIA - Para casos especiais

class ValidadorAvancado:
    """
    Classe para validações mais complexas usando sistema centralizado
    """
    
    def __init__(self):
        self.field_validator = field_validator
        self.business_validator = business_validator
    
    def validar_formulario_completo(self, dados_formulario: Dict) -> Dict[str, Any]:
        """
        Valida um formulário completo com múltiplos campos
        
        Args:
            dados_formulario: Dict com dados do formulário
            
        Returns:
            Dict com resultado consolidado da validação
        """
        resultado = {
            "valido": True,
            "erros_por_campo": {},
            "avisos_por_campo": {},
            "resumo": {
                "total_campos": 0,
                "campos_validos": 0,
                "campos_com_erro": 0,
                "campos_com_aviso": 0
            }
        }
        
        for campo, valor in dados_formulario.items():
            resultado["resumo"]["total_campos"] += 1
            
            # Detecta tipo do campo automaticamente
            if "email" in campo.lower():
                validation_result = self.field_validator.validate_email_field(valor, required=True)
            elif "data" in campo.lower() and "hora" in dados_formulario:
                # Pula se já processou data+hora
                continue
            elif "senha" in campo.lower():
                from ..validators import security_validator
                validation_result = security_validator.validate_password_policy(valor)
            else:
                # Default: texto
                validation_result = self.field_validator.validate_text_field(valor, campo, required=True)
            
            if validation_result.valid:
                resultado["resumo"]["campos_validos"] += 1
            else:
                resultado["valido"] = False
                resultado["resumo"]["campos_com_erro"] += 1
                resultado["erros_por_campo"][campo] = validation_result.errors
            
            if validation_result.warnings:
                resultado["resumo"]["campos_com_aviso"] += 1
                resultado["avisos_por_campo"][campo] = validation_result.warnings
        
        return resultado
    
    def validar_lote_registros(self, registros: list, configuracao: Dict) -> Dict[str, Any]:
        """
        Valida um lote de registros usando as mesmas regras
        
        Args:
            registros: Lista de dicionários com dados
            configuracao: Configuração de validação
            
        Returns:
            Dict com resultado do lote
        """
        resultado = {
            "valido": True,
            "total_registros": len(registros),
            "registros_validos": 0,
            "registros_com_erro": 0,
            "erros_detalhados": [],
            "estatisticas": {}
        }
        
        for idx, registro in enumerate(registros):
            registro_resultado = self.validar_formulario_completo(registro)
            
            if registro_resultado["valido"]:
                resultado["registros_validos"] += 1
            else:
                resultado["valido"] = False
                resultado["registros_com_erro"] += 1
                resultado["erros_detalhados"].append({
                    "registro_index": idx,
                    "erros": registro_resultado["erros_por_campo"]
                })
        
        # Estatísticas
        if resultado["total_registros"] > 0:
            resultado["estatisticas"] = {
                "percentual_sucesso": (resultado["registros_validos"] / resultado["total_registros"]) * 100,
                "percentual_erro": (resultado["registros_com_erro"] / resultado["total_registros"]) * 100
            }
        
        return resultado


# 🚀 INSTÂNCIA GLOBAL - Para uso direto
validador_avancado = ValidadorAvancado()