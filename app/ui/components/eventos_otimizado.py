"""
Versão otimizada do gerenciador de eventos - sem flicker
"""
import flet as ft
import pandas as pd
import re
from datetime import datetime
from ...core.session_state import get_session_state
from ...services.evento_processor import EventoProcessor
from ...utils.ui_utils import get_screen_size


class EventosManagerOtimizado:
    """Gerenciador de eventos otimizado sem recarregamento da página"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.cards_eventos = {}  # Cache dos cards criados
        
    def criar_lista_eventos(self):
        """Cria a lista de eventos"""
        eventos_content = []
        
        # Filtra dados por usuário
        df_filtrado = self._filtrar_dados_por_usuario()
        
        if df_filtrado.empty:
            # Sem eventos para mostrar
            eventos_content.append(
                ft.Container(
                    content=ft.Column([
                        ft.Image(
                            src="images/sem_tratativas.svg",
                            width=200,
                            height=200,
                            fit=ft.ImageFit.CONTAIN
                        ),
                        ft.Container(height=20),
                        ft.Text(
                            "Não há desvios para serem tratados", 
                            size=24, 
                            weight=ft.FontWeight.BOLD, 
                            color=ft.colors.GREY_700
                        ),
                        ft.Text(
                            "Todos os eventos estão em dia!", 
                            size=16, 
                            color=ft.colors.GREY_500
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=50,
                    alignment=ft.alignment.center
                )
            )
        else:
            # Ordena eventos por data
            if "Titulo" in df_filtrado.columns:
                eventos_unicos = sorted(
                    df_filtrado["Titulo"].unique(), 
                    key=self._extrair_data_titulo
                )
            else:
                eventos_unicos = []
            
            # Cria cards para cada evento
            for evento in eventos_unicos:
                df_evento = df_filtrado[df_filtrado["Titulo"] == evento]
                try:
                    card = self._criar_card_evento_otimizado(evento, df_evento)
                    if card:
                        eventos_content.append(card)
                        # Armazena referência do card
                        self.cards_eventos[evento] = card
                except Exception:
                    continue
        
        return ft.ListView(
            eventos_content, 
            spacing=5, 
            padding=ft.padding.all(10),
            auto_scroll=False,
            expand=True
        )
    
    def _filtrar_dados_por_usuario(self):
        session = get_session_state(self.page)
        """Filtra dados baseado no perfil e áreas do usuário"""
        # Filtra dados não aprovados
        df_nao_aprovados = session.df_desvios[
            session.df_desvios["Status"].ne("Aprovado")
        ] if "Status" in session.df_desvios.columns else session.df_desvios
        
        perfil = session.get_perfil_usuario()
        areas = session.get_areas_usuario()
        
        # Se não é aprovador nem torre, filtrar por área
        if perfil not in ("aprovador", "torre"):
            df_filtrado = pd.DataFrame()
            
            for _, row in df_nao_aprovados.iterrows():
                evento_titulo = row.get("Titulo", "")
                if evento_titulo:
                    try:
                        evento_info = EventoProcessor.parse_titulo_completo(evento_titulo)
                        poi_amigavel = evento_info["poi_amigavel"]
                        
                        # Verificar acesso ao POI
                        if EventoProcessor.validar_acesso_usuario(poi_amigavel, areas):
                            df_filtrado = pd.concat([df_filtrado, row.to_frame().T], ignore_index=True)
                    except Exception:
                        continue
            
            return df_filtrado
        
        return df_nao_aprovados
    
    def _extrair_data_titulo(self, titulo):
        """Extrai data do título para ordenação"""
        m = re.search(r'_(\d{2})(\d{2})(\d{4})_(\d{2})(\d{2})(\d{2})', titulo)
        if m:
            dia, mes, ano, hora, minuto, segundo = m.groups()
            return datetime(int(ano), int(mes), int(dia), int(hora), int(minuto), int(segundo))
        return datetime.max
    
    def _criar_card_evento_otimizado(self, evento, df_evento):
        session = get_session_state(self.page)
        """Cria card individual para um evento com expansão otimizada"""
        # Parse do título
        evento_info = EventoProcessor.parse_titulo_completo(evento)
        tipo_amigavel = evento_info["tipo_amigavel"]
        poi_amigavel = evento_info["poi_amigavel"]
        datahora_fmt = evento_info["datahora_fmt"]
        
        # Verifica acesso do usuário
        perfil = session.get_perfil_usuario()
        areas = session.get_areas_usuario()
        
        if perfil not in ("aprovador", "torre"):
            if not EventoProcessor.validar_acesso_usuario(poi_amigavel, areas):
                return None
        
        # Determina status
        status = df_evento["Status"].iloc[0] if "Status" in df_evento.columns else "Pendente"
        
        if status == "Preenchido":
            status_texto = "Aguardando aprovação"
            status_cor = ft.colors.ORANGE_600
        elif status == "Reprovado":
            status_texto = "Reprovado - Preencha novamente"
            status_cor = ft.colors.PURPLE_600
        else:
            status_texto = "Aguardando preenchimento"
            status_cor = ft.colors.RED_600
        
        # Ícone do evento
        icones_eventos = {
            "Alerta Informativo": "info.png",
            "Tratativa N1": "N1.png",
            "Tratativa N2": "N2.png",
            "Tratativa N3": "N3.png",
            "Tratativa N4": "N4.png"
        }
        icone_arquivo = icones_eventos.get(tipo_amigavel, "info.png")
        
        # Estado de expansão
        if evento not in session.estado_expansao:
            session.estado_expansao[evento] = False
        
        # Container para conteúdo expansível (criado uma vez)
        conteudo_expansivel_container = ft.Container(
            visible=session.estado_expansao[evento],
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        )
        
        # Atualiza conteúdo se expandido
        if session.estado_expansao[evento]:
            conteudo_expansivel_container.content = self._criar_conteudo_expansivel(evento, df_evento)
        
        # Função otimizada para alternar expansão
        def alternar_expansao_otimizada(e):
            # Alterna estado
            session.estado_expansao[evento] = not session.estado_expansao[evento]
            
            # Atualiza ícone
            icone_button = e.control
            if session.estado_expansao[evento]:
                icone_button.icon = ft.icons.KEYBOARD_ARROW_DOWN
                # Cria conteúdo da tabela
                conteudo_expansivel_container.content = self._criar_conteudo_expansivel(evento, df_evento)
            else:
                icone_button.icon = ft.icons.KEYBOARD_ARROW_RIGHT
                # Remove conteúdo para economizar memória
                conteudo_expansivel_container.content = None
            
            # Mostra/esconde container
            conteudo_expansivel_container.visible = session.estado_expansao[evento]
            
            # Atualiza apenas este card (sem recarregar página)
            self.page.update()
        
        # Ícone de expansão inicial
        icone_expansao = ft.icons.KEYBOARD_ARROW_DOWN if session.estado_expansao[evento] else ft.icons.KEYBOARD_ARROW_RIGHT
        
        # Lado esquerdo do header
        lado_esquerdo = ft.Row([
            ft.IconButton(
                icon=icone_expansao, 
                on_click=alternar_expansao_otimizada, 
                tooltip="Expandir/Encolher"
            ),
            ft.Row([
                ft.Image(
                    src=f"images/{icone_arquivo}", 
                    width=18, 
                    height=18, 
                    fit=ft.ImageFit.CONTAIN
                ),
                ft.Text(
                    f"{tipo_amigavel} - {poi_amigavel} - {datahora_fmt}", 
                    size=14, 
                    weight=ft.FontWeight.BOLD
                )
            ], spacing=8)
        ], spacing=5)
        
        # Lado direito do header
        if status == "Reprovado":
            lado_direito = ft.Row([
                ft.Text(status_texto, color=status_cor, weight=ft.FontWeight.BOLD, size=13),
                ft.IconButton(
                    icon=ft.icons.INFO_OUTLINE,
                    tooltip="Ver motivo da reprovação",
                    on_click=lambda e: self._mostrar_justificativa_reprovacao(df_evento),
                    icon_color=ft.colors.PURPLE_600,
                    bgcolor=ft.colors.PURPLE_50,
                    style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=4)
                )
            ], spacing=5)
        else:
            lado_direito = ft.Text(status_texto, color=status_cor, weight=ft.FontWeight.BOLD, size=13)
        
        # Header do card
        header = ft.Container(
            content=ft.Row([
                lado_esquerdo, 
                lado_direito
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=3, 
            bgcolor=ft.colors.RED_50,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            container_width = 1200
        elif screen_size == "medium":
            container_width = 1300
        else:
            container_width = 1400
        
        # Container final otimizado
        container_final = ft.Container(
            content=ft.Column([
                header, 
                conteudo_expansivel_container
            ]),
            margin=ft.margin.only(bottom=8),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1, 
                blur_radius=5, 
                color=ft.colors.BLACK12
            ),
            width=container_width
        )
        
        return container_final
    
    def _criar_conteudo_expansivel(self, evento, df_evento):
        """Cria conteúdo expansível do evento"""
        from .tabela_justificativas import TabelaJustificativas
        
        # Cria tabela de justificativas
        tabela_component = TabelaJustificativas(self.page, self.app_controller)
        return tabela_component.criar_tabela(evento, df_evento)
    
    def _mostrar_justificativa_reprovacao(self, df_evento):
        """Mostra justificativa de reprovação em modal"""
        def limpar_texto_html(texto_html: str) -> str:
            """Remove tags HTML e decodifica entidades HTML"""
            import html
            import re
            
            if not texto_html:
                return ""
            
            # Remove tags HTML comuns
            texto = re.sub(r'<div[^>]*>', '', texto_html)
            texto = re.sub(r'</div>', '\n', texto)
            texto = re.sub(r'<br\s*/?>', '\n', texto)
            texto = re.sub(r'<p[^>]*>', '', texto)
            texto = re.sub(r'</p>', '\n\n', texto)
            texto = re.sub(r'<[^>]+>', '', texto)
            
            # Decodifica entidades HTML
            texto = html.unescape(texto)
            
            # Limpa espaços extras
            texto = re.sub(r'\n\s*\n', '\n\n', texto)
            texto = re.sub(r'^\s+|\s+$', '', texto)
            
            return texto
        
        justificativa = ""
        if "Reprova" in df_evento.columns:
            primeira_justificativa = df_evento["Reprova"].iloc[0]
            if pd.notnull(primeira_justificativa) and str(primeira_justificativa).strip():
                justificativa = str(primeira_justificativa).strip()
        
        if not justificativa:
            justificativa = "Justificativa não informada"
        else:
            justificativa = limpar_texto_html(justificativa)
        
        def fechar_modal_justificativa():
            modal_justificativa.open = False
            self.page.update()
        
        modal_justificativa = ft.AlertDialog(
            modal=True,
            title=ft.Text("Motivo da Reprovação", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Text(
                    justificativa, 
                    size=14, 
                    selectable=True,
                    max_lines=None,
                    overflow=ft.TextOverflow.VISIBLE,
                    text_align=ft.TextAlign.LEFT
                ),
                width=450, 
                height=200, 
                padding=15
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: fechar_modal_justificativa())
            ],
            shape=ft.RoundedRectangleBorder(radius=4)
        )
        
        self.page.dialog = modal_justificativa
        modal_justificativa.open = True
        self.page.update()