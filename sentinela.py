import flet as ft
import pandas as pd
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from datetime import datetime
import pytz
import re
from datetime import date, timedelta
import datetime as dt
import os
from dataclasses import dataclass
from typing import Dict, Any

import logging
from datetime import datetime
import sys

class CustomFormatter(logging.Formatter):
    """Formatter personalizado com cores e timestamps"""
    
    # Cores para diferentes níveis
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Adiciona timestamp brasileiro
        record.timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Formato da mensagem
        log_format = f"[{record.timestamp}] {record.levelname}: {record.getMessage()}"
        
        # Adiciona cor se for terminal
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            log_format = f"{color}{log_format}{self.COLORS['RESET']}"
        
        return log_format

def setup_logger(name: str = "sentinela", level: str = "INFO") -> logging.Logger:
    """Configura e retorna logger personalizado"""
    logger = logging.getLogger(name)
    
    # Limpa handlers existentes para evitar conflitos
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Configura nível baseado no parâmetro
    logger.setLevel(logging.DEBUG)  # Sempre DEBUG para capturar tudo
    
    # Desabilita propagação para evitar duplicação
    logger.propagate = False

    # Handler para console - FORÇANDO sys.stderr para melhor visibilidade
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG) # Sempre DEBUG no handler
    console_handler.setFormatter(CustomFormatter())

    # Força flush imediato dos logs
    original_emit = console_handler.emit

    def emit_with_flush(record):
        original_emit(record)
        sys.stderr.flush()  # Força flush imediato
    console_handler.emit = emit_with_flush

    logger.addHandler(console_handler)

    return logger

# CONFIGURAÇÃO OTIMIZADA: Apenas logs críticos
import logging
logging.basicConfig(
    level=logging.ERROR,  # Apenas ERROR e CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # Apenas stderr para erros
    ]
)

# Logger global da aplicação - APENAS CRÍTICO
logger = setup_logger(level="ERROR")
# Configuração de logging para arquivo
import os
from datetime import datetime

# Cria diretório de logs se não existir
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Nome do arquivo de log com timestamp
log_filename = f"sentinela_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(logs_dir, log_filename)

# Adiciona handler de arquivo ao logger existente
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Log inicial informando onde encontrar os logs
logger.info(f"📁 Logs sendo salvos em: {log_filepath}")


@dataclass
class AppConfig:
    """Configurações centralizadas da aplicação"""
    # SharePoint
    site_url: str
    usuarios_list: str
    desvios_list: str
    username_sp: str
    password_sp: str
    
    # UI
    window_width: int = 1400
    window_maximized: bool = True
    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    # Motivos por POI
    motivos_poi: Dict[str, list] = None
    
    def __post_init__(self):
        if self.motivos_poi is None:
            self.motivos_poi = {
                "PA Agua Clara": ["Absenteísmo", "Ciclo Antecipado - Aguardando Motorista", "Falta Mão de Obra", "Informação Incorreta", "Outros"],
                "Manutenção": ["Preventiva", "Manutenção Grande Monta", "ITR", "Falta Mão de Obra", "Informação Incorreta"],
                "Terminal": ["Chegada em Comboio", "Troca de Turno", "Absenteísmo", "Falta Mão de Obra", "Indisponibilidade Mecânica", "Outros"],
                "Fábrica": ["Chegada em Comboio", "Troca de Turno", "Absenteísmo", "Falta Mão de Obra", "Indisponibilidade Mecânica", "Aguardando Nota", "Outros"]
            }

