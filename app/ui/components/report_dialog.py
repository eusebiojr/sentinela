import flet as ft
from typing import List, Optional, Dict, Any
import threading

from ...core.session_state import get_session_state
from ...services.ticket_service import ticket_service, obter_categorias, obter_orientacoes
from ...services.file_upload_service import file_upload_service
from ...utils.ui_utils import mostrar_mensagem, get_screen_size
from ...config.logging_config import setup_logger

logger = setup_logger("report_dialog")


class ReportDialog:
    """Modal para reportar problemas e abrir tickets"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.modal = None
        self.arquivos_selecionados = []
        self.file_picker = None
        self.processando = False
        
        # Componentes do formulário
        self.motivo_dropdown = None
        self.usuario_field = None
        self.descricao_field = None
        self.arquivos_container = None
        self.btn_enviar = None
        self.error_text = None
        
        logger.info("🎫 ReportDialog inicializado - Versão final corrigida")
    
    def criar_modal(self, usuario_logado: str = "") -> ft.AlertDialog:
        """Cria o modal de report - VERSÃO FINAL CORRIGIDA"""
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            modal_width = min(480, self.page.window_width - 30)
            modal_height = 650
            field_width = modal_width - 50
        elif screen_size == "medium":
            modal_width = 600
            modal_height = 700
            field_width = modal_width - 60
        else:  # large
            modal_width = 700
            modal_height = 750
            field_width = modal_width - 80
        
        # Inicializa FilePicker
        self._setup_file_picker()
        
        # Campos do formulário
        self._criar_campos_formulario(field_width, usuario_logado)
        
        # Seções do modal
        secao_orientacoes = self._criar_secao_orientacoes()
        secao_formulario = self._criar_secao_formulario()
        secao_anexos = self._criar_secao_anexos()
        
        # Texto de erro
        self.error_text = ft.Text(
            "", 
            color=ft.colors.RED, 
            size=12, 
            visible=False,
            max_lines=5,
            overflow=ft.TextOverflow.VISIBLE
        )
        
        # CORRIGIDO: Botões com tamanho fixo
        btn_cancelar = ft.TextButton(
            "Cancelar", 
            on_click=self._cancelar,
            width=100  # Tamanho fixo
        )
        
        self.btn_enviar.width = 140  # Tamanho fixo
        
        # Modal principal
        content_column = ft.Column([
            secao_orientacoes,
            ft.Divider(height=20, color=ft.colors.GREY_300),
            secao_formulario,
            secao_anexos,
            ft.Container(height=15),
            self.error_text
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        self.modal = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.BUG_REPORT, color=ft.colors.ORANGE_600, size=28),
                ft.Text("Reportar Problema", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=10),
            content=ft.Container(
                content=content_column,
                width=modal_width,
                height=modal_height,
                padding=ft.padding.all(20)
            ),
            actions=[btn_cancelar, self.btn_enviar],  # Botões com tamanho fixo
            actions_alignment=ft.MainAxisAlignment.END,  # Alinhamento
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        return self.modal
    
    def _setup_file_picker(self):
        """CORRIGIDO: FilePicker mais compatível"""
        if self.file_picker:
            if self.file_picker in self.page.overlay:
                self.page.overlay.remove(self.file_picker)
        
        self.file_picker = ft.FilePicker(on_result=self._on_files_selected)
        self.page.overlay.append(self.file_picker)
        self.page.update()
    
    def _criar_campos_formulario(self, field_width: int, usuario_logado: str):
        """Cria os campos do formulário"""
        
        # Dropdown de motivo
        categorias = obter_categorias()
        opcoes_motivo = [ft.dropdown.Option(categoria) for categoria in categorias]
        
        self.motivo_dropdown = ft.Dropdown(
            label="Tipo do Problema *",
            options=opcoes_motivo,
            width=field_width,
            hint_text="Selecione a categoria do problema",
            border_radius=8,
            filled=True,
            bgcolor=ft.colors.GREY_50
        )
        
        # Campo de usuário
        self.usuario_field = ft.TextField(
            label="Seu Email *",
            value=usuario_logado,
            width=field_width,
            hint_text="exemplo@suzano.com.br",
            prefix_icon=ft.icons.EMAIL,
            border_radius=8,
            filled=True,
            bgcolor=ft.colors.GREY_50
        )
        
        # Campo de descrição
        self.descricao_field = ft.TextField(
            label="Descrição Detalhada do Problema *",
            multiline=True,
            min_lines=4,
            max_lines=8,
            width=field_width,
            hint_text="Descreva o problema com o máximo de detalhes possível...",
            border_radius=8,
            filled=True,
            bgcolor=ft.colors.GREY_50
        )
        
        # CORRIGIDO: Botão enviar com tamanho fixo
        self.btn_enviar = ft.ElevatedButton(
            "Enviar Ticket",
            icon=ft.icons.SEND,
            on_click=self._enviar_ticket,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            width=140,  # Tamanho fixo
            height=40
        )
    
    def _criar_secao_orientacoes(self) -> ft.Container:
        """Cria seção com orientações"""
        orientacoes = obter_orientacoes()
        
        orientacoes_text = ft.Column([
            ft.Text(
                "💡 Para nos ajudar a resolver seu problema rapidamente, inclua:",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_700
            ),
            ft.Container(height=5),
            *[
                ft.Text(orientacao, size=11, color=ft.colors.GREY_700)
                for orientacao in orientacoes
            ]
        ], spacing=2)
        
        return ft.Container(
            content=orientacoes_text,
            padding=ft.padding.all(15),
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_200)
        )
    
    def _criar_secao_formulario(self) -> ft.Column:
        """Cria seção do formulário"""
        return ft.Column([
            ft.Text("📝 Informações do Problema", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800),
            self.motivo_dropdown,
            self.usuario_field,
            self.descricao_field
        ], spacing=12)
    
    def _criar_secao_anexos(self) -> ft.Column:
        """Cria seção de anexos"""
        # Container para arquivos selecionados
        self.arquivos_container = ft.Column(spacing=8)
        
        # Botão para selecionar arquivos
        btn_selecionar = ft.ElevatedButton(
            "📎 Anexar Imagens",
            icon=ft.icons.ATTACH_FILE,
            on_click=self._selecionar_arquivos,
            bgcolor=ft.colors.GREEN_100,
            color=ft.colors.GREEN_800,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            width=180  # Tamanho fixo
        )
        
        # Informações sobre limites
        limites = file_upload_service.obter_informacoes_limites()
        info_limites = ft.Text(
            f"Máximo: {limites['max_files']} arquivos, "
            f"{limites['max_file_size_mb']}MB cada, "
            f"{limites['max_total_size_mb']}MB total. "
            f"Formatos: {limites['allowed_formats']}",
            size=10,
            color=ft.colors.GREY_600,
            italic=True
        )
        
        return ft.Column([
            ft.Text("📷 Anexos (Opcional)", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800),
            btn_selecionar,
            info_limites,
            self.arquivos_container
        ], spacing=8)
    
    def _selecionar_arquivos(self, e):
        """CORRIGIDO: Seleção de arquivos mais robusta"""
        if self.processando:
            return
        
        try:
            logger.info("📁 Iniciando seleção de arquivos...")
            
            # CORRIGIDO: Usar pick_files simples sem especificar tipo
            self.file_picker.pick_files(
                dialog_title="Selecionar Imagens para Anexar",
                allow_multiple=True
                # Removido file_type e allowed_extensions para maior compatibilidade
            )
            
        except Exception as ex:
            logger.error(f"❌ Erro ao abrir seletor: {ex}")
            self._mostrar_erro(f"Erro ao abrir seletor de arquivos: {str(ex)}")
    
    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        """CORRIGIDO: Callback melhorado para files selected"""
        try:
            logger.info(f"📁 Callback executado - Event: {e}")
            
            if not e.files:
                logger.warning("⚠️ Nenhum arquivo no evento")
                mostrar_mensagem(self.page, "ℹ️ Nenhum arquivo selecionado", "info")
                return
            
            logger.info(f"📋 {len(e.files)} arquivos detectados no evento")
            
            # CORRIGIDO: Debug detalhado dos arquivos
            file_paths = []
            for i, f in enumerate(e.files):
                logger.debug(f"📂 Arquivo {i+1}: name='{f.name}', path='{f.path}', size={getattr(f, 'size', 'N/A')}")
                
                # CORRIGIDO: Verifica se arquivo tem path válido
                if hasattr(f, 'path') and f.path:
                    file_paths.append(f.path)
                elif hasattr(f, 'name') and f.name:
                    # Fallback: se não tem path, usa apenas o nome (web)
                    logger.warning(f"⚠️ Arquivo sem path, apenas nome: {f.name}")
                    # No Flet web, não temos acesso ao path real
                    self._mostrar_erro("Seleção de arquivos não suportada no navegador. Use a versão desktop.")
                    return
            
            if not file_paths:
                logger.warning("⚠️ Nenhum path válido encontrado")
                self._mostrar_erro("Nenhum arquivo com caminho válido encontrado. Tente novamente.")
                return
            
            logger.info(f"📋 {len(file_paths)} caminhos válidos para processar")
            
            # CORRIGIDO: Filtra apenas imagens manualmente
            file_paths_filtrados = []
            for path in file_paths:
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    file_paths_filtrados.append(path)
                    logger.debug(f"✅ Arquivo de imagem aceito: {path}")
                else:
                    logger.warning(f"⚠️ Arquivo não é imagem: {path}")
            
            if not file_paths_filtrados:
                self._mostrar_erro("Nenhum arquivo de imagem válido selecionado. Use: PNG, JPG, GIF, BMP ou WebP")
                return
            
            # Valida arquivos
            logger.info(f"🔍 Validando {len(file_paths_filtrados)} arquivos de imagem...")
            validacao = file_upload_service.validar_lote_arquivos(file_paths_filtrados)
            
            if not validacao["valido"]:
                erros_str = "\\n".join(validacao["erros"])
                logger.warning(f"❌ Validação falhou: {validacao['erros']}")
                self._mostrar_erro(f"Erro nos arquivos:\\n{erros_str}")
                return
            
            # Armazena arquivos válidos
            self.arquivos_selecionados = validacao["arquivos_validos"]
            
            # Atualiza interface
            self._atualizar_lista_arquivos()
            
            # Mensagem de sucesso
            mensagem_sucesso = f"✅ {len(self.arquivos_selecionados)} arquivo(s) selecionado(s) com sucesso"
            mostrar_mensagem(self.page, mensagem_sucesso, "success")
            
            logger.info(f"✅ {len(self.arquivos_selecionados)} arquivos processados com sucesso")
            
        except Exception as ex:
            logger.error(f"❌ Erro crítico no callback: {ex}")
            self._mostrar_erro(f"Erro interno ao processar arquivos: {str(ex)}")
    
    def _atualizar_lista_arquivos(self):
        """Atualiza a lista de arquivos selecionados"""
        self.arquivos_container.controls.clear()
        
        if not self.arquivos_selecionados:
            return
        
        for i, arquivo in enumerate(self.arquivos_selecionados):
            # Card do arquivo
            arquivo_card = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.IMAGE, color=ft.colors.GREEN_600, size=20),
                    ft.Column([
                        ft.Text(
                            arquivo["nome"], 
                            size=12, 
                            weight=ft.FontWeight.W_500,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            f"{arquivo['tamanho_mb']:.1f} MB", 
                            size=10, 
                            color=ft.colors.GREY_600
                        )
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        icon_color=ft.colors.RED_600,
                        icon_size=18,
                        tooltip="Remover arquivo",
                        on_click=lambda e, idx=i: self._remover_arquivo(idx)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.all(10),
                bgcolor=ft.colors.GREEN_50,
                border_radius=6,
                border=ft.border.all(1, ft.colors.GREEN_200)
            )
            
            self.arquivos_container.controls.append(arquivo_card)
        
        self.page.update()
    
    def _remover_arquivo(self, index: int):
        """Remove um arquivo da lista"""
        if 0 <= index < len(self.arquivos_selecionados):
            arquivo_removido = self.arquivos_selecionados.pop(index)
            self._atualizar_lista_arquivos()
            
            mostrar_mensagem(
                self.page, 
                f"🗑️ {arquivo_removido['nome']} removido", 
                "info"
            )
    
    def _validar_formulario(self) -> Dict[str, Any]:
        """Valida o formulário antes do envio"""
        resultado = {
            "valido": True,
            "erros": []
        }
        
        # Valida motivo
        if not self.motivo_dropdown.value:
            resultado["erros"].append("Selecione o tipo do problema")
        
        # Valida usuário
        if not self.usuario_field.value or not self.usuario_field.value.strip():
            resultado["erros"].append("Informe seu email")
        elif "@" not in self.usuario_field.value or "." not in self.usuario_field.value:
            resultado["erros"].append("Email inválido")
        
        # Valida descrição
        descricao = self.descricao_field.value or ""
        if not descricao.strip():
            resultado["erros"].append("Descreva o problema")
        elif len(descricao.strip()) < 10:
            resultado["erros"].append("Descrição muito curta (mínimo 10 caracteres)")
        
        if resultado["erros"]:
            resultado["valido"] = False
        
        return resultado
    
    def _mostrar_erro(self, mensagem: str):
        """Mostra mensagem de erro no modal"""
        self.error_text.value = f"⚠️ {mensagem}"
        self.error_text.visible = True
        self.page.update()
        
        logger.warning(f"⚠️ Erro mostrado: {mensagem}")
    
    def _limpar_erro(self):
        """Limpa mensagem de erro"""
        self.error_text.visible = False
        self.page.update()
    
    def _ativar_modo_envio(self, ativo: bool):
        """Ativa/desativa modo de envio"""
        self.processando = ativo
        
        if ativo:
            self.btn_enviar.text = "Enviando..."
            self.btn_enviar.icon = ft.icons.HOURGLASS_EMPTY
            self.btn_enviar.disabled = True
        else:
            self.btn_enviar.text = "Enviar Ticket"
            self.btn_enviar.icon = ft.icons.SEND
            self.btn_enviar.disabled = False
        
        # Desabilita campos durante envio
        self.motivo_dropdown.disabled = ativo
        self.usuario_field.disabled = ativo
        self.descricao_field.disabled = ativo
        
        self.page.update()
    
    def _mostrar_mensagem_sucesso_grande(self, ticket_id: int):
        """CORRIGIDO: Mensagem de sucesso com botão fixo"""
        def fechar_sucesso(e):
            modal_sucesso.open = False
            self.page.update()
        
        # Mensagem completa de sucesso
        mensagem_completa = f"""🎫 Obrigado! Seu ticket #{ticket_id} foi aberto e será tratado o quanto antes.

