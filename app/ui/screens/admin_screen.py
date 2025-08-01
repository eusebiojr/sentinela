"""
ARQUIVO: app/ui/screens/admin_screen.py
Tela principal para visualização administrativa
"""
import flet as ft
import pandas as pd
from datetime import datetime
from ..components.admin_visualizacao import AdminVisualizacao
from ...core.session_state import get_session_state
from ...services.evento_processor import EventoProcessor
from ...utils.ui_utils import mostrar_mensagem


class AdminScreen:
    """Tela de visualização administrativa"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.admin_viz = AdminVisualizacao(page, app_controller)
    
    def mostrar(self):
        """Exibe a tela administrativa"""
        session = get_session_state(self.page)
        
        # Verifica permissão
        perfil = session.get_perfil_usuario()
        if perfil not in ("admin", "torre"):
            self.page.title = "Sentinela - Acesso Negado"
            content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.BLOCK, size=64, color=ft.colors.RED_600),
                    ft.Text(
                        "Acesso Restrito",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.RED_700
                    ),
                    ft.Text(
                        "Esta funcionalidade é exclusiva para perfis Administrativos.",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton(
                        "🏠 Voltar ao Dashboard",
                        on_click=lambda _: self.app_controller.mostrar_dashboard(),
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=50,
                alignment=ft.alignment.center
            )
        else:
            self.page.title = "Sentinela - Visualização Administrativa" 
            content = self.admin_viz.criar_interface()
        
        self.page.clean()
        self.page.add(content)
        self.page.update()


# ============================================================================
# ARQUIVO: Modificações no app_controller.py
# ============================================================================

"""
MODIFICAÇÕES NECESSÁRIAS NO APP_CONTROLLER:

1. Adicionar import da nova tela:
from .ui.screens.admin_screen import AdminScreen

2. Adicionar no __init__:
self.admin_screen = AdminScreen(self.page, self)

3. Adicionar método para mostrar tela admin:
def mostrar_admin(self):
    '''Mostra tela de visualização administrativa'''
    self.admin_screen.mostrar()