def load_config() -> AppConfig:
    """Carrega configurações de variáveis de ambiente ou arquivo"""
    return AppConfig(
        site_url=os.getenv("SITE_URL", "https://suzano.sharepoint.com/sites/Controleoperacional"),
        usuarios_list=os.getenv("USUARIOS_LIST", "UsuariosPainelTorre"),
        desvios_list=os.getenv("DESVIOS_LIST", "Desvios"),
        username_sp=os.getenv("USERNAME_SP", "eusebioagj@suzano.com.br"),
        password_sp=os.getenv("PASSWORD_SP", "290422@Cc"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )

# Instância global de configuração
config = load_config()

@dataclass
class AppState:
    """Estado centralizado da aplicação"""
    # Dados do usuário logado
    usuario: Dict[str, Any] = None
    
    # DataFrames principais
    df_usuarios: pd.DataFrame = None
    df_desvios: pd.DataFrame = None
    
    # Controle de alterações
    alteracoes_pendentes: Dict[str, Dict[str, Any]] = None
    
    # Estado da interface
    estado_expansao: Dict[str, bool] = None
    
    # Status de carregamento
    dados_carregados: bool = False
    carregamento_em_progresso: bool = False
    
    def __post_init__(self):
        """Inicializa valores padrão"""
        if self.df_usuarios is None:
            self.df_usuarios = pd.DataFrame()
        if self.df_desvios is None:
            self.df_desvios = pd.DataFrame()
        if self.alteracoes_pendentes is None:
            self.alteracoes_pendentes = {}
        if self.estado_expansao is None:
            self.estado_expansao = {}
    
    def reset_dados(self):
        """Limpa todos os dados (útil para logout)"""
        self.usuario = None
        self.df_usuarios = pd.DataFrame()
        self.df_desvios = pd.DataFrame()
        self.alteracoes_pendentes = {}
        self.estado_expansao = {}
        self.dados_carregados = False
        self.carregamento_em_progresso = False
    
    def is_usuario_logado(self) -> bool:
        """Verifica se há usuário logado"""
        return self.usuario is not None
    
    def get_perfil_usuario(self) -> str:
        """Retorna o perfil do usuário logado"""
        if not self.is_usuario_logado():
            return ""
        return self.usuario.get("Perfil", "").strip().lower()
    
    def get_areas_usuario(self) -> list:
        """Retorna as áreas do usuário logado"""
        if not self.is_usuario_logado():
            return []
        return DataUtils.obter_areas_usuario(self.usuario)
    
    def get_nome_usuario(self) -> str:
        """Retorna o nome de exibição do usuário"""
        if not self.is_usuario_logado():
            return ""
        return (self.usuario.get('NomeExibicao') or 
                self.usuario.get('nomeexibicao') or 
                self.usuario.get('Nome') or 
                self.usuario.get('nome') or 
                "Usuário")
    
    def atualizar_alteracao(self, chave: str, campo: str, valor: Any):
        """Registra uma alteração pendente"""
        if chave not in self.alteracoes_pendentes:
            self.alteracoes_pendentes[chave] = {}
        self.alteracoes_pendentes[chave][campo] = valor
    
    def limpar_alteracoes_evento(self, evento: str):
        """Remove alterações pendentes de um evento específico"""
        chaves_para_remover = [k for k in self.alteracoes_pendentes.keys() 
                              if k.startswith(f"{evento}_")]
        for chave in chaves_para_remover:
            del self.alteracoes_pendentes[chave]
    
    def has_alteracoes_pendentes(self) -> bool:
        """Verifica se há alterações não salvas"""
        return len(self.alteracoes_pendentes) > 0

# Instância global do estado
app_state = AppState()

class EventoProcessor:
    """Classe especializada para processamento de eventos"""
    
    @staticmethod
    def parse_titulo_completo(titulo: str) -> Dict[str, Any]:
        """Parse completo do título do evento com todas as informações"""
        resultado = {
            "titulo_original": titulo,
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
            
            # Mapeamento de POIs
            poi_map = {
                "PAAGUACLARA": "P.A. Água Clara",
                "CARREGAMENTOFABRICARRP": "Fábrica RRP",
                "OFICINAJSL": "Oficina JSL",
                "TERMINALINOCENCIA": "Terminal Inocência"
            }
            
            # Mapeamento de tipos
            tipo_map = {
                "Informativo": "Alerta Informativo",
                "N1": "Tratativa N1", "N2": "Tratativa N2",
                "N3": "Tratativa N3", "N4": "Tratativa N4"
            }
            
            # Processa POI
            poi_amigavel = next((v for k, v in poi_map.items() if k in poi_raw), poi_raw.title())
            
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
        """Calcula tempo decorrido desde a entrada"""
        resultado = {
            "horas": 0,
            "texto_formatado": "0h",
            "status_tempo": "normal",  # normal, atencao, critico
            "data_entrada_valida": False
        }
        
        if not data_entrada or str(data_entrada).strip() == "":
            return resultado
        
        try:
            from datetime import datetime
            import pytz
            
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
    def determinar_motivos_por_poi(poi_amigavel: str) -> list:
        """Determina motivos disponíveis baseado no POI"""
        if poi_amigavel == "P.A. Água Clara":
            return config.motivos_poi["PA Agua Clara"]
        elif "MANUTEN" in poi_amigavel.upper():
            return config.motivos_poi["Manutenção"]
        elif "TERMINAL" in poi_amigavel.upper():
            return config.motivos_poi["Terminal"]
        elif "FÁBRICA" in poi_amigavel.upper() or "FABRICA" in poi_amigavel.upper():
            return config.motivos_poi["Fábrica"]
        else:
            return ["Outros"]
    
    @staticmethod
    def validar_acesso_usuario(poi_amigavel: str, areas_usuario: list) -> bool:
        """Verifica se usuário tem acesso ao POI"""
        if not areas_usuario:
            return False
        
        for area in areas_usuario:
            if (area.strip().lower() in poi_amigavel.strip().lower() or 
                poi_amigavel.strip().lower() in area.strip().lower()):
                return True
        
        return False
    
    @staticmethod
    def calcular_status_evento(df_evento: pd.DataFrame, alteracoes_pendentes: Dict) -> str:
        """Calcula status do evento baseado no preenchimento de TODOS os registros"""
        if df_evento.empty:
            return "Pendente"

        evento_titulo = df_evento["Titulo"].iloc[0] if "Titulo" in df_evento.columns else ""
        
        # CORREÇÃO: Verifica se TODOS os registros estão preenchidos
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

            # CORREÇÃO: Se qualquer registro não estiver completo, retorna "Pendente"
            motivo_ok = motivo_atual and motivo_atual.strip() != ""
            previsao_ok = previsao_atual and previsao_atual.strip() != ""
            
            if not (motivo_ok and previsao_ok):
                return "Pendente"  # Se qualquer registro estiver incompleto, todo o evento fica pendente

        # Se chegou aqui, todos os registros estão completos
        return "Preenchido"


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
            
            # CORREÇÃO: Normaliza valores "None" e "— Selecione —" ANTES de aplicar alterações
            if motivo_atual.lower() in ("none", "— selecione —"):
                motivo_atual = ""
            if obs_atual.lower() == "none":
                obs_atual = ""
            
            # Aplica alterações pendentes
            if chave_alteracao in alteracoes_pendentes:
                alteracoes = alteracoes_pendentes[chave_alteracao]
                if "Motivo" in alteracoes:
                    motivo_pendente = str(alteracoes["Motivo"]).strip()
                    # CORREÇÃO: Normaliza também as alterações pendentes
                    if motivo_pendente.lower() in ("none", "— selecione —"):
                        motivo_atual = ""
                    else:
                        motivo_atual = motivo_pendente
                if "Observacoes" in alteracoes:
                    obs_pendente = str(alteracoes["Observacoes"]).strip()
                    # CORREÇÃO: Normaliza também as observações pendentes
                    if obs_pendente.lower() == "none":
                        obs_atual = ""
                    else:
                        obs_atual = obs_pendente
            
            # CORREÇÃO CRÍTICA: Só valida se motivo não estiver vazio E for "outros"
            if motivo_atual and motivo_atual.lower() == "outros":
                validacao_obs = DataValidator.validar_observacao_obrigatoria(motivo_atual, obs_atual)
                if not validacao_obs["valido"]:
                    resultado["erros"].append(f"• Placa {placa}: {validacao_obs['erro']}")
        
        if resultado["erros"]:
            resultado["valido"] = False
        
        return resultado

class DataFormatter:
    """Classe especializada para formatação de dados"""
    
    @staticmethod
    def formatar_valor_sharepoint(valor: Any, campo: str = None) -> Any:
        """Formata valor para envio ao SharePoint"""
        if valor == "— Selecione —":
            return ""
        
        if campo == "Previsao_Liberacao":
            if valor is None or str(valor).strip() == "" or str(valor).lower() in ("none", "nat"):
                return None
            
            if isinstance(valor, pd.Timestamp) or isinstance(valor, datetime):
                return valor.strftime("%Y-%m-%dT%H:%M:%S")
            
            try:
                if "/" in str(valor):
                    dt = datetime.strptime(str(valor).strip(), "%d/%m/%Y %H:%M")
                    return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except:
                pass
            
            return str(valor).strip() if valor else None
        else:
            if valor is None or str(valor).lower() in ("none", "nat"):
                return ""
            return str(valor).strip()
    
    @staticmethod
    def formatar_data_exibicao(valor: Any) -> str:
        """Formata data para exibição na interface"""
        if pd.isnull(valor) or str(valor).strip().lower() in ("none", ""):
            return ""
        
        try:
            if isinstance(valor, str):
                try:
                    dt = datetime.strptime(valor, "%d/%m/%Y %H:%M")
                    dt = pytz.timezone("America/Campo_Grande").localize(dt)
                except ValueError:
                    dt = pd.to_datetime(valor, errors="coerce", utc=True)
            else:
                dt = pd.to_datetime(valor, errors="coerce", utc=True)
            
            if pd.isnull(dt):
                return str(valor)
            
            if dt.tzinfo is None:
                dt = pytz.timezone("America/Campo_Grande").localize(dt)
            else:
                dt = dt.tz_convert("America/Campo_Grande")
            
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return str(valor)
    
    @staticmethod
    def formatar_tempo_decorrido(horas: float) -> str:
        """Formata tempo decorrido para exibição"""
        if horas == 0:
            return "0h"
        elif horas < 1:
            minutos = int(horas * 60)
            return f"{minutos}min"
        elif horas < 24:
            return f"{horas:.1f}h"
        else:
            dias = int(horas // 24)
            horas_restantes = horas % 24
            if horas_restantes < 1:
                return f"{dias}d"
            else:
                return f"{dias}d {horas_restantes:.0f}h"
    
    @staticmethod
    def safe_str(valor: Any) -> str:
        """Converte valor para string de forma segura"""
        if pd.isnull(valor) or valor is None:
            return ""
        return str(valor)


# Funções para detecção de tamanho de tela desktop
def get_screen_size(page_width=None):
    """Detecta o tamanho da tela para ajustes responsivos em desktop"""
    try:
        # Tenta obter a largura da página de forma segura
        if page_width is not None:
            width = float(page_width)
        else:
            width = 1400  # valor padrão
    except (ValueError, TypeError, AttributeError):
        # Se houver qualquer erro na conversão, usa valor padrão
        width = 1400
    
    # Garante que width é um número válido
    if not isinstance(width, (int, float)) or width <= 0:
        width = 1400
    
    if width >= 1920:
        return "large"  # Telas grandes (1920px+)
    elif width >= 1366:
        return "medium"  # Telas médias (1366-1919px)
    else:
        return "small"   # Telas pequenas (até 1365px)


def is_small_screen(page_width=None):
    return get_screen_size(page_width) == "small"

def is_medium_screen(page_width=None):
    return get_screen_size(page_width) == "medium"

def is_large_screen(page_width=None):
    return get_screen_size(page_width) == "large"


class SharePointClient:
    @staticmethod
    def carregar_lista(list_name, limite=2000):
        tentativas = 0
        max_tentativas = 3
        
        while tentativas < max_tentativas:
            try:
                ctx = ClientContext(config.site_url).with_credentials(UserCredential(config.username_sp, config.password_sp))
                sp_list = ctx.web.lists.get_by_title(list_name)
                items = sp_list.items.top(limite).get().execute_query()
                
                data = [item.properties for item in items]
                df = pd.DataFrame(data)
                return df
            except Exception as e:
                tentativas += 1
                if tentativas < max_tentativas:
                    import time
                    time.sleep(2)
                else:
                    # APENAS log crítico de falha definitiva
                    logger.error(f"❌ CRÍTICO: Falha ao carregar '{list_name}' após {max_tentativas} tentativas: {str(e)}")
                    return pd.DataFrame()

    @staticmethod
    def atualizar_item(item_id, dados):
        try:
            ctx = ClientContext(config.site_url).with_credentials(UserCredential(config.username_sp, config.password_sp))
            sp_list = ctx.web.lists.get_by_title(config.desvios_list)
            item = sp_list.get_item_by_id(item_id)
            
            for campo, valor in dados.items():
                item.set_property(campo, valor)
            item.update().execute_query()
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar item {item_id}: {str(e)}")
            return False
        
    @staticmethod
    def atualizar_lote(atualizacoes):
        """
        Atualiza múltiplos itens em paralelo para melhor performance
        atualizacoes: lista de tuplas (id, dados)
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def atualizar_item_thread(item_id, dados):
            return SharePointClient.atualizar_item(item_id, dados)
        
        sucessos = 0
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(atualizar_item_thread, item_id, dados): item_id 
                    for item_id, dados in atualizacoes}
            
            for future in as_completed(futures):
                if future.result():
                    sucessos += 1
        
        return sucessos
    
def gerar_opcoes_previsao():
    """Gera opções de data e hora para o dropdown de previsão"""
    from datetime import datetime, timedelta
    import pytz
    
    opcoes = [ft.dropdown.Option("", "— Selecione —")]
    
    # Timezone do Brasil
    tz_brasil = pytz.timezone("America/Campo_Grande")
    agora = datetime.now(tz_brasil)
    
    # Gera opções para as próximas 48 horas, de 2 em 2 horas
    for i in range(0, 49, 2):  # 0, 2, 4, 6... até 48 horas
        data_opcao = agora + timedelta(hours=i)
        
        # Formata para exibição
        if i == 0:
            texto_exibicao = f"Agora ({data_opcao.strftime('%d/%m %H:%M')})"
        elif i < 24:
            texto_exibicao = f"Hoje {data_opcao.strftime('%H:%M')} ({data_opcao.strftime('%d/%m')})"
        elif i < 48:
            texto_exibicao = f"Amanhã {data_opcao.strftime('%H:%M')} ({data_opcao.strftime('%d/%m')})"
        else:
            texto_exibicao = data_opcao.strftime('%d/%m/%Y %H:%M')
        
        # Valor no formato que o SharePoint espera
        valor_sharepoint = data_opcao.strftime('%d/%m/%Y %H:%M')
        
        opcoes.append(ft.dropdown.Option(valor_sharepoint, texto_exibicao))
    
    return opcoes

class DataUtils:
    @staticmethod
    def processar_desvios(df):
        if df.empty:
            return df

        if "Tipo_Alerta" in df.columns:
            df["Tipo_Alerta"] = df["Tipo_Alerta"].str.strip().str.lower().replace({
                "informativo": "Alerta Informativo",
                "alerta informativo": "Alerta Informativo",
                "n1": "Tratativa N1", "tratativa n1": "Tratativa N1",
                "n2": "Tratativa N2", "tratativa n2": "Tratativa N2",
                "n3": "Tratativa N3", "tratativa n3": "Tratativa N3",
                "n4": "Tratativa N4", "tratativa n4": "Tratativa N4"
            })
        else:
            df["Tipo_Alerta"] = "Alerta Informativo"

        if "Previsao_Liberacao" in df.columns:
            df["Previsao_Liberacao"] = pd.to_datetime(df["Previsao_Liberacao"], errors="coerce", utc=True)
            try:
                df["Previsao_Liberacao"] = df["Previsao_Liberacao"].dt.tz_convert("America/Campo_Grande")
            except:
                pass

        rename_map = {
            "Title": "Titulo",
            "Ponto_de_Interesse": "PontodeInteresse",
            "Data_Hora_Entrada": "Data/Hora Entrada",
            "Data Entrada": "Data/Hora Entrada"
        }
        df = df.rename(columns=rename_map)

        colunas_necessarias = ["Observacoes", "Status", "Motivo"]
        for col in colunas_necessarias:
            if col not in df.columns:
                df[col] = ""

        return df

    @staticmethod
    def parse_titulo(titulo):
        partes = titulo.split('_')
        if len(partes) < 5:
            return "", "", ""

        tipo = partes[-3]
        poi_raw = partes[1].upper()
        data_str = partes[-2]
        hora_str = partes[-1]

        poi_map = {
            "PAAGUACLARA": "P.A. Água Clara",
            "CARREGAMENTOFABRICARRP": "Fábrica RRP",
            "OFICINAJSL": "Oficina JSL",
            "TERMINALINOCENCIA": "Terminal Inocência"
        }
        poi_amigavel = next((v for k, v in poi_map.items() if k in poi_raw), poi_raw.title())

        tipo_map = {
            "Informativo": "Alerta Informativo",
            "N1": "Tratativa N1", "N2": "Tratativa N2",
            "N3": "Tratativa N3", "N4": "Tratativa N4"
        }
        tipo_amigavel = tipo_map.get(tipo, tipo)

        try:
            datahora = datetime.strptime(data_str + "_" + hora_str, "%d%m%Y_%H%M%S")
            datahora_fmt = datahora.strftime("%d/%m %H:00")
        except:
            datahora_fmt = f"{data_str} {hora_str}"

        return tipo_amigavel, poi_amigavel, datahora_fmt

    @staticmethod
    def obter_areas_usuario(usuario):
        areas = usuario.get("Area", "")
        if isinstance(areas, list):
            return [a.strip().lower() for a in areas if a]
        if isinstance(areas, str):
            return [a.strip().lower() for a in re.split(r'[;\n]+', areas) if a.strip()]
        return []

    @staticmethod
    def formatar_data(valor):
        if pd.isnull(valor) or str(valor).strip().lower() in ("none", ""):
            return ""
        
        try:
            if isinstance(valor, str):
                try:
                    dt = datetime.strptime(valor, "%d/%m/%Y %H:%M")
                    dt = pytz.timezone("America/Campo_Grande").localize(dt)
                except ValueError:
                    dt = pd.to_datetime(valor, errors="coerce", utc=True)
            else:
                dt = pd.to_datetime(valor, errors="coerce", utc=True)

            if pd.isnull(dt):
                return str(valor)

            if dt.tzinfo is None:
                dt = pytz.timezone("America/Campo_Grande").localize(dt)
            else:
                dt = dt.tz_convert("America/Campo_Grande")

            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return str(valor)

def main(page: ft.Page):
    page.title = "Painel Logístico Suzano"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = ft.colors.GREY_50
    page.window_width = 1400
    page.window_maximized = True

    def carregar_dados_iniciais():
        try:
            logger.info("Iniciando carregamento de dados de usuários...")
            app_state.df_usuarios = SharePointClient.carregar_lista(config.usuarios_list)
            
            if not app_state.df_usuarios.empty:
                logger.info(f"✅ {len(app_state.df_usuarios)} usuários carregados com sucesso")
                return True
            else:
                logger.warning("⚠️ Nenhum usuário encontrado na lista")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados iniciais: {str(e)}")
            return False

    def mostrar_mensagem(texto, erro=False):
        cor = ft.colors.RED_400 if erro else ft.colors.GREEN_400
        
        # Cria snackbar mais visível
        snack = ft.SnackBar(
            content=ft.Text(
                texto, 
                size=16, 
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE
            ), 
            bgcolor=cor, 
            action="OK",
            duration=4000,  # 4 segundos
            show_close_icon=True
        )
        
        page.snack_bar = snack
        snack.open = True
        page.update()

    def carregar_dados():
        try:
            print("\n" + "=" * 60)
            print("🔄 [SENTINELA] CARREGANDO DADOS DO PAINEL")
            print("=" * 60)
            print("🔄 [SISTEMA] Atualizando dados...")

            # Marca carregamento em progresso
            app_state.carregamento_em_progresso = True

            # Carrega usuários (sem logs detalhados)
            app_state.df_usuarios = SharePointClient.carregar_lista(config.usuarios_list)

            # Carrega desvios (sem logs detalhados)
            app_state.df_desvios = SharePointClient.carregar_lista(config.desvios_list)

            # Processa desvios
            app_state.df_desvios = DataUtils.processar_desvios(app_state.df_desvios)

            # Marca dados como carregados
            app_state.dados_carregados = True
            app_state.carregamento_em_progresso = False

            logger.info(f"✅ Dados atualizados: {len(app_state.df_usuarios)} usuários, {len(app_state.df_desvios)} desvios")

            return True

        except Exception as e:
            app_state.carregamento_em_progresso = False
            logger.error(f"❌ Erro ao carregar dados: {str(e)}")
            return False

    def validar_login(email, senha):
        if app_state.df_usuarios.empty:
            logger.warning("Tentativa de login com dados de usuários vazios")
            return False, None

        logger.info(f"Tentativa de login para: {email}")

        # Busca coluna de email
        email_columns = [col for col in app_state.df_usuarios.columns if 'email' in col.lower()]
        if not email_columns:
            return False, None

        email_col = email_columns[0]

        # Busca usuário
        email_normalizado = email.strip().lower()
        df_usuarios_temp = app_state.df_usuarios.copy()
        df_usuarios_temp['email_normalizado'] = df_usuarios_temp[email_col].astype(str).str.strip().str.lower()
        
        usuario_df = df_usuarios_temp[df_usuarios_temp['email_normalizado'] == email_normalizado]
        
        if not usuario_df.empty:
            user_data = usuario_df.iloc[0]
            
            # Busca coluna de senha
            senha_columns = [col for col in user_data.index if any(palavra in col.lower() for palavra in ['senha', 'password', 'pass'])]
            
            if senha_columns:
                senha_col = senha_columns[0]
                senha_bd = str(user_data[senha_col]).strip()
                senha_input = str(senha).strip()
                
                if senha_input == senha_bd:
                    logger.info(f"✅ Login bem-sucedido para: {email}")
                    return True, user_data.to_dict()

                logger.warning(f"❌ Senha incorreta para: {email}")
                return False, None
        
        return False, None

    def fazer_login(e):
        email = email_field.value.strip()
        senha = password_field.value.strip()

        if not email or not senha:
            mostrar_mensagem("Preencha email e senha", True)
            return

        # Primeiro valida o login com dados já carregados
        try:
            sucesso, user_data = validar_login(email, senha)

            if not sucesso:
                mostrar_mensagem("Login inválido", True)
                return

            # Login válido - armazena no estado
            app_state.usuario = user_data
            nome_exibicao = app_state.get_nome_usuario()
            
            # Configurações responsivas para tela de carregamento
            try:
                current_width = page.window_width
                current_height = page.window_height
            except:
                current_width = 1400
                current_height = 800

            screen_size = get_screen_size(current_width)

            if screen_size == "small":
                circulo_size = 180
                logo_size = 160
                welcome_size = 18
                loading_size = 14
                subtitle_size = 12
                spacing_text = 30  # Reduzido de 150 para 120
            elif screen_size == "medium":
                circulo_size = 240
                logo_size = 220
                welcome_size = 20
                loading_size = 15
                subtitle_size = 13
                spacing_text = 175  # Mantido
            else:  # large
                circulo_size = 300
                logo_size = 280
                welcome_size = 24
                loading_size = 16
                subtitle_size = 14
                spacing_text = 200  # Mantido

            loading_pos_login = ft.Container(
            content=ft.Column([
                # Espaço flexível acima
                ft.Container(expand=True),
                
                # Container das imagens centralizadas
                ft.Container(
                    content=ft.Stack([
                        # GIF de fundo (loader animado)
                        ft.Container(
                            content=ft.Image(
                                src="images/circulo.png",
                                width=circulo_size,
                                height=circulo_size,
                                fit=ft.ImageFit.CONTAIN
                            ),
                            alignment=ft.alignment.center
                        ),
                        # Logo centralizada sobre o círculo
                        ft.Container(
                            content=ft.Image(
                                src="images/sentinela.png",
                                width=logo_size,
                                height=logo_size,
                                fit=ft.ImageFit.CONTAIN
                            ),
                            alignment=ft.alignment.center
                        )
                    ]),
                    height=circulo_size,  # Altura fixa baseada no tamanho do círculo
                    alignment=ft.alignment.center
                ),
                
                # Espaçamento entre imagens e textos
                ft.Container(height=30),
                
                # Textos posicionados abaixo das imagens
                ft.Column([
                    ft.Text(
                        f"Bem-vindo, {nome_exibicao}!",
                        size=welcome_size,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_800,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Carregando seu painel...",
                        size=loading_size,
                        color=ft.colors.BLUE_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Aguarde alguns instantes",
                        size=subtitle_size,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                
                # Espaço flexível abaixo
                ft.Container(expand=True)
            ]),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.WHITE,
            expand=True
        )
            
            page.clean()
            page.add(loading_pos_login)
            page.update()
            
            # Carrega dados atualizados em background
            import threading
            def carregar_e_mostrar():
                try:
                    sucesso_dados = carregar_dados()
                    if sucesso_dados:
                        mostrar_painel()
                    else:
                        # Configurações responsivas para tela de erro
                        screen_size = get_screen_size(current_width)

                        if screen_size == "small":
                            icon_size = 60
                            title_size = 16
                            subtitle_size = 12
                            button_width = 200
                        elif screen_size == "medium":
                            icon_size = 70
                            title_size = 18
                            subtitle_size = 13
                            button_width = 250
                        else:  # large
                            icon_size = 80
                            title_size = 20
                            subtitle_size = 14
                            button_width = 300

                        erro_dados = ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.ERROR, size=icon_size, color=ft.colors.RED_600),
                                ft.Text("Erro ao carregar dados", size=title_size, weight=ft.FontWeight.BOLD),
                                ft.Text("Verifique sua conexão com a internet", size=subtitle_size, color=ft.colors.GREY_600),
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "Tentar Novamente",
                                    on_click=lambda e: carregar_e_mostrar(),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=button_width
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            bgcolor=ft.colors.GREY_50
                        )

                        page.add(erro_dados)
                        page.update()
                except Exception as ex:
                    page.clean()
                    erro_exception = ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.ERROR, size=80, color=ft.colors.RED_600),
                            ft.Text("Erro inesperado", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Detalhes: {str(ex)}", size=12, color=ft.colors.GREY_600),
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "Tentar Novamente",
                                on_click=lambda e: carregar_e_mostrar(),
                                bgcolor=ft.colors.BLUE_600,
                                color=ft.colors.WHITE
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        bgcolor=ft.colors.GREY_50
                    )
                    page.add(erro_exception)
                    page.update()
            
            # Executa carregamento em thread separada para não travar a UI
            thread_carregamento = threading.Thread(target=carregar_e_mostrar, daemon=True)
            thread_carregamento.start()
        
        except Exception as ex:
            mostrar_mensagem(f"Erro ao processar login: {str(ex)}", True)

    def criar_cards_dashboard():
        tipos = ["Alerta Informativo", "Tratativa N1", "Tratativa N2", "Tratativa N3", "Tratativa N4"]
        
        # Cores principais e gradientes modernos
        configuracoes_cores = {
            "Alerta Informativo": {
                "cor_principal": ft.colors.BLUE_600,
                "cor_gradient_start": "#4A90E2",
                "cor_gradient_end": "#357ABD",
                "cor_accent": "#3B82F6",
                "cor_text": ft.colors.WHITE,
                "cor_background": "#F0F7FF"
            },
            "Tratativa N1": {
                "cor_principal": ft.colors.ORANGE_600,
                "cor_gradient_start": "#FF9500",
                "cor_gradient_end": "#FF7A00",
                "cor_accent": "#F97316",
                "cor_text": ft.colors.WHITE,
                "cor_background": "#FFF4E6"
            },
            "Tratativa N2": {
                "cor_principal": ft.colors.RED_600,
                "cor_gradient_start": "#FF4757",
                "cor_gradient_end": "#FF3742",
                "cor_accent": "#EF4444",
                "cor_text": ft.colors.WHITE,
                "cor_background": "#FFEBEE"
            },
            "Tratativa N3": {
                "cor_principal": ft.colors.RED_800,
                "cor_gradient_start": "#C53030",
                "cor_gradient_end": "#9B2C2C",
                "cor_accent": "#DC2626",
                "cor_text": ft.colors.WHITE,
                "cor_background": "#FFEBEE"
            },
            "Tratativa N4": {
                "cor_principal": ft.colors.PURPLE_600,
                "cor_gradient_start": "#8B5CF6",
                "cor_gradient_end": "#7C3AED",
                "cor_accent": "#9333EA",
                "cor_text": ft.colors.WHITE,
                "cor_background": "#F3E8FF"
            }
        }
        
        icones_png = {
            "Alerta Informativo": "info.png",
            "Tratativa N1": "N1.png",
            "Tratativa N2": "N2.png",
            "Tratativa N3": "N3.png",
            "Tratativa N4": "N4.png"
        }

        # APLICAR FILTRO POR ÁREA DO USUÁRIO
        perfil = app_state.get_perfil_usuario()
        areas = app_state.get_areas_usuario()

        # Filtrar dados baseado no perfil e áreas do usuário
        df_nao_aprovados = app_state.df_desvios[app_state.df_desvios["Status"].ne("Aprovado")] if "Status" in app_state.df_desvios.columns else app_state.df_desvios
        
        # Se o usuário não é aprovador nem torre, filtrar por área
        if perfil not in ("aprovador", "torre"):
            # Filtrar registros baseado nas áreas do usuário
            df_filtrado = pd.DataFrame()
            
            for _, row in df_nao_aprovados.iterrows():
                evento_titulo = row.get("Titulo", "")
                if evento_titulo:
                    try:
                        # Parse do título para obter o POI
                        evento_info = EventoProcessor.parse_titulo_completo(evento_titulo)
                        tipo_amigavel = evento_info["tipo_amigavel"]
                        poi_amigavel = evento_info["poi_amigavel"]
                        datahora_fmt = evento_info["datahora_fmt"]
                        
                        # Verificar se o usuário tem acesso a este POI
                        match_encontrado = False
                        for area in areas:
                            if area.strip().lower() in poi_amigavel.strip().lower() or poi_amigavel.strip().lower() in area.strip().lower():
                                match_encontrado = True
                                break
                        
                        # Se tem acesso, incluir no DataFrame filtrado
                        if match_encontrado:
                            df_filtrado = pd.concat([df_filtrado, row.to_frame().T], ignore_index=True)
                            
                    except Exception:
                        # Se der erro no parse, pula este registro
                        continue
            
            # Usar dados filtrados
            df_nao_aprovados = df_filtrado
        
        # Agrupamentos para métricas (agora com dados filtrados)
        df_eventos = df_nao_aprovados.drop_duplicates(subset=["Titulo"]) if not df_nao_aprovados.empty else pd.DataFrame()
        contadores_eventos = df_eventos.groupby("Tipo_Alerta")["Titulo"].nunique().reset_index(name="Count_Eventos") if not df_eventos.empty else pd.DataFrame()
        
        # Contagem total de registros (todos os itens, não apenas eventos únicos)
        contadores_registros = df_nao_aprovados.groupby("Tipo_Alerta").size().reset_index(name="Count_Registros") if not df_nao_aprovados.empty else pd.DataFrame()

        # Função para calcular tempo médio
        def calcular_tempo_medio(df_tipo):
            """Calcula o tempo médio em horas usando EventoProcessor"""
            if df_tipo.empty:
                return 0
            
            tempos = []
            for _, row in df_tipo.iterrows():
                data_entrada_str = row.get("Data/Hora Entrada", "")
                tempo_info = EventoProcessor.calcular_tempo_decorrido(data_entrada_str)
                if tempo_info["data_entrada_valida"]:
                    tempos.append(tempo_info["horas"])
            
            return sum(tempos) / len(tempos) if tempos else 0

        # Calcula métricas para cada tipo (com dados filtrados)
        metricas_tipos = {}
        for tipo in tipos:
            df_tipo = df_nao_aprovados[df_nao_aprovados["Tipo_Alerta"] == tipo] if not df_nao_aprovados.empty else pd.DataFrame()
            
            count_eventos = int(contadores_eventos[contadores_eventos["Tipo_Alerta"] == tipo]["Count_Eventos"].values[0]) if not contadores_eventos.empty and tipo in contadores_eventos["Tipo_Alerta"].values else 0
            count_registros = int(contadores_registros[contadores_registros["Tipo_Alerta"] == tipo]["Count_Registros"].values[0]) if not contadores_registros.empty and tipo in contadores_registros["Tipo_Alerta"].values else 0
            tempo_medio_horas = calcular_tempo_medio(df_tipo)
            
            metricas_tipos[tipo] = {
                "eventos": count_eventos,
                "registros": count_registros,
                "tempo_medio": tempo_medio_horas
            }

        def formatar_tempo(horas):
            """Formata tempo usando DataFormatter"""
            return DataFormatter.formatar_tempo_decorrido(horas)

        cards = []
        
        # Configurações responsivas
        try:
            current_width = page.window_width
        except:
            current_width = None

        screen_size = get_screen_size(current_width)
        
        if screen_size == "small":
            spacing = 12
            card_width = 180
            card_height = 140
            number_size = 24
            title_size = 11
            icon_size = 14
            metric_size = 10
            padding = 16
            badge_size = 50
        elif screen_size == "medium":
            spacing = 16
            card_width = 200
            card_height = 160
            number_size = 28
            title_size = 12
            icon_size = 16
            metric_size = 11
            padding = 18
            badge_size = 55
        else:  # large
            spacing = 20
            card_width = 220
            card_height = 180
            number_size = 32
            title_size = 13
            icon_size = 18
            metric_size = 12
            padding = 20
            badge_size = 60

        for tipo in tipos:
            metricas = metricas_tipos[tipo]
            count_eventos = metricas["eventos"]
            count_registros = metricas["registros"] 
            tempo_medio = metricas["tempo_medio"]
            
            config = configuracoes_cores[tipo]
            icone_png = icones_png.get(tipo, "info.png")
            
            # SISTEMA DE ALERTAS BASEADO NO TEMPO MÉDIO
            tempo_em_minutos = tempo_medio * 60
            
            # Definir estado do alerta baseado no tempo
            if tipo != "Alerta Informativo":  # Alertas informativos não têm limite de tempo
                if tempo_em_minutos >= 90:  # 1:30h ou mais - CRÍTICO
                    alerta_estado = "critico"
                    card_border_color = ft.colors.RED_400
                    card_border_width = 3
                    opacity = 1.0
                elif tempo_em_minutos >= 45:  # 45min+ - ATENÇÃO
                    alerta_estado = "atencao"
                    card_border_color = ft.colors.ORANGE_400
                    card_border_width = 2
                    opacity = 1.0
                else:  # Tempo normal
                    alerta_estado = "normal"
                    card_border_color = ft.colors.with_opacity(0.1, ft.colors.GREY_400)
                    card_border_width = 1
                    opacity = 1.0 if count_eventos > 0 else 0.6
            else:
                # Alerta Informativo não tem limites de tempo
                alerta_estado = "normal"
                card_border_color = ft.colors.with_opacity(0.1, ft.colors.GREY_400)
                card_border_width = 1
                opacity = 1.0 if count_eventos > 0 else 0.6
            
            # Header simples com ícone + título (SEM badges de alerta)
            header_row = ft.Row([
                ft.Image(
                    src=f"images/{icone_png}",
                    width=icon_size,
                    height=icon_size,
                    fit=ft.ImageFit.CONTAIN
                ),
                ft.Text(
                    tipo,
                    size=title_size,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                )
            ], spacing=4, alignment=ft.MainAxisAlignment.START)
            
            # Badge de contagem (quadrado arredondado) - eventos únicos
            # Modificar cor de fundo se crítico
            badge_bg_color = config["cor_principal"]
            if alerta_estado == "critico" and count_eventos > 0:
                badge_bg_color = ft.colors.RED_600
            elif alerta_estado == "atencao" and count_eventos > 0:
                badge_bg_color = ft.colors.ORANGE_600
            
            badge_numero = ft.Container(
                content=ft.Text(
                    str(count_eventos),
                    size=number_size,
                    weight=ft.FontWeight.BOLD,
                    color=config["cor_text"]
                ),
                width=badge_size,
                height=badge_size,
                alignment=ft.alignment.center,
                bgcolor=badge_bg_color,
                border_radius=12,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.colors.with_opacity(0.3, badge_bg_color),
                    offset=ft.Offset(0, 4)
                )
            )
            
            # Métricas adicionais com destaque para tempo crítico
            tempo_texto = formatar_tempo(tempo_medio)
            tempo_cor = ft.colors.GREY_600
            tempo_weight = ft.FontWeight.W_500
            
            # Destacar tempo se estiver em alerta (mantém relógio + adiciona alerta após)
            if alerta_estado == "critico" and count_eventos > 0:
                tempo_cor = ft.colors.RED_600
                tempo_weight = ft.FontWeight.BOLD
                tempo_texto = f"⏱️ {tempo_texto} 🚨"
            elif alerta_estado == "atencao" and count_eventos > 0:
                tempo_cor = ft.colors.ORANGE_600
                tempo_weight = ft.FontWeight.BOLD
                tempo_texto = f"⏱️ {tempo_texto} ⚠️"
            else:
                tempo_texto = f"⏱️ {tempo_texto}"
            
            metricas_row = ft.Column([
                ft.Text(
                    f"📋 {count_registros} registros",
                    size=metric_size,
                    color=ft.colors.GREY_600,
                    weight=ft.FontWeight.W_500
                ),
                ft.Text(
                    tempo_texto,
                    size=metric_size,
                    color=tempo_cor,
                    weight=tempo_weight
                )
            ], 
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.START
            )
            
            # Layout vertical simples (SEM banner de alerta)
            card_content = ft.Column([
                header_row,  # Ícone + título no topo
                ft.Container(height=8),  # Espaçamento entre header e número
                badge_numero,  # Número de eventos
                ft.Container(height=8),  # Espaçamento entre número e métricas
                metricas_row  # Métricas adicionais
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.START
            )
            
            # Função de hover effect
            def create_hover_effect(card_container, original_shadow, hover_shadow):
                def on_hover(e):
                    if e.data == "true":  # Mouse enter
                        card_container.shadow = hover_shadow
                        card_container.scale = 1.02
                    else:  # Mouse leave
                        card_container.shadow = original_shadow
                        card_container.scale = 1.0
                    card_container.update()
                return on_hover
            
            # Sombras para efeito hover (mais intensas se em alerta)
            if alerta_estado == "critico" and count_eventos > 0:
                original_shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.colors.with_opacity(0.3, ft.colors.RED_400),
                    offset=ft.Offset(0, 4)
                )
                hover_shadow = ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=25,
                    color=ft.colors.with_opacity(0.4, ft.colors.RED_400),
                    offset=ft.Offset(0, 8)
                )
            elif alerta_estado == "atencao" and count_eventos > 0:
                original_shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.colors.with_opacity(0.3, ft.colors.ORANGE_400),
                    offset=ft.Offset(0, 4)
                )
                hover_shadow = ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=25,
                    color=ft.colors.with_opacity(0.4, ft.colors.ORANGE_400),
                    offset=ft.Offset(0, 8)
                )
            else:
                original_shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                    offset=ft.Offset(0, 4)
                )
                hover_shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.colors.with_opacity(0.15, config["cor_principal"]),
                    offset=ft.Offset(0, 8)
                )
            
            # Container principal com alertas visuais (altura normal, sem espaço extra para banner)
            card = ft.Container(
                content=card_content,
                width=card_width,
                height=card_height,  # Altura normal sem ajuste extra
                padding=padding,
                bgcolor=ft.colors.WHITE,
                border_radius=16,
                shadow=original_shadow,
                border=ft.border.all(
                    width=card_border_width,
                    color=card_border_color
                ),
                opacity=opacity,
                animate_scale=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
            )
            
            # Adiciona efeito hover
            card.on_hover = create_hover_effect(card, original_shadow, hover_shadow)
            
            cards.append(card)

        # Container principal dos cards com layout responsivo
        cards_container = ft.Container(
            content=ft.Row(
                cards,
                spacing=spacing,
                scroll=ft.ScrollMode.AUTO,
                wrap=False,
                alignment=ft.MainAxisAlignment.START
            ),
            margin=ft.margin.only(top=8, bottom=8),
            padding=ft.padding.symmetric(horizontal=4)
        )

        return cards_container

    def aprovar_evento(evento):
        def confirmar_aprovacao(e):
            # Fecha o dialog de confirmação
            page.dialog.open = False
            page.update()
            
            # Mostra feedback imediato
            mostrar_mensagem("⏳ Aprovando evento...", False)

            # Processa aprovação em background
            import threading
            def processar_aprovacao():
                try:
                    df_evento = app_state.df_desvios[app_state.df_desvios["Titulo"] == evento]
                    if df_evento.empty:
                        return

                    # Coleta todas as atualizações em lote
                    atualizacoes_aprovacao = []
                    for _, row in df_evento.iterrows():
                        dados = {"Status": "Aprovado"}
                        atualizacoes_aprovacao.append((int(row["ID"]), dados))

                    # Envia todas as aprovações em paralelo
                    if atualizacoes_aprovacao:
                        sucessos = SharePointClient.atualizar_lote(atualizacoes_aprovacao)
                        if sucessos > 0:
                            # Atualiza interface após conclusão
                            mostrar_mensagem("✅ Evento aprovado com sucesso!")
                            carregar_dados()
                            mostrar_painel()
                        else:
                            mostrar_mensagem("❌ Erro ao aprovar evento", True)
                except Exception as ex:
                    mostrar_mensagem(f"❌ Erro ao aprovar evento: {str(ex)}", True)

            # Executa processamento em thread separada
            thread_aprovacao = threading.Thread(target=processar_aprovacao, daemon=True)
            thread_aprovacao.start()

        def cancelar_aprovacao(e):
            # Fecha o dialog sem fazer nada
            page.dialog.open = False
            page.update()

        # Cria o dialog de confirmação
        confirmation_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color=ft.colors.GREEN_600, size=24),
                ft.Text("Confirmar Aprovação", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Tem certeza de que deseja aprovar este evento?",
                        size=16,
                        color=ft.colors.GREY_800
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"📋 Evento:",
                                size=12,
                                color=ft.colors.BLUE_800,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Container(height=3),
                            ft.Text(
                                f"{EventoProcessor.parse_titulo_completo(evento)['tipo_amigavel']} - {EventoProcessor.parse_titulo_completo(evento)['poi_amigavel']} - {EventoProcessor.parse_titulo_completo(evento)['datahora_fmt']}",
                                size=14,
                                color=ft.colors.BLUE_700,
                                weight=ft.FontWeight.W_500
                            )
                        ], spacing=0),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=6,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    ft.Container(height=5),
                    ft.Text(
                        "⚠️ Esta ação não pode ser desfeita.",
                        size=12,
                        color=ft.colors.ORANGE_600,
                        italic=True
                    )
                ], tight=True),
                width=400,
                padding=10
            ),
            actions=[
                ft.Row([
                    ft.TextButton(
                        "Não",
                        on_click=cancelar_aprovacao,
                        style=ft.ButtonStyle(color=ft.colors.GREY_600)
                    ),
                    ft.Container(width=80),  # Espaçamento de 80px entre os botões
                    ft.ElevatedButton(
                        "Sim, Aprovar",
                        on_click=confirmar_aprovacao,
                        bgcolor=ft.colors.GREEN_600,
                        color=ft.colors.WHITE,
                        icon=ft.icons.CHECK,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ],
            shape=ft.RoundedRectangleBorder(radius=8)
        )

        # Exibe o dialog
        page.dialog = confirmation_dialog
        confirmation_dialog.open = True
        page.update()


    def reprovar_evento(evento):
        justificativa_field = ft.TextField(label="Motivo da reprovação", multiline=True, width=800, height=120)

        def confirmar(e):
            if not justificativa_field.value.strip():
                mostrar_mensagem("Insira uma justificativa", True)
                return

            # Fecha o modal imediatamente para melhor UX
            modal.open = False
            page.update()
            
            # Mostra feedback imediato
            mostrar_mensagem("⏳ Reprovando evento...", False)
            
            # Processa reprovação em background
            import threading
            
            def processar_reprovacao():
                try:
                    df_evento = app_state.df_desvios[app_state.df_desvios["Titulo"] == evento]
                    
                    # Coleta todas as atualizações em lote
                    atualizacoes_reprovacao = []
                    for _, row in df_evento.iterrows():
                        dados = {"Status": "Reprovado", "Reprova": justificativa_field.value}
                        atualizacoes_reprovacao.append((int(row["ID"]), dados))
                    
                    # Envia todas as reprovações em paralelo
                    if atualizacoes_reprovacao:
                        SharePointClient.atualizar_lote(atualizacoes_reprovacao)
                    
                    # Atualiza interface após conclusão
                    mostrar_mensagem("✅ Evento reprovado com sucesso!")
                    carregar_dados()
                    mostrar_painel()
                    
                except Exception as ex:
                    mostrar_mensagem(f"❌ Erro ao reprovar evento: {str(ex)}", True)
            
            # Executa processamento em thread separada
            thread_reprovacao = threading.Thread(target=processar_reprovacao, daemon=True)
            thread_reprovacao.start()

        def fechar(e):
            modal.open = False
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reprovar Evento", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Motivo da reprovação:", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(height=10),
                    justificativa_field
                ]),
                width=800,
                height=180,
                padding=10,
                border_radius=4
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton("Confirmar", on_click=confirmar, bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE)
            ],
            shape=ft.RoundedRectangleBorder(radius=4)  # Bordas menos arredondadas
        )

        page.dialog = modal
        modal.open = True
        page.update()

    def criar_card_evento(evento, df_evento):
        font_size = 14
        field_height = 42

        def make_on_change_handler(chave, campo):
            def handler(e):
                valor = e.control.value
                if valor == "— Selecione —" or valor == "" or valor is None:
                    valor = ""
                atualizar_alteracao(chave, campo, valor)
            return handler

        # Garante que estado_expansao existe e inicializa o evento
        if not hasattr(app_state, 'estado_expansao') or app_state.estado_expansao is None:
            app_state.estado_expansao = {}
        if evento not in app_state.estado_expansao:
            app_state.estado_expansao[evento] = False

        def safe_str(x):
            return DataFormatter.safe_str(x)

        evento_info = EventoProcessor.parse_titulo_completo(evento)
        tipo_amigavel = evento_info["tipo_amigavel"]
        poi_amigavel = evento_info["poi_amigavel"]
        datahora_fmt = evento_info["datahora_fmt"]
        perfil = app_state.get_perfil_usuario()
        areas = app_state.get_areas_usuario()

        # Perfis "aprovador" e "torre" veem todos os eventos
        if perfil not in ("aprovador", "torre"):
            if not EventoProcessor.validar_acesso_usuario(poi_amigavel, areas):
                return None

        status = df_evento["Status"].iloc[0] if "Status" in df_evento.columns else "Pendente"

        if status == "Preenchido":
            status_texto = "Aguardando aprovação"
            status_cor = ft.colors.ORANGE_600
        elif status == "Reprovado":
            status_texto = "Reprovado - Preencha novamente"
            status_cor = ft.colors.PURPLE_600
        else:
            status_texto = "Aguardando preenchimento"
            status_cor = ft.colors.RED_600

        # Usando ícones PNG nos cards de eventos
        icones_eventos = {
            "Alerta Informativo": "info.png",
            "Tratativa N1": "N1.png",
            "Tratativa N2": "N2.png",
            "Tratativa N3": "N3.png",
            "Tratativa N4": "N4.png"
        }

        icone_arquivo = icones_eventos.get(tipo_amigavel, "info.png")

        def alternar_expansao(e):
            # Garante que estado_expansao existe
            if not hasattr(app_state, 'estado_expansao') or app_state.estado_expansao is None:
                app_state.estado_expansao = {}
            if evento not in app_state.estado_expansao:
                app_state.estado_expansao[evento] = False
            
            app_state.estado_expansao[evento] = not app_state.estado_expansao[evento]
            mostrar_painel()

        icone_expansao = ft.icons.KEYBOARD_ARROW_DOWN if app_state.estado_expansao[evento] else ft.icons.KEYBOARD_ARROW_RIGHT

        def limpar_texto_html(texto_html: str) -> str:
            """Remove tags HTML e decodifica entidades HTML"""
            import html
            import re
            
            if not texto_html:
                return ""
            
            # Remove tags HTML comuns
            texto = re.sub(r'<div[^>]*>', '', texto_html)  # Remove <div> com atributos
            texto = re.sub(r'</div>', '\n', texto)         # Substitui </div> por quebra de linha
            texto = re.sub(r'<br\s*/?>', '\n', texto)     # Substitui <br> por quebra de linha
            texto = re.sub(r'<p[^>]*>', '', texto)        # Remove <p> com atributos
            texto = re.sub(r'</p>', '\n\n', texto)        # Substitui </p> por dupla quebra
            texto = re.sub(r'<[^>]+>', '', texto)         # Remove qualquer outra tag HTML
            
            # Decodifica entidades HTML (&#58; vira :, &amp; vira &, etc.)
            texto = html.unescape(texto)
            
            # Limpa espaços extras e quebras desnecessárias
            texto = re.sub(r'\n\s*\n', '\n\n', texto)    # Remove linhas vazias extras
            texto = re.sub(r'^\s+|\s+$', '', texto)      # Remove espaços do início e fim
            
            return texto

        # Função para mostrar justificativa de reprovação
        def mostrar_justificativa_reprovacao(e):
            justificativa = ""
            if "Reprova" in df_evento.columns:
                primeira_justificativa = df_evento["Reprova"].iloc[0]
                if pd.notnull(primeira_justificativa) and str(primeira_justificativa).strip():
                    justificativa = str(primeira_justificativa).strip()
            
            if not justificativa:
                justificativa = "Justificativa não informada"
            else:
                # CORREÇÃO: Limpa HTML e decodifica entidades
                justificativa = limpar_texto_html(justificativa)
            
            modal_justificativa = ft.AlertDialog(
                modal=True,
                title=ft.Text("Motivo da Reprovação", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Text(
                        justificativa, 
                        size=14, 
                        selectable=True,
                        max_lines=None,  # Permite múltiplas linhas
                        overflow=ft.TextOverflow.VISIBLE,  # Mostra todo o texto
                        text_align=ft.TextAlign.LEFT
                    ),
                    width=450, 
                    height=200, 
                    padding=15
                ),
                actions=[ft.TextButton("Fechar", on_click=lambda e: fechar_modal_justificativa())],
                shape=ft.RoundedRectangleBorder(radius=4)  # Bordas menos arredondadas
            )
            
            def fechar_modal_justificativa():
                modal_justificativa.open = False
                page.update()
            
            page.dialog = modal_justificativa
            modal_justificativa.open = True
            page.update()

        # Lado esquerdo: botão expandir + texto do evento
        lado_esquerdo = ft.Row([
            ft.IconButton(icon=icone_expansao, on_click=alternar_expansao, tooltip="Expandir/Encolher"),
            ft.Row([
                ft.Image(src=f"images/{icone_arquivo}", width=18, height=18, fit=ft.ImageFit.CONTAIN),
                ft.Text(f"{tipo_amigavel} - {poi_amigavel} - {datahora_fmt}", size=14, weight=ft.FontWeight.BOLD)
            ], spacing=8)
        ], spacing=5)

        # Lado direito: status + botão de justificativa (se reprovado)
        if status == "Reprovado":
            lado_direito = ft.Row([
                ft.Text(status_texto, color=status_cor, weight=ft.FontWeight.BOLD, size=13),
                ft.IconButton(
                    icon=ft.icons.INFO_OUTLINE,
                    tooltip="Ver motivo da reprovação",
                    on_click=mostrar_justificativa_reprovacao,
                    icon_color=ft.colors.PURPLE_600,
                    bgcolor=ft.colors.PURPLE_50,
                    style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=4)
                )
            ], spacing=5)
        else:
            lado_direito = ft.Text(status_texto, color=status_cor, weight=ft.FontWeight.BOLD, size=13)

        header = ft.Container(
            content=ft.Row([lado_esquerdo, lado_direito], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=3, 
            bgcolor=ft.colors.RED_50,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )

        # Determinar motivos disponíveis usando EventoProcessor
        motivos = EventoProcessor.determinar_motivos_por_poi(poi_amigavel)

        table_rows = []
        pode_editar = perfil not in ("aprovador", "torre") and status != "Aprovado"

        df_evento_reset = df_evento.reset_index(drop=True)
        df_evento_reset = df_evento_reset.rename(columns={
            "Id": "ID", "id": "ID",
            "data/hora entrada": "Data/Hora Entrada",
            "data_entrada": "Data/Hora Entrada"
        })

        colunas_necessarias = ["ID", "Placa", "Data/Hora Entrada", "Motivo", "Previsao_Liberacao", "Observacoes"]
        colunas_faltando = [col for col in colunas_necessarias if col not in df_evento_reset.columns]
        for col in colunas_faltando:
            df_evento_reset[col] = ""

        df_exibir = df_evento_reset[colunas_necessarias].copy()
        df_exibir["Data/Hora Entrada"] = df_exibir["Data/Hora Entrada"].apply(DataFormatter.formatar_data_exibicao)
        df_exibir["Previsao_Liberacao"] = df_exibir["Previsao_Liberacao"].apply(DataFormatter.formatar_data_exibicao)

        # Configurações responsivas
        try:
            current_width = page.window_width
        except:
            current_width = None

        screen_size = get_screen_size(current_width)

        if screen_size == "small":
            motivo_width = 182
            previsao_width = 160
            obs_width = 380
            font_size = 12
            field_height = 38
        elif screen_size == "medium":
            motivo_width = 218
            previsao_width = 175
            obs_width = 450
            font_size = 13
            field_height = 40
        else:  # large
            motivo_width = 237
            previsao_width = 190
            obs_width = 600
            font_size = 14
            field_height = 42

        # NOVA IMPLEMENTAÇÃO DE DATEPICKER - MODAL APPROACH
        def criar_campo_data_hora(valor_inicial, chave_alteracao):
            """Cria campo de data/hora com modal personalizado"""
            
            # Parse do valor inicial
            data_inicial = None
            hora_inicial = "12:00"
            display_value = ""
            
            if valor_inicial and str(valor_inicial).strip():
                try:
                    if "/" in str(valor_inicial):
                        dt_parse = datetime.strptime(str(valor_inicial), "%d/%m/%Y %H:%M")
                    else:
                        dt_parse = pd.to_datetime(valor_inicial)
                    data_inicial = dt_parse.date()
                    hora_inicial = dt_parse.strftime("%H:%M")
                    display_value = f"{data_inicial.strftime('%d/%m/%Y')} {hora_inicial}"
                except:
                    pass

            # Campo de exibição
            campo_display = ft.TextField(
                value=display_value,
                hint_text="Clique para selecionar",
                width=previsao_width,
                height=field_height,
                text_size=font_size,
                dense=True,
                filled=True,
                bgcolor=ft.colors.GREY_100,
                read_only=True,
                prefix_icon=ft.icons.SCHEDULE,
                border_radius=8
            )

            # Campos temporários para o modal
            temp_data_field = ft.TextField(
                label="Data (dd/mm/aaaa)",
                value=data_inicial.strftime("%d/%m/%Y") if data_inicial else "",
                width=150,
                hint_text="12/07/2025"
            )
            
            temp_hora_field = ft.TextField(
                label="Hora (hh:mm)",
                value=hora_inicial,
                width=120,
                hint_text="14:30"
            )

            def abrir_modal(e):
                def confirmar_data_hora(e):
                    try:
                        # Limpa e normaliza os valores dos campos
                        data_str = temp_data_field.value.strip() if temp_data_field.value else ""
                        hora_str = temp_hora_field.value.strip() if temp_hora_field.value else ""
                        
                        # NOVA LÓGICA: Permite campos em branco para remover a informação
                        if not data_str and not hora_str:
                            # Ambos campos vazios - remove a informação
                            campo_display.value = ""
                            atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", "")
                            modal_datetime.open = False
                            page.update()
                            return
                        elif not data_str or not hora_str:
                            # Apenas um campo preenchido - mostra erro
                            error_text.value = "⚠️ Preencha ambos os campos ou deixe ambos em branco"
                            error_text.visible = True
                            error_text.color = ft.colors.ORANGE_600
                            page.update()
                            return
                        
                        # Ambos campos preenchidos - valida formato e data
                        if data_str and hora_str:
                            # Valida formato da data/hora inserida
                            dt_inserida = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
                            
                            # VALIDAÇÃO: Compara com data de entrada
                            data_entrada_str = safe_str(row["Data/Hora Entrada"])
                            if data_entrada_str:
                                try:
                                    # Parse da data de entrada (formato: "07/06/2025 11:26")
                                    dt_entrada = datetime.strptime(data_entrada_str, "%d/%m/%Y %H:%M")
                                    
                                    # Verifica se data inserida é anterior à data de entrada
                                    if dt_inserida <= dt_entrada:
                                        error_text.value = f"⚠️ Data/hora deve ser posterior à entrada: {data_entrada_str}"
                                        error_text.visible = True
                                        error_text.color = ft.colors.RED
                                        page.update()
                                        return  # Não prossegue com a confirmação
                                        
                                except ValueError:
                                    # Se não conseguir fazer parse da data de entrada, continua sem validação
                                    pass
                            
                            # Se chegou aqui, a validação passou
                            # Atualiza o campo display
                            novo_valor = f"{data_str} {hora_str}"
                            campo_display.value = novo_valor
                            
                            # Registra alteração
                            atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", novo_valor)
                            
                            # Fecha modal
                            modal_datetime.open = False
                            page.update()
                            
                    except ValueError:
                        error_text.value = "❌ Formato inválido. Use dd/mm/aaaa hh:mm"
                        error_text.visible = True
                        error_text.color = ft.colors.RED
                        page.update()

                def cancelar(e):
                    modal_datetime.open = False
                    page.update()

                def limpar_campos(e):
                    # Limpa os campos do modal
                    temp_data_field.value = ""
                    temp_hora_field.value = ""
                    
                    # Limpa mensagens de erro
                    error_text.value = ""
                    error_text.visible = False
                    
                    # Limpa o campo display na tabela
                    campo_display.value = ""
                    
                    # Registra a alteração como vazio
                    atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", "")
                    
                    # Atualiza a interface SEM fechar o modal
                    page.update()
                    
                    # Opcional: Foca no campo de data para facilitar nova digitação
                    temp_data_field.focus()

                error_text = ft.Text("", color=ft.colors.RED, size=12, visible=False)

                modal_datetime = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Selecionar Data e Hora", weight=ft.FontWeight.BOLD),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Informe a data e hora prevista:", size=14),
                            ft.Container(
                                content=ft.Text(
                                    f"📅 Data de entrada: {safe_str(row['Data/Hora Entrada'])}", 
                                    size=12, 
                                    color=ft.colors.BLUE_700,
                                    weight=ft.FontWeight.W_500
                                ),
                                padding=ft.padding.symmetric(vertical=5),
                                bgcolor=ft.colors.BLUE_50,
                                border_radius=3
                            ),
                            ft.Container(height=10),
                            ft.Row([temp_data_field, temp_hora_field], spacing=10),
                            ft.Container(height=5),
                            error_text,
                            ft.Container(height=5),
                            ft.Text("Exemplo: 12/07/2025 14:30", size=12, color=ft.colors.GREY_600),
                            ft.Text("💡 A data deve ser posterior à data de entrada", size=11, color=ft.colors.GREY_500, italic=True),
                            ft.Text("📝 Deixe ambos campos em branco para remover", size=11, color=ft.colors.BLUE_500, italic=True),
                            ft.Container(height=10)  # Espaçamento extra no final
                        ], tight=True),  # tight=True para melhor controle do espaçamento
                        width=380,
                        height=280,  # Aumentado de 220 para 280
                        padding=15
                    ),
                    actions=[
                        ft.TextButton("Limpar", on_click=limpar_campos),
                        ft.TextButton("Cancelar", on_click=cancelar),
                        ft.ElevatedButton("Confirmar", on_click=confirmar_data_hora, bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE)
                    ],
                    shape=ft.RoundedRectangleBorder(radius=6)
                )
                
                page.dialog = modal_datetime
                modal_datetime.open = True
                page.update()

            campo_display.on_click = abrir_modal
            
            return ft.Row([
                campo_display,
                ft.IconButton(
                    icon=ft.icons.EDIT_CALENDAR,
                    tooltip="Editar data/hora",
                    on_click=abrir_modal,
                    icon_size=16,
                    icon_color=ft.colors.BLUE_600
                )
            ], spacing=2)

        # Criação das linhas da tabela
        for idx, row in df_exibir.iterrows():
            evento_str = str(evento).strip()
            
            if isinstance(row["ID"], pd.Series):
                row_id = str(row["ID"].iloc[0]).strip()
            else:
                row_id = str(row["ID"]).strip()

            chave_alteracao = f"{evento_str}_{row_id}"

            if pode_editar:
                opcoes_motivo = [ft.dropdown.Option("", "— Selecione —")] + [ft.dropdown.Option(m) for m in sorted(motivos)]
                valor_dropdown = row["Motivo"] if (row["Motivo"] in motivos and row["Motivo"].strip() != "") else ""

                # CRIAR CAMPOS COM IDs ÚNICOS PARA EVITAR CONFLITOS
                
                # Campo de observação (criado primeiro para ser referenciado no dropdown)
                obs_field = ft.TextField(
                    value=str(row["Observacoes"]) if pd.notnull(row["Observacoes"]) else "",
                    width=obs_width,
                    height=field_height,
                    text_size=font_size,
                    dense=True,
                    filled=True,
                    bgcolor=ft.colors.GREY_100,
                    multiline=True,
                    min_lines=1,
                    max_lines=3,
                    label="Observações",
                    border_radius=6
                )

                # Ícone de alerta (inicialmente invisível)
                icone_alerta = ft.Icon(
                    ft.icons.WARNING,
                    color=ft.colors.ORANGE_600,
                    size=20,
                    visible=False,
                    tooltip="Observação obrigatória quando motivo é 'Outros'"
                )

                # Função de validação específica para esta linha
                def criar_validadores(chave_alt, obs_field_ref, icone_alerta_ref, row_id_atual):
                    # Variável compartilhada para armazenar o valor atual do motivo
                    motivo_atual = {"valor": valor_dropdown}
                    
                    def validar_motivo_mudanca(e):
                        motivo_selecionado = e.control.value
                        motivo_atual["valor"] = motivo_selecionado # Atualiza a variável compartilhada
                        obs_value = obs_field_ref.value
                        
                        # Normalização mais robusta
                        motivo_normalizado = str(motivo_selecionado).strip().lower() if motivo_selecionado else ""
                        obs_normalizada = str(obs_value).strip() if obs_value else ""
                        
                        # Se selecionou "Outros" e observação está vazia
                        if motivo_normalizado == "outros" and not obs_normalizada:
                            obs_field_ref.border_color = ft.colors.ORANGE_600
                            icone_alerta_ref.visible = True
                        else:
                            obs_field_ref.border_color = None
                            icone_alerta_ref.visible = False
                        
                        # Registra a alteração normalmente
                        atualizar_alteracao(chave_alt, "Motivo", motivo_selecionado)
                        page.update()

                    def validar_observacao_mudanca(e):
                        # Agora usa a variável compartilhada em vez de tentar acessar o dropdown
                        motivo_selecionado = motivo_atual["valor"]
                        obs_value = e.control.value
                        
                        # Se motivo é "Outros" e observação está vazia
                        if (motivo_selecionado and motivo_selecionado.lower() == "outros" and 
                            (not obs_value or not obs_value.strip())):
                            obs_field_ref.border_color = ft.colors.ORANGE_600
                            icone_alerta_ref.visible = True
                        else:
                            obs_field_ref.border_color = None
                            icone_alerta_ref.visible = False
                        
                        # Registra a alteração normalmente
                        atualizar_alteracao(chave_alt, "Observacoes", obs_value)
                        page.update()

                    return validar_motivo_mudanca, validar_observacao_mudanca

                # Cria os validadores específicos para esta linha
                validar_motivo_fn, validar_obs_fn = criar_validadores(chave_alteracao, obs_field, icone_alerta, row_id)

                # Dropdown de motivo
                motivo_dropdown = ft.Dropdown(
                    value=valor_dropdown,
                    options=opcoes_motivo,
                    width=motivo_width,
                    height=field_height,
                    text_size=font_size,
                    dense=True,
                    filled=True,
                    bgcolor=ft.colors.GREY_100,
                    content_padding=ft.padding.only(left=12, right=8, top=8, bottom=8),
                    alignment=ft.alignment.center_left,
                    on_change=validar_motivo_fn
                )

                # Configura validação no campo de observação
                obs_field.on_change = validar_obs_fn

                # Validação inicial (se já tem "Outros" selecionado)
                if (valor_dropdown and valor_dropdown.lower() == "outros" and 
                    (not obs_field.value or not obs_field.value.strip())):
                    obs_field.border_color = ft.colors.ORANGE_600
                    icone_alerta.visible = True

                # NOVO CAMPO DE DATA/HORA
                previsao_field = criar_campo_data_hora(row["Previsao_Liberacao"], chave_alteracao)

                # Container do campo observações com ícone de alerta
                obs_container = ft.Row([
                    obs_field,
                    icone_alerta
                ], spacing=5, alignment=ft.MainAxisAlignment.START)

                cells = [
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Placa"]), size=15, weight=ft.FontWeight.W_500), width=65)),
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Data/Hora Entrada"]), size=15), width=130)),
                    ft.DataCell(ft.Container(motivo_dropdown, width=motivo_width + 20)),
                    ft.DataCell(ft.Container(previsao_field, width=previsao_width + 40)),
                    ft.DataCell(ft.Container(obs_container, width=obs_width + 20))  # Usando container com ícone
                ]

            else:
                cells = [
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Placa"]), size=15, weight=ft.FontWeight.W_500), padding=5)),
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Data/Hora Entrada"]), size=15), padding=5)),
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Motivo"]), size=15), padding=5)),
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Previsao_Liberacao"]), size=15), padding=5)),
                    ft.DataCell(ft.Container(ft.Text(safe_str(row["Observacoes"]), size=15), padding=5))
                ]

            table_rows.append(ft.DataRow(cells=cells))

        # Ajusta tamanho da fonte dos cabeçalhos
        header_font_size = font_size + 1

        columns = [
            ft.DataColumn(ft.Text("Placa", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Data/Hora Entrada", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Motivo", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Previsão Liberação", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Observações", weight=ft.FontWeight.BOLD, size=header_font_size))
        ]

        # Ajusta largura da tabela baseado no tamanho da tela
        if screen_size == "small":
            table_width = 1200
            column_spacing = 3
        elif screen_size == "medium":
            table_width = 1400
            column_spacing = 4
        else:  # large
            table_width = 1600
            column_spacing = 5

        tabela = ft.DataTable(
            columns=columns,
            rows=table_rows,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=5,
            bgcolor=ft.colors.WHITE,
            horizontal_lines=ft.border.BorderSide(1, ft.colors.GREY_200),
            column_spacing=column_spacing,
            data_row_min_height=38,
            data_row_max_height=55,
            heading_row_height=40,
            width=table_width
        )

        botoes = ft.Container()

        if pode_editar:
            btn_enviar = ft.ElevatedButton(
                "Enviar Justificativas",
                bgcolor=ft.colors.GREEN_600,
                color=ft.colors.WHITE,
                icon=ft.icons.SEND,
                on_click=lambda e, ev=evento: enviar_justificativas(ev, df_evento),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
            )
            botoes = ft.Row([btn_enviar], alignment=ft.MainAxisAlignment.END)

        elif perfil in ("aprovador", "torre") and status_texto == "Aguardando aprovação":
            btn_reprovar = ft.ElevatedButton("❌ Reprovar", bgcolor=ft.colors.RED_600, color=ft.colors.WHITE, on_click=lambda e, ev=evento: reprovar_evento(ev))
            btn_aprovar = ft.ElevatedButton("✅ Aprovar", bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE, on_click=lambda e, ev=evento: aprovar_evento(ev))
            botoes = ft.Row(
                controls=[
                    btn_reprovar,
                    ft.Container(
                        content=btn_aprovar,
                        expand=True,
                        alignment=ft.alignment.center_right
                    )
                ]
            )

        tabela_container = ft.Container(
            content=ft.Row([tabela], scroll=ft.ScrollMode.ADAPTIVE),
            padding=5
        )

        conteudo_expansivel = ft.Container()
        # Garante que estado_expansao existe antes de verificar
        if (hasattr(app_state, 'estado_expansao') and 
            app_state.estado_expansao is not None and 
            evento in app_state.estado_expansao and 
            app_state.estado_expansao[evento]):
            conteudo_expansivel = ft.Container(
                content=ft.Column([tabela_container, ft.Container(height=5), botoes]),
                padding=8
            )

        # Ajusta largura do container baseado no tamanho da tela
        if screen_size == "small":
            container_width = 1200
        elif screen_size == "medium":
            container_width = 1300
        else:  # large
            container_width = 1400

        container_final = ft.Container(
            content=ft.Column([header, conteudo_expansivel]),
            margin=ft.margin.only(bottom=8),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.BLACK12),
            width=container_width
        )
        return container_final

    def atualizar_alteracao(chave, campo, valor):
        app_state.atualizar_alteracao(chave, campo, valor)

    def enviar_justificativas(evento, df_evento):
        print(f"📝 [SISTEMA] Processando: {evento}")
        mostrar_mensagem("⏳ Salvando alterações...", False)
        
        def safe_str(x):
            return DataFormatter.safe_str(x)
        
        # Validação usando DataValidator
        validacao_resultado = DataValidator.validar_justificativas_evento(df_evento, app_state.alteracoes_pendentes)
        erros_validacao = validacao_resultado["erros"]

        # Se há erros de validação, mostra mensagem e para o processamento
        if erros_validacao:
            # Criar modal de erro personalizado com altura dinâmica
            def fechar_erro(e):
                modal_erro.open = False
                page.update()

            # CORREÇÃO: Cálculo melhorado da altura dinâmica
            altura_base = 180 # Aumentada para acomodar melhor o conteúdo
            altura_por_erro = 35 # Aumentada para dar mais espaço por erro
            altura_padding = 80 # Aumentado para incluir espaço do botão
            altura_minima = 300 # Aumentada altura mínima
            altura_maxima = 700 # Aumentada altura máxima

            altura_calculada = altura_base + (len(erros_validacao) * altura_por_erro) + altura_padding
            altura_final = max(altura_minima, min(altura_calculada, altura_maxima))

            # Se ultrapassar altura máxima, adiciona scroll
            usar_scroll = altura_calculada > altura_maxima

            # CORREÇÃO: Container dos erros com altura ajustada
            container_erros = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.WARNING, color=ft.colors.ORANGE_600, size=18),
                            ft.Text(linha, size=14, color=ft.colors.RED_800, weight=ft.FontWeight.W_500)
                        ], spacing=8),
                        padding=ft.padding.symmetric(vertical=5, horizontal=10),
                        bgcolor=ft.colors.RED_50,
                        border_radius=6,
                        border=ft.border.all(1, ft.colors.RED_200)
                    )
                    for linha in erros_validacao
                ], spacing=8, scroll=ft.ScrollMode.AUTO if usar_scroll else None),
                padding=15,
                # CORREÇÃO: Altura ajustada para deixar espaço para o botão
                height=min(400, len(erros_validacao) * altura_por_erro + 20) if usar_scroll else None
            )

            modal_erro = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.colors.RED_600, size=28),
                    ft.Text("Campos Obrigatórios Pendentes", weight=ft.FontWeight.BOLD, color=ft.colors.RED_600, size=18)
                ], spacing=10),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE_600, size=20),
                                    ft.Text(
                                        "Regra de Preenchimento:",
                                        size=15,
                                        color=ft.colors.BLUE_800,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ], spacing=8),
                                ft.Container(height=5),
                                ft.Text(
                                    "Quando o motivo for 'Outros', é obrigatório informar detalhes no campo Observações.",
                                    size=14,
                                    color=ft.colors.GREY_800,
                                    weight=ft.FontWeight.W_500
                                )
                            ], spacing=0),
                            padding=ft.padding.all(15),
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.colors.BLUE_200)
                        ),
                        ft.Container(height=15),
                        ft.Text(
                            f"📋 Registros pendentes ({len(erros_validacao)}):",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY_800
                        ),
                        ft.Container(height=10),
                        container_erros
                    ], tight=True),
                        width=700, # CORREÇÃO: Largura aumentada para melhor layout
                        height=altura_final,
                        padding=25
                    ),
                    actions=[
                    ft.ElevatedButton(
                        "Entendido",
                        on_click=fechar_erro,
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE,
                        icon=ft.icons.CHECK_CIRCLE,
                        width=150,
                        height=45,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,

                    shape=ft.RoundedRectangleBorder(radius=8) 
            )

            page.dialog = modal_erro
            modal_erro.open = True
            page.update()
            return # Para a execução aqui
        
        # Se chegou aqui, validação passou - continua com o código original
        registros_atualizados = 0

        def limpa_valor(val, campo=None):
            return DataFormatter.formatar_valor_sharepoint(val, campo)

        def verificar_status_evento(evento_titulo, df_evento_atual, alteracoes_pendentes_param):
            return EventoProcessor.calcular_status_evento(df_evento_atual, alteracoes_pendentes_param)

        if "ID" not in df_evento.columns:
            mostrar_mensagem("❌ Erro: Coluna ID não encontrada nos dados.", True)
            return

        # Coleta todas as atualizações em lote antes de enviar
        atualizacoes_lote = []
        status_evento = verificar_status_evento(evento, df_evento, app_state.alteracoes_pendentes)

        # Primeira passada: coleta registros com alterações
        for _, row in df_evento.iterrows():
            row_id = str(row["ID"]).strip()
            chave_alteracao = f"{evento}_{row_id}"
            
            if chave_alteracao in app_state.alteracoes_pendentes:
                alteracoes = app_state.alteracoes_pendentes[chave_alteracao]                
                valor_motivo_df = row.get("Motivo", "")
                valor_previsao_df = row.get("Previsao_Liberacao", "")
                valor_obs_df = row.get("Observacoes", "")
                valor_motivo_user = alteracoes.get("Motivo", valor_motivo_df) if "Motivo" in alteracoes else valor_motivo_df
                valor_previsao_user = alteracoes.get("Previsao_Liberacao", valor_previsao_df) if "Previsao_Liberacao" in alteracoes else valor_previsao_df
                valor_obs_user = alteracoes.get("Observacoes", valor_obs_df) if "Observacoes" in alteracoes else valor_obs_df
                dados = {
                    "Motivo": limpa_valor(valor_motivo_user),
                    "Previsao_Liberacao": limpa_valor(valor_previsao_user, "Previsao_Liberacao"),
                    "Observacoes": limpa_valor(valor_obs_user),
                    "Status": status_evento
                }
                
                atualizacoes_lote.append((int(row_id), dados))

        # Envia todas as alterações em paralelo
        if atualizacoes_lote:
            # Logs otimizados - apenas resultado final
            registros_atualizados = SharePointClient.atualizar_lote(atualizacoes_lote)
            print(f"✅ [SISTEMA] {registros_atualizados} registros processados!")

        # Atualiza status de TODOS os registros do evento (não apenas os não alterados)
        atualizacoes_status = []
        for _, row in df_evento.iterrows():
            row_id = str(row["ID"]).strip()
            
            # CORREÇÃO: Atualiza status de todos os registros, independente de terem alterações
            dados_status = {"Status": status_evento}
            atualizacoes_status.append((int(row_id), dados_status))

        # Envia todas as atualizações de status em paralelo
        if atualizacoes_status:
            SharePointClient.atualizar_lote(atualizacoes_status)

        # Limpa alterações pendentes
        app_state.limpar_alteracoes_evento(evento)

        if registros_atualizados > 0:
            mostrar_mensagem(f"✅ {registros_atualizados} registro(s) atualizado(s)!")
            carregar_dados()
            mostrar_painel()
        else:
            mostrar_mensagem("⚠️ Nenhuma alteração detectada.", True)

    def atualizar_painel(e):
        carregar_dados()
        mostrar_painel()

    def mostrar_painel():
        header = ft.Container(
            content=ft.Row([
                # Logo e título juntos
                ft.Row([
                    ft.Image(
                        src="images/logo.png",
                        width=20,
                        height=20,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Container(width=10),
                    ft.Text(f"Sentinela - {app_state.get_nome_usuario()}", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
                ], spacing=0),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "🔄 Atualizar", 
                    on_click=atualizar_painel, 
                    bgcolor=ft.colors.WHITE, 
                    color=ft.colors.BLUE_600,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6)
                    )
                )
            ]),
            padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
            bgcolor=ft.colors.BLUE_600
        )

        # Cards dashboard com mais espaçamento superior (removida a legenda)
        dashboard = ft.Container(
            content=ft.Column([ft.Container(height=15), criar_cards_dashboard()]), 
            padding=ft.padding.only(left=20, right=20, top=10, bottom=15)  # Aumentado o padding superior
        )

        eventos_content = []

        # Primeiro filtra por status não aprovado
        df_nao_aprovados = app_state.df_desvios[app_state.df_desvios["Status"].ne("Aprovado")] if "Status" in app_state.df_desvios.columns else app_state.df_desvios

        # Depois aplica filtro por área do usuário se necessário
        perfil = app_state.get_perfil_usuario()
        areas = app_state.get_areas_usuario()

        # Se o usuário não é aprovador nem torre, filtrar por área
        if perfil not in ("aprovador", "torre"):
            # Filtrar registros baseado nas áreas do usuário
            df_filtrado_usuario = pd.DataFrame()
            for _, row in df_nao_aprovados.iterrows():
                evento_titulo = row.get("Titulo", "")
                if evento_titulo:
                    try:
                        # Parse do título para obter o POI
                        evento_info = EventoProcessor.parse_titulo_completo(evento_titulo)
                        poi_amigavel = evento_info["poi_amigavel"]
                        
                        # Verificar se o usuário tem acesso a este POI
                        if EventoProcessor.validar_acesso_usuario(poi_amigavel, areas):
                            df_filtrado_usuario = pd.concat([df_filtrado_usuario, row.to_frame().T], ignore_index=True)
                    except Exception:
                        # Se der erro no parse, pula este registro
                        continue
            
            # Usar dados filtrados para este usuário
            df_nao_aprovados = df_filtrado_usuario

        # Só mostra mensagem se NÃO há desvios após todos os filtros
        if df_nao_aprovados.empty:
            eventos_content.append(
                ft.Container(
                    content=ft.Column([
                        ft.Image(
                            src="images/sem_tratativas.svg",
                            width=200,
                            height=200,
                            fit=ft.ImageFit.CONTAIN
                        ),
                        ft.Container(height=20),
                        ft.Text("Não há desvios para serem tratados", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                        ft.Text("Todos os eventos estão em dia!", size=16, color=ft.colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=50,
                    alignment=ft.alignment.center
                )
            )
        else:
                def extrair_data(titulo):
                    m = re.search(r'_(\d{2})(\d{2})(\d{4})_(\d{2})(\d{2})(\d{2})', titulo)
                    if m:
                        dia, mes, ano, hora, minuto, segundo = m.groups()
                        return datetime(int(ano), int(mes), int(dia), int(hora), int(minuto), int(segundo))
                    return datetime.max

                if "Titulo" in df_nao_aprovados.columns:
                    eventos_unicos = sorted(df_nao_aprovados["Titulo"].unique(), key=extrair_data)
                else:
                    eventos_unicos = []

                for evento in eventos_unicos:
                    df_evento = df_nao_aprovados[df_nao_aprovados["Titulo"] == evento]
                    try:
                        card = criar_card_evento(evento, df_evento)
                        if card:
                            eventos_content.append(card)
                    except Exception:
                        continue

        eventos_lista = ft.ListView(
            eventos_content, 
            spacing=5, 
            padding=ft.padding.all(10),
            auto_scroll=False,
            expand=True
        )

        rodape = ft.Container(
            content=ft.Text("Developed by Logistica MS - Suzano", size=14, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
            padding=5,
            alignment=ft.alignment.center
        )

        # Layout final sem legenda - direto header → cards → eventos
        page.clean()
        page.add(
            ft.Column([
                # Header fixo
                header,
                # Cards dashboard fixos (SEM legenda)
                ft.Container(
                    content=dashboard,
                    padding=ft.padding.only(left=0, right=0, top=0, bottom=10),
                    bgcolor=ft.colors.GREY_50
                ),
                # Lista de eventos com scroll independente
                ft.Container(
                    content=eventos_lista,
                    expand=True,  # Ocupa o espaço restante
                    bgcolor=ft.colors.GREY_50
                ),
                # Rodapé fixo
                rodape
            ], 
            expand=True  # Importante: faz a coluna ocupar toda a altura
            )
        )
        page.update()

    # Campos de login
    email_field = ft.TextField(
        label="E-mail corporativo",
        width=400,
        prefix_icon=ft.icons.EMAIL,
        border_radius=10,
        keyboard_type=ft.KeyboardType.EMAIL,
        autofocus=True
    )

    password_field = ft.TextField(
        label="Senha",
        width=400,
        prefix_icon=ft.icons.LOCK,
        password=True,
        can_reveal_password=True,
        border_radius=10,
        on_submit=fazer_login
    )

    btn_login = ft.ElevatedButton(
        text="Entrar",
        width=400,
        height=50,
        on_click=fazer_login,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )

    # Detecta tamanho da tela para responsividade
    try:
        current_width = page.window_width
        current_height = page.window_height
    except:
        current_width = 1400
        current_height = 800

    screen_size = get_screen_size(current_width)

    # Configurações responsivas para login
    if screen_size == "small":
        container_width = min(380, current_width - 40)
        image_size = 120
        title_size = 28
        subtitle_size = 14
        field_width = container_width - 60
        padding_container = 20
        spacing_top = 20
        spacing_middle = 30
        spacing_fields = 10
    elif screen_size == "medium":
        container_width = min(450, current_width - 60)
        image_size = 160
        title_size = 32
        subtitle_size = 16
        field_width = container_width - 80
        padding_container = 35
        spacing_top = 35
        spacing_middle = 35
        spacing_fields = 15
    else:  # large
        container_width = 500
        image_size = 200
        title_size = 36
        subtitle_size = 18
        field_width = 400
        padding_container = 50
        spacing_top = 50
        spacing_middle = 40
        spacing_fields = 15

    # Campos de login responsivos
    email_field = ft.TextField(
        label="E-mail corporativo",
        width=field_width,
        prefix_icon=ft.icons.EMAIL,
        border_radius=10,
        keyboard_type=ft.KeyboardType.EMAIL,
        autofocus=True
    )

    password_field = ft.TextField(
        label="Senha",
        width=field_width,
        prefix_icon=ft.icons.LOCK,
        password=True,
        can_reveal_password=True,
        border_radius=10,
        on_submit=fazer_login
    )

    btn_login = ft.ElevatedButton(
        text="Entrar",
        width=field_width,
        height=50,
        on_click=fazer_login,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )

    login_container = ft.Container(
        content=ft.Column([
            ft.Container(height=spacing_top),
            ft.Image(
                src="images/sentinela.png",
                width=image_size,
                height=image_size,
                fit=ft.ImageFit.CONTAIN
            ),
            ft.Text("Sentinela", size=title_size, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
            ft.Text("Faça seu login para continuar", size=subtitle_size, color=ft.colors.GREY_600),
            ft.Container(height=spacing_middle),
            email_field,
            ft.Container(height=spacing_fields),
            password_field,
            ft.Container(height=spacing_fields + 10),
            btn_login
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=padding_container,
        border_radius=20,
        bgcolor=ft.colors.WHITE,
        shadow=ft.BoxShadow(spread_radius=2, blur_radius=15, color=ft.colors.BLACK12),
        width=container_width,
        margin=ft.margin.all(20),
        alignment=ft.alignment.center
    )

    # Carrega dados iniciais para validação de login
    loading_inicial = ft.Container(
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text("Inicializando sistema...", size=16)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center
    )

    page.add(loading_inicial)
    page.update()

    print("🚀 SENTINELA - APLICAÇÃO INICIANDO")
    print(f"📁 LOGS SALVOS EM: {log_filepath}")

    logger.info("🚀 Aplicação iniciando...")
    logger.info("📋 Sistema de logging ativo - logs salvos em arquivo")

    # Carrega dados iniciais para validação de login
    sucesso_inicial = carregar_dados_iniciais()

    page.clean()

    if not sucesso_inicial:
        erro_inicial = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ERROR, size=100, color=ft.colors.RED_600),
                ft.Text("Erro ao inicializar sistema", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Verifique sua conexão", size=14, color=ft.colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
        page.add(erro_inicial)
    else:
        # Mostra tela de login responsiva e centralizada
        login_screen = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),  # Espaço flexível à esquerda
                ft.Column([
                    ft.Container(expand=True),  # Espaço flexível acima
                    login_container,
                    ft.Container(expand=True)   # Espaço flexível abaixo
                ], expand=True),
                ft.Container(expand=True)   # Espaço flexível à direita
            ]),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_50,
            expand=True
        )

        page.add(login_screen)

    page.update()

# Função para monitorar logs em tempo real (opcional)
def monitorar_logs():
    """Função para acompanhar logs em tempo real via terminal"""
    import time
    import threading
    
    def tail_log():
        if os.path.exists(log_filepath):
            with open(log_filepath, 'r', encoding='utf-8') as f:
                # Vai para o final do arquivo
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        print(f"[LOG] {line.strip()}")
                    else:
                        time.sleep(0.1)
    
    # Inicia thread de monitoramento
    log_thread = threading.Thread(target=tail_log, daemon=True)
    log_thread.start()
    
    print(f"📊 [SISTEMA] Monitoramento de logs iniciado")
    print(f"📁 [SISTEMA] Arquivo de log: {log_filepath}")

# Inicia monitoramento de logs em tempo real
#monitorar_logs()

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8081, assets_dir="assets")