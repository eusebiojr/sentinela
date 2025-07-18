"""
Serviço para mudança de senha - Suzano SharePoint
Adaptado para estrutura existente: email, Senha, NomeExibicao, Perfil, Area
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

try:
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.client_context import ClientContext
    from office365.sharepoint.lists.list import List
except ImportError:
    AuthenticationContext = None
    ClientContext = None
    List = None

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SuzanoPasswordService:
    """Serviço para gerenciamento de senhas no SharePoint Suzano"""
    
    def __init__(self):
        """Inicializa o serviço com configurações Suzano"""
        self.site_url = 'https://suzano.sharepoint.com/sites/Controleoperacional'
        self.lista_usuarios = 'UsuariosPainelTorre'
        self.ctx = None
        
    def conectar_sharepoint(self, username: str, password: str) -> bool:
        """
        Estabelece conexão com SharePoint Suzano
        
        Args:
            username: Usuário para autenticação
            password: Senha para autenticação
            
        Returns:
            bool: True se conectou com sucesso
        """
        try:
            if not AuthenticationContext:
                raise Exception("Biblioteca Office365 não instalada")
                
            # Autenticação
            auth_ctx = AuthenticationContext(self.site_url)
            if auth_ctx.acquire_token_for_user(username, password):
                # Contexto do cliente
                self.ctx = ClientContext(self.site_url, auth_ctx)
                
                # Teste de conexão
                web = self.ctx.web
                self.ctx.load(web)
                self.ctx.execute_query()
                
                logger.info(f"✅ Conectado ao SharePoint Suzano: {web.properties.get('Title', 'N/A')}")
                return True
            else:
                logger.error("❌ Falha na autenticação SharePoint")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SharePoint: {e}")
            return False
    
    def validar_politica_senha(self, senha: str) -> Tuple[bool, str]:
        """
        Valida política de senhas (simplificada conforme solicitado)
        
        Args:
            senha: Senha a ser validada
            
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
        if len(senha) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
        
        if len(senha) > 50:
            return False, "Senha não pode ter mais de 50 caracteres"
        
        return True, "Senha válida"
    
    def buscar_usuario_por_email(self, email: str) -> Dict[str, Any]:
        """
        Busca usuário por email na lista UsuariosPainelTorre
        
        Args:
            email: Email do usuário
            
        Returns:
            Dict com dados do usuário ou None se não encontrado
        """
        try:
            if not self.ctx:
                raise Exception("Conexão SharePoint não estabelecida")
            
            # Buscar na lista UsuariosPainelTorre
            lista_usuarios = self.ctx.web.lists.get_by_title(self.lista_usuarios)
            
            # Query para buscar por email
            items = lista_usuarios.items.filter(f"Email eq '{email}'")
            self.ctx.load(items)
            self.ctx.execute_query()
            
            if len(items) > 0:
                usuario = items[0]
                return {
                    'ID': usuario.properties.get('ID'),
                    'Email': usuario.properties.get('Email', ''),
                    'Senha': usuario.properties.get('Senha', ''),
                    'NomeExibicao': usuario.properties.get('NomeExibicao', ''),
                    'Perfil': usuario.properties.get('Perfil', ''),
                    'Area': usuario.properties.get('Area', ''),
                    '_item': usuario  # Referência para atualização
                }
            else:
                logger.warning(f"⚠️ Usuário não encontrado: {email}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuário: {e}")
            raise e
    
    def validar_senha_atual(self, email: str, senha_atual: str) -> bool:
        """
        Valida se a senha atual está correta
        
        Args:
            email: Email do usuário
            senha_atual: Senha atual informada
            
        Returns:
            bool: True se senha está correta
        """
        try:
            usuario = self.buscar_usuario_por_email(email)
            
            if not usuario:
                return False
            
            # Comparação direta da senha (texto plano)
            senha_armazenada = usuario.get('Senha', '')
            return senha_atual == senha_armazenada
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar senha: {e}")
            return False
    
    def alterar_senha(self, email: str, senha_atual: str, nova_senha: str) -> Dict[str, Any]:
        """
        Altera senha do usuário no SharePoint Suzano
        
        Args:
            email: Email do usuário
            senha_atual: Senha atual do usuário
            nova_senha: Nova senha
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info(f"🔐 Iniciando alteração de senha para: {email}")
            
            # 1. Validar nova senha
            valida, mensagem = self.validar_politica_senha(nova_senha)
            if not valida:
                return {
                    'sucesso': False,
                    'erro': f"Política de senha: {mensagem}"
                }
            
            # 2. Buscar usuário
            usuario = self.buscar_usuario_por_email(email)
            if not usuario:
                return {
                    'sucesso': False,
                    'erro': "Usuário não encontrado"
                }
            
            # 3. Verificar senha atual
            if not self.validar_senha_atual(email, senha_atual):
                logger.warning(f"⚠️ Tentativa de alteração com senha incorreta: {email}")
                return {
                    'sucesso': False,
                    'erro': "Senha atual incorreta"
                }
            
            # 4. Atualizar senha no SharePoint
            usuario_item = usuario['_item']
            usuario_item.set_property('Senha', nova_senha)
            usuario_item.update()
            self.ctx.execute_query()
            
            logger.info(f"✅ Senha alterada com sucesso: {email}")
            
            return {
                'sucesso': True,
                'mensagem': 'Senha alterada com sucesso'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao alterar senha: {e}")
            return {
                'sucesso': False,
                'erro': f"Erro interno: {str(e)}"
            }
    
    def obter_dados_usuario(self, email: str) -> Dict[str, Any]:
        """
        Obtém dados completos do usuário
        
        Args:
            email: Email do usuário
            
        Returns:
            Dict com dados do usuário
        """
        try:
            usuario = self.buscar_usuario_por_email(email)
            
            if usuario:
                # Remover referência interna antes de retornar
                dados = usuario.copy()
                if '_item' in dados:
                    del dados['_item']
                return dados
            else:
                raise Exception("Usuário não encontrado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados do usuário: {e}")
            raise e


# Instância global do serviço
suzano_password_service = SuzanoPasswordService()