4. Adicionar botão no menu principal (modificar create_navbar):
"""

def create_navbar_with_admin(self):
    """
    VERSÃO MODIFICADA DO NAVBAR COM OPÇÃO ADMIN
    Substitui o método create_navbar existente
    """
    session = get_session_state(self.page)
    perfil = session.get_perfil_usuario()
    
    # Botões base do menu
    menu_items = [
        ft.NavigationRailDestination(
            icon=ft.icons.DASHBOARD,
            selected_icon=ft.icons.DASHBOARD,
            label="Dashboard"
        ),
        ft.NavigationRailDestination(
            icon=ft.icons.LIST_ALT,
            selected_icon=ft.icons.LIST_ALT, 
            label="Eventos"
        )
    ]
    
    # Adiciona opção Admin apenas para perfis autorizados
    if perfil in ("admin", "torre"):
        menu_items.append(
            ft.NavigationRailDestination(
                icon=ft.icons.ADMIN_PANEL_SETTINGS,
                selected_icon=ft.icons.ADMIN_PANEL_SETTINGS,
                label="Admin"
            )
        )
    
    def on_destination_change(e):
        """Handler para mudança de navegação"""
        selected_index = e.control.selected_index
        
        if selected_index == 0:
            self.mostrar_dashboard()
        elif selected_index == 1:
            self.mostrar_eventos()
        elif selected_index == 2 and perfil in ("admin", "torre"):
            self.mostrar_admin()  # NOVA FUNÇÃO
    
    navbar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=120,
        min_extended_width=200,
        destinations=menu_items,
        on_change=on_destination_change,
        bgcolor=ft.colors.BLUE_50,
        indicator_color=ft.colors.BLUE_100
    )
    
    return navbar


# ============================================================================
# ARQUIVO: Melhorias na AdminVisualizacao
# ============================================================================

"""
MELHORIAS ADICIONAIS PARA O COMPONENTE PRINCIPAL:
"""

class AdminVisualizacaoMelhorada:
    """Versão aprimorada com funcionalidades extras"""
    
    def _criar_filtros_data_melhorado(self):
        """Versão melhorada dos filtros de data com atalhos"""
        
        # Botões de atalho para períodos comuns
        botoes_periodo = ft.Row([
            ft.TextButton(
                "Hoje",
                on_click=lambda _: self._aplicar_periodo_atalho("hoje"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            ),
            ft.TextButton(
                "Última Semana", 
                on_click=lambda _: self._aplicar_periodo_atalho("semana"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            ),
            ft.TextButton(
                "Último Mês",
                on_click=lambda _: self._aplicar_periodo_atalho("mes"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            ),
            ft.TextButton(
                "3 Meses",
                on_click=lambda _: self._aplicar_periodo_atalho("3meses"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            )
        ], spacing=10)
        
        return ft.Column([
            ft.Text("📅 Atalhos de Período:", size=12, weight=ft.FontWeight.BOLD),
            botoes_periodo,
            ft.Divider(height=10),
            # ... resto dos filtros de data originais
        ], spacing=8)
    
    def _aplicar_periodo_atalho(self, periodo: str):
        """Aplica filtros de período por atalhos"""
        from datetime import datetime, timedelta
        
        hoje = datetime.now().date()
        
        if periodo == "hoje":
            self.data_inicio_field.value = hoje
            self.data_fim_field.value = hoje
        elif periodo == "semana":
            self.data_inicio_field.value = hoje - timedelta(days=7)
            self.data_fim_field.value = hoje
        elif periodo == "mes":
            self.data_inicio_field.value = hoje - timedelta(days=30)
            self.data_fim_field.value = hoje
        elif periodo == "3meses":
            self.data_inicio_field.value = hoje - timedelta(days=90)
            self.data_fim_field.value = hoje
        
        # Aplica filtros automaticamente
        self._aplicar_filtros(None)
        self.page.update()
    
    def _criar_estatisticas_resumo(self):
        """Cria cards de estatísticas resumidas"""
        if self.df_filtrado.empty:
            return ft.Container()
        
        # Calcula estatísticas
        total = len(self.df_filtrado)
        pendentes = len(self.df_filtrado[self.df_filtrado.get("Status", "") == "Pendente"])
        aprovados = len(self.df_filtrado[self.df_filtrado.get("Status", "") == "Aprovado"])
        reprovados = len(self.df_filtrado[self.df_filtrado.get("Status", "") == "Reprovado"])
        
        # Cria cards de estatísticas
        cards_stats = ft.Row([
            self._criar_card_stat("Total", total, ft.colors.BLUE_600, ft.icons.DATASET),
            self._criar_card_stat("Pendentes", pendentes, ft.colors.ORANGE_600, ft.icons.PENDING),
            self._criar_card_stat("Aprovados", aprovados, ft.colors.GREEN_600, ft.icons.CHECK_CIRCLE),
            self._criar_card_stat("Reprovados", reprovados, ft.colors.RED_600, ft.icons.CANCEL)
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("📊 Resumo Estatístico", size=16, weight=ft.FontWeight.BOLD),
                cards_stats
            ], spacing=10),
            padding=15,
            bgcolor=ft.colors.GREY_50,
            border_radius=10,
            margin=ft.margin.only(bottom=20)
        )
    
    def _criar_card_stat(self, titulo: str, valor: int, cor: str, icone):
        """Cria card individual de estatística"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icone, size=24, color=cor),
                ft.Text(str(valor), size=20, weight=ft.FontWeight.BOLD, color=cor),
                ft.Text(titulo, size=12, color=ft.colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=120,
            height=80,
            padding=10,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.colors.GREY_300),
            alignment=ft.alignment.center
        )
    
    def _implementar_filtro_data_por_titulo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        IMPLEMENTAÇÃO CORRETA DO FILTRO DE DATA
        Extrai data do título e aplica filtros de período
        """
        if not self.data_inicio_field or not self.data_fim_field:
            return df
        
        data_inicio = self.data_inicio_field.value
        data_fim = self.data_fim_field.value
        
        if not data_inicio and not data_fim:
            return df
        
        # Função para extrair data do título
        def extrair_data_titulo(titulo: str):
            """Extrai data do título do evento"""
            try:
                evento_info = EventoProcessor.parse_titulo_completo(titulo)
                data_evento = evento_info.get("data_evento")
                
                if data_evento:
                    return data_evento.date()
                return None
            except:
                return None
        
        # Aplica o filtro
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
    
    def _criar_exportacao_avancada(self):
        """Cria opções avançadas de exportação"""
        opcoes_export = [
            ft.dropdown.Option("xlsx", "Excel (.xlsx)"),
            ft.dropdown.Option("csv", "CSV (.csv)"),
            ft.dropdown.Option("pdf", "PDF Report (.pdf)")
        ]
        
        formato_dropdown = ft.Dropdown(
            label="Formato",
            value="xlsx",
            options=opcoes_export,
            width=150
        )
        
        incluir_detalhes = ft.Checkbox(
            label="Incluir campos técnicos",
            value=False
        )
        
        return ft.Row([
            formato_dropdown,
            incluir_detalhes,
            ft.ElevatedButton(
                "📊 Exportar Avançado",
                on_click=lambda e: self._exportar_avancado(
                    formato_dropdown.value,
                    incluir_detalhes.value
                ),
                bgcolor=ft.colors.GREEN_600,
                color=ft.colors.WHITE
            )
        ], spacing=15, alignment=ft.MainAxisAlignment.END)
    
    def _exportar_avancado(self, formato: str, incluir_detalhes: bool):
        """Exportação com opções avançadas"""
        if self.df_filtrado.empty:
            mostrar_mensagem(self.page, "⚠️ Nenhum dado para exportar", "warning")
            return
        
        try:
            # Prepara dados base
            df_export = self._preparar_dados_exportacao(incluir_detalhes)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_base = f"sentinela_admin_{timestamp}"
            
            if formato == "xlsx":
                nome_arquivo = f"{nome_base}.xlsx"
                df_export.to_excel(nome_arquivo, index=False, sheet_name="Desvios")
                
            elif formato == "csv":
                nome_arquivo = f"{nome_base}.csv"
                df_export.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
                
            elif formato == "pdf":
                nome_arquivo = f"{nome_base}.pdf"
                # TODO: Implementar exportação PDF com reportlab
                self._exportar_para_pdf(df_export, nome_arquivo)
            
            mostrar_mensagem(
                self.page,
                f"📊 Exportado com sucesso! Arquivo: {nome_arquivo}",
                "success"
            )
            
        except Exception as ex:
            mostrar_mensagem(
                self.page,
                f"❌ Erro na exportação: {str(ex)}",
                "error"
            )
    
    def _preparar_dados_exportacao(self, incluir_detalhes: bool) -> pd.DataFrame:
        """Prepara dados formatados para exportação"""
        df_export = self.df_filtrado.copy()
        
        # Colunas base (sempre incluídas)
        colunas_base = [
            "Data_Evento", "Tipo_Evento", "POI_Amigavel", "Status",
            "Preenchido_por", "Data_Preenchimento", 
            "Aprovado_por", "Data_Aprovacao",
            "Motivo", "Observacao"
        ]
        
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
        
        # Colunas detalhadas (opcionais)
        if incluir_detalhes:
            colunas_detalhes = [
                "ID", "Titulo", "Created", "Modified", 
                "Author", "Editor", "Placa", "Localizacao"
            ]
            colunas_finais = colunas_base + [col for col in colunas_detalhes if col in df_export.columns]
        else:
            colunas_finais = colunas_base
        
        # Seleciona apenas colunas existentes
        colunas_existentes = [col for col in colunas_finais if col in df_export.columns]
        
        return df_export[colunas_existentes].copy()


# ============================================================================
# RESUMO DE IMPLEMENTAÇÃO
# ============================================================================

"""
🚀 IMPLEMENTAÇÃO COMPLETA DA VISUALIZAÇÃO ADMIN

