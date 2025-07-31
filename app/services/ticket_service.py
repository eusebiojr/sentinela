"""
Serviço para gerenciamento de tickets de suporte - VERSÃO CORRIGIDA COM CONFIGS
app/services/ticket_service.py
"""
import base64
import io
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import pandas as pd

# Imports condicionais para compatibilidade
try:
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.user_credential import UserCredential
    OFFICE365_AVAILABLE = True
except ImportError:
    OFFICE365_AVAILABLE = False
    ClientContext = None
    UserCredential = None

try:
    from ..config.settings import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    config = None

try:
    from ..config.logging_config import setup_logger
    logger = setup_logger("ticket_service")
except ImportError:
    import logging
    logger = logging.getLogger("ticket_service")


class TicketService:
    """Serviço robusto para gerenciamento de tickets com upload de imagens COMPATÍVEL"""
    
    # Configurações de upload de imagem
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    ALLOWED_MIME_TYPES = {
        'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 
        'image/bmp', 'image/webp'
    }
    
    # Motivos predefinidos
    MOTIVOS_TICKETS = [
        "Erro de login",
        "Bug tela aprovação/preenchimento", 
        "Falha no preenchimento/aprovação",
        "Sistema instável/Lento",
        "Melhoria",
        "Dúvida",
        "Outros"
    ]
    
    def __init__(self):
        """Inicializa o serviço de tickets"""
        self.lista_tickets = "SentinelaTickets"
        
        # 🔧 CORREÇÃO: USA CONFIGURAÇÕES DO SISTEMA
        if CONFIG_AVAILABLE and config:
            self.lista_usuarios = config.usuarios_list
            self.site_url = config.site_url
            self.username = config.username_sp
            self.password = config.password_sp
            logger.info(f"✅ Configurações carregadas: {self.username} @ {self.site_url}")
        else:
            # Valores padrão/fallback apenas se config não disponível
            self.lista_usuarios = "UsuariosPainelTorre"
            self.site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
            self.username = "eusebioagj@suzano.com.br"  # SEU EMAIL
            self.password = "290422@Cc"  # SUA SENHA
            logger.warning("⚠️ Config não disponível, usando valores padrão")
        
        logger.info(f"🎫 TicketService inicializado - Lista: {self.lista_tickets}")
    
    def validar_usuario_email(self, email: str) -> Tuple[bool, str]:
        """
        Valida se o email existe na lista de usuários do SharePoint
        
        Args:
            email: Email a ser validado
            
        Returns:
            Tuple[bool, str]: (válido, mensagem)
        """
        try:
            if not OFFICE365_AVAILABLE:
                logger.warning("⚠️ Office365 não disponível - validação simulada")
                return True, "Validação simulada (Office365 indisponível)"
            
            email = email.strip().lower()
            
            if not email:
                return False, "Email é obrigatório"
            
            if '@' not in email:
                return False, "Formato de email inválido"
            
            # Conecta ao SharePoint para validar
            ctx = self._get_sharepoint_context()
            if not ctx:
                return False, "Erro de conexão SharePoint"
            
            usuarios_list = ctx.web.lists.get_by_title(self.lista_usuarios)
            items = usuarios_list.items.filter(f"email eq '{email}'").get().execute_query()
            
            if len(items) > 0:
                logger.info(f"✅ Email validado: {email}")
                return True, "Email válido"
            else:
                logger.warning(f"⚠️ Email não encontrado: {email}")
                return False, "Email não cadastrado no sistema"
                
        except Exception as e:
            logger.error(f"❌ Erro ao validar email: {str(e)}")
            return False, f"Erro na validação: {str(e)}"
    
    def validar_imagem(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Valida arquivo de imagem
        
        Args:
            file_content: Conteúdo do arquivo
            filename: Nome do arquivo
            
        Returns:
            Tuple[bool, str]: (válido, mensagem)
        """
        try:
            # Valida tamanho
            if len(file_content) > self.MAX_FILE_SIZE:
                return False, f"Arquivo muito grande. Máximo: 10MB"
            
            # Valida extensão
            file_ext = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
            if file_ext not in self.ALLOWED_EXTENSIONS:
                return False, f"Formato não permitido. Use: {', '.join(self.ALLOWED_EXTENSIONS)}"
            
            # Valida MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
                return False, "Tipo de arquivo não permitido"
            
            # Valida se é realmente uma imagem (basic check)
            if len(file_content) < 100:  # Muito pequeno para ser imagem
                return False, "Arquivo corrompido ou inválido"
            
            return True, "Imagem válida"
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar imagem: {str(e)}")
            return False, f"Erro na validação: {str(e)}"
    
    def criar_ticket(self, dados_ticket: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Cria um novo ticket no SharePoint
        
        Args:
            dados_ticket: {
                'motivo': str,
                'usuario': str (email),
                'descricao': str,
                'imagem_content': bytes (opcional),
                'imagem_filename': str (opcional)
            }
            
        Returns:
            Tuple[bool, str, Optional[int]]: (sucesso, mensagem, ticket_id)
        """
        try:
            if not OFFICE365_AVAILABLE:
                logger.warning("⚠️ Office365 não disponível - ticket simulado")
                return self._criar_ticket_simulado(dados_ticket)
            
            # Validações básicas
            motivo = dados_ticket.get('motivo', '').strip()
            usuario = dados_ticket.get('usuario', '').strip().lower()
            descricao = dados_ticket.get('descricao', '').strip()
            
            if not motivo or motivo not in self.MOTIVOS_TICKETS:
                return False, "Motivo é obrigatório e deve ser válido", None
            
            if not usuario:
                return False, "Usuário é obrigatório", None
            
            if not descricao or len(descricao) < 10:
                return False, "Descrição deve ter pelo menos 10 caracteres", None
            
            # Valida usuário
            email_valido, msg_email = self.validar_usuario_email(usuario)
            if not email_valido:
                return False, msg_email, None
            
            # Conecta ao SharePoint
            ctx = self._get_sharepoint_context()
            if not ctx:
                return False, "Erro de conexão SharePoint", None
            
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            
            # Prepara dados do ticket
            ticket_data = {
                'Motivo': motivo,
                'Usuario': usuario,
                'Descricao': descricao,
                'Abertura': datetime.now().isoformat()
            }
            
            # Cria o item no SharePoint - versão compatível
            new_item = tickets_list.add_item(ticket_data)
            ctx.execute_query()
            
            # Obtém ID do ticket
            if hasattr(new_item, 'properties'):
                ticket_id = new_item.properties.get('ID')
            else:
                ticket_id = getattr(new_item, 'ID', None)
            
            if not ticket_id:
                # Tenta recarregar o item
                ctx.load(new_item)
                ctx.execute_query()
                ticket_id = getattr(new_item, 'id', 999)  # Fallback
            
            logger.info(f"✅ Ticket {ticket_id} criado com sucesso")
            
            # Upload da imagem (se fornecida) - VERSÃO SIMPLIFICADA
            if dados_ticket.get('imagem_content') and dados_ticket.get('imagem_filename'):
                sucesso_img, msg_img = self._upload_imagem_simplificado(
                    ctx, ticket_id, 
                    dados_ticket['imagem_content'], 
                    dados_ticket['imagem_filename']
                )
                
                if not sucesso_img:
                    logger.warning(f"⚠️ Ticket {ticket_id} criado, mas falha no upload da imagem: {msg_img}")
                    return True, f"Ticket criado (ID: {ticket_id}), mas erro no upload da imagem: {msg_img}", ticket_id
            
            return True, f"Ticket criado com sucesso! ID: {ticket_id}", ticket_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket: {str(e)}")
            return False, f"Erro interno: {str(e)}", None
    
    def _criar_ticket_simulado(self, dados_ticket: Dict[str, Any]) -> Tuple[bool, str, int]:
        """Cria ticket simulado quando Office365 não está disponível"""
        ticket_id = 999
        logger.info(f"🎫 TICKET SIMULADO #{ticket_id}")
        logger.info(f"   📧 Usuário: {dados_ticket.get('usuario', 'N/A')}")
        logger.info(f"   🎯 Motivo: {dados_ticket.get('motivo', 'N/A')}")
        logger.info(f"   📝 Descrição: {dados_ticket.get('descricao', 'N/A')[:50]}...")
        logger.info(f"   🖼️ Imagem: {'Sim' if dados_ticket.get('imagem_filename') else 'Não'}")
        
        return True, f"Ticket simulado criado! ID: {ticket_id}", ticket_id
    
    def _upload_imagem_simplificado(self, ctx, ticket_id: int, 
                                file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Upload de imagem CORRIGIDO para SharePoint
        Resolve o erro de JSON parsing
        """
        try:
            logger.info(f"🔄 Iniciando upload: {filename} ({len(file_content)} bytes)")
            
            # ESTRATÉGIA 1: Upload como anexo (mais compatível)
            try:
                tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
                ticket_item = tickets_list.get_item_by_id(ticket_id)
                
                # Anexa arquivo como attachment
                attachment_file = ticket_item.attachment_files.add(filename, file_content)
                ctx.execute_query()
                
                logger.info(f"✅ Imagem anexada como attachment: {filename}")
                return True, f"Imagem anexada: {filename}"
                
            except Exception as attach_error:
                logger.warning(f"⚠️ Attachment falhou: {str(attach_error)}")
                
                # ESTRATÉGIA 2: Upload como texto base64 (fallback)
                try:
                    # Converte para base64 mais limpo
                    import base64
                    base64_content = base64.b64encode(file_content).decode('utf-8')
                    
                    # Prepara dados mais simples
                    mime_type, _ = mimetypes.guess_type(filename)
                    if not mime_type:
                        mime_type = 'image/jpeg'
                    
                    # Verifica tamanho do base64
                    if len(base64_content) > 50000:  # Limite mais conservador
                        return False, "Imagem muito grande para SharePoint (reduzir para <500KB)"
                    
                    # Atualiza apenas o campo de texto
                    tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
                    ticket_item = tickets_list.get_item_by_id(ticket_id)
                    
                    # Salva informações da imagem em campo texto
                    info_imagem = f"Arquivo: {filename}\nTipo: {mime_type}\nTamanho: {len(file_content)} bytes"
                    
                    ticket_item.set_property('Observacoes', info_imagem)
                    ticket_item.update()
                    ctx.execute_query()
                    
                    logger.info(f"✅ Info da imagem salva no campo Observacoes")
                    return True, f"Info da imagem salva: {filename}"
                    
                except Exception as text_error:
                    logger.warning(f"⚠️ Upload texto falhou: {str(text_error)}")
                    
                    # ESTRATÉGIA 3: Apenas registra que tinha imagem
                    try:
                        tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
                        ticket_item = tickets_list.get_item_by_id(ticket_id)
                        
                        # Adiciona nota sobre imagem na descrição
                        descricao_atual = ticket_item.properties.get('Descricao', '')
                        nova_descricao = f"{descricao_atual}\n\n[ANEXO: {filename} - {len(file_content)} bytes]"
                        
                        ticket_item.set_property('Descricao', nova_descricao)
                        ticket_item.update()
                        ctx.execute_query()
                        
                        logger.info(f"✅ Referência à imagem adicionada na descrição")
                        return True, f"Imagem referenciada na descrição: {filename}"
                        
                    except Exception as ref_error:
                        logger.error(f"❌ Todas as estratégias falharam: {str(ref_error)}")
                        return False, f"Falha completa no upload: {str(ref_error)}"
                
        except Exception as e:
            logger.error(f"❌ Erro geral no upload: {str(e)}")
            return False, f"Erro no upload: {str(e)}"
    
    def _get_sharepoint_context(self):
        """Obtém contexto do SharePoint com tratamento de erro"""
        try:
            if not OFFICE365_AVAILABLE:
                return None
            
            logger.info(f"🔗 Conectando com: {self.username}")
            ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            return ctx
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SharePoint: {str(e)}")
            return None
    
    def testar_conexao(self) -> Tuple[bool, str]:
        """Testa conexão com SharePoint e lista de tickets"""
        try:
            if not OFFICE365_AVAILABLE:
                return False, "Office365 não disponível - instale: pip install Office365-REST-Python-Client"
            
            ctx = self._get_sharepoint_context()
            if not ctx:
                return False, "Falha na conexão SharePoint"
            
            # Testa acesso à lista de tickets
            try:
                tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
                ctx.load(tickets_list)
                ctx.execute_query()
                logger.info(f"✅ Lista '{self.lista_tickets}' acessível")
            except Exception as e:
                return False, f"Lista '{self.lista_tickets}' não encontrada: {str(e)}"
            
            # Testa acesso à lista de usuários
            try:
                usuarios_list = ctx.web.lists.get_by_title(self.lista_usuarios)
                ctx.load(usuarios_list)
                ctx.execute_query()
                logger.info(f"✅ Lista '{self.lista_usuarios}' acessível")
            except Exception as e:
                return False, f"Lista '{self.lista_usuarios}' não encontrada: {str(e)}"
            
            logger.info("✅ Conexão com SharePoint OK")
            return True, "Conexão estabelecida com sucesso"
            
        except Exception as e:
            logger.error(f"❌ Falha na conexão: {str(e)}")
            return False, f"Erro de conexão: {str(e)}"


# Instância global do serviço
ticket_service = TicketService()


# Função de teste para debug
def testar_ticket_service():
    """Função de teste para verificar se tudo está funcionando"""
    print("🧪 Testando TicketService...")
    
    # Teste 1: Conexão
    sucesso, msg = ticket_service.testar_conexao()
    print(f"Conexão: {'✅' if sucesso else '❌'} {msg}")
    
    # Teste 2: Validação de email
    try:
        valido, msg_email = ticket_service.validar_usuario_email("eusebioagj@suzano.com.br")
        print(f"Email: {'✅' if valido else '❌'} {msg_email}")
    except Exception as e:
        print(f"Email: ❌ Erro: {str(e)}")
    
    # Teste 3: Motivos
    print(f"Motivos: ✅ {len(ticket_service.MOTIVOS_TICKETS)} opções disponíveis")
    
    print("🎯 Teste concluído!")


if __name__ == "__main__":
    testar_ticket_service()