"""
Processador de Localização - Suporte para RRP e TLS - MAPEAMENTO COMPLETO ATUALIZADO
"""
from typing import Dict, Any, List
from ..config.logging_config import setup_logger

logger = setup_logger("location_processor")


class LocationProcessor:
    """Processador para diferentes localizações (RRP, TLS) com mapeamento completo"""
    
    # Configurações por localização - ATUALIZADO COM TODOS OS POIs
    LOCATIONS_CONFIG = {
        "RRP": {
            "nome_completo": "Ribas do Rio Pardo",
            "codigo": "RRP",
            "pois": {
                "PAAGUACLARA": "P.A. Água Clara - RRP",
                "CARREGAMENTOFABRICARRP": "Carregamento Fábrica - RRP",
                "CARREGAMENTOFABRICA": "Carregamento Fábrica - RRP",  # Fallback
                "OFICINAJSL": "Manutenção - RRP",
                "OFICINA": "Manutenção - RRP",  # Fallback
                "TERMINALINOCENCIA": "Terminal Inocência - RRP",
                "DESCARGAINOCENCIA": "Terminal Inocência - RRP"
            },
            "areas_usuario": [
                "PA Agua Clara RRP",
                "Carregamento Fábrica RRP", 
                "Manutenção RRP",
                "Terminal RRP"
            ]
        },
        "TLS": {
            "nome_completo": "Três Lagoas",
            "codigo": "TLS",
            "pois": {
                "PACELULOSE": "P.A. Celulose - TLS",
                "PAAGUACLARA": "P.A. Celulose - TLS",  # Fallback para TLS
                "CARREGAMENTOFABRICATLS": "Carregamento Fábrica - TLS",
                "CARREGAMENTOFABRICA": "Carregamento Fábrica - TLS",  # Detecção por localização
                "DESCARGATAP": "Terminal Aparecida - TLS",
                "DESCARGA": "Terminal Aparecida - TLS",  # Fallback
                "TERMINAL": "Terminal Aparecida - TLS",  # Fallback
                "OFICINA": "Manutenção - TLS"
            },
            "areas_usuario": [
                "PA Celulose TLS",
                "Carregamento Fábrica TLS",
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
            titulo_upper = titulo.upper()
            
            # Busca por indicadores específicos
            if "RRP" in titulo_upper or "INOCENCIA" in titulo_upper or "PAAGUACLARA" in titulo_upper:
                return "RRP"
            elif "TLS" in titulo_upper or "CELULOSE" in titulo_upper or "TAP" in titulo_upper:
                return "TLS"
            
            return "RRP"  # Default para compatibilidade
    
    @staticmethod
    def parse_titulo_com_localizacao(titulo: str) -> Dict[str, Any]:
        """
        Parse completo do título considerando localização - FORMATO PADRONIZADO
        
        Args:
            titulo: Título do evento
            
        Returns:
            Dict com informações parsed incluindo localização e formato padronizado
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
            
            # NOVO: Mapeamento inteligente de POIs
            poi_amigavel = LocationProcessor._mapear_poi_inteligente(poi_raw, localizacao, pois_map)
            
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
    def _mapear_poi_inteligente(poi_raw: str, localizacao: str, pois_map: Dict[str, str]) -> str:
        """
        NOVO: Mapeamento inteligente de POIs com fallbacks e detecção por contexto
        
        Args:
            poi_raw: POI raw do título
            localizacao: Código da localização (RRP/TLS)
            pois_map: Mapa de POIs da localização
            
        Returns:
            Nome amigável do POI com unidade
        """
        # 1. Tentativa direta no mapeamento
        if poi_raw in pois_map:
            return pois_map[poi_raw]
        
        # 2. Busca por substring (para casos como "CARREGAMENTOFABRICARRP")
        for key, value in pois_map.items():
            if key in poi_raw or poi_raw in key:
                return value
        
        # 3. Mapeamento por padrões específicos
        poi_patterns = {
            # P.A. / Pátios
            "PA": f"P.A. {LocationProcessor._get_unit_name(localizacao)} - {localizacao}",
            "PATIO": f"P.A. {LocationProcessor._get_unit_name(localizacao)} - {localizacao}",
            
            # Carregamento/Fábrica
            "CARREGAMENTO": f"Carregamento Fábrica - {localizacao}",
            "FABRICA": f"Carregamento Fábrica - {localizacao}",
            
            # Descarga/Terminal
            "DESCARGA": f"Terminal {LocationProcessor._get_terminal_name(localizacao)} - {localizacao}",
            "TERMINAL": f"Terminal {LocationProcessor._get_terminal_name(localizacao)} - {localizacao}",
            
            # Manutenção/Oficina
            "OFICINA": f"Manutenção - {localizacao}",
            "MANUTENCAO": f"Manutenção - {localizacao}"
        }
        
        # Busca por padrões
        poi_upper = poi_raw.upper()
        for pattern, formatted_name in poi_patterns.items():
            if pattern in poi_upper:
                return formatted_name
        
        # 4. Fallback - nome com localização
        return f"{poi_raw.title()} - {localizacao}"
    
    @staticmethod
    def _get_unit_name(localizacao: str) -> str:
        """Retorna nome da unidade para P.A."""
        if localizacao == "TLS":
            return "Celulose"
        else:  # RRP
            return "Água Clara"
    
    @staticmethod
    def _get_terminal_name(localizacao: str) -> str:
        """Retorna nome do terminal"""
        if localizacao == "TLS":
            return "Aparecida"
        else:  # RRP
            return "Inocência"
    
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
        
        if "P.A." in poi_upper or "AGUA CLARA" in poi_upper or "CELULOSE" in poi_upper:
            motivos = motivos_base["PA_AGUA_CLARA"]
        elif "MANUTENÇÃO" in poi_upper or "MANUTENCAO" in poi_upper:
            motivos = motivos_base["MANUTENCAO"]
        elif "TERMINAL" in poi_upper or "APARECIDA" in poi_upper or "INOCÊNCIA" in poi_upper:
            motivos = motivos_base["TERMINAL"]
        elif "FÁBRICA" in poi_upper or "FABRICA" in poi_upper or "CARREGAMENTO" in poi_upper:
            motivos = motivos_base["FABRICA"]
        else:
            motivos = ["Outros"]
        
        return motivos
    
    @staticmethod
    def validar_acesso_usuario_por_localizacao(
        poi_amigavel: str, 
        localizacao: str, 
        areas_usuario: List[str]
    ) -> bool:
        """
        Validação SIMPLES e DIRETA - Mapeamento estático área → POI
        """
        if not areas_usuario:
            return False
        
        # MAPEAMENTO DIRETO: Área do usuário → POIs que ele pode ver
        MAPEAMENTO_ACESSO = {
            # P.A. específicos por unidade
            "pa agua clara rrp": ["PA AGUA CLARA"],
            "pa celulose tls": ["PACELULOSE"],
            
            # Carregamento/Fábrica por unidade  
            "carregamento fábrica rrp": ["CARREGAMENTOFABRICARRP", "CARREGAMENTOFABRICA"],
            "carregamento fabrica rrp": ["CARREGAMENTOFABRICARRP", "CARREGAMENTOFABRICA"],
            "fábrica rrp": ["CARREGAMENTOFABRICARRP", "CARREGAMENTOFABRICA"],
            "fabrica rrp": ["CARREGAMENTOFABRICARRP", "CARREGAMENTOFABRICA"],
            
            "carregamento fábrica tls": ["CARREGAMENTOFABRICATLS", "CARREGAMENTOFABRICA"],
            "carregamento fabrica tls": ["CARREGAMENTOFABRICATLS", "CARREGAMENTOFABRICA"],
            "fábrica tls": ["CARREGAMENTOFABRICATLS", "CARREGAMENTOFABRICA"],
            "fabrica tls": ["CARREGAMENTOFABRICATLS", "CARREGAMENTOFABRICA"],
            
            # Terminal por unidade
            "terminal rrp": ["TERMINALINOCENCIA", "DESCARGAINOCENCIA"],
            "terminal tls": ["DESCARGATAP", "TERMINAL"],
            
            # Manutenção por unidade
            "manutenção rrp": ["OFICINAJSL", "OFICINA"],
            "manutencao rrp": ["OFICINAJSL", "OFICINA"],
            "oficina rrp": ["OFICINAJSL", "OFICINA"],
            
            "manutenção tls": ["OFICINA"],
            "manutencao tls": ["OFICINA"],
            "oficina tls": ["OFICINA"],
            
            # Áreas especiais (veem tudo)
            "geral": ["*"],  # * = todos os POIs
            "all": ["*"],
            "todos": ["*"],
            "todas": ["*"]
        }
        
        # Normaliza áreas do usuário
        areas_normalizadas = [area.strip().lower() for area in areas_usuario]
        
        logger.info(f"🔍 [VALIDAÇÃO SIMPLES] POI: {poi_amigavel}, Áreas usuário: {areas_usuario}")
        
        # Extrai o POI original do título para comparação
        poi_original = LocationProcessor._extrair_poi_original_do_titulo(poi_amigavel)
        logger.info(f"📋 POI original extraído: {poi_original}")
        
        # Verifica cada área do usuário
        for area_usuario in areas_normalizadas:
            pois_permitidos = MAPEAMENTO_ACESSO.get(area_usuario, [])
            
            # Área especial "geral" vê tudo
            if "*" in pois_permitidos:
                logger.info(f"✅ Acesso liberado - Área especial: {area_usuario}")
                return True
            
            # Verifica se POI está na lista permitida
            if poi_original in pois_permitidos:
                logger.info(f"✅ Acesso liberado - Match direto: {area_usuario} → {poi_original}")
                return True
        
        logger.info(f"❌ Acesso negado - Nenhuma área permite POI: {poi_original}")
        return False

    @staticmethod
    def _extrair_poi_original_do_titulo(poi_amigavel: str) -> str:
        """
        Extrai o POI original (como aparece no SharePoint) do nome amigável
        
        Args:
            poi_amigavel: "P.A. Celulose - TLS" 
            
        Returns:
            "PACELULOSE" (como está na coluna Ponto_de_Interesse)
        """
        
        # MAPEAMENTO REVERSO: Nome amigável → POI original do SharePoint
        MAPEAMENTO_REVERSO = {
            "p.a. água clara - rrp": "PA AGUA CLARA",
            "p.a. agua clara - rrp": "PA AGUA CLARA", 
            "p.a. celulose - tls": "PACELULOSE",
            
            "carregamento fábrica - rrp": "CARREGAMENTOFABRICARRP",
            "carregamento fabrica - rrp": "CARREGAMENTOFABRICARRP",
            "carregamento fábrica - tls": "CARREGAMENTOFABRICATLS", 
            "carregamento fabrica - tls": "CARREGAMENTOFABRICATLS",
            
            "terminal inocência - rrp": "TERMINALINOCENCIA",
            "terminal inocencia - rrp": "TERMINALINOCENCIA",
            "terminal aparecida - tls": "DESCARGATAP",
            
            "manutenção - rrp": "OFICINAJSL",
            "manutencao - rrp": "OFICINAJSL", 
            "manutenção - tls": "OFICINA",
            "manutencao - tls": "OFICINA"
        }
        
        poi_normalizado = poi_amigavel.strip().lower()
        poi_original = MAPEAMENTO_REVERSO.get(poi_normalizado, poi_normalizado.upper())
        
        return poi_original

    @staticmethod
    def validar_acesso_usuario_por_localizacao(
        poi_amigavel: str, 
        localizacao: str, 
        areas_usuario: List[str]
    ) -> bool:
        """
        Verifica se usuário tem acesso ao POI considerando localização
        """
        if not areas_usuario:
            return False
        
        # Normaliza áreas do usuário
        areas_normalizadas = [area.strip().lower() for area in areas_usuario]
        poi_lower = poi_amigavel.lower()
        localizacao_lower = localizacao.lower()
        
        logger.debug(f"🔍 Validando acesso: POI='{poi_amigavel}', Localização='{localizacao}', Áreas={areas_usuario}")
        
        # 1. VERIFICAÇÃO PRIMÁRIA: Match EXATO unidade + categoria
        for area in areas_normalizadas:
            # Verifica se a área contém a localização específica
            if localizacao_lower in area:
                acesso_concedido = LocationProcessor._validar_acesso_unidade_especifica(
                    area, poi_lower, localizacao_lower
                )
                if acesso_concedido:
                    logger.debug(f"✅ Acesso concedido via área específica: {area}")
                    return True
            
            # ÁREAS ESPECIAIS (sempre têm acesso)
            elif area in ["geral", "all", "todos", "todas"]:
                logger.debug(f"✅ Acesso concedido via área especial: {area}")
                return True
        
        # 2. VERIFICAÇÃO SECUNDÁRIA: Formato legado MUITO restritivo
        for area in areas_normalizadas:
            # Só processa se não tem localização específica na área
            if not any(loc in area for loc in ["rrp", "tls"]):
                acesso_concedido = LocationProcessor._validar_acesso_legado_restritivo(
                    area, poi_lower, localizacao_lower
                )
                if acesso_concedido:
                    logger.debug(f"✅ Acesso concedido via formato legado: {area}")
                    return True
        
        # 2. FORMATO ANTIGO (Compatibilidade) - Match mais específico
        for area in areas_normalizadas:
            if not any(loc in area for loc in ["rrp", "tls"]):  # Só processa se não tem localização
                acesso_concedido = LocationProcessor._validar_acesso_legado_rigoroso(area, poi_lower)
                if acesso_concedido:
                    return True
        
        # 3. ÁREAS ESPECIAIS
        for area in areas_normalizadas:
            if area in ["geral", "all", "todos", "todas"]:
                return True

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
                "Carregamento Fábrica", 
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
    """Valida acesso do usuário ao POI"""
    return location_processor.validar_acesso_usuario_por_localizacao(poi_amigavel, localizacao, areas_usuario)


def obter_areas_disponiveis() -> Dict[str, List[str]]:
    """Obtém todas as áreas disponíveis"""
    return location_processor.obter_areas_disponiveis()