"""
Componente de cards do dashboard
"""
import flet as ft
import pandas as pd
from ...core.session_state import get_session_state
from ...services.evento_processor import EventoProcessor
from ...services.data_formatter import DataFormatter
from ...utils.ui_utils import get_screen_size


class DashboardCards:
    """Componente responsável pelos cards do dashboard"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        
    def criar_cards(self):
        """Cria os cards do dashboard"""
        tipos = ["Alerta Informativo", "Tratativa N1", "Tratativa N2", "Tratativa N3", "Tratativa N4"]
        
        # Cores e configurações dos cards
        configuracoes_cores = {
            "Alerta Informativo": {
                "cor_principal": ft.colors.BLUE_600,
                "cor_text": ft.colors.WHITE,
            },
            "Tratativa N1": {
                "cor_principal": ft.colors.ORANGE_600,
                "cor_text": ft.colors.WHITE,
            },
            "Tratativa N2": {
                "cor_principal": ft.colors.RED_600,
                "cor_text": ft.colors.WHITE,
            },
            "Tratativa N3": {
                "cor_principal": ft.colors.RED_800,
                "cor_text": ft.colors.WHITE,
            },
            "Tratativa N4": {
                "cor_principal": ft.colors.PURPLE_600,
                "cor_text": ft.colors.WHITE,
            }
        }
        
        # Ícones dos cards
        icones_png = {
            "Alerta Informativo": "info.png",
            "Tratativa N1": "N1.png",
            "Tratativa N2": "N2.png",
            "Tratativa N3": "N3.png",
            "Tratativa N4": "N4.png"
        }
        
        # Filtra dados por usuário
        df_filtrado = self._filtrar_dados_por_usuario()
        
        # Calcula métricas
        metricas_tipos = self._calcular_metricas(df_filtrado, tipos)
        
        # Cria cards
        cards = []
        screen_size = get_screen_size(self.page.window_width)
        
        # Configurações responsivas
        if screen_size == "small":
            spacing = 12
            card_width = 180
            card_height = 140
            number_size = 24
            title_size = 11
            icon_size = 14
            metric_size = 10
            padding = 16
            badge_size = 50
        elif screen_size == "medium":
            spacing = 16
            card_width = 200
            card_height = 160
            number_size = 28
            title_size = 12
            icon_size = 16
            metric_size = 11
            padding = 18
            badge_size = 55
        else:  # large
            spacing = 20
            card_width = 220
            card_height = 180
            number_size = 32
            title_size = 13
            icon_size = 18
            metric_size = 12
            padding = 20
            badge_size = 60
        
        for tipo in tipos:
            config = configuracoes_cores[tipo]
            icone_png = icones_png.get(tipo, "info.png")
            metricas = metricas_tipos[tipo]
            
            count_eventos = metricas["eventos"]
            count_registros = metricas["registros"]
            tempo_medio = metricas["tempo_medio"]
            
            # Determina status baseado no tempo
            tempo_em_minutos = tempo_medio * 60
            
            if tipo != "Alerta Informativo":
                if tempo_em_minutos >= 90:
                    alerta_estado = "critico"
                    card_border_color = ft.colors.RED_400
                    card_border_width = 3
                elif tempo_em_minutos >= 45:
                    alerta_estado = "atencao"
                    card_border_color = ft.colors.ORANGE_400
                    card_border_width = 2
                else:
                    alerta_estado = "normal"
                    card_border_color = ft.colors.with_opacity(0.1, ft.colors.GREY_400)
                    card_border_width = 1
            else:
                alerta_estado = "normal"
                card_border_color = ft.colors.with_opacity(0.1, ft.colors.GREY_400)
                card_border_width = 1
            
            opacity = 1.0 if count_eventos > 0 else 0.6
            
            # Header do card
            header_row = ft.Row([
                ft.Image(
                    src=f"images/{icone_png}",
                    width=icon_size,
                    height=icon_size,
                    fit=ft.ImageFit.CONTAIN
                ),
                ft.Text(
                    tipo,
                    size=title_size,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                )
            ], spacing=4, alignment=ft.MainAxisAlignment.START)
            
            # Badge de contagem
            badge_bg_color = config["cor_principal"]
            if alerta_estado == "critico" and count_eventos > 0:
                badge_bg_color = ft.colors.RED_600
            elif alerta_estado == "atencao" and count_eventos > 0:
                badge_bg_color = ft.colors.ORANGE_600
            
            badge_numero = ft.Container(
                content=ft.Text(
                    str(count_eventos),
                    size=number_size,
                    weight=ft.FontWeight.BOLD,
                    color=config["cor_text"]
                ),
                width=badge_size,
                height=badge_size,
                alignment=ft.alignment.center,
                bgcolor=badge_bg_color,
                border_radius=12,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.colors.with_opacity(0.3, badge_bg_color),
                    offset=ft.Offset(0, 4)
                )
            )
            
            # Métricas
            tempo_texto = DataFormatter.formatar_tempo_decorrido(tempo_medio)
            tempo_cor = ft.colors.GREY_600
            tempo_weight = ft.FontWeight.W_500
            
            if alerta_estado == "critico" and count_eventos > 0:
                tempo_cor = ft.colors.RED_600
                tempo_weight = ft.FontWeight.BOLD
                tempo_texto = f"⏱️ {tempo_texto} 🚨"
            elif alerta_estado == "atencao" and count_eventos > 0:
                tempo_cor = ft.colors.ORANGE_600
                tempo_weight = ft.FontWeight.BOLD
                tempo_texto = f"⏱️ {tempo_texto} ⚠️"
            else:
                tempo_texto = f"⏱️ {tempo_texto}"
            
            metricas_row = ft.Column([
                ft.Text(
                    f"📋 {count_registros} registros",
                    size=metric_size,
                    color=ft.colors.GREY_600,
                    weight=ft.FontWeight.W_500
                ),
                ft.Text(
                    tempo_texto,
                    size=metric_size,
                    color=tempo_cor,
                    weight=tempo_weight
                )
            ], 
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.START
            )
            
            # Layout do card
            card_content = ft.Column([
                header_row,
                ft.Container(height=8),
                badge_numero,
                ft.Container(height=8),
                metricas_row
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.START
            )
            
            # Container do card
            card = ft.Container(
                content=card_content,
                width=card_width,
                height=card_height,
                padding=padding,
                bgcolor=ft.colors.WHITE,
                border_radius=16,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                    offset=ft.Offset(0, 4)
                ),
                border=ft.border.all(
                    width=card_border_width,
                    color=card_border_color
                ),
                opacity=opacity,
                animate_scale=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
            )
            
            cards.append(card)
        
        # Container dos cards
        cards_container = ft.Container(
            content=ft.Row(
                cards,
                spacing=spacing,
                scroll=ft.ScrollMode.AUTO,
                wrap=False,
                alignment=ft.MainAxisAlignment.START
            ),
            margin=ft.margin.only(top=8, bottom=8),
            padding=ft.padding.symmetric(horizontal=4)
        )
        
        return cards_container
    
    def _filtrar_dados_por_usuario(self):
        session = get_session_state(self.page)
        """Filtra dados baseado no perfil e áreas do usuário"""
        # Filtra dados não aprovados
        df_nao_aprovados = session.df_desvios[
            ~session.df_desvios["Status"].isin(["Aprovado", "Não Tratado"])
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
    
    def _calcular_metricas(self, df_filtrado, tipos):
        """Calcula métricas para cada tipo de evento"""
        metricas_tipos = {}
        
        # Eventos únicos
        df_eventos = df_filtrado.drop_duplicates(subset=["Titulo"]) if not df_filtrado.empty else pd.DataFrame()
        contadores_eventos = df_eventos.groupby("Tipo_Alerta")["Titulo"].nunique().reset_index(name="Count_Eventos") if not df_eventos.empty else pd.DataFrame()
        
        # Contagem de registros
        contadores_registros = df_filtrado.groupby("Tipo_Alerta").size().reset_index(name="Count_Registros") if not df_filtrado.empty else pd.DataFrame()
        
        for tipo in tipos:
            df_tipo = df_filtrado[df_filtrado["Tipo_Alerta"] == tipo] if not df_filtrado.empty else pd.DataFrame()
            
            count_eventos = int(contadores_eventos[contadores_eventos["Tipo_Alerta"] == tipo]["Count_Eventos"].values[0]) if not contadores_eventos.empty and tipo in contadores_eventos["Tipo_Alerta"].values else 0
            count_registros = int(contadores_registros[contadores_registros["Tipo_Alerta"] == tipo]["Count_Registros"].values[0]) if not contadores_registros.empty and tipo in contadores_registros["Tipo_Alerta"].values else 0
            tempo_medio_horas = self._calcular_tempo_medio(df_tipo)
            
            metricas_tipos[tipo] = {
                "eventos": count_eventos,
                "registros": count_registros,
                "tempo_medio": tempo_medio_horas
            }
        
        return metricas_tipos
    
    def _calcular_tempo_medio(self, df_tipo):
        """Calcula tempo médio em horas"""
        if df_tipo.empty:
            return 0
        
        tempos = []
        for _, row in df_tipo.iterrows():
            data_entrada_str = row.get("Data/Hora Entrada", "")
            tempo_info = EventoProcessor.calcular_tempo_decorrido(data_entrada_str)
            if tempo_info["data_entrada_valida"]:
                tempos.append(tempo_info["horas"])
        
        return sum(tempos) / len(tempos) if tempos else 0