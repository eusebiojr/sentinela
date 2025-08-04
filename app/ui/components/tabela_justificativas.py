"""
Componente de tabela de justificativas - VERSÃO CORRIGIDA SEM ERROS DE SINTAXE
"""
import flet as ft
import pandas as pd
from datetime import datetime
from ...core.session_state import get_session_state
from ...services.evento_processor import EventoProcessor
from ...services.data_formatter import DataFormatter
from ...services.sharepoint_client import SharePointClient
from ...services.audit_service import audit_service
from ...utils.ui_utils import get_screen_size, mostrar_mensagem

# NOVO: Importa validadores centralizados
from ...validators import field_validator, business_validator


class TabelaJustificativas:
    """Componente para exibir e editar justificativas de eventos com validações centralizadas"""
    
    def __init__(self, page: ft.Page, app_controller):
        self.page = page
        self.app_controller = app_controller
        self.processando_envio = False
        
    def criar_tabela(self, evento: str, df_evento: pd.DataFrame):
        session = get_session_state(self.page)
        """Cria tabela completa de justificativas"""
        
        # Configurações responsivas
        screen_size = get_screen_size(self.page.window_width)
        
        if screen_size == "small":
            placa_width, motivo_width, previsao_width, obs_width = 75, 273, 160, 380
            font_size, field_height = 12, 38
        elif screen_size == "medium":
            placa_width, motivo_width, previsao_width, obs_width = 86, 327, 175, 450
            font_size, field_height = 13, 40
        else:  # large
            placa_width, motivo_width, previsao_width, obs_width = 98, 356, 190, 600
            font_size, field_height = 14, 42
        
        # Determina motivos disponíveis
        evento_info = EventoProcessor.parse_titulo_completo(evento)
        poi_amigavel = evento_info["poi_amigavel"]
        localizacao = evento_info.get("localizacao", "RRP")
        motivos = EventoProcessor.determinar_motivos_por_poi(poi_amigavel, localizacao)
        
        # Verifica se usuário pode editar
        perfil = session.get_perfil_usuario()
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
        
        if screen_size == "small":
            table_width, column_spacing = 1300, 3
        elif screen_size == "medium":
            table_width, column_spacing = 1500, 4
        else:
            table_width, column_spacing = 1700, 5
        
        tabela = ft.DataTable(
            columns=columns, rows=table_rows,
            border=ft.border.all(1, ft.colors.GREY_300), border_radius=5,
            bgcolor=ft.colors.WHITE,
            horizontal_lines=ft.border.BorderSide(1, ft.colors.GREY_200),
            column_spacing=column_spacing, data_row_min_height=38,
            data_row_max_height=55, heading_row_height=40, width=table_width
        )
        
        tabela_container = ft.Container(
            content=ft.Row([tabela], scroll=ft.ScrollMode.ADAPTIVE),
            padding=5
        )
        
        botoes = self._criar_botoes_acao(evento, df_evento, pode_editar)
        
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
    
    def _criar_campo_motivo(self, motivos, chave_alteracao, valor_atual, campo_desabilitado, motivo_width, field_height, font_size):
        """Campo de motivo COM INTEGRAÇÃO de monitoring"""
        
        # NOVO: Registra valor original no sistema de monitoring
        try:
            self.app_controller.registrar_campo_para_monitoring(
                campo_id=f"motivo_{chave_alteracao}",
                valor_original=valor_atual
            )
        except Exception as e:
            logger.debug(f"Monitoring não disponível: {e}")
        
        def on_change(e):
            """Callback quando motivo muda - INTEGRADO COM MONITORING"""
            if self.processando_envio:
                return
                
            novo_valor = e.control.value
            session = get_session_state(self.page)
            
            # Atualização existente do estado
            session.atualizar_alteracao(chave_alteracao, "Motivo", novo_valor)
            
            # NOVO: Notifica sistema de monitoring
            try:
                self.app_controller.notificar_alteracao_campo(
                    campo_id=f"motivo_{chave_alteracao}",
                    novo_valor=novo_valor
                )
            except Exception as e:
                logger.debug(f"Monitoring não disponível: {e}")
        
        dropdown_motivo = ft.Dropdown(
            options=[ft.dropdown.Option(motivo, motivo) for motivo in motivos],
            value=valor_atual,
            on_change=on_change,
            width=motivo_width, height=field_height, text_size=font_size,
            dense=True, filled=True, border_radius=8,
            disabled=campo_desabilitado,
            bgcolor=ft.colors.GREY_100 if not campo_desabilitado else ft.colors.GREY_200
        )
        
        return dropdown_motivo

    def _criar_campo_observacao(self, chave_alteracao, valor_atual, campo_desabilitado, obs_width, field_height, font_size):
        """Campo de observação COM INTEGRAÇÃO de monitoring"""
        
        # NOVO: Registra valor original no sistema de monitoring
        try:
            self.app_controller.registrar_campo_para_monitoring(
                campo_id=f"observacao_{chave_alteracao}",
                valor_original=valor_atual
            )
        except Exception as e:
            logger.debug(f"Monitoring não disponível: {e}")
        
        def on_change(e):
            """Callback quando observação muda - INTEGRADO COM MONITORING"""
            if self.processando_envio:
                return
                
            novo_valor = e.control.value
            session = get_session_state(self.page)
            
            # Atualização existente do estado
            session.atualizar_alteracao(chave_alteracao, "Observacao", novo_valor)
            
            # NOVO: Notifica sistema de monitoring
            try:
                self.app_controller.notificar_alteracao_campo(
                    campo_id=f"observacao_{chave_alteracao}",
                    novo_valor=novo_valor
                )
            except Exception as e:
                logger.debug(f"Monitoring não disponível: {e}")
        
        campo_observacao = ft.TextField(
            value=valor_atual,
            hint_text="Digite a observação...",
            on_change=on_change,
            width=obs_width, height=field_height, text_size=font_size,
            multiline=False, dense=True, filled=True, border_radius=8,
            disabled=campo_desabilitado,
            bgcolor=ft.colors.GREY_100 if not campo_desabilitado else ft.colors.GREY_200
        )
        
        return campo_observacao

    def _criar_campo_previsao(self, chave_alteracao, row, campo_desabilitado, previsao_width, field_height, font_size):
        """Campo de previsão COM INTEGRAÇÃO de monitoring"""
        
        session = get_session_state(self.page)
        valor_atual = session.alteracoes_pendentes.get(chave_alteracao, {}).get("Previsao_Normalizacao", "")
        
        # Se não há alteração pendente, usa valor original da linha
        if not valor_atual:
            valor_atual = DataFormatter.safe_str(row.get('Previsao_Normalizacao', ''))
        
        # NOVO: Registra valor original no sistema de monitoring
        try:
            valor_original = DataFormatter.safe_str(row.get('Previsao_Normalizacao', ''))
            self.app_controller.registrar_campo_para_monitoring(
                campo_id=f"previsao_{chave_alteracao}",
                valor_original=valor_original
            )
        except Exception as e:
            logger.debug(f"Monitoring não disponível: {e}")
        
        def on_previsao_change(nova_previsao):
            """Callback quando previsão muda - INTEGRADO COM MONITORING"""
            if self.processando_envio:
                return
                
            # Atualização existente do estado
            session.atualizar_alteracao(chave_alteracao, "Previsao_Normalizacao", nova_previsao)
            
            # NOVO: Notifica sistema de monitoring
            try:
                self.app_controller.notificar_alteracao_campo(
                    campo_id=f"previsao_{chave_alteracao}",
                    novo_valor=nova_previsao
                )
            except Exception as e:
                logger.debug(f"Monitoring não disponível: {e}")
            
            # Atualiza display
            campo_display.value = nova_previsao
            self.page.update()
        
        # Campo de display (readonly)
        display_value = valor_atual if valor_atual else "Clique para selecionar"
        
        campo_display = ft.TextField(
            value=display_value,
            hint_text="Clique para selecionar" if not campo_desabilitado else "Processando...",
            width=previsao_width, height=field_height, text_size=font_size,
            dense=True, filled=True,
            bgcolor=ft.colors.GREY_100 if not campo_desabilitado else ft.colors.GREY_200,
            read_only=True, prefix_icon=ft.icons.SCHEDULE, border_radius=8,
            disabled=campo_desabilitado
        )
        
        def abrir_modal(e):
            if self.processando_envio:
                mostrar_mensagem(self.page, "⏳ Aguarde finalizar o processamento atual", "warning")
                return
            self._mostrar_modal_data_hora(campo_display, chave_alteracao, row)
        
        if not campo_desabilitado:
            campo_display.on_click = abrir_modal
        
        btn_edicao = ft.IconButton(
            icon=ft.icons.EDIT_CALENDAR,
            tooltip="Editar data/hora" if not campo_desabilitado else "Aguarde processamento...",
            on_click=abrir_modal if not campo_desabilitado else None,
            icon_size=16,
            icon_color=ft.colors.BLUE_600 if not campo_desabilitado else ft.colors.GREY_400,
            disabled=campo_desabilitado
        )
        
        return ft.Row([campo_display, btn_edicao], spacing=2)

    def _processar_justificativas(self, evento):
        """Processa justificativas COM LIMPEZA do monitoring"""
        
        def processar():
            try:
                session = get_session_state(self.page)
                alteracoes = session.alteracoes_pendentes
                
                if alteracoes:
                    # Processamento existente...
                    atualizacoes_lote = audit_service.processar_alteracoes_com_auditoria(
                        self.page, alteracoes
                    )
                    
                    if atualizacoes_lote:
                        sucessos = SharePointClient.atualizar_lote(atualizacoes_lote)
                        
                        if sucessos > 0:
                            # Limpeza existente
                            session.alteracoes_pendentes.clear()
                            
                            # NOVO: Limpa também o monitoring de campos
                            try:
                                self.app_controller.limpar_alteracoes_campos()
                            except Exception as e:
                                logger.debug(f"Limpeza monitoring não disponível: {e}")
                            
                            mostrar_mensagem(self.page, f"✅ {sucessos} registro(s) atualizado(s) com sucesso!", "success")
                            
                            # Desativa modo processamento
                            self._ativar_modo_processamento(False)
                            
                            # Aguarda e atualiza dados
                            import time
                            time.sleep(0.5)
                            self.app_controller.atualizar_dados()
                        else:
                            mostrar_mensagem(self.page, "❌ Nenhum registro foi atualizado no SharePoint", "error")
                            self._ativar_modo_processamento(False)
                    else:
                        mostrar_mensagem(self.page, "⚠️ Nenhuma alteração para processar.", "warning")
                        self._ativar_modo_processamento(False)
                    
            except Exception as e:
                logger.error(f"❌ Erro no processamento: {str(e)}")
                mostrar_mensagem(self.page, f"❌ Erro ao enviar justificativas: {str(e)}", "error")
                self._ativar_modo_processamento(False)
        
        thread = threading.Thread(target=processar, daemon=True)
        thread.start()

    def limpar_alteracoes_evento(self, evento: str):
        """Limpa alterações de um evento específico"""
        try:
            session = get_session_state(self.page)
            
            # Limpa alterações do estado da sessão
            session.limpar_alteracoes_evento(evento)
            
            # NOVO: Limpa também alterações do monitoring para este evento
            if hasattr(session, 'field_monitor_service') and session.field_monitor_service:
                # Identifica campos deste evento e limpa
                campos_evento = [
                    f"motivo_{evento}_{idx}",
                    f"observacao_{evento}_{idx}", 
                    f"previsao_{evento}_{idx}"
                    for idx in range(20)  # Assume máximo 20 registros por evento
                ]
                
                for campo_id in campos_evento:
                    session.field_monitor_service.limpar_campo(campo_id)
                    
            logger.info(f"✅ Alterações do evento {evento} limpas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar alterações do evento: {e}")

    def _criar_linha_tabela(self, evento, row, motivos, pode_editar, 
                          placa_width, motivo_width, previsao_width, obs_width, 
                          font_size, field_height):
        """Cria uma linha da tabela"""
        
        evento_str = str(evento).strip()
        
        if isinstance(row["ID"], pd.Series):
            row_id = str(row["ID"].iloc[0]).strip()
        else:
            row_id = str(row["ID"]).strip()
        
        chave_alteracao = f"{evento_str}_{row_id}"
                
        if pode_editar:
            return self._criar_campos_editaveis(
                row, motivos, chave_alteracao,
                placa_width, motivo_width, previsao_width, obs_width,
                font_size, field_height
            )
        else:
            return self._criar_campos_readonly(row, placa_width, font_size)
    
    def _criar_campos_editaveis(self, row, motivos, chave_alteracao,
                               placa_width, motivo_width, previsao_width, obs_width,
                               font_size, field_height):
        """Cria campos editáveis - MIGRADO PARA VALIDAÇÕES CENTRALIZADAS"""
        
        campos_desabilitados = self.processando_envio
        
        # Opções do dropdown
        opcoes_motivo = [ft.dropdown.Option("", "— Selecione —")] + [
            ft.dropdown.Option(m) for m in sorted(motivos)
        ]
        
        valor_dropdown = row["Motivo"] if (row["Motivo"] in motivos and row["Motivo"].strip() != "") else ""
        
        # Campo de observação
        obs_field = ft.TextField(
            value=str(row["Observacoes"]) if pd.notnull(row["Observacoes"]) else "",
            width=obs_width, height=field_height, text_size=font_size,
            dense=True, filled=True,
            bgcolor=ft.colors.GREY_100 if not campos_desabilitados else ft.colors.GREY_200,
            multiline=True, min_lines=1, max_lines=3,
            label="Observações", border_radius=6, disabled=campos_desabilitados
        )
        
        # Ícone de alerta
        icone_alerta = ft.Icon(
            ft.icons.WARNING, color=ft.colors.ORANGE_600, size=20, visible=False,
            tooltip="Observação obrigatória quando motivo é 'Outros'"
        )
        
        # Validação centralizada
        def validar_motivo_mudanca(e):
            session = get_session_state(self.page)
            if campos_desabilitados:
                return
            
            motivo_selecionado = e.control.value
            obs_value = obs_field.value
            
            # USA NOVO VALIDADOR CENTRALIZADO
            validation_result = business_validator.validate_motivo_observacao(
                motivo_selecionado, obs_value
            )
            
            if not validation_result.valid:
                obs_field.border_color = ft.colors.ORANGE_600
                icone_alerta.visible = True
            else:
                obs_field.border_color = None
                icone_alerta.visible = False
            
            session.atualizar_alteracao(chave_alteracao, "Motivo", motivo_selecionado)
            self.page.update()
        
        def validar_observacao_mudanca(e):
            session = get_session_state(self.page)
            if campos_desabilitados:
                return
            
            motivo_selecionado = motivo_dropdown.value
            obs_value = e.control.value
            
            # USA NOVO VALIDADOR CENTRALIZADO
            validation_result = business_validator.validate_motivo_observacao(
                motivo_selecionado, obs_value
            )
            
            if not validation_result.valid:
                obs_field.border_color = ft.colors.ORANGE_600
                icone_alerta.visible = True
            else:
                obs_field.border_color = None
                icone_alerta.visible = False
            
            session.atualizar_alteracao(chave_alteracao, "Observacoes", obs_value)
            self.page.update()
        
        # Dropdown de motivo
        motivo_dropdown = ft.Dropdown(
            value=valor_dropdown, options=opcoes_motivo,
            width=motivo_width, height=field_height, text_size=font_size,
            dense=True, filled=True,
            bgcolor=ft.colors.GREY_100 if not campos_desabilitados else ft.colors.GREY_200,
            content_padding=ft.padding.only(left=12, right=8, top=8, bottom=8),
            alignment=ft.alignment.center_left,
            on_change=validar_motivo_mudanca if not campos_desabilitados else None,
            disabled=campos_desabilitados
        )
        
        if not campos_desabilitados:
            obs_field.on_change = validar_observacao_mudanca
        
        # Validação inicial centralizada
        if not campos_desabilitados:
            initial_validation = business_validator.validate_motivo_observacao(
                valor_dropdown, obs_field.value
            )
            if not initial_validation.valid:
                obs_field.border_color = ft.colors.ORANGE_600
                icone_alerta.visible = True
        
        # Campo de previsão
        previsao_field = self._criar_campo_previsao(
            row["Previsao_Liberacao"], chave_alteracao, row,
            previsao_width, font_size, field_height
        )
        
        obs_container = ft.Row([obs_field, icone_alerta], spacing=5, alignment=ft.MainAxisAlignment.START)
        
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
                width=placa_width, padding=5
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
        """Cria campo de previsão com modal"""
        
        display_value = ""
        if valor_inicial and str(valor_inicial).strip():
            display_value = str(valor_inicial).strip()
        
        campo_desabilitado = self.processando_envio
        
        campo_display = ft.TextField(
            value=display_value,
            hint_text="Clique para selecionar" if not campo_desabilitado else "Processando...",
            width=previsao_width, height=field_height, text_size=font_size,
            dense=True, filled=True,
            bgcolor=ft.colors.GREY_100 if not campo_desabilitado else ft.colors.GREY_200,
            read_only=True, prefix_icon=ft.icons.SCHEDULE, border_radius=8,
            disabled=campo_desabilitado
        )
        
        def abrir_modal(e):
            if self.processando_envio:
                mostrar_mensagem(self.page, "⏳ Aguarde finalizar o processamento atual", "warning")
                return
            self._mostrar_modal_data_hora(campo_display, chave_alteracao, row)
        
        if not campo_desabilitado:
            campo_display.on_click = abrir_modal
        
        btn_edicao = ft.IconButton(
            icon=ft.icons.EDIT_CALENDAR,
            tooltip="Editar data/hora" if not campo_desabilitado else "Aguarde processamento...",
            on_click=abrir_modal if not campo_desabilitado else None,
            icon_size=16,
            icon_color=ft.colors.BLUE_600 if not campo_desabilitado else ft.colors.GREY_400,
            disabled=campo_desabilitado
        )
        
        return ft.Row([campo_display, btn_edicao], spacing=2)

    def _mostrar_modal_data_hora(self, campo_display, chave_alteracao, row):
        """Modal de data/hora com validação centralizada"""
        
        def gerar_opcoes_horario():
            opcoes = []
            for hora in range(24):
                for minuto in [0, 30]:
                    hora_formatada = f"{hora:02d}:{minuto:02d}"
                    opcoes.append(ft.dropdown.Option(hora_formatada, hora_formatada))
            return opcoes
        
        from datetime import datetime, timedelta
        import pytz
        
        agora = datetime.now(pytz.timezone("America/Campo_Grande"))
        data_hoje = agora.strftime("%d/%m/%Y")
        
        hora_padrao = agora + timedelta(hours=1)
        minutos = hora_padrao.minute
        
        if minutos <= 30:
            hora_padrao = hora_padrao.replace(minute=30, second=0, microsecond=0)
        else:
            hora_padrao = hora_padrao.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        hora_padrao_str = hora_padrao.strftime("%H:%M")
        
        temp_data_field = ft.TextField(
            label="Data (dd/mm/aaaa)", value=data_hoje, width=150, hint_text="12/07/2025"
        )
        
        temp_hora_dropdown = ft.Dropdown(
            label="Hora", value=hora_padrao_str, options=gerar_opcoes_horario(),
            width=120, dense=True, filled=True, bgcolor=ft.colors.GREY_100,
            content_padding=ft.padding.only(left=12, right=8, top=8, bottom=8)
        )
        
        error_text = ft.Text("", color=ft.colors.RED, size=12, visible=False)
        
        def confirmar_data_hora(e):
            session = get_session_state(self.page)
            try:
                data_str = temp_data_field.value.strip()
                hora_str = temp_hora_dropdown.value
                
                # USA VALIDAÇÃO CENTRALIZADA
                datetime_validation = field_validator.validate_datetime_fields(
                    data_str, 
                    hora_str, 
                    reference_date=DataFormatter.safe_str(row["Data/Hora Entrada"]),
                    must_be_future=False,
                    max_days_future=30
                )
                
                if not datetime_validation.valid:
                    error_text.value = f"⚠️ {datetime_validation.errors[0]}"
                    error_text.visible = True
                    self.page.update()
                    return
                
                # Se validação passou
                novo_valor = datetime_validation.data.get("formatted_datetime", f"{data_str} {hora_str}")
                campo_display.value = novo_valor
                
                session.atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", novo_valor)
                
                modal_datetime.open = False
                self.page.update()
                
            except Exception as ex:
                error_text.value = f"❌ Erro: {str(ex)}"
                error_text.visible = True
                self.page.update()
        
        def cancelar(e):
            modal_datetime.open = False
            self.page.update()
        
        def limpar_campos(e):
            session = get_session_state(self.page)
            temp_data_field.value = ""
            temp_hora_dropdown.value = None
            error_text.visible = False
            campo_display.value = ""
            session.atualizar_alteracao(chave_alteracao, "Previsao_Liberacao", "")
            self.page.update()
        
        def usar_hoje_mais_uma_hora(e):
            agora = datetime.now(pytz.timezone("America/Campo_Grande"))
            data_hoje = agora.strftime("%d/%m/%Y")
            hora_mais_uma = agora + timedelta(hours=1)
            minutos = hora_mais_uma.minute
            
            if minutos <= 30:
                hora_mais_uma = hora_mais_uma.replace(minute=30, second=0, microsecond=0)
            else:
                hora_mais_uma = hora_mais_uma.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            hora_str = hora_mais_uma.strftime("%H:%M")
            temp_data_field.value = data_hoje
            temp_hora_dropdown.value = hora_str
            error_text.visible = False
            self.page.update()
        
        def usar_amanha_mesmo_horario(e):
            agora = datetime.now(pytz.timezone("America/Campo_Grande"))
            amanha = agora + timedelta(days=1)
            data_amanha = amanha.strftime("%d/%m/%Y")
            
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
        
        botoes_atalho = ft.Row([
            ft.ElevatedButton("📅 Hoje +1h", on_click=usar_hoje_mais_uma_hora, 
                            bgcolor=ft.colors.BLUE_100, color=ft.colors.BLUE_800,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                            height=36, width=130),
            ft.ElevatedButton("📅 Amanhã", on_click=usar_amanha_mesmo_horario,
                            bgcolor=ft.colors.GREEN_100, color=ft.colors.GREEN_800,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                            height=36, width=130)
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        
        modal_datetime = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecionar Data e Hora", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Informe a data e hora prevista:", size=14),
                    ft.Container(
                        content=ft.Text(
                            f"📅 Data de entrada: {DataFormatter.safe_str(row['Data/Hora Entrada'])}", 
                            size=12, color=ft.colors.BLUE_700, weight=ft.FontWeight.W_500
                        ),
                        padding=ft.padding.symmetric(vertical=5),
                        bgcolor=ft.colors.BLUE_50, border_radius=3
                    ),
                    ft.Container(height=10),
                    ft.Text("⚡ Atalhos rápidos:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    botoes_atalho,
                    ft.Container(height=15),
                    ft.Text("📝 Ou preencha manualmente:", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
                    ft.Row([temp_data_field, temp_hora_dropdown], spacing=10),
                    ft.Container(height=5),
                    error_text,
                    ft.Container(height=15),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("💡 Dicas:", size=11, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_600),
                            ft.Text("• A data deve ser posterior à data de entrada", size=10, color=ft.colors.GREY_500),
                            ft.Text("• Use os atalhos para preenchimento rápido", size=10, color=ft.colors.GREY_500),
                            ft.Text("• Horários disponíveis de meia em meia hora", size=10, color=ft.colors.GREY_500),
                        ], spacing=2),
                        padding=ft.padding.all(8), bgcolor=ft.colors.GREY_50,
                        border_radius=4, border=ft.border.all(1, ft.colors.GREY_200)
                    ),
                    ft.Container(height=10)
                ], tight=True),
                width=450, height=400, padding=15
            ),
            actions=[
                ft.TextButton("Limpar", on_click=limpar_campos),
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Confirmar", on_click=confirmar_data_hora, 
                                bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE, icon=ft.icons.CHECK)
            ],
            shape=ft.RoundedRectangleBorder(radius=8)
        )
        
        self.page.dialog = modal_datetime
        modal_datetime.open = True
        self.page.update()

    def _criar_botoes_acao(self, evento, df_evento, pode_editar):
        """Cria botões de ação"""
        session = get_session_state(self.page)
        if pode_editar:
            if self.processando_envio:
                btn_text, btn_color, btn_disabled, btn_icon = "⏳ Enviando...", ft.colors.GREY_600, True, ft.icons.HOURGLASS_EMPTY
            else:
                btn_text, btn_color, btn_disabled, btn_icon = "Enviar Justificativas", ft.colors.GREEN_600, False, ft.icons.SEND
            
            btn_enviar = ft.ElevatedButton(
                btn_text, bgcolor=btn_color, color=ft.colors.WHITE, icon=btn_icon,
                on_click=lambda e: self._enviar_justificativas(evento, df_evento) if not btn_disabled else None,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)), disabled=btn_disabled
            )
            return ft.Row([btn_enviar], alignment=ft.MainAxisAlignment.END)
        
        else:
            perfil = session.get_perfil_usuario()
            status = df_evento["Status"].iloc[0] if "Status" in df_evento.columns else "Pendente"
            
            if perfil in ("aprovador", "torre") and status == "Preenchido":
                btn_reprovar = ft.ElevatedButton(
                    "❌ Reprovar", bgcolor=ft.colors.RED_600, color=ft.colors.WHITE,
                    on_click=lambda e: self._reprovar_evento(evento)
                )
                btn_aprovar = ft.ElevatedButton(
                    "✅ Aprovar", bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE,
                    on_click=lambda e: self._aprovar_evento(evento)
                )
                return ft.Row([
                    btn_reprovar,
                    ft.Container(content=btn_aprovar, expand=True, alignment=ft.alignment.center_right)
                ])
        
        return ft.Container()
    
    def _enviar_justificativas(self, evento, df_evento):
        """Envio com validação centralizada"""
        session = get_session_state(self.page)
        
        if self.processando_envio:
            mostrar_mensagem(self.page, "⏳ Aguarde... processamento em andamento", "warning")
            return
        
        mostrar_mensagem(self.page, "⏳ Validando dados...", "info")
        
        # USA VALIDADOR CENTRALIZADO
        titulo_evento = df_evento["Titulo"].iloc[0] if "Titulo" in df_evento.columns else ""
        
        validation_result = business_validator.validate_evento_justificativas(
            df_evento, session.alteracoes_pendentes, titulo_evento
        )
        
        if not validation_result.valid:
            mostrar_mensagem(self.page, "❌ Existem campos obrigatórios não preenchidos", "error")
            self._mostrar_modal_validacao(validation_result.errors)
            return
        
        # Se validação passou, continua com envio
        self._ativar_modo_processamento(True)
        mostrar_mensagem(self.page, "⏳ Enviando justificativas...", "info")
        self._processar_envio_com_auditoria(evento, df_evento)
    
    def _mostrar_modal_validacao(self, erros_validacao):
        """Modal de erro com validações"""
        
        def fechar_erro(e):
            modal_erro.open = False
            self.page.update()

        # Calcula altura dinâmica
        altura_base = 180
        altura_por_erro = 35
        altura_padding = 80
        altura_minima = 300
        altura_maxima = 700

        altura_calculada = altura_base + (len(erros_validacao) * altura_por_erro) + altura_padding
        altura_final = max(altura_minima, min(altura_calculada, altura_maxima))
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
                    bgcolor=ft.colors.RED_50, border_radius=6,
                    border=ft.border.all(1, ft.colors.RED_200)
                )
                for linha in erros_validacao
            ], spacing=8, scroll=ft.ScrollMode.AUTO if usar_scroll else None),
            padding=15,
            height=min(400, len(erros_validacao) * altura_por_erro + 20) if usar_scroll else None
        )

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
                                ft.Text("Regra de Preenchimento:", size=15, color=ft.colors.BLUE_800, weight=ft.FontWeight.BOLD)
                            ], spacing=8),
                            ft.Container(height=5),
                            ft.Text("Quando o motivo for 'Outros', é obrigatório informar detalhes no campo Observações.",
                                    size=14, color=ft.colors.GREY_800, weight=ft.FontWeight.W_500)
                        ], spacing=0),
                        padding=ft.padding.all(15), bgcolor=ft.colors.BLUE_50, border_radius=8,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    ft.Container(height=15),
                    ft.Text(f"📋 Registros pendentes ({len(erros_validacao)}):", size=16, 
                            weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800),
                    ft.Container(height=10),
                    container_erros
                ], tight=True),
                width=700, height=altura_final, padding=25
            ),
            actions=[
                ft.ElevatedButton("Entendido", on_click=fechar_erro, bgcolor=ft.colors.BLUE_600, 
                                color=ft.colors.WHITE, icon=ft.icons.CHECK_CIRCLE, width=150, height=45,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=8)
        )

        self.page.dialog = modal_erro
        modal_erro.open = True
        self.page.update()
    
    def _ativar_modo_processamento(self, ativo: bool):
        """Ativa/desativa modo processamento"""
        self.processando_envio = ativo
        try:
            self.page.update()
        except Exception as e:
            print(f"⚠️ [PROCESSAMENTO] Erro ao atualizar interface: {e}")
    
    def _processar_envio_com_auditoria(self, evento, df_evento):
        """Processa envio com auditoria"""
        session = get_session_state(self.page)
        
        import threading
        def processar():
            try:
                alteracoes_evento = {k: v for k, v in session.alteracoes_pendentes.items() 
                                if k.startswith(f"{evento}_")}
                
                if not alteracoes_evento:
                    mostrar_mensagem(self.page, "⚠️ Nenhuma alteração detectada.", "warning")
                    self._ativar_modo_processamento(False)
                    return
                
                atualizacoes_lote = audit_service.processar_preenchimento_com_auditoria(
                    self.page, evento, df_evento, session.alteracoes_pendentes
                )
                
                if atualizacoes_lote:
                    print(f"📊 Enviando {len(atualizacoes_lote)} registros com auditoria...")
                    registros_atualizados = SharePointClient.atualizar_lote(atualizacoes_lote)
                    print(f"✅ {registros_atualizados} registros atualizados no SharePoint")
                    
                    status_evento = EventoProcessor.calcular_status_evento(df_evento, session.alteracoes_pendentes)
                    
                    atualizacoes_status = []
                    for _, row in df_evento.iterrows():
                        row_id = str(row["ID"]).strip()
                        dados_status = {"Status": status_evento}
                        atualizacoes_status.append((int(row_id), dados_status))
                    
                    if atualizacoes_status:
                        print(f"📊 Atualizando status para {len(atualizacoes_status)} registros...")
                        SharePointClient.atualizar_lote(atualizacoes_status)
                    
                    session.limpar_alteracoes_evento(evento)
                    
                    if registros_atualizados > 0:
                        mostrar_mensagem(self.page, f"✅ {registros_atualizados} registro(s) atualizado(s) com sucesso!", "success")
                        import time
                        time.sleep(0.5)
                        self.app_controller.atualizar_dados()
                    else:
                        mostrar_mensagem(self.page, "❌ Nenhum registro foi atualizado no SharePoint", "error")
                        self._ativar_modo_processamento(False)
                else:
                    mostrar_mensagem(self.page, "⚠️ Nenhuma alteração para processar.", "warning")
                    self._ativar_modo_processamento(False)
                
            except Exception as e:
                print(f"❌ Erro no processamento: {str(e)}")
                mostrar_mensagem(self.page, f"❌ Erro ao enviar justificativas: {str(e)}", "error")
                self._ativar_modo_processamento(False)
        
        thread = threading.Thread(target=processar, daemon=True)
        thread.start()
    
    def _aprovar_evento(self, evento):
        """Aprova evento COM LIMPEZA do monitoring"""
        
        def confirmar_aprovacao(e):
            self.page.dialog.open = False
            self.page.update()
            mostrar_mensagem(self.page, "⏳ Aprovando evento...", "info")

            import threading
            def processar_aprovacao():
                try:
                    session = get_session_state(self.page)
                    df_evento = session.df_desvios[session.df_desvios["Titulo"] == evento]
                    
                    if not df_evento.empty:
                        atualizacoes_aprovacao = audit_service.processar_aprovacao_com_auditoria(
                            self.page, df_evento, "Aprovado"
                        )
                        
                        if atualizacoes_aprovacao:
                            sucessos = SharePointClient.atualizar_lote(atualizacoes_aprovacao)
                            
                            if sucessos > 0:
                                # NOVO: Limpa alterações de monitoring deste evento
                                self.limpar_alteracoes_evento(evento)
                                
                                mostrar_mensagem(self.page, "✅ Evento aprovado com sucesso!", "success")
                                self.app_controller.atualizar_dados()
                            else:
                                mostrar_mensagem(self.page, "❌ Erro ao aprovar evento", "error")
                        else:
                            mostrar_mensagem(self.page, "❌ Erro ao preparar aprovação", "error")
                            
                except Exception as ex:
                    mostrar_mensagem(self.page, f"❌ Erro ao aprovar evento: {str(ex)}", "error")
            
            thread_aprovacao = threading.Thread(target=processar_aprovacao, daemon=True)
            thread_aprovacao.start()

        def cancelar_aprovacao(e):
            self.page.dialog.open = False
            self.page.update()

        # O resto do método permanece igual (dialog de confirmação)
        evento_info = EventoProcessor.parse_titulo_completo(evento)
        
        confirmation_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color=ft.colors.GREEN_600, size=24),
                ft.Text("Confirmar Aprovação", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Tem certeza de que deseja aprovar este evento?", size=16, color=ft.colors.GREY_800),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📋 Evento:", size=12, color=ft.colors.BLUE_800, weight=ft.FontWeight.BOLD),
                            ft.Container(height=3),
                            ft.Text(f"{evento_info['tipo_amigavel']} - {evento_info['poi_amigavel']} - {evento_info['datahora_fmt']}",
                                    size=14, color=ft.colors.BLUE_700, weight=ft.FontWeight.W_500)
                        ], spacing=0),
                        padding=ft.padding.all(12), bgcolor=ft.colors.BLUE_50, border_radius=6,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    ft.Container(height=8),
                    ft.Text("⚠️ Esta ação não pode ser desfeita.", size=12, color=ft.colors.ORANGE_600, italic=True)
                ], spacing=5),
                width=400, height=120
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_aprovacao),
                ft.ElevatedButton(
                    "✅ Aprovar",
                    on_click=confirmar_aprovacao,
                    bgcolor=ft.colors.GREEN_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        self.page.dialog = confirmation_dialog
        confirmation_dialog.open = True
        self.page.update()
    
    def _reprovar_evento(self, evento):
        """Reprova evento COM LIMPEZA do monitoring"""
        
        def processar_reprovacao():
            try:
                session = get_session_state(self.page)
                df_evento = session.df_desvios[session.df_desvios["Titulo"] == evento]
                
                if not df_evento.empty:
                    atualizacoes_reprovacao = audit_service.processar_aprovacao_com_auditoria(
                        self.page, df_evento, "Não Tratado"
                    )
                    
                    if atualizacoes_reprovacao:
                        sucessos = SharePointClient.atualizar_lote(atualizacoes_reprovacao)
                        
                        if sucessos > 0:
                            # NOVO: Limpa alterações de monitoring deste evento
                            self.limpar_alteracoes_evento(evento)
                            
                            mostrar_mensagem(self.page, "✅ Evento reprovado com sucesso!", "success")
                            self.app_controller.atualizar_dados()
                        else:
                            mostrar_mensagem(self.page, "❌ Erro ao reprovar evento", "error")
                    else:
                        mostrar_mensagem(self.page, "❌ Erro ao preparar reprovação", "error")
                    
            except Exception as ex:
                mostrar_mensagem(self.page, f"❌ Erro ao reprovar evento: {str(ex)}", "error")
        
        # Dialog de confirmação (código existente adaptado)
        evento_info = EventoProcessor.parse_titulo_completo(evento)

        def fechar(e):
            modal.open = False
            self.page.update()

        def confirmar_reprovacao(e):
            modal.open = False
            self.page.update()
            mostrar_mensagem(self.page, "⏳ Reprovando evento...", "info")
            
            thread_reprovacao = threading.Thread(target=processar_reprovacao, daemon=True)
            thread_reprovacao.start()

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
                            ft.Text("📋 Evento:", size=12, color=ft.colors.BLUE_800, weight=ft.FontWeight.BOLD),
                            ft.Container(height=3),
                            ft.Text(f"{evento_info['tipo_amigavel']} - {evento_info['poi_amigavel']} - {evento_info['datahora_fmt']}",
                                    size=14, color=ft.colors.BLUE_700, weight=ft.FontWeight.W_500)
                        ], spacing=0),
                        padding=ft.padding.all(12), bgcolor=ft.colors.BLUE_50, border_radius=6,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    ft.Container(height=12),
                    ft.Text("Tem certeza de que deseja reprovar este evento?", size=14, color=ft.colors.GREY_800),
                    ft.Container(height=8),
                    ft.Text("⚠️ O evento será marcado como 'Não Tratado' e esta ação não pode ser desfeita.", 
                            size=12, color=ft.colors.RED_600, italic=True)
                ], spacing=8),
                width=400, height=140
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton(
                    "❌ Reprovar",
                    on_click=confirmar_reprovacao,
                    bgcolor=ft.colors.RED_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        self.page.dialog = modal
        modal.open = True
        self.page.update()

    def _mostrar_justificativa_reprovacao(self, df_evento):
        """Mostra justificativa de reprovação"""
        def limpar_texto_html(texto_html: str) -> str:
            import html
            import re
            
            if not texto_html:
                return ""
            
            texto = re.sub(r'<div[^>]*>', '', texto_html)
            texto = re.sub(r'</div>', '\n', texto)
            texto = re.sub(r'<br\s*/?>', '\n', texto)
            texto = re.sub(r'<p[^>]*>', '', texto)
            texto = re.sub(r'</p>', '\n\n', texto)
            texto = re.sub(r'<[^>]+>', '', texto)
            texto = html.unescape(texto)
            texto = re.sub(r'\n\s*\n', '\n\n', texto)
            texto = re.sub(r'^\s+|\s+', texto)
            
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
                content=ft.Text(justificativa, size=14, selectable=True, max_lines=None,
                               overflow=ft.TextOverflow.VISIBLE, text_align=ft.TextAlign.LEFT),
                width=450, height=200, padding=15
            ),
            actions=[ft.TextButton("Fechar", on_click=lambda e: fechar_modal_justificativa())],
            shape=ft.RoundedRectangleBorder(radius=4)
        )
        
        self.page.dialog = modal_justificativa
        modal_justificativa.open = True
        self.page.update()