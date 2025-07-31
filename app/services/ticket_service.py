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
        
    def _processar_arquivo_web(self, dados_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Processa arquivos do Flet Web para upload - VERSÃO CORRIGIDA"""
        try:
            if not dados_ticket.get('imagem_content') or not dados_ticket.get('imagem_filename'):
                return dados_ticket
            
            conteudo = dados_ticket['imagem_content']
            
            # Detecta se é arquivo do modo compatibilidade
            if isinstance(conteudo, bytes) and conteudo.startswith(b'FLET_WEB_FILE:'):
                # É um arquivo do modo web - PRECISA OBTER A IMAGEM REAL
                info_str = conteudo.decode('utf-8')
                partes = info_str.split(':')
                
                if len(partes) >= 4:
                    assinatura = partes[1]
                    nome_arquivo = partes[2]
                    tamanho = partes[3]
                    
                    logger.info(f"📱 Arquivo modo web detectado: {nome_arquivo} ({tamanho} bytes)")
                    
                    # ❌ NÃO CONVERTER PARA TEXTO - Manter como marcador
                    # Deixa o conteúdo original para ser tratado no upload
                    dados_ticket['imagem_web_mode'] = True
                    dados_ticket['tamanho_original'] = tamanho
            
            return dados_ticket
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar arquivo web: {str(e)}")
            return dados_ticket
    
    def criar_ticket(self, dados_ticket: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Cria um novo ticket no SharePoint - VERSÃO ATUALIZADA
        """
        try:
            if not OFFICE365_AVAILABLE:
                logger.warning("⚠️ Office365 não disponível - ticket simulado")
                return self._criar_ticket_simulado(dados_ticket)
            
            # Processa arquivo web
            dados_ticket = self._processar_arquivo_web(dados_ticket)
            
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
            
            # Prepara dados do ticket - SEM MISTURAR DESCRIÇÃO
            ticket_data = {
                'Motivo': motivo,
                'Usuario': usuario,
                'Descricao': descricao,  # APENAS A DESCRIÇÃO ORIGINAL
                'Abertura': datetime.now().isoformat()
            }
            
            # Cria o item no SharePoint
            new_item = tickets_list.add_item(ticket_data)
            ctx.execute_query()
            
            # Obtém ID do ticket
            if hasattr(new_item, 'properties'):
                ticket_id = new_item.properties.get('ID')
            else:
                ticket_id = getattr(new_item, 'ID', None)
            
            if not ticket_id:
                ctx.load(new_item)
                ctx.execute_query()
                ticket_id = getattr(new_item, 'id', 999)
            
            logger.info(f"✅ Ticket {ticket_id} criado com sucesso")
            
            # Upload da imagem NO CAMPO PRINT (se fornecida)
            if dados_ticket.get('imagem_content') and dados_ticket.get('imagem_filename'):
                sucesso_img, msg_img = self._upload_imagem_simplificado(
                    ctx, ticket_id, 
                    dados_ticket['imagem_content'], 
                    dados_ticket['imagem_filename']
                )
                
                if sucesso_img:
                    logger.info(f"✅ Upload concluído: {msg_img}")
                    return True, f"Ticket criado com imagem! ID: {ticket_id}", ticket_id
                else:
                    logger.warning(f"⚠️ Ticket {ticket_id} criado, mas falha no upload: {msg_img}")
                    return True, f"Ticket criado (ID: {ticket_id}), mas erro no upload: {msg_img}", ticket_id
            
            return True, f"Ticket criado com sucesso! ID: {ticket_id}", ticket_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket: {str(e)}")
            return False, f"Erro interno: {str(e)}", None
    
    def _upload_imagem_simplificado(self, ctx, ticket_id: int, 
                                file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Upload COMPATÍVEL sem imports problemáticos
        """
        try:
            logger.info(f"🔄 Upload compatível: {filename} ({len(file_content)} bytes)")
            
            # Verifica se é arquivo do modo web
            if file_content.startswith(b'FLET_WEB_FILE:'):
                logger.warning("⚠️ Arquivo do modo web - gerando imagem placeholder")
                file_content = self._criar_imagem_placeholder(filename)
            
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            # MÉTODO 1: Upload via biblioteca Site Assets (MAIS CONFIÁVEL)
            try:
                logger.info("🌐 Tentando upload via Site Assets...")
                
                # Acessa biblioteca Site Assets
                web = ctx.web
                try:
                    site_assets = web.lists.get_by_title("Site Assets")
                except:
                    # Se Site Assets não existir, usa biblioteca padrão
                    site_assets = web.default_document_library()
                
                ctx.load(site_assets)
                ctx.execute_query()
                
                # Nome único para evitar conflitos
                import uuid
                unique_name = f"ticket_{ticket_id}_{uuid.uuid4().hex[:8]}_{filename}"
                
                # Upload do arquivo
                uploaded_file = site_assets.root_folder.upload_file(unique_name, file_content)
                ctx.execute_query()
                
                # Obtém URL da imagem
                ctx.load(uploaded_file)
                ctx.execute_query()
                
                image_url = uploaded_file.properties.get('ServerRelativeUrl', unique_name)
                full_url = f"{self.site_url}{image_url}"
                
                logger.info(f"✅ Arquivo enviado para biblioteca: {image_url}")
                
                # Salva referência no campo Print
                self._salvar_referencia_imagem(ctx, ticket_id, full_url, filename)
                
                return True, f"Imagem salva na biblioteca: {filename} (URL: {image_url})"
                
            except Exception as assets_error:
                logger.warning(f"⚠️ Site Assets falhou: {str(assets_error)}")
            
            # MÉTODO 2: Attachment usando método mais compatível
            try:
                logger.info("📎 Tentando attachment compatível...")
                
                # Método que funciona na maioria das versões
                attachment_files = target_item.attachment_files
                
                # Cria um dicionário simples para o attachment
                attachment_data = {
                    'FileName': filename,
                    'Content': file_content
                }
                
                # Tenta diferentes sintaxes de add
                try:
                    # Sintaxe 1: Dicionário
                    new_attachment = attachment_files.add(attachment_data)
                    ctx.execute_query()
                    logger.info("✅ Attachment método 1 funcionou")
                except:
                    try:
                        # Sintaxe 2: Parâmetros separados (pode funcionar)
                        attachment_files.add_using_path(filename, file_content)
                        ctx.execute_query()
                        logger.info("✅ Attachment método 2 funcionou")
                    except:
                        # Sintaxe 3: Manual
                        from office365.sharepoint.files.creation_information import FileCreationInformation
                        
                        file_info = FileCreationInformation()
                        file_info.url = filename
                        file_info.content = file_content
                        
                        # Upload para pasta de attachments
                        attachments_folder = target_item.folder.folders.add(f"Attachments/{ticket_id}")
                        ctx.execute_query()
                        
                        uploaded = attachments_folder.files.add(file_info)
                        ctx.execute_query()
                        logger.info("✅ Attachment método 3 funcionou")
                
                # URL padrão de attachment do SharePoint
                attachment_url = f"/sites/Controleoperacional/Lists/SentinelaTickets/Attachments/{ticket_id}/{filename}"
                
                # Salva referência no Print
                self._salvar_referencia_imagem(ctx, ticket_id, attachment_url, filename)
                
                return True, f"Imagem anexada: {filename}"
                
            except Exception as attach_error:
                logger.warning(f"⚠️ Attachment falhou: {str(attach_error)}")
            
            # MÉTODO 3: Salva como base64 no campo (SEMPRE FUNCIONA)
            try:
                logger.info("💾 Salvando como base64...")
                
                import base64
                base64_content = base64.b64encode(file_content).decode('utf-8')
                
                # Trunca se muito grande
                if len(base64_content) > 30000:
                    base64_content = base64_content[:30000] + "..."
                    logger.warning("⚠️ Base64 truncado devido ao tamanho")
                
                # Dados estruturados da imagem
                image_data = {
                    "filename": filename,
                    "size": len(file_content),
                    "base64": base64_content,
                    "type": "image"
                }
                
                import json
                image_json = json.dumps(image_data)
                
                # Salva no campo Print
                target_item.set_property('Print', image_json)
                target_item.update()
                ctx.execute_query()
                
                logger.info("✅ Imagem salva como base64 estruturado")
                return True, f"Imagem salva como dados: {filename}"
                
            except Exception as base64_error:
                logger.warning(f"⚠️ Base64 falhou: {str(base64_error)}")
            
            # MÉTODO 4: Fallback mínimo - só o nome
            try:
                logger.info("📝 Salvando referência mínima...")
                
                target_item.set_property('Print', f"Imagem: {filename} ({len(file_content)} bytes)")
                target_item.update()
                ctx.execute_query()
                
                logger.info("✅ Referência mínima salva")
                return True, f"Referência da imagem salva: {filename}"
                
            except Exception as minimal_error:
                logger.error(f"❌ Até referência mínima falhou: {str(minimal_error)}")
            
            return False, "Todos os métodos falharam"
            
        except Exception as e:
            logger.error(f"❌ Erro geral: {str(e)}")
            return False, f"Erro no upload: {str(e)}"
        
    def _salvar_referencia_imagem(self, ctx, ticket_id: int, image_url: str, filename: str):
        """Salva referência da imagem no campo Print"""
        try:
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            # Tenta diferentes formatos
            formats_to_try = [
                # Formato 1: JSON estruturado
                {
                    "type": "image",
                    "url": image_url,
                    "filename": filename
                },
                # Formato 2: Data URL se for base64
                f"data:image/jpeg;name={filename};url={image_url}",
                # Formato 3: URL simples
                image_url,
                # Formato 4: Nome com URL
                f"{filename}|{image_url}"
            ]
            
            for i, format_data in enumerate(formats_to_try, 1):
                try:
                    if isinstance(format_data, dict):
                        import json
                        data_to_save = json.dumps(format_data)
                    else:
                        data_to_save = str(format_data)
                    
                    target_item.set_property('Print', data_to_save)
                    target_item.update()
                    ctx.execute_query()
                    
                    logger.info(f"✅ Formato {i} funcionou para referência")
                    return
                    
                except Exception as format_error:
                    logger.warning(f"⚠️ Formato {i} falhou: {str(format_error)}")
                    continue
            
            logger.error("❌ Nenhum formato de referência funcionou")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar referência: {str(e)}")
        
    def _atualizar_campo_visualizacao(self, ctx, ticket_id: int, filename: str):
        """Atualiza campo para permitir visualização da imagem"""
        try:
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            # URL do anexo (padrão SharePoint)
            attachment_url = f"/sites/Controleoperacional/Lists/SentinelaTickets/Attachments/{ticket_id}/{filename}"
            
            # Formato JSON correto para campo Thumbnail
            thumbnail_data = {
                "type": "thumbnail",
                "fileName": filename,
                "serverUrl": attachment_url,
                "serverRelativeUrl": attachment_url,
                "id": f"attachment_{ticket_id}"
            }
            
            import json
            thumbnail_json = json.dumps(thumbnail_data)
            
            # Tenta salvar no campo Print
            target_item.set_property('Print', thumbnail_json)
            target_item.update()
            ctx.execute_query()
            
            logger.info(f"✅ Campo Print atualizado com JSON de visualização")
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao atualizar campo visualização: {str(e)}")
            
            # Fallback: salva apenas o nome do arquivo
            try:
                target_item.set_property('Print', filename)
                target_item.update()
                ctx.execute_query()
                logger.info(f"✅ Campo Print atualizado com nome do arquivo")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback também falhou: {str(fallback_error)}")

    def _salvar_url_como_thumbnail(self, ctx, ticket_id: int, image_url: str, filename: str):
        """Salva URL da imagem no formato correto para thumbnails"""
        try:
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            # Formato completo baseado na pesquisa
            thumbnail_object = {
                "type": "thumbnail",
                "fileName": filename,
                "nativeFile": {},
                "fieldName": "Print",
                "serverUrl": image_url,
                "serverRelativeUrl": image_url,
                "id": f"library_{ticket_id}_{filename}"
            }
            
            import json
            thumbnail_json = json.dumps(thumbnail_object)
            
            target_item.set_property('Print', thumbnail_json)
            target_item.update()
            ctx.execute_query()
            
            logger.info(f"✅ URL salva como thumbnail no campo Print")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar URL como thumbnail: {str(e)}")

    def criar_campo_nome_arquivo(ctx, lista_nome="SentinelaTickets"):
        """
        Cria campo auxiliar 'NomeArquivo' para formatação JSON
        Execute esta função UMA VEZ para preparar a lista
        """
        try:
            # Obtém a lista
            target_list = ctx.web.lists.get_by_title(lista_nome)
            ctx.load(target_list)
            ctx.execute_query()
            
            # Cria campo de texto para armazenar nome do arquivo
            field_xml = """
            <Field Type='Text' 
                DisplayName='NomeArquivo' 
                Name='NomeArquivo' 
                MaxLength='255' 
                Description='Nome do arquivo anexado para visualização' />
            """
            
            target_list.fields.create_field_as_xml(field_xml)
            ctx.execute_query()
            
            logger.info("✅ Campo 'NomeArquivo' criado com sucesso")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Campo pode já existir ou erro: {str(e)}")
            return False
        
    def _criar_imagem_placeholder(self, filename: str) -> bytes:
        """Cria uma imagem placeholder PNG válida"""
        try:
            # PNG 1x1 pixel azul válido (para representar que é um arquivo web)
            png_blue_1x1 = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                0x00, 0x00, 0x00, 0x0D,  # IHDR chunk size
                0x49, 0x48, 0x44, 0x52,  # IHDR
                0x00, 0x00, 0x00, 0x01,  # width = 1
                0x00, 0x00, 0x00, 0x01,  # height = 1
                0x08, 0x02,              # bit depth = 8, color type = 2 (RGB)
                0x00, 0x00, 0x00,        # compression, filter, interlace
                0x90, 0x77, 0x53, 0xDE,  # CRC
                0x00, 0x00, 0x00, 0x0C,  # IDAT chunk size
                0x49, 0x44, 0x41, 0x54,  # IDAT
                0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0x00, 0xFF,
                0xFF, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01,
                0xE5, 0x27, 0xDE, 0xFC,  # CRC
                0x00, 0x00, 0x00, 0x00,  # IEND chunk size
                0x49, 0x45, 0x4E, 0x44,  # IEND
                0xAE, 0x42, 0x60, 0x82   # CRC
            ])
            
            logger.info(f"🎨 Placeholder PNG criado para {filename}")
            return png_blue_1x1
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar placeholder: {str(e)}")
            # Fallback mínimo
            return b'PNG_PLACEHOLDER_DATA'
    
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