✅ CRIADO:
1. AdminVisualizacao - Componente principal com todos os filtros
2. AdminScreen - Tela de integração com verificação de permissão  
3. Modificações necessárias no app_controller
4. Melhorias avançadas (atalhos, estatísticas, exportação)

📋 PRÓXIMOS PASSOS:

1. Salvar AdminVisualizacao em: app/ui/components/admin_visualizacao.py
2. Criar AdminScreen em: app/ui/screens/admin_screen.py  
3. Modificar app_controller.py com:
   - Import da AdminScreen
   - Método mostrar_admin()
   - Navbar modificado com opção Admin
4. Testar funcionalidades e ajustar filtros conforme necessário

🎯 FUNCIONALIDADES IMPLEMENTADAS:
✅ Filtros de data com atalhos (hoje, semana, mês, 3 meses)
✅ Filtro de status (multiselect)
✅ Filtros de usuários (preenchimento + aprovação)
✅ Filtro de motivos padronizados
✅ Busca em tempo real nas observações
✅ Tabela completa de resultados
✅ Contador de registros filtrados
✅ Exportação para Excel/CSV
✅ Cards de estatísticas resumidas
✅ Controle de acesso (admin/torre apenas)
✅ Interface responsiva seguindo padrão do sistema

🔧 VALIDAÇÕES INCLUÍDAS:
✅ Verificação de perfil de usuário
✅ Validação de dados antes da exportação
✅ Tratamento de erros em filtros
✅ Mensagens de feedback ao usuário
"""