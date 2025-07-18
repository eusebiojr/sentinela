"""
Serviço para mudança de senha - Suzano SharePoint - VERSÃO FINAL LIMPA
Substitui o arquivo app/services/suzano_password_service.py
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

try:
    from office365.runtime.auth.user_credential import UserCredential
    from office365.sharepoint.client_context import ClientContext
    from office365.sharepoint.lists.list import List
except ImportError:
    UserCredential = None
    ClientContext = None
    List = None

from ..config.settings import config
from ..config.logging_config import setup_logger

# Setup do logger
logger = setup_logger("password_service")


class SuzanoPasswordService:
    """Serviço para gerenciamento de senhas no SharePoint Suzano - VERSÃO FINAL"""
    
    def __init__(self):
        """Inicializa o serviço com configurações do sistema"""
        self.site_url = config.site_url
        self.lista_usuarios = config.usuarios_list
        self.username = config.username_sp
        self.password = config.password_sp
        self.ctx = None
        
        logger.info("🔐 SuzanoPasswordService inicializado")
        
    def conectar_sharepoint(self) -> bool:
        """Estabelece conexão com SharePoint usando credenciais do sistema"""
        try:
            if not UserCredential or not ClientContext:
                raise Exception("Biblioteca Office365 não instalada")
                
            logger.info("🔗 Conectando ao SharePoint...")
            
            # Usa as credenciais do sistema já configuradas
            self.ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            
            # Teste de conexão
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            logger.info(f"✅ Conectado ao SharePoint: {web.properties.get('Title', 'N/A')}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SharePoint: {e}")
            return False
    
    def validar_politica_senha(self, senha: str) -> Tuple[bool, str]:
        """Valida política de senhas (conforme configuração Suzano)"""
        if not senha:
            return False, "Senha não pode estar vazia"
            
        if len(senha) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
        
        if len(senha) > 50:
            return False, "Senha não pode ter mais de 50 caracteres"
        
        return True, "Senha válida"
    
    def buscar_usuario_por_email(self, email: str) -> Dict[str, Any]:
        """Busca usuário por email na lista UsuariosPainelTorre"""
        try:
            if not self.ctx:
                if not self.conectar_sharepoint():
                    raise Exception("Não foi possível conectar ao SharePoint")
            
            logger.info(f"🔍 Buscando usuário: {email}")
            
            # Buscar na lista UsuariosPainelTorre
            lista_usuarios = self.ctx.web.lists.get_by_title(self.lista_usuarios)
            
            # Normaliza email para busca
            email_normalizado = email.strip().lower()
            
            # Carrega todos os itens
            items = lista_usuarios.items.get_all()
            self.ctx.execute_query()
            
            # Busca manual com múltiplos campos
            for item in items:
                # Testa diferentes campos que podem conter email
                campos_email = ['Email', 'email', 'EMAIL', 'UserName', 'User', 'Login']
                
                for campo in campos_email:
                    email_item = item.properties.get(campo, '')
                    if email_item:
                        email_item_normalizado = str(email_item).strip().lower()
                        if email_item_normalizado == email_normalizado:
                            logger.info(f"✅ Usuário encontrado: ID {item.properties.get('ID')}")
                            return {
                                'ID': item.properties.get('ID'),
                                'Email': item.properties.get('Email', ''),
                                'Senha': item.properties.get('Senha', ''),
                                'NomeExibicao': item.properties.get('NomeExibicao', ''),
                                'Perfil': item.properties.get('Perfil', ''),
                                'Area': item.properties.get('Area', ''),
                                '_item_ref': item
                            }
            
            logger.warning(f"⚠️ Usuário não encontrado: {email}")
            return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuário: {e}")
            raise e
    
    def validar_senha_atual(self, email: str, senha_atual: str) -> bool:
        """Valida se a senha atual está correta"""
        try:
            logger.info(f"🔐 Validando senha atual para: {email}")
            
            usuario = self.buscar_usuario_por_email(email)
            
            if not usuario:
                logger.warning(f"⚠️ Usuário não encontrado para validação: {email}")
                return False
            
            # Comparação direta da senha (texto plano conforme estrutura Suzano)
            senha_armazenada = str(usuario.get('Senha', '')).strip()
            senha_informada = str(senha_atual).strip()
            
            is_valid = senha_informada == senha_armazenada
            
            if is_valid:
                logger.info(f"✅ Senha atual validada para: {email}")
            else:
                logger.warning(f"⚠️ Senha atual incorreta para: {email}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar senha: {e}")
            return False
    
    def alterar_senha(self, email: str, senha_atual: str, nova_senha: str) -> Dict[str, Any]:
        """Altera senha do usuário no SharePoint Suzano - FUNCIONAL"""
        try:
            logger.info(f"🔐 Iniciando alteração de senha para: {email}")
            
            # 1. Validar nova senha
            valida, mensagem = self.validar_politica_senha(nova_senha)
            if not valida:
                logger.warning(f"⚠️ Política de senha não atendida: {mensagem}")
                return {
                    'sucesso': False,
                    'erro': f"Política de senha: {mensagem}"
                }
            
            # 2. Conectar ao SharePoint se necessário
            if not self.ctx:
                if not self.conectar_sharepoint():
                    return {
                        'sucesso': False,
                        'erro': "Erro de conexão com SharePoint"
                    }
            
            # 3. Buscar usuário
            usuario = self.buscar_usuario_por_email(email)
            if not usuario:
                logger.error(f"❌ Usuário não encontrado: {email}")
                return {
                    'sucesso': False,
                    'erro': "Usuário não encontrado"
                }
            
            # 4. Verificar senha atual
            if not self.validar_senha_atual(email, senha_atual):
                logger.warning(f"⚠️ Tentativa de alteração com senha incorreta: {email}")
                return {
                    'sucesso': False,
                    'erro': "Senha atual incorreta"
                }
            
            # 5. Atualizar senha no SharePoint
            try:
                lista_usuarios = self.ctx.web.lists.get_by_title(self.lista_usuarios)
                item = lista_usuarios.get_item_by_id(usuario['ID'])
                
                # Atualiza a senha
                item.set_property('Senha', nova_senha)
                item.update()
                self.ctx.execute_query()
                
                logger.info(f"✅ Senha alterada com sucesso no SharePoint: {email}")
                
                # Log de auditoria
                self._log_alteracao_senha(email, usuario['ID'])
                
                return {
                    'sucesso': True,
                    'mensagem': 'Senha alterada com sucesso',
                    'usuario_id': usuario['ID']
                }
                
            except Exception as sp_error:
                logger.error(f"❌ Erro específico do SharePoint: {sp_error}")
                return {
                    'sucesso': False,
                    'erro': f"Erro ao atualizar no SharePoint: {str(sp_error)}"
                }
            
        except Exception as e:
            logger.error(f"❌ Erro geral ao alterar senha: {e}")
            return {
                'sucesso': False,
                'erro': f"Erro interno: {str(e)}"
            }
    
    def _log_alteracao_senha(self, email: str, usuario_id: int):
        """Registra log de auditoria para alteração de senha"""
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            logger.info(f"📋 AUDITORIA - Senha alterada | Usuário: {email} | ID: {usuario_id} | Timestamp: {timestamp}")
        except Exception:
            pass  # Log de auditoria não deve quebrar o fluxo principal
    
    def obter_dados_usuario(self, email: str) -> Dict[str, Any]:
        """Obtém dados completos do usuário"""
        try:
            usuario = self.buscar_usuario_por_email(email)
            
            if usuario:
                # Remove referência interna antes de retornar
                dados = usuario.copy()
                if '_item_ref' in dados:
                    del dados['_item_ref']
                return dados
            else:
                raise Exception("Usuário não encontrado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados do usuário: {e}")
            raise e
    
    def testar_conexao(self) -> bool:
        """Testa conectividade básica com SharePoint"""
        try:
            if self.conectar_sharepoint():
                logger.info("✅ Teste de conexão SharePoint passou")
                return True
            else:
                logger.error("❌ Teste de conexão SharePoint falhou")
                return False
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão: {e}")
            return False


# Instância global do serviço
suzano_password_service = SuzanoPasswordService()


def inicializar_servico_senha():
    """Função utilitária para inicializar o serviço de senha"""
    try:
        logger.info("🚀 Inicializando serviço de senha...")
        if suzano_password_service.testar_conexao():
            logger.info("✅ Serviço de senha pronto para uso")
            return True
        else:
            logger.warning("⚠️ Serviço de senha com problemas de conectividade")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar serviço de senha: {e}")
        return False


def alterar_senha_usuario(email: str, senha_atual: str, nova_senha: str) -> Dict[str, Any]:
    """Wrapper function para facilitar o uso do serviço"""
    return suzano_password_service.alterar_senha(email, senha_atual, nova_senha)