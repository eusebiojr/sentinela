"""
Serviço para mudança de senha - VERSÃO MIGRADA COM VALIDAÇÕES CENTRALIZADAS
Usa SecurityValidator internamente mas mantém API pública
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

# 🚀 NOVA IMPORTAÇÃO - Usa sistema centralizado
from ..validators import security_validator

logger = setup_logger("password_service")


class SuzanoPasswordService:
    """Serviço para gerenciamento de senhas - MIGRADO PARA VALIDAÇÕES CENTRALIZADAS"""
    
    def __init__(self):
        """Inicializa o serviço com configurações do sistema"""
        self.site_url = config.site_url
        self.lista_usuarios = config.usuarios_list
        self.username = config.username_sp
        self.password = config.password_sp
        self.ctx = None
        
        logger.info("🔐 SuzanoPasswordService inicializado (versão migrada)")
        
    def conectar_sharepoint(self) -> bool:
        """Estabelece conexão com SharePoint (mantido igual)"""
        try:
            if not UserCredential or not ClientContext:
                raise Exception("Biblioteca Office365 não instalada")
                
            logger.info("🔗 Conectando ao SharePoint...")
            
            self.ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            logger.info(f"✅ Conectado ao SharePoint: {web.properties.get('Title', 'N/A')}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SharePoint: {e}")
            return False
    
    def validar_politica_senha(self, senha: str) -> Tuple[bool, str]:
        """
        🚀 MIGRADO - Usa SecurityValidator centralizado
        Mantém API idêntica para compatibilidade
        """
        if not senha:
            return False, "Senha não pode estar vazia"
        
        # 🚀 USA VALIDADOR CENTRALIZADO - Substitui lógica manual antiga
        validation_result = security_validator.validate_password_policy(senha)
        
        if validation_result.valid:
            return True, "Senha válida"
        else:
            return False, validation_result.errors[0] if validation_result.errors else "Erro de validação"
    
    def buscar_usuario_por_email(self, email: str) -> Dict[str, Any]:
        """Busca usuário por email (mantido igual)"""
        try:
            if not self.ctx:
                if not self.conectar_sharepoint():
                    raise Exception("Não foi possível conectar ao SharePoint")
            
            logger.info(f"🔍 Buscando usuário: {email}")
            
            lista_usuarios = self.ctx.web.lists.get_by_title(self.lista_usuarios)
            email_normalizado = email.strip().lower()
            
            items = lista_usuarios.items.get_all()
            self.ctx.execute_query()
            
            for item in items:
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
        """Valida se a senha atual está correta (mantido igual)"""
        try:
            logger.info(f"🔐 Validando senha atual para: {email}")
            
            usuario = self.buscar_usuario_por_email(email)
            
            if not usuario:
                logger.warning(f"⚠️ Usuário não encontrado para validação: {email}")
                return False
            
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
        """
        🚀 MIGRADO - Usa SecurityValidator para validação de política
        Mantém API idêntica mas validação interna melhorada
        """
        try:
            logger.info(f"🔐 Iniciando alteração de senha para: {email}")
            
            # 🚀 USA VALIDADOR CENTRALIZADO - Substitui validação manual antiga
            validation_result = security_validator.validate_password_policy(nova_senha)
            
            if not validation_result.valid:
                logger.warning(f"⚠️ Política de senha não atendida: {validation_result.errors[0]}")
                return {
                    'sucesso': False,
                    'erro': f"Política de senha: {validation_result.errors[0]}"
                }
            
            # Log adicional sobre força da senha
            strength_level = validation_result.data.get('strength_level', 'Desconhecida')
            logger.info(f"📊 Força da nova senha: {strength_level}")
            
            if not self.ctx:
                if not self.conectar_sharepoint():
                    return {
                        'sucesso': False,
                        'erro': "Erro de conexão com SharePoint"
                    }
            
            usuario = self.buscar_usuario_por_email(email)
            if not usuario:
                logger.error(f"❌ Usuário não encontrado: {email}")
                return {
                    'sucesso': False,
                    'erro': "Usuário não encontrado"
                }
            
            if not self.validar_senha_atual(email, senha_atual):
                logger.warning(f"⚠️ Tentativa de alteração com senha incorreta: {email}")
                return {
                    'sucesso': False,
                    'erro': "Senha atual incorreta"
                }
            
            try:
                lista_usuarios = self.ctx.web.lists.get_by_title(self.lista_usuarios)
                item = lista_usuarios.get_item_by_id(usuario['ID'])
                
                item.set_property('Senha', nova_senha)
                item.update()
                self.ctx.execute_query()
                
                logger.info(f"✅ Senha alterada com sucesso no SharePoint: {email}")
                self._log_alteracao_senha(email, usuario['ID'], strength_level)
                
                return {
                    'sucesso': True,
                    'mensagem': 'Senha alterada com sucesso',
                    'usuario_id': usuario['ID'],
                    'forca_senha': strength_level  # 🚀 NOVO: Retorna força da senha
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
    
    def _log_alteracao_senha(self, email: str, usuario_id: int, forca_senha: str = ""):
        """🚀 MELHORADO - Log de auditoria com informação de força da senha"""
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            logger.info(f"📋 AUDITORIA - Senha alterada | Usuário: {email} | ID: {usuario_id} | "
                       f"Força: {forca_senha} | Timestamp: {timestamp}")
        except Exception:
            pass
    
    def obter_dados_usuario(self, email: str) -> Dict[str, Any]:
        """Obtém dados completos do usuário (mantido igual)"""
        try:
            usuario = self.buscar_usuario_por_email(email)
            
            if usuario:
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
        """Testa conectividade básica (mantido igual)"""
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
    
    # 🚀 NOVOS MÉTODOS - Aproveitam sistema centralizado
    
    def avaliar_forca_senha(self, senha: str) -> Dict[str, Any]:
        """
        NOVO - Avalia força da senha sem validar política
        
        Args:
            senha: Senha a ser avaliada
            
        Returns:
            Dict com análise detalhada da força
        """
        validation_result = security_validator.validate_password_policy(senha)
        
        return {
            'forca_numerica': validation_result.data.get('strength_score', 0),
            'nivel_forca': validation_result.data.get('strength_level', 'Desconhecida'),
            'tem_letra': validation_result.data.get('has_letter', False),
            'tem_numero': validation_result.data.get('has_number', False),
            'tem_especial': validation_result.data.get('has_special', False),
            'comprimento': validation_result.data.get('password_length', 0),
            'recomendacoes': self._gerar_recomendacoes_senha(validation_result)
        }
    
    def _gerar_recomendacoes_senha(self, validation_result) -> list:
        """Gera recomendações para melhorar a senha"""
        recomendacoes = []
        
        if validation_result.data.get('password_length', 0) < 8:
            recomendacoes.append("Use pelo menos 8 caracteres para maior segurança")
        
        if not validation_result.data.get('has_letter', False):
            recomendacoes.append("Adicione pelo menos uma letra")
        
        if not validation_result.data.get('has_number', False):
            recomendacoes.append("Adicione pelo menos um número")
        
        if not validation_result.data.get('has_special', False):
            recomendacoes.append("Considere adicionar caracteres especiais (!@#$%)")
        
        strength_score = validation_result.data.get('strength_score', 0)
        if strength_score < 60:
            recomendacoes.append("Combine letras maiúsculas, minúsculas, números e símbolos")
        
        return recomendacoes
    
    def validar_troca_senha_completa(self, email: str, senha_atual: str, 
                                   nova_senha: str, confirmar_senha: str) -> Dict[str, Any]:
        """
        NOVO - Validação completa de troca de senha usando sistema centralizado
        
        Args:
            email: Email do usuário
            senha_atual: Senha atual
            nova_senha: Nova senha
            confirmar_senha: Confirmação da nova senha
            
        Returns:
            Dict com resultado completo da validação
        """
        # 🚀 USA VALIDADOR CENTRALIZADO PARA TROCA COMPLETA
        validation_result = security_validator.validate_password_change(
            senha_atual, nova_senha, confirmar_senha
        )
        
        resultado = {
            'validacao_ok': validation_result.valid,
            'erros': validation_result.errors,
            'avisos': validation_result.warnings,
            'pode_alterar': validation_result.valid
        }
        
        # Adiciona informações específicas do usuário
        if validation_result.valid:
            try:
                usuario = self.buscar_usuario_por_email(email)
                if usuario:
                    resultado['usuario_encontrado'] = True
                    resultado['usuario_id'] = usuario.get('ID')
                else:
                    resultado['validacao_ok'] = False
                    resultado['erros'].append("Usuário não encontrado no sistema")
            except Exception as e:
                resultado['validacao_ok'] = False
                resultado['erros'].append(f"Erro ao verificar usuário: {str(e)}")
        
        return resultado


# Instância global do serviço
suzano_password_service = SuzanoPasswordService()

# 🚀 FUNÇÕES DE CONVENIÊNCIA - Simplificam o uso

def validar_senha_suzano(senha: str) -> Tuple[bool, str]:
    """Função rápida para validar senha conforme política Suzano"""
    return suzano_password_service.validar_politica_senha(senha)

def avaliar_forca_senha_rapido(senha: str) -> str:
    """Retorna apenas o nível de força da senha"""
    avaliacao = suzano_password_service.avaliar_forca_senha(senha)
    return avaliacao['nivel_forca']

def alterar_senha_usuario_completo(email: str, senha_atual: str, nova_senha: str, 
                                 confirmar_senha: str) -> Dict[str, Any]:
    """Função completa para alteração de senha com todas as validações"""
    # Primeiro valida tudo
    validacao = suzano_password_service.validar_troca_senha_completa(
        email, senha_atual, nova_senha, confirmar_senha
    )
    
    if not validacao['validacao_ok']:
        return {
            'sucesso': False,
            'erro': validacao['erros'][0] if validacao['erros'] else 'Erro na validação',
            'detalhes': validacao
        }
    
    # Se validação passou, executa a alteração
    return suzano_password_service.alterar_senha(email, senha_atual, nova_senha)

# 🧹 LIMPEZA - Funções antigas removidas e substituídas por sistema centralizado

print("🚀 SuzanoPasswordService migrado para sistema centralizado!")
print("✅ Mantém 100% de compatibilidade com código existente") 
print("🔧 Agora usa SecurityValidator internamente")
print("🎯 Novas funcionalidades: avaliação de força e validação completa")