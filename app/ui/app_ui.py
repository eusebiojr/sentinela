"""
Orquestrador principal da interface do usuário
"""
import flet as ft
import threading
from ..core.session_state import get_session_state
from ..services.sharepoint_client import SharePointClient
from ..utils.data_utils import DataUtils
from ..utils.ui_utils import mostrar_mensagem, get_screen_size
from ..config.logging_config import setup_logger
from .screens.login import LoginScreen
from .screens.dashboard import DashboardScreen
from typing import Dict, Any, Optional
from ..config.logging_config import setup_logger
from ..services.auto_refresh_service import inicializar_auto_refresh, obter_auto_refresh_service
from ..ui.components.auto_refresh_indicator import criar_auto_refresh_indicator, obter_auto_refresh_indicator



logger = setup_logger()


class SentinelaApp:
    """Classe principal que orquestra toda a aplicação"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.login_screen = LoginScreen(page, self)
        self.dashboard_screen = DashboardScreen(page, self)
        self.carregando_dados = False
        self.auto_refresh_service = inicializar_auto_refresh(page, self)
        self.auto_refresh_indicator = criar_auto_refresh_indicator(page)
        self._configurar_auto_refresh_callbacks()
        
    """
Modificações para integrar Auto-Refresh na SentinelaApp
Localização: app/ui/app_ui.py

