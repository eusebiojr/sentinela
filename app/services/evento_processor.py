"""
Processador de eventos - lógica de negócio para eventos - MIGRADO PARA VALIDAÇÕES CENTRALIZADAS
"""
import pandas as pd
import pytz
from datetime import datetime
from typing import Dict, Any, List

# NOVO: Import do processador de localização
try:
    from .location_processor import location_processor
    LOCATION_PROCESSOR_AVAILABLE = True
except ImportError:
    LOCATION_PROCESSOR_AVAILABLE = False

# 🚀 NOVA IMPORTAÇÃO - Usa sistema centralizado para validações
from ..validators import business_validator


class EventoProcessor:
    """Classe especializada para processamento de eventos com validações centralizadas"""
    
    @staticmethod
    def parse_titulo_completo(titulo: str) -> Dict[str, Any]:
        """Parse completo do título do evento COM suporte a localização PADRONIZADA"""
        
        # NOVO: Usa processador de localização se disponível
        if LOCATION_PROCESSOR_AVAILABLE:
            return location_processor.parse_titulo_com_localizacao(titulo)
        
        # FALLBACK: Lógica original (apenas RRP) - ATUALIZADA
        resultado = {
            "titulo_original": titulo,
            "localizacao": "RRP",  # Assume RRP como padrão
            "tipo_amigavel": "",
            "poi_amigavel": "",
            "datahora_fmt": "",
            "data_evento": None,
            "valido": False
        }
        
        try:
            partes = titulo.split('_')
            if len(partes) < 5:
                return resultado
            
            tipo = partes[-3]
            poi_raw = partes[1].upper()
            data_str = partes[-2]
            hora_str = partes[-1]
            
            # Mapeamento de POIs ATUALIZADO COM UNIDADE
            poi_map = {
                "PAAGUACLARA": "PA AGUA CLARA",
                "CARREGAMENTOFABRICARRP": "Carregamento Fabrica RRP",
                "CARREGAMENTOFABRICA": "Carregamento Fabrica",
                "OFICINAJSL": "Oficina JSL",
                "OFICINA": "Oficina JSL",
                "TERMINALINOCENCIA": "Descarga Inocencia",
                "DESCARGAINOCENCIA": "Descarga Inocencia"
            }
            
            # Processa POI com fallback inteligente
            poi_amigavel = poi_map.get(poi_raw)
            if not poi_amigavel:
                # Busca por substring
                for key, value in poi_map.items():
                    if key in poi_raw or poi_raw in key:
                        poi_amigavel = value
                        break
                else:
                    poi_amigavel = f"{poi_raw.title()} - RRP"
            
            # Mapeamento de tipos
            tipo_map = {
                "Informativo": "Alerta Informativo",
                "N1": "Tratativa N1", "N2": "Tratativa N2",
                "N3": "Tratativa N3", "N4": "Tratativa N4"
            }
            
            # Processa tipo
            tipo_amigavel = tipo_map.get(tipo, tipo)
            
            # Processa data/hora
            try:
                datahora = datetime.strptime(data_str + "_" + hora_str, "%d%m%Y_%H%M%S")
                datahora_fmt = datahora.strftime("%d/%m %H:00")
                data_evento = datahora
            except:
                datahora_fmt = f"{data_str} {hora_str}"
                data_evento = None
            
            resultado.update({
                "tipo_amigavel": tipo_amigavel,
                "poi_amigavel": poi_amigavel,
                "datahora_fmt": datahora_fmt,
                "data_evento": data_evento,
                "valido": True
            })
            
        except Exception:
            pass
        
        return resultado

    @staticmethod
    def calcular_tempo_decorrido(data_entrada: str) -> Dict[str, Any]:
        """Calcula tempo decorrido desde a entrada (sem alterações)"""
        resultado = {
            "horas": 0,
            "texto_formatado": "0h",
            "status_tempo": "normal",  # normal, atencao, critico
            "data_entrada_valida": False
        }
        
        if not data_entrada or str(data_entrada).strip() == "":
            return resultado
        
        try:
            agora = datetime.now(pytz.timezone("America/Campo_Grande"))
            
            # Parse da data de entrada
            if "/" in str(data_entrada):
                dt_entrada = datetime.strptime(str(data_entrada).strip(), "%d/%m/%Y %H:%M")
                dt_entrada = pytz.timezone("America/Campo_Grande").localize(dt_entrada)
            else:
                dt_entrada = pd.to_datetime(data_entrada, errors="coerce")
                if pd.isnull(dt_entrada):
                    return resultado
                
                if dt_entrada.tzinfo is None:
                    dt_entrada = pytz.timezone("America/Campo_Grande").localize(dt_entrada)
                else:
                    dt_entrada = dt_entrada.tz_convert("America/Campo_Grande")
            
            # Calcula diferença
            diferenca = agora - dt_entrada
            horas = diferenca.total_seconds() / 3600
            
            if horas < 0:
                horas = 0
            
            # Determina status baseado no tempo
            if horas >= 1.5:  # 1:30h ou mais
                status_tempo = "critico"
            elif horas >= 0.75:  # 45min ou mais
                status_tempo = "atencao"
            else:
                status_tempo = "normal"
            
            # Formata texto
            if horas == 0:
                texto = "0h"
            elif horas < 1:
                minutos = int(horas * 60)
                texto = f"{minutos}min"
            elif horas < 24:
                texto = f"{horas:.1f}h"
            else:
                dias = int(horas // 24)
                horas_restantes = horas % 24
                if horas_restantes < 1:
                    texto = f"{dias}d"
                else:
                    texto = f"{dias}d {horas_restantes:.0f}h"
            
            resultado.update({
                "horas": horas,
                "texto_formatado": texto,
                "status_tempo": status_tempo,
                "data_entrada_valida": True
            })
            
        except Exception:
            pass
        
        return resultado
    
    @staticmethod
    def determinar_motivos_por_poi(poi_amigavel: str, localizacao: str = "RRP") -> List[str]:
        """Determina motivos disponíveis baseado no POI COM suporte a localização"""
        
        # NOVO: Usa processador de localização se disponível
        if LOCATION_PROCESSOR_AVAILABLE:
            return location_processor.obter_motivos_por_poi_e_localizacao(poi_amigavel, localizacao)
        
        # FALLBACK: Lógica original
        from ..config.settings import config
        
        if "P.A. Água Clara" in poi_amigavel:
            return config.motivos_poi["PA Agua Clara"]
        elif "MANUTEN" in poi_amigavel.upper() or "OFICINA" in poi_amigavel.upper():
            return config.motivos_poi["Manutenção"]
        elif "TERMINAL" in poi_amigavel.upper() or "INOCÊNCIA" in poi_amigavel.upper():
            return config.motivos_poi["Terminal"]
        elif "FÁBRICA" in poi_amigavel.upper() or "FABRICA" in poi_amigavel.upper():
            return config.motivos_poi["Fábrica"]
        else:
            return ["Outros"]
    
    @staticmethod
    def validar_acesso_usuario(poi_amigavel: str, areas_usuario: List[str], localizacao: str = "RRP") -> bool:
        """
        ✅ VALIDAÇÃO CORRIGIDA - Baseada nos dados reais da sua tabela
        """
        if not areas_usuario:
            return False
        
        # Normaliza texto (remove acentos, case insensitive)
        import unicodedata
        
        def normalizar(texto):
            if not texto:
                return ""
            # Remove acentos
            nfd = unicodedata.normalize('NFD', texto)
            without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
            return without_accents.lower().strip()
        
        poi_normalizado = normalizar(poi_amigavel)
        
        # MAPEAMENTO EXATO baseado na tabela que você enviou
        MAPEAMENTO_ACESSO = {
            # Fábrica RRP → Carregamento Fabrica RRP
            "fabrica rrp": "carregamento fabrica rrp",
            
            # Fábrica TLS → Carregamento Fabrica  
            "fabrica tls": "carregamento fabrica",
            
            # Terminal RRP → Descarga Inocencia
            "terminal rrp": "descarga inocencia",
            
            # Manutenção RRP → Oficina JSL
            "manutencao rrp": "oficina jsl",
            "manutenção rrp": "oficina jsl",  # Com acento também
            
            # PA Agua Clara RRP → PA AGUA CLARA
            "pa agua clara rrp": "pa agua clara",
            
            # PA Celulose TLS → PA Celulose
            "pa celulose tls": "pa celulose",
            
            # Áreas administrativas
            "geral": "*",
            "torre": "*"
        }
        
        # Testa cada área do usuário
        for area in areas_usuario:
            area_normalizada = normalizar(area)
            
            # Busca no mapeamento
            poi_esperado = MAPEAMENTO_ACESSO.get(area_normalizada)
            
            if not poi_esperado:
                # Busca por substring flexível
                for key, value in MAPEAMENTO_ACESSO.items():
                    if key in area_normalizada or area_normalizada in key:
                        poi_esperado = value
                        break
            
            # Verifica acesso
            if poi_esperado == "*":  # Acesso total
                return True
            elif poi_esperado and poi_esperado in poi_normalizado:
                return True
        
        return False
    
    @staticmethod 
    def debug_mapeamento(poi_amigavel: str, areas_usuario: List[str]):
        """Função de debug para testar o mapeamento"""
        print(f"\n🔍 DEBUG MAPEAMENTO:")
        print(f"POI: '{poi_amigavel}'")
        print(f"Áreas: {areas_usuario}")
        
        result = EventoProcessor.validar_acesso_usuario(poi_amigavel, areas_usuario)
        print(f"Resultado: {result}")
        
        return result

    @staticmethod
    def calcular_status_evento(df_evento: pd.DataFrame, alteracoes_pendentes: Dict) -> str:
        """Calcula status do evento baseado no preenchimento de TODOS os registros (sem alterações)"""
        if df_evento.empty:
            return "Pendente"

        evento_titulo = df_evento["Titulo"].iloc[0] if "Titulo" in df_evento.columns else ""
        
        # Verifica se TODOS os registros estão preenchidos
        for _, row in df_evento.iterrows():
            row_id = str(row["ID"]).strip()
            chave_alteracao = f"{evento_titulo}_{row_id}"

            # Valores atuais - normalização mais robusta
            motivo_atual = str(row.get("Motivo", "")).strip()
            previsao_atual = str(row.get("Previsao_Liberacao", "")).strip()

            # Normaliza valores "None" e "— Selecione —"
            if motivo_atual.lower() in ("none", "— selecione —"):
                motivo_atual = ""
            if previsao_atual.lower() in ("none", ""):
                previsao_atual = ""

            # Aplica alterações pendentes
            if chave_alteracao in alteracoes_pendentes:
                alteracoes = alteracoes_pendentes[chave_alteracao]
                if "Motivo" in alteracoes:
                    motivo_pendente = str(alteracoes["Motivo"]).strip()
                    if motivo_pendente.lower() in ("none", "— selecione —"):
                        motivo_atual = ""
                    else:
                        motivo_atual = motivo_pendente
                if "Previsao_Liberacao" in alteracoes:
                    previsao_pendente = str(alteracoes["Previsao_Liberacao"]).strip()
                    if previsao_pendente.lower() in ("none", ""):
                        previsao_atual = ""
                    else:
                        previsao_atual = previsao_pendente

            # Se qualquer registro não estiver completo, retorna "Pendente"
            motivo_ok = motivo_atual and motivo_atual.strip() != ""
            previsao_ok = previsao_atual and previsao_atual.strip() != ""
            
            if not (motivo_ok and previsao_ok):
                return "Pendente"

        # Se chegou aqui, todos os registros estão completos
        return "Preenchido"