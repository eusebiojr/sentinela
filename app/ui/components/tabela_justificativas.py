"""
Componente de tabela de justificativas para eventos - VERSÃO COMPLETA COM AUDITORIA E MULTI-LOCALIZAÇÃO
"""
import flet as ft
import pandas as pd
from datetime import datetime
from ...core.state import app_state
from ...services.evento_processor import EventoProcessor
from ...services.data_validator import DataValidator
from ...services.data_formatter import DataFormatter
from ...services.sharepoint_client import SharePointClient
from ...services.audit_service import audit_service
from ...utils.ui_utils import get_screen_size, mostrar_mensagem


class TabelaJustificativas:
    """Componente para exibir e editar justificativas de eventos com auditoria"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.processando_envio = False
        
    def criar_tabela(self, evento: str, df_evento: pd.DataFrame):
        """Cria tabela completa de justificativas sem painel de auditoria"""
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            placa_width = 75
            motivo_width = 273
            previsao_width = 160
            obs_width = 380
            font_size = 12
            field_height = 38
        elif screen_size == "medium":
            placa_width = 86
            motivo_width = 327
            previsao_width = 175
            obs_width = 450
            font_size = 13
            field_height = 40
        else:  # large
            placa_width = 98
            motivo_width = 356
            previsao_width = 190
            obs_width = 600
            font_size = 14
            field_height = 42
        
        # Determina motivos disponíveis COM LOCALIZAÇÃO
        evento_info = EventoProcessor.parse_titulo_completo(evento)
        poi_amigavel = evento_info["poi_amigavel"]
        localizacao = evento_info.get("localizacao", "RRP")  # NOVO: Extrai localização
        motivos = EventoProcessor.determinar_motivos_por_poi(poi_amigavel, localizacao)  # NOVO: Passa localização
        
        # Verifica se usuário pode editar
        perfil = app_state.get_perfil_usuario()
        status = df_evento["Status"].iloc[0] if "Status" in df_evento.columns else "Pendente"
        pode_editar = perfil not in ("aprovador", "torre") and status != "Aprovado"
        
        # Processa dados para exibição
        df_evento_reset = df_evento.reset_index(drop=True)
        df_evento_reset = self._normalizar_colunas(df_evento_reset)
        
        # Cria linhas da tabela
        table_rows = []
        for idx, row in df_evento_reset.iterrows():
            row_cells = self._criar_linha_tabela(
                evento, row, motivos, pode_editar, 
                placa_width, motivo_width, previsao_width, obs_width, 
                font_size, field_height
            )
            table_rows.append(ft.DataRow(cells=row_cells))
        
        # Cabeçalhos da tabela
        header_font_size = font_size + 1
        columns = [
            ft.DataColumn(ft.Text("Placa", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Data/Hora Entrada", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Motivo", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Previsão Liberação", weight=ft.FontWeight.BOLD, size=header_font_size)),
            ft.DataColumn(ft.Text("Observações", weight=ft.FontWeight.BOLD, size=header_font_size))
        ]
        
        # Configurações da tabela
        if screen_size == "small":
            table_width = 1300
            column_spacing = 3
        elif screen_size == "medium":
            table_width = 1500
            column_spacing = 4
        else:
            table_width = 1700
            column_spacing = 5
        
        # Cria tabela
        tabela = ft.DataTable(
            columns=columns,
            rows=table_rows,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=5,
            bgcolor=ft.colors.WHITE,
            horizontal_lines=ft.border.BorderSide(1, ft.colors.GREY_200),
            column_spacing=column_spacing,
            data_row_min_height=38,
            data_row_max_height=55,
            heading_row_height=40,
            width=table_width
        )
        
        # Container da tabela com scroll
        tabela_container = ft.Container(
            content=ft.Row([tabela], scroll=ft.ScrollMode.ADAPTIVE),
            padding=5
        )
        
        # Botões de ação
        botoes = self._criar_botoes_acao(evento, df_evento, pode_editar)
        
        # Container final SEM painel de auditoria
        return ft.Container(
            content=ft.Column([
                tabela_container, 
                ft.Container(height=5), 
                botoes
            ]),
            padding=8
        )
    
    def _normalizar_colunas(self, df_evento):
        """Normaliza colunas do DataFrame"""
        df_evento = df_evento.rename(columns={
            "Id": "ID", "id": "ID",
            "data/hora entrada": "Data/Hora Entrada",
            "data_entrada": "Data/Hora Entrada"
        })
        
        colunas_necessarias = ["ID", "Placa", "Data/Hora Entrada", "Motivo", "Previsao_Liberacao", "Observacoes"]
        for col in colunas_necessarias:
            if col not in df_evento.columns:
                df_evento[col] = ""
        
        df_exibir = df_evento[colunas_necessarias].copy()
        df_exibir["Data/Hora Entrada"] = df_exibir["Data/Hora Entrada"].apply(DataFormatter.formatar_data_exibicao)
        df_exibir["Previsao_Liberacao"] = df_exibir["Previsao_Liberacao"].apply(DataFormatter.formatar_data_exibicao)
        
        return df_exibir
    
    def _criar_linha_tabela(self, evento, row, motivos, pode_editar, 
                          placa_width, motivo_width, previsao_width, obs_width, 
                          font_size, field_height):
        """Cria uma linha da tabela"""
        
        evento_str = str(evento).strip()
        
        # Extrai ID corretamente
        if isinstance(row["ID"], pd.Series):
            row_id = str(row["ID"].iloc[0]).strip()
        else:
            row_id = str(row["ID"]).strip()
        
        # Chave de alteração
        chave_alteracao = f"{evento_str}_{row_id}"
                
        if pode_editar:
            # Campos editáveis
            return self._criar_campos_editaveis(
                row, motivos, chave_alteracao,
                placa_width, motivo_width, previsao_width, obs_width,
                font_size, field_height
            )
        else:
            # Campos apenas leitura
            return self._criar_campos_readonly(row, placa_width, font_size)
    
    def _criar_campos_editaveis(self, row, motivos, chave_alteracao,
                               placa_width, motivo_width, previsao_width, obs_width,
                               font_size, field_height):
        """Cria campos editáveis para uma linha"""
        
        campos_desabilitados = self.processando_envio
        
        # Opções do dropdown de motivo
        opcoes_motivo = [ft.dropdown.Option("", "— Selecione —")] + [
            ft.dropdown.Option(m) for m in sorted(motivos)
        ]
        
        valor_dropdown = row["Motivo"] if (row["Motivo"] in motivos and row["Motivo"].strip() != "") else ""
        
        # Campo de observação
        obs_field = ft.TextField(
            value=str(row["Observacoes"]) if pd.notnull(row["Observacoes"]) else "",
            width=obs_width,
            height=field_height,
            text_size=font_size,
            dense=True,
            filled=True,
            bgcolor=ft.colors.GREY_100 if not campos_desabilitados else ft.colors.GREY_200,
            multiline=True,
            min_lines=1,
            max_lines=3,
            label="Observações",
            border_radius=6,
            disabled=campos_desabilitados
        )
        
        # Ícone de alerta para observação obrigatória
        icone_alerta = ft.Icon(
            ft.icons.WARNING,
            color=ft.colors.ORANGE_600,
            size=20,
            visible=False,
            tooltip="Observação obrigatória quando motivo é 'Outros'"
        )
        
        # Validadores
        def validar_motivo_mudanca(e):
            if campos_desabilitados:
                return
            
            motivo_selecionado = e.control.value
            obs_value = obs_field.value
            
            motivo_normalizado = str(motivo_selecionado).strip().lower() if motivo_selecionado else ""
            obs_normalizada = str(obs_value).strip() if obs_value else ""
            
            if motivo_normalizado == "outros" and not obs_normalizada:
                obs_field.border_color = ft.colors.ORANGE_600
                icone_alerta.visible = True
            else:
                obs_field.border_color = None
                icone_alerta.visible = False
            
            # REMOVIDO: Debug log
            app_state.atualizar_alteracao(chave_alteracao, "Motivo", motivo_selecionado)
            self.page.update()
        
        def validar_observacao_mudanca(e):
            if campos_desabilitados:
                return
            
            motivo_selecionado = motivo_dropdown.value
            obs_value = e.control.value
            
            if (motivo_selecionado and motivo_selecionado.lower() == "outros" and 
                (not obs_value or not obs_value.strip())):
                obs_field.border_color = ft.colors.ORANGE_600
                icone_alerta.visible = True
            else:
                obs_field.border_color = None
                icone_alerta.visible = False
            
            # REMOVIDO: Debug log
            app_state.atualizar_alteracao(chave_alteracao, "Observacoes", obs_value)
            self.page.update()
        
        # Dropdown de motivo
        motivo_dropdown = ft.Dropdown(
            value=valor_dropdown,
            options=opcoes_motivo,
            width=motivo_width,
            height=field_height,
            text_size=font_size,
            dense=True,
            filled=True,
            bgcolor=ft.colors.GREY_100 if not campos_desabilitados else ft.colors.GREY_200,
            content_padding=ft.padding.only(left=12, right=8, top=8, bottom=8),
            alignment=ft.alignment.center_left,
            on_change=validar_motivo_mudanca if not campos_desabilitados else None,
            disabled=campos_desabilitados
        )
        
        # Configura validação da observação
        if not campos_desabilitados:
            obs_field.on_change = validar_observacao_mudanca
        
        # Validação inicial
        if not campos_desabilitados and (valor_dropdown and valor_dropdown.lower() == "outros" and 
            (not obs_field.value or not obs_field.value.strip())):
            obs_field.border_color = ft.colors.ORANGE_600
            icone_alerta.visible = True
        
        # Campo de previsão com modal personalizado
        previsao_field = self._criar_campo_previsao(
            row["Previsao_Liberacao"], chave_alteracao, row,
            previsao_width, font_size, field_height
        )
        
        # Container da observação com ícone
        obs_container = ft.Row([
            obs_field,
            icone_alerta
        ], spacing=5, alignment=ft.MainAxisAlignment.START)
        
        # Células da linha
        return [
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Placa"]), size=15, weight=ft.FontWeight.W_500), 
                width=placa_width
            )),
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Data/Hora Entrada"]), size=15), 
                width=130
            )),
            ft.DataCell(ft.Container(motivo_dropdown, width=motivo_width + 20)),
            ft.DataCell(ft.Container(previsao_field, width=previsao_width + 40)),
            ft.DataCell(ft.Container(obs_container, width=obs_width + 20))
        ]
    
    def _criar_campos_readonly(self, row, placa_width, font_size):
        """Cria campos apenas leitura"""
        return [
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Placa"]), size=15, weight=ft.FontWeight.W_500), 
                width=placa_width,
                padding=5
            )),
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Data/Hora Entrada"]), size=15), 
                padding=5
            )),
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Motivo"]), size=15), 
                padding=5
            )),
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Previsao_Liberacao"]), size=15), 
                padding=5
            )),
            ft.DataCell(ft.Container(
                ft.Text(DataFormatter.safe_str(row["Observacoes"]), size=15), 
                padding=5
            ))
        ]
    
    def _criar_campo_previsao(self, valor_inicial, chave_alteracao, row, previsao_width, font_size, field_height):
        """Cria campo de previsão com modal personalizado para seleção de data/hora"""
        
        # Parse do valor inicial
        display_value = ""
        if valor_inicial and str(valor_inicial).strip():
            display_value = str(valor_inicial).strip()
        
        # Determina se deve estar desabilitado
        campo_desabilitado = self.processando_envio
        
        # Campo de exibição (read-only)
        campo_display = ft.TextField(
            value=display_value,
            hint_text="Clique para selecionar" if not campo_desabilitado else "Processando...",
            width=previsao_width,
            height=field_height,
            text_size=font_size,
            dense=True,
            filled=True,
            bgcolor=ft.colors.GREY_100 if not campo_desabilitado else ft.colors.GREY_200,
            read_only=True,
            prefix_icon=ft.icons.SCHEDULE,
            border_radius=8,
            disabled=campo_desabilitado
        )
        
        # Função para abrir modal
        def abrir_modal(e):
            # Verifica se está processando
            if self.processando_envio:
                mostrar_mensagem(self.page, "⏳ Aguarde finalizar o processamento atual", "warning")
                return
                
            self._mostrar_modal_data_hora(campo_display, chave_alteracao, row)
        
        # Só adiciona evento se não estiver processando
        if not campo_desabilitado:
            campo_display.on_click = abrir_modal
        
        # Botão de edição
        btn_edicao = ft.IconButton(
            icon=ft.icons.EDIT_CALENDAR,
            tooltip="Editar data/hora" if not campo_desabilitado else "Aguarde processamento...",
            on_click=abrir_modal if not campo_desabilitado else None,
            icon_size=16,
            icon_color=ft.colors.BLUE_600 if not campo_desabilitado else ft.colors.GREY_400,
            disabled=campo_desabilitado
        )
        
        return ft.Row([
            campo_display,
            btn_edicao
        ], spacing=2)

    def _mostrar_modal_data_hora(self, campo_display, chave_alteracao, row):
        """Mostra modal personalizado para seleção de data/hora com dropdown de horários"""
        
        # Função para gerar opções de horário (meia em meia hora)
        def gerar_opcoes_horario():
            opcoes = []
            for hora in range(24):
                for minuto in [0, 30]:
                    hora_formatada = f"{hora:02d}:{minuto:02d}"
                    opcoes.append(ft.dropdown.Option(hora_formatada, hora_formatada))
            return opcoes
        
        # Obter data de hoje e hora atual + 1 hora
        from datetime import datetime, timedelta
        import pytz
        
        agora = datetime.now(pytz.timezone("America/Campo_Grande"))
        data_hoje = agora.strftime("%d/%m/%Y")
        
        # Calcula hora padrão (atual + 1 hora, arredondada para meia hora)
        hora_padrao = agora + timedelta(hours=1)
        minutos = hora_padrao.minute
        
        # Arredonda para a próxima meia hora
        if minutos <= 30:
            hora_padrao = hora_padrao.replace(minute=30, second=0, microsecond=0)
        else:
            hora_padrao = hora_padrao.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        hora_padrao_str = hora_padrao.strftime("%H:%M")
        
        # Campo de data com valor padrão
        temp_data_field = ft.TextField(
            label="Data (dd/mm/aaaa)",
            value=data_hoje,  # Pré-preenchido com data de hoje
            width=150,
            hint_text="12/07/2025"
        )
        
        # Dropdown de hora
        temp_hora_dropdown = ft.Dropdown(
            label="Hora",
            value=hora_padrao_str,  # Pré-preenchido com hora atual + 1h
            options=gerar_opcoes_horario(),
            width=120,
            dense=True,
            filled=True,
            bgcolor=ft.colors.GREY_100,
            content_padding=ft.padding.only(left=12, right=8, top=8, bottom=8)
        )
        
        error_text = ft.Text("", color=ft.colors.RED, size=12, visible=False)
        
        def confirmar_data_hora(e):
            try:
                data_str = temp_data_field.value.strip()
                hora_str = temp_hora_dropdown.value
                
                if not data_str and not hora_str:
                    campo_display.value = ""
                    app_state.atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", "")
                    modal_datetime.open = False
                    self.page.update()
                    return
                elif not data_str or not hora_str:
                    error_text.value = "⚠️ Preencha ambos os campos ou deixe ambos em branco"
                    error_text.visible = True
                    self.page.update()
                    return
                
                # Valida formato da data
                dt_inserida = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
                
                # Valida se é posterior à entrada
                data_entrada_str = DataFormatter.safe_str(row["Data/Hora Entrada"])
                if data_entrada_str:
                    try:
                        dt_entrada = datetime.strptime(data_entrada_str, "%d/%m/%Y %H:%M")
                        if dt_inserida <= dt_entrada:
                            error_text.value = f"⚠️ Data/hora deve ser posterior à entrada: {data_entrada_str}"
                            error_text.visible = True
                            self.page.update()
                            return
                    except ValueError:
                        pass
                
                # Atualiza campos
                novo_valor = f"{data_str} {hora_str}"
                campo_display.value = novo_valor
                
                app_state.atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", novo_valor)
                
                modal_datetime.open = False
                self.page.update()
                
            except ValueError:
                error_text.value = "❌ Formato de data inválido. Use dd/mm/aaaa"
                error_text.visible = True
                self.page.update()
        
        def cancelar(e):
            modal_datetime.open = False
            self.page.update()
        
        def limpar_campos(e):
            temp_data_field.value = ""
            temp_hora_dropdown.value = None
            error_text.visible = False
            campo_display.value = ""
            app_state.atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", "")
            self.page.update()
        
        # Função para definir como "hoje + 1 hora"
        def usar_hoje_mais_uma_hora(e):
            agora = datetime.now(pytz.timezone("America/Campo_Grande"))
            data_hoje = agora.strftime("%d/%m/%Y")
            
            # Calcula hora atual + 1 hora, arredondada para meia hora
            hora_mais_uma = agora + timedelta(hours=1)
            minutos = hora_mais_uma.minute
            
            # Arredonda para a próxima meia hora
            if minutos <= 30:
                hora_mais_uma = hora_mais_uma.replace(minute=30, second=0, microsecond=0)
            else:
                hora_mais_uma = hora_mais_uma.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            hora_str = hora_mais_uma.strftime("%H:%M")
            
            temp_data_field.value = data_hoje
            temp_hora_dropdown.value = hora_str
            error_text.visible = False
            self.page.update()
        
        # Função para definir como "amanhã mesmo horário"
        def usar_amanha_mesmo_horario(e):
            agora = datetime.now(pytz.timezone("America/Campo_Grande"))
            amanha = agora + timedelta(days=1)
            data_amanha = amanha.strftime("%d/%m/%Y")
            
            # Arredonda hora atual para meia hora mais próxima
            minutos = agora.minute
            if minutos <= 15:
                hora_arredondada = agora.replace(minute=0, second=0, microsecond=0)
            elif minutos <= 45:
                hora_arredondada = agora.replace(minute=30, second=0, microsecond=0)
            else:
                hora_arredondada = agora.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            temp_data_field.value = data_amanha
            temp_hora_dropdown.value = hora_arredondada.strftime("%H:%M")
            error_text.visible = False
            self.page.update()
        
        # Botões de atalho
        botoes_atalho = ft.Row([
            ft.ElevatedButton(
                "📅 Hoje +1h",
                on_click=usar_hoje_mais_uma_hora,
                bgcolor=ft.colors.BLUE_100,
                color=ft.colors.BLUE_800,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4)
                ),
                height=36,
                width=130
            ),
            ft.ElevatedButton(
                "📅 Amanhã",
                on_click=usar_amanha_mesmo_horario,
                bgcolor=ft.colors.GREEN_100,
                color=ft.colors.GREEN_800,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4)
                ),
                height=36,
                width=130
            )
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        
        # Modal principal
        modal_datetime = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecionar Data e Hora", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Informe a data e hora prevista:", size=14),
                    ft.Container(
                        content=ft.Text(
                            f"📅 Data de entrada: {DataFormatter.safe_str(row['Data/Hora Entrada'])}", 
                            size=12, 
                            color=ft.colors.BLUE_700,
                            weight=ft.FontWeight.W_500
                        ),
                        padding=ft.padding.symmetric(vertical=5),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=3
                    ),
                    ft.Container(height=10),
                    
                    # Atalhos rápidos
                    ft.Text("⚡ Atalhos rápidos:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    botoes_atalho,
                    ft.Container(height=15),
                    
                    # Campos de entrada
                    ft.Text("📝 Ou preencha manualmente:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    ft.Row([temp_data_field, temp_hora_dropdown], spacing=10),
                    ft.Container(height=5),
                    error_text,
                    ft.Container(height=15),
                    
                    # Dicas
                    ft.Container(
                        content=ft.Column([
                            ft.Text("💡 Dicas:", size=11, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_600),
                            ft.Text("• A data deve ser posterior à data de entrada", size=10, color=ft.colors.GREY_500),
                            ft.Text("• Use os atalhos para preenchimento rápido", size=10, color=ft.colors.GREY_500),
                            ft.Text("• Horários disponíveis de meia em meia hora", size=10, color=ft.colors.GREY_500),
                        ], spacing=2),
                        padding=ft.padding.all(8),
                        bgcolor=ft.colors.GREY_50,
                        border_radius=4,
                        border=ft.border.all(1, ft.colors.GREY_200)
                    ),
                    ft.Container(height=10)
                ], tight=True),
                width=450,
                height=400,
                padding=15
            ),
            actions=[
                ft.TextButton("Limpar", on_click=limpar_campos),
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Confirmar", 
                    on_click=confirmar_data_hora, 
                    bgcolor=ft.colors.BLUE_600, 
                    color=ft.colors.WHITE,
                    icon=ft.icons.CHECK
                )
            ],
            shape=ft.RoundedRectangleBorder(radius=8)
        )
        
        self.page.dialog = modal_datetime
        modal_datetime.open = True
        self.page.update()

    def _criar_botoes_acao(self, evento, df_evento, pode_editar):
        """Cria botões de ação para o evento"""
        if pode_editar:
            # Texto e cor dinâmicos baseados no estado
            if self.processando_envio:
                btn_text = "⏳ Enviando..."
                btn_color = ft.colors.GREY_600
                btn_disabled = True
                btn_icon = ft.icons.HOURGLASS_EMPTY
            else:
                btn_text = "Enviar Justificativas"
                btn_color = ft.colors.GREEN_600
                btn_disabled = False
                btn_icon = ft.icons.SEND
            
            btn_enviar = ft.ElevatedButton(
                btn_text,
                bgcolor=btn_color,
                color=ft.colors.WHITE,
                icon=btn_icon,
                on_click=lambda e: self._enviar_justificativas(evento, df_evento) if not btn_disabled else None,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                disabled=btn_disabled
            )
            return ft.Row([btn_enviar], alignment=ft.MainAxisAlignment.END)
        
        else:
            perfil = app_state.get_perfil_usuario()
            status = df_evento["Status"].iloc[0] if "Status" in df_evento.columns else "Pendente"
            
            if perfil in ("aprovador", "torre") and status == "Preenchido":
                btn_reprovar = ft.ElevatedButton(
                    "❌ Reprovar", 
                    bgcolor=ft.colors.RED_600, 
                    color=ft.colors.WHITE, 
                    on_click=lambda e: self._reprovar_evento(evento)
                )
                btn_aprovar = ft.ElevatedButton(
                    "✅ Aprovar", 
                    bgcolor=ft.colors.GREEN_600, 
                    color=ft.colors.WHITE, 
                    on_click=lambda e: self._aprovar_evento(evento)
                )
                return ft.Row([
                    btn_reprovar,
                    ft.Container(
                        content=btn_aprovar,
                        expand=True,
                        alignment=ft.alignment.center_right
                    )
                ])
        
        return ft.Container()
    
    def _enviar_justificativas(self, evento, df_evento):
        """Envia justificativas para o SharePoint com bloqueio de interface"""
        
        # Verifica se já está processando
        if self.processando_envio:
            mostrar_mensagem(self.page, "⏳ Aguarde... processamento em andamento", "warning")
            return
        
        mostrar_mensagem(self.page, "⏳ Validando dados...", "info")
        
        # Validação usando DataValidator
        validacao_resultado = DataValidator.validar_justificativas_evento(df_evento, app_state.alteracoes_pendentes)
        erros_validacao = validacao_resultado["erros"]

        # Se há erros de validação, mostra modal personalizado
        if erros_validacao:
            mostrar_mensagem(self.page, "❌ Existem campos obrigatórios não preenchidos", "error")
            self._mostrar_modal_validacao(erros_validacao)
            return
        
        # Ativa modo processamento
        self._ativar_modo_processamento(True)
        
        # Se validação passou, processa envio
        mostrar_mensagem(self.page, "⏳ Enviando justificativas...", "info")
        self._processar_envio_com_auditoria(evento, df_evento)

    def _ativar_modo_processamento(self, ativo: bool):
        """Ativa/desativa modo processamento - bloqueia/desbloqueia interface"""
        self.processando_envio = ativo
        
        # Força atualização da interface para refletir mudanças
        try:
            self.page.update()
        except Exception as e:
            print(f"⚠️ [PROCESSAMENTO] Erro ao atualizar interface: {e}")
    
    def _processar_envio_com_auditoria(self, evento, df_evento):
        """Processa envio das justificativas COM auditoria integrada"""
        
        # Processa em background
        import threading
        def processar():
            try:
                # Verifica se há alterações pendentes para este evento
                alteracoes_evento = {k: v for k, v in app_state.alteracoes_pendentes.items() 
                                if k.startswith(f"{evento}_")}
                
                if not alteracoes_evento:
                    mostrar_mensagem(self.page, "⚠️ Nenhuma alteração detectada.", "warning")
                    # Desativa modo processamento
                    self._ativar_modo_processamento(False)
                    return
                
                # NOVO: Usa função simplificada que SEMPRE atualiza timestamp
                atualizacoes_lote = audit_service.processar_preenchimento_com_auditoria(
                    evento, df_evento, app_state.alteracoes_pendentes
                )
                
                # Envia todas as alterações em paralelo
                if atualizacoes_lote:
                    print(f"📊 Enviando {len(atualizacoes_lote)} registros com auditoria...")
                    registros_atualizados = SharePointClient.atualizar_lote(atualizacoes_lote)
                    print(f"✅ {registros_atualizados} registros atualizados no SharePoint")
                    
                    # Atualiza status de TODOS os registros do evento
                    status_evento = EventoProcessor.calcular_status_evento(df_evento, app_state.alteracoes_pendentes)
                    
                    atualizacoes_status = []
                    for _, row in df_evento.iterrows():
                        row_id = str(row["ID"]).strip()
                        dados_status = {"Status": status_evento}
                        atualizacoes_status.append((int(row_id), dados_status))
                    
                    # Envia atualizações de status
                    if atualizacoes_status:
                        print(f"📊 Atualizando status para {len(atualizacoes_status)} registros...")
                        SharePointClient.atualizar_lote(atualizacoes_status)
                    
                    # Limpa alterações pendentes deste evento
                    app_state.limpar_alteracoes_evento(evento)
                    
                    if registros_atualizados > 0:
                        mostrar_mensagem(self.page, f"✅ {registros_atualizados} registro(s) atualizado(s) com sucesso!", "success")
                        
                        # Pequeno delay antes de recarregar (melhor UX)
                        import time
                        time.sleep(0.5)
                        
                        # Atualiza dados e interface
                        self.app_controller.atualizar_dados()
                    else:
                        mostrar_mensagem(self.page, "❌ Nenhum registro foi atualizado no SharePoint", "error")
                        # Desativa modo processamento em caso de erro
                        self._ativar_modo_processamento(False)
                else:
                    mostrar_mensagem(self.page, "⚠️ Nenhuma alteração para processar.", "warning")
                    # Desativa modo processamento
                    self._ativar_modo_processamento(False)
                
            except Exception as e:
                print(f"❌ Erro no processamento: {str(e)}")
                mostrar_mensagem(self.page, f"❌ Erro ao enviar justificativas: {str(e)}", "error")
                # Desativa modo processamento em caso de erro
                self._ativar_modo_processamento(False)
        
        # Executa em thread separada
        thread = threading.Thread(target=processar, daemon=True)
        thread.start()

    def _mostrar_modal_validacao(self, erros_validacao):
        """Mostra modal de erro com validações pendentes"""
        
        def fechar_erro(e):
            modal_erro.open = False
            self.page.update()

        # Calcula altura dinâmica baseada no número de erros
        altura_base = 180
        altura_por_erro = 35
        altura_padding = 80
        altura_minima = 300
        altura_maxima = 700

        altura_calculada = altura_base + (len(erros_validacao) * altura_por_erro) + altura_padding
        altura_final = max(altura_minima, min(altura_calculada, altura_maxima))

        # Se ultrapassar altura máxima, adiciona scroll
        usar_scroll = altura_calculada > altura_maxima

        # Container dos erros
        container_erros = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.WARNING, color=ft.colors.ORANGE_600, size=18),
                        ft.Text(linha, size=14, color=ft.colors.RED_800, weight=ft.FontWeight.W_500)
                    ], spacing=8),
                    padding=ft.padding.symmetric(vertical=5, horizontal=10),
                    bgcolor=ft.colors.RED_50,
                    border_radius=6,
                    border=ft.border.all(1, ft.colors.RED_200)
                )
                for linha in erros_validacao
            ], spacing=8, scroll=ft.ScrollMode.AUTO if usar_scroll else None),
            padding=15,
            height=min(400, len(erros_validacao) * altura_por_erro + 20) if usar_scroll else None
        )

        # Modal de erro
        modal_erro = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.ERROR_OUTLINE, color=ft.colors.RED_600, size=28),
                ft.Text("Campos Obrigatórios Pendentes", weight=ft.FontWeight.BOLD, color=ft.colors.RED_600, size=18)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE_600, size=20),
                                ft.Text(
                                    "Regra de Preenchimento:",
                                    size=15,
                                    color=ft.colors.BLUE_800,
                                    weight=ft.FontWeight.BOLD
                                )
                            ], spacing=8),
                            ft.Container(height=5),
                            ft.Text(
                                "Quando o motivo for 'Outros', é obrigatório informar detalhes no campo Observações.",
                                size=14,
                                color=ft.colors.GREY_800,
                                weight=ft.FontWeight.W_500
                            )
                        ], spacing=0),
                        padding=ft.padding.all(15),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        f"📋 Registros pendentes ({len(erros_validacao)}):",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.GREY_800
                    ),
                    ft.Container(height=10),
                    container_erros
                ], tight=True),
                width=700,
                height=altura_final,
                padding=25
            ),
            actions=[
                ft.ElevatedButton(
                    "Entendido",
                    on_click=fechar_erro,
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE,
                    icon=ft.icons.CHECK_CIRCLE,
                    width=150,
                    height=45,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6)
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=8)
        )

        self.page.dialog = modal_erro
        modal_erro.open = True
        self.page.update()
    
    def _aprovar_evento(self, evento):
        """Aprova um evento COM auditoria"""
        def confirmar_aprovacao(e):
            # Fecha o dialog de confirmação
            self.page.dialog.open = False
            self.page.update()
            
            # Mostra feedback imediato
            mostrar_mensagem(self.page, "⏳ Aprovando evento...", "info")

            # Processa aprovação em background
            import threading
            def processar_aprovacao():
                try:
                    df_evento = app_state.df_desvios[app_state.df_desvios["Titulo"] == evento]
                    if df_evento.empty:
                        return

                    # NOVO: Usa função simplificada para aprovação
                    atualizacoes_aprovacao = audit_service.processar_aprovacao_com_auditoria(
                        df_evento, "Aprovado"
                    )

                    # Envia todas as aprovações em paralelo
                    if atualizacoes_aprovacao:
                        sucessos = SharePointClient.atualizar_lote(atualizacoes_aprovacao)
                        if sucessos > 0:
                            mostrar_mensagem(self.page, "✅ Evento aprovado com sucesso!", "success")
                            self.app_controller.atualizar_dados()
                        else:
                            mostrar_mensagem(self.page, "❌ Erro ao aprovar evento", "error")
                except Exception as ex:
                    mostrar_mensagem(self.page, f"❌ Erro ao aprovar evento: {str(ex)}", "error")

            # Executa processamento em thread separada
            thread_aprovacao = threading.Thread(target=processar_aprovacao, daemon=True)
            thread_aprovacao.start()

        def cancelar_aprovacao(e):
            # Fecha o dialog sem fazer nada
            self.page.dialog.open = False
            self.page.update()

        # Parse do evento para exibição
        evento_info = EventoProcessor.parse_titulo_completo(evento)
        
        # Cria o dialog de confirmação
        confirmation_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color=ft.colors.GREEN_600, size=24),
                ft.Text("Confirmar Aprovação", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Tem certeza de que deseja aprovar este evento?",
                        size=16,
                        color=ft.colors.GREY_800
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"📋 Evento:",
                                size=12,
                                color=ft.colors.BLUE_800,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Container(height=3),
                            ft.Text(
                                f"{evento_info['tipo_amigavel']} - {evento_info['poi_amigavel']} - {evento_info['datahora_fmt']}",
                                size=14,
                                color=ft.colors.BLUE_700,
                                weight=ft.FontWeight.W_500
                            )
                        ], spacing=0),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=6,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "⚠️ Esta ação não pode ser desfeita.",
                        size=12,
                        color=ft.colors.ORANGE_600,
                        italic=True
                    )
                ], tight=True),
                width=420,
                padding=10
            ),
            actions=[
                ft.Row([
                    ft.TextButton(
                        "Não",
                        on_click=cancelar_aprovacao,
                        style=ft.ButtonStyle(color=ft.colors.GREY_600)
                    ),
                    ft.Container(width=80),
                    ft.ElevatedButton(
                        "Sim, Aprovar",
                        on_click=confirmar_aprovacao,
                        bgcolor=ft.colors.GREEN_600,
                        color=ft.colors.WHITE,
                        icon=ft.icons.CHECK,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ],
            shape=ft.RoundedRectangleBorder(radius=8)
        )

        # Exibe o dialog
        self.page.dialog = confirmation_dialog
        confirmation_dialog.open = True
        self.page.update()
    
    def _reprovar_evento(self, evento):
        """Reprova um evento COM auditoria"""
        justificativa_field = ft.TextField(
            label="Motivo da reprovação", 
            multiline=True, 
            width=800, 
            height=120
        )

        def confirmar(e):
            if not justificativa_field.value or not justificativa_field.value.strip():
                mostrar_mensagem(self.page, "Insira uma justificativa", "warning")
                return

            # Fecha o modal imediatamente
            modal.open = False
            self.page.update()
            
            # Mostra feedback imediato
            mostrar_mensagem(self.page, "⏳ Reprovando evento...", "info")
            
            # Processa reprovação em background
            import threading
            
            def processar_reprovacao():
                try:
                    df_evento = app_state.df_desvios[app_state.df_desvios["Titulo"] == evento]
                    
                    # NOVO: Usa função simplificada para reprovação
                    atualizacoes_reprovacao = audit_service.processar_aprovacao_com_auditoria(
                        df_evento, "Reprovado", justificativa_field.value
                    )
                    
                    # Envia todas as reprovações em paralelo
                    if atualizacoes_reprovacao:
                        sucessos = SharePointClient.atualizar_lote(atualizacoes_reprovacao)
                        if sucessos > 0:
                            mostrar_mensagem(self.page, "✅ Evento reprovado com sucesso!", "success")
                            self.app_controller.atualizar_dados()
                        else:
                            mostrar_mensagem(self.page, "❌ Erro ao reprovar evento", "error")
                    
                except Exception as ex:
                    mostrar_mensagem(self.page, f"❌ Erro ao reprovar evento: {str(ex)}", "error")
            
            # Executa processamento em thread separada
            thread_reprovacao = threading.Thread(target=processar_reprovacao, daemon=True)
            thread_reprovacao.start()

        def fechar(e):
            modal.open = False
            self.page.update()

        # Parse do evento para exibição
        evento_info = EventoProcessor.parse_titulo_completo(evento)

        # Modal de reprovação
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CANCEL, color=ft.colors.RED_600, size=24),
                ft.Text("Reprovar Evento", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.RED_600)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"📋 Evento:",
                                size=12,
                                color=ft.colors.BLUE_800,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Container(height=3),
                            ft.Text(
                                f"{evento_info['tipo_amigavel']} - {evento_info['poi_amigavel']} - {evento_info['datahora_fmt']}",
                                size=14,
                                color=ft.colors.BLUE_700,
                                weight=ft.FontWeight.W_500
                            )
                        ], spacing=0),
                        padding=ft.padding.all(12),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=6,
                        border=ft.border.all(1, ft.colors.BLUE_200),
                        margin=ft.margin.only(bottom=15)
                    ),
                    ft.Text("Motivo da reprovação:", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(height=10),
                    justificativa_field,
                    ft.Container(height=15)
                ]),
                width=800,
                height=220,
                padding=10,
                border_radius=4
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton(
                    "Confirmar Reprovação", 
                    on_click=confirmar, 
                    bgcolor=ft.colors.RED_600, 
                    color=ft.colors.WHITE,
                    icon=ft.icons.CANCEL
                )
            ],
            shape=ft.RoundedRectangleBorder(radius=4)
        )

        self.page.dialog = modal
        modal.open = True
        self.page.update()