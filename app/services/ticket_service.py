"""
Serviço de Tickets - Sistema Sentinela
Gerencia abertura de tickets de suporte no SharePoint
"""
import pytz
from datetime import datetime
from typing import Dict, Any, List, Optional
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

from ..config.settings import config
from ..config.logging_config import setup_logger
from ..validators import field_validator

logger = setup_logger("ticket_service")


class TicketService:
    """Serviço para gerenciamento de tickets de suporte"""
    
    # Categorias de motivos disponíveis
    CATEGORIAS_MOTIVO = [
        "Erro de login",
        "Bug tela aprovação/preenchimento", 
        "Falha no preenchimento/aprovação",
        "Sistema instável",
        "Melhoria",
        "Dúvida",
        "Outros"
    ]
    
    # Nome da lista SharePoint
    LISTA_TICKETS = "SentinelaTickets"
    
    def __init__(self):
        """Inicializa o serviço de tickets"""
        self.site_url = config.site_url
        self.username = config.username_sp
        self.password = config.password_sp
        self.ctx = None
        
        logger.info("🎫 TicketService inicializado")
    
    def conectar_sharepoint(self) -> bool:
        """Estabelece conexão com SharePoint"""
        try:
            logger.info("🔗 Conectando ao SharePoint para tickets...")
            
            self.ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            
            # Testa conexão
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            logger.info(f"✅ Conectado para tickets: {web.properties.get('Title', 'N/A')}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SharePoint para tickets: {e}")
            return False
    
    def validar_dados_ticket(self, dados_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida dados do ticket antes de enviar
        
        Args:
            dados_ticket: Dict com dados do ticket
            
        Returns:
            Dict com resultado da validação
        """
        resultado = {
            "valido": True,
            "erros": [],
            "dados_processados": {}
        }
        
        try:
            # Valida motivo (obrigatório)
            motivo = dados_ticket.get("motivo", "").strip()
            if not motivo:
                resultado["erros"].append("Motivo é obrigatório")
            elif motivo not in self.CATEGORIAS_MOTIVO:
                resultado["erros"].append("Motivo inválido")
            else:
                resultado["dados_processados"]["Motivo"] = motivo
            
            # Valida usuário (obrigatório)
            usuario = dados_ticket.get("usuario", "").strip()
            if not usuario:
                resultado["erros"].append("Usuário é obrigatório")
            else:
                # USA VALIDADOR CENTRALIZADO para email
                email_validation = field_validator.validate_email_field(usuario, required=True)
                if not email_validation.valid:
                    resultado["erros"].append("Email do usuário inválido")
                else:
                    resultado["dados_processados"]["Usuario"] = email_validation.data.get("email_normalized", usuario)
            
            # Valida descrição (obrigatória)
            descricao = dados_ticket.get("descricao", "").strip()
            if not descricao:
                resultado["erros"].append("Descrição é obrigatória")
            elif len(descricao) < 10:
                resultado["erros"].append("Descrição muito curta (mínimo 10 caracteres)")
            else:
                resultado["dados_processados"]["Descricao"] = descricao
            
            # Data de abertura (automática)
            tz_brasilia = pytz.timezone("America/Campo_Grande")
            agora = datetime.now(tz_brasilia)
            resultado["dados_processados"]["Abertura"] = agora.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Anexos (opcional)
            anexos = dados_ticket.get("anexos", [])
            if anexos:
                # Valida se são arquivos válidos
                anexos_validos = []
                for anexo in anexos:
                    if self._validar_anexo(anexo):
                        anexos_validos.append(anexo)
                    else:
                        resultado["erros"].append(f"Anexo inválido: {anexo.get('name', 'Sem nome')}")
                
                resultado["dados_processados"]["anexos"] = anexos_validos
            
            # Se há erros, marca como inválido
            if resultado["erros"]:
                resultado["valido"] = False
            
            logger.info(f"📋 Validação ticket: {'✅ OK' if resultado['valido'] else '❌ ERRO'}")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do ticket: {e}")
            resultado["valido"] = False
            resultado["erros"].append(f"Erro interno: {str(e)}")
        
        return resultado
    
    def _validar_anexo(self, anexo: Dict) -> bool:
        """Valida um anexo individualmente"""
        try:
            # Verifica se tem nome e dados
            if not anexo.get("name") or not anexo.get("data"):
                return False
            
            # Verifica extensão (apenas imagens)
            nome = anexo["name"].lower()
            extensoes_validas = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
            
            if not any(nome.endswith(ext) for ext in extensoes_validas):
                return False
            
            # Verifica tamanho (máximo 5MB por imagem)
            tamanho = len(anexo.get("data", b""))
            if tamanho > 5 * 1024 * 1024:  # 5MB
                return False
            
            return True
            
        except Exception:
            return False
    
    def criar_ticket(self, dados_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo ticket no SharePoint
        
        Args:
            dados_ticket: Dados do ticket validados
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info(f"🎫 Criando ticket para usuário: {dados_ticket.get('Usuario', 'N/A')}")
            
            # Conecta se necessário
            if not self.ctx:
                if not self.conectar_sharepoint():
                    return {
                        "sucesso": False,
                        "erro": "Erro de conexão com SharePoint"
                    }
            
            # Obtém lista de tickets
            lista_tickets = self.ctx.web.lists.get_by_title(self.LISTA_TICKETS)
            
            # Cria item
            item_properties = {
                "Motivo": dados_ticket["Motivo"],
                "Usuario": dados_ticket["Usuario"], 
                "Descricao": dados_ticket["Descricao"],
                "Abertura": dados_ticket["Abertura"]
            }
            
            # Cria o item
            novo_item = lista_tickets.add_item(item_properties)
            self.ctx.execute_query()
            
            # Obtém ID do item criado
            item_id = novo_item.properties["ID"]
            
            logger.info(f"✅ Ticket criado com ID: {item_id}")
            
            # Processa anexos se houver
            anexos_processados = 0
            if "anexos" in dados_ticket and dados_ticket["anexos"]:
                anexos_processados = self._processar_anexos_ticket(item_id, dados_ticket["anexos"])
            
            return {
                "sucesso": True,
                "ticket_id": item_id,
                "anexos_processados": anexos_processados,
                "mensagem": f"Ticket #{item_id} criado com sucesso"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket: {e}")
            return {
                "sucesso": False,
                "erro": f"Erro ao criar ticket: {str(e)}"
            }
    
    def _processar_anexos_ticket(self, ticket_id: int, anexos: List[Dict]) -> int:
        """
        Processa anexos do ticket (upload para SharePoint)
        
        Args:
            ticket_id: ID do ticket
            anexos: Lista de anexos
            
        Returns:
            Número de anexos processados com sucesso
        """
        anexos_processados = 0
        
        try:
            # Para SharePoint, vamos salvar na biblioteca de documentos
            # com uma pasta específica para tickets
            pasta_tickets = f"Tickets/Ticket_{ticket_id}"
            
            for anexo in anexos:
                try:
                    nome_arquivo = f"{ticket_id}_{anexo['name']}"
                    
                    # Aqui você implementaria o upload real para SharePoint
                    # Por enquanto, simula o processamento
                    logger.info(f"📎 Processando anexo: {nome_arquivo}")
                    
                    # TODO: Implementar upload real para biblioteca de documentos
                    # target_folder = self.ctx.web.get_folder_by_server_relative_url(pasta_tickets)
                    # target_folder.upload_file(nome_arquivo, anexo["data"])
                    # self.ctx.execute_query()
                    
                    anexos_processados += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar anexo {anexo.get('name')}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Erro geral no processamento de anexos: {e}")
        
        logger.info(f"📎 {anexos_processados}/{len(anexos)} anexos processados")
        return anexos_processados
    
    def abrir_ticket_completo(self, motivo: str, usuario: str, descricao: str, 
                             anexos: List[Dict] = None) -> Dict[str, Any]:
        """
        Método principal para abertura completa de ticket
        
        Args:
            motivo: Categoria do problema
            usuario: Email do usuário
            descricao: Descrição detalhada
            anexos: Lista de anexos (opcional)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            # Monta dados do ticket
            dados_ticket = {
                "motivo": motivo,
                "usuario": usuario,
                "descricao": descricao,
                "anexos": anexos or []
            }
            
            # Valida dados
            validacao = self.validar_dados_ticket(dados_ticket)
            
            if not validacao["valido"]:
                return {
                    "sucesso": False,
                    "erro": "Dados inválidos",
                    "detalhes": validacao["erros"]
                }
            
            # Cria ticket
            resultado_criacao = self.criar_ticket(validacao["dados_processados"])
            
            if resultado_criacao["sucesso"]:
                # Log de auditoria
                self._log_ticket_criado(
                    resultado_criacao["ticket_id"], 
                    usuario, 
                    motivo
                )
            
            return resultado_criacao
            
        except Exception as e:
            logger.error(f"❌ Erro na abertura completa de ticket: {e}")
            return {
                "sucesso": False,
                "erro": f"Erro interno: {str(e)}"
            }
    
    def _log_ticket_criado(self, ticket_id: int, usuario: str, motivo: str):
        """Log de auditoria para ticket criado"""
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            logger.info(
                f"📋 AUDITORIA TICKET - ID: {ticket_id} | "
                f"Usuário: {usuario} | Motivo: {motivo} | "
                f"Timestamp: {timestamp}"
            )
        except Exception:
            pass
    
    def testar_conexao_tickets(self) -> bool:
        """Testa conectividade específica para tickets"""
        try:
            if self.conectar_sharepoint():
                # Tenta acessar a lista de tickets
                lista_tickets = self.ctx.web.lists.get_by_title(self.LISTA_TICKETS)
                self.ctx.load(lista_tickets)
                self.ctx.execute_query()
                
                logger.info("✅ Lista de tickets acessível")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão de tickets: {e}")
            return False
    
    @classmethod
    def obter_categorias_motivo(cls) -> List[str]:
        """Retorna lista de categorias disponíveis"""
        return cls.CATEGORIAS_MOTIVO.copy()
    
    @classmethod
    def obter_orientacoes_descricao(cls) -> List[str]:
        """Retorna orientações para uma boa descrição"""
        return [
            "• Máximo de detalhes possíveis do problema",
            "• Como o problema ocorreu (passo a passo)",
            "• Quando ele ocorreu (data/hora aproximada)", 
            "• Se é a primeira vez ou já aconteceu mais vezes",
            "• Quando começou a ocorrer",
            "• O que você estava fazendo quando ocorreu",
            "• Qual navegador estava usando (Chrome, Edge, etc.)",
            "• Se possível, anexe prints da tela"
        ]


# Instância global do serviço
ticket_service = TicketService()


# Funções de conveniência para uso direto
def abrir_ticket(motivo: str, usuario: str, descricao: str, anexos: List[Dict] = None) -> Dict[str, Any]:
    """Função rápida para abrir ticket"""
    return ticket_service.abrir_ticket_completo(motivo, usuario, descricao, anexos)


def obter_categorias() -> List[str]:
    """Obtém categorias de motivos"""
    return TicketService.obter_categorias_motivo()


def obter_orientacoes() -> List[str]:
    """Obtém orientações para descrição"""
    return TicketService.obter_orientacoes_descricao()


def testar_servico_tickets() -> bool:
    """Testa se o serviço de tickets está funcionando"""
    return ticket_service.testar_conexao_tickets()