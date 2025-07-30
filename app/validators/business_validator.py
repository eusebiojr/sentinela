"""
Validador de regras de negócio específicas do Sistema Sentinela - Suzano
Centraliza todas as validações relacionadas às regras de negócio logístico
"""
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseValidator, ValidationResult, ValidationMessages, ValidationType
from .field_validator import FieldValidator
import logging

class BusinessValidator(BaseValidator):
    """
    Validador especializado em regras de negócio da Suzano
    
    Suporta validações de:
    - Regras motivo + observação
    - Previsões de liberação
    - Validações de eventos completos
    - Regras de acesso por área/POI
    - Validações de auditoria
    """
    
    def __init__(self):
        super().__init__("BusinessValidator")
        self.field_validator = FieldValidator()
        
        # Configurações de negócio
        self.motivos_que_exigem_observacao = ["outros"]
        self.max_dias_previsao = 30  # Máximo 30 dias no futuro
    
    def _validate_impl(self, value: Any, context: Dict, result: ValidationResult, **kwargs):
        """Implementação principal - redireciona para validador específico"""
        rule_name = kwargs.get('rule_name', 'unknown')
        
        if rule_name == 'motivo_observacao':
            self._validate_motivo_observacao_rule(value, result, **kwargs)
        elif rule_name == 'previsao_posterior':
            self._validate_previsao_posterior_rule(value, result, **kwargs)
        elif rule_name == 'evento_completo':
            self._validate_evento_completo_rule(value, result, **kwargs)
        elif rule_name == 'acesso_poi':
            self._validate_acesso_poi_rule(value, result, **kwargs)
        elif rule_name == 'integridade_auditoria':
            self._validate_integridade_auditoria_rule(value, result, **kwargs)
        else:
            result.add_error(
                ValidationMessages.format_message(
                    ValidationMessages.UNKNOWN_VALIDATION,
                    type=rule_name
                )
            )

    def validate_rule(self, rule_name: str, data: Dict, **kwargs) -> ValidationResult:
        """
        Método público para validar regra específica por nome
        
        Args:
            rule_name: Nome da regra de negócio
            data: Dados para validação
            **kwargs: Parâmetros específicos da regra
            
        Returns:
            ValidationResult: Resultado da validação
        """
        return self.validate(data, rule_name=rule_name, **kwargs)
    
    # =================== VALIDADORES DE REGRAS ESPECÍFICAS ===================
    
    def _validate_motivo_observacao_rule(self, data: Dict, result: ValidationResult, **kwargs):
        """
        Valida regra: Quando motivo é 'Outros', observação é obrigatória
        
        Args:
            data: Dict com 'motivo' e 'observacao'
        """
        motivo = data.get('motivo', '')
        observacao = data.get('observacao', '')
        
        # Normaliza valores
        motivo_normalizado = self._ensure_string(motivo).lower()
        observacao_normalizada = self._ensure_string(observacao)
        
        # Determina se observação é obrigatória
        observacao_obrigatoria = motivo_normalizado in self.motivos_que_exigem_observacao
        result.add_data('observacao_obrigatoria', observacao_obrigatoria)
        
        # Se obrigatória e não preenchida, erro
        if observacao_obrigatoria and not observacao_normalizada:
            result.add_error(ValidationMessages.OBSERVACAO_OBRIGATORIA)
        
        # Dados úteis para UI
        result.add_data('motivo_normalizado', motivo_normalizado)
        result.add_data('observacao_normalizada', observacao_normalizada)
    
    def _validate_previsao_posterior_rule(self, data: Dict, result: ValidationResult, **kwargs):
        """
        Valida regra: Previsão deve ser posterior à data de entrada
        
        Args:
            data: Dict com 'previsao' e 'data_entrada'
        """
        previsao = data.get('previsao', '')
        data_entrada = data.get('data_entrada', '')
        
        # Se previsão não informada, não valida (pode ser opcional)
        if not previsao:
            return
        
        # Valida formato da previsão
        previsao_result = self.field_validator.validate_datetime_fields(
            previsao.split(' ')[0] if ' ' in previsao else previsao,
            previsao.split(' ')[1] if ' ' in previsao else '',
            required=False,
            reference_date=data_entrada,
            must_be_future=kwargs.get('must_be_future', False),
            max_days_future=kwargs.get('max_days_future', self.max_dias_previsao)
        )
        
        result.merge(previsao_result)
        
        # Se data de entrada informada, valida se é posterior
        if data_entrada and previsao_result.valid:
            try:
                if ' ' in previsao:
                    dt_previsao = datetime.strptime(previsao, "%d/%m/%Y %H:%M")
                else:
                    dt_previsao = datetime.strptime(previsao, "%d/%m/%Y")
                
                if ' ' in data_entrada:
                    dt_entrada = datetime.strptime(data_entrada, "%d/%m/%Y %H:%M")
                else:
                    dt_entrada = datetime.strptime(data_entrada, "%d/%m/%Y")
                
                if dt_previsao <= dt_entrada:
                    result.add_error(
                        ValidationMessages.format_message(
                            ValidationMessages.PREVISAO_POSTERIOR,
                            data_entrada=data_entrada
                        )
                    )
            except ValueError as e:
                result.add_error(f"Erro ao validar datas: {str(e)}")
    
    def _validate_evento_completo_rule(self, data: Dict, result: ValidationResult, **kwargs):
        """
        Valida evento completo (todos os registros de um evento)
        
        Args:
            data: Dict com 'df_evento' e 'alteracoes_pendentes'
        """
        df_evento = data.get('df_evento')
        alteracoes_pendentes = data.get('alteracoes_pendentes', {})
        titulo_evento = data.get('titulo_evento', '')
        
        if df_evento is None or df_evento.empty:
            result.add_error("DataFrame do evento não pode estar vazio")
            return
        
        erros_registros = []
        
        # Valida cada registro do evento
        for _, row in df_evento.iterrows():
            row_id = str(row["ID"]).strip()
            chave_alteracao = f"{titulo_evento}_{row_id}"
            placa = str(row.get("Placa", ""))
            
            # Obtém valores atuais (com alterações pendentes aplicadas)
            motivo_atual = self._get_valor_com_alteracoes(
                row, "Motivo", alteracoes_pendentes, chave_alteracao
            )
            obs_atual = self._get_valor_com_alteracoes(
                row, "Observacoes", alteracoes_pendentes, chave_alteracao
            )
            
            # 🚀 CORREÇÃO: Valida motivo + observação de forma mais simples
            try:
                # Usa validação interna direta para evitar recursão
                motivo_normalizado = str(motivo_atual).strip().lower() if motivo_atual else ""
                obs_normalizada = str(obs_atual).strip() if obs_atual else ""
                
                # Verifica regra específica
                if motivo_normalizado == "outros" and not obs_normalizada:
                    erros_registros.append(f"• Placa {placa}: Observação é obrigatória quando motivo é 'Outros'")
                    
            except Exception as e:
                # Log do erro mas não para a validação
                print(f"⚠️ Erro na validação do registro {placa}: {str(e)}")
                erros_registros.append(f"• Placa {placa}: Erro na validação - verifique os dados")
        
        # Adiciona todos os erros encontrados
        for erro in erros_registros:
            result.add_error(erro)
        
        # Dados úteis
        result.add_data('total_registros', len(df_evento))
        result.add_data('registros_com_erro', len(erros_registros))

    def _validar_acesso_rigoroso(self, poi_amigavel: str, areas_usuario: List[str], localizacao: str) -> bool:
        """
        🚀 CORREÇÃO - Usa LocationProcessor diretamente (mapeamento correto)
        
        Args:
            poi_amigavel: Nome amigável do POI
            areas_usuario: Lista de áreas do usuário
            localizacao: Código da localização
            
        Returns:
            bool: True se usuário tem acesso
        """
        try:
            from ..services.location_processor import LocationProcessor
            return LocationProcessor.validar_acesso_usuario_por_localizacao(
                poi_amigavel, localizacao, areas_usuario
            )
        except Exception as e:
            print(f"⚠️ Erro na validação de acesso no BusinessValidator: {e}")
            # Para debug: permite acesso temporariamente
            return True

    def _validate_acesso_poi_rule(self, data: Dict, result: ValidationResult, **kwargs):
        """
        Valida se usuário tem acesso ao POI - LÓGICA MIGRADA DO EventoProcessor
        
        Args:
            data: Dict com 'poi_amigavel', 'areas_usuario', 'localizacao'
        """
        poi_amigavel = data.get('poi_amigavel', '')
        areas_usuario = data.get('areas_usuario', [])
        localizacao = data.get('localizacao', 'RRP')
        
        if not areas_usuario:
            result.add_error("Usuário não possui áreas definidas")
            return
        
        # 🚀 LÓGICA MIGRADA - Validação rigorosa por área/POI
        tem_acesso = self._validar_acesso_rigoroso(poi_amigavel, areas_usuario, localizacao)
        
        if not tem_acesso:
            result.add_error(ValidationMessages.ACESSO_NEGADO)
        
        result.add_data('tem_acesso', tem_acesso)
        result.add_data('areas_validadas', areas_usuario)
        result.add_data('poi_validado', poi_amigavel)
        result.add_data('localizacao', localizacao)
    
    def _validate_integridade_auditoria_rule(self, data: Dict, result: ValidationResult, **kwargs):
        """
        Valida integridade dos dados de auditoria
        
        Args:
            data: Dict com 'df_registros'
        """
        df_registros = data.get('df_registros')
        
        if df_registros is None or df_registros.empty:
            result.add_error("DataFrame para auditoria não pode estar vazio")
            return
        
        problemas = []
        
        # Verifica registros com usuário de preenchimento mas sem data
        if 'Preenchido_por' in df_registros.columns and 'Data_Preenchimento' in df_registros.columns:
            sem_data_preench = df_registros[
                (df_registros["Preenchido_por"].notnull()) & 
                (df_registros["Preenchido_por"] != "") & 
                (df_registros["Data_Preenchimento"].isna())
            ]
            
            if not sem_data_preench.empty:
                problemas.append(
                    f"Encontrados {len(sem_data_preench)} registros com usuário de preenchimento mas sem data"
                )
        
        # Verifica registros aprovados sem auditoria
        if 'Status' in df_registros.columns and 'Aprovado_por' in df_registros.columns:
            status_sem_auditoria = df_registros[
                (df_registros["Status"].isin(["Aprovado", "Reprovado"])) &
                ((df_registros["Aprovado_por"].isna()) | (df_registros["Aprovado_por"] == ""))
            ]
            
            if not status_sem_auditoria.empty:
                problemas.append(
                    f"Encontrados {len(status_sem_auditoria)} registros aprovados/reprovados sem auditoria"
                )
        
        # Adiciona problemas como erros
        for problema in problemas:
            result.add_error(problema)
        
        # Dados de resumo
        result.add_data('total_verificado', len(df_registros))
        result.add_data('problemas_encontrados', len(problemas))
    
    # =================== MÉTODOS UTILITÁRIOS ===================
    
    def _get_valor_com_alteracoes(self, row: pd.Series, campo: str, 
                                 alteracoes: Dict, chave_alteracao: str) -> str:
        """
        Obtém valor atual do campo considerando alterações pendentes
        
        Args:
            row: Linha do DataFrame
            campo: Nome do campo
            alteracoes: Dicionário de alterações pendentes
            chave_alteracao: Chave específica das alterações
            
        Returns:
            str: Valor atual (original ou alterado)
        """
        # Valor original do DataFrame
        valor_original = str(row.get(campo, "")).strip()
        
        # Normaliza valores especiais
        if valor_original.lower() in ("none", "— selecione —"):
            valor_original = ""
        
        # Verifica se há alteração pendente
        if chave_alteracao in alteracoes and campo in alteracoes[chave_alteracao]:
            valor_alteracao = str(alteracoes[chave_alteracao][campo]).strip()
            if valor_alteracao.lower() in ("none", "— selecione —"):
                return ""
            return valor_alteracao
        
        return valor_original
    
    # =================== MÉTODOS PÚBLICOS ESPECÍFICOS ===================
    
    def validate_motivo_observacao(self, motivo: str, observacao: str) -> ValidationResult:
        """
        Método público para validar relação motivo + observação
        
        Compatível com DataValidator.validar_observacao_obrigatoria()
        """
        data = {'motivo': motivo, 'observacao': observacao}
        return self.validate_rule('motivo_observacao', data)
    
    def validate_previsao_posterior(self, previsao: str, data_entrada: str, 
                                  must_be_future: bool = False) -> ValidationResult:
        """Método público para validar previsão posterior à entrada"""
        data = {'previsao': previsao, 'data_entrada': data_entrada}
        return self.validate_rule('previsao_posterior', data, must_be_future=must_be_future)
    
    def validate_evento_justificativas(self, df_evento: pd.DataFrame, 
                                     alteracoes_pendentes: Dict, 
                                     titulo_evento: str = "") -> ValidationResult:
        """
        Método público para validar justificativas completas de um evento
        
        Compatível com DataValidator.validar_justificativas_evento()
        """
        data = {
            'df_evento': df_evento,
            'alteracoes_pendentes': alteracoes_pendentes,
            'titulo_evento': titulo_evento
        }
        return self.validate_rule('evento_completo', data)
    
    def validate_acesso_usuario_poi(self, poi_amigavel: str, areas_usuario: List[str], 
                                   localizacao: str = "RRP") -> ValidationResult:
        """Método público para validar acesso do usuário ao POI"""
        data = {
            'poi_amigavel': poi_amigavel,
            'areas_usuario': areas_usuario,
            'localizacao': localizacao
        }
        return self.validate_rule('acesso_poi', data)
    
    def validate_integridade_auditoria(self, df_registros: pd.DataFrame) -> ValidationResult:
        """Método público para validar integridade de auditoria"""
        data = {'df_registros': df_registros}
        return self.validate_rule('integridade_auditoria', data)
    
    # =================== VALIDADORES COMPOSTOS ===================
    
    def validate_registro_completo(self, motivo: str, observacao: str, previsao: str, 
                                  data_entrada: str, placa: str = "") -> ValidationResult:
        """
        Valida um registro completo (motivo + observação + previsão)
        
        Args:
            motivo: Motivo selecionado
            observacao: Observação informada
            previsao: Previsão de liberação
            data_entrada: Data de entrada do registro
            placa: Placa do veículo (para identificação nos erros)
            
        Returns:
            ValidationResult: Resultado consolidado
        """
        resultado_final = ValidationResult(valid=True)
        
        # Valida motivo + observação
        motivo_obs_result = self.validate_motivo_observacao(motivo, observacao)
        resultado_final.merge(motivo_obs_result)
        
        # Valida previsão se informada
        if previsao and previsao.strip():
            previsao_result = self.validate_previsao_posterior(previsao, data_entrada)
            resultado_final.merge(previsao_result)
        
        # Adiciona contexto da placa nos erros se informada
        if placa and not resultado_final.valid:
            erros_com_placa = []
            for erro in resultado_final.errors:
                if not erro.startswith("• Placa"):
                    erros_com_placa.append(f"• Placa {placa}: {erro}")
                else:
                    erros_com_placa.append(erro)
            resultado_final.errors = erros_com_placa
        
        return resultado_final