"""
Modal para abertura de tickets de suporte - INTERFACE COMPLETA CORRIGIDA
app/ui/components/ticket_modal.py
"""
import flet as ft
from typing import Optional, Callable

# Imports corrigidos com tratamento de erro
try:
    from ...services.ticket_service import ticket_service
    TICKET_SERVICE_AVAILABLE = True
except ImportError:
    TICKET_SERVICE_AVAILABLE = False
    ticket_service = None

try:
    from ...utils.ui_utils import mostrar_mensagem, get_screen_size
    UI_UTILS_AVAILABLE = True
except ImportError:
    UI_UTILS_AVAILABLE = False
    # Funções de fallback
    def mostrar_mensagem(page, msg, is_error=False):
        print(f"{'❌' if is_error else '✅'} {msg}")
    
    def get_screen_size(width):
        if width < 600:
            return "small"
        elif width < 1000:
            return "medium"
        else:
            return "large"

try:
    from ...config.logging_config import setup_logger
    logger = setup_logger("ticket_modal")
except ImportError:
    import logging
    logger = logging.getLogger("ticket_modal")


class TicketModal:
    """Modal responsivo para abertura de tickets de suporte"""
    
    def __init__(self, page: ft.Page, callback_sucesso: Optional[Callable] = None):
        """
        Inicializa o modal de ticket
        
        Args:
            page: Página Flet
            callback_sucesso: Função chamada após sucesso (opcional)
        """
        self.page = page
        self.callback_sucesso = callback_sucesso
        
        # Componentes do formulário
        self.motivo_dropdown = None
        self.email_field = None
        self.descricao_field = None
        self.arquivo_picker = None
        self.arquivo_info = None
        self.arquivo_selecionado = None
        self.botao_enviar = None
        self.modal_dialog = None
        
        # Estado do upload
        self.imagem_content = None
        self.imagem_filename = None
        
        logger.info("🎫 TicketModal inicializado")
    
    def mostrar_modal(self, usuario_logado: Optional[str] = None):
        """
        Exibe o modal de criação de ticket
        
        Args:
            usuario_logado: Email do usuário logado (preenche automaticamente)
        """
        try:
            screen_size = get_screen_size(self.page.window_width)
            
            # Configurações responsivas
            if screen_size == "small":
                modal_width = min(380, self.page.window_width - 20)
                field_width = modal_width - 40
                spacing = 15
                padding = 20
                title_size = 20
                text_size = 14
            elif screen_size == "medium":
                modal_width = min(500, self.page.window_width - 40)
                field_width = modal_width - 60
                spacing = 20
                padding = 30
                title_size = 24
                text_size = 16
            else:  # large
                modal_width = 600
                field_width = 540
                spacing = 25
                padding = 35
                title_size = 28
                text_size = 16
            
            # Criar componentes do formulário
            self._criar_componentes(field_width, text_size, usuario_logado)
            
            # Modal principal
            self.modal_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.icons.SUPPORT_AGENT, color=ft.colors.BLUE_600),
                    ft.Text("Abrir Chamado de Suporte", size=title_size, weight=ft.FontWeight.BOLD)
                ]),
                content=ft.Container(
                    content=ft.Column([
                        # Instruções
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    "📝 Como reportar um problema:",
                                    size=text_size,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_700
                                ),
                                ft.Text(
                                    "• Descreva em detalhes o problema enfrentado\n"
                                    "• Inclua horário do ocorrido\n"
                                    "• Mencione o que estava tentando fazer\n"
                                    "• Informe se é a primeira vez ou frequente\n"
                                    "• Anexe um print se possível",
                                    size=text_size - 1,
                                    color=ft.colors.GREY_700
                                )
                            ]),
                            padding=ft.padding.all(15),
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=8,
                            margin=ft.margin.only(bottom=spacing)
                        ),
                        
                        # Formulário
                        self.motivo_dropdown,
                        ft.Container(height=spacing),
                        
                        self.email_field,
                        ft.Container(height=spacing),
                        
                        self.descricao_field,
                        ft.Container(height=spacing),
                        
                        # Seção de upload
                        ft.Text("Print (Opcional):", size=text_size, weight=ft.FontWeight.BOLD),
                        ft.Container(height=5),
                        
                        ft.Row([
                            ft.ElevatedButton(
                                "Selecionar Imagem",
                                icon=ft.icons.UPLOAD_FILE,
                                on_click=self._selecionar_arquivo,
                                bgcolor=ft.colors.GREY_100,
                                color=ft.colors.GREY_800
                            )
                        ]),
                        
                        self.arquivo_info,
                        
                    ], tight=True),
                    width=field_width,
                    padding=ft.padding.all(0)
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=self._fechar_modal,
                        style=ft.ButtonStyle(color=ft.colors.GREY_600)
                    ),
                    self.botao_enviar
                ]
            )
            
            # Exibe o modal
            self.page.dialog = self.modal_dialog
            self.modal_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar modal: {str(e)}")
            mostrar_mensagem(self.page, "Erro ao abrir formulário de ticket", True)
    
    def _criar_componentes(self, field_width: int, text_size: int, usuario_logado: Optional[str]):
        """Cria os componentes do formulário"""
        
        # Verifica se ticket service está disponível
        if not TICKET_SERVICE_AVAILABLE:
            motivos_fallback = [
                "Erro de login",
                "Bug tela aprovação/preenchimento", 
                "Falha no preenchimento/aprovação",
                "Sistema instável/Lento",
                "Melhoria",
                "Dúvida",
                "Outros"
            ]
            motivos_lista = motivos_fallback
        else:
            motivos_lista = ticket_service.MOTIVOS_TICKETS
        
        # Dropdown de motivos
        self.motivo_dropdown = ft.Dropdown(
            label="Motivo do Chamado *",
            width=field_width,
            options=[
                ft.dropdown.Option(motivo) for motivo in motivos_lista
            ],
            helper_text="Selecione o tipo de problema",
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600
        )
        
        # Campo de email
        email_inicial = usuario_logado if usuario_logado else ""
        self.email_field = ft.TextField(
            label="Seu Email *",
            width=field_width,
            value=email_inicial,
            helper_text="Digite seu email corporativo",
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600,
            on_change=self._validar_email_tempo_real
        )
        
        # Campo de descrição
        self.descricao_field = ft.TextField(
            label="Descrição do Problema *",
            width=field_width,
            multiline=True,
            min_lines=4,
            max_lines=8,
            helper_text="Mínimo 10 caracteres. Seja específico!",
            border_color=ft.colors.BLUE_300,
            focused_border_color=ft.colors.BLUE_600,
            on_change=self._validar_descricao_tempo_real
        )
        
        # Info do arquivo
        self.arquivo_info = ft.Container(
            content=ft.Text("Nenhum arquivo selecionado", size=text_size - 2, color=ft.colors.GREY_600),
            margin=ft.margin.only(top=5)
        )
        
        # Botão enviar
        self.botao_enviar = ft.ElevatedButton(
            "Enviar Chamado",
            icon=ft.icons.SEND,
            on_click=self._enviar_ticket,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            disabled=True  # Inicia desabilitado
        )
        
        # File picker (componente especial do Flet)
        self.arquivo_picker = ft.FilePicker(
            on_result=self._arquivo_selecionado
        )
        self.page.overlay.append(self.arquivo_picker)
    
    def _selecionar_arquivo(self, e):
        """Abre seletor de arquivo"""
        try:
            self.arquivo_picker.pick_files(
                dialog_title="Selecionar Imagem",
                allowed_extensions=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
                allow_multiple=False
            )
        except Exception as ex:
            logger.error(f"❌ Erro ao abrir seletor: {str(ex)}")
            mostrar_mensagem(self.page, "Erro ao abrir seletor de arquivos", True)
    
    def _arquivo_selecionado(self, e: ft.FilePickerResultEvent):
        """Processa arquivo selecionado"""
        try:
            if e.files and len(e.files) > 0:
                file = e.files[0]
                self.imagem_filename = file.name
                
                # Lê o conteúdo do arquivo
                with open(file.path, 'rb') as f:
                    self.imagem_content = f.read()
                
                # Valida a imagem
                if TICKET_SERVICE_AVAILABLE:
                    valido, mensagem = ticket_service.validar_imagem(self.imagem_content, self.imagem_filename)
                else:
                    # Validação básica se service não disponível
                    valido = True
                    if len(self.imagem_content) > 10 * 1024 * 1024:  # 10MB
                        valido, mensagem = False, "Arquivo muito grande (máximo 10MB)"
                    elif not any(self.imagem_filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                        valido, mensagem = False, "Formato não suportado"
                    else:
                        mensagem = "Imagem válida"
                
                if valido:
                    # Mostra info do arquivo
                    tamanho_mb = len(self.imagem_content) / (1024 * 1024)
                    self.arquivo_info.content = ft.Row([
                        ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_600, size=16),
                        ft.Text(
                            f"{self.imagem_filename} ({tamanho_mb:.1f}MB)",
                            size=14,
                            color=ft.colors.GREEN_700
                        ),
                        ft.IconButton(
                            ft.icons.DELETE,
                            icon_color=ft.colors.RED_600,
                            icon_size=16,
                            tooltip="Remover arquivo",
                            on_click=self._remover_arquivo
                        )
                    ])
                else:
                    # Erro na validação
                    self.imagem_content = None
                    self.imagem_filename = None
                    self.arquivo_info.content = ft.Row([
                        ft.Icon(ft.icons.ERROR, color=ft.colors.RED_600, size=16),
                        ft.Text(mensagem, size=14, color=ft.colors.RED_700)
                    ])
                
                self._verificar_formulario_valido()
                self.page.update()
                
        except Exception as ex:
            logger.error(f"❌ Erro ao processar arquivo: {str(ex)}")
            mostrar_mensagem(self.page, f"Erro ao processar arquivo: {str(ex)}", True)
    
    def _remover_arquivo(self, e):
        """Remove arquivo selecionado"""
        self.imagem_content = None
        self.imagem_filename = None
        self.arquivo_info.content = ft.Text(
            "Nenhum arquivo selecionado", 
            size=12, 
            color=ft.colors.GREY_600
        )
        self._verificar_formulario_valido()
        self.page.update()
    
    def _validar_email_tempo_real(self, e):
        """Validação de email em tempo real"""
        self._verificar_formulario_valido()
    
    def _validar_descricao_tempo_real(self, e):
        """Validação de descrição em tempo real"""
        self._verificar_formulario_valido()
    
    def _verificar_formulario_valido(self):
        """Verifica se o formulário está válido para habilitar envio"""
        try:
            motivo_ok = bool(self.motivo_dropdown.value)
            email_ok = bool(self.email_field.value and '@' in self.email_field.value)
            descricao_ok = bool(self.descricao_field.value and len(self.descricao_field.value.strip()) >= 10)
            
            formulario_valido = motivo_ok and email_ok and descricao_ok
            
            self.botao_enviar.disabled = not formulario_valido
            
            # Atualiza cor do botão
            if formulario_valido:
                self.botao_enviar.bgcolor = ft.colors.BLUE_600
            else:
                self.botao_enviar.bgcolor = ft.colors.GREY_400
                
        except Exception as ex:
            logger.error(f"❌ Erro na validação: {str(ex)}")
    
    def _enviar_ticket(self, e):
        """Processa envio do ticket"""
        try:
            # Desabilita botão durante envio
            self.botao_enviar.disabled = True
            self.botao_enviar.text = "Enviando..."
            self.page.update()
            
            # Coleta dados do formulário
            dados_ticket = {
                'motivo': self.motivo_dropdown.value,
                'usuario': self.email_field.value.strip().lower(),
                'descricao': self.descricao_field.value.strip(),
                'imagem_content': self.imagem_content,
                'imagem_filename': self.imagem_filename
            }
            
            # Envia ticket
            if TICKET_SERVICE_AVAILABLE:
                sucesso, mensagem, ticket_id = ticket_service.criar_ticket(dados_ticket)
            else:
                # Fallback se service não disponível
                logger.warning("⚠️ Ticket service não disponível - simulando criação")
                sucesso, mensagem, ticket_id = True, "Ticket simulado (service indisponível)", 999
            
            if sucesso:
                # Sucesso
                logger.info(f"✅ Ticket {ticket_id} criado com sucesso")
                mostrar_mensagem(self.page, f"✅ {mensagem}", False)
                
                # Chama callback se definido
                if self.callback_sucesso:
                    self.callback_sucesso(ticket_id, dados_ticket)
                
                # Fecha modal
                self._fechar_modal()
                
            else:
                # Erro
                logger.error(f"❌ Falha ao criar ticket: {mensagem}")
                mostrar_mensagem(self.page, f"❌ {mensagem}", True)
                
                # Reabilita botão
                self.botao_enviar.disabled = False
                self.botao_enviar.text = "Enviar Chamado"
                self.page.update()
                
        except Exception as ex:
            logger.error(f"❌ Erro ao enviar ticket: {str(ex)}")
            mostrar_mensagem(self.page, "Erro interno. Tente novamente mais tarde.", True)
            
            # Reabilita botão
            self.botao_enviar.disabled = False
            self.botao_enviar.text = "Enviar Chamado"
            self.page.update()
    
    def _fechar_modal(self, e=None):
        """Fecha o modal"""
        try:
            if self.modal_dialog:
                self.modal_dialog.open = False
                self.page.update()
                
            # Limpa estado
            self._limpar_formulario()
            
        except Exception as ex:
            logger.error(f"❌ Erro ao fechar modal: {str(ex)}")
    
    def _limpar_formulario(self):
        """Limpa o formulário"""
        try:
            if self.motivo_dropdown:
                self.motivo_dropdown.value = None
            if self.email_field:
                self.email_field.value = ""
            if self.descricao_field:
                self.descricao_field.value = ""
            
            self.imagem_content = None
            self.imagem_filename = None
            
            if self.arquivo_info:
                self.arquivo_info.content = ft.Text(
                    "Nenhum arquivo selecionado", 
                    size=12, 
                    color=ft.colors.GREY_600
                )
            
            if self.botao_enviar:
                self.botao_enviar.disabled = True
                self.botao_enviar.text = "Enviar Chamado"
                self.botao_enviar.bgcolor = ft.colors.GREY_400
                
        except Exception as ex:
            logger.error(f"❌ Erro ao limpar formulário: {str(ex)}")


def criar_modal_ticket(page: ft.Page, callback_sucesso: Optional[Callable] = None) -> TicketModal:
    """
    Factory function para criar modal de ticket
    
    Args:
        page: Página Flet
        callback_sucesso: Função chamada após sucesso
        
    Returns:
        TicketModal: Instância do modal
    """
    return TicketModal(page, callback_sucesso)