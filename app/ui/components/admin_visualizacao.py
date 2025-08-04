"""
Componente de Visualização Admin - VERSÃO COMPLETA COM TODOS OS DADOS E FILTROS
"""
import flet as ft
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ...core.session_state import get_session_state
from ...services.evento_processor import EventoProcessor
from ...services.sharepoint_client import SharePointClient
from ...utils.ui_utils import get_screen_size, mostrar_mensagem


class AdminVisualizacao:
    """Componente de visualização admin completo"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.df_todos_dados = pd.DataFrame()  # TODOS os dados sem filtro
        self.df_filtrado = pd.DataFrame()
        
        # Componentes de filtro
        self.status_dropdown = None
        self.usuario_preench_dropdown = None
        self.usuario_aprov_dropdown = None
        self.motivos_dropdown = None
        self.observacao_field = None
        self.data_inicio_field = None
        self.data_fim_field = None
        self.contador_registros = None
        
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
        
        # Carrega TODOS os dados (sem filtros)
        self._carregar_todos_dados()
        
        # Cria interface
        return ft.Column([
            self._criar_header(),
            self._criar_secao_filtros(),
            self._criar_contador_exportacao(),
            self._criar_lista_eventos()
        ], spacing=20, expand=True)
    
    def _carregar_todos_dados(self):
        """Carrega TODOS os dados disponíveis com debug detalhado"""
        try:
            print("🔄 Carregando TODOS os dados BRUTOS para visualização admin...")
            
            # CARREGA DADOS BRUTOS DIRETO DO SHAREPOINT (sem processamento)
            try:
                df_brutos = SharePointClient.carregar_lista("Desvios", limite=5000, ordenar_por_recentes=True)
                
                if not df_brutos.empty:
                    self.df_todos_dados = df_brutos.copy()
                    self.df_filtrado = df_brutos.copy()
                    print(f"✅ Carregados {len(df_brutos)} registros BRUTOS do SharePoint")
                    
                    # Debug detalhado
                    print("🔍 DEBUG - Colunas disponíveis:")
                    for col in df_brutos.columns:
                        print(f"   - {col}")
                    
                    # Debug: amostra de títulos com teste de processamento
                    if "Titulo" in df_brutos.columns:
                        print("🔍 DEBUG - Testando processamento de títulos:")
                        titulos_amostra = df_brutos["Titulo"].dropna().head(5)
                        for i, titulo in enumerate(titulos_amostra, 1):
                            print(f"\n📋 Teste {i}: {titulo}")
                            data_fmt, tipo, poi = self._extrair_info_basica_titulo(titulo)
                            print(f"    📅 Data: {data_fmt}")
                            print(f"    🎯 Tipo: {tipo}")
                            print(f"    📍 POI: {poi}")
                    
                    # Debug: mostra contagem por status
                    if "Status" in df_brutos.columns:
                        contagem_status = df_brutos["Status"].value_counts()
                        print("\n📊 Contagem por status (DADOS BRUTOS):")
                        for status, count in contagem_status.items():
                            print(f"   {status}: {count}")
                    
                    self._atualizar_contador()
                    return
                    
            except Exception as sp_error:
                print(f"⚠️ Erro no SharePoint direto: {sp_error}")
            
            # Fallback 1: dados da sessão (podem estar filtrados)
            session = get_session_state(self.page)
            if hasattr(session, 'df_desvios') and not session.df_desvios.empty:
                self.df_todos_dados = session.df_desvios.copy()
                self.df_filtrado = session.df_desvios.copy()
                print(f"⚠️ Usando dados da sessão: {len(self.df_filtrado)} registros")
                
                # Debug detalhado da sessão
                print("🔍 DEBUG SESSÃO - Colunas disponíveis:")
                for col in self.df_todos_dados.columns:
                    print(f"   - {col}")
                
                # Debug: amostra de títulos da sessão com teste
                if "Titulo" in self.df_todos_dados.columns:
                    print("🔍 DEBUG SESSÃO - Testando processamento de títulos:")
                    titulos_amostra = self.df_todos_dados["Titulo"].dropna().head(5)
                    for i, titulo in enumerate(titulos_amostra, 1):
                        print(f"\n📋 Teste Sessão {i}: {titulo}")
                        data_fmt, tipo, poi = self._extrair_info_basica_titulo(titulo)
                        print(f"    📅 Data: {data_fmt}")
                        print(f"    🎯 Tipo: {tipo}")
                        print(f"    📍 POI: {poi}")
                
                # Debug: mostra contagem por status
                if "Status" in self.df_todos_dados.columns:
                    contagem_status = self.df_todos_dados["Status"].value_counts()
                    print("\n📊 Contagem por status (DADOS SESSÃO):")
                    for status, count in contagem_status.items():
                        print(f"   {status}: {count}")
                
                self._atualizar_contador()
                return
            
            # Fallback 2: dados vazios
            print("❌ Nenhum dado disponível")
            self.df_todos_dados = pd.DataFrame()
            self.df_filtrado = pd.DataFrame()
            self._atualizar_contador()
            
        except Exception as e:
            print(f"❌ Erro geral ao carregar dados: {e}")
            self.df_todos_dados = pd.DataFrame()
            self.df_filtrado = pd.DataFrame()
            self._atualizar_contador()
    
    def _criar_header(self):
        """Cria header da página admin"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS, size=28, color=ft.colors.BLUE_600),
                ft.Text(
                    "Visualização Administrativa - TODOS OS DESVIOS",
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
        return ft.Container(
            content=ft.Column([
                ft.Text("🔍 Filtros Avançados", size=18, weight=ft.FontWeight.BOLD),
                
                # Linha 1: Filtros de data
                self._criar_filtros_data(),
                
                # Linha 2: Status e Usuários
                self._criar_filtros_status_usuarios(),
                
                # Linha 3: Motivos e Observações
                self._criar_filtros_motivos_observacoes(),
                
                # Linha 4: Botões de ação
                self._criar_botoes_filtros()
                
            ], spacing=15),
            padding=20,
            bgcolor=ft.colors.GREY_50,
            border_radius=10,
            border=ft.border.all(1, ft.colors.GREY_300)
        )
    
    def _criar_filtros_data(self):
        """Cria filtros de data simples"""
        self.data_inicio_field = ft.TextField(
            label="Data Início (DD/MM/AAAA)",
            hint_text="01/01/2024",
            width=200,
            on_change=self._aplicar_filtros
        )
        
        self.data_fim_field = ft.TextField(
            label="Data Fim (DD/MM/AAAA)",
            hint_text="31/12/2024",
            width=200,
            on_change=self._aplicar_filtros
        )
        
        return ft.Row([
            ft.Text("📅 Período:", weight=ft.FontWeight.BOLD, width=100),
            self.data_inicio_field,
            ft.Text("até", color=ft.colors.GREY_600),
            self.data_fim_field,
            ft.TextButton(
                "Hoje",
                on_click=lambda _: self._aplicar_periodo_atalho("hoje"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            ),
            ft.TextButton(
                "Semana",
                on_click=lambda _: self._aplicar_periodo_atalho("semana"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            ),
            ft.TextButton(
                "Mês",
                on_click=lambda _: self._aplicar_periodo_atalho("mes"),
                style=ft.ButtonStyle(color=ft.colors.BLUE_600)
            )
        ], spacing=10)
    
    def _criar_filtros_status_usuarios(self):
        """Cria filtros de status e usuários"""
        # Status dropdown (TODOS os status)
        self.status_dropdown = ft.Dropdown(
            label="Status",
            hint_text="Todos os status",
            options=[
                ft.dropdown.Option("Todos", "Todos"),
                ft.dropdown.Option("Pendente", "Pendente"),
                ft.dropdown.Option("Preenchido", "Preenchido"),
                ft.dropdown.Option("Aprovado", "Aprovado"),
                ft.dropdown.Option("Reprovado", "Reprovado"),
                ft.dropdown.Option("Não Tratado", "Não Tratado")
            ],
            on_change=self._aplicar_filtros,
            width=200
        )
        
        # Usuários dropdowns
        usuarios_disponiveis = self._obter_usuarios_sistema()
        
        self.usuario_preench_dropdown = ft.Dropdown(
            label="Preenchido Por",
            hint_text="Todos os usuários",
            options=[ft.dropdown.Option("Todos", "Todos")] + [
                ft.dropdown.Option(user, user) for user in usuarios_disponiveis
            ],
            on_change=self._aplicar_filtros,
            width=200
        )
        
        self.usuario_aprov_dropdown = ft.Dropdown(
            label="Aprovado Por",
            hint_text="Todos os usuários",
            options=[ft.dropdown.Option("Todos", "Todos")] + [
                ft.dropdown.Option(user, user) for user in usuarios_disponiveis
            ],
            on_change=self._aplicar_filtros,
            width=200
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
        # Motivos dropdown
        motivos_padronizados = self._obter_motivos_sistema()
        
        self.motivos_dropdown = ft.Dropdown(
            label="Motivos",
            hint_text="Todos os motivos",
            options=[ft.dropdown.Option("Todos", "Todos")] + [
                ft.dropdown.Option(motivo, motivo) for motivo in motivos_padronizados
            ],
            on_change=self._aplicar_filtros,
            width=250
        )
        
        # Campo de busca em observações
        self.observacao_field = ft.TextField(
            label="Buscar em Observações",
            hint_text="Digite para buscar...",
            on_change=self._buscar_observacoes,
            suffix_icon=ft.icons.SEARCH,
            width=300
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
            ft.ElevatedButton(
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
            icon=ft.icons.DOWNLOAD
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
    
    def _criar_lista_eventos(self):
        """Cria lista de eventos filtrados"""
        if self.df_filtrado.empty:
            return ft.Container(
                content=ft.Text(
                    "📭 Nenhum evento encontrado com os filtros aplicados",
                    size=16,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=50,
                alignment=ft.alignment.center
            )
        
        # Lista limitada a 100 registros para performance
        eventos = []
        df_limitado = self.df_filtrado.head(100)
        
        for idx, row in df_limitado.iterrows():
            card_evento = self._criar_card_evento(row)
            if card_evento:
                eventos.append(card_evento)
        
        if len(self.df_filtrado) > 100:
            eventos.append(
                ft.Container(
                    content=ft.Text(
                        f"... e mais {len(self.df_filtrado) - 100} registros (use filtros para refinar)",
                        size=14,
                        color=ft.colors.ORANGE_600,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD
                    ),
                    padding=15,
                    bgcolor=ft.colors.ORANGE_50,
                    border_radius=8,
                    margin=ft.margin.only(top=10)
                )
            )
        
        return ft.Container(
            content=ft.Column(eventos, spacing=0, scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=10
        )
    
    def _criar_card_evento(self, row):
        """Cria card individual para um evento - VERSÃO CORRIGIDA"""
        titulo = row.get("Titulo", "")
        status = row.get("Status", "N/A")
        observacao = row.get("Observacao", "")
        motivo = row.get("Motivo", "")
        preenchido_por = row.get("Preenchido_por", "")
        aprovado_por = row.get("Aprovado_por", "")
        
        # Processa título com tratamento de erro robusto
        data_fmt = tipo = poi = "N/A"
        
        if titulo and titulo.strip():
            try:
                print(f"🔍 Debug: Processando título: {titulo[:50]}...")
                evento_info = EventoProcessor.parse_titulo_completo(titulo)
                
                if evento_info and evento_info.get("valido", False):
                    data_fmt = evento_info.get("datahora_fmt", "N/A")
                    tipo = evento_info.get("tipo_amigavel", "N/A")
                    poi = evento_info.get("poi_amigavel", "N/A")
                    print(f"✅ Processado: {data_fmt} | {tipo} | {poi}")
                else:
                    print(f"⚠️ Evento inválido ou não reconhecido")
                    # Tenta extrair informações básicas do título
                    data_fmt, tipo, poi = self._extrair_info_basica_titulo(titulo)
                    
            except Exception as e:
                print(f"❌ Erro ao processar título: {e}")
                # Fallback: extração manual básica
                data_fmt, tipo, poi = self._extrair_info_basica_titulo(titulo)
        else:
            print(f"⚠️ Título vazio ou inválido")
        
        # Se ainda está N/A, tenta usar outras colunas do registro
        if data_fmt == "N/A":
            data_fmt = self._extrair_data_alternativa(row)
        
        if tipo == "N/A":
            tipo = self._extrair_tipo_alternativo(row)
            
        if poi == "N/A":
            poi = self._extrair_poi_alternativo(row)
        
        # Trunca textos longos
        if len(observacao) > 150:
            observacao = observacao[:147] + "..."
        
        # Cria conteúdo do card com informações disponíveis
        conteudo = ft.Column([
            # Linha 1: Data, Tipo e Status
            ft.Row([
                ft.Text(f"📅 {data_fmt}", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f"🎯 {tipo}", size=14, color=ft.colors.BLUE_700),
                ft.Container(
                    content=ft.Text(
                        status,
                        size=12,
                        color=ft.colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=self._cor_status(status),
                    border_radius=12
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Linha 2: POI
            ft.Text(f"📍 {poi}", size=13, color=ft.colors.GREY_700),
            
            # Linha 3: Título original (para debug)
            ft.Text(f"🔗 {titulo[:80]}..." if len(titulo) > 80 else f"🔗 {titulo}", 
                   size=11, color=ft.colors.GREY_500) if titulo else ft.Container(),
            
            # Linha 4: Usuários (se preenchidos)
            ft.Row([
                ft.Text(f"✏️ {preenchido_por}" if preenchido_por else "✏️ Não preenchido", 
                       size=12, color=ft.colors.GREY_600),
                ft.Text(f"✅ {aprovado_por}" if aprovado_por else "⏳ Não aprovado",
                       size=12, color=ft.colors.GREY_600)
            ], spacing=20) if preenchido_por or aprovado_por else ft.Container(),
            
            # Linha 5: Motivo (se houver)
            ft.Text(f"🏷️ {motivo}", size=12, color=ft.colors.ORANGE_700) if motivo else ft.Container(),
            
            # Linha 6: Observação (se houver)
            ft.Text(f"💭 {observacao}", size=12, color=ft.colors.GREY_600) if observacao else ft.Container()
            
        ], spacing=8)
        
        return ft.Container(
            content=conteudo,
            padding=15,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.colors.GREY_300),
            margin=ft.margin.only(bottom=10)
        )
    
    def _extrair_info_basica_titulo(self, titulo: str):
        """Extrai informações básicas do título - VERSÃO CORRIGIDA PARA PADRÃO SUZANO"""
        import re
        
        data_fmt = tipo = poi = "N/A"
        
        try:
            print(f"🔧 Processando título: {titulo}")
            
            # PADRÃO: RRP_CarrregamentoFabricaRRP_N1_21072025_16000
            # FORMATO: UNIDADE_LOCAL_TIPO_DDMMAAAA_HHMM[SS]
            
            # 1. EXTRAI DATA E HORA
            # Busca padrão: _DDMMAAAA_HHMM ou _DDMMAAAA_HHMMSS
            match_data = re.search(r'_(\d{2})(\d{2})(\d{4})_(\d{4,6})(?:_|$)', titulo)
            if match_data:
                dia, mes, ano, hora_completa = match_data.groups()
                
                # Processa hora (pode ser HHMM ou HHMMSS)
                if len(hora_completa) == 4:  # HHMM
                    hora = hora_completa[:2]
                    minuto = hora_completa[2:4]
                elif len(hora_completa) == 6:  # HHMMSS
                    hora = hora_completa[:2]
                    minuto = hora_completa[2:4]
                else:
                    hora = "00"
                    minuto = "00"
                
                data_fmt = f"{dia}/{mes} {hora}:{minuto}"
                print(f"✅ Data extraída: {data_fmt}")
            
            # 2. EXTRAI TIPO (N1, N2, N3, N4, Informativo)
            if "_N1_" in titulo:
                tipo = "Tratativa N1"
            elif "_N2_" in titulo:
                tipo = "Tratativa N2"
            elif "_N3_" in titulo:
                tipo = "Tratativa N3"
            elif "_N4_" in titulo:
                tipo = "Tratativa N4"
            elif "Informativo" in titulo:
                tipo = "Alerta Informativo"
            else:
                # Tenta extrair qualquer _NX_
                match_tipo = re.search(r'_N(\d+)_', titulo)
                if match_tipo:
                    numero = match_tipo.group(1)
                    tipo = f"Tratativa N{numero}"
                else:
                    tipo = "Tipo não identificado"
            
            print(f"✅ Tipo extraído: {tipo}")
            
            # 3. EXTRAI UNIDADE E LOCAL (POI)
            # Divide o título em partes
            partes = titulo.split('_')
            
            if len(partes) >= 2:
                unidade = partes[0]  # RRP ou TLS
                local_raw = partes[1]  # CarrregamentoFabricaRRP, PAAGUACLARA, etc.
                
                # Mapeamento de locais por unidade
                if unidade == "RRP":
                    if "Carregamento" in local_raw or "carregamento" in local_raw:
                        poi = "Carregamento Fábrica - RRP"
                    elif "PAAGUACLARA" in local_raw or "PAaguaClara" in local_raw or "AguaClara" in local_raw:
                        poi = "P.A. Água Clara - RRP"
                    elif "Oficina" in local_raw or "oficina" in local_raw:
                        poi = "Manutenção - RRP"
                    elif "Terminal" in local_raw or "Inocencia" in local_raw or "terminal" in local_raw:
                        poi = "Terminal Inocência - RRP"
                    else:
                        poi = f"RRP - {local_raw}"
                        
                elif unidade == "TLS":
                    if "Carregamento" in local_raw or "carregamento" in local_raw:
                        poi = "Carregamento Fábrica - TLS"
                    elif "PACELULOSE" in local_raw or "PAcelulose" in local_raw or "Celulose" in local_raw:
                        poi = "P.A. Celulose - TLS"
                    elif "Oficina" in local_raw or "oficina" in local_raw:
                        poi = "Manutenção - TLS"
                    elif "Terminal" in local_raw or "TAP" in local_raw or "Aparecida" in local_raw:
                        poi = "Terminal Aparecida - TLS"
                    else:
                        poi = f"TLS - {local_raw}"
                else:
                    poi = f"{unidade} - {local_raw}"
            
            print(f"✅ POI extraído: {poi}")
            
            # EXEMPLO DE PROCESSAMENTO COMPLETO:
            # Título: RRP_CarrregamentoFabricaRRP_N1_21072025_16000
            # Resultado: 21/07 16:00 | Tratativa N1 | Carregamento Fábrica - RRP
            
        except Exception as e:
            print(f"❌ Erro na extração do título: {e}")
            # Fallback básico
            if "RRP" in titulo:
                poi = "Ribas do Rio Pardo"
            elif "TLS" in titulo:
                poi = "Três Lagoas"
        
        print(f"🎯 Resultado final: {data_fmt} | {tipo} | {poi}")
        return data_fmt, tipo, poi
    
    def _extrair_data_alternativa(self, row):
        """Tenta extrair data de outras colunas"""
        try:
            # Tenta colunas de data
            for col in ['Created', 'Data_Criacao', 'DataCriacao', 'Modified']:
                if col in row and row[col]:
                    data_str = str(row[col])
                    if data_str and data_str != 'nan':
                        # Tenta formatar data ISO
                        if 'T' in data_str:
                            from datetime import datetime
                            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                            return dt.strftime("%d/%m %H:%M")
                        return data_str[:16]  # Primeiros 16 caracteres
            return "Data não encontrada"
        except:
            return "Erro na data"
    
    def _extrair_tipo_alternativo(self, row):
        """Tenta extrair tipo de outras colunas ou inferir"""
        try:
            # Verifica se há coluna de tipo
            for col in ['Tipo', 'TipoEvento', 'Categoria']:
                if col in row and row[col]:
                    return str(row[col])
            
            # Infere pelo status
            status = row.get("Status", "")
            if status in ["Aprovado", "Reprovado"]:
                return "Evento Processado"
            elif status == "Pendente":
                return "Aguardando Tratamento"
            
            return "Tipo não identificado"
        except:
            return "Erro no tipo"
    
    def _extrair_poi_alternativo(self, row):
        """Tenta extrair POI de outras colunas"""
        try:
            # Verifica colunas relacionadas
            for col in ['Local', 'POI', 'Area', 'Localizacao']:
                if col in row and row[col]:
                    return str(row[col])
            
            # Usa título parcial se disponível
            titulo = row.get("Titulo", "")
            if "RRP" in titulo:
                return "Ribas do Rio Pardo"
            elif "TLS" in titulo:
                return "Três Lagoas"
            
            return "Local não identificado"
        except:
            return "Erro no local"
    
    def _cor_status(self, status: str) -> str:
        """Retorna cor baseada no status"""
        cores = {
            "Pendente": ft.colors.ORANGE_600,
            "Preenchido": ft.colors.BLUE_600,
            "Aprovado": ft.colors.GREEN_600,
            "Reprovado": ft.colors.RED_600,
            "Não Tratado": ft.colors.GREY_600
        }
        return cores.get(status, ft.colors.GREY_600)
    
    def _obter_usuarios_sistema(self) -> List[str]:
        """Obtém lista única de usuários do sistema"""
        usuarios = set()
        
        if not self.df_todos_dados.empty:
            # Usuários que preencheram
            if "Preenchido_por" in self.df_todos_dados.columns:
                usuarios.update(self.df_todos_dados["Preenchido_por"].dropna().unique())
            
            # Usuários que aprovaram
            if "Aprovado_por" in self.df_todos_dados.columns:
                usuarios.update(self.df_todos_dados["Aprovado_por"].dropna().unique())
        
        return sorted([user for user in usuarios if user and user.strip()])
    
    def _obter_motivos_sistema(self) -> List[str]:
        """Obtém lista única de motivos do sistema"""
        motivos = set()
        
        if not self.df_todos_dados.empty and "Motivo" in self.df_todos_dados.columns:
            motivos.update(self.df_todos_dados["Motivo"].dropna().unique())
        
        # Adiciona motivos padrão
        motivos_padrao = [
            "Chuva", "Quebra Equipamento", "Falta Energia", 
            "Manutenção Programada", "Falta Pessoal", 
            "Problema Sistema", "Congestionamento", "Outros"
        ]
        motivos.update(motivos_padrao)
        
        return sorted([motivo for motivo in motivos if motivo and motivo.strip()])
    
    def _aplicar_periodo_atalho(self, periodo: str):
        """Aplica filtros de período por atalhos"""
        hoje = datetime.now()
        
        if periodo == "hoje":
            data_inicio = hoje.strftime("%d/%m/%Y")
            data_fim = hoje.strftime("%d/%m/%Y")
        elif periodo == "semana":
            data_inicio = (hoje - timedelta(days=7)).strftime("%d/%m/%Y")
            data_fim = hoje.strftime("%d/%m/%Y")
        elif periodo == "mes":
            data_inicio = (hoje - timedelta(days=30)).strftime("%d/%m/%Y")
            data_fim = hoje.strftime("%d/%m/%Y")
        else:
            return
        
        # Atualiza campos
        if self.data_inicio_field:
            self.data_inicio_field.value = data_inicio
        if self.data_fim_field:
            self.data_fim_field.value = data_fim
        
        # Aplica filtros
        self._aplicar_filtros(None)
        self.page.update()
    
    def _aplicar_filtros(self, e):
        """Aplica todos os filtros selecionados"""
        if self.df_todos_dados.empty:
            return
        
        df_resultado = self.df_todos_dados.copy()
        
        # Filtro de Status
        if (self.status_dropdown and self.status_dropdown.value and 
            self.status_dropdown.value != "Todos" and "Status" in df_resultado.columns):
            df_resultado = df_resultado[df_resultado["Status"] == self.status_dropdown.value]
        
        # Filtro de Usuário Preenchimento
        if (self.usuario_preench_dropdown and self.usuario_preench_dropdown.value and 
            self.usuario_preench_dropdown.value != "Todos" and "Preenchido_por" in df_resultado.columns):
            df_resultado = df_resultado[df_resultado["Preenchido_por"] == self.usuario_preench_dropdown.value]
        
        # Filtro de Usuário Aprovação
        if (self.usuario_aprov_dropdown and self.usuario_aprov_dropdown.value and 
            self.usuario_aprov_dropdown.value != "Todos" and "Aprovado_por" in df_resultado.columns):
            df_resultado = df_resultado[df_resultado["Aprovado_por"] == self.usuario_aprov_dropdown.value]
        
        # Filtro de Motivos
        if (self.motivos_dropdown and self.motivos_dropdown.value and 
            self.motivos_dropdown.value != "Todos" and "Motivo" in df_resultado.columns):
            df_resultado = df_resultado[df_resultado["Motivo"] == self.motivos_dropdown.value]
        
        # Aplicar filtros de data seria aqui (implementação futura)
        
        self.df_filtrado = df_resultado
        self._atualizar_contador()
        
        # Reconstrói interface
        self.app_controller.mostrar_admin()
    
    def _buscar_observacoes(self, e):
        """Busca nas observações em tempo real"""
        busca = e.control.value.strip() if e.control.value else ""
        
        if self.df_todos_dados.empty:
            return
        
        df_resultado = self.df_todos_dados.copy()
        
        # Aplica outros filtros primeiro
        self._aplicar_filtros_base(df_resultado)
        
        # Aplica busca em observações
        if busca and "Observacao" in df_resultado.columns:
            mask = df_resultado["Observacao"].str.contains(
                busca, case=False, na=False, regex=False
            )
            df_resultado = df_resultado[mask]
        
        self.df_filtrado = df_resultado
        self._atualizar_contador()
        
        # Reconstrói interface
        self.app_controller.mostrar_admin()
    
    def _aplicar_filtros_base(self, df):
        """Aplica filtros base (sem observações)"""
        # Este método seria usado para aplicar outros filtros antes da busca
        # Por simplicidade, mantém o DataFrame como está
        pass
    
    def _limpar_filtros(self, e):
        """Limpa todos os filtros"""
        if self.status_dropdown:
            self.status_dropdown.value = "Todos"
        if self.usuario_preench_dropdown:
            self.usuario_preench_dropdown.value = "Todos"
        if self.usuario_aprov_dropdown:
            self.usuario_aprov_dropdown.value = "Todos"
        if self.motivos_dropdown:
            self.motivos_dropdown.value = "Todos"
        if self.observacao_field:
            self.observacao_field.value = ""
        if self.data_inicio_field:
            self.data_inicio_field.value = ""
        if self.data_fim_field:
            self.data_fim_field.value = ""
        
        # Restaura todos os dados
        self.df_filtrado = self.df_todos_dados.copy()
        self._atualizar_contador()
        
        # Reconstrói interface
        self.app_controller.mostrar_admin()
        
        mostrar_mensagem(self.page, "🧹 Filtros limpos!", "success")
    
    def _atualizar_dados(self, e):
        """Atualiza dados do sistema forçando recarregamento"""
        try:
            mostrar_mensagem(self.page, "🔄 Recarregando TODOS os dados...", "info")
            
            # Força recarregamento completo
            self._carregar_todos_dados()
            
            # Se ainda não temos dados, tenta forçar via app_controller
            if self.df_todos_dados.empty:
                print("⚠️ Tentando recarregar via app_controller...")
                if hasattr(self.app_controller, 'atualizar_dados'):
                    self.app_controller.atualizar_dados()
                
                # Espera um pouco e tenta novamente
                import time
                time.sleep(1)
                session = get_session_state(self.page)
                if hasattr(session, 'df_desvios') and not session.df_desvios.empty:
                    self.df_todos_dados = session.df_desvios.copy()
                    self.df_filtrado = session.df_desvios.copy()
                    print(f"✅ Dados recarregados via app_controller: {len(self.df_filtrado)} registros")
            
            # Reconstrói interface
            self.app_controller.mostrar_admin()
            
            if not self.df_todos_dados.empty:
                mostrar_mensagem(self.page, f"✅ {len(self.df_todos_dados)} registros carregados!", "success")
            else:
                mostrar_mensagem(self.page, "⚠️ Nenhum dado encontrado", "warning")
                
        except Exception as ex:
            print(f"❌ Erro na atualização: {ex}")
            mostrar_mensagem(self.page, f"❌ Erro: {str(ex)}", "error")
    
    def _atualizar_contador(self):
        """Atualiza contador de registros"""
        if self.contador_registros:
            total_original = len(self.df_todos_dados)
            total_filtrado = len(self.df_filtrado)
            
            if total_filtrado == total_original:
                self.contador_registros.value = f"📋 {total_filtrado:,} registro(s) total"
            else:
                self.contador_registros.value = f"📋 {total_filtrado:,} de {total_original:,} registro(s)"
    
    def _exportar_dados(self, e):
        """Exporta dados filtrados para Excel"""
        try:
            if self.df_filtrado.empty:
                mostrar_mensagem(self.page, "⚠️ Nenhum dado para exportar", "warning")
                return
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"sentinela_admin_completo_{timestamp}.xlsx"
            
            # Prepara dados para exportação
            dados_export = []
            
            for _, row in self.df_filtrado.iterrows():
                titulo = row.get("Titulo", "")
                
                # Dados básicos sempre incluídos
                linha = {
                    "Status": row.get("Status", ""),
                    "Preenchido_por": row.get("Preenchido_por", ""),
                    "Data_Preenchimento": row.get("Data_Preenchimento", ""),
                    "Aprovado_por": row.get("Aprovado_por", ""),
                    "Data_Aprovacao": row.get("Data_Aprovacao", ""),
                    "Motivo": row.get("Motivo", ""),
                    "Observacao": row.get("Observacao", ""),
                    "Titulo_Original": titulo
                }
                
                # Processa título se possível
                try:
                    if titulo:
                        evento_info = EventoProcessor.parse_titulo_completo(titulo)
                        linha.update({
                            "Data_Evento": evento_info.get("datahora_fmt", ""),
                            "Tipo_Evento": evento_info.get("tipo_amigavel", ""),
                            "POI": evento_info.get("poi_amigavel", "")
                        })
                    else:
                        linha.update({
                            "Data_Evento": "",
                            "Tipo_Evento": "",
                            "POI": ""
                        })
                except:
                    linha.update({
                        "Data_Evento": "Erro processamento",
                        "Tipo_Evento": "Erro processamento",
                        "POI": "Erro processamento"
                    })
                
                dados_export.append(linha)
            
            # Cria DataFrame final
            df_final = pd.DataFrame(dados_export)
            
            # Reordena colunas
            colunas_ordem = [
                "Data_Evento", "Tipo_Evento", "POI", "Status",
                "Preenchido_por", "Data_Preenchimento",
                "Aprovado_por", "Data_Aprovacao", 
                "Motivo", "Observacao", "Titulo_Original"
            ]
            
            colunas_existentes = [col for col in colunas_ordem if col in df_final.columns]
            df_final = df_final[colunas_existentes]
            
            # Salva arquivo Excel
            df_final.to_excel(nome_arquivo, index=False)
            
            mostrar_mensagem(
                self.page,
                f"✅ Exportado! Arquivo: {nome_arquivo} ({len(df_final)} registros)",
                "success"
            )
            
        except Exception as ex:
            mostrar_mensagem(
                self.page,
                f"❌ Erro na exportação: {str(ex)}",
                "error"
            )