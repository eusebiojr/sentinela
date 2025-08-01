"""
Componente de Visualização Admin - Sistema Sentinela
Visualização completa de desvios com filtros avançados para perfis Admin/Torre
"""
import flet as ft
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ...core.session_state import get_session_state
from ...services.evento_processor import EventoProcessor
from ...utils.ui_utils import get_screen_size, mostrar_mensagem

# Imports opcionais para funcionalidades extras
try:
    from ...services.data_formatter import DataFormatter
    DATA_FORMATTER_AVAILABLE = True
except ImportError:
    DATA_FORMATTER_AVAILABLE = False
    DataFormatter = None

try:
    from ...validators import field_validator, business_validator
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    field_validator = None
    business_validator = None


class AdminVisualizacao:
    """Componente de visualização admin com filtros avançados"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.df_filtrado = pd.DataFrame()
        self.filtros_ativos = {
            "data_inicio": None,
            "data_fim": None,
            "status": [],
            "usuario_preenchimento": None,
            "usuario_aprovacao": None,
            "motivos": [],
            "observacao_busca": ""
        }
        
        # Componentes de filtro
        self.data_inicio_field = None
        self.data_fim_field = None
        self.status_dropdown = None
        self.usuario_preench_dropdown = None
        self.usuario_aprov_dropdown = None
        self.motivos_dropdown = None
        self.observacao_field = None
        self.contador_registros = None
        self.tabela_resultados = None
        
    def criar_interface(self):
        """Cria interface completa da visualização admin"""
        session = get_session_state(self.page)
        
        # Verifica permissão
        perfil = session.get_perfil_usuario()
        if perfil not in ("admin", "torre"):
            return ft.Container(
                content=ft.Text(
                    "❌ Acesso negado. Esta funcionalidade é exclusiva para perfis Admin/Torre.",
                    size=16,
                    color=ft.colors.RED_600,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=50,
                alignment=ft.alignment.center
            )
        
        # Prepara dados iniciais
        self._preparar_dados_iniciais()
        
        return ft.Column([
            self._criar_header(),
            self._criar_secao_filtros(),
            self._criar_contador_exportacao(),
            self._criar_tabela_resultados()
        ], spacing=20, expand=True)
    
    def _criar_header(self):
        """Cria header da página admin"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS, size=28, color=ft.colors.BLUE_600),
                ft.Text(
                    "Visualização Administrativa - Todos os Desvios",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_800
                )
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=ft.colors.BLUE_50,
            border_radius=10,
            border=ft.border.all(1, ft.colors.BLUE_200)
        )
    
    def _criar_secao_filtros(self):
        """Cria seção completa de filtros"""
        screen_size = get_screen_size(self.page.window_width)
        
        # Filtros de data
        filtros_data = self._criar_filtros_data()
        
        # Filtros de status e usuários
        filtros_status_usuarios = self._criar_filtros_status_usuarios()
        
        # Filtros de motivos e observações
        filtros_motivos_obs = self._criar_filtros_motivos_observacoes()
        
        # Botões de ação
        botoes_acao = self._criar_botoes_filtros()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("🔍 Filtros Avançados", size=18, weight=ft.FontWeight.BOLD),
                filtros_data,
                filtros_status_usuarios,
                filtros_motivos_obs,
                botoes_acao
            ], spacing=15),
            padding=20,
            bgcolor=ft.colors.GREY_50,
            border_radius=10,
            border=ft.border.all(1, ft.colors.GREY_300)
        )
    
    def _criar_filtros_data(self):
        """Cria filtros de data de criação"""
        # Data início
        self.data_inicio_field = ft.DatePicker(
            first_date=datetime(2024, 1, 1),
            last_date=datetime.now(),
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            on_change=self._on_filtro_mudanca
        )
        
        # Data fim
        self.data_fim_field = ft.DatePicker(
            first_date=datetime(2024, 1, 1),
            last_date=datetime.now(),
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            on_change=self._on_filtro_mudanca
        )
        
        # Campos de exibição
        data_inicio_display = ft.TextField(
            label="Data Início",
            hint_text="Selecione data inicial",
            read_only=True,
            suffix_icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.page.open(self.data_inicio_field),
            width=200
        )
        
        data_fim_display = ft.TextField(
            label="Data Fim", 
            hint_text="Selecione data final",
            read_only=True,
            suffix_icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.page.open(self.data_fim_field),
            width=200
        )
        
        return ft.Row([
            ft.Text("📅 Período:", weight=ft.FontWeight.BOLD, width=100),
            data_inicio_display,
            ft.Text("até", color=ft.colors.GREY_600),
            data_fim_display
        ], spacing=10, alignment=ft.MainAxisAlignment.START)
    
    def _criar_filtros_status_usuarios(self):
        """Cria filtros de status e usuários"""
        # Status dropdown (multiselect)
        opcoes_status = [
            ft.dropdown.Option("Pendente", "Pendente"),
            ft.dropdown.Option("Preenchido", "Preenchido"), 
            ft.dropdown.Option("Aprovado", "Aprovado"),
            ft.dropdown.Option("Reprovado", "Reprovado"),
            ft.dropdown.Option("Não Tratado", "Não Tratado")
        ]
        
        self.status_dropdown = ft.Dropdown(
            label="Status",
            hint_text="Selecione status...",
            options=opcoes_status,
            multiselect=True,
            on_change=self._on_filtro_mudanca,
            width=250
        )
        
        # Usuários dropdowns
        usuarios_disponiveis = self._obter_usuarios_sistema()
        
        self.usuario_preench_dropdown = ft.Dropdown(
            label="Usuário Preenchimento",
            hint_text="Todos os usuários",
            options=[ft.dropdown.Option(user, user) for user in usuarios_disponiveis],
            on_change=self._on_filtro_mudanca,
            width=250
        )
        
        self.usuario_aprov_dropdown = ft.Dropdown(
            label="Usuário Aprovação",
            hint_text="Todos os usuários",
            options=[ft.dropdown.Option(user, user) for user in usuarios_disponiveis],
            on_change=self._on_filtro_mudanca,
            width=250
        )
        
        return ft.Column([
            ft.Row([
                ft.Text("📊 Status:", weight=ft.FontWeight.BOLD, width=100),
                self.status_dropdown
            ], spacing=10),
            ft.Row([
                ft.Text("👥 Usuários:", weight=ft.FontWeight.BOLD, width=100),
                self.usuario_preench_dropdown,
                self.usuario_aprov_dropdown
            ], spacing=10)
        ], spacing=10)
    
    def _criar_filtros_motivos_observacoes(self):
        """Cria filtros de motivos e observações"""
        # Motivos dropdown (multiselect)
        motivos_padronizados = [
            "Chuva", "Quebra Equipamento", "Falta Energia", "Manutenção Programada",
            "Falta Pessoal", "Problema Sistema", "Congestionamento", "Outros"
        ]
        
        self.motivos_dropdown = ft.Dropdown(
            label="Motivos",
            hint_text="Selecione motivos...",
            options=[ft.dropdown.Option(motivo, motivo) for motivo in motivos_padronizados],
            multiselect=True,
            on_change=self._on_filtro_mudanca,
            width=300
        )
        
        # Campo de busca em observações
        self.observacao_field = ft.TextField(
            label="Buscar em Observações",
            hint_text="Digite para buscar nas observações...",
            on_change=self._on_observacao_busca,
            suffix_icon=ft.icons.SEARCH,
            width=400
        )
        
        return ft.Column([
            ft.Row([
                ft.Text("🏷️ Motivos:", weight=ft.FontWeight.BOLD, width=100),
                self.motivos_dropdown
            ], spacing=10),
            ft.Row([
                ft.Text("💭 Observações:", weight=ft.FontWeight.BOLD, width=100),
                self.observacao_field
            ], spacing=10)
        ], spacing=10)
    
    def _criar_botoes_filtros(self):
        """Cria botões de ação dos filtros"""
        return ft.Row([
            ft.ElevatedButton(
                "🔍 Aplicar Filtros",
                on_click=self._aplicar_filtros,
                bgcolor=ft.colors.BLUE_600,
                color=ft.colors.WHITE,
                icon=ft.icons.FILTER_LIST
            ),
            ft.OutlinedButton(
                "🧹 Limpar Filtros",
                on_click=self._limpar_filtros,
                icon=ft.icons.CLEAR_ALL
            ),
            ft.ElevatedButton(
                "🔄 Atualizar Dados",
                on_click=self._atualizar_dados,
                bgcolor=ft.colors.GREEN_600,
                color=ft.colors.WHITE,
                icon=ft.icons.REFRESH
            )
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
    
    def _criar_contador_exportacao(self):
        """Cria seção com contador e botão de exportação"""
        self.contador_registros = ft.Text(
            "📋 Carregando dados...",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_700
        )
        
        botao_exportar = ft.ElevatedButton(
            "📊 Exportar Filtrados",
            on_click=self._exportar_dados,
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            icon=ft.icons.DOWNLOAD,
            disabled=True  # Será habilitado quando houver dados
        )
        
        return ft.Container(
            content=ft.Row([
                self.contador_registros,
                ft.VerticalDivider(width=20),
                botao_exportar
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.colors.BLUE_50,
            border_radius=8
        )
    
    def _criar_tabela_resultados(self):
        """Cria tabela de resultados filtrados"""
        # Header da tabela
        header_row = ft.DataRow([
            ft.DataCell(ft.Text("Data", weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("Tipo", weight=ft.FontWeight.BOLD)), 
            ft.DataCell(ft.Text("POI", weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("Status", weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("Preenchido Por", weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("Aprovado Por", weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("Motivo", weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("Observação", weight=ft.FontWeight.BOLD))
        ])
        
        self.tabela_resultados = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("POI")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Preenchido Por")),
                ft.DataColumn(ft.Text("Aprovado Por")),
                ft.DataColumn(ft.Text("Motivo")),
                ft.DataColumn(ft.Text("Observação"))
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=10,
            data_row_color={ft.MaterialState.HOVERED: ft.colors.GREY_100}
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("📋 Resultados", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.tabela_resultados,
                    height=500,
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.all(1, ft.colors.GREY_300)
                )
            ], spacing=10),
            expand=True
        )
    
    # MÉTODOS DE PROCESSAMENTO
    
    def _preparar_dados_iniciais(self):
        """Prepara dados iniciais da visualização"""
        session = get_session_state(self.page)
        
        # Carrega TODOS os desvios (sem filtros de status)
        if hasattr(session, 'df_desvios') and not session.df_desvios.empty:
            self.df_filtrado = session.df_desvios.copy()
            self._atualizar_contador()
            self._atualizar_tabela()
        else:
            self.df_filtrado = pd.DataFrame()
    
    def _obter_usuarios_sistema(self) -> List[str]:
        """Obtém lista única de usuários do sistema"""
        session = get_session_state(self.page)
        usuarios = set()
        
        if hasattr(session, 'df_desvios') and not session.df_desvios.empty:
            df = session.df_desvios
            
            # Usuários que preencheram
            if "Preenchido_por" in df.columns:
                usuarios.update(df["Preenchido_por"].dropna().unique())
            
            # Usuários que aprovaram
            if "Aprovado_por" in df.columns:
                usuarios.update(df["Aprovado_por"].dropna().unique())
        
        return sorted([user for user in usuarios if user and user.strip()])
    
    def _on_filtro_mudanca(self, e):
        """Handler para mudanças nos filtros"""
        # Atualiza automaticamente quando filtros mudam
        self._aplicar_filtros(None)
    
    def _on_observacao_busca(self, e):
        """Handler para busca em tempo real nas observações"""
        self.filtros_ativos["observacao_busca"] = e.control.value.strip()
        # Aplica filtro com delay para não sobrecarregar
        self._aplicar_filtros_observacao()
    
    def _aplicar_filtros(self, e):
        """Aplica todos os filtros selecionados"""
        session = get_session_state(self.page)
        
        if not hasattr(session, 'df_desvios') or session.df_desvios.empty:
            mostrar_mensagem(self.page, "⚠️ Nenhum dado disponível para filtrar", "warning")
            return
        
        df_original = session.df_desvios.copy()
        
        # Aplica filtros sequencialmente
        df_filtrado = self._aplicar_filtro_datas(df_original)
        df_filtrado = self._aplicar_filtro_status(df_filtrado)
        df_filtrado = self._aplicar_filtro_usuarios(df_filtrado)
        df_filtrado = self._aplicar_filtro_motivos(df_filtrado)
        df_filtrado = self._aplicar_filtro_observacoes(df_filtrado)
        
        self.df_filtrado = df_filtrado
        self._atualizar_contador()
        self._atualizar_tabela()
    
    def _aplicar_filtro_datas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtro de datas de criação - VERSÃO CORRIGIDA"""
        data_inicio = None
        data_fim = None
        
        # Obtém datas dos campos (se existirem)
        if hasattr(self, 'data_inicio_field') and self.data_inicio_field and hasattr(self.data_inicio_field, 'value'):
            data_inicio = self.data_inicio_field.value
        
        if hasattr(self, 'data_fim_field') and self.data_fim_field and hasattr(self.data_fim_field, 'value'):
            data_fim = self.data_fim_field.value
        
        # Se não há filtros de data, retorna DataFrame original
        if not data_inicio and not data_fim:
            return df
        
        # Função para extrair data do título
        def extrair_data_titulo(titulo: str):
            """Extrai data do título do evento"""
            try:
                if not titulo:
                    return None
                    
                evento_info = EventoProcessor.parse_titulo_completo(titulo)
                data_evento = evento_info.get("data_evento")
                
                if data_evento and hasattr(data_evento, 'date'):
                    return data_evento.date()
                return None
            except Exception:
                return None
        
        # Aplica o filtro se há coluna Titulo
        if "Titulo" in df.columns:
            df_com_data = df.copy()
            df_com_data["Data_Extraida"] = df_com_data["Titulo"].apply(extrair_data_titulo)
            
            # Remove registros sem data válida
            df_com_data = df_com_data[df_com_data["Data_Extraida"].notnull()]
            
            # Aplica filtro de data início
            if data_inicio:
                df_com_data = df_com_data[df_com_data["Data_Extraida"] >= data_inicio]
            
            # Aplica filtro de data fim
            if data_fim:
                df_com_data = df_com_data[df_com_data["Data_Extraida"] <= data_fim]
            
            # Remove coluna temporária
            df_com_data = df_com_data.drop(columns=["Data_Extraida"])
            
            return df_com_data
        
        return df
    
    def _aplicar_filtro_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtro de status"""
        if self.status_dropdown and self.status_dropdown.value:
            status_selecionados = self.status_dropdown.value
            if status_selecionados and "Status" in df.columns:
                df = df[df["Status"].isin(status_selecionados)]
        
        return df
    
    def _aplicar_filtro_usuarios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtros de usuários"""
        # Filtro usuário preenchimento
        if self.usuario_preench_dropdown and self.usuario_preench_dropdown.value:
            usuario_preench = self.usuario_preench_dropdown.value
            if "Preenchido_por" in df.columns:
                df = df[df["Preenchido_por"] == usuario_preench]
        
        # Filtro usuário aprovação
        if self.usuario_aprov_dropdown and self.usuario_aprov_dropdown.value:
            usuario_aprov = self.usuario_aprov_dropdown.value
            if "Aprovado_por" in df.columns:
                df = df[df["Aprovado_por"] == usuario_aprov]
        
        return df
    
    def _aplicar_filtro_motivos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtro de motivos"""
        if self.motivos_dropdown and self.motivos_dropdown.value:
            motivos_selecionados = self.motivos_dropdown.value
            if motivos_selecionados and "Motivo" in df.columns:
                df = df[df["Motivo"].isin(motivos_selecionados)]
        
        return df
    
    def _aplicar_filtro_observacoes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtro de observações (busca textual)"""
        busca = self.filtros_ativos.get("observacao_busca", "").strip()
        
        if busca and "Observacao" in df.columns:
            # Busca case-insensitive nas observações
            mask = df["Observacao"].str.contains(
                busca, case=False, na=False, regex=False
            )
            df = df[mask]
        
        return df
    
    def _aplicar_filtros_observacao(self):
        """Aplica apenas filtro de observações (para busca em tempo real)"""
        if hasattr(self, 'df_filtrado') and not self.df_filtrado.empty:
            self._aplicar_filtros(None)
    
    def _limpar_filtros(self, e):
        """Limpa todos os filtros aplicados"""
        # Reset campos de filtro
        if self.data_inicio_field:
            self.data_inicio_field.value = None
        if self.data_fim_field:
            self.data_fim_field.value = None
        if self.status_dropdown:
            self.status_dropdown.value = None
        if self.usuario_preench_dropdown:
            self.usuario_preench_dropdown.value = None
        if self.usuario_aprov_dropdown:
            self.usuario_aprov_dropdown.value = None
        if self.motivos_dropdown:
            self.motivos_dropdown.value = None
        if self.observacao_field:
            self.observacao_field.value = ""
        
        # Reset filtros internos
        self.filtros_ativos = {
            "data_inicio": None,
            "data_fim": None,
            "status": [],
            "usuario_preenchimento": None,
            "usuario_aprovacao": None,
            "motivos": [],
            "observacao_busca": ""
        }
        
        # Restaura dados originais
        self._preparar_dados_iniciais()
        self.page.update()
        
        mostrar_mensagem(self.page, "🧹 Filtros limpos com sucesso!", "success")
    
    def _atualizar_dados(self, e):
        """Atualiza dados do SharePoint"""
        mostrar_mensagem(self.page, "🔄 Atualizando dados...", "info")
        self.app_controller.atualizar_dados()
        self._preparar_dados_iniciais()
        mostrar_mensagem(self.page, "✅ Dados atualizados!", "success")
    
    def _atualizar_contador(self):
        """Atualiza contador de registros filtrados"""
        if self.contador_registros:
            total = len(self.df_filtrado)
            self.contador_registros.value = f"📋 {total:,} registro(s) encontrado(s)"
            self.contador_registros.update()
    
    def _atualizar_tabela(self):
        """Atualiza tabela com dados filtrados"""
        if not hasattr(self, 'tabela_resultados') or self.tabela_resultados is None:
            return
        
        # Limpa linhas existentes
        self.tabela_resultados.rows.clear()
        
        # Adiciona novas linhas
        for _, row in self.df_filtrado.iterrows():
            # Processa dados do evento
            titulo = row.get("Titulo", "")
            evento_info = EventoProcessor.parse_titulo_completo(titulo) if titulo else {}
            
            data_fmt = evento_info.get("datahora_fmt", "N/A")
            tipo = evento_info.get("tipo_amigavel", "N/A")
            poi = evento_info.get("poi_amigavel", "N/A")
            status = row.get("Status", "N/A")
            preenchido_por = row.get("Preenchido_por", "")
            aprovado_por = row.get("Aprovado_por", "")
            motivo = row.get("Motivo", "")
            observacao = row.get("Observacao", "")
            
            # Trunca observação se muito longa
            if len(observacao) > 50:
                observacao = observacao[:47] + "..."
            
            nova_linha = ft.DataRow([
                ft.DataCell(ft.Text(data_fmt, size=12)),
                ft.DataCell(ft.Text(tipo, size=12)),
                ft.DataCell(ft.Text(poi, size=12)),
                ft.DataCell(ft.Text(status, size=12)),
                ft.DataCell(ft.Text(preenchido_por, size=12)),
                ft.DataCell(ft.Text(aprovado_por, size=12)),
                ft.DataCell(ft.Text(motivo, size=12)),
                ft.DataCell(ft.Text(observacao, size=12))
            ])
            
            self.tabela_resultados.rows.append(nova_linha)
        
        self.tabela_resultados.update()
    
    def _exportar_dados(self, e):
        """Exporta dados filtrados para Excel"""
        if self.df_filtrado.empty:
            mostrar_mensagem(self.page, "⚠️ Nenhum dado para exportar", "warning")
            return
        
        try:
            # Prepara dados para exportação
            df_export = self.df_filtrado.copy()
            
            # Adiciona colunas processadas
            df_export["Data_Evento"] = df_export["Titulo"].apply(
                lambda x: EventoProcessor.parse_titulo_completo(x).get("datahora_fmt", "")
            )
            df_export["Tipo_Evento"] = df_export["Titulo"].apply(
                lambda x: EventoProcessor.parse_titulo_completo(x).get("tipo_amigavel", "")
            )
            df_export["POI_Amigavel"] = df_export["Titulo"].apply(
                lambda x: EventoProcessor.parse_titulo_completo(x).get("poi_amigavel", "")
            )
            
            # Seleciona colunas para exportação
            colunas_export = [
                "Data_Evento", "Tipo_Evento", "POI_Amigavel", "Status",
                "Preenchido_por", "Data_Preenchimento", "Aprovado_por", "Data_Aprovacao",
                "Motivo", "Observacao", "Titulo"
            ]
            
            df_final = df_export[colunas_export].copy()
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"sentinela_admin_export_{timestamp}.xlsx"
            
            # Salva arquivo (em produção, seria um download)
            df_final.to_excel(nome_arquivo, index=False)
            
            mostrar_mensagem(
                self.page, 
                f"📊 Dados exportados com sucesso! Arquivo: {nome_arquivo}", 
                "success"
            )
            
        except Exception as ex:
            mostrar_mensagem(
                self.page, 
                f"❌ Erro na exportação: {str(ex)}", 
                "error"
            )