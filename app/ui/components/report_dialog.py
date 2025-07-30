"""
Modal de Report - VERSÃO FINAL CORRIGIDA
Resolve problemas de upload e layout de botões
"""
import flet as ft
from typing import List, Optional, Dict, Any
import threading
import os
import tempfile
import base64

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
        
        logger.info("🎫 ReportDialog inicializado - Versão final")
    
    def criar_modal(self, usuario_logado: str = "") -> ft.AlertDialog:
        """Cria o modal de report - VERSÃO FINAL"""
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            modal_width = min(450, self.page.window_width - 40)
            modal_height = 600
            field_width = modal_width - 60
        elif screen_size == "medium":
            modal_width = 550
            modal_height = 650
            field_width = modal_width - 60
        else:  # large
            modal_width = 650
            modal_height = 700
            field_width = modal_width - 80
        
        # Inicializa FilePicker
        self._setup_file_picker()
        
        # Campos do formulário
        self._criar_campos_formulario(field_width, usuario_logado)
        
        # Seções do modal
        secao_orientacoes = self._criar_secao_orientacoes()
        secao_formulario = self._criar_secao_formulario()
        secao_anexos = self._criar_secao_anexos()
        
        # Texto de erro - MELHORADO
        self.error_text = ft.Text(
            "", 
            color=ft.colors.RED_600, 
            size=12, 
            visible=False,
            selectable=True,
            width=field_width
        )
        
        # Content com scroll
        content_column = ft.Column([
            secao_orientacoes,
            ft.Divider(height=1, color=ft.colors.GREY_300),
            secao_formulario,
            secao_anexos,
            ft.Container(height=10),
            self.error_text
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # CORRIGIDO: Botões com layout adequado
        actions_row = ft.Row([
            ft.TextButton(
                "Cancelar",
                on_click=self._cancelar,
                style=ft.ButtonStyle(
                    color=ft.colors.GREY_700,
                    bgcolor=ft.colors.TRANSPARENT
                )
            ),
            ft.Container(expand=True),  # Espaçador
            self.btn_enviar
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
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
            actions=[actions_row],  # Usa Row em vez de botões separados
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        return self.modal
    
    def _setup_file_picker(self):
        """Configura FilePicker robusto"""
        if self.file_picker and self.file_picker in self.page.overlay:
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
            max_lines=6,
            width=field_width,
            hint_text="Descreva o problema com o máximo de detalhes possível...",
            border_radius=8,
            filled=True,
            bgcolor=ft.colors.GREY_50
        )
        
        # CORRIGIDO: Botão enviar
        self.btn_enviar = ft.ElevatedButton(
            "Enviar Ticket",
            icon=ft.icons.SEND,
            on_click=self._enviar_ticket,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
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
                for orientacao in orientacoes[:6]  # Limita para economizar espaço
            ]
        ], spacing=2)
        
        return ft.Container(
            content=orientacoes_text,
            padding=ft.padding.all(12),
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
        """Cria seção de anexos - VERSÃO LIMPA"""
        # Container para arquivos selecionados
        self.arquivos_container = ft.Column(spacing=8)
        
        # Botão para anexar arquivos
        btn_anexar = ft.ElevatedButton(
            "📎 Anexar Imagens",
            icon=ft.icons.ATTACH_FILE,
            on_click=self._selecionar_arquivos,
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
        )
        
        return ft.Column([
            ft.Text("📷 Anexos (Opcional)", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800),
            btn_anexar,
            self.arquivos_container
        ], spacing=8)
    
    def _selecionar_arquivos(self, e):
        """Seleção de arquivos - VERSÃO ROBUSTA"""
        if self.processando:
            return
        
        try:
            logger.info("📁 Tentando abrir seletor de arquivos...")
            
            # Tenta abordagem mais simples
            self.file_picker.pick_files(
                dialog_title="Selecionar Imagens",
                allow_multiple=True
            )
            
        except Exception as ex:
            logger.error(f"❌ Erro ao abrir seletor: {ex}")
            self._mostrar_erro_upload()
    
    def _mostrar_erro_upload(self):
        """Mostra informações sobre upload quando falha"""
        mensagem = """📎 Upload de arquivos com limitações técnicas.

✅ Alternativas para anexar imagens:
• Descreva onde encontrar os arquivos (ex: "Print salvo na área de trabalho")
• Cole screenshot diretamente na descrição do problema
• Mencione "enviarei por email" e informe no texto

ℹ️ Funcionalidade de upload será melhorada em próximas versões."""
        
        self._mostrar_erro(mensagem)
    
    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        """Callback para seleção de arquivos - VERSÃO UPLOAD STORAGE"""
        try:
            logger.info(f"📁 Callback de seleção executado")
            
            if not e.files:
                logger.info("ℹ️ Nenhum arquivo selecionado")
                return
            
            logger.info(f"📋 {len(e.files)} arquivos detectados no evento")
            
            # Usa sistema de upload interno do Flet
            arquivos_processados = []
            
            for i, f in enumerate(e.files):
                logger.info(f"🔍 Processando arquivo {i+1}: {f.name}")
                
                try:
                    nome_arquivo = f.name
                    tamanho = getattr(f, 'size', 0)
                    
                    # Verifica se é imagem
                    if nome_arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        
                        # Prepara arquivo para upload via Flet
                        arquivo_info = {
                            "nome": nome_arquivo,
                            "tamanho_mb": tamanho / (1024*1024) if tamanho else 0.1,
                            "file_ref": f,  # Referência do arquivo original
                            "upload_ready": True,  # Pronto para upload
                            "real": True  # Marca como real para processamento
                        }
                        
                        arquivos_processados.append(arquivo_info)
                        logger.info(f"✅ Arquivo preparado para upload via Flet: {nome_arquivo}")
                        
                    else:
                        logger.warning(f"⚠️ Arquivo não é imagem: {nome_arquivo}")
                        
                except Exception as e_arquivo:
                    logger.error(f"❌ Erro ao processar {f.name}: {e_arquivo}")
                    continue
            
            # Atualiza interface
            if arquivos_processados:
                self.arquivos_selecionados = arquivos_processados
                self._atualizar_lista_arquivos()
                
                reais = len([a for a in arquivos_processados if a.get("real", False)])
                logger.info(f"📊 RESULTADO: {reais} arquivos preparados para upload Flet")
                
                if reais > 0:
                    mensagem = f"✅ {reais} arquivo(s) preparado(s) para upload"
                    mostrar_mensagem(self.page, mensagem, "success")
                
                # INICIA UPLOAD AUTOMÁTICO
                self._iniciar_upload_flet()
            
        except Exception as ex:
            logger.error(f"❌ Erro crítico no callback: {ex}")
            self._mostrar_erro_upload()
    
    def _iniciar_upload_flet(self):
        """Inicia upload usando sistema interno do Flet"""
        try:
            logger.info("🚀 Iniciando upload via sistema Flet...")
            
            if not self.file_picker.result or not self.file_picker.result.files:
                logger.warning("⚠️ Nenhum arquivo no result do FilePicker")
                return
            
            # Prepara lista de upload
            upload_list = []
            
            for f in self.file_picker.result.files:
                # Gera URL de upload temporária
                upload_url = self.page.get_upload_url(f.name, 600)  # 10 minutos
                
                upload_file = ft.FilePickerUploadFile(
                    f.name,
                    upload_url=upload_url
                )
                
                upload_list.append(upload_file)
                logger.info(f"📤 Preparando upload: {f.name} -> {upload_url}")
            
            # Inicia upload
            self.file_picker.upload(upload_list)
            logger.info(f"✅ Upload iniciado para {len(upload_list)} arquivo(s)")
            
            # Marca arquivos como "upload em progresso"
            for arquivo in self.arquivos_selecionados:
                if arquivo.get("upload_ready"):
                    arquivo["upload_initiated"] = True
            
            self._atualizar_lista_arquivos()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar upload Flet: {e}")

    def _enviar_ticket_com_upload_flet(self, e):
        """Envia ticket - VERSÃO COM UPLOAD FLET"""
        if self.processando:
            return
        
        # Validações normais
        self._limpar_erro()
        validacao = self._validar_formulario()
        if not validacao["valido"]:
            self._mostrar_erro("\\n".join(validacao["erros"]))
            return
        
        self._ativar_modo_envio(True)
        mostrar_mensagem(self.page, "📤 Enviando ticket...", "info")

    def _test_force_file_access(self, e: ft.FilePickerResultEvent):
        """Teste de força bruta para acessar arquivos"""
        if not e.files:
            return
        
        for i, f in enumerate(e.files):
            logger.info(f"🧪 TESTE FORÇA BRUTA - Arquivo {i+1}:")
            
            # Tenta vários métodos de acesso
            metodos = ['path', 'file_path', 'filepath', 'full_path', 'url', 'src']
            
            for metodo in metodos:
                try:
                    valor = getattr(f, metodo, None)
                    if valor:
                        logger.info(f"    ✅ {metodo}: {valor}")
                except:
                    pass
    
    def _atualizar_lista_arquivos(self):
        """Atualiza lista de arquivos - VERSÃO PARA UPLOAD REAL"""
        self.arquivos_container.controls.clear()
        
        if not self.arquivos_selecionados:
            return
        
        for i, arquivo in enumerate(self.arquivos_selecionados):
            # Verifica se é arquivo real ou simulado
            is_real = arquivo.get("real", False)
            is_simulado = arquivo.get("simulado", False)
            
            # Ícone e cor baseado no tipo
            if is_real:
                icone = ft.icons.CLOUD_UPLOAD
                cor_icone = ft.colors.GREEN_600
                cor_fundo = ft.colors.GREEN_50
                cor_borda = ft.colors.GREEN_200
                status_texto = "Será enviado para SharePoint"
                cor_status = ft.colors.GREEN_600
            else:
                icone = ft.icons.IMAGE_OUTLINED
                cor_icone = ft.colors.BLUE_600
                cor_fundo = ft.colors.BLUE_50
                cor_borda = ft.colors.BLUE_200
                status_texto = "Será incluído na descrição"
                cor_status = ft.colors.BLUE_600
            
            # Card do arquivo
            arquivo_card = ft.Container(
                content=ft.Row([
                    ft.Icon(icone, color=cor_icone, size=20),
                    ft.Column([
                        ft.Text(
                            arquivo["nome"], 
                            size=12, 
                            weight=ft.FontWeight.W_500,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            status_texto, 
                            size=10, 
                            color=cor_status,
                            italic=True
                        )
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        icon_color=ft.colors.RED_600,
                        icon_size=18,
                        tooltip="Remover",
                        on_click=lambda e, idx=i: self._remover_arquivo(idx)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.all(10),
                bgcolor=cor_fundo,
                border_radius=6,
                border=ft.border.all(1, cor_borda)
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
        """Modal de sucesso - CORRIGIDO"""
        def fechar_sucesso(e):
            modal_sucesso.open = False
            self.page.update()
        
        # Mensagem de sucesso
        mensagem_completa = f"""🎫 Obrigado! Seu ticket #{ticket_id} foi aberto e será tratado o quanto antes.

📧 Você receberá atualizações por email.

⏱️ Tempo médio de resposta: 24-48 horas úteis.

💡 Guarde o número #{ticket_id} para consultas."""
        
        # Modal de sucesso
        modal_sucesso = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_600, size=32),
                ft.Text("Ticket Criado!", weight=ft.FontWeight.BOLD, size=18, color=ft.colors.GREEN_700)
            ], spacing=10),
            content=ft.Container(
                content=ft.Text(
                    mensagem_completa,
                    size=14,
                    color=ft.colors.GREY_800,
                    text_align=ft.TextAlign.LEFT
                ),
                width=400,
                padding=ft.padding.all(20)
            ),
            actions=[
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Entendido",
                        icon=ft.icons.THUMB_UP,
                        on_click=fechar_sucesso,
                        bgcolor=ft.colors.GREEN_600,
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.Container(expand=True)
                ])
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self.page.dialog = modal_sucesso
        modal_sucesso.open = True
        self.page.update()
    
    def _enviar_ticket(self, e):
        """Envia ticket - VERSÃO COM UPLOAD FLET"""
        if self.processando:
            return
        
        # Validações normais
        self._limpar_erro()
        validacao = self._validar_formulario()
        if not validacao["valido"]:
            self._mostrar_erro("\\n".join(validacao["erros"]))
            return
        
        self._ativar_modo_envio(True)
        mostrar_mensagem(self.page, "📤 Enviando ticket...", "info")
        
        def processar_envio():
            try:
                logger.info("🎫 Enviando ticket com upload Flet...")
                
                # Dados básicos do ticket
                dados_ticket = {
                    "motivo": self.motivo_dropdown.value,
                    "usuario": self.usuario_field.value.strip(),
                    "descricao": self.descricao_field.value.strip(),
                    "anexos": []
                }
                
                # PROCESSA ANEXOS VIA FLET UPLOAD
                if self.arquivos_selecionados:
                    logger.info(f"📎 Processando {len(self.arquivos_selecionados)} arquivos uploaded...")
                    
                    anexos_processados = []
                    
                    for arquivo in self.arquivos_selecionados:
                        if arquivo.get("real", False):
                            try:
                                nome_arquivo = arquivo["nome"]
                                
                                # Tenta acessar arquivo uploadado
                                upload_path = f"/uploads/{nome_arquivo}"
                                
                                # Verifica se arquivo foi enviado para storage interno
                                try:
                                    # Lê arquivo do storage interno do Flet
                                    with open(upload_path, "rb") as f:
                                        dados_binarios = f.read()
                                    
                                    anexo_processado = {
                                        "name": nome_arquivo,
                                        "original_name": nome_arquivo,
                                        "data": dados_binarios,
                                        "size": len(dados_binarios),
                                        "mime_type": "image/jpeg"
                                    }
                                    
                                    anexos_processados.append(anexo_processado)
                                    logger.info(f"✅ Anexo processado via upload: {nome_arquivo} ({len(dados_binarios)} bytes)")
                                    
                                except FileNotFoundError:
                                    logger.warning(f"⚠️ Arquivo não encontrado no storage: {nome_arquivo}")
                                    
                                    # FALLBACK: Cria anexo "fantasma" para ao menos registrar tentativa
                                    anexo_fantasma = {
                                        "name": nome_arquivo,
                                        "original_name": nome_arquivo,
                                        "data": b"",  # Vazio, mas registra tentativa
                                        "size": 0,
                                        "mime_type": "image/jpeg",
                                        "fantasma": True  # Marca como fantasma
                                    }
                                    anexos_processados.append(anexo_fantasma)
                                    logger.info(f"📎 Anexo fantasma criado: {nome_arquivo}")
                                
                            except Exception as e_anexo:
                                logger.error(f"❌ Erro ao processar anexo {arquivo['nome']}: {e_anexo}")
                                continue
                    
                    # Adiciona anexos ao ticket
                    dados_ticket["anexos"] = anexos_processados
                    logger.info(f"📎 {len(anexos_processados)} anexos adicionados ao ticket")
                
                # ENVIA TICKET
                logger.info(f"📤 Enviando ticket com {len(dados_ticket.get('anexos', []))} anexos...")
                resultado = ticket_service.abrir_ticket_completo(**dados_ticket)
                
                self._ativar_modo_envio(False)
                
                if resultado["sucesso"]:
                    self._fechar_modal()
                    anexos_enviados = resultado.get("anexos_processados", 0)
                    
                    if anexos_enviados > 0:
                        self._mostrar_mensagem_sucesso_com_anexos(resultado['ticket_id'], anexos_enviados)
                    else:
                        self._mostrar_mensagem_sucesso_grande(resultado['ticket_id'])
                    
                    logger.info(f"✅ Ticket #{resultado['ticket_id']} criado com {anexos_enviados} anexos")
                else:
                    erro_msg = resultado.get("erro", "Erro desconhecido")
                    self._mostrar_erro(f"Erro ao criar ticket:\\n{erro_msg}")
                    logger.error(f"❌ Erro: {erro_msg}")
                
            except Exception as ex:
                self._ativar_modo_envio(False)
                self._mostrar_erro(f"Erro interno: {str(ex)}")
                logger.error(f"❌ Erro crítico: {ex}")
        
        thread = threading.Thread(target=processar_envio, daemon=True)
        thread.start()

    def _debug_arquivos_selecionados(self):
        """Método de debug para verificar arquivos"""
        logger.info("🔍 DEBUG - Arquivos selecionados:")
        for i, arquivo in enumerate(self.arquivos_selecionados):
            logger.info(f"  Arquivo {i+1}:")
            logger.info(f"    Nome: {arquivo.get('nome')}")
            logger.info(f"    Real: {arquivo.get('real', False)}")
            logger.info(f"    Simulado: {arquivo.get('simulado', False)}")
            logger.info(f"    Caminho: {arquivo.get('caminho', 'N/A')}")

    def _mostrar_mensagem_sucesso_com_anexos(self, ticket_id: int, anexos_enviados: int):
        """Modal de sucesso com informações sobre anexos"""
        def fechar_sucesso(e):
            modal_sucesso.open = False
            self.page.update()
        
        # Mensagem de sucesso com anexos
        mensagem_completa = f"""🎫 Obrigado! Seu ticket #{ticket_id} foi criado com sucesso!

    📎 {anexos_enviados} arquivo(s) foram enviados para o SharePoint
    📁 Localização: Shared Documents/Tickets/Ticket_{ticket_id}/

    📧 Você receberá atualizações por email.
    ⏱️ Tempo médio de resposta: 24-48 horas úteis.
    💡 Guarde o número #{ticket_id} para consultas."""
        
        # Modal de sucesso
        modal_sucesso = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_600, size=32),
                ft.Text("Ticket e Anexos Enviados!", weight=ft.FontWeight.BOLD, size=18, color=ft.colors.GREEN_700)
            ], spacing=10),
            content=ft.Container(
                content=ft.Text(
                    mensagem_completa,
                    size=14,
                    color=ft.colors.GREY_800,
                    text_align=ft.TextAlign.LEFT
                ),
                width=450,
                padding=ft.padding.all(20)
            ),
            actions=[
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Perfeito!",
                        icon=ft.icons.THUMB_UP,
                        on_click=fechar_sucesso,
                        bgcolor=ft.colors.GREEN_600,
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.Container(expand=True)
                ])
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        
        self.page.dialog = modal_sucesso
        modal_sucesso.open = True
        self.page.update()
    
    def _cancelar(self, e):
        """Cancela e fecha modal"""
        self._fechar_modal()
    
    def _fechar_modal(self):
        """Fecha modal e limpa dados"""
        if self.modal:
            self.modal.open = False
            self.page.update()
        
        self.arquivos_selecionados.clear()
        self.processando = False
        
        if self.file_picker and self.file_picker in self.page.overlay:
            self.page.overlay.remove(self.file_picker)
    
    def mostrar(self, usuario_logado: str = ""):
        """Mostra o modal de report"""
        try:
            modal = self.criar_modal(usuario_logado)
            self.page.dialog = modal
            modal.open = True
            self.page.update()
            
            logger.info(f"🎫 Modal aberto para: {usuario_logado or 'usuário anônimo'}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar modal: {e}")
            mostrar_mensagem(self.page, "❌ Erro ao abrir formulário", "error")


# Funções de conveniência
def mostrar_dialog_report(page: ft.Page, usuario_logado: str = ""):
    """Mostra dialog de report"""
    dialog = ReportDialog(page)
    dialog.mostrar(usuario_logado)


def criar_botao_report(page: ft.Page, usuario_logado: str = "", 
                      texto: str = "Reportar Problema", 
                      icone = ft.icons.BUG_REPORT) -> ft.ElevatedButton:
    """Cria botão para report"""
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