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
    
    def _processar_anexos_ticket_imagem(self, ticket_id: int, anexos: List[Dict]) -> int:
        """
        Processa anexos para campo Print tipo IMAGEM
        Substitua no ticket_service.py
        """
        anexos_processados = 0
        
        try:
            logger.info(f"📎 Processando {len(anexos)} anexos para campo Print (Imagem)...")
            
            if not self.ctx or not anexos:
                logger.warning("❌ Sem contexto SharePoint ou anexos vazios")
                return 0
            
            # Pega apenas o primeiro anexo para o campo Print
            primeiro_anexo = anexos[0]
            nome_original = primeiro_anexo.get('original_name', 'imagem.jpg')
            dados_arquivo = primeiro_anexo.get('data', b'')
            
            if not dados_arquivo:
                logger.warning("⚠️ Primeiro anexo sem dados")
                return 0
            
            logger.info(f"📎 Processando anexo para campo Print: {nome_original} ({len(dados_arquivo)} bytes)")
            
            try:
                # Obtém o item do ticket
                lista_tickets = self.ctx.web.lists.get_by_title(self.LISTA_TICKETS)
                item_ticket = lista_tickets.get_item_by_id(ticket_id)
                
                # MÉTODO 1: Upload direto para campo de imagem
                try:
                    logger.info("📷 Tentando upload direto para campo Print...")
                    
                    # Para campo tipo Imagem, precisa fazer upload para biblioteca primeiro
                    biblioteca_documentos = "Shared Documents"
                    web = self.ctx.web
                    doc_lib = web.lists.get_by_title(biblioteca_documentos)
                    root_folder = doc_lib.root_folder
                    
                    # Nome único para o arquivo
                    import uuid
                    nome_unico = f"ticket_{ticket_id}_{uuid.uuid4().hex[:8]}_{nome_original}"
                    
                    # Upload para biblioteca
                    arquivo_enviado = root_folder.upload_file(nome_unico, dados_arquivo)
                    self.ctx.execute_query()
                    
                    # Obtém URL do arquivo
                    self.ctx.load(arquivo_enviado)
                    self.ctx.execute_query()
                    url_arquivo = arquivo_enviado.serverRelativeUrl
                    
                    logger.info(f"✅ Arquivo enviado para biblioteca: {url_arquivo}")
                    
                    # Atualiza campo Print com URL da imagem
                    item_ticket.set_property("Print", url_arquivo)
                    item_ticket.update()
                    self.ctx.execute_query()
                    
                    logger.info(f"✅ Campo Print atualizado com: {url_arquivo}")
                    anexos_processados = 1
                    
                except Exception as e1:
                    logger.warning(f"⚠️ Método 1 falhou: {e1}")
                    
                    # MÉTODO 2: Base64 inline
                    try:
                        logger.info("📷 Tentando método base64...")
                        
                        import base64
                        dados_base64 = base64.b64encode(dados_arquivo).decode('utf-8')
                        data_url = f"data:image/jpeg;base64,{dados_base64}"
                        
                        # Atualiza campo Print
                        item_ticket.set_property("Print", data_url)
                        item_ticket.update()
                        self.ctx.execute_query()
                        
                        logger.info("✅ Campo Print atualizado com base64")
                        anexos_processados = 1
                        
                    except Exception as e2:
                        logger.error(f"❌ Método 2 também falhou: {e2}")
                
                # Atualiza descrição do ticket SEM "anexos mencionados"
                if anexos_processados > 0:
                    try:
                        # Carrega item atual
                        self.ctx.load(item_ticket)
                        self.ctx.execute_query()
                        
                        descricao_atual = item_ticket.properties.get("Descricao", "")
                        descricao_atualizada = descricao_atual + f"\\n\\n📎 Imagem anexada: {nome_original}"
                        
                        item_ticket.set_property("Descricao", descricao_atualizada)
                        item_ticket.update()
                        self.ctx.execute_query()
                        
                        logger.info("✅ Descrição atualizada com informação do anexo")
                        
                    except Exception as e_desc:
                        logger.warning(f"⚠️ Erro ao atualizar descrição: {e_desc}")
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento do anexo: {e}")
        
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")
        
        logger.info(f"📎 Processamento concluído: {anexos_processados} anexo(s)")
        return anexos_processados

    def _adicionar_referencia_anexo_no_ticket(self, ticket_id: int, nome_arquivo: str, url_arquivo: str):
        """
        Adiciona referência do anexo no campo do ticket
        
        Args:
            ticket_id: ID do ticket
            nome_arquivo: Nome original do arquivo
            url_arquivo: URL do arquivo no SharePoint
        """
        try:
            # Esta função é chamada após cada upload individual
            # Para evitar múltiplas atualizações, apenas registra o link
            logger.debug(f"📎 Anexo registrado: {nome_arquivo} -> {url_arquivo}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao registrar anexo: {e}")

    def _atualizar_ticket_com_anexos_enviados(self, ticket_id: int, anexos_enviados: int, total_anexos: int):
        """
        Atualiza o ticket com informações sobre anexos enviados
        
        Args:
            ticket_id: ID do ticket
            anexos_enviados: Número de anexos enviados com sucesso
            total_anexos: Total de anexos tentados
        """
        try:
            lista_tickets = self.ctx.web.lists.get_by_title(self.LISTA_TICKETS)
            item_ticket = lista_tickets.get_item_by_id(ticket_id)
            
            # Carrega item atual
            self.ctx.load(item_ticket)
            self.ctx.execute_query()
            
            # Obtém descrição atual
            descricao_atual = item_ticket.properties.get("Descricao", "")
            
            # Adiciona informações sobre anexos enviados
            if anexos_enviados == total_anexos:
                status_anexos = f"\n\n📎 ANEXOS ENVIADOS: {anexos_enviados} arquivo(s) enviado(s) com sucesso para SharePoint"
            else:
                status_anexos = f"\n\n📎 ANEXOS ENVIADOS: {anexos_enviados}/{total_anexos} arquivo(s) enviado(s) para SharePoint"
            
            # Localização dos anexos
            status_anexos += f"\n📁 Localização: Shared Documents/Tickets/Ticket_{ticket_id}/"
            
            descricao_atualizada = descricao_atual + status_anexos
            
            # Atualiza o item
            item_ticket.set_property("Descricao", descricao_atualizada)
            item_ticket.update()
            self.ctx.execute_query()
            
            logger.info(f"✅ Ticket #{ticket_id} atualizado com status dos anexos")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao atualizar ticket com status dos anexos: {e}")
    
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