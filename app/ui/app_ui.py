"""
Orquestrador principal da interface do usuário
"""
import flet as ft
import threading
from ..core.state import app_state
from ..services.sharepoint_client import SharePointClient
from ..utils.data_utils import DataUtils
from ..utils.ui_utils import mostrar_mensagem, get_screen_size
from ..config.logging_config import setup_logger
from .screens.login import LoginScreen
from .screens.dashboard import DashboardScreen
from typing import Dict, Any, Optional
from ..config.logging_config import setup_logger

logger = setup_logger()


class SentinelaApp:
    """Classe principal que orquestra toda a aplicação"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.login_screen = LoginScreen(page, self)
        self.dashboard_screen = DashboardScreen(page, self)
        
    def inicializar(self):
        """Inicializa a aplicação"""
        logger.info("🚀 Sentinela iniciando...")
        
        # Mostra tela de carregamento inicial
        self._mostrar_carregamento_inicial()
        
        # Carrega dados em background
        self._carregar_dados_iniciais()
    
    def _mostrar_carregamento_inicial(self):
        """Exibe tela de carregamento inicial"""
        loading_inicial = ft.Container(
            content=ft.Column([
                ft.ProgressRing(),
                ft.Text("Inicializando sistema...", size=16)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
        
        self.page.clean()
        self.page.add(loading_inicial)
        self.page.update()
    
    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais para validação de login"""
        def carregar():
            try:
                logger.info("Carregando dados de usuários...")
                app_state.df_usuarios = SharePointClient.carregar_lista("UsuariosPainelTorre")
                
                if not app_state.df_usuarios.empty:
                    logger.info(f"✅ {len(app_state.df_usuarios)} usuários carregados")
                    self.login_screen.mostrar()
                else:
                    logger.warning("⚠️ Nenhum usuário encontrado")
                    self._mostrar_erro_inicial("Nenhum usuário encontrado na base de dados")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao carregar dados iniciais: {str(e)}")
                self._mostrar_erro_inicial(f"Erro ao conectar com SharePoint: {str(e)}")
        
        # Executa em thread separada
        thread = threading.Thread(target=carregar, daemon=True)
        thread.start()
    
    def _mostrar_erro_inicial(self, mensagem: str):
        """Exibe tela de erro inicial"""
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            icon_size = 60
            title_size = 16
            subtitle_size = 12
            button_width = 200
        elif screen_size == "medium":
            icon_size = 70
            title_size = 18
            subtitle_size = 13
            button_width = 250
        else:
            icon_size = 80
            title_size = 20
            subtitle_size = 14
            button_width = 300
        
        erro_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ERROR, size=icon_size, color=ft.colors.RED_600),
                ft.Text("Erro ao inicializar sistema", size=title_size, weight=ft.FontWeight.BOLD),
                ft.Text(mensagem, size=subtitle_size, color=ft.colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Tentar Novamente",
                    on_click=lambda e: self._carregar_dados_iniciais(),
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE,
                    width=button_width
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_50
        )
        
        self.page.clean()
        self.page.add(erro_container)
        self.page.update()
    
    def fazer_login(self, email: str, senha: str) -> bool:
        """Processa login do usuário"""
        try:
            # Valida credenciais
            sucesso, user_data = self._validar_login(email, senha)
            
            if not sucesso:
                return False
            
            # Armazena usuário no estado
            app_state.usuario = user_data
            
            # Mostra tela de carregamento pós-login
            self._mostrar_carregamento_pos_login()
            
            # Carrega dados completos em background
            self._carregar_dados_completos()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no login: {str(e)}")
            return False
    
    def _validar_login(self, email: str, senha: str) -> tuple:
        """Valida credenciais do usuário"""
        if app_state.df_usuarios.empty:
            return False, None
        
        # Busca coluna de email
        email_columns = [col for col in app_state.df_usuarios.columns if 'email' in col.lower()]
        if not email_columns:
            return False, None
        
        email_col = email_columns[0]
        
        # Busca usuário
        email_normalizado = email.strip().lower()
        df_temp = app_state.df_usuarios.copy()
        df_temp['email_normalizado'] = df_temp[email_col].astype(str).str.strip().str.lower()
        
        usuario_df = df_temp[df_temp['email_normalizado'] == email_normalizado]
        
        if not usuario_df.empty:
            user_data = usuario_df.iloc[0]
            
            # Busca coluna de senha
            senha_columns = [col for col in user_data.index if any(palavra in col.lower() for palavra in ['senha', 'password', 'pass'])]
            
            if senha_columns:
                senha_col = senha_columns[0]
                senha_bd = str(user_data[senha_col]).strip()
                
                if str(senha).strip() == senha_bd:
                    return True, user_data.to_dict()
        
        return False, None
    
    def _mostrar_carregamento_pos_login(self):
        """Mostra tela de carregamento após login"""
        nome_usuario = app_state.get_nome_usuario()
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            circulo_size = 180
            logo_size = 160
            welcome_size = 18
            loading_size = 14
            subtitle_size = 12
        elif screen_size == "medium":
            circulo_size = 240
            logo_size = 220
            welcome_size = 20
            loading_size = 15
            subtitle_size = 13
        else:
            circulo_size = 300
            logo_size = 280
            welcome_size = 24
            loading_size = 16
            subtitle_size = 14
        
        loading_container = ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            content=ft.Image(
                                src="images/circulo.png",
                                width=circulo_size,
                                height=circulo_size,
                                fit=ft.ImageFit.CONTAIN
                            ),
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            content=ft.Image(
                                src="images/sentinela.png",
                                width=logo_size,
                                height=logo_size,
                                fit=ft.ImageFit.CONTAIN
                            ),
                            alignment=ft.alignment.center
                        )
                    ]),
                    height=circulo_size,
                    alignment=ft.alignment.center
                ),
                ft.Container(height=30),
                ft.Column([
                    ft.Text(
                        f"Bem-vindo, {nome_usuario}!",
                        size=welcome_size,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_800,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Carregando seu painel...",
                        size=loading_size,
                        color=ft.colors.BLUE_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Aguarde alguns instantes",
                        size=subtitle_size,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(expand=True)
            ]),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.WHITE,
            expand=True
        )
        
        self.page.clean()
        self.page.add(loading_container)
        self.page.update()
    
    def _carregar_dados_completos(self):
        """Carrega todos os dados da aplicação"""
        def carregar():
            try:
                logger.info("Carregando dados completos...")
                
                # Carrega desvios
                app_state.df_desvios = SharePointClient.carregar_lista("Desvios")
                
                # Processa dados
                app_state.df_desvios = DataUtils.processar_desvios(app_state.df_desvios)
                
                # Marca como carregado
                app_state.dados_carregados = True
                
                logger.info(f"✅ Dados carregados: {len(app_state.df_desvios)} desvios")
                
                # Mostra dashboard
                self.dashboard_screen.mostrar()
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar dados: {str(e)}")
                self._mostrar_erro_dados()
        
        # Executa em thread separada
        thread = threading.Thread(target=carregar, daemon=True)
        thread.start()
    
    def _mostrar_erro_dados(self):
        """Mostra erro ao carregar dados"""
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            icon_size = 60
            title_size = 16
            subtitle_size = 12
            button_width = 200
        elif screen_size == "medium":
            icon_size = 70
            title_size = 18
            subtitle_size = 13
            button_width = 250
        else:
            icon_size = 80
            title_size = 20
            subtitle_size = 14
            button_width = 300
        
        erro_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ERROR, size=icon_size, color=ft.colors.RED_600),
                ft.Text("Erro ao carregar dados", size=title_size, weight=ft.FontWeight.BOLD),
                ft.Text("Verifique sua conexão com a internet", size=subtitle_size, color=ft.colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Tentar Novamente",
                    on_click=lambda e: self._carregar_dados_completos(),
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE,
                    width=button_width
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_50
        )
        
        self.page.clean()
        self.page.add(erro_container)
        self.page.update()
    
    def atualizar_dados(self):
        """Atualiza dados da aplicação"""
        mostrar_mensagem(self.page, "🔄 Atualizando dados...", False)
        self._carregar_dados_completos()

