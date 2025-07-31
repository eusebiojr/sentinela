"""
Serviço para gerenciamento de tickets de suporte - VERSÃO CORRIGIDA PARA OFFICE365 v2.4.2
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
        
        if CONFIG_AVAILABLE and config:
            self.lista_usuarios = config.usuarios_list
            self.site_url = config.site_url
            self.username = config.username_sp
            self.password = config.password_sp
        else:
            # Valores padrão/fallback
            self.lista_usuarios = "UsuariosPainelTorre"
            self.site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
            self.username = "usuario@suzano.com.br"
            self.password = "senha"
            logger.warning("⚠️ Config não disponível, usando valores padrão")
        
        logger.info("🎫 TicketService inicializado")
    
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
            
            # Busca usuário por email - versão compatível
            items = usuarios_list.items.filter(f"substringof('{email}', Email)").get()
            ctx.execute_query()
            
            if len(items) == 0:
                return False, "Email não encontrado na base de usuários"
            
            # Encontra o usuário exato
            for item in items:
                if hasattr(item, 'properties'):
                    item_email = item.properties.get('Email', '').lower().strip()
                else:
                    # Fallback para versões antigas
                    item_email = getattr(item, 'Email', '').lower().strip()
                
                if item_email == email:
                    logger.info(f"✅ Email validado: {email}")
                    return True, "Email válido"
            
            return False, "Email não encontrado na base de usuários"
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar email {email}: {str(e)}")
            return False, f"Erro na validação: {str(e)}"
    
    def validar_imagem(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Valida arquivo de imagem
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome do arquivo
            
        Returns:
            Tuple[bool, str]: (válido, mensagem)
        """
        try:
            # Valida tamanho
            if len(file_content) > self.MAX_FILE_SIZE:
                size_mb = len(file_content) / (1024 * 1024)
                return False, f"Arquivo muito grande ({size_mb:.1f}MB). Máximo: 10MB"
            
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
        Upload de imagem SIMPLIFICADO para compatibilidade
        Usa apenas estratégia base64 que é mais compatível
        """
        try:
            # Converte para base64
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            # Prepara dados da imagem
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'image/jpeg'  # Fallback
            
            data_url = f"data:{mime_type};base64,{base64_content}"
            
            # Verifica tamanho (SharePoint tem limites)
            if len(data_url) > 30000:  # Limite conservador
                return False, "Imagem muito grande para upload via base64"
            
            # Atualiza o ticket
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            ticket_item = tickets_list.get_item_by_id(ticket_id)
            
            # Salva como data URL no campo Print
            ticket_item.set_property('Print', data_url)
            ticket_item.update()
            ctx.execute_query()
            
            logger.info(f"✅ Imagem salva como base64: {filename}")
            return True, f"Imagem anexada: {filename}"
            
        except Exception as e:
            logger.error(f"❌ Erro no upload simplificado: {str(e)}")
            return False, f"Falha no upload: {str(e)}"
    
    def _get_sharepoint_context(self):
        """Obtém contexto do SharePoint com tratamento de erro"""
        try:
            if not OFFICE365_AVAILABLE:
                return None
            
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
            except Exception as e:
                return False, f"Lista '{self.lista_tickets}' não encontrada: {str(e)}"
            
            # Testa acesso à lista de usuários
            try:
                usuarios_list = ctx.web.lists.get_by_title(self.lista_usuarios)
                ctx.load(usuarios_list)
                ctx.execute_query()
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
        valido, msg_email = ticket_service.validar_usuario_email("teste@suzano.com.br")
        print(f"Email: {'✅' if valido else '❌'} {msg_email}")
    except Exception as e:
        print(f"Email: ❌ Erro: {str(e)}")
    
    # Teste 3: Motivos
    print(f"Motivos: ✅ {len(ticket_service.MOTIVOS_TICKETS)} opções disponíveis")
    
    print("🎯 Teste concluído!")


if __name__ == "__main__":
    testar_ticket_service()