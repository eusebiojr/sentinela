"""
Processador de Localização - Suporte para RRP e TLS - CORRIGIDO
"""
from typing import Dict, Any, List
from ..config.logging_config import setup_logger

logger = setup_logger("location_processor")


class LocationProcessor:
    """Processador para diferentes localizações (RRP, TLS)"""
    
    # Configurações por localização
    LOCATIONS_CONFIG = {
        "RRP": {
            "nome_completo": "Ribas do Rio Pardo",
            "codigo": "RRP",
            "pois": {
                "PAAGUACLARA": "P.A. Água Clara - RRP",
                "CARREGAMENTOFABRICARRP": "Fábrica RRP",
                "OFICINAJSL": "Oficina JSL - RRP",
                "TERMINALINOCENCIA": "Terminal Inocência - RRP"
            },
            "areas_usuario": [
                "PA Agua Clara RRP",
                "Fábrica RRP", 
                "Manutenção RRP",
                "Terminal RRP"
            ]
        },
        "TLS": {
            "nome_completo": "Três Lagoas",
            "codigo": "TLS",
            "pois": {
                "PAAGUACLARA": "P.A. Água Clara - TLS",
                "CARREGAMENTOFABRICATLS": "Fábrica TLS",
                "OFICINA": "Oficina - TLS",
                "TERMINAL": "Terminal - TLS"
            },
            "areas_usuario": [
                "PA Agua Clara TLS",
                "Fábrica TLS",
                "Manutenção TLS", 
                "Terminal TLS"
            ]
        }
    }
    
    @staticmethod
    def extrair_localizacao_do_titulo(titulo: str) -> str:
        """
        Extrai código da localização do título do evento
        
        Args:
            titulo: Título do evento (ex: "RRP_CarregamentoFabricaRRP_N1_...")
            
        Returns:
            Código da localização ("RRP", "TLS", ou "UNKNOWN")
        """
        if not titulo:
            return "UNKNOWN"
        
        # Verifica o prefixo do título
        if titulo.startswith("RRP_"):
            return "RRP"
        elif titulo.startswith("TLS_"):
            return "TLS"
        else:
            # Fallback: tenta detectar pelo conteúdo
            if "RRP" in titulo.upper():
                return "RRP"
            elif "TLS" in titulo.upper():
                return "TLS"
            
            return "UNKNOWN"
    
    @staticmethod
    def parse_titulo_com_localizacao(titulo: str) -> Dict[str, Any]:
        """
        Parse completo do título considerando localização
        
        Args:
            titulo: Título do evento
            
        Returns:
            Dict com informações parsed incluindo localização
        """
        resultado = {
            "titulo_original": titulo,
            "localizacao": "UNKNOWN",
            "tipo_amigavel": "",
            "poi_amigavel": "",
            "datahora_fmt": "",
            "data_evento": None,
            "valido": False
        }
        
        try:
            # Extrai localização
            localizacao = LocationProcessor.extrair_localizacao_do_titulo(titulo)
            resultado["localizacao"] = localizacao
            
            # Parse das partes do título
            partes = titulo.split('_')
            if len(partes) < 5:
                return resultado
            
            # Estrutura esperada: LOCALIZACAO_POI_TIPO_DATA_HORA
            tipo = partes[-3]
            poi_raw = partes[1].upper()
            data_str = partes[-2]
            hora_str = partes[-1]
            
            # Obtém configuração da localização
            config_loc = LocationProcessor.LOCATIONS_CONFIG.get(localizacao, {})
            pois_map = config_loc.get("pois", {})
            
            # Mapeamento de POIs com localização
            poi_amigavel = pois_map.get(poi_raw, poi_raw.title())
            
            # Se não encontrou na configuração específica, usa fallback genérico
            if poi_amigavel == poi_raw.title():
                pois_genericos = {
                    "PAAGUACLARA": "P.A. Água Clara",
                    "CARREGAMENTOFABRICA": "Fábrica",
                    "OFICINA": "Oficina",
                    "TERMINAL": "Terminal"
                }
                
                # Busca por substring
                for key, value in pois_genericos.items():
                    if key in poi_raw:
                        poi_amigavel = f"{value} - {localizacao}"
                        break
            
            # Mapeamento de tipos (universal)
            tipo_map = {
                "Informativo": "Alerta Informativo",
                "N1": "Tratativa N1", "N2": "Tratativa N2",
                "N3": "Tratativa N3", "N4": "Tratativa N4"
            }
            tipo_amigavel = tipo_map.get(tipo, tipo)
            
            # Processa data/hora
            try:
                from datetime import datetime
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
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse do título: {e}")
        
        return resultado
    
    @staticmethod
    def obter_motivos_por_poi_e_localizacao(poi_amigavel: str, localizacao: str) -> List[str]:
        """
        Determina motivos disponíveis baseado no POI e localização
        
        Args:
            poi_amigavel: Nome amigável do POI
            localizacao: Código da localização (RRP/TLS)
            
        Returns:
            Lista de motivos disponíveis
        """
        # Motivos base (aplicam para todas as localizações)
        motivos_base = {
            "PA_AGUA_CLARA": [
                "Atestado Motorista",
                "Brecha na escala", 
                "Ciclo Antecipado - Aguardando Motorista", 
                "Falta Motorista",
                "Outros", 
                "Refeição", 
                "Socorro Mecânico"
            ],
            "MANUTENCAO": [
                "Corretiva",
                "Falta Mecânico",
                "Falta Material", 
                "Inspeção", 
                "Lavagem", 
                "Preventiva", 
                "Outros"
            ],
            "TERMINAL": [
                "Chegada em Comboio", 
                "Falta de Espaço", 
                "Falta de Máquina", 
                "Falta de Operador", 
                "Janela de Descarga",
                "Prioridade Ferrovia",
                "Outros"
            ],
            "FABRICA": [
                "Chegada em Comboio", 
                "Emissão Nota Fiscal", 
                "Falta de Máquina", 
                "Falta de Material", 
                "Falta de Operador", 
                "Janela Carregamento", 
                "Outros",
                "Restrição de Tráfego"
            ]
        }
        
        # Detecta tipo baseado no POI
        poi_upper = poi_amigavel.upper()
        
        if "P.A." in poi_upper or "AGUA CLARA" in poi_upper:
            motivos = motivos_base["PA_AGUA_CLARA"]
        elif "OFICINA" in poi_upper or "MANUTENÇÃO" in poi_upper:
            motivos = motivos_base["MANUTENCAO"]
        elif "TERMINAL" in poi_upper:
            motivos = motivos_base["TERMINAL"]
        elif "FÁBRICA" in poi_upper or "FABRICA" in poi_upper:
            motivos = motivos_base["FABRICA"]
        else:
            motivos = ["Outros"]
        
        # Futuramente, pode-se adicionar motivos específicos por localização
        # if localizacao == "TLS":
        #     motivos.extend(["Motivo específico TLS"])
        
        return motivos
    
    @staticmethod
    def validar_acesso_usuario_por_localizacao(
        poi_amigavel: str, 
        localizacao: str, 
        areas_usuario: List[str]
    ) -> bool:
        """
        Verifica se usuário tem acesso ao POI considerando localização
        COMPATÍVEL com formato antigo E novo
        
        Args:
            poi_amigavel: Nome amigável do POI
            localizacao: Código da localização
            areas_usuario: Lista de áreas do usuário
            
        Returns:
            bool: True se tem acesso
        """
        if not areas_usuario:
            return False
        
        # Normaliza áreas do usuário
        areas_normalizadas = [area.strip().lower() for area in areas_usuario]
        
        # 1. FORMATO NOVO (Preferido) - Área + Localização
        # Ex: "PA Agua Clara RRP", "Fábrica TLS"
        for area in areas_normalizadas:
            if localizacao.lower() in area:
                # Verifica se a área corresponde ao POI
                if LocationProcessor._area_corresponde_poi(area, poi_amigavel):
                    return True
        
        # 2. FORMATO ANTIGO (Compatibilidade) - Apenas área genérica
        # Ex: "P.A. Água Clara", "fábrica", "Terminal Inocência"
        for area in areas_normalizadas:
            if LocationProcessor._area_generica_corresponde_poi(area, poi_amigavel):
                return True
        
        # 3. ÁREAS ESPECIAIS
        for area in areas_normalizadas:
            if area in ["geral", "all", "todos", "todas"]:
                return True
        
        return False
    
    @staticmethod
    def _area_corresponde_poi(area_normalizada: str, poi_amigavel: str) -> bool:
        """
        Verifica se área específica (com localização) corresponde ao POI
        
        Args:
            area_normalizada: Área normalizada (ex: "fábrica rrp")
            poi_amigavel: POI amigável (ex: "Fábrica RRP")
            
        Returns:
            bool: True se corresponde
        """
        poi_lower = poi_amigavel.lower()
        
        # Mapeamentos diretos
        mapeamentos = {
            # Água Clara
            ("pa agua clara", "agua clara"): ["agua clara", "p.a.", "pa"],
            # Fábrica  
            ("fábrica", "fabrica"): ["fábrica", "fabrica", "carregamento"],
            # Manutenção
            ("manutenção", "manutencao"): ["oficina", "manutenção", "manutencao"],
            # Terminal
            ("terminal",): ["terminal", "inocência", "inocencia"]
        }
        
        for palavras_area, palavras_poi in mapeamentos.items():
            if any(palavra in area_normalizada for palavra in palavras_area):
                if any(palavra in poi_lower for palavra in palavras_poi):
                    return True
        
        return False
    
    @staticmethod  
    def _area_generica_corresponde_poi(area_normalizada: str, poi_amigavel: str) -> bool:
        """
        Verifica se área genérica (formato antigo) corresponde ao POI
        
        Args:
            area_normalizada: Área normalizada (ex: "p.a. água clara")
            poi_amigavel: POI amigável (ex: "P.A. Água Clara - RRP")
            
        Returns:
            bool: True se corresponde
        """
        poi_lower = poi_amigavel.lower()
        
        # Mapeamentos do formato antigo
        if any(palavra in area_normalizada for palavra in ["p.a.", "agua clara", "água clara"]):
            return any(palavra in poi_lower for palavra in ["agua clara", "p.a."])
        
        elif any(palavra in area_normalizada for palavra in ["fábrica", "fabrica"]):
            return any(palavra in poi_lower for palavra in ["fábrica", "fabrica", "carregamento"])
        
        elif any(palavra in area_normalizada for palavra in ["terminal", "inocência", "inocencia"]):
            return any(palavra in poi_lower for palavra in ["terminal", "inocência", "inocencia"])
        
        elif any(palavra in area_normalizada for palavra in ["oficina", "manutenção", "manutencao"]):
            return any(palavra in poi_lower for palavra in ["oficina", "manutenção", "manutencao"])
        
        return False
    
    @staticmethod
    def obter_areas_disponiveis() -> Dict[str, List[str]]:
        """
        Retorna todas as áreas disponíveis organizadas por localização
        
        Returns:
            Dict com áreas por localização
        """
        areas_por_localizacao = {}
        
        for loc_code, config in LocationProcessor.LOCATIONS_CONFIG.items():
            areas_por_localizacao[loc_code] = {
                "nome": config["nome_completo"],
                "areas": config["areas_usuario"]
            }
        
        # Adiciona áreas genéricas
        areas_por_localizacao["GERAL"] = {
            "nome": "Geral (Todas as localizações)",
            "areas": [
                "Geral",
                "PA Agua Clara",
                "Fábrica", 
                "Manutenção",
                "Terminal"
            ]
        }
        
        return areas_por_localizacao


# Instância global
location_processor = LocationProcessor()


# Funções de conveniência
def parse_titulo_com_localizacao(titulo: str) -> Dict[str, Any]:
    """Parse de título considerando localização"""
    return location_processor.parse_titulo_com_localizacao(titulo)


def obter_motivos_por_poi_e_localizacao(poi_amigavel: str, localizacao: str) -> List[str]:
    """Obtém motivos por POI e localização"""
    return location_processor.obter_motivos_por_poi_e_localizacao(poi_amigavel, localizacao)


def validar_acesso_usuario_por_localizacao(poi_amigavel: str, localizacao: str, areas_usuario: List[str]) -> bool:
    """Valida acesso considerando localização"""
    return location_processor.validar_acesso_usuario_por_localizacao(poi_amigavel, localizacao, areas_usuario)


def obter_areas_disponiveis() -> Dict[str, List[str]]:
    """Obtém todas as áreas disponíveis"""
    return location_processor.obter_areas_disponiveis()