try:
    from ..services.suzano_password_service import suzano_password_service
    PASSWORD_SERVICE_AVAILABLE = True
except ImportError:
    PASSWORD_SERVICE_AVAILABLE = False
    suzano_password_service = None


class PasswordManager:
    """Gerenciador simplificado para operações de senha"""
    
    @staticmethod
    def is_service_available() -> bool:
        """
        Verifica se o serviço de senha está disponível
        
        Returns:
            bool: True se serviço está disponível
        """
        return PASSWORD_SERVICE_AVAILABLE and suzano_password_service is not None
    
    @staticmethod
    def validate_password_policy(password: str) -> Dict[str, Any]:
        """
        Valida política de senha
        
        Args:
            password: Senha a ser validada
            
        Returns:
            Dict com resultado da validação
        """
        if not PasswordManager.is_service_available():
            return {
                'valid': False,
                'error': 'Serviço de senha não disponível'
            }
        
        try:
            is_valid, message = suzano_password_service.validar_politica_senha(password)
            return {
                'valid': is_valid,
                'message': message,
                'error': None if is_valid else message
            }
        except Exception as e:
            logger.error(f"❌ Erro ao validar política de senha: {e}")
            return {
                'valid': False,
                'error': f'Erro na validação: {str(e)}'
            }
    
    @staticmethod
    def change_user_password(email: str, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Altera senha do usuário
        
        Args:
            email: Email do usuário
            current_password: Senha atual
            new_password: Nova senha
            
        Returns:
            Dict com resultado da operação
        """
        if not PasswordManager.is_service_available():
            return {
                'success': False,
                'error': 'Serviço de senha não disponível',
                'user_message': 'Funcionalidade de troca de senha temporariamente indisponível'
            }
        
        try:
            logger.info(f"🔐 Iniciando troca de senha para: {email}")
            
            resultado = suzano_password_service.alterar_senha(
                email=email,
                senha_atual=current_password,
                nova_senha=new_password
            )
            
            if resultado.get('sucesso', False):
                logger.info(f"✅ Senha alterada com sucesso para: {email}")
                return {
                    'success': True,
                    'message': resultado.get('mensagem', 'Senha alterada com sucesso'),
                    'user_message': '🔐 Sua senha foi alterada com sucesso!',
                    'user_id': resultado.get('usuario_id')
                }
            else:
                error_msg = resultado.get('erro', 'Erro desconhecido')
                logger.warning(f"⚠️ Falha na troca de senha para {email}: {error_msg}")
                
                # Mapeia erros para mensagens mais amigáveis
                user_friendly_errors = {
                    'senha atual incorreta': 'A senha atual informada está incorreta',
                    'usuário não encontrado': 'Usuário não encontrado no sistema',
                    'política de senha': 'A nova senha não atende aos requisitos de segurança',
                    'conexão': 'Erro de conexão com o servidor. Tente novamente.'
                }
                
                user_message = error_msg
                for key, friendly_msg in user_friendly_errors.items():
                    if key in error_msg.lower():
                        user_message = friendly_msg
                        break
                
                return {
                    'success': False,
                    'error': error_msg,
                    'user_message': user_message
                }
                
        except Exception as e:
            logger.error(f"❌ Erro crítico na troca de senha: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_message': 'Erro interno do sistema. Contate o suporte técnico.'
            }
    
    @staticmethod
    def verify_current_password(email: str, password: str) -> bool:
        """
        Verifica se a senha atual está correta
        
        Args:
            email: Email do usuário
            password: Senha a ser verificada
            
        Returns:
            bool: True se senha está correta
        """
        if not PasswordManager.is_service_available():
            logger.warning("⚠️ Tentativa de verificação de senha sem serviço disponível")
            return False
        
        try:
            return suzano_password_service.validar_senha_atual(email, password)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar senha atual: {e}")
            return False
    
    @staticmethod
    def get_user_info(email: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do usuário
        
        Args:
            email: Email do usuário
            
        Returns:
            Dict com dados do usuário ou None
        """
        if not PasswordManager.is_service_available():
            return None
        
        try:
            return suzano_password_service.obter_dados_usuario(email)
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados do usuário: {e}")
            return None
    
    @staticmethod
    def test_service_connection() -> Dict[str, Any]:
        """
        Testa conexão com o serviço
        
        Returns:
            Dict com resultado do teste
        """
        if not PasswordManager.is_service_available():
            return {
                'connected': False,
                'message': 'Serviço não disponível',
                'details': 'Biblioteca ou configuração ausente'
            }
        
        try:
            connected = suzano_password_service.testar_conexao()
            return {
                'connected': connected,
                'message': 'Conectado com sucesso' if connected else 'Falha na conexão',
                'details': 'SharePoint acessível' if connected else 'Verificar credenciais e rede'
            }
        except Exception as e:
            return {
                'connected': False,
                'message': 'Erro no teste de conexão',
                'details': str(e)
            }
    
    @staticmethod
    def get_password_requirements() -> Dict[str, Any]:
        """
        Retorna requisitos da política de senha
        
        Returns:
            Dict com requisitos da senha
        """
        return {
            'min_length': 6,
            'max_length': 50,
            'requires_letter': False,  # Conforme configuração Suzano
            'requires_number': False,
            'requires_special': False,
            'description': [
                'Mínimo de 6 caracteres',
                'Máximo de 50 caracteres',
                'Não pode estar vazia',
                'Recomendado: use uma combinação de letras, números e símbolos'
            ]
        }


# Funções de conveniência para uso direto
def alterar_senha(email: str, senha_atual: str, nova_senha: str) -> Dict[str, Any]:
    """
    Função de conveniência para alterar senha
    
    Args:
        email: Email do usuário
        senha_atual: Senha atual
        nova_senha: Nova senha
        
    Returns:
        Dict com resultado da operação
    """
    return PasswordManager.change_user_password(email, senha_atual, nova_senha)


def validar_senha(senha: str) -> Dict[str, Any]:
    """
    Função de conveniência para validar senha
    
    Args:
        senha: Senha a ser validada
        
    Returns:
        Dict com resultado da validação
    """
    return PasswordManager.validate_password_policy(senha)


def servico_disponivel() -> bool:
    """
    Função de conveniência para verificar disponibilidade do serviço
    
    Returns:
        bool: True se serviço está disponível
    """
    return PasswordManager.is_service_available()


def obter_requisitos_senha() -> Dict[str, Any]:
    """
    Função de conveniência para obter requisitos de senha
    
    Returns:
        Dict com requisitos da senha
    """
    return PasswordManager.get_password_requirements()


def testar_servico() -> Dict[str, Any]:
    """
    Função de conveniência para testar serviço
    
    Returns:
        Dict com resultado do teste
    """
    return PasswordManager.test_service_connection()