📧 Você receberá atualizações sobre o andamento do seu ticket por email.

⏱️ Tempo médio de resposta: 24-48 horas úteis.

💡 Dica: Guarde o número #{ticket_id} para futuras consultas."""
        
        # CORRIGIDO: Botão com tamanho fixo
        btn_entendido = ft.ElevatedButton(
            "Entendido",
            icon=ft.icons.THUMB_UP,
            on_click=fechar_sucesso,
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            width=120,  # Tamanho fixo
            height=40
        )
        
        # Modal de sucesso
        modal_sucesso = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_600, size=32),
                ft.Text("Ticket Criado com Sucesso!", weight=ft.FontWeight.BOLD, size=18, color=ft.colors.GREEN_700)
            ], spacing=10),
            content=ft.Container(
                content=ft.Text(
                    mensagem_completa,
                    size=14,
                    color=ft.colors.GREY_800,
                    text_align=ft.TextAlign.LEFT
                ),
                width=450,  # Largura maior
                padding=ft.padding.all(20)
            ),
            actions=[btn_entendido],
            actions_alignment=ft.MainAxisAlignment.CENTER,  # Centraliza botão
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        # Mostra modal de sucesso
        self.page.dialog = modal_sucesso
        modal_sucesso.open = True
        self.page.update()
    
    def _enviar_ticket(self, e):
        """Envia o ticket"""
        if self.processando:
            return
        
        # Limpa erros anteriores
        self._limpar_erro()
        
        # Valida formulário
        validacao = self._validar_formulario()
        if not validacao["valido"]:
            self._mostrar_erro("\\n".join(validacao["erros"]))
            return
        
        # Ativa modo envio
        self._ativar_modo_envio(True)
        mostrar_mensagem(self.page, "📤 Enviando ticket...", "info")
        
        # Processa em thread separada
        def processar_envio():
            try:
                logger.info("🎫 Iniciando envio de ticket...")
                
                # Prepara dados do ticket
                dados_ticket = {
                    "motivo": self.motivo_dropdown.value,
                    "usuario": self.usuario_field.value.strip(),
                    "descricao": self.descricao_field.value.strip(),
                    "anexos": []
                }
                
                # Processa anexos se houver
                if self.arquivos_selecionados:
                    logger.info(f"📎 Processando {len(self.arquivos_selecionados)} anexos...")
                    file_paths = [arquivo["caminho"] for arquivo in self.arquivos_selecionados]
                    resultado_anexos = file_upload_service.processar_arquivos_para_ticket(file_paths)
                    
                    if resultado_anexos["sucesso"]:
                        dados_ticket["anexos"] = resultado_anexos["arquivos_processados"]
                        logger.info(f"✅ {len(dados_ticket['anexos'])} anexos processados")
                    else:
                        logger.warning(f"⚠️ Erro nos anexos: {resultado_anexos['erros']}")
                
                # Envia ticket
                logger.info("📤 Enviando dados para SharePoint...")
                resultado = ticket_service.abrir_ticket_completo(**dados_ticket)
                
                # Desativa modo envio
                self._ativar_modo_envio(False)
                
                if resultado["sucesso"]:
                    # Sucesso - fecha modal atual
                    self._fechar_modal()
                    
                    # Mostra modal de sucesso grande
                    self._mostrar_mensagem_sucesso_grande(resultado['ticket_id'])
                    
                    logger.info(f"✅ Ticket #{resultado['ticket_id']} criado com sucesso")
                    
                else:
                    # Erro no envio
                    erro_msg = resultado.get("erro", "Erro desconhecido")
                    detalhes = resultado.get("detalhes", [])
                    
                    if detalhes:
                        erro_completo = f"{erro_msg}\\n\\nDetalhes:\\n" + "\\n".join(detalhes)
                    else:
                        erro_completo = erro_msg
                    
                    self._mostrar_erro(f"Erro ao criar ticket:\\n{erro_completo}")
                    logger.error(f"❌ Erro ao criar ticket: {erro_msg}")
                
            except Exception as ex:
                # Erro geral
                self._ativar_modo_envio(False)
                erro_msg = f"Erro interno: {str(ex)}"
                self._mostrar_erro(erro_msg)
                logger.error(f"❌ Erro crítico no envio: {ex}")
        
        # Executa em thread
        thread = threading.Thread(target=processar_envio, daemon=True)
        thread.start()
    
    def _cancelar(self, e):
        """Cancela e fecha o modal"""
        self._fechar_modal()
    
    def _fechar_modal(self):
        """Fecha o modal e limpa dados"""
        if self.modal:
            self.modal.open = False
            self.page.update()
        
        # Limpa dados
        self.arquivos_selecionados.clear()
        self.processando = False
        
        # Remove file picker
        if self.file_picker and self.file_picker in self.page.overlay:
            self.page.overlay.remove(self.file_picker)
    
    def mostrar(self, usuario_logado: str = ""):
        """Mostra o modal de report"""
        try:
            # Cria e mostra modal
            modal = self.criar_modal(usuario_logado)
            self.page.dialog = modal
            modal.open = True
            self.page.update()
            
            logger.info(f"🎫 Modal de report aberto para: {usuario_logado or 'usuário não logado'}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar modal de report: {e}")
            mostrar_mensagem(self.page, "❌ Erro ao abrir formulário de report", "error")


# Funções de conveniência
def mostrar_dialog_report(page: ft.Page, usuario_logado: str = ""):
    """Função rápida para mostrar dialog de report"""
    dialog = ReportDialog(page)
    dialog.mostrar(usuario_logado)


def criar_botao_report(page: ft.Page, usuario_logado: str = "", 
                      texto: str = "Reportar Problema", 
                      icone = ft.icons.BUG_REPORT) -> ft.ElevatedButton:
    """Cria botão para abrir dialog de report"""
    def abrir_report(e):
        mostrar_dialog_report(page, usuario_logado)
    
    return ft.ElevatedButton(
        texto,
        icon=icone,
        on_click=abrir_report,
        bgcolor=ft.colors.ORANGE_600,
        color=ft.colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )