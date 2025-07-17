"""
Validador de dados - validações de negócio
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any


class DataValidator:
    """Classe especializada para validação de dados"""
    
    @staticmethod
    def validar_data_hora(data_str: str, hora_str: str) -> Dict[str, Any]:
        """Valida formato de data e hora"""
        resultado = {
            "valido": False,
            "erro": "",
            "data_formatada": "",
            "datetime_obj": None
        }
        
        try:
            # Verifica se ambos estão preenchidos ou ambos vazios
            if not data_str and not hora_str:
                resultado["valido"] = True
                return resultado
            
            if not data_str or not hora_str:
                resultado["erro"] = "Preencha ambos os campos ou deixe ambos em branco"
                return resultado
            
            # Valida formato
            dt = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
            
            resultado.update({
                "valido": True,
                "data_formatada": f"{data_str} {hora_str}",
                "datetime_obj": dt
            })
            
        except ValueError:
            resultado["erro"] = "Formato inválido. Use dd/mm/aaaa hh:mm"
        
        return resultado
    
    @staticmethod
    def validar_data_posterior(data_nova: datetime, data_entrada_str: str) -> Dict[str, Any]:
        """Valida se data é posterior à data de entrada"""
        resultado = {
            "valido": True,
            "erro": ""
        }
        
        if not data_entrada_str:
            return resultado
        
        try:
            dt_entrada = datetime.strptime(data_entrada_str, "%d/%m/%Y %H:%M")
            
            if data_nova <= dt_entrada:
                resultado.update({
                    "valido": False,
                    "erro": f"Data/hora deve ser posterior à entrada: {data_entrada_str}"
                })
        except ValueError:
            # Se não conseguir fazer parse da data de entrada, considera válido
            pass
        
        return resultado
    
    @staticmethod
    def validar_observacao_obrigatoria(motivo: str, observacao: str) -> Dict[str, Any]:
        """Valida se observação é obrigatória para o motivo"""
        resultado = {
            "valido": True,
            "erro": "",
            "obrigatoria": False
        }
        
        # Normaliza o motivo para comparação mais robusta
        motivo_normalizado = str(motivo).strip().lower() if motivo else ""
        observacao_normalizada = str(observacao).strip() if observacao else ""
        
        if motivo_normalizado == "outros":
            resultado["obrigatoria"] = True
            if not observacao_normalizada:
                resultado.update({
                    "valido": False,
                    "erro": "Observação obrigatória quando motivo é 'Outros'"
                })
        
        return resultado
    
    @staticmethod
    def validar_justificativas_evento(df_evento: pd.DataFrame, alteracoes_pendentes: Dict) -> Dict[str, Any]:
        """Valida todas as justificativas de um evento"""
        resultado = {
            "valido": True,
            "erros": []
        }
        
        evento_titulo = df_evento["Titulo"].iloc[0] if "Titulo" in df_evento.columns else ""
        
        for _, row in df_evento.iterrows():
            row_id = str(row["ID"]).strip()
            chave_alteracao = f"{evento_titulo}_{row_id}"
            placa = str(row.get("Placa", ""))
            
            # Valores atuais - normalização mais robusta
            motivo_atual = str(row.get("Motivo", "")).strip()
            obs_atual = str(row.get("Observacoes", "")).strip()
            
            # Normaliza valores "None" e "— Selecione —" ANTES de aplicar alterações
            if motivo_atual.lower() in ("none", "— selecione —"):
                motivo_atual = ""
            if obs_atual.lower() == "none":
                obs_atual = ""
            
            # Aplica alterações pendentes
            if chave_alteracao in alteracoes_pendentes:
                alteracoes = alteracoes_pendentes[chave_alteracao]
                
                if "Motivo" in alteracoes:
                    motivo_pendente = str(alteracoes["Motivo"]).strip()
                    # Normaliza também as alterações pendentes
                    if motivo_pendente.lower() in ("none", "— selecione —"):
                        motivo_atual = ""
                    else:
                        motivo_atual = motivo_pendente
                        
                if "Observacoes" in alteracoes:
                    obs_pendente = str(alteracoes["Observacoes"]).strip()
                    # Normaliza também as observações pendentes
                    if obs_pendente.lower() == "none":
                        obs_atual = ""
                    else:
                        obs_atual = obs_pendente
            
            # Só valida se motivo não estiver vazio E for "outros"
            if motivo_atual and motivo_atual.lower() == "outros":
                validacao_obs = DataValidator.validar_observacao_obrigatoria(motivo_atual, obs_atual)
                
                if not validacao_obs["valido"]:
                    erro_msg = f"• Placa {placa}: {validacao_obs['erro']}"
                    resultado["erros"].append(erro_msg)
        
        if resultado["erros"]:
            resultado["valido"] = False
        
        return resultado