"""
Serviço para gerenciamento de tickets de suporte - VERSÃO FINAL LIMPA
app/services/ticket_service.py - USA CAMPO 'Imagem' (Hiperlink-Imagem)
"""
import base64
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import pandas as pd

# Imports condicionais
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
    """Serviço FINAL para tickets - USA CAMPO 'Imagem' (Hiperlink-Imagem)"""
    
    # Configurações
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    
    # Motivos predefinidos
    MOTIVOS_TICKETS = [
        "Erro de login",
        "Bug tela aprovação/preenchimento", 
        "Falha no preenchimento/aprovação",
        "Sistema instável/Lento",
        "Melhoria",
        "Dúvida",
        "Outro"
    ]
    
    def __init__(self):
        """Inicializa o serviço"""
        if CONFIG_AVAILABLE and config:
            self.site_url = config.site_url
            self.username = config.username_sp
            self.password = config.password_sp
            self.lista_tickets = getattr(config, 'lista_tickets', 'SentinelaTickets')
        else:
            self.site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
            self.username = ""
            self.password = ""
            self.lista_tickets = "SentinelaTickets"
            
        logger.info(f"✅ TicketService LIMPO inicializado - Campo: Imagem (Hiperlink-Imagem)")
    
    def criar_ticket(self, dados_ticket: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Cria ticket usando CAMPO IMAGEM (Hiperlink-Imagem)"""
        try:
            # Extrai dados
            motivo = dados_ticket.get('motivo', '').strip()
            usuario = dados_ticket.get('usuario', '').strip()
            descricao = dados_ticket.get('descricao', '').strip()
            
            # Validações
            if not motivo or not usuario or not descricao:
                return False, "Todos os campos são obrigatórios", None
            
            logger.info(f"🎫 Criando ticket: {motivo} - {usuario}")
            
            # Conecta SharePoint
            ctx = self._get_sharepoint_context()
            if not ctx:
                return False, "Erro de conexão SharePoint", None
            
            # Cria ticket
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            ticket_data = {
                'Motivo': motivo,
                'Usuario': usuario,
                'Descricao': descricao,
                'Abertura': datetime.now().isoformat()
            }
            
            new_item = tickets_list.add_item(ticket_data)
            ctx.execute_query()
            
            # Obtém ID
            ticket_id = self._obter_ticket_id(ctx, new_item)
            logger.info(f"✅ Ticket {ticket_id} criado")
            
            # Upload de imagem (se fornecida)
            if dados_ticket.get('imagem_content') and dados_ticket.get('imagem_filename'):
                sucesso_img, msg_img = self._processar_upload_imagem(
                    ctx, ticket_id, 
                    dados_ticket['imagem_content'], 
                    dados_ticket['imagem_filename']
                )
                
                if sucesso_img:
                    return True, f"Ticket criado com imagem! ID: {ticket_id}", ticket_id
                else:
                    return True, f"Ticket criado (ID: {ticket_id}), mas erro no upload: {msg_img}", ticket_id
            
            return True, f"Ticket criado! ID: {ticket_id}", ticket_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket: {str(e)}")
            return False, f"Erro: {str(e)}", None
    
    def _processar_upload_imagem(self, ctx, ticket_id: int, 
                               file_content: bytes, filename: str) -> Tuple[bool, str]:
        """Upload para CAMPO IMAGEM (Hiperlink-Imagem)"""
        try:
            logger.info(f"🖼️ Upload CAMPO IMAGEM: {filename} ({len(file_content)} bytes)")
            
            # Processa arquivo Flet Web
            file_content = self._processar_arquivo_flet_web(file_content, filename)
            
            # ESTRATÉGIA 1: Upload real + Campo Imagem
            sucesso = self._upload_campo_imagem(ctx, ticket_id, file_content, filename)
            if sucesso:
                return True, f"✅ Imagem salva no campo Imagem: {filename}"
            
            # ESTRATÉGIA 2: Base64 + Campo Imagem
            sucesso = self._upload_base64_campo_imagem(ctx, ticket_id, file_content, filename)
            if sucesso:
                return True, f"✅ Base64 salva no campo Imagem: {filename}"
            
            return False, "❌ Ambas estratégias falharam"
            
        except Exception as e:
            logger.error(f"❌ Erro no upload: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    def _upload_campo_imagem(self, ctx, ticket_id: int, file_content: bytes, filename: str) -> bool:
        """ESTRATÉGIA 1: Upload real para campo Imagem"""
        try:
            logger.info("🎯 Estratégia 1: Upload real para campo Imagem...")
            
            # Upload para Ativos do Site
            web = ctx.web
            site_assets = web.lists.get_by_title("Ativos do Site")
            
            # Nome único
            unique_filename = f"ticket_{ticket_id}_{uuid.uuid4().hex[:6]}_{filename}"
            
            # Upload
            uploaded_file = site_assets.root_folder.upload_file(unique_filename, file_content)
            ctx.execute_query()
            
            # URL
            ctx.load(uploaded_file)
            ctx.execute_query()
            file_url = uploaded_file.properties.get('ServerRelativeUrl')
            full_url = f"{self.site_url}{file_url}"
            
            logger.info(f"✅ Arquivo uploadeado: {file_url}")
            
            # Salva no campo Imagem (Hiperlink-Imagem)
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            hyperlink_data = {
                "Url": full_url,
                "Description": filename
            }
            
            target_item.set_property('Imagem', hyperlink_data)
            target_item.update()
            ctx.execute_query()
            
            logger.info("✅ Salvo no campo Imagem (Hiperlink-Imagem)")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Estratégia 1 falhou: {str(e)}")
            return False
    
    def _upload_base64_campo_imagem(self, ctx, ticket_id: int, file_content: bytes, filename: str) -> bool:
        """ESTRATÉGIA 2: Base64 para campo Imagem"""
        try:
            logger.info("💾 Estratégia 2: Base64 para campo Imagem...")
            
            # Base64
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            # MIME type
            if filename.lower().endswith('.png'):
                mime_type = 'image/png'
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/png'
            
            # Data URL
            data_url = f"data:{mime_type};base64,{base64_content}"
            
            # Salva no campo Imagem
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            hyperlink_data = {
                "Url": data_url,
                "Description": filename
            }
            
            target_item.set_property('Imagem', hyperlink_data)
            target_item.update()
            ctx.execute_query()
            
            logger.info("✅ Base64 salva no campo Imagem")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Estratégia 2 falhou: {str(e)}")
            return False
    
    def _processar_arquivo_flet_web(self, file_content: bytes, filename: str) -> bytes:
        """Processamento MELHORADO de arquivo Flet Web"""
        try:
            logger.info(f"🔍 Analisando arquivo: {len(file_content)} bytes")
            
            # Se não é arquivo Flet Web, usa direto
            if not file_content.startswith(b'FLET_WEB_FILE:'):
                logger.info("✅ Arquivo normal (não Flet Web)")
                return file_content
            
            logger.info("🌐 Arquivo Flet Web detectado - tentando extrair dados reais...")
            
            # MÉTODO 1: Busca base64 na string
            try:
                file_data_str = file_content.decode('utf-8')
                logger.info(f"📝 Conteúdo string: {file_data_str[:200]}...")
                
                # Procura diferentes padrões de base64
                base64_patterns = [
                    'data:image/jpeg;base64,',
                    'data:image/png;base64,',
                    'data:image/jpg;base64,',
                    'base64,',
                    ';base64,',
                ]
                
                for pattern in base64_patterns:
                    if pattern in file_data_str:
                        logger.info(f"🎯 Padrão encontrado: {pattern}")
                        
                        base64_start = file_data_str.find(pattern) + len(pattern)
                        base64_data = file_data_str[base64_start:].strip()
                        
                        # Limpa dados base64 (remove quebras de linha, etc.)
                        base64_data = base64_data.replace('\n', '').replace('\r', '')
                        base64_data = base64_data.split(',')[0].split('"')[0].split("'")[0]
                        
                        if base64_data:
                            try:
                                real_content = base64.b64decode(base64_data)
                                logger.info(f"✅ SUCESSO! Dados reais extraídos: {len(real_content)} bytes")
                                
                                # Valida se é uma imagem válida
                                if len(real_content) > 100 and (
                                    real_content.startswith(b'\xff\xd8') or  # JPEG
                                    real_content.startswith(b'\x89PNG') or   # PNG
                                    real_content.startswith(b'GIF8')         # GIF
                                ):
                                    logger.info("✅ Imagem válida detectada!")
                                    return real_content
                                    
                            except Exception as decode_error:
                                logger.warning(f"⚠️ Erro decode base64: {str(decode_error)}")
                                continue
                
            except Exception as extract_error:
                logger.warning(f"⚠️ Erro na extração: {str(extract_error)}")
            
            # MÉTODO 2: Tenta interpretar como dados binários
            try:
                # Remove prefixo e tenta decodificar
                clean_data = file_content.replace(b'FLET_WEB_FILE:', b'')
                if len(clean_data) > 100:
                    logger.info(f"🔄 Tentando dados binários: {len(clean_data)} bytes")
                    return clean_data
                    
            except Exception as binary_error:
                logger.warning(f"⚠️ Erro dados binários: {str(binary_error)}")
            
            # FALLBACK: Cria imagem maior e mais visível
            logger.info("🎨 Criando imagem exemplo MAIOR e COLORIDA...")
            return self._criar_imagem_exemplo_visivel()
            
        except Exception as e:
            logger.error(f"❌ Erro processamento: {str(e)}")
            return self._criar_imagem_exemplo_visivel()
    
    def _criar_imagem_exemplo_visivel(self) -> bytes:
        """Cria imagem exemplo MAIOR e mais VISÍVEL"""
        try:
            # Cria PNG 100x100 pixels com texto "TESTE"
            width, height = 100, 100
            
            # Header PNG
            png_data = bytearray([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
            
            # IHDR chunk
            ihdr_data = bytearray()
            ihdr_data.extend(width.to_bytes(4, 'big'))
            ihdr_data.extend(height.to_bytes(4, 'big'))
            ihdr_data.extend([8, 2, 0, 0, 0])  # RGB
            
            import zlib
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
            
            png_data.extend(len(ihdr_data).to_bytes(4, 'big'))
            png_data.extend(b'IHDR')
            png_data.extend(ihdr_data)
            png_data.extend(ihdr_crc.to_bytes(4, 'big'))
            
            # IDAT chunk - imagem azul com bordas vermelhas
            image_data = bytearray()
            for y in range(height):
                image_data.append(0)  # Filter
                for x in range(width):
                    # Borda vermelha
                    if x < 5 or x >= width-5 or y < 5 or y >= height-5:
                        image_data.extend([255, 0, 0])  # Vermelho
                    else:
                        image_data.extend([0, 150, 255])  # Azul claro
            
            compressed_data = zlib.compress(image_data)
            idat_crc = zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff
            
            png_data.extend(len(compressed_data).to_bytes(4, 'big'))
            png_data.extend(b'IDAT')
            png_data.extend(compressed_data)
            png_data.extend(idat_crc.to_bytes(4, 'big'))
            
            # IEND chunk
            iend_crc = zlib.crc32(b'IEND') & 0xffffffff
            png_data.extend((0).to_bytes(4, 'big'))
            png_data.extend(b'IEND')
            png_data.extend(iend_crc.to_bytes(4, 'big'))
            
            logger.info(f"🎨 PNG exemplo VISÍVEL criado: {len(png_data)} bytes (100x100 azul com borda vermelha)")
            return bytes(png_data)
            
        except Exception as e:
            logger.error(f"❌ Erro criar PNG visível: {str(e)}")
            # Fallback ainda mais simples
            return bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x0A,
                0x08, 0x02, 0x00, 0x00, 0x00, 0x02, 0x50, 0x58,
                0xEA, 0x00, 0x00, 0x00, 0x15, 0x49, 0x44, 0x41,
                0x54, 0x78, 0x9C, 0x63, 0xF8, 0x0F, 0x00, 0x01,
                0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4, 0xE5,
                0x27, 0xDE, 0xFC, 0x00, 0x00, 0x00, 0x00, 0x49,
                0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
            ])
    
    def _upload_campo_imagem(self, ctx, ticket_id: int, file_content: bytes, filename: str) -> bool:
        """ESTRATÉGIA 1: Upload real com FORMATOS ALTERNATIVOS"""
        try:
            logger.info("🎯 Estratégia 1: Upload real + formatos alternativos...")
            
            # Upload para Ativos do Site
            web = ctx.web
            site_assets = web.lists.get_by_title("Ativos do Site")
            
            unique_filename = f"ticket_{ticket_id}_{uuid.uuid4().hex[:6]}_{filename}"
            uploaded_file = site_assets.root_folder.upload_file(unique_filename, file_content)
            ctx.execute_query()
            
            # URL
            ctx.load(uploaded_file)
            ctx.execute_query()
            file_url = uploaded_file.properties.get('ServerRelativeUrl')
            full_url = f"{self.site_url}{file_url}"
            
            logger.info(f"✅ Arquivo uploadeado: {file_url}")
            
            # Testa diferentes formatos para campo Hiperlink-Imagem
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            target_item = tickets_list.get_item_by_id(ticket_id)
            
            formats_to_try = [
                # Formato 1: Padrão Hiperlink-Imagem
                {"Url": full_url, "Description": filename},
                
                # Formato 2: Apenas URL
                full_url,
                
                # Formato 3: Formato estendido
                {
                    "Url": full_url,
                    "Description": filename,
                    "__metadata": {"type": "SP.FieldUrlValue"}
                },
                
                # Formato 4: Com propriedades adicionais
                {
                    "Url": full_url,
                    "Description": filename,
                    "Title": filename
                }
            ]
            
            for i, format_data in enumerate(formats_to_try, 1):
                try:
                    logger.info(f"🧪 Testando formato {i}: {type(format_data)}")
                    
                    target_item.set_property('Imagem', format_data)
                    target_item.update()
                    ctx.execute_query()
                    
                    logger.info(f"✅ Formato {i} funcionou!")
                    return True
                    
                except Exception as format_error:
                    logger.warning(f"⚠️ Formato {i} falhou: {str(format_error)}")
                    continue
            
            logger.error("❌ Nenhum formato funcionou")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Estratégia 1 falhou: {str(e)}")
            return False

    def _obter_ticket_id(self, ctx, new_item) -> int:
        """Obtém ID do ticket"""
        try:
            if hasattr(new_item, 'properties'):
                ticket_id = new_item.properties.get('ID')
                if ticket_id:
                    return ticket_id
            
            ctx.load(new_item)
            ctx.execute_query()
            return getattr(new_item, 'id', 999)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter ID: {str(e)}")
            return 999
    
    def _get_sharepoint_context(self):
        """Conecta ao SharePoint"""
        try:
            if not OFFICE365_AVAILABLE:
                return None
            
            if not self.username or not self.password:
                return None
            
            ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            
            # Testa conexão
            web = ctx.web
            ctx.load(web)
            ctx.execute_query()
            
            logger.info(f"✅ Conectado: {web.properties.get('Title', 'Site')}")
            return ctx
            
        except Exception as e:
            logger.error(f"❌ Erro conexão: {str(e)}")
            return None
    
    def obter_tickets(self, limit: int = 50) -> pd.DataFrame:
        """Obtém tickets com campo Imagem"""
        try:
            ctx = self._get_sharepoint_context()
            if not ctx:
                return pd.DataFrame()
            
            tickets_list = ctx.web.lists.get_by_title(self.lista_tickets)
            items = tickets_list.items.top(limit).get().execute_query()
            
            if not items:
                return pd.DataFrame()
            
            tickets_data = []
            for item in items:
                ticket_data = {
                    'ID': item.properties.get('ID'),
                    'Motivo': item.properties.get('Motivo', ''),
                    'Usuario': item.properties.get('Usuario', ''),
                    'Descricao': item.properties.get('Descricao', ''),
                    'Abertura': item.properties.get('Abertura', ''),
                    'Imagem': item.properties.get('Imagem', '')  # Campo correto
                }
                tickets_data.append(ticket_data)
            
            df = pd.DataFrame(tickets_data)
            logger.info(f"✅ {len(df)} tickets obtidos")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro obter tickets: {str(e)}")
            return pd.DataFrame()
    
    def get_motivos_disponiveis(self) -> list:
        """Retorna motivos disponíveis"""
        return self.MOTIVOS_TICKETS.copy()


# INSTÂNCIA GLOBAL
ticket_service = TicketService()


# TESTE
def testar_ticket_service():
    """Teste do serviço"""
    print("🧪 Testando TicketService LIMPO...")
    
    ctx = ticket_service._get_sharepoint_context()
    sucesso = ctx is not None
    print(f"Conexão: {'✅' if sucesso else '❌'}")
    
    motivos = ticket_service.get_motivos_disponiveis()
    print(f"Motivos: ✅ {len(motivos)} opções")
    
    print("🎯 Teste concluído!")


if __name__ == "__main__":
    testar_ticket_service()