INSTRUÇÕES: Aplicar estas modificações no arquivo existente
"""

# ================================
# 1. IMPORTS ADICIONAIS (adicionar no topo)
# ================================
from ..services.auto_refresh_service import inicializar_auto_refresh, obter_auto_refresh_service
from ..ui.components.auto_refresh_indicator import criar_auto_refresh_indicator, obter_auto_refresh_indicator


# ================================
# 2. MODIFICAÇÃO NA CLASSE SentinelaApp
# ================================

class SentinelaApp:
    """Classe principal que orquestra toda a aplicação - VERSÃO COM AUTO-REFRESH"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.login_screen = LoginScreen(page, self)
        self.dashboard_screen = DashboardScreen(page, self)
        
        # NOVO: Status de carregamento
        self.carregando_dados = False
        
        # NOVO: Inicializa services de auto-refresh
        self.auto_refresh_service = inicializar_auto_refresh(page, self)
        self.auto_refresh_indicator = criar_auto_refresh_indicator(page)
        
        # NOVO: Configura callbacks entre services
        self._configurar_auto_refresh_callbacks()
        
    def _configurar_auto_refresh_callbacks(self):
        """Configura callbacks entre auto-refresh e indicador visual"""
        try:
            # Callback para atualização de dados
            def callback_atualizacao():
                self.atualizar_dados(auto_refresh=True)
            
            # Callback para mudança de status
            def callback_status_mudou(status):
                if self.auto_refresh_indicator:
                    self.auto_refresh_indicator.atualizar_status(status)
                    
                    # Mostra toast em mudanças importantes
                    estado_anterior = getattr(self, '_ultimo_estado_refresh', None)
                    estado_atual = status.get("estado")
                    
                    if estado_anterior != estado_atual and estado_anterior is not None:
                        self.auto_refresh_indicator.mostrar_toast_mudanca(estado_atual)
                    
                    self._ultimo_estado_refresh = estado_atual
            
            # Configura callbacks no service
            if self.auto_refresh_service:
                self.auto_refresh_service.configurar_callbacks(
                    callback_atualizacao=callback_atualizacao,
                    callback_status_mudou=callback_status_mudou
                )
                
            logger.info("✅ Callbacks do auto-refresh configurados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar callbacks auto-refresh: {e}")

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
                session = get_session_state(self.page)
                session.df_usuarios = SharePointClient.carregar_lista("UsuariosPainelTorre")
                
                if not session.df_usuarios.empty:
                    logger.info(f"✅ {len(session.df_usuarios)} usuários carregados")
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
            # IMPORTANTE: Obtém sessão limpa para este usuário
            session = get_session_state(self.page)
            
            # Garante que não há dados de outro usuário
            if session.usuario and session.usuario.get('Email', '').lower() != email.lower():
                logger.warning(f"⚠️ Limpando sessão anterior de {session.usuario.get('Email')}")
                session.reset_dados()
            
            # Valida credenciais
            sucesso, user_data = self._validar_login(email, senha)
            
            if not sucesso:
                return False
            
            # Armazena usuário na sessão específica
            session.usuario = user_data
            logger.info(f"✅ Login bem-sucedido: {email} na sessão {session.session_id}")
            
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
        session = get_session_state(self.page)
        if session.df_usuarios.empty:
            return False, None
        
        # Busca coluna de email
        email_columns = [col for col in session.df_usuarios.columns if 'email' in col.lower()]
        if not email_columns:
            return False, None
        
        email_col = email_columns[0]
        
        # Busca usuário
        email_normalizado = email.strip().lower()
        df_temp = session.df_usuarios.copy()
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
        session = get_session_state(self.page)
        nome_usuario = session.get_nome_usuario()
        
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
                
                session = get_session_state(self.page)
                # Carrega desvios
                session.df_desvios = SharePointClient.carregar_lista("Desvios")
                
                # Processa dados
                session.df_desvios = DataUtils.processar_desvios(session.df_desvios)
                
                # Marca como carregado
                session.dados_carregados = True
                
                logger.info(f"✅ Dados carregados: {len(session.df_desvios)} desvios")
                
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
    
    def atualizar_dados(self, auto_refresh=False):
        """
        Atualiza dados do sistema
        
        Args:
            auto_refresh: True se chamado pelo timer automático
        """
        if self.carregando_dados:
            if not auto_refresh:  # Só mostra aviso se não for auto-refresh
                mostrar_mensagem(self.page, "⏳ Atualização já em andamento...", "info")
            return

        try:
            self.carregando_dados = True
            session = get_session_state(self.page)
            
            if not auto_refresh:
                mostrar_mensagem(self.page, "🔄 Atualizando dados...", "info")
            else:
                logger.info("🔄 Auto-refresh executando atualização...")
            
            # Carrega dados atualizados
            df_usuarios_novo = SharePointClient.obter_usuarios()
            df_desvios_novo = SharePointClient.obter_desvios()
            
            if not df_usuarios_novo.empty and not df_desvios_novo.empty:
                # Processa dados
                df_desvios_processado = DataUtils.processar_desvios_completo(df_desvios_novo)
                
                # Atualiza sessão
                session.df_usuarios = df_usuarios_novo
                session.df_desvios = df_desvios_processado
                session.dados_carregados = True
                
                # Reconstrói interface atual
                self._reconstruir_interface_atual()
                
                if not auto_refresh:
                    mostrar_mensagem(self.page, "✅ Dados atualizados com sucesso!", "success")
                else:
                    logger.info("✅ Auto-refresh concluído com sucesso")
                    
            else:
                if not auto_refresh:
                    mostrar_mensagem(self.page, "⚠️ Erro ao carregar dados atualizados", "warning")
                else:
                    logger.warning("⚠️ Auto-refresh: erro ao carregar dados")
                
        except Exception as e:
            logger.error(f"❌ Erro na atualização de dados: {e}")
            if not auto_refresh:
                mostrar_mensagem(self.page, f"❌ Erro: {str(e)}", "error")
        finally:
            self.carregando_dados = False

    def _reconstruir_interface_atual(self):
        """Reconstrói a interface atual após atualização de dados"""
        try:
            session = get_session_state(self.page)
            
            # Verifica qual tela está ativa e reconstrói
            if session.is_usuario_logado():
                # Reconstrói dashboard (tela principal)
                self.mostrar_dashboard()
                
        except Exception as e:
            logger.error(f"❌ Erro ao reconstruir interface: {e}")

    def inicializar_auto_refresh_para_usuario(self):
        """Inicializa auto-refresh baseado nas configurações do usuário"""
        try:
            session = get_session_state(self.page)
            
            # Verifica configuração do usuário
            auto_refresh_habilitado = session.obter_configuracao_usuario('auto_refresh', False)
            
            if auto_refresh_habilitado and self.auto_refresh_service:
                logger.info(f"🔄 Habilitando auto-refresh para usuário {session.get_nome_usuario()}")
                self.auto_refresh_service.habilitar_usuario(True)
            else:
                logger.info(f"🔕 Auto-refresh desabilitado para usuário {session.get_nome_usuario()}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar auto-refresh: {e}")

    def parar_auto_refresh(self):
        """Para o auto-refresh (usado no logout)"""
        try:
            if self.auto_refresh_service:
                self.auto_refresh_service.parar_timer()
                
            if self.auto_refresh_indicator:
                self.auto_refresh_indicator.parar_atualizacao()
                
            logger.info("🛑 Auto-refresh parado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar auto-refresh: {e}")

    def obter_componente_auto_refresh_indicator(self):
        """
        Retorna componente do indicador para integração no header
        
        Returns:
            ft.Container: Componente visual do indicador
        """
        if self.auto_refresh_indicator:
            return self.auto_refresh_indicator.criar_indicador()
        return ft.Container()  # Container vazio se não disponível
      
    def registrar_campo_para_monitoring(self, campo_id: str, valor_original: any):
        """
        Registra um campo para monitoramento de alterações
        
        Args:
            campo_id: Identificador único do campo
            valor_original: Valor original do campo
        """
        try:
            session = get_session_state(self.page)
            session.registrar_campo_original(campo_id, valor_original)
        except Exception as e:
            logger.error(f"❌ Erro ao registrar campo: {e}")

    def notificar_alteracao_campo(self, campo_id: str, novo_valor: any):
        """
        Notifica alteração em um campo
        
        Args:
            campo_id: Identificador único do campo
            novo_valor: Novo valor do campo
        """
        try:
            session = get_session_state(self.page)
            session.registrar_alteracao_campo(campo_id, novo_valor)
        except Exception as e:
            logger.error(f"❌ Erro ao notificar alteração: {e}")

    def limpar_alteracoes_campos(self):
        """Limpa todas as alterações de campos (após salvar)"""
        try:
            session = get_session_state(self.page)
            session.limpar_alteracoes_campos()
            logger.info("✅ Alterações de campos limpas")
        except Exception as e:
            logger.error(f"❌ Erro ao limpar alterações: {e}")

    def mostrar_dashboard(self):
        """Mostra a tela do dashboard"""
        self.dashboard_screen.mostrar()
    
    def fazer_logout(self):
        """Faz logout do usuário - VERSÃO ATUALIZADA"""
        try:
            # NOVO: Para auto-refresh antes do logout
            self.parar_auto_refresh()
            
            # Limpeza existente
            session = get_session_state(self.page)
            session.reset_dados()
            
            # Volta para tela de login
            self.login_screen.mostrar()
            
            logger.info("✅ Logout realizado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro no logout: {